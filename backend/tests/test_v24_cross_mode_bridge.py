import base64
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import Event, EventLog
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactState, FactVisibility, GameState, LocationState, NPCState, PlayerState
from app.main import app
from app.platform.cross_mode import (
    CrossModeApplyPlan,
    CrossModeArtifactStatus,
    CrossModeDirection,
    CrossModeDraft,
    CrossModeProposal,
    CrossModeRepository,
    CrossModeTimelineService,
    WorldTavernSyncService,
    NovelCharacterToTavernPipeline,
    NovelToWorldPipeline,
    TavernToNovelPipeline,
    TavernToWorldApplyService,
    WorldToNovelPipeline,
    validate_cross_mode_project,
)
from app.platform.novel_studio import NovelScene
from app.platform.narrative_project import NarrativeProject
from app.platform.project_packages import export_project, import_project_apply, import_project_dry_run
from app.platform.project_repository import ProjectRepository
from app.platform.shared_libraries import CrossModeLink


def _repo(tmp_path: Path) -> ProjectRepository:
    repo = ProjectRepository(tmp_path)
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(tmp_path / "demo")))
    return repo


def test_cross_mode_schema_repository_validation_and_audit(tmp_path: Path) -> None:
    project_repo = _repo(tmp_path)
    project_root = Path(project_repo.load_project("demo").project_root)
    repo = CrossModeRepository(project_root)
    draft = repo.create_draft(
        CrossModeDraft(
            artifact_id="d1",
            project_id="demo",
            direction=CrossModeDirection.NOVEL_TO_WORLD,
            source_refs=[],
            target_refs=["world:fact:f1"],
            artifact_type="fact_draft",
            proposed_content={"summary": "safe"},
            validation_status="valid",
        )
    )
    proposal = repo.create_proposal(
        CrossModeProposal(
            proposal_id="p1",
            project_id="demo",
            draft_id=draft.artifact_id,
            direction=CrossModeDirection.NOVEL_TO_WORLD,
            target_refs=["world:fact:f1"],
            validation_status="valid",
        )
    )
    plan = repo.save_apply_plan(CrossModeApplyPlan(apply_plan_id="ap1", project_id="demo", proposal_id=proposal.proposal_id))

    assert repo.load_draft("d1").artifact_id == "d1"
    assert repo.load_proposal("p1").proposal_id == "p1"
    assert plan.requires_confirmation is True
    assert repo.list_audit_records()[0].action_type == "create_draft"
    with pytest.raises(ValueError):
        repo.load_draft("../secret")
    assert validate_cross_mode_project(project_root).ok


def test_cross_mode_validation_catches_blockers_and_redacts(tmp_path: Path) -> None:
    project_repo = _repo(tmp_path)
    project_root = Path(project_repo.load_project("demo").project_root)
    repo = CrossModeRepository(project_root)
    repo.save_apply_plan(CrossModeApplyPlan(apply_plan_id="unsafe", project_id="demo", proposal_id="p", requires_confirmation=False))
    (project_root / "cross_mode_links.json").write_text(
        json.dumps(
            [
                CrossModeLink(link_id="hidden", project_id="demo", source_mode="novel", source_ref="missing", target_mode="world", target_ref="missing", link_type="x", hidden=True).model_dump(mode="json"),
                CrossModeLink(link_id="broken", project_id="demo", source_mode="novel", source_ref="missing", target_mode="world", target_ref="missing", link_type="x", status="broken").model_dump(mode="json"),
            ]
        ),
        encoding="utf-8",
    )
    report = validate_cross_mode_project(project_root)
    payload = report.model_dump_json().lower()
    assert not report.ok
    assert "apply_plan_missing_confirmation" in payload
    assert "cross_mode_link_broken" in payload
    assert "cross_mode_hidden_target_risk" in payload
    assert "sk-" not in payload


def test_cross_mode_pipelines_do_not_mutate_world_or_sources(tmp_path: Path) -> None:
    project_repo = _repo(tmp_path)
    project_root = Path(project_repo.load_project("demo").project_root)
    repo = CrossModeRepository(project_root)

    nw = NovelToWorldPipeline(repo).create_draft(project_id="demo", source_ref="character:mira", draft_type="npc_draft")
    assert nw.direction == CrossModeDirection.NOVEL_TO_WORLD
    assert not (project_root / "world" / "content_pack" / "facts.yaml").exists()

    preview = WorldToNovelPipeline(repo).preview(project_id="demo", safe_event_summaries=["The bell rang."], source_event_ids=["e1"], target_chapter_id="c1")
    assert preview.source_event_ids == ["e1"]
    assert "state_delta" not in preview.model_dump_json().lower()

    tn = TavernToNovelPipeline(repo).preview(project_id="demo", session_id="s1", safe_messages=["hello"], target_chapter_id="c1")
    assert tn.direction == CrossModeDirection.TAVERN_TO_NOVEL

    nt = NovelCharacterToTavernPipeline(repo).create_character_draft(project_id="demo", character_profile_id="mira")
    assert nt.direction == CrossModeDirection.NOVEL_TO_TAVERN

    proposal = repo.create_proposal(CrossModeProposal(proposal_id="tp1", project_id="demo", draft_id="d", direction=CrossModeDirection.TAVERN_TO_WORLD, validation_status="valid"))
    service = TavernToWorldApplyService(repo)
    plan = service.build_apply_plan(proposal)
    audit_count = len(repo.list_audit_records())
    dry = service.dry_run_apply(plan)
    assert dry.dry_run_result["writes"] == 0
    assert repo.load_apply_plan(plan.apply_plan_id).dry_run_result == {}
    assert len(repo.list_audit_records()) == audit_count
    with pytest.raises(ValueError):
        service.apply_confirmed(plan, explicit_confirm=False)


