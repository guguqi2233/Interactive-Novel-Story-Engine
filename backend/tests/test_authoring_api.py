from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def make_client(tmp_path: Path, authoring_enabled: bool = True) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "authoring_api.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(
        enable_authoring_api=authoring_enabled,
        llm_api_key="super-secret-test-key",
    )
    return TestClient(app)


def test_authoring_disabled_returns_forbidden(tmp_path: Path) -> None:
    client = make_client(tmp_path, authoring_enabled=False)

    response = client.get("/authoring/worlds")

    assert response.status_code == 403
    assert response.json()["detail"] == "Authoring API is disabled"


def test_authoring_enabled_lists_worlds(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/authoring/worlds")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    assert [world["world_id"] for world in payload["worlds"]] == ["mist_valley"]


def test_authoring_reads_whitelisted_yaml_file(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/authoring/worlds/mist_valley/files/manifest.yaml")

    assert response.status_code == 200
    payload = response.json()
    assert payload["file_name"] == "manifest.yaml"
    assert "world_id:" in payload["content"]


def test_authoring_rejects_non_whitelisted_file(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/authoring/worlds/mist_valley/files/.env")

    assert response.status_code == 400
    assert "not authoring-allowed" in response.json()["detail"]


def test_authoring_rejects_path_traversal(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/authoring/worlds/../files/manifest.yaml")

    assert response.status_code in {400, 404}
    assert "super-secret-test-key" not in response.text


def test_authoring_put_invalid_yaml_returns_error(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.put(
        "/authoring/worlds/mist_valley/files/facts.yaml",
        json={"content": "facts: [unterminated"},
    )

    assert response.status_code == 400
    assert "Invalid YAML" in response.json()["detail"]


def test_authoring_put_valid_yaml_then_validate_runs(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/facts.yaml").json()["content"]
    content = original + """
  - id: village_notice
    text: The village notice board has been freshly painted.
    visibility: public
    known_by:
      - player
    tags:
      - notice
"""

    put_response = client.put(
        "/authoring/worlds/mist_valley/files/facts.yaml",
        json={"content": content},
    )
    validate_response = client.post("/authoring/worlds/mist_valley/validate")

    assert put_response.status_code == 200
    assert put_response.json()["validation"]["ok"] is True
    assert validate_response.status_code == 200
    assert validate_response.json()["ok"] is True


def test_authoring_preview_valid_yaml_reports_diff_without_writing(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/facts.yaml").json()["content"]
    proposed = original + """
  - id: preview_only_fact
    text: Preview-only fact.
    visibility: public
    known_by:
      - player
    tags: []
"""

    response = client.post(
        "/authoring/worlds/mist_valley/preview-file-change",
        json={"file_name": "facts.yaml", "proposed_content": proposed},
    )
    after = client.get("/authoring/worlds/mist_valley/files/facts.yaml").json()["content"]

    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed_ok"] is True
    assert payload["validation_report"]["ok"] is True
    assert "preview_only_fact" in payload["diff_summary"]["added_ids"]
    assert payload["potential_save_migration_required"] is False
    assert after == original


def test_authoring_preview_invalid_yaml_returns_parse_error(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/authoring/worlds/mist_valley/preview-file-change",
        json={"file_name": "facts.yaml", "proposed_content": "facts: [unterminated"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["parsed_ok"] is False
    assert payload["validation_report"]["ok"] is False
    assert payload["validation_report"]["errors"][0]["code"] == "draft_yaml_parse_error"


def test_authoring_impact_detects_removed_npc_id(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/npcs.yaml").json()["content"]
    proposed = original.replace("  - id: harlan", "  - id: harlan_removed")

    response = client.post(
        "/authoring/worlds/mist_valley/impact-analysis",
        json={"file_name": "npcs.yaml", "proposed_content": proposed},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "harlan" in payload["removed_npcs"]
    assert payload["may_break_saves"] is True


def test_authoring_impact_detects_removed_location_id(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]
    proposed = original.replace("  - id: blacksmith", "  - id: old_forge")

    response = client.post(
        "/authoring/worlds/mist_valley/impact-analysis",
        json={"file_name": "locations.yaml", "proposed_content": proposed},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "blacksmith" in payload["removed_locations"]
    assert payload["may_break_saves"] is True


def test_authoring_validate_draft_does_not_modify_active_game_state(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    start_response = client.post("/game/start", json={"world_id": "mist_valley"})
    session_id = start_response.json()["session_id"]
    original_state = client.get(f"/game/state/{session_id}").json()["visible_state"]
    original = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]
    proposed = original.replace("Village Square", "Draft Square")

    response = client.post(
        "/authoring/worlds/mist_valley/validate-draft",
        json={"file_name": "locations.yaml", "proposed_content": proposed},
    )
    after_state = client.get(f"/game/state/{session_id}").json()["visible_state"]

    assert response.status_code == 200
    assert after_state == original_state


def test_authoring_preview_rejects_path_traversal(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/authoring/worlds/mist_valley/preview-file-change",
        json={"file_name": "../manifest.yaml", "proposed_content": "world_id: x"},
    )

    assert response.status_code == 400
    assert "not authoring-allowed" in response.json()["detail"]


def test_authoring_validation_errors_are_clear_and_do_not_persist(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]
    invalid_content = """locations:
  - id: village_square
    name: Village Square
    description: Broken exit.
    exits:
      north: missing_location
"""

    response = client.put(
        "/authoring/worlds/mist_valley/files/locations.yaml",
        json={"content": invalid_content},
    )
    after = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]

    assert response.status_code == 400
    assert response.json()["detail"]["ok"] is False
    issue = response.json()["detail"]["errors"][0]
    assert issue["file"] == "locations.yaml"
    assert issue["code"]
    assert issue["path"].startswith("locations.yaml")
    assert after == original


def test_authoring_api_does_not_leak_env_or_api_key(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    blocked_response = client.get("/authoring/worlds/mist_valley/files/.env")
    list_response = client.get("/authoring/worlds")

    combined = blocked_response.text + list_response.text
    assert "super-secret-test-key" not in combined
    assert "LLM_API_KEY" not in combined
    assert "llm_api_key" not in combined
