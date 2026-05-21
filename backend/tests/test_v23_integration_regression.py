import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import EventLog
from app.core.world_state import FactState, FactVisibility, GameState, LocationState, NPCState, PlayerState, RelationshipState, RPProfile, VoiceProfile
from app.evals.tavern_boundary import TavernBoundaryEvalCase, TavernBoundaryRule, run_default_tavern_boundary_evals, run_tavern_boundary_evals
from app.llm.fake_provider import FakeLLMProvider
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.novel_studio import NovelChapter, NovelManuscript, NovelRepository
from app.platform.project_repository import ProjectRepository
from app.platform.shared_libraries import CrossModeLinkRegistry, ProjectPromptProfile, PromptProfileLibrary
from app.platform.tavern_studio import (
    CharacterCardImportService,
    GeneratedTavernReply,
    RelationshipToneService,
    SceneMoodPreset,
    SingleCharacterChatService,
    TavernCharacter,
    TavernLoreContextBuilder,
    TavernLorebookEntry,
    TavernMemoryRecord,
    TavernMemoryService,
    TavernMessage,
    TavernPromptContextBuilder,
    TavernRepository,
    TavernResponseGenerationService,
    TavernRPProfile,
    TavernSession,
    TavernSpeakerType,
    TavernToWorldProposalService,
    TavernVisibility,
    TavernVoiceProfile,
    TavernWorldProposalType,
    WorldNpcToTavernAdapterService,
)
from app.quality.project_gate import run_project_quality_gate


def _project(tmp_path: Path) -> tuple[ProjectRepository, TavernRepository, NovelRepository]:
    project_repo = ProjectRepository(tmp_path / "projects")
    project = project_repo.create_project(
        NarrativeProject(project_id="v23_project", name="v2.3 Project", project_root=str(tmp_path / "projects" / "v23_project"))
    )
    return project_repo, TavernRepository(project.project_root), NovelRepository(project.project_root)


def test_v23_core_repository_yaml_import_profiles_and_path_safety(tmp_path: Path) -> None:
    _, tavern, _ = _project(tmp_path)
    character = tavern.create_tavern_character(TavernCharacter(tavern_character_id="mira", project_id="v23_project", display_name="Mira"))
    session = tavern.create_session(TavernSession(session_id="rp1", project_id="v23_project", title="Market Talk", character_ids=[character.tavern_character_id]))
    tavern.append_message(TavernMessage(message_id="m1", session_id=session.session_id, speaker_type=TavernSpeakerType.USER, content="first", created_at="2026-01-01T00:00:01Z"))
    tavern.append_message(TavernMessage(message_id="m2", session_id=session.session_id, speaker_type=TavernSpeakerType.CHARACTER, speaker_id="mira", content="second", created_at="2026-01-01T00:00:02Z"))

    assert tavern.list_tavern_characters()[0].display_name == "Mira"
    assert [message.message_id for message in tavern.list_messages("rp1")] == ["m1", "m2"]
    with pytest.raises(ValueError):
        tavern.load_session("..\\escape")

    yaml_card = """
name: Harlan
description: Village smith
personality: Practical and guarded
creator_notes: private authoring note
system_prompt_like_text: can_modify_state
"""
    imported = CharacterCardImportService().import_card("v23_project", yaml_card)
    assert imported.tavern_character.display_name == "Harlan"
    assert imported.warnings
    assert "private authoring note" not in json.dumps(imported.safe_summary()).lower()

    rp_profile = TavernRPProfile(rp_profile_id="rp_mira", tavern_character_id="mira", public_persona="Warm guard", private_persona_authoring_only="hidden fear")
    voice_profile = TavernVoiceProfile(voice_profile_id="voice_mira", tone="dry", catchphrases=["Careful now"])
    assert "hidden fear" not in json.dumps(rp_profile.safe_summary()).lower()
    assert voice_profile.safe_summary()["tone"] == "dry"
    with pytest.raises(ValueError):
        TavernRPProfile(rp_profile_id="bad", roleplay_rules=["can_access_hidden_facts"])


