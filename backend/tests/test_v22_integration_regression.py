from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import Event, EventLog
from app.core.state_delta import StateDelta
from app.core.world_state import GameState
from app.llm.fake_provider import FakeLLMProvider
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.novel_studio import (
    CharacterArc,
    CharacterArcService,
    ChapterDraftImportProposal,
    EventLogToNovelDraftService,
    ForeshadowingItem,
    ForeshadowingService,
    GeneratedNovelDraft,
    NovelChapter,
    NovelConsistencyChecker,
    NovelDraftGenerationService,
    NovelExportRequest,
    NovelExportService,
    NovelManuscript,
    NovelPromptContextBuilder,
    NovelQualityEvalCase,
    NovelQualityEvaluator,
    NovelRepository,
    NovelScene,
    NovelTimelineService,
    NovelToWorldDraftService,
    NovelWorldBibleContextBuilder,
    NovelWorldBibleContextRequest,
    OutlineService,
    PlotThread,
    PlotThreadService,
)
from app.platform.project_repository import ProjectRepository
from app.platform.shared_libraries import (
    CharacterLibrary,
    CharacterProfile,
    CrossModeLinkRegistry,
    ProjectPromptProfile,
    PromptProfileLibrary,
    TimelineEvent,
    TimelineLibrary,
    WorldBible,
    WorldBibleEntry,
    WorldBibleEntryType,
)
from app.quality.project_gate import run_project_quality_gate


def _project(tmp_path: Path) -> tuple[ProjectRepository, NovelRepository]:
    repository = ProjectRepository(tmp_path / "projects")
    project = repository.create_project(
        NarrativeProject(project_id="v22_project", name="v2.2 Project", project_root=str(tmp_path / "projects" / "v22_project"))
    )
    return repository, NovelRepository(project.project_root)


def _seed(repo: NovelRepository) -> tuple[NovelManuscript, NovelChapter, NovelScene]:
    manuscript = repo.create_manuscript(NovelManuscript(project_id="v22_project", manuscript_id="ms", title="The Mist Book"))
    chapter = repo.create_chapter(NovelChapter(project_id="v22_project", manuscript_id="ms", chapter_id="ch1", title="Opening", order_index=0, draft_text="Opening safe text."))
    scene = repo.create_scene(NovelScene(project_id="v22_project", chapter_id="ch1", scene_id="sc1", title="Bridge", draft_text="Bridge safe text."))
    repo.save_chapter(chapter.model_copy(update={"scene_refs": ["sc1"]}))
    return manuscript, chapter, scene


def test_v22_core_repository_api_and_disabled_gate(tmp_path: Path) -> None:
    project_repository, repo = _project(tmp_path)
    manuscript, chapter, scene = _seed(repo)

    assert repo.load_manuscript("ms").title == manuscript.title
    assert repo.load_chapter("ch1").chapter_id == chapter.chapter_id
    assert repo.list_scenes()[0].scene_id == scene.scene_id
    with pytest.raises(ValueError):
        repo._path("chapters", "../escape")

    app.state.project_repository = project_repository
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, llm_provider="mock")
    if hasattr(app.state, "project_session_stores"):
        delattr(app.state, "project_session_stores")
    client = TestClient(app)
    assert client.get("/projects/v22_project/novel/manuscripts").status_code == 200
    assert client.post("/projects/v22_project/novel/chapters", json={"chapter_id": "ch2", "manuscript_id": "ms", "title": "Two"}).status_code == 200
    assert client.post("/projects/v22_project/novel/scenes", json={"scene_id": "sc2", "chapter_id": "ch2", "title": "Second Scene"}).status_code == 200
    response_text = json.dumps(client.get("/projects/v22_project/novel/manuscripts").json()).lower()
    assert "api_key" not in response_text
    assert "hidden fact text" not in response_text

    app.state.settings = Settings(enable_authoring_api=False, llm_provider="mock")
    disabled = client.get("/projects/v22_project/novel/manuscripts")
    assert disabled.status_code in {403, 404}


