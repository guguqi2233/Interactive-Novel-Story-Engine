from pathlib import Path

from app.core.state_delta import apply_delta
from app.core.world_state import FactionState, GameState, LocationState, NPCState, PlayerState, ReputationState, WorldObjectState
from app.db.repository import SQLiteSaveRepository
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.rules.economy import buy_item, can_buy, can_sell, get_item_price, get_shop_inventory, sell_item
from app.llm.schemas import PlayerActionType, PlayerIntent


def make_state(currency: int = 20, reputation: int = 0) -> GameState:
    return GameState(
        world_id="economy-test",
        player=PlayerState(location_id="market", currency=currency),
        locations={"market": LocationState(id="market", name="Market")},
        factions={
            "guild": FactionState(
                id="guild",
                name="Guild",
                reputation=ReputationState(value=reputation, known_to_player=True),
                known_by_player=True,
            )
        },
        npcs={
            "mira": NPCState(
                id="mira",
                location_id="market",
                faction_id="guild",
                merchant=True,
                shop_inventory=["apple", "hidden_gem"],
                buy_price_modifier=1.0,
                sell_price_modifier=0.5,
            )
        },
        objects={
            "apple": WorldObjectState(
                id="apple",
                owner_id="mira",
                portable=True,
                base_price=10,
                tradeable=True,
                rarity="common",
            ),
            "hidden_gem": WorldObjectState(
                id="hidden_gem",
                owner_id="mira",
                portable=True,
                hidden=True,
                base_price=100,
                tradeable=True,
                rarity="rare",
            ),
            "keepsake": WorldObjectState(
                id="keepsake",
                owner_id="player",
                portable=True,
                base_price=30,
                tradeable=False,
            ),
            "herb": WorldObjectState(
                id="herb",
                owner_id="player",
                portable=True,
                base_price=12,
                tradeable=True,
            ),
            "stolen_ring": WorldObjectState(
                id="stolen_ring",
                owner_id="player",
                portable=True,
                base_price=50,
                tradeable=True,
                tags=["stolen"],
            ),
        },
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def make_intent(action_type: PlayerActionType, target_id: str) -> PlayerIntent:
    return PlayerIntent(
        action_type=action_type,
        target_id=target_id,
        raw_text=f"{action_type.value} {target_id}",
        confidence=1.0,
        requires_clarification=False,
    )


def test_player_can_buy_tradeable_item() -> None:
    state = make_state(currency=20)
    result = can_buy(state, "mira", "apple")
    next_state = apply_all(state, buy_item(state, "mira", "apple"))

    assert result.allowed
    assert result.price == 10
    assert next_state.player.currency == 10
    assert next_state.objects["apple"].owner_id == "player"
    assert "apple" not in next_state.npcs["mira"].shop_inventory


def test_insufficient_balance_cannot_buy() -> None:
    state = make_state(currency=5)

    result = can_buy(state, "mira", "apple")

    assert not result.allowed
    assert result.reason == "Not enough currency."


def test_player_can_sell_owned_tradeable_item() -> None:
    state = make_state(currency=0)
    result = can_sell(state, "mira", "herb")
    next_state = apply_all(state, sell_item(state, "mira", "herb"))

    assert result.allowed
    assert result.price == 6
    assert next_state.player.currency == 6
    assert next_state.objects["herb"].owner_id == "mira"
    assert "herb" in next_state.npcs["mira"].shop_inventory


def test_non_tradeable_item_cannot_be_sold() -> None:
    result = can_sell(make_state(), "mira", "keepsake")

    assert not result.allowed
    assert result.reason == "Item is not tradeable."


def test_stolen_item_is_refused() -> None:
    result = can_sell(make_state(), "mira", "stolen_ring")

    assert not result.allowed
    assert result.reason == "Merchant refuses stolen item."


def test_reputation_affects_price() -> None:
    hostile_price = get_item_price(make_state(reputation=-50), "apple", "mira", "buy")
    trusted_price = get_item_price(make_state(reputation=60), "apple", "mira", "buy")

    assert hostile_price == 15
    assert trusted_price == 8


def test_trade_action_generates_state_deltas() -> None:
    state = make_state(currency=20)
    result = ActionDispatcher().resolve(make_intent(PlayerActionType.BUY, "apple@mira"), state)
    next_state = apply_all(state, result.state_deltas)

    assert result.success_level == "success"
    assert any(delta.path == "player.currency" for delta in result.state_deltas)
    assert next_state.objects["apple"].owner_id == "player"


def test_hidden_item_not_in_shop_inventory() -> None:
    inventory = get_shop_inventory(make_state(), "mira")

    assert [item.id for item in inventory] == ["apple"]


def test_save_load_preserves_economy_state(tmp_path: Path) -> None:
    state = apply_all(make_state(currency=20), buy_item(make_state(currency=20), "mira", "apple"))
    repository = SQLiteSaveRepository(tmp_path / "economy.db")

    repository.create_save("save-1", state)
    loaded = repository.load_save("save-1")

    assert loaded.player.currency == state.player.currency
    assert loaded.objects["apple"].owner_id == "player"
    assert loaded.npcs["mira"].shop_inventory == ["hidden_gem"]
