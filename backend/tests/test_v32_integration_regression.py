from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import EventLog
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactState, FactVisibility, GameState, LocationState, NPCState, PlayerState, RPProfile, VoiceProfile
from app.llm.fake_provider import FakeLLMProvider
from app.main import app
from app.platform.cross_mode import CrossModeDirection, CrossModeProposal, CrossModeRepository, TavernToNovelPipeline, TavernToWorldApplyService
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository
from app.platform.tavern_studio import (
    GeneratedTavernReply,
    TavernCharacter,
    TavernMemoryRecord,
    TavernMemoryService,
    TavernMessage,
    TavernPromptContextBuilder,
    TavernRepository,
    TavernRPProfile,
    TavernSession,
    TavernSpeakerType,
    TavernToWorldProposalService,
    TavernVisibility,
    TavernVoiceProfile,
    TavernWorldProposalType,
    WorldNpcToTavernAdapterService,
)


def _client(tmp_path: Path) -> tuple[TestClient, ProjectRepository, TavernRepository]:
    repo = ProjectRepository(tmp_path)
    project = NarrativeProject(project_id="demo", name="Demo", project_root=str(tmp_path / "demo"))
    repo.save_project(project)
    tavern = TavernRepository(Path(project.project_root))
    tavern.create_tavern_character(
        TavernCharacter(
            tavern_character_id="mira",
            project_id="demo",
            display_name="Mira",
            description="A careful local guide.",
            rp_profile_id="rp_mira",
            voice_profile_id="voice_mira",
        )
    )
    tavern.create_session(TavernSession(session_id="s1", project_id="demo", title="Safe Session", character_ids=["mira"]))
    tavern.append_message(TavernMessage(message_id="m1", session_id="s1", speaker_type=TavernSpeakerType.USER, speaker_id="player", content="hello"))
    tavern.append_message(TavernMessage(message_id="hidden", session_id="s1", speaker_type=TavernSpeakerType.SYSTEM, content="hidden fact text", visibility=TavernVisibility.HIDDEN))
    tavern.append_message(TavernMessage(message_id="mature", session_id="s1", speaker_type=TavernSpeakerType.SYSTEM, content="mature_only private memory", visibility=TavernVisibility.MATURE_ONLY))
    app.state.project_repository = repo
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    app.state.v28_multi_scenes = {}
    app.state.tavern_llm_provider = FakeLLMProvider(
        json_responses=[
            GeneratedTavernReply(content="Provider gateway chat reply.", speaker_id="mira", safety_notes=["mock"]).model_dump(mode="json"),
            GeneratedTavernReply(content="Provider gateway multi reply.", speaker_id="mira", safety_notes=["mock"]).model_dump(mode="json"),
        ]
    )
    return TestClient(app), repo, tavern