def test_tavern_to_world_apply_uses_state_delta_and_event_log(tmp_path: Path) -> None:
    project_repo = _repo(tmp_path)
    project_root = Path(project_repo.load_project("demo").project_root)
    repo = CrossModeRepository(project_root)
    proposal = repo.create_proposal(CrossModeProposal(proposal_id="tp_apply", project_id="demo", draft_id="d", direction=CrossModeDirection.TAVERN_TO_WORLD, validation_status="valid"))
    plan = TavernToWorldApplyService(repo).build_apply_plan(proposal)
    state = GameState(world_id="demo", player=PlayerState(location_id="square"), locations={"square": LocationState(id="square", name="Square")}, facts={"old": FactState(id="old", text="Old", visibility=FactVisibility.PUBLIC)})
    event_log = EventLog()
    before_world_id = state.world_id
    delta = StateDelta(operation=StateDeltaOperation.SET, path="facts.new", value=FactState(id="new", text="New safe fact", visibility=FactVisibility.PUBLIC).model_dump(mode="json"), source="cross_mode")
    record = TavernToWorldApplyService(repo).apply_confirmed(plan, explicit_confirm=True, state=state, event_log=event_log, state_deltas=[delta])

    assert state.world_id == before_world_id
    assert "new" in state.facts
    events = event_log.list_events()
    assert len(events) == 1
    assert events[0].event_type == "cross_mode_apply"
    assert events[0].state_deltas
    assert record.related_event_id == events[0].event_id
    with pytest.raises(ValueError):
        TavernToWorldApplyService(repo).apply_confirmed(plan, explicit_confirm=True, state=state, event_log=event_log, state_deltas=[])


def test_world_to_novel_filters_raw_deltas_and_apply_writes_only_novel(tmp_path: Path) -> None:
    project_repo = _repo(tmp_path)
    project_root = Path(project_repo.load_project("demo").project_root)
    repo = CrossModeRepository(project_root)
    event_log = EventLog(
        [
            Event(event_id="visible", turn=1, actor_id="player", action_type="look", result="ok", visible_to_player=True, allow_empty_delta=True, visible_summary="The forge glows."),
            Event(event_id="hidden", turn=2, actor_id="system", action_type="secret", result="secret", visible_to_player=False, allow_empty_delta=True, debug_summary="hidden truth"),
            Event(event_id="delta_text", turn=3, actor_id="system", action_type="debug", result="state_delta raw", visible_to_player=True, allow_empty_delta=True, visible_summary="raw state_delta dump"),
        ]
    )
    safe = []
    source_ids = []
    excluded = 0
    for event in event_log.list_events():
        if event.visible_to_player and event.visible_summary and "state_delta" not in event.visible_summary.lower():
            safe.append(event.visible_summary)
            source_ids.append(event.event_id)
        else:
            excluded += 1
    preview = WorldToNovelPipeline(repo).preview(project_id="demo", safe_event_summaries=safe, source_event_ids=source_ids, target_chapter_id="c1")
    assert preview.source_event_ids == ["visible"]
    assert excluded == 2
    assert "state_delta" not in preview.model_dump_json().lower()

    from app.platform.novel_studio import NovelRepository

    novel = NovelRepository(project_root)
    saved = novel.save_scene(NovelScene(project_id="demo", scene_id="from_world", chapter_id="c1", title="From World", draft_text=preview.draft_text or ""))
    assert saved.draft_text == "The forge glows."
    assert len(event_log.list_events()) == 3


def test_world_tavern_sync_and_hidden_timeline_boundaries(tmp_path: Path) -> None:
    project_repo = _repo(tmp_path)
    project_root = Path(project_repo.load_project("demo").project_root)
    npc = NPCState(id="harlan", location_id="square", secrets=["npc secret"])
    before = npc.model_copy(deep=True)
    diff = WorldTavernSyncService().compare_world_npc_and_tavern_character(project_id="demo", npc_ref="world:npc:harlan", tavern_character_ref="tavern:character:harlan", mode="player_safe")
    proposal = WorldTavernSyncService().build_sync_proposal(diff)
    assert "hidden truth value" not in diff.model_dump_json().lower()
    assert proposal.direction == "compare_only"
    assert npc == before

    visible_dir = project_root / "novel" / "scenes"
    visible_dir.mkdir(parents=True, exist_ok=True)
    (visible_dir / "safe.yaml").write_text("scene_id: safe\ntitle: Safe\nsummary: visible\nvisibility: normal\nchapter_id: c1\n", encoding="utf-8")
    (visible_dir / "hidden.yaml").write_text("scene_id: hidden\ntitle: Hidden\nsummary: hidden truth\nvisibility: hidden\nchapter_id: c1\n", encoding="utf-8")
    timeline = CrossModeTimelineService(project_root).build_project_timeline()
    payload = timeline.model_dump_json().lower()
    assert "safe" in payload
    assert "hidden truth" not in payload


