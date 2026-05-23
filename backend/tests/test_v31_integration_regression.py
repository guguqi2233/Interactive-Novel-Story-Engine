from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import Event, EventLog
from app.core.world_state import GameState
from app.llm.provider_base import LLMProvider, Message, SchemaT
from app.llm.provider_gateway import ProviderGateway
from app.llm.provider_router import ProviderRouter, ProviderRoutingConfig, ProviderRoutingContext, ProviderRoutingRule
from app.main import app
from app.platform.cross_mode import CrossModeLink, CrossModeLinkRegistry, CrossModeRepository, NovelToWorldPipeline, WorldToNovelPipeline
from app.platform.narrative_project import NarrativeProject
from app.platform.novel_studio import (
    CharacterArc,
    EventLogToNovelDraftService,
    GeneratedNovelDraft,
    NovelChapter,
    NovelDraftGenerationService,
    NovelExportRequest,
    NovelExportService,
    NovelManuscript,
    NovelPromptContext,
    NovelRepository,
    NovelScene,
    NovelTimelineService,
)
from app.platform.project_repository import ProjectRepository
from app.platform.shared_libraries import TimelineEvent, TimelineLibrary


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"


class RecordingProvider(LLMProvider):
    def __init__(self) -> None:
        self.messages: list[list[Message]] = []

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        self.messages.append(messages)
        return "safe text"

    def generate_json(self, messages: list[Message], schema: type[SchemaT], temperature: float = 0.2) -> SchemaT:
        self.messages.append(messages)
        return schema.model_validate({"text": "Safe novel draft.", "summary": "safe"})


def _project(tmp_path: Path) -> tuple[ProjectRepository, NovelRepository, Path]:
    project_repository = ProjectRepository(tmp_path / "projects")
    project = project_repository.create_project(
        NarrativeProject(project_id="v31_project", name="v3.1 Project", project_root=str(tmp_path / "projects" / "v31_project"))
    )
    repo = NovelRepository(project.project_root)
    repo.create_manuscript(NovelManuscript(project_id="v31_project", manuscript_id="ms", title="Mist Novel"))
    repo.create_chapter(
        NovelChapter(
            project_id="v31_project",
            manuscript_id="ms",
            chapter_id="ch1",
            title="Opening",
            order_index=0,
            draft_text="Safe chapter text.",
            authoring_notes="private authoring note",
            scene_refs=["sc1"],
        )
    )
    repo.create_scene(
        NovelScene(
            project_id="v31_project",
            chapter_id="ch1",
            scene_id="sc1",
            title="Bridge",
            draft_text="Safe scene text.",
            summary="Safe scene summary.",
        )
    )
    return project_repository, repo, Path(project.project_root)


def test_v31_novel_ui_pro_api_regression(tmp_path: Path) -> None:
    project_repository, _, _ = _project(tmp_path)
    app.state.project_repository = project_repository
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, llm_provider="mock")
    client = TestClient(app)

    assert client.get("/projects/v31_project/novel/manuscripts").json()["manuscripts"][0]["manuscript_id"] == "ms"

    outline = client.put(
        "/projects/v31_project/novel/outline",
        json={"outline_id": "outline1", "manuscript_id": "ms", "nodes": [{"node_id": "act1", "node_type": "act", "title": "Act 1"}]},
    )
    assert outline.status_code == 200, outline.text
    tree = client.get("/projects/v31_project/novel/outlines/outline1/tree")
    assert tree.status_code == 200
    assert tree.json()["tree"][0]["node_id"] == "act1"

    assert client.get("/projects/v31_project/novel/chapters").status_code == 200
    assert client.get("/projects/v31_project/novel/scenes").status_code == 200
    assert client.post("/projects/v31_project/novel/arcs", json={"arc_id": "arc1", "character_id": "mira", "title": "Arc"}).status_code == 200
    assert client.post("/projects/v31_project/novel/plot-threads", json={"plot_thread_id": "plot1", "title": "Thread"}).status_code == 200
    assert client.post("/projects/v31_project/novel/foreshadowing", json={"foreshadowing_id": "f1", "setup_scene_id": "sc1", "hint_text": "safe hint", "hidden_truth_ref": "hidden_ref"}).status_code == 200

    search = client.get("/projects/v31_project/novel/search?keyword=safe")
    assert search.status_code == 200
    assert {item["result_type"] for item in search.json()["results"]} >= {"chapter", "scene"}

    snapshot = client.post("/projects/v31_project/novel/draft-snapshots", json={"target_type": "chapter", "target_id": "ch1", "snapshot_id": "snap1"})
    assert snapshot.status_code == 200
    assert snapshot.json()["draft_text"] == "[stored locally]"
    compare = client.post("/projects/v31_project/novel/draft-snapshots/compare", json={"left_snapshot_id": "snap1", "current_text": "changed"})
    assert compare.status_code == 200
    assert "api_key" not in compare.text.lower()


