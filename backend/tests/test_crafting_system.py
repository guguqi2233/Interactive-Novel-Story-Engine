from random import Random

from app.core.state_delta import apply_delta
from app.core.world_state import CraftingStationState, GameState, LocationState, PlayerState, WorldObjectState
from app.engine.action_registry import ActionRegistry
from app.engine.actions.schemas import SuccessLevel
from app.engine.rules.crafting import (
    CraftingActionHandler,
    CraftingFailurePolicy,
    CraftingModuleConfig,
    RecipeDefinition,
    crafting_action_definitions,
)
from app.llm.schemas import PlayerActionType, PlayerIntent


def _state(*, include_wood: bool = True, include_station: bool = True) -> GameState:
    objects = {
        "hammer": WorldObjectState(id="hammer", owner_id="player", portable=True, tags=["tool"]),
        "plank": WorldObjectState(id="plank", owner_id="player", portable=True),
    }
    if include_wood:
        objects["wood"] = WorldObjectState(id="wood", owner_id="player", portable=True)
    stations = {}
    if include_station:
        stations["bench"] = CraftingStationState(id="bench", location_id="workshop", tags=["workbench"])
    return GameState(
        world_id="crafting-test",
        turn=4,
        player=PlayerState(location_id="workshop"),
        locations={"workshop": LocationState(id="workshop", name="Workshop")},
        objects=objects,
        crafting_stations=stations,
    )


def _recipe(**updates: object) -> RecipeDefinition:
    payload = {
        "id": "make_chair",
        "output_item_id": "chair",
        "required_items": ["hammer", "wood"],
        "consumed_items": ["wood"],
        "required_station_tags": ["workbench"],
        "time_cost": 30,
        "aliases": ["craft chair"],
    }
    payload.update(updates)
    return RecipeDefinition.model_validate(payload)


def _handler(recipe: RecipeDefinition | None = None) -> CraftingActionHandler:
    active_recipe = recipe or _recipe()
    return CraftingActionHandler(CraftingModuleConfig(recipes={active_recipe.id: active_recipe}))


def _intent(raw_text: str = "craft chair") -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.UNKNOWN,
        raw_text=raw_text,
        confidence=1.0,
        requires_clarification=False,
    )


def _apply_all(state: GameState, deltas: list) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_craft_item_success_consumes_material_and_generates_item() -> None:
    state = _state()

    execution = _handler().resolve_with_event(_intent(), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.SUCCESS
    assert next_state.objects["wood"].owner_id is None
    assert "consumed" in next_state.objects["wood"].tags
    assert next_state.objects["chair"].owner_id == "player"
    assert "crafted" in next_state.objects["chair"].tags


def test_missing_material_fails() -> None:
    execution = _handler().resolve_with_event(_intent(), _state(include_wood=False), Random(1))

    assert execution.action_result.success_level == SuccessLevel.FAILURE
    assert "Missing required item" in execution.action_result.reason


def test_missing_station_fails() -> None:
    execution = _handler().resolve_with_event(_intent(), _state(include_station=False), Random(1))

    assert execution.action_result.success_level == SuccessLevel.FAILURE
    assert execution.action_result.reason == "Missing required crafting station."


def test_non_consumed_tool_is_not_consumed() -> None:
    state = _state()
    execution = _handler().resolve_with_event(_intent(), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert next_state.objects["hammer"].owner_id == "player"
    assert "consumed" not in next_state.objects["hammer"].tags


def test_failure_policy_can_consume_partial_materials() -> None:
    recipe = _recipe(
        required_items=["hammer", "wood", "gem"],
        consumed_items=["wood", "gem"],
        failure_policy=CraftingFailurePolicy.CONSUME_PARTIAL_MATERIALS,
    )
    state = _state()

    execution = _handler(recipe).resolve_with_event(_intent(), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.FAILURE
    assert next_state.objects["wood"].owner_id is None
    assert "gem" not in next_state.objects


def test_inventory_output_does_not_conflict_with_existing_location_item() -> None:
    state = _state().model_copy(deep=True)
    state.objects["chair"] = WorldObjectState(id="chair", location_id="workshop", portable=True, visible=True)

    execution = _handler().resolve_with_event(_intent(), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert next_state.objects["chair"].owner_id == "player"
    assert next_state.objects["chair"].location_id is None
    assert next_state.objects["chair"].container_id is None


def test_save_load_preserves_crafted_item() -> None:
    state = _state()
    execution = _handler().resolve_with_event(_intent(), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    restored = GameState.model_validate_json(next_state.model_dump_json())

    assert restored.objects["chair"].owner_id == "player"
    assert restored.crafting_stations["bench"].tags == ["workbench"]


def test_crafting_action_registers_through_action_registry() -> None:
    registry = ActionRegistry(include_core=False)
    handler = _handler()
    for definition in crafting_action_definitions():
        registry.register_module_action(definition, module_id="crafting", handler=handler)

    resolved = registry.get_handler_for_intent(_intent(), _state())

    assert resolved is not None
    assert registry.get_action_definition("crafting.craft_item") is not None
