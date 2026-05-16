import pytest
from pydantic import ValidationError

from app.core.state_delta import apply_delta
from app.core.world_state import GameState, LocationState, PlayerState, WorldObjectState
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.rules.inventory import (
    can_pick_up,
    drop_item,
    get_inventory,
    has_item,
    pick_up_item,
)
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.session_store import build_visible_state


def make_state() -> GameState:
    return GameState(
        world_id="inventory-test",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Square")},
        objects={
            "coin": WorldObjectState(
                id="coin",
                name="Coin",
                location_id="square",
                portable=True,
            ),
            "anvil": WorldObjectState(
                id="anvil",
                name="Anvil",
                location_id="square",
                portable=False,
            ),
            "hidden_key": WorldObjectState(
                id="hidden_key",
                name="Hidden Key",
                location_id="square",
                portable=True,
                hidden=True,
            ),
            "owned_knife": WorldObjectState(
                id="owned_knife",
                name="Owned Knife",
                owner_id="player",
                portable=True,
            ),
        },
    )


def use_item_intent(item_id: str) -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.USE_ITEM,
        target_id=item_id,
        raw_text=f"use {item_id}",
        confidence=1.0,
        requires_clarification=False,
    )


def test_player_can_pick_up_portable_item() -> None:
    state = make_state()

    assert can_pick_up(state, "player", "coin").allowed is True
    assert pick_up_item(state, "player", "coin")


def test_player_cannot_pick_up_non_portable_item() -> None:
    state = make_state()

    result = can_pick_up(state, "player", "anvil")

    assert result.allowed is False
    assert result.reason == "Item is not portable."


def test_hidden_item_cannot_be_picked_up_before_discovery() -> None:
    state = make_state()

    result = can_pick_up(state, "player", "hidden_key")

    assert result.allowed is False
    assert result.reason == "Item has not been discovered."


def test_pick_up_sets_owner_and_clears_location() -> None:
    state = make_state()
    next_state = state

    for delta in pick_up_item(state, "player", "coin"):
        next_state = apply_delta(next_state, delta)

    assert next_state.objects["coin"].owner_id == "player"
    assert next_state.objects["coin"].location_id is None
    assert next_state.objects["coin"].container_id is None
    assert has_item(next_state, "player", "coin") is True


def test_drop_item_places_item_at_current_location() -> None:
    state = make_state()
    next_state = state

    for delta in drop_item(state, "player", "owned_knife"):
        next_state = apply_delta(next_state, delta)

    assert next_state.objects["owned_knife"].owner_id is None
    assert next_state.objects["owned_knife"].container_id is None
    assert next_state.objects["owned_knife"].location_id == "square"


def test_use_item_checks_ownership_or_accessibility() -> None:
    state = make_state()

    owned_result = ActionDispatcher().resolve(use_item_intent("owned_knife"), state)
    accessible_result = ActionDispatcher().resolve(use_item_intent("coin"), state)
    hidden_result = ActionDispatcher().resolve(use_item_intent("hidden_key"), state)

    assert owned_result.success_level == "partial_success"
    assert accessible_result.success_level == "partial_success"
    assert hidden_result.success_level == "failure"


def test_visible_inventory_only_shows_owned_items() -> None:
    visible_state = build_visible_state(make_state())

    assert [item.id for item in visible_state.inventory] == ["owned_knife"]
    assert "coin" not in str(visible_state.inventory)


def test_get_inventory_uses_item_owner() -> None:
    inventory = get_inventory(make_state(), "player")

    assert [item.id for item in inventory] == ["owned_knife"]


def test_item_cannot_have_conflicting_placement() -> None:
    with pytest.raises(ValidationError, match="multiple placements"):
        WorldObjectState(
            id="bad_item",
            location_id="square",
            owner_id="player",
        )
