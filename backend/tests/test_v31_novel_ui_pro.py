from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import GameState
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.novel_studio import (
    CharacterArc,
    DraftVersionService,
    NovelChapter,
    NovelPreferences,
    NovelPreferencesService,
    NovelRepository,
    NovelSearchService,
    NovelScene,
    NovelManuscript,
    PlotThread,
    WritingSessionService,
)
from app.platform.project_repository import ProjectRepository


def _repo(tmp_path: Path) -> NovelRepository:
    project_root = tmp_path / "project"
    ProjectRepository(tmp_path).create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    repo = NovelRepository(project_root)
    repo.create_manuscript(NovelManuscript(project_id="demo", manuscript_id="m1", title="Mist Novel"))
    repo.create_chapter(NovelChapter(project_id="demo", manuscript_id="m1", chapter_id="c1", title="Arrival", draft_text="safe draft words", summary="safe summary"))
    repo.create_scene(NovelScene(project_id="demo", scene_id="s1", chapter_id="c1", title="Gate", draft_text="safe scene text", summary="safe scene"))
    return repo


def test_v31_draft_snapshots_compare_restore_and_no_world_mutation(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    before = GameState(world_id="mist_valley").model_dump(mode="json")

    service = DraftVersionService(repo)
    snapshot = service.create_snapshot(target_type="chapter", target_id="c1", snapshot_id="snap1")
    assert snapshot.draft_text == "safe draft words"
    assert "api_key" not in snapshot.model_dump_json().lower()

    repo.save_chapter(repo.load_chapter("c1").model_copy(update={"draft_text": "changed draft"}))
    compare = service.compare_snapshots("snap1", current_text="changed draft")
    assert compare.changed

    with pytest.raises(ValueError):
      service.restore_snapshot_confirmed("snap1")

    restored = service.restore_snapshot_confirmed("snap1", explicit_confirm=True, overwrite=True)
    assert restored.draft_text == "safe draft words"
    assert GameState(world_id="mist_valley").model_dump(mode="json") == before


def test_v31_writing_session_search_and_preferences_are_local_safe(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    repo.create_chapter(
        NovelChapter(
            project_id="demo",
            manuscript_id="m1",
            chapter_id="hidden_chapter",
            title="Hidden Chapter",
            draft_text="ordinary concealed chapter text",
            summary="ordinary concealed summary",
            visibility="hidden",
        )
    )
    repo.create_scene(
        NovelScene(
            project_id="demo",
            scene_id="hidden_scene",
            chapter_id="hidden_chapter",
            title="Hidden Scene",
            draft_text="ordinary concealed scene text",
            summary="ordinary concealed scene",
            visibility="hidden",
        )
    )
    repo.save_plot_thread(PlotThread(plot_thread_id="plot1", title="Find Gate", description="public plot"))
    repo.save_character_arc(CharacterArc(arc_id="arc1", character_id="mira", title="Mira Arc", premise="public premise", authoring_notes="private note"))

    session_service = WritingSessionService(repo)
    session = session_service.start_session(session_id="session1", manuscript_id="m1", active_chapter_id="c1")
    assert session.word_count_start >= 3
    assert session_service.get_current_session("m1") is not None
    ended = session_service.end_session("session1")
    assert ended.ended_at is not None
    assert "private note" not in ended.model_dump_json().lower()

    results = NovelSearchService(repo).search(keyword="private")
    assert results == []
    hidden_results = NovelSearchService(repo).search(keyword="concealed")
    assert hidden_results == []
    public_results = NovelSearchService(repo).search(keyword="safe")
    assert {item.result_type for item in public_results} >= {"chapter", "scene"}

    prefs = NovelPreferencesService(repo).save_preferences(NovelPreferences(project_id="demo", default_manuscript_id="m1", default_prompt_profile_id="novel_safe"))
    payload = prefs.model_dump_json().lower()
    assert "api_key" not in payload
    assert "hidden fact" not in payload


def test_v31_novel_api_smoke_safe_outputs(tmp_path: Path) -> None:
    repository = ProjectRepository(tmp_path / "projects")
    app.state.project_repository = repository
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, llm_provider="mock")
    client = TestClient(app)

    assert client.post("/projects", json={"project_id": "v31_project", "name": "Novel UI Pro", "project_root": str(tmp_path / "projects" / "v31_project")}).status_code == 200
    assert client.post("/projects/v31_project/novel/manuscripts", json={"manuscript_id": "m1", "title": "Novel"}).status_code == 200
    assert client.post("/projects/v31_project/novel/chapters", json={"chapter_id": "c1", "manuscript_id": "m1", "title": "One", "draft_text": "safe draft"}).status_code == 200

    snapshot = client.post("/projects/v31_project/novel/draft-snapshots", json={"target_type": "chapter", "target_id": "c1", "snapshot_id": "snap1"})
    assert snapshot.status_code == 200, snapshot.text
    assert snapshot.json()["draft_text"] == "[stored locally]"

    session = client.post("/projects/v31_project/novel/writing-sessions/start", json={"session_id": "session1", "manuscript_id": "m1"})
    assert session.status_code == 200, session.text

    search = client.get("/projects/v31_project/novel/search?keyword=safe")
    assert search.status_code == 200
    assert "api_key" not in search.text.lower()

    prefs = client.put("/projects/v31_project/novel/preferences", json={"default_manuscript_id": "m1"})
    assert prefs.status_code == 200
    assert "api_key" not in prefs.text.lower()


def test_v31_normal_novel_api_export_and_snapshots_filter_hidden_content(tmp_path: Path) -> None:
    repository = ProjectRepository(tmp_path / "projects")
    app.state.project_repository = repository
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, llm_provider="mock")
    client = TestClient(app)

    assert client.post("/projects", json={"project_id": "v31_hidden_project", "name": "Novel UI Pro", "project_root": str(tmp_path / "projects" / "v31_hidden_project")}).status_code == 200
    assert client.post("/projects/v31_hidden_project/novel/manuscripts", json={"manuscript_id": "m1", "title": "Novel"}).status_code == 200
    assert client.post("/projects/v31_hidden_project/novel/chapters", json={"chapter_id": "c1", "manuscript_id": "m1", "title": "One", "draft_text": "public draft", "authoring_notes": "private authoring note"}).status_code == 200
    assert client.post(
        "/projects/v31_hidden_project/novel/chapters",
        json={
            "chapter_id": "hidden_chapter",
            "manuscript_id": "m1",
            "title": "Hidden",
            "draft_text": "ordinary concealed chapter text",
            "summary": "ordinary concealed summary",
            "visibility": "hidden",
        },
    ).status_code == 200

    chapters = client.get("/projects/v31_hidden_project/novel/chapters")
    assert chapters.status_code == 200
    payload = chapters.text.lower()
    assert "private authoring note" not in payload
    assert "ordinary concealed chapter text" not in payload
    assert "[redacted]" in payload

    snapshot = client.post("/projects/v31_hidden_project/novel/draft-snapshots", json={"target_type": "chapter", "target_id": "hidden_chapter", "snapshot_id": "hidden_snapshot"})
    assert snapshot.status_code == 400

    export = client.post("/projects/v31_hidden_project/novel/export", json={"manuscript_id": "m1", "format": "markdown"})
    assert export.status_code == 200, export.text
    export_path = Path(export.json()["path"])
    text = export_path.read_text(encoding="utf-8").lower()
    assert "public draft" in text
    assert "ordinary concealed chapter text" not in text
    assert "private authoring note" not in text
