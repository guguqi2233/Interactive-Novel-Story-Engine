from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import Event, EventLog
from app.core.world_state import GameState
from app.llm.fake_provider import FakeLLMProvider
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.novel_studio import (
    ChapterDraftImportProposal,
    ChapterSceneService,
    EventLogToNovelDraftService,
    ForeshadowingItem,
    GeneratedNovelDraft,
    NovelChapter,
    NovelConsistencyChecker,
    NovelDraftGenerationService,
    NovelExportRequest,
    NovelExportService,
    NovelManuscript,
    NovelOutline,
    NovelOutlineNode,
    NovelPromptContextBuilder,
    NovelRepository,
    NovelScene,
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
    LoreFactEntry,
    LoreFactLibrary,
    ProjectPromptProfile,
    PromptProfileLibrary,
    TimelineEvent,
    TimelineLibrary,
    WorldBible,
    WorldBibleEntry,
    WorldBibleEntryType,
)


def _repo(tmp_path: Path) -> NovelRepository:
    project_root = tmp_path / "project"
    ProjectRepository(tmp_path).create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    return NovelRepository(project_root)


def _seed_novel(repo: NovelRepository) -> tuple[NovelManuscript, NovelChapter, NovelScene]:
    manuscript = repo.create_manuscript(NovelManuscript(project_id="demo", manuscript_id="m1", title="Mist Novel"))
    chapter = repo.create_chapter(NovelChapter(project_id="demo", manuscript_id="m1", chapter_id="c1", title="Arrival", order_index=0, draft_text="Safe draft"))
    scene = ChapterSceneService(repo).create_scene(NovelScene(project_id="demo", chapter_id="c1", scene_id="s1", title="Gate", draft_text="Scene text"))
    return manuscript, chapter, scene


