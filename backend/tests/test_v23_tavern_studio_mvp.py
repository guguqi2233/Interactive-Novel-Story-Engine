import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import EventLog
from app.core.world_state import FactState, FactVisibility, GameState, LocationState, NPCState, PlayerState, RPProfile, VoiceProfile
from app.evals.tavern_boundary import TavernBoundaryEvalCase, TavernBoundaryRule, evaluate_tavern_boundary_case
from app.llm.fake_provider import FakeLLMProvider
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository
from app.platform.shared_libraries import LoreFactEntry, LoreFactLibrary, ProjectPromptProfile, PromptProfileLibrary, WorldBible, WorldBibleEntry, WorldBibleEntryType
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
    TavernProjectSection,
    TavernRepository,
    TavernResponseGenerationService,
    TavernSession,
    TavernSpeakerType,
    TavernToWorldProposalService,
    TavernVisibility,
    TavernWorldProposalType,
    WorldNpcToTavernAdapterService,
)


def _project_repo(tmp_path: Path) -> ProjectRepository:
    repo = ProjectRepository(tmp_path)
    project = NarrativeProject(project_id="demo", name="Demo", project_root=str(tmp_path / "demo"))
    repo.create_project(project)
    return repo


def test_tavern_schema_repository_and_importer(tmp_path: Path) -> None:
    repo = _project_repo(tmp_path)
    tavern = TavernRepository(repo.load_project("demo").project_root)
    character = tavern.create_tavern_character(TavernCharacter(tavern_character_id="mira", project_id="demo", display_name="Mira"))
    session = tavern.create_session(TavernSession(session_id="s1", project_id="demo", title="Evening", character_ids=["mira"]))
    message = tavern.append_message(TavernMessage(message_id="m1", session_id="s1", speaker_type=TavernSpeakerType.USER, content="hello"))

    assert tavern.load_tavern_character("mira").display_name == character.display_name
    assert tavern.load_session("s1").message_refs == ["m1"]
    assert tavern.list_messages("s1")[0].message_id == message.message_id
    with pytest.raises(ValueError):
        tavern.load_tavern_character("../secret")

    result = CharacterCardImportService().import_card("demo", '{"name":"Harlan","description":"Smith","creator_notes":"private note"}')
    assert result.tavern_character.tavern_character_id == "harlan"
    assert "private note" not in json.dumps(result.safe_summary()).lower()


def test_lore_memory_prompt_generation_and_chat_do_not_leak_or_mutate(tmp_path: Path) -> None:
    repo = _project_repo(tmp_path)
    tavern = TavernRepository(repo.load_project("demo").project_root)
    character = tavern.create_tavern_character(TavernCharacter(tavern_character_id="mira", project_id="demo", display_name="Mira", default_prompt_profile_id="tavern"))
    session = tavern.create_session(TavernSession(session_id="s1", project_id="demo", title="Talk", character_ids=["mira"]))
    memory = TavernMemoryService(
        [
            TavernMemoryRecord(memory_id="safe", project_id="demo", session_id="s1", character_ids=["mira"], content="Mira prefers careful answers.", visibility=TavernVisibility.TAVERN_SAFE),
            TavernMemoryRecord(memory_id="hidden", project_id="demo", session_id="s1", character_ids=["mira"], content="hidden fact text", visibility=TavernVisibility.HIDDEN),
        ]
    ).build_tavern_memory_context(session_id="s1", character_id="mira")
    bible = WorldBible(world_bible_id="bible", project_id="demo", title="Bible")
    bible.entries["flavor"] = WorldBibleEntry(id="flavor", title="Mist", content="The valley is misty.", entry_type=WorldBibleEntryType.FLAVOR)
    bible.entries["hidden"] = WorldBibleEntry(id="hidden", title="Hidden", content="hidden fact text", entry_type=WorldBibleEntryType.HIDDEN, visibility="hidden")
    lore = LoreFactLibrary(project_id="demo")
    lore.add_draft_lore(LoreFactEntry(id="public", project_id="demo", title="Bell", text="The bell is old.", fact_type="flavor", safe_for_tavern=True))
    lore.add_draft_lore(LoreFactEntry(id="secret", project_id="demo", title="Secret", text="hidden fact text", fact_type="hidden", visibility="hidden", safe_for_tavern=True))
    lore_context = TavernLoreContextBuilder(
        lorebook_entries=[TavernLorebookEntry(lorebook_entry_id="entry", title="Forge", content="The forge is warm.", trigger_keywords=["forge"])],
        world_bible=bible,
        lore_facts=lore,
        memory_context=memory,
    ).build(project_id="demo", session_id="s1", character_id="mira", recent_user_message="forge", scene_context=session.scene_context)
    assert "hidden fact text" not in lore_context.model_dump_json().lower()

    profiles = PromptProfileLibrary(project_id="demo", profiles={"tavern": ProjectPromptProfile(profile_id="tavern", mode_scopes=["tavern"], rp_style="warm but concise")})
    context = TavernPromptContextBuilder(profiles).build(session=session, character=character, project_section=TavernProjectSection(default_prompt_profile_id="tavern"), lore_context=lore_context)
    assert context.prompt_profile_id == "tavern"
    assert "hidden fact text" not in context.model_dump_json().lower()
    with pytest.raises(ValueError):
        ProjectPromptProfile(profile_id="bad", mode_scopes=["tavern"], can_access_hidden_facts=True)  # type: ignore[arg-type]

    state = GameState(world_id="demo", player=PlayerState(location_id="square"), locations={"square": LocationState(id="square", name="Square")})
    before = state.model_copy(deep=True)
    event_log = EventLog()
    provider = FakeLLMProvider(json_responses=[GeneratedTavernReply(content="A safe reply.", speaker_id="mira", safety_notes=["safe"]).model_dump(mode="json")])
    draft = TavernResponseGenerationService(provider).generate_character_reply(context)
    assert draft.content == "A safe reply."
    service = SingleCharacterChatService(tavern, TavernResponseGenerationService(FakeLLMProvider(json_responses=[GeneratedTavernReply(content="Chat reply.", speaker_id="mira").model_dump(mode="json")])))
    response = service.chat(project_id="demo", session_id="s1", user_message="hello", character_id="mira")
    assert response.content == "Chat reply."
    assert state == before
    assert event_log.list_events() == []


