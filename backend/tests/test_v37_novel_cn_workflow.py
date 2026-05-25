from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import GameState
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository


def test_v37_novel_cn_fake_generation_uses_provider_gateway_and_is_safe(tmp_path: Path) -> None:
    repository = ProjectRepository(tmp_path / "projects")
    repository.create_project(
        NarrativeProject(
            project_id="demo",
            name="Demo",
            project_root=str(tmp_path / "projects" / "demo"),
        )
    )
    previous_repo = getattr(app.state, "project_repository", None)
    previous_settings = getattr(app.state, "settings", None)
    previous_novel_provider = getattr(app.state, "novel_llm_provider", None)
    app.state.project_repository = repository
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, llm_provider="mock")
    if hasattr(app.state, "novel_llm_provider"):
        delattr(app.state, "novel_llm_provider")
    client = TestClient(app)
    before_state = GameState(world_id="mist_valley").model_dump(mode="json")
    try:
        assert client.post("/projects/demo/novel/manuscripts", json={"manuscript_id": "m1", "title": "中文稿件"}).status_code == 200
        assert client.post(
            "/projects/demo/novel/chapters",
            json={"chapter_id": "c1", "manuscript_id": "m1", "title": "第一章", "draft_text": "安全的章节草稿"},
        ).status_code == 200

        generated = client.post(
            "/projects/demo/novel/llm/generate",
            json={"action": "draft", "manuscript_id": "m1", "chapter_id": "c1", "text": "安全的章节草稿"},
        )
        rewritten = client.post(
            "/projects/demo/novel/llm/generate",
            json={"action": "rewrite", "manuscript_id": "m1", "chapter_id": "c1", "text": "安全的章节草稿"},
        )
        summarized = client.post(
            "/projects/demo/novel/llm/generate",
            json={"action": "summary", "manuscript_id": "m1", "chapter_id": "c1", "text": "安全的章节草稿"},
        )
    finally:
        if previous_repo is None:
            if hasattr(app.state, "project_repository"):
                delattr(app.state, "project_repository")
        else:
            app.state.project_repository = previous_repo
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        if previous_novel_provider is None:
            if hasattr(app.state, "novel_llm_provider"):
                delattr(app.state, "novel_llm_provider")
        else:
            app.state.novel_llm_provider = previous_novel_provider

    for response in (generated, rewritten, summarized):
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["provider_gateway_used"] is True
        assert payload["world_state_unchanged"] is True
        assert payload["generated_text"]
        rendered = response.text.lower()
        assert "api_key" not in rendered
        assert "authorization" not in rendered
        assert "transient_api_key" not in rendered
        assert "raw_state_delta" not in rendered

    assert GameState(world_id="mist_valley").model_dump(mode="json") == before_state
