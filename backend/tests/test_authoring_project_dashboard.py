from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def _client(tmp_path: Path, *, authoring: bool = True) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "project_dashboard.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = tmp_path / "mods"
    app.state.quality_gate_results = []
    app.state.settings = Settings(
        enable_authoring_api=authoring,
        enable_debug_api=True,
        llm_provider="mock",
        llm_api_key="test-api-key-placeholder",
    )
    return TestClient(app)


def test_project_summary_api_returns_project_status(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/authoring/project-summary", params={"world_id": "mist_valley"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_world"] == "mist_valley"
    assert payload["local_only"] is True
    assert payload["hidden_details_redacted"] is True
    assert payload["content_counts"]["locations"] > 0
    assert payload["validation_status"]["status"] in {"passed", "blocked"}
    assert isinstance(payload["recent_edits"], list)


def test_project_summary_does_not_return_api_key_or_hidden_text(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/authoring/project-summary", params={"world_id": "mist_valley"})

    assert response.status_code == 200
    assert "test-api-key-placeholder" not in response.text
    assert "A sealed letter is hidden beneath a loose paving stone." not in response.text
    assert "sealed_letter_under_stone" not in response.text


def test_project_summary_unavailable_when_authoring_disabled(tmp_path: Path) -> None:
    client = _client(tmp_path, authoring=False)

    response = client.get("/authoring/project-summary", params={"world_id": "mist_valley"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Authoring API is disabled"