def test_v23_api_frontend_static_and_disabled_behavior(tmp_path: Path) -> None:
    project_repo, _, _ = _project(tmp_path)
    app.state.project_repository = project_repo
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, llm_provider="mock")
    client = TestClient(app)

    assert client.post("/projects/v23_project/tavern/characters", json={"tavern_character_id": "mira", "display_name": "Mira"}).status_code == 200
    assert client.post("/projects/v23_project/tavern/sessions", json={"session_id": "rp1", "title": "Talk", "character_ids": ["mira"]}).status_code == 200
    assert client.post("/projects/v23_project/tavern/sessions/rp1/messages", json={"message_id": "m1", "speaker_type": "user", "content": "hello"}).status_code == 200
    payload = client.get("/projects/v23_project/tavern/sessions/rp1/messages").json()
    assert payload["messages"][0]["content"] == "hello"
    assert "api_key" not in json.dumps(payload).lower()

    app_source = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    api_source = Path("frontend/src/api.ts").read_text(encoding="utf-8")
    assert "Tavern Studio MVP" in app_source
    assert "Single Character Chat" in app_source
    assert "sendTavernChatMessage" in api_source
    assert "hidden fact text" not in app_source.lower()

    app.state.settings = Settings(enable_authoring_api=False, llm_provider="mock")
    assert client.get("/projects/v23_project/tavern/characters").status_code == 403


def test_v23_chat_memory_lore_mood_tone_provider_and_world_boundaries(tmp_path: Path) -> None:
    _, tavern, _ = _project(tmp_path)
    character = tavern.create_tavern_character(TavernCharacter(tavern_character_id="mira", project_id="v23_project", display_name="Mira", default_prompt_profile_id="tavern"))
    session = tavern.create_session(TavernSession(session_id="rp1", project_id="v23_project", title="Talk", character_ids=["mira"]))
    memory_service = TavernMemoryService(
        [
            TavernMemoryRecord(memory_id="safe", project_id="v23_project", session_id="rp1", character_ids=["mira"], content="Mira trusts careful wording.", visibility=TavernVisibility.TAVERN_SAFE),
            TavernMemoryRecord(memory_id="debug", project_id="v23_project", session_id="rp1", character_ids=["mira"], content="debug memory text", visibility=TavernVisibility.DEBUG_ONLY),
        ]
    )
    memory_context = memory_service.build_tavern_memory_context(session_id="rp1", character_id="mira")
    assert "debug memory text" not in memory_context.model_dump_json().lower()

    lore_context = TavernLoreContextBuilder(
        lorebook_entries=[
            TavernLorebookEntry(lorebook_entry_id="safe", title="Bell", content="The bell is public.", trigger_keywords=["bell"], linked_fact_ids=["public_fact"]),
            TavernLorebookEntry(lorebook_entry_id="hidden", title="Secret", content="hidden fact text", visibility="hidden", trigger_keywords=["bell"]),
            TavernLorebookEntry(lorebook_entry_id="unknown", title="Unknown", content="NPC unknown fact", trigger_keywords=["bell"], linked_fact_ids=["unknown_fact"]),
        ],
        memory_context=memory_context,
        npc_known_fact_ids={"public_fact"},
    ).build(project_id="v23_project", session_id="rp1", character_id="mira", recent_user_message="bell", scene_context=session.scene_context)
    lore_payload = lore_context.model_dump_json().lower()
    assert "the bell is public" in lore_payload
    assert "hidden fact text" not in lore_payload
    assert "npc unknown fact" not in lore_payload

    preset = SceneMoodPreset(preset_id="quiet", name="Quiet", narration_style="soft")
    relation_state = RelationshipState(id="mira_player", source_id="mira", target_id="player", relation_type="trust", trust=10, affinity=5)
    relation_before = relation_state.model_copy(deep=True)
    tone = RelationshipToneService().derive_tone_from_world_relationship_safe(relation_state.model_dump(mode="json"))
    assert tone is not None
    assert relation_state == relation_before

    profiles = PromptProfileLibrary(project_id="v23_project", profiles={"tavern": ProjectPromptProfile(profile_id="tavern", mode_scopes=["tavern"], rp_style="gentle")})
    context = TavernPromptContextBuilder(profiles).build(session=session, character=character, scene_mood=preset, relationship_tone=tone, lore_context=lore_context)
    context_payload = context.model_dump_json().lower()
    assert "hidden fact" not in context_payload
    assert "debug memory text" not in context_payload
    assert "state_delta" not in context_payload

    state = GameState(world_id="v23_world", player=PlayerState(location_id="square"), locations={"square": LocationState(id="square", name="Square")})
    before = state.model_copy(deep=True)
    event_log = EventLog()
    fake_provider = FakeLLMProvider(json_responses=[GeneratedTavernReply(content="Safe RP reply", speaker_id="mira", safety_notes=["fake provider"]).model_dump(mode="json")])
    reply = TavernResponseGenerationService(fake_provider).generate_character_reply(context)
    assert reply.content == "Safe RP reply"
    chat = SingleCharacterChatService(tavern, TavernResponseGenerationService(FakeLLMProvider(json_responses=[GeneratedTavernReply(content="Stored reply", speaker_id="mira").model_dump(mode="json")])))
    assert chat.chat(project_id="v23_project", session_id="rp1", user_message="hello", character_id="mira").content == "Stored reply"
    assert state == before
    assert event_log.list_events() == []


