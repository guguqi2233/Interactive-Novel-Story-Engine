from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.item_economy_authoring import (
    item_economy_to_yaml,
    parse_item_economy_authoring,
    preview_item_economy_authoring,
)
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.economy import get_shop_inventory
from app.main import app
from app.session_store import InMemorySessionStore


def _copy_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def _client(tmp_path: Path, worlds_root: Path, *, authoring: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "item_economy_authoring.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=authoring, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def test_items_yaml_parses_to_item_economy_authoring_graph(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)

    graph = parse_item_economy_authoring("mist_valley", ContentAuthoringService(worlds_root))

    assert [item.id for item in graph.items] == ["notice_board", "anvil", "sealed_letter"]
    assert graph.merchants[0].npc_id == "harlan"
    assert graph.merchants[0].shop_inventory == ["sealed_letter"]


def test_item_economy_roundtrip_preserves_price_fields(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_item_economy_authoring("mist_valley", service)
    graph.items[2].base_price = 17
    graph.items[2].rarity = "rare"

    yaml_contents = item_economy_to_yaml("mist_valley", graph, service)

    assert "base_price: 17" in yaml_contents["items.yaml"]
    assert "rarity: rare" in yaml_contents["items.yaml"]


def test_invalid_item_ownership_conflict_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_item_economy_authoring("mist_valley", service)
    graph.items[2].owner_id = "harlan"
    graph.items[2].location_id = "village_square"

    preview = preview_item_economy_authoring("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "item_conflicting_ownership" for issue in preview.validation.errors)


def test_invalid_shop_inventory_item_id_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_item_economy_authoring("mist_valley", service)
    graph.merchants[0].shop_inventory = ["missing_item"]

    preview = preview_item_economy_authoring("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "npc_shop_inventory_missing_item" for issue in preview.validation.errors)


def test_negative_price_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_item_economy_authoring("mist_valley", service)
    graph.items[0].base_price = -1

    preview = preview_item_economy_authoring("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "item_negative_base_price" or "base_price" in issue.path for issue in preview.validation.errors)


def test_hidden_item_does_not_enter_player_shop_ui(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    state = WorldLoader(worlds_root).load("mist_valley").to_game_state()

    inventory = get_shop_inventory(state, "harlan")

    assert all(item.id != "sealed_letter" for item in inventory)


def test_item_economy_preview_api_does_not_write_files(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    items_before = (worlds_root / "mist_valley" / "items.yaml").read_text(encoding="utf-8")
    npcs_before = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")
    graph_payload = client.get("/authoring/worlds/mist_valley/economy").json()
    graph_payload["items"][2]["base_price"] = 42

    response = client.post("/authoring/worlds/mist_valley/economy/preview", json={"graph": graph_payload})

    assert response.status_code == 200
    assert response.json()["validation"]["ok"] is True
    assert (worlds_root / "mist_valley" / "items.yaml").read_text(encoding="utf-8") == items_before
    assert (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8") == npcs_before


def test_item_economy_save_uses_validation(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    graph_payload = client.get("/authoring/worlds/mist_valley/economy").json()
    graph_payload["items"][2]["base_price"] = 9

    saved = client.put("/authoring/worlds/mist_valley/economy", json={"graph": graph_payload})
    persisted = (worlds_root / "mist_valley" / "items.yaml").read_text(encoding="utf-8")

    assert saved.status_code == 200
    assert saved.json()["saved"] is True
    assert "base_price: 9" in persisted

    graph_payload["items"][2]["owner_id"] = "harlan"
    graph_payload["items"][2]["location_id"] = "village_square"
    rejected = client.put("/authoring/worlds/mist_valley/economy", json={"graph": graph_payload})
    persisted_after_reject = (worlds_root / "mist_valley" / "items.yaml").read_text(encoding="utf-8")

    assert rejected.status_code == 200
    assert rejected.json()["saved"] is False
    assert persisted_after_reject == persisted
