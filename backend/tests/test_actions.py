from random import Random

from app.core.state_delta import apply_delta
from app.core.world_state import GameState, LocationState, NPCState, PlayerState
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.actions.schemas import SuccessLevel
from app.llm.schemas import PlayerActionType, PlayerIntent


def make_state() -> GameState:
    return GameState(
        world_id="test-world",
        turn=3,
        player=PlayerState(location_id="square", inventory=["iron_key"]),
        locations={
            "square": LocationState(
                id="square",
                name="Town Square",
                exits={"east": "smithy"},
                visible_objects=["well"],
            ),
            "smithy": LocationState(id="smithy", name="Blacksmith", exits={"west": "square"}),
            "forest": LocationState(id="forest", name="Forest"),
        },
        npcs={
            "harlan": NPCState(id="harlan", location_id="square"),
            "mira": NPCState(id="mira", location_id="forest"),
        },
    )


def make_intent(
    action_type: PlayerActionType,
    target_id: str | None = None,
    raw_text: str = "test",
) -> PlayerIntent:
    return PlayerIntent(
        action_type=action_type,
        target_id=target_id,
        raw_text=raw_text,
        confidence=1.0,
        requires_clarification=False,
    )


def test_observe_returns_current_location_visible_objects_only() -> None:
    result = ActionDispatcher().resolve(
        make_intent(PlayerActionType.OBSERVE),
        make_state(),
        Random(1),
    )

    assert result.success_level == SuccessLevel.SUCCESS
    assert result.state_deltas
    assert result.state_deltas[0].path == "current_time"
    assert result.visible_facts == ["square", "well", "harlan"]
    assert "mira" not in result.visible_facts


def test_move_requires_target_in_current_location_exits() -> None:
    state = make_state()
    result = ActionDispatcher().resolve(
        make_intent(PlayerActionType.MOVE, target_id="smithy"),
        state,
        Random(1),
    )

    assert result.success_level == SuccessLevel.SUCCESS
    assert result.state_deltas
    next_state = state
    for delta in result.state_deltas:
        next_state = apply_delta(next_state, delta)
    assert next_state.player.location_id == "smithy"


def test_move_fails_for_unreachable_target() -> None:
    result = ActionDispatcher().resolve(
        make_intent(PlayerActionType.MOVE, target_id="forest"),
        make_state(),
        Random(1),
    )

    assert result.success_level == SuccessLevel.FAILURE
    assert result.state_deltas == []


def test_talk_succeeds_only_for_present_npc() -> None:
    result = ActionDispatcher().resolve(
        make_intent(PlayerActionType.TALK, target_id="harlan"),
        make_state(),
        Random(1),
    )

    assert result.success_level == SuccessLevel.SUCCESS
    assert "harlan" in result.visible_facts


def test_talk_fails_for_absent_npc() -> None:
    result = ActionDispatcher().resolve(
        make_intent(PlayerActionType.TALK, target_id="mira"),
        make_state(),
        Random(1),
    )

    assert result.success_level == SuccessLevel.FAILURE
    assert result.state_deltas == []


def test_use_item_checks_inventory_structurally() -> None:
    result = ActionDispatcher().resolve(
        make_intent(PlayerActionType.USE_ITEM, target_id="iron_key"),
        make_state(),
        Random(1),
    )

    assert result.success_level == SuccessLevel.PARTIAL_SUCCESS
    assert result.visible_facts == ["iron_key"]
    assert result.hidden_facts == ["missing_item_rule"]


def test_wait_advances_time_with_delta() -> None:
    state = make_state()
    result = ActionDispatcher().resolve(
        make_intent(PlayerActionType.WAIT),
        state,
        Random(1),
    )

    assert result.success_level == SuccessLevel.SUCCESS
    assert result.state_deltas
    next_state = apply_delta(state, result.state_deltas[0])
    assert next_state.current_time.minutes_of_day == state.current_time.minutes_of_day + 30
