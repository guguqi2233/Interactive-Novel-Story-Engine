from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.desktop.workspaces import RecentProjectsService, WorkspaceService
from app.main import app
from app.session_store import InMemorySessionStore


def _make_workspace(root: Path, *, with_world: bool = True) -> Path:
    workspace = root / "workspace"
    workspace.mkdir(parents=True)
    if with_world:
        world = workspace / "worlds" / "demo_world"
        world.mkdir(parents=True)
        (world / "manifest.yaml").write_text("id: demo_world\nname: Demo\n", encoding="utf-8")
    return workspace


def _make_client(tmp_path: Path, *, database_url: str | None = None, workspace: Path | None = None) -> TestClient:
    database_path = tmp_path / "health.db"
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(database_path)
    app.state.settings = Settings(
        database_url=database_url if database_url is not None else f"sqlite:///{database_path}",
        llm_provider="openai",
        llm_api_key="sk-test-secret-that-must-not-appear",
        enable_authoring_api=True,
        enable_debug_api=False,
    )
    app.state.workspace_service = WorkspaceService(default_workspace=workspace or tmp_path)
    app.state.recent_projects_service = RecentProjectsService()
    return TestClient(app)


def test_desktop_health_check_normal(tmp_path: Path) -> None:
    client = _make_client(tmp_path, workspace=_make_workspace(tmp_path))

    response = client.get("/studio/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    assert payload["provider_config"]["api_key_configured"] is True
    assert any(check["check_id"] == "backend_alive" and check["status"] == "pass" for check in payload["checks"])
    assert any(check["check_id"] == "database_reachable" and check["status"] == "pass" for check in payload["checks"])
    assert "sk-test-secret-that-must-not-appear" not in response.text
    assert str(tmp_path) not in response.text


def test_desktop_health_missing_database_returns_error(tmp_path: Path) -> None:
    client = _make_client(tmp_path, database_url="", workspace=_make_workspace(tmp_path))

    response = client.post("/studio/health/check")

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] == "error"
    assert any(check["check_id"] == "database_reachable" and check["status"] == "error" for check in payload["checks"])
    assert "sk-test-secret-that-must-not-appear" not in response.text


def test_desktop_health_missing_workspace_returns_warning(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    app.state.workspace_service.remove_workspace_reference(app.state.workspace_service.get_current_workspace().workspace_id)

    response = client.get("/studio/health")

    assert response.status_code == 200
    payload = response.json()
    assert any(check["check_id"] == "current_workspace_valid" and check["status"] == "warning" for check in payload["checks"])
    assert payload["current_workspace"] is None


def test_desktop_health_no_api_key_leakage_for_provider_warning(tmp_path: Path) -> None:
    client = _make_client(tmp_path, workspace=_make_workspace(tmp_path, with_world=False))
    app.state.settings = app.state.settings.model_copy(update={"llm_api_key": None})

    response = client.get("/studio/health")

    assert response.status_code == 200
    payload = response.json()
    assert any(
        check["check_id"] == "provider_config_safe_summary" and check["status"] == "warning"
        for check in payload["checks"]
    )
    assert "LLM_API_KEY" not in response.text
    assert "sk-" not in response.text