def test_v22_frontend_shell_static_contract() -> None:
    app_source = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    api_source = Path("frontend/src/api.ts").read_text(encoding="utf-8")
    assert "Novel Studio MVP" in app_source
    assert "Create Manuscript" in app_source
    assert "Chapter Editor" in app_source
    assert "Structure Tools" in app_source
    assert "fetchNovelManuscripts" in api_source
    assert "createNovelChapter" in api_source
    assert "exportNovelManuscript" in api_source
    assert "hidden fact text" not in app_source.lower()


def test_v22_structure_timeline_worldbible_prompt_and_generation_boundaries(tmp_path: Path) -> None:
    _, repo = _project(tmp_path)
    manuscript, chapter, scene = _seed(repo)
    state = GameState(world_id="mist_valley")
    before_state = state.model_dump(mode="json")

    characters = CharacterLibrary(project_id="v22_project", characters={"mira": CharacterProfile(character_id="mira", name="Mira")})
    with pytest.raises(ValueError):
        CharacterArcService(repo, characters).create_arc(CharacterArc(arc_id="arc1", project_id="v22_project", character_id="missing", title="Missing"))

    repo.save_scene(NovelScene(project_id="v22_project", chapter_id="ch1", scene_id="sc0", title="Earlier"))
    foreshadowing = ForeshadowingService(repo).create_item(ForeshadowingItem(foreshadowing_id="f1", setup_scene_id="sc1", payoff_scene_id="sc0", hint_text="Safe hint", hidden_truth_ref="secret"))
    assert foreshadowing.safe_summary()["hidden_truth_ref"] == "[hidden-ref]"
    consistency = NovelConsistencyChecker(repo).check("ms")
    assert "payoff_before_setup" in {issue.code for issue in consistency.issues}

    timeline = TimelineLibrary(project_id="v22_project")
    timeline.add_timeline_event(TimelineEvent(timeline_event_id="t1", project_id="v22_project", title="Public event", event_type="world", visibility="public"))
    timeline.add_timeline_event(TimelineEvent(timeline_event_id="t_hidden", project_id="v22_project", title="Hidden event", description="hidden fact text", visibility="hidden"))
    links = CrossModeLinkRegistry(project_id="v22_project")
    linked = NovelTimelineService(repo, timeline, links).link_scene_to_timeline_event("sc1", "t1", create_cross_mode_link=True)
    assert "t1" in linked.timeline_event_refs
    assert links.links
    assert "hidden fact text" not in NovelTimelineService(repo, timeline).build_novel_timeline_summary("ms").model_dump_json().lower()

    bible = WorldBible(world_bible_id="bible", project_id="v22_project", title="Bible", flavor_lore=["safe lore"])
    bible.entries["hidden"] = WorldBibleEntry(id="hidden", title="Hidden", content="hidden fact text", entry_type=WorldBibleEntryType.HIDDEN, visibility="hidden")
    novel_context = NovelWorldBibleContextBuilder(bible).build(NovelWorldBibleContextRequest(project_id="v22_project", manuscript_id="ms"))
    assert "safe lore" in novel_context.model_dump_json().lower()
    assert "hidden fact text" not in novel_context.model_dump_json().lower()

    profiles = PromptProfileLibrary(project_id="v22_project", profiles={"novel": ProjectPromptProfile(profile_id="novel", mode_scopes=["novel"], novel_style="quiet")})
    prompt_context = NovelPromptContextBuilder(profiles, characters).build(manuscript=manuscript.model_copy(update={"default_prompt_profile_id": "novel"}), chapter=chapter.model_copy(update={"linked_character_ids": ["mira"]}), scene=scene, world_bible_context=novel_context)
    assert prompt_context.prompt_profile_id == "novel"
    with pytest.raises(ValueError):
        ProjectPromptProfile(profile_id="bad", mode_scopes=["novel"], can_modify_state=True)  # type: ignore[arg-type]

    provider = FakeLLMProvider(json_responses=[GeneratedNovelDraft(text="Draft from fake provider", summary="Safe").model_dump(mode="json")])
    draft = NovelDraftGenerationService(provider).generate_scene_draft(prompt_context)
    assert draft.text == "Draft from fake provider"
    assert state.model_dump(mode="json") == before_state