def test_v32_tavern_api_provider_and_mature_boundaries(tmp_path: Path) -> None:
    client, _, tavern = _client(tmp_path)

    characters = client.get("/projects/demo/tavern/characters")
    assert characters.status_code == 200
    assert characters.json()["characters"][0]["display_name"] == "Mira"

    sessions = client.get("/projects/demo/tavern/sessions")
    assert sessions.status_code == 200
    assert sessions.json()["sessions"][0]["title"] == "Safe Session"

    messages = client.get("/projects/demo/tavern/sessions/s1/messages")
    assert messages.status_code == 200
    payload = json.dumps(messages.json(), ensure_ascii=False).lower()
    assert "hello" in payload
    assert "hidden fact text" not in payload
    assert "mature_only" not in payload

    rp_profile = TavernRPProfile(rp_profile_id="rp_mira", tavern_character_id="mira", public_persona="Public guide.", private_persona_authoring_only="private persona text")
    voice_profile = TavernVoiceProfile(voice_profile_id="voice_mira", tone="dry", catchphrases=["Careful now"])
    profile_payload = json.dumps({"rp": rp_profile.safe_summary(), "voice": voice_profile.safe_summary()}, ensure_ascii=False).lower()
    assert "private persona text" not in profile_payload
    assert "dry" in profile_payload

    memory_context = TavernMemoryService(
        [
            TavernMemoryRecord(memory_id="safe", project_id="demo", session_id="s1", character_ids=["mira"], content="Mira likes concise replies.", visibility=TavernVisibility.TAVERN_SAFE),
            TavernMemoryRecord(memory_id="hidden", project_id="demo", session_id="s1", character_ids=["mira"], content="hidden fact text", visibility=TavernVisibility.HIDDEN),
            TavernMemoryRecord(memory_id="mature", project_id="demo", session_id="s1", character_ids=["mira"], content="mature_only private memory", visibility=TavernVisibility.MATURE_ONLY),
        ]
    ).build_tavern_memory_context(session_id="s1", character_id="mira")
    assert "hidden fact text" not in memory_context.model_dump_json().lower()
    assert "mature_only" not in memory_context.model_dump_json().lower()

    prompt_context = TavernPromptContextBuilder().build(
        session=tavern.load_session("s1"),
        character=tavern.load_tavern_character("mira"),
        rp_profile=rp_profile,
        voice_profile=voice_profile,
    )
    context_payload = prompt_context.model_dump_json().lower()
    assert "hidden fact" not in context_payload
    assert "npc secret" not in context_payload
    assert "api_key" not in context_payload

    chat = client.post("/projects/demo/tavern/sessions/s1/chat", json={"user_message": "reply please", "character_id": "mira"})
    assert chat.status_code == 200
    assert chat.json()["content"] == "Provider gateway chat reply."

    scene = client.post("/projects/demo/tavern/multi-scenes", json={"scene_id": "scene1", "session_id": "s1", "character_ids": ["mira"], "scene_context": {"scene_summary": "Safe scene."}})
    assert scene.status_code == 200
    multi = client.post("/projects/demo/tavern/multi-scenes/scene1/next-reply")
    assert multi.status_code == 200
    assert multi.json()["message"]["content"] == "Provider gateway multi reply."
    assert "api_key" not in json.dumps(multi.json()).lower()


def test_v32_tavern_provider_failure_and_errors_remain_safe(tmp_path: Path) -> None:
    client, _, _ = _client(tmp_path)
    app.state.tavern_llm_provider = FakeLLMProvider(json_responses=[])

    scene = client.post(
        "/projects/demo/tavern/multi-scenes",
        json={"scene_id": "scene_fallback", "session_id": "s1", "character_ids": ["mira"], "scene_context": {"scene_summary": "Safe scene."}},
    )
    assert scene.status_code == 200
    multi = client.post("/projects/demo/tavern/multi-scenes/scene_fallback/next-reply")
    assert multi.status_code == 200
    fallback_payload = json.dumps(multi.json(), ensure_ascii=False).lower()
    assert "i will stay within what i know" in fallback_payload
    assert "api_key" not in fallback_payload
    assert "state_delta" not in fallback_payload

    rejected = client.post(
        "/projects/demo/tavern/recovery",
        json={"record_id": "bad", "target_type": "message", "target_id": "s1", "safe_draft_text": "sk-real-looking-secret"},
    )
    assert rejected.status_code == 400
    assert rejected.json()["detail"] == "Invalid Tavern recovery payload"
    assert "sk-real-looking-secret" not in rejected.text
    assert str(tmp_path).lower() not in rejected.text.lower()

    missing = client.post("/projects/demo/tavern/recovery/missing/restore", json={"explicit_confirm": True})
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Tavern recovery record not found"
    assert str(tmp_path).lower() not in missing.text.lower()


