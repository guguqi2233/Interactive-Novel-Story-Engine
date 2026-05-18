import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.quality import QualityIssueSeverity
from app.quality.economy_balance import analyze_economy_balance


def test_negative_price_is_blocker(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        items_yaml="""
items:
  - id: cursed_coin
    name: Cursed Coin
    location_id: square
    base_price: -5
    tradeable: true
""",
    )

    report = analyze_economy_balance("test_world", worlds_root=tmp_path)

    assert report.negative_price_issues[0].severity == QualityIssueSeverity.BLOCKER
    assert report.negative_price_issues[0].safe_details["base_price"] == -5


def test_arbitrage_risk_is_reported(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        npcs_yaml="""
npcs:
  - id: mira
    name: Mira
    location_id: square
    personality: Sharp.
    merchant: true
    shop_inventory: [apple]
    buy_price_modifier: 0.5
    sell_price_modifier: 1.5
""",
    )

    report = analyze_economy_balance("test_world", worlds_root=tmp_path)

    assert report.arbitrage_risks[0].entity_id == "mira"
    assert report.arbitrage_risks[0].severity == QualityIssueSeverity.ERROR


def test_missing_shop_item_is_error(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        npcs_yaml="""
npcs:
  - id: mira
    name: Mira
    location_id: square
    personality: Sharp.
    merchant: true
    shop_inventory: [missing_apple]
""",
    )

    report = analyze_economy_balance("test_world", worlds_root=tmp_path)

    assert report.missing_shop_items[0].safe_details["item_id"] == "missing_apple"
    assert report.missing_shop_items[0].severity == QualityIssueSeverity.ERROR


def test_hidden_item_visible_in_shop_is_error_and_normal_report_is_safe(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        items_yaml="""
items:
  - id: hidden_gem
    name: Hidden Gem
    location_id: square
    base_price: 100
    tradeable: true
    hidden: true
""",
        npcs_yaml="""
npcs:
  - id: mira
    name: Mira
    location_id: square
    personality: Sharp.
    merchant: true
    shop_inventory: [hidden_gem]
""",
    )

    report = analyze_economy_balance("test_world", worlds_root=tmp_path)
    normal_payload = json.dumps(report.model_dump_normal(), ensure_ascii=False)
    debug_payload = json.dumps(report.model_dump(mode="json"), ensure_ascii=False)

    assert report.hidden_shop_items[0].severity == QualityIssueSeverity.ERROR
    assert "hidden_gem" not in normal_payload
    assert "Hidden Gem" not in normal_payload
    assert "hidden_gem" in debug_payload


def test_valid_economy_has_no_blocker(tmp_path: Path) -> None:
    write_world(tmp_path)

    report = analyze_economy_balance("test_world", worlds_root=tmp_path)

    assert not any(issue.severity == QualityIssueSeverity.BLOCKER for issue in report.quality_report.issues)
    assert not report.negative_price_issues
    assert not report.arbitrage_risks
    assert not report.missing_shop_items


def test_economy_balance_api(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        items_yaml="""
items:
  - id: cursed_coin
    name: Cursed Coin
    location_id: square
    base_price: -5
    tradeable: true
""",
    )
    previous_worlds_root = getattr(app.state, "worlds_root", None)
    app.state.worlds_root = tmp_path
    client = TestClient(app)
    try:
        response = client.post("/quality/worlds/test_world/economy/analyze", json={})
    finally:
        app.state.worlds_root = previous_worlds_root or "worlds"

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_id"] == "test_world"
    assert payload["negative_price_issues"][0]["severity"] == "blocker"


def write_world(
    root: Path,
    *,
    items_yaml: str | None = None,
    npcs_yaml: str | None = None,
    quests_yaml: str | None = None,
) -> None:
    world = root / "test_world"
    world.mkdir()
    (world / "manifest.yaml").write_text(
        """
world_id: test_world
name: Test World
version: "1.0"
start_location_id: square
""",
        encoding="utf-8",
    )
    (world / "locations.yaml").write_text(
        """
locations:
  - id: square
    name: Square
    description: Start.
    exits: {}
""",
        encoding="utf-8",
    )
    (world / "items.yaml").write_text(
        items_yaml
        or """
items:
  - id: apple
    name: Apple
    location_id: square
    base_price: 10
    tradeable: true
""",
        encoding="utf-8",
    )
    (world / "npcs.yaml").write_text(
        npcs_yaml
        or """
npcs:
  - id: mira
    name: Mira
    location_id: square
    personality: Sharp.
    merchant: true
    shop_inventory: [apple]
    buy_price_modifier: 1.0
    sell_price_modifier: 0.5
""",
        encoding="utf-8",
    )
    (world / "quests.yaml").write_text(quests_yaml or "quests: []\n", encoding="utf-8")
    (world / "facts.yaml").write_text("facts: []\n", encoding="utf-8")
    (world / "factions.yaml").write_text("factions: []\n", encoding="utf-8")
    (world / "rumors.yaml").write_text("rumors: []\n", encoding="utf-8")
    (world / "relationships.yaml").write_text("relationships: []\n", encoding="utf-8")
