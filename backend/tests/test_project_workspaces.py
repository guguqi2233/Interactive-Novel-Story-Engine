from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.desktop.workspaces import RecentProjectsService, WorkspaceService
from app.main import app
from app.session_store import InMemorySessionStore


def _make_workspace(root: Path, name: str = "demo_world") -> Path:
    workspace = root / "workspace"
    world = workspace / "worlds" / name
    world.mkdir(parents=True)
    (world / "manifest.yaml").write_text("id: demo_world\nname: Demo\n", encoding="utf-8")
    return workspace


def _make_client(tmp_path: Path) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "saves.db")
    app.state.settings = Settings(llm_api_key="sk-test-secret-that-must-not-appear")
    app.state.workspace_service = WorkspaceService(default_workspace=tmp_path)
    app.state.recent_projects_service = RecentProjectsService()
    return TestClient(app)


def test_list_workspace_returns_safe_summary(tmp_path: Path) -> None:
    _make_workspace(tmp_path)
    client = _make_client(tmp_path)

    response = client.get("/studio/workspaces")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    assert len(payload["workspaces"]) == 1
    text = response.text
    assert "sk-test-secret-that-must-not-appear" not in text
    assert "LLM_API_KEY" not in text
    assert ".env" not in text


def test_add_workspace_counts_worlds_and_redacts_path(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    client = _make_client(tmp_path)

    response = client.post("/studio/workspaces", json={"path": str(workspace), "name": "My Project"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "My Project"
    assert payload["world_count"] == 1
    assert payload["safe_status"] == "ok"
    assert str(tmp_path) not in response.text


def test_add_workspace_rejects_path_traversal(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    response = client.post("/studio/workspaces", json={"path": "../outside"})

    assert response.status_code == 400
    assert "not allowed" in response.text


def test_select_workspace_sets_current_without_active_save_mutation(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    client = _make_client(tmp_path)
    added = client.post("/studio/workspaces", json={"path": str(workspace), "name": "Selectable"}).json()

    selected = client.post("/studio/workspaces/select", json={"workspace_id": added["workspace_id"]})
    current = client.get("/studio/workspaces/current")

    assert selected.status_code == 200
    assert current.status_code == 200
    assert current.json()["workspace_id"] == added["workspace_id"]
    assert current.json()["last_opened_at"]
    assert getattr(app.state.session_store, "_sessions") == {}


def test_select_workspace_records_recent_project(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    client = _make_client(tmp_path)
    added = client.post("/studio/workspaces", json={"path": str(workspace), "name": "Recent One"}).json()

    selected = client.post(
        "/studio/workspaces/select",
        json={"workspace_id": added["workspace_id"], "last_world_id": "demo_world"},
    )
    recent = client.get("/studio/recent-projects")

    assert selected.status_code == 200
    assert recent.status_code == 200
    payload = recent.json()
    assert payload["projects"][0]["workspace_id"] == added["workspace_id"]
    assert payload["projects"][0]["display_name"] == "Recent One"
    assert payload["projects"][0]["last_world_id"] == "demo_world"
    assert "sk-test-secret-that-must-not-appear" not in recent.text
    assert str(tmp_path) not in recent.text


def test_recent_projects_sort_clear_and_remove(tmp_path: Path) -> None:
    first = _make_workspace(tmp_path / "first", name="world_a")
    second = _make_workspace(tmp_path / "second", name="world_b")
    client = _make_client(tmp_path)
    first_added = client.post("/studio/workspaces", json={"path": str(first), "name": "First"}).json()
    second_added = client.post("/studio/workspaces", json={"path": str(second), "name": "Second"}).json()

    client.post("/studio/workspaces/select", json={"workspace_id": first_added["workspace_id"]})
    client.post("/studio/workspaces/select", json={"workspace_id": second_added["workspace_id"]})
    recent = client.get("/studio/recent-projects").json()["projects"]

    assert [item["display_name"] for item in recent] == ["Second", "First"]

    removed = client.delete(f"/studio/recent-projects/{second_added['workspace_id']}")
    assert removed.status_code == 200
    assert removed.json()["removed"] is True
    assert [item["display_name"] for item in client.get("/studio/recent-projects").json()["projects"]] == ["First"]

    cleared = client.post("/studio/recent-projects/clear")
    assert cleared.status_code == 200
    assert cleared.json()["cleared"] is True
    assert client.get("/studio/recent-projects").json()["projects"] == []


def test_workspace_summary_does_not_read_env_or_api_key(tmp_path: Path) -> None:
    workspace = _make_workspace(tmp_path)
    (workspace / ".env").write_text("LLM_API_KEY=sk-test-secret-that-must-not-appear\n", encoding="utf-8")
    client = _make_client(tmp_path)

    response = client.post("/studio/workspaces", json={"path": str(workspace)})

    assert response.status_code == 200
    assert "sk-test-secret-that-must-not-appear" not in response.text
    assert "LLM_API_KEY" not in response.text


def test_list_workspace_templates(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    response = client.get("/studio/workspace-templates")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    template_ids = {template["template_id"] for template in payload["templates"]}
    assert "blank_studio" in template_ids
    assert "world_project" in template_ids
    assert "sk-test-secret-that-must-not-appear" not in response.text
    assert ".env" not in response.text


def test_create_blank_workspace_from_template(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    target = tmp_path / "blank_project"

    response = client.post(
        "/studio/workspaces/create-from-template",
        json={"template_id": "blank_studio", "path": str(target), "name": "Blank"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Blank"
    assert payload["safe_status"] == "ok"
    assert (target / "worlds").is_dir()
    assert (target / "config.template.env").exists()
    assert not (target / ".env").exists()
    assert "sk-test-secret-that-must-not-appear" not in response.text
    assert str(tmp_path) not in response.text


def test_create_world_project_from_template(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    target = tmp_path / "world_project"

    response = client.post(
        "/studio/workspaces/create-from-template",
        json={"template_id": "world_project", "path": str(target), "name": "World Project"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_count"] == 1
    assert (target / "worlds" / "starter_world" / "manifest.yaml").exists()
    assert "LLM_API_KEY" not in (target / "config.template.env").read_text(encoding="utf-8")


def test_create_workspace_from_template_rejects_path_traversal(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    response = client.post(
        "/studio/workspaces/create-from-template",
        json={"template_id": "blank_studio", "path": "../unsafe"},
    )

    assert response.status_code == 400
    assert "not allowed" in response.text


def test_create_workspace_from_template_refuses_existing_non_empty(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    target = tmp_path / "existing"
    target.mkdir()
    (target / "README.md").write_text("already here", encoding="utf-8")

    response = client.post(
        "/studio/workspaces/create-from-template",
        json={"template_id": "blank_studio", "path": str(target)},
    )

    assert response.status_code == 400
    assert "not empty" in response.text