def test_v32_cross_mode_export_and_world_boundaries(tmp_path: Path) -> None:
    client, project_repo, tavern = _client(tmp_path)
    project_root = Path(project_repo.load_project("demo").project_root)
    state = GameState(
        world_id="demo",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Square")},
        player_visible_facts={"public"},
        facts={"secret": FactState(id="secret", text="hidden fact text", visibility=FactVisibility.HIDDEN, known_by={"harlan"})},
        npcs={"harlan": NPCState(id="harlan", location_id="square", knowledge=["secret"], secrets=["npc secret"], rp_profile=RPProfile(public_persona="A smith.", private_self_summary="private npc fear"), voice_profile=VoiceProfile(tone="dry"))},
    )
    before = state.model_copy(deep=True)

    adapter = WorldNpcToTavernAdapterService().adapt(project_id="demo", world_id="demo", npc=state.npcs["harlan"], mode="player_safe", player_visible_fact_ids=state.player_visible_facts)
    adapter_payload = json.dumps(adapter.safe_summary(), ensure_ascii=False).lower()
    assert "npc secret" not in adapter_payload
    assert "private npc fear" not in adapter_payload
    assert "hidden fact text" not in adapter_payload
    assert state == before

    message = tavern.append_message(TavernMessage(message_id="proposal_src", session_id="s1", speaker_type=TavernSpeakerType.USER, content="I promise to help."))
    proposal = TavernToWorldProposalService(tavern).create_proposal_from_message(
        project_id="demo",
        session_id="s1",
        message=message,
        proposal_type=TavernWorldProposalType.PROMISE_OR_DEAL,
        proposed_content={"summary": "A promise was made."},
        target_world_refs=["relationship:mira:player"],
    )
    assert TavernToWorldProposalService(tavern).validate_proposal(proposal).ok
    assert state == before

    cross_mode = CrossModeRepository(project_root)
    cm_proposal = cross_mode.create_proposal(CrossModeProposal(proposal_id="tp1", project_id="demo", draft_id="d1", direction=CrossModeDirection.TAVERN_TO_WORLD, validation_status="valid"))
    apply_service = TavernToWorldApplyService(cross_mode)
    plan = apply_service.build_apply_plan(cm_proposal)
    with pytest.raises(ValueError):
        apply_service.apply_confirmed(plan, explicit_confirm=False, state=state, event_log=EventLog(), state_deltas=[])
    dry = apply_service.dry_run_apply(plan)
    assert dry.dry_run_result["writes"] == 0
    assert state == before

    delta = StateDelta(operation=StateDeltaOperation.SET, path="facts.public2", value=FactState(id="public2", text="Safe public fact", visibility=FactVisibility.PUBLIC).model_dump(mode="json"), source="cross_mode")
    event_log = EventLog()
    apply_service.apply_confirmed(plan, explicit_confirm=True, state=state, event_log=event_log, state_deltas=[delta])
    assert "public2" in state.facts
    assert event_log.list_events()[0].event_type == "cross_mode_apply"

    original_refs = list(tavern.load_session("s1").message_refs)
    preview = TavernToNovelPipeline(cross_mode).preview(project_id="demo", session_id="s1", safe_messages=["hello", "mature_only private scene"], target_chapter_id="c1")
    assert preview.direction == CrossModeDirection.TAVERN_TO_NOVEL
    preview_payload = preview.model_dump_json().lower()
    assert "mature_only" not in preview_payload
    assert tavern.load_session("s1").message_refs == original_refs

    export_preview = client.post("/projects/demo/tavern/sessions/export-preview", json={"scope": "current_session", "session_ids": ["s1"], "format": "json_safe"})
    assert export_preview.status_code == 200
    assert export_preview.json()["dry_run"] is True
    exported = client.post("/projects/demo/tavern/sessions/export", json={"scope": "current_session", "session_ids": ["s1"], "format": "json_safe", "explicit_confirm": True})
    assert exported.status_code == 200
    export_payload = json.dumps(exported.json(), ensure_ascii=False).lower()
    assert "hidden fact text" not in export_payload
    assert "npc secret\"" not in export_payload
    assert "mature_only" not in export_payload
    assert "api_key" not in export_payload


def test_v32_frontend_tavern_ui_regression_tokens() -> None:
    root = Path(__file__).resolve().parents[2]
    tavern_ui = (root / "frontend" / "src" / "tavernUi.tsx").read_text(encoding="utf-8")
    app_tsx = (root / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    package_json = (root / "frontend" / "package.json").read_text(encoding="utf-8")
    combined = f"{tavern_ui}\n{app_tsx}\n{package_json}"

    for token in [
        "TavernWorkspaceShell",
        "CharacterCardLibrary",
        "SingleCharacterChatPro",
        "MultiNPCScenePro",
        "RPSafetyDashboardPanel",
        "BoundaryMatureSettingsPanel",
        "Mature Module is disabled by default",
        "API key not shown",
        "NPC secrets excluded",
        "check:v32-tavern-ui",
    ]:
        assert token in combined

    lowered = combined.lower()
    assert 'name="api_key"' not in lowered
    assert "online rp primary entry" not in lowered
    assert "cloud sync primary entry" not in lowered
