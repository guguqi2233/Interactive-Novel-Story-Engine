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
    app.state.session_store = InMemorySessionStore(worlds_root=str(worlds_root))
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "map_authoring.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(
        enable_authoring_api=authoring_enabled,
        llm_provider="mock",
        llm_api_key="super-secret-test-key",
    )
    return TestClient(app)


def test_authoring_disabled_blocks_map_api(tmp_path: Path) -> None:
    client = make_client(tmp_path, authoring_enabled=False)

    response = client.get("/authoring/worlds/mist_valley/map")

    assert response.status_code == 403
    assert response.json()["detail"] == "Authoring API is disabled"


def test_get_map_returns_graph(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/authoring/worlds/mist_valley/map")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    assert payload["world_id"] == "mist_valley"
    assert {node["location_id"] for node in payload["graph"]["nodes"]} >= {
        "village_square",
        "blacksmith",
    }
    assert any(edge["source_location_id"] == "village_square" for edge in payload["graph"]["edges"])


def test_map_preview_does_not_write_locations_file(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]
    graph = client.get("/authoring/worlds/mist_valley/map").json()["graph"]
    graph["nodes"][0]["x"] = graph["nodes"][0]["x"] + 123

    response = client.post("/authoring/worlds/mist_valley/map/preview", json={"graph": graph})
    after = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]

    assert response.status_code == 200
    assert response.json()["yaml_content"] != original
    assert after == original


def test_map_validate_invalid_edge_returns_error(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    graph = client.get("/authoring/worlds/mist_valley/map").json()["graph"]
    graph["edges"].append(
        {
            "source_location_id": "village_square",
            "target_location_id": "void",
            "edge_type": "exit",
            "label": "down",
            "visibility": "public",
        }
    )

    response = client.post("/authoring/worlds/mist_valley/map/validate", json={"graph": graph})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert any("Exit points to missing location: void" in issue["message"] for issue in payload["errors"])


def test_put_valid_map_updates_locations_yaml(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    graph = client.get("/authoring/worlds/mist_valley/map").json()["graph"]
    node = next(item for item in graph["nodes"] if item["location_id"] == "blacksmith")
    node["x"] = 333
    node["y"] = 44

    response = client.put("/authoring/worlds/mist_valley/map", json={"graph": graph})
    locations = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]

    assert response.status_code == 200
    assert response.json()["validation"]["ok"] is True
    assert "x: 333" in locations
    assert "y: 44" in locations


def test_put_invalid_map_is_rejected_and_original_file_is_preserved(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]
    graph = client.get("/authoring/worlds/mist_valley/map").json()["graph"]
    graph["edges"].append(
        {
            "source_location_id": "village_square",
            "target_location_id": "void",
            "edge_type": "exit",
            "label": "down",
            "visibility": "public",
        }
    )

    response = client.put("/authoring/worlds/mist_valley/map", json={"graph": graph})
    after = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]

    assert response.status_code == 400
    assert "Exit points to missing location: void" in response.text
    assert after == original


def test_hidden_map_data_does_not_enter_player_api(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    graph = client.get("/authoring/worlds/mist_valley/map").json()["graph"]
    node = next(item for item in graph["nodes"] if item["location_id"] == "blacksmith")
    node["visibility"] = "hidden"
    node["tags"] = ["authoring_secret"]
    assert client.put("/authoring/worlds/mist_valley/map", json={"graph": graph}).status_code == 200

    start = client.post("/game/start", json={"world_id": "mist_valley"}).json()
    visible_payload = start["visible_state"]

    assert "authoring_secret" not in str(visible_payload)
    assert "visibility" not in str(visible_payload)
    assert "hidden" not in str(visible_payload)


def test_map_api_rejects_path_traversal(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/authoring/worlds/../map")

    assert response.status_code in {400, 404}
    assert "super-secret-test-key" not in response.text