def test_scene_mood_relationship_proposal_and_adapter_are_style_or_draft_only(tmp_path: Path) -> None:
    repo = _project_repo(tmp_path)
    tavern = TavernRepository(repo.load_project("demo").project_root)
    preset = tavern.save_scene_mood_preset(SceneMoodPreset(preset_id="quiet", name="Quiet", mood_tags=["soft"], narration_style="spare"))
    assert preset.safe_summary()["narration_style"] == "spare"
    with pytest.raises(ValueError):
        SceneMoodPreset(preset_id="bad", name="Bad", narration_style="can_modify_state")

    memory = TavernMemoryRecord(memory_id="rel", project_id="demo", session_id="s1", character_ids=["a", "b"], memory_type="relationship", content="They trust each other.", visibility=TavernVisibility.TAVERN_SAFE)
    tone = RelationshipToneService().derive_tone_from_tavern_memory([memory], "a", "b")
    proposal = RelationshipToneService().propose_tone_change(tone, {"trust_band": "high"})
    assert proposal.modifies_world_state is False

    message = TavernMessage(message_id="m1", session_id="s1", speaker_type=TavernSpeakerType.USER, content="I promise to help.")
    world_proposal = TavernToWorldProposalService(tavern).create_proposal_from_message(project_id="demo", session_id="s1", message=message, proposal_type=TavernWorldProposalType.RELATIONSHIP_CHANGE, proposed_content={"summary": "promise"}, target_world_refs=["relationship:a:b"])
    assert TavernToWorldProposalService(tavern).validate_proposal(world_proposal).ok
    assert not (Path(repo.load_project("demo").project_root) / "world" / "content_pack" / "facts.yaml").exists()

    state = GameState(
        world_id="demo",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Square")},
        player_visible_facts={"public"},
        facts={"secret": FactState(id="secret", text="hidden fact text", visibility=FactVisibility.HIDDEN, known_by={"harlan"})},
        npcs={"harlan": NPCState(id="harlan", location_id="square", knowledge=["secret"], secrets=["npc secret"], rp_profile=RPProfile(public_persona="A smith.", private_self_summary="hidden fear"), voice_profile=VoiceProfile(tone="dry"))},
    )
    before = state.model_copy(deep=True)
    adapted = WorldNpcToTavernAdapterService().adapt(project_id="demo", world_id="demo", npc=state.npcs["harlan"], mode="player_safe", player_visible_fact_ids=state.player_visible_facts)
    payload = json.dumps(adapted.safe_summary(), ensure_ascii=False).lower()
    assert "npc secret" not in payload
    assert "hidden fear" not in payload
    assert "secret" not in adapted.tavern_character.lorebook_refs
    assert state == before


def test_tavern_api_enabled_and_disabled(tmp_path: Path) -> None:
    project_repo = _project_repo(tmp_path)
    app.state.project_repository = project_repo
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)

    created = client.post("/projects/demo/tavern/characters", json={"tavern_character_id": "mira", "display_name": "Mira"})
    assert created.status_code == 200
    assert "api" not in created.text.lower()
    session = client.post("/projects/demo/tavern/sessions", json={"session_id": "s1", "title": "Talk", "character_ids": ["mira"]})
    assert session.status_code == 200
    messages = client.post("/projects/demo/tavern/sessions/s1/messages", json={"message_id": "m1", "speaker_type": "user", "content": "hello"})
    assert messages.status_code == 200
    assert client.get("/projects/demo/tavern/sessions/s1/messages").json()["messages"][0]["content"] == "hello"
    preset = client.post("/projects/demo/tavern/scene-presets", json={"preset_id": "quiet", "name": "Quiet"})
    assert preset.status_code == 200
    proposal = client.post("/projects/demo/tavern/proposals", json={"source_session_id": "s1", "source_message_id": "m1", "proposal_type": "relationship_change", "proposed_content": {"summary": "safe"}, "target_world_refs": ["relationship:mira:player"]})
    assert proposal.status_code == 200

    app.state.settings = Settings(enable_authoring_api=False)
    disabled = client.get("/projects/demo/tavern/characters")
    assert disabled.status_code == 403


def test_tavern_boundary_eval_redacts_hidden_text() -> None:
    hidden = "the hidden heir is under the chapel"
    result = evaluate_tavern_boundary_case(
        TavernBoundaryEvalCase(
            id="hidden_prompt",
            rule=TavernBoundaryRule.NO_HIDDEN_FACT_PROMPT_LEAK,
            payload={"prompt": hidden},
            forbidden_terms=[hidden],
            expected_issue_codes=["hidden_fact_prompt_leak"],
        )
    )
    assert result.passed
    assert hidden not in result.model_dump_json()
