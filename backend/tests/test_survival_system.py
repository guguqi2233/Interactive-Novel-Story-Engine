from random import Random

from app.core.state_delta import apply_delta
from app.core.world_state import (
    GameState,
    LocationState,
    PlayerState,
    SurvivalState,
    TravelRouteState,
    WeatherState,
    WorldObjectState,
)
from app.engine.action_registry import ActionRegistry
from app.engine.actions.schemas import SuccessLevel
from app.engine.rules.survival import SurvivalActionHandler, survival_action_definitions
from app.llm.schemas import PlayerActionType, PlayerIntent


def _state(*, include_food: bool = True, weather_severity: int = 0) -> GameState:
    objects = {
        "waterskin": WorldObjectState(id="waterskin", owner_id="player", portable=True, tags=["water"]),
    }
    if include_food:
        objects["rations"] = WorldObjectState(id="rations", owner_id="player", portable=True, tags=["food"])
    return GameState(
        world_id="survival-test",
        turn=5,
        player=PlayerState(location_id="village"),
        locations={
            "village": LocationState(id="village", name="Village"),
            "pass": LocationState(id="pass", name="Mountain Pass"),
        },
        objects=objects,
        survival={"player": SurvivalState(actor_id="player", fatigue=20, hunger=40, thirst=30)},
        travel_routes={
            "village_to_pass": TravelRouteState(
                id="village_to_pass",
                from_location_id="village",
                to_location_id="pass",
                time_cost=180,
                fatigue_cost=15,
                hunger_cost=5,
                thirst_cost=8,
                risk_level=0,
            )
        },
        weather={"village": WeatherState(location_id="village", condition="storm", severity=weather_severity, tags=["bad_weather"])},
    )


def _intent(raw_text: str, target_id: str | None = None) -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.UNKNOWN,
        raw_text=raw_text,
        confidence=1.0,
        requires_clarification=False,
        target_id=target_id,
    )


def _apply_all(state: GameState, deltas: list) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_travel_route_advances_time_and_location() -> None:
    state = _state()

    execution = SurvivalActionHandler().resolve_with_event(_intent("travel route", "village_to_pass"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.SUCCESS
    assert next_state.player.location_id == "pass"
    assert next_state.current_time.minutes_of_day == state.current_time.minutes_of_day + 180


def test_travel_route_increases_fatigue() -> None:
    state = _state()

    execution = SurvivalActionHandler().resolve_with_event(_intent("travel route", "village_to_pass"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert next_state.survival["player"].fatigue == 35


def test_rest_reduces_fatigue() -> None:
    state = _state()

    execution = SurvivalActionHandler().resolve_with_event(_intent("rest"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert next_state.survival["player"].fatigue == 0
    assert next_state.survival["player"].last_rest_turn == 5


def test_consume_food_reduces_hunger() -> None:
    state = _state()

    execution = SurvivalActionHandler().resolve_with_event(_intent("consume food"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.SUCCESS
    assert next_state.survival["player"].hunger == 5
    assert next_state.objects["rations"].owner_id is None


def test_missing_food_fails() -> None:
    execution = SurvivalActionHandler().resolve_with_event(_intent("consume food"), _state(include_food=False), Random(1))

    assert execution.action_result.success_level == SuccessLevel.FAILURE
    assert execution.action_result.reason == "Missing food."
    assert execution.action_result.state_deltas == []


def test_bad_weather_affects_travel_check() -> None:
    state = _state(weather_severity=80)

    execution = SurvivalActionHandler().resolve_with_event(_intent("travel route", "village_to_pass"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert next_state.survival["player"].fatigue == 38


def test_save_load_preserves_survival_state() -> None:
    state = _state()
    restored = GameState.model_validate_json(state.model_dump_json())

    assert restored.survival["player"].hunger == 40
    assert restored.travel_routes["village_to_pass"].to_location_id == "pass"
    assert restored.weather["village"].condition == "storm"


def test_survival_actions_register_through_action_registry() -> None:
    registry = ActionRegistry(include_core=False)
    handler = SurvivalActionHandler()
    for definition in survival_action_definitions():
        registry.register_module_action(definition, module_id="survival", handler=handler)

    resolved = registry.get_handler_for_intent(_intent("travel route", "village_to_pass"), _state())

    assert resolved is not None
    assert registry.get_action_definition("survival.travel_route") is not None