def test_v23_cross_mode_proposals_adapter_links_quality_and_v22_novel_regression(tmp_path: Path) -> None:
    _, tavern, novel = _project(tmp_path)
    novel.create_manuscript(NovelManuscript(project_id="v23_project", manuscript_id="ms", title="Novel Still Works"))
    novel.create_chapter(NovelChapter(project_id="v23_project", manuscript_id="ms", chapter_id="ch1", title="Opening", order_index=0, draft_text="Safe text"))
    assert novel.load_manuscript("ms").title == "Novel Still Works"

    links = CrossModeLinkRegistry(project_id="v23_project")
    message = TavernMessage(message_id="m1", session_id="rp1", speaker_type=TavernSpeakerType.USER, content="We made a deal.")
    proposal_service = TavernToWorldProposalService(tavern, links)
    proposal = proposal_service.create_proposal_from_message(project_id="v23_project", session_id="rp1", message=message, proposal_type=TavernWorldProposalType.PROMISE_OR_DEAL, proposed_content={"summary": "safe deal"}, target_world_refs=["quest:deal"], create_link=True)
    assert proposal_service.validate_proposal(proposal).ok
    assert links.links
    assert not (Path(tavern.project_root) / "world" / "content_pack" / "facts.yaml").exists()
    invalid = proposal.model_copy(update={"target_world_refs": ["../facts.yaml"]})
    assert not proposal_service.validate_proposal(invalid).ok

    state = GameState(
        world_id="v23_world",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Square")},
        player_visible_facts={"public"},
        facts={"secret": FactState(id="secret", text="hidden fact text", visibility=FactVisibility.HIDDEN, known_by={"harlan"})},
        npcs={"harlan": NPCState(id="harlan", location_id="square", knowledge=["secret"], secrets=["npc secret"], rp_profile=RPProfile(public_persona="Public persona", private_self_summary="private note"), voice_profile=VoiceProfile(tone="dry"))},
    )
    before = state.model_copy(deep=True)
    adapted = WorldNpcToTavernAdapterService().adapt(project_id="v23_project", world_id="v23_world", npc=state.npcs["harlan"], mode="player_safe", player_visible_fact_ids=state.player_visible_facts)
    adapted_payload = json.dumps(adapted.safe_summary(), ensure_ascii=False).lower()
    assert "npc secret" not in adapted_payload
    assert "private note" not in adapted_payload
    assert state == before

    gate = run_project_quality_gate(tavern.project_root)
    assert any(check.check_id == "tavern_boundary_gate" for check in gate.checks)
    assert any(check.check_id == "novel_quality_gate" for check in gate.checks)


def test_v23_tavern_boundary_eval_suite_redacts_and_detects_failures() -> None:
    hidden = "the secret bridge is under the chapel"
    report = run_tavern_boundary_evals(
        [
            TavernBoundaryEvalCase(id="safe", rule=TavernBoundaryRule.SAFE_TAVERN_CONTEXT, payload={"prompt": "safe"}, should_pass=True),
            TavernBoundaryEvalCase(id="hidden", rule=TavernBoundaryRule.NO_HIDDEN_FACT_PROMPT_LEAK, payload={"prompt": hidden}, forbidden_terms=[hidden], expected_issue_codes=["hidden_fact_prompt_leak"]),
            TavernBoundaryEvalCase(id="state_delta", rule=TavernBoundaryRule.NO_RAW_STATE_DELTAS, payload={"prompt": "raw state_delta: relationships.x.trust"}, expected_issue_codes=["raw_state_delta_leak"]),
            TavernBoundaryEvalCase(id="mutation", rule=TavernBoundaryRule.NO_GAMESTATE_MUTATION, state_before=GameState(world_id="a"), state_after=GameState(world_id="b"), expected_issue_codes=["direct_gamestate_mutation"]),
        ]
    )
    assert report.failed == 0
    assert hidden not in json.dumps(report.model_dump_normal(), ensure_ascii=False)
    assert run_default_tavern_boundary_evals().failed == 0
