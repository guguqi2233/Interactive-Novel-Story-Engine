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
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "references.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = tmp_path / "mods"
    app.state.settings = Settings(enable_authoring_api=authoring, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def test_reference_index_returns_valid_entities(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/authoring/worlds/mist_valley/references")

    assert response.status_code == 200
    payload = response.json()
    refs = {(item["kind"], item["id"]) for item in payload["items"]}
    assert ("location", "village_square") in refs
    assert ("NPC", "harlan") in refs
    assert ("fact", "village_square_is_misty") in refs
    assert ("prompt profile", "default_safe") in refs


def test_reference_index_does_not_return_missing_refs(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/authoring/worlds/mist_valley/references")

    assert response.status_code == 200
    assert all(item["id"] != "missing_location" for item in response.json()["items"])


def test_reference_index_marks_hidden_refs_without_hidden_text(tmp_path: Path) -> None:
    client = _client(tmp_path)
    rumors = Path(app.state.worlds_root) / "mist_valley" / "rumors.yaml"
    rumors.write_text(
        rumors.read_text(encoding="utf-8")
        + "\n  - id: secret_rumor_label\n    fact_id: sealed_letter_under_stone\n    text_for_player: The mayor hid the vault key.\n    known_by_player: false\n",
        encoding="utf-8",
    )

    response = client.get("/authoring/worlds/mist_valley/references")

    assert response.status_code == 200
    hidden_fact = next(item for item in response.json()["items"] if item["id"] == "sealed_letter_under_stone")
    hidden_rumor = next(item for item in response.json()["items"] if item["id"] == "secret_rumor_label")
    assert hidden_fact["hidden"] is True
    assert hidden_fact["player_visible"] is False
    assert hidden_fact["authoring_safe_metadata"]["text_redacted"] is True
    assert hidden_rumor["hidden"] is True
    assert hidden_rumor["label"] == "secret_rumor_label"
    assert "A sealed letter is hidden beneath a loose paving stone." not in response.text
    assert "The mayor hid the vault key." not in response.text


def test_reference_index_is_not_a_player_api_and_requires_authoring(tmp_path: Path) -> None:
    disabled_client = _client(tmp_path, authoring=False)

    disabled_response = disabled_client.get("/authoring/worlds/mist_valley/references")
    player_response = disabled_client.get("/game/worlds/mist_valley/references")

    assert disabled_response.status_code == 403
    assert player_response.status_code == 404
