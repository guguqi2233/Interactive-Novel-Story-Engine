from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def _client(tmp_path: Path) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "merge.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def _branch(client: TestClient, branch_id: str) -> None:
    response = client.post("/authoring/worlds/mist_valley/branches", json={"branch_id": branch_id, "name": branch_id})
    assert response.status_code == 200


def test_simple_merge_draft_can_be_generated(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _branch(client, "ours")
    _branch(client, "theirs")
    items = tmp_path / "worlds" / ".branches" / "mist_valley" / "theirs" / "items.yaml"
    items.write_text(items.read_text(encoding="utf-8") + "\n  - id: merge_item\n    name: Merge Item\n    description: Branch item.\n    location_id: village_square\n    portable: true\n", encoding="utf-8")

    response = client.post("/authoring/worlds/mist_valley/merge/preview", json={"ours": "ours", "theirs": "theirs"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["validation"]["ok"] is True
    assert "merge_item" in payload["proposed_files"]["items.yaml"]
    assert payload["writes_to_disk"] is False


def test_conflicting_entity_is_detected(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _branch(client, "ours")
    _branch(client, "theirs")
    ours = tmp_path / "worlds" / ".branches" / "mist_valley" / "ours" / "items.yaml"
    theirs = tmp_path / "worlds" / ".branches" / "mist_valley" / "theirs" / "items.yaml"
    ours.write_text(ours.read_text(encoding="utf-8").replace("Iron Nails", "Ours Nails"), encoding="utf-8")
    theirs.write_text(theirs.read_text(encoding="utf-8").replace("Iron Nails", "Theirs Nails"), encoding="utf-8")

    response = client.post("/authoring/worlds/mist_valley/merge/preview", json={"ours": "ours", "theirs": "theirs"})

    assert response.status_code == 200
    assert any(conflict["conflict_type"] == "same_entity_changed" for conflict in response.json()["conflicts"])
    assert all(conflict["base"].get("details_redacted") for conflict in response.json()["conflicts"] if conflict["base"])


def test_hidden_visibility_mismatch_is_detected(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _branch(client, "ours")
    _branch(client, "theirs")
    ours = tmp_path / "worlds" / ".branches" / "mist_valley" / "ours" / "facts.yaml"
    theirs = tmp_path / "worlds" / ".branches" / "mist_valley" / "theirs" / "facts.yaml"
    ours.write_text(ours.read_text(encoding="utf-8").replace("visibility: public", "visibility: hidden", 1), encoding="utf-8")
    theirs.write_text(theirs.read_text(encoding="utf-8").replace("The village square is damp with morning mist.", "The square is clear."), encoding="utf-8")

    response = client.post("/authoring/worlds/mist_valley/merge/preview", json={"ours": "ours", "theirs": "theirs"})

    assert response.status_code == 200
    assert any(conflict["conflict_type"] == "hidden_visibility_mismatch" for conflict in response.json()["conflicts"])
    assert "The square is clear." not in response.text
    assert "details_redacted" in response.text


def test_merge_preview_does_not_write_disk(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _branch(client, "ours")
    _branch(client, "theirs")
    base_items = tmp_path / "worlds" / "mist_valley" / "items.yaml"
    before = base_items.read_text(encoding="utf-8")
    theirs = tmp_path / "worlds" / ".branches" / "mist_valley" / "theirs" / "items.yaml"
    theirs.write_text(theirs.read_text(encoding="utf-8") + "\n  - id: preview_only\n    name: Preview Only\n    description: Draft.\n    location_id: village_square\n    portable: true\n", encoding="utf-8")

    response = client.post("/authoring/worlds/mist_valley/merge/preview", json={"ours": "ours", "theirs": "theirs"})

    assert response.status_code == 200
    assert base_items.read_text(encoding="utf-8") == before


def test_invalid_merge_blocks_save(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _branch(client, "ours")
    _branch(client, "theirs")
    theirs = tmp_path / "worlds" / ".branches" / "mist_valley" / "theirs" / "npcs.yaml"
    theirs.write_text(theirs.read_text(encoding="utf-8").replace("location_id: blacksmith", "location_id: missing_place"), encoding="utf-8")
    before = (tmp_path / "worlds" / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")

    response = client.post("/authoring/worlds/mist_valley/merge/save", json={"ours": "ours", "theirs": "theirs", "confirm_save": True})

    assert response.status_code == 200
    assert response.json()["saved"] is False
    assert response.json()["validation"]["ok"] is False
    assert (tmp_path / "worlds" / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8") == before


def test_merge_does_not_modify_active_game_state(tmp_path: Path) -> None:
    client = _client(tmp_path)
    start = client.post("/game/start", json={"world_id": "mist_valley"}).json()
    before_state = client.get(f"/game/state/{start['session_id']}").json()
    _branch(client, "ours")
    _branch(client, "theirs")
    theirs = tmp_path / "worlds" / ".branches" / "mist_valley" / "theirs" / "items.yaml"
    theirs.write_text(theirs.read_text(encoding="utf-8") + "\n  - id: saved_merge_item\n    name: Saved Merge Item\n    description: Draft.\n    location_id: village_square\n    portable: true\n", encoding="utf-8")

    response = client.post("/authoring/worlds/mist_valley/merge/save", json={"ours": "ours", "theirs": "theirs", "confirm_save": True})
    after_state = client.get(f"/game/state/{start['session_id']}").json()

    assert response.status_code == 200
    assert response.json()["saved"] is True
    assert after_state == before_state