def test_v22_export_cross_mode_eventlog_quality_and_world_mode_boundaries(tmp_path: Path) -> None:
    project_repository, repo = _project(tmp_path)
    manuscript, chapter, scene = _seed(repo)
    state = GameState(world_id="mist_valley")
    before_state = state.model_dump(mode="json")

    repo.save_chapter(chapter.model_copy(update={"authoring_notes": "private note", "draft_text": "Safe chapter text"}))
    markdown = NovelExportService(repo).export(NovelExportRequest(manuscript_id="ms", format="markdown"))
    txt = NovelExportService(repo).export(NovelExportRequest(manuscript_id="ms", format="txt"))
    assert Path(markdown.path).read_text(encoding="utf-8").startswith("# The Mist Book")
    assert "private note" not in Path(markdown.path).read_text(encoding="utf-8")
    assert "api_key" not in Path(txt.path).read_text(encoding="utf-8").lower()

    thread = PlotThreadService(repo).create_thread(PlotThread(plot_thread_id="quest1", title="Quest", description="Safe quest"))
    draft = NovelToWorldDraftService(repo).convert_plot_thread(thread)
    assert draft.draft_type == "quest"
    assert not (Path(repo.project_root) / "world" / "content_pack" / "quest1.yaml").exists()

    event_log = EventLog()
    event_log.append(
        Event(
            event_id="e1",
            turn=1,
            actor_id="player",
            action_type="wait",
            result="visible",
            visible_to_player=True,
            visible_summary="The bell rang.",
                state_deltas=[StateDelta(operation="set", path="turn", value=1)],
        )
    )
    event_log.append(
        Event(
            event_id="e2",
            turn=2,
            actor_id="system",
            action_type="debug",
            result="hidden",
            visible_to_player=False,
            debug_summary="hidden fact text",
            allow_empty_delta=True,
        )
    )
    importer = EventLogToNovelDraftService(repo)
    proposal = importer.preview_import(event_log, turn_start=1, turn_end=2)
    assert proposal.source_event_ids == ["e1"]
    assert proposal.hidden_events_excluded_count == 1
    assert "state_delta" not in proposal.model_dump_json().lower()
    with pytest.raises(ValueError):
        importer.apply_import(ChapterDraftImportProposal(**proposal.model_dump(mode="json")), "ch1")
    importer.apply_import(ChapterDraftImportProposal(**proposal.model_dump(mode="json")), "ch1", explicit_confirm=True, overwrite=True)
    assert state.model_dump(mode="json") == before_state

    quality = NovelQualityEvaluator(NovelConsistencyChecker(repo)).run(NovelQualityEvalCase(case_id="case1", project_id="v22_project", manuscript_id="ms"))
    assert quality.status in {"pass", "warning", "fail"}
    gate = run_project_quality_gate(repo.project_root)
    assert any(check.check_id == "novel_quality_gate" for check in gate.checks)

    app.state.project_repository = project_repository
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, llm_provider="mock")
    client = TestClient(app)
    world_start = client.post("/projects/v22_project/world/start", json={"world_id": "mist_valley"})
    assert world_start.status_code == 200
    payload = world_start.json()
    assert "hidden_facts" not in json.dumps(payload).lower()
    stores = app.state.project_session_stores
    loop = next(store.get_session(payload["session_id"]) for store in stores.values())
    result = loop.step("wait")
    assert result.event is not None
    assert loop.event_log.list_events()