def test_v22_novel_schema_repository_outline_and_chapter_scene_services(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    manuscript, chapter, scene = _seed_novel(repo)

    assert repo.load_manuscript("m1").title == manuscript.title
    assert repo.list_chapters()[0].chapter_id == chapter.chapter_id
    assert repo.list_scenes()[0].scene_id == scene.scene_id

    outline = repo.save_outline(
        NovelOutline(
            project_id="demo",
            outline_id="o1",
            manuscript_id="m1",
            nodes=[
                NovelOutlineNode(node_id="act1", node_type="act", title="Act 1", order_index=0),
                NovelOutlineNode(node_id="beat1", parent_id="act1", node_type="beat", title="Beat", order_index=0),
            ],
        )
    )
    tree = OutlineService(repo).get_outline_tree(outline.outline_id)
    assert tree[0]["children"][0]["node_id"] == "beat1"

    with pytest.raises(ValueError):
        OutlineService(repo).add_outline_node("o1", NovelOutlineNode(node_id="bad", parent_id="missing", title="Bad"))

    service = ChapterSceneService(repo)
    service.reorder_chapters(["c1"])
    moved = service.move_scene_to_chapter("s1", "c1")
    assert moved.chapter_id == "c1"

    before = GameState(world_id="mist_valley").model_dump(mode="json")
    assert GameState(world_id="mist_valley").model_dump(mode="json") == before


def test_v22_world_bible_prompt_context_and_generation_are_redacted(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    manuscript, chapter, scene = _seed_novel(repo)

    bible = WorldBible(world_bible_id="bible", project_id="demo", title="Bible", flavor_lore=["Safe mist lore"])
    bible.entries["hidden"] = WorldBibleEntry(
        id="hidden",
        title="Hidden",
        content="hidden fact text",
        entry_type=WorldBibleEntryType.HIDDEN,
        visibility="hidden",
    )
    bible.entries["fact"] = WorldBibleEntry(
        id="fact",
        title="Clocktower",
        content="The public clocktower is old.",
        entry_type=WorldBibleEntryType.STRUCTURED_FACT,
        visibility="public",
    )
    lore = LoreFactLibrary(project_id="demo")
    lore.add_draft_lore(LoreFactEntry(id="novel", project_id="demo", title="Flavor", text="Novel safe lore", fact_type="flavor", visibility="novel_safe", safe_for_novel=True))
    lore.add_draft_lore(LoreFactEntry(id="secret", project_id="demo", title="Secret", text="hidden fact text", fact_type="hidden", visibility="hidden", safe_for_novel=True))

    world_context = NovelWorldBibleContextBuilder(bible, lore).build(NovelWorldBibleContextRequest(project_id="demo", manuscript_id="m1"))
    payload = world_context.model_dump_json().lower()
    assert "safe mist lore" in payload
    assert "clocktower" in payload
    assert "hidden fact text" not in payload

    profiles = PromptProfileLibrary(
        project_id="demo",
        profiles={"novel": ProjectPromptProfile(profile_id="novel", mode_scopes=["novel"], novel_style="spare, vivid prose")},
    )
    characters = CharacterLibrary(project_id="demo", characters={"mira": CharacterProfile(character_id="mira", name="Mira", private_notes_authoring_only="hidden fact text")})
    chapter.linked_character_ids = ["mira"]
    manuscript.default_prompt_profile_id = "novel"
    context = NovelPromptContextBuilder(profiles, characters).build(manuscript=manuscript, chapter=chapter, scene=scene, world_bible_context=world_context)
    assert context.style_instructions == "spare, vivid prose"
    assert "hidden fact text" not in context.model_dump_json().lower()

    with pytest.raises(ValueError):
        ProjectPromptProfile(profile_id="unsafe", mode_scopes=["novel"], can_access_hidden_facts=True)  # type: ignore[arg-type]

    provider = FakeLLMProvider(json_responses=[GeneratedNovelDraft(text="Generated safe scene", summary="Summary").model_dump(mode="json")])
    draft = NovelDraftGenerationService(provider, repo).generate_scene_draft(context)
    assert draft.text == "Generated safe scene"
    assert repo.load_scene("s1").draft_text == "Scene text"
    saved = NovelDraftGenerationService(provider, repo).save_scene_draft("s1", draft, explicit_confirm=True, overwrite=True)
    assert saved.draft_text == "Generated safe scene"


def test_v22_consistency_export_world_draft_eventlog_import_and_quality(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    manuscript, chapter, scene = _seed_novel(repo)
    repo.save_chapter(chapter.model_copy(update={"linked_character_ids": ["missing"], "authoring_notes": "private note", "draft_text": "Safe draft private note"}))
    repo.save_foreshadowing_item(ForeshadowingItem(foreshadowing_id="f1", setup_scene_id="s1", hint_text="hint", hidden_truth_ref="hidden_fact"))

    report = NovelConsistencyChecker(repo, hidden_labels=["hidden fact text"]).check("m1")
    codes = {issue.code for issue in report.issues}
    assert "missing_character_ref" in codes or "authoring_notes_in_export_candidate" in codes
    assert "hidden fact text" not in report.model_dump_json().lower()

    repo.save_chapter(repo.load_chapter("c1").model_copy(update={"draft_text": "Safe export text", "authoring_notes": "private note"}))
    exported = NovelExportService(repo).export(NovelExportRequest(manuscript_id="m1", format="markdown"))
    text = Path(exported.path).read_text(encoding="utf-8")
    assert "# Mist Novel" in text
    assert "private note" not in text

    thread = PlotThreadService(repo).create_thread(PlotThread(plot_thread_id="thread1", title="Find the bell", description="A public quest"))
    world_draft = NovelToWorldDraftService(repo).convert_plot_thread(thread)
    assert world_draft.draft_type == "quest"
    assert not (Path(repo.project_root) / "world" / "content_pack" / "thread1.yaml").exists()

    event_log = EventLog()
    event_log.append(Event(event_id="e1", turn=1, event_type="action", actor_id="player", action_type="wait", result="ok", visible_to_player=True, visible_summary="The gate opened.", allow_empty_delta=True))
    event_log.append(Event(event_id="e2", turn=2, event_type="debug", actor_id="system", action_type="debug", result="hidden", visible_to_player=False, debug_summary="hidden fact text", allow_empty_delta=True))
    importer = EventLogToNovelDraftService(repo)
    proposal = importer.preview_import(event_log, turn_start=1, turn_end=2)
    assert proposal.hidden_events_excluded_count == 1
    assert "state_delta" not in proposal.model_dump_json().lower()
    before = json.dumps([event.model_dump(mode="json") for event in event_log.list_events()], sort_keys=True)
    importer.apply_import(ChapterDraftImportProposal(**proposal.model_dump(mode="json")), "c1", explicit_confirm=True, overwrite=True)
    after = json.dumps([event.model_dump(mode="json") for event in event_log.list_events()], sort_keys=True)
    assert before == after


def test_v22_novel_api_smoke(tmp_path: Path) -> None:
    repository = ProjectRepository(tmp_path / "projects")
    app.state.project_repository = repository
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, llm_provider="mock")
    client = TestClient(app)
    create = client.post("/projects", json={"project_id": "novel_api", "name": "Novel API", "project_root": str(tmp_path / "projects" / "novel_api")})
    assert create.status_code == 200
    manuscript = client.post("/projects/novel_api/novel/manuscripts", json={"manuscript_id": "m1", "title": "API Novel"})
    assert manuscript.status_code == 200, manuscript.text
    chapter = client.post("/projects/novel_api/novel/chapters", json={"chapter_id": "c1", "manuscript_id": "m1", "title": "One", "draft_text": "safe"})
    assert chapter.status_code == 200, chapter.text
    scene = client.post("/projects/novel_api/novel/scenes", json={"scene_id": "s1", "chapter_id": "c1", "title": "Scene"})
    assert scene.status_code == 200, scene.text
    listed = client.get("/projects/novel_api/novel/manuscripts")
    assert listed.json()["manuscripts"][0]["manuscript_id"] == "m1"
    quality = client.post("/projects/novel_api/novel/quality/run", json={"case_id": "q1", "manuscript_id": "m1"})
    assert quality.status_code == 200