def test_v31_cross_mode_world_fact_boundaries_remain_intact(tmp_path: Path) -> None:
    _, repo, project_root = _project(tmp_path)
    state = GameState(world_id="mist_valley")
    before_state = state.model_dump(mode="json")
    event_log = EventLog()
    event_log.append(Event(event_id="e1", turn=1, actor_id="player", action_type="wait", result="ok", visible_to_player=True, visible_summary="The gate opened.", allow_empty_delta=True))
    event_log.append(Event(event_id="e2", turn=2, actor_id="system", action_type="debug", result="hidden", visible_to_player=False, debug_summary="hidden fact text", allow_empty_delta=True))
    before_events = json.dumps([event.model_dump(mode="json") for event in event_log.list_events()], sort_keys=True)

    proposal = EventLogToNovelDraftService(repo).preview_import(event_log, turn_start=1, turn_end=2)
    assert proposal.source_event_ids == ["e1"]
    assert proposal.hidden_events_excluded_count == 1
    assert "state_delta" not in proposal.model_dump_json().lower()
    assert json.dumps([event.model_dump(mode="json") for event in event_log.list_events()], sort_keys=True) == before_events
    assert state.model_dump(mode="json") == before_state

    cross_mode = CrossModeRepository(project_root)
    draft = NovelToWorldPipeline(cross_mode).create_draft(project_id="v31_project", source_ref="novel:scene:sc1", draft_type="fact_draft")
    assert draft.direction == "novel_to_world"
    assert not (project_root / "world" / "content_pack" / "facts.yaml").exists()

    preview = WorldToNovelPipeline(cross_mode).preview(project_id="v31_project", safe_event_summaries=["Safe event"], source_event_ids=["e1"], target_chapter_id="ch1")
    assert preview.source_event_ids == ["e1"]
    assert "state_delta" not in preview.model_dump_json().lower()

    links = CrossModeLinkRegistry(project_id="v31_project")
    links.create_link(CrossModeLink(link_id="valid", project_id="v31_project", source_mode="novel", source_ref="novel:scene:sc1", target_mode="world", target_ref="world:event:e1", link_type="novel_scene_to_world_event"))
    assert links.validate_link("valid", {"novel:scene:sc1", "world:event:e1"}).ok


def test_v31_timeline_provider_prompt_and_export_privacy(tmp_path: Path) -> None:
    _, repo, _ = _project(tmp_path)
    timeline = TimelineLibrary(project_id="v31_project")
    timeline.add_timeline_event(TimelineEvent(timeline_event_id="public", project_id="v31_project", title="Public event", visibility="public"))
    timeline.add_timeline_event(TimelineEvent(timeline_event_id="hidden", project_id="v31_project", title="Hidden event", description="hidden fact text", visibility="hidden"))
    repo.save_scene(repo.load_scene("sc1").model_copy(update={"timeline_event_refs": ["public", "hidden"]}))
    summary = NovelTimelineService(repo, timeline).build_novel_timeline_summary("ms")
    assert summary.hidden_events_excluded == 1
    assert "hidden fact text" not in summary.model_dump_json().lower()

    provider = RecordingProvider()
    gateway = ProviderGateway(
        {"local_stub": provider},
        router=ProviderRouter(config=ProviderRoutingConfig(rules=[ProviderRoutingRule(use_case="novel_draft", primary_provider_id="local_stub", primary_model_id="local_stub")])),
    )
    novel_provider = gateway.provider_for(ProviderRoutingContext(mode="novel", use_case="novel_draft"))
    service = NovelDraftGenerationService(novel_provider)
    context = NovelPromptContext(project_id="v31_project", manuscript_id="ms", scene_summary="safe visible scene")
    draft = service.generate_scene_draft(context)
    rewrite = service.rewrite_scene_style(context, "safe visible draft")
    summary_draft = service.summarize_chapter(context)
    assert draft.text == "Safe novel draft."
    assert rewrite.text == "Safe novel draft."
    assert summary_draft.text == "Safe novel draft."
    rendered_messages = json.dumps(provider.messages).lower()
    assert "hidden fact text" not in rendered_messages
    assert "api_key" not in rendered_messages
    assert "state_delta" not in rendered_messages

    exported = NovelExportService(repo).export(NovelExportRequest(manuscript_id="ms", format="markdown"))
    text = Path(exported.path).read_text(encoding="utf-8").lower()
    assert "private authoring note" not in text
    assert "hidden_ref" not in text
    assert "mature_only" not in text
    assert "api_key" not in text


def test_v31_frontend_static_regression_surfaces_and_no_onlineization() -> None:
    app_source = (FRONTEND / "src" / "App.tsx").read_text(encoding="utf-8")
    novel_source = (FRONTEND / "src" / "novelUi.tsx").read_text(encoding="utf-8")
    api_source = (FRONTEND / "src" / "api.ts").read_text(encoding="utf-8")
    package_source = (FRONTEND / "package.json").read_text(encoding="utf-8")
    check_source = (FRONTEND / "scripts" / "check-v31-novel-ui.mjs").read_text(encoding="utf-8")
    combined = app_source + novel_source + api_source

    for token in [
        "NovelWorkspaceShell",
        "OutlineTreePro",
        "ChapterEditorPro",
        "SceneCardsBoard",
        "NovelExportWizard",
        "NovelQualityDashboard",
        "NovelPromptProviderPanel",
    ]:
        assert token in combined

    assert "check:v31-novel-ui" in package_source
    assert "Plaintext api_key input" in check_source
    assert not re.search(r"<input[^>]+name=[\"']api_key[\"']", combined, flags=re.IGNORECASE)
    assert "API key not shown" in combined
    assert "raw state_deltas" in combined
    assert "does not directly modify GameState" in combined
    assert not re.search(r"<button[^>]*>\s*(Account|Cloud Sync|Online Publishing|Online Marketplace)\s*</button>", combined, flags=re.IGNORECASE)