def test_cross_mode_timeline_quality_gate_and_api(tmp_path: Path) -> None:
    project_repo = _repo(tmp_path)
    app.state.project_repository = project_repo
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, llm_provider="mock")
    client = TestClient(app)

    created = client.post("/projects/demo/cross-mode/novel-to-world/draft", json={"source_ref": "novel:scene:s1", "draft_type": "fact_draft"})
    assert created.status_code == 200
    draft_id = created.json()["artifact_id"]
    assert client.post("/projects/demo/cross-mode/novel-to-world/validate", json={"draft_id": draft_id}).status_code == 200
    assert client.post("/projects/demo/cross-mode/world-to-novel/preview", json={"safe_event_summaries": ["A safe event."], "source_event_ids": ["e1"]}).status_code == 200
    assert client.get("/projects/demo/cross-mode/timeline").status_code == 200
    assert client.post("/projects/demo/cross-mode/validate", json={}).status_code == 200
    gate = client.post("/projects/demo/quality-gate/run?include_cross_mode=true", json={})
    assert gate.status_code == 200
    assert "api_key" not in gate.text.lower()
    assert CrossModeTimelineService(project_repo.load_project("demo").project_root).build_project_timeline().entries


def test_cross_mode_quality_gate_fails_on_blockers_and_provider_secret(tmp_path: Path) -> None:
    project_repo = _repo(tmp_path)
    project_root = Path(project_repo.load_project("demo").project_root)
    repo = CrossModeRepository(project_root)
    repo.save_apply_plan(CrossModeApplyPlan(apply_plan_id="bad", project_id="demo", proposal_id="p", requires_confirmation=False))
    with pytest.raises(ValueError):
        repo.create_draft(CrossModeDraft(artifact_id="secret", project_id="demo", direction=CrossModeDirection.NOVEL_TO_WORLD, artifact_type="fact_draft", proposed_content={"token": "sk-abcdefghijklmnopqrstuvwx"}))
    app.state.project_repository = project_repo
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, llm_provider="mock")
    client = TestClient(app)
    gate = client.post("/projects/demo/quality-gate/run?include_cross_mode=true", json={})
    assert gate.status_code == 200
    assert not gate.json()["passed"]
    assert "sk-abcdefghijklmnopqrstuvwx" not in gate.text


def test_cross_mode_import_export_safety(tmp_path: Path) -> None:
    project_repo = _repo(tmp_path)
    project_root = Path(project_repo.load_project("demo").project_root)
    repo = CrossModeRepository(project_root)
    repo.create_draft(CrossModeDraft(artifact_id="d1", project_id="demo", direction=CrossModeDirection.NOVEL_TO_WORLD, artifact_type="fact_draft", validation_status="valid"))
    exported = export_project("demo", project_repo, sections=["project.yaml", "cross_mode/drafts", "cross_mode/audit"], export_mode="normal")
    raw = base64.b64decode(exported.archive_base64)
    assert b"sk-" not in raw
    assert "cross_mode/drafts/d1.yaml" in exported.manifest.included_sections
    assert import_project_dry_run(exported.archive_base64, tmp_path / "imports", project_repo).ok
    assert not import_project_apply(exported.archive_base64, tmp_path / "imports", project_repo).ok

    bad = BytesIO()
    with ZipFile(bad, "w", ZIP_DEFLATED) as archive:
        archive.writestr("project_package_manifest.json", json.dumps(exported.manifest.model_dump(mode="json")))
        archive.writestr("../evil.yaml", "bad")
    assert not import_project_dry_run(base64.b64encode(bad.getvalue()).decode("ascii"), tmp_path / "bad", project_repo).ok

    with pytest.raises(ValueError):
        export_project("demo", project_repo, export_mode="debug")


def test_validate_cross_mode_cli_and_frontend_contract_smoke(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project_repo = _repo(tmp_path)
    project_root = Path(project_repo.load_project("demo").project_root)
    CrossModeRepository(project_root).create_draft(CrossModeDraft(artifact_id="d1", project_id="demo", direction=CrossModeDirection.NOVEL_TO_WORLD, artifact_type="fact_draft", validation_status="valid"))
    from app.tools.validate_cross_mode import main as validate_main

    assert validate_main([str(project_root), "--json"]) == 0
    output = capsys.readouterr().out
    assert '"ok": true' in output
    assert "api_key" not in output.lower()
