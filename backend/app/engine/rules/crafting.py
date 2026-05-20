from enum import StrEnum
from random import Random

from pydantic import BaseModel, Field, field_validator

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import CraftingStationState, GameState, WorldObjectState
from app.engine.actions.base import ActionHandler
from app.engine.actions.declarative import (
    DeclarativeActionCategory,
    DeclarativeActionDefinition,
    DeclarativeOutcome,
    DeclarativeVisibilityPolicy,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.inventory import has_item, item_is_accessible
from app.engine.rules.time import make_time_delta
from app.llm.schemas import PlayerActionType, PlayerIntent


class CraftingActionType(StrEnum):
    CRAFT_ITEM = "craft_item"
    REPAIR_ITEM = "repair_item"
    DISMANTLE_ITEM = "dismantle_item"


class CraftingFailurePolicy(StrEnum):
    NO_CONSUME = "no_consume"
    CONSUME_TIME = "consume_time"
    CONSUME_PARTIAL_MATERIALS = "consume_partial_materials"


class RecipeDefinition(BaseModel):
    id: str
    output_item_id: str
    required_items: list[str] = Field(default_factory=list)
    consumed_items: list[str] = Field(default_factory=list)
    required_station_tags: list[str] = Field(default_factory=list)
    required_skill: str | None = None
    time_cost: int = Field(default=0, ge=0)
    failure_policy: CraftingFailurePolicy = CraftingFailurePolicy.NO_CONSUME
    aliases: list[str] = Field(default_factory=list)

    @field_validator("id", "output_item_id")
    @classmethod
    def validate_safe_id(cls, value: str) -> str:
        if not value or any(token in value for token in ("/", "\\", "..", "`", "$")):
            raise ValueError("Crafting ids must be safe local identifiers")
        return value


class CraftingAttemptResult(BaseModel):
    recipe_id: str | None
    action_type: CraftingActionType
    action_result: ActionResult
    event: Event


class CraftingModuleConfig(BaseModel):
    module_id: str = "crafting"
    recipes: dict[str, RecipeDefinition] = Field(default_factory=dict)


class CraftingActionHandler(ActionHandler):
    action_type = PlayerActionType.UNKNOWN

    def __init__(self, config: CraftingModuleConfig) -> None:
        self.config = config

    def can_handle(self, intent: PlayerIntent, state: GameState) -> bool:
        return self._recipe_for_intent(intent) is not None or _normalized(intent.raw_text).startswith(("craft", "repair", "dismantle"))

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        return self.resolve_with_event(intent, state, rng).action_result

    def resolve_with_event(self, intent: PlayerIntent, state: GameState, rng: Random | None = None) -> CraftingAttemptResult:
        recipe = self._recipe_for_intent(intent)
        action_type = self._action_type_for_intent(intent)
        event_id = f"event-{action_type.value}-{recipe.id if recipe else 'unknown'}-{state.turn}"
        if recipe is None:
            return self._result(None, action_type, event_id, intent, state, SuccessLevel.INVALID, "Unknown recipe.", [], visible_to_player=False)

        issue = self._validate_recipe(recipe, state)
        if issue is not None:
            deltas = self._failure_deltas(recipe, event_id, state)
            return self._result(recipe, action_type, event_id, intent, state, SuccessLevel.FAILURE, issue, deltas, visible_to_player=True)

        deltas = self._success_deltas(recipe, event_id, state)
        return self._result(
            recipe,
            action_type,
            event_id,
            intent,
            state,
            SuccessLevel.SUCCESS,
            "Crafting recipe resolved by deterministic local rules.",
            deltas,
            visible_to_player=True,
            visible_facts=[recipe.output_item_id],
        )

    def _recipe_for_intent(self, intent: PlayerIntent) -> RecipeDefinition | None:
        normalized = _normalized(intent.raw_text)
        for recipe in self.config.recipes.values():
            aliases = {
                recipe.id,
                recipe.output_item_id,
                f"craft {recipe.output_item_id}",
                f"repair {recipe.output_item_id}",
                f"dismantle {recipe.output_item_id}",
                *[_normalized(alias) for alias in recipe.aliases],
            }
            if normalized in aliases:
                return recipe
        return None

    def _action_type_for_intent(self, intent: PlayerIntent) -> CraftingActionType:
        normalized = _normalized(intent.raw_text)
        if normalized.startswith("repair"):
            return CraftingActionType.REPAIR_ITEM
        if normalized.startswith("dismantle"):
            return CraftingActionType.DISMANTLE_ITEM
        return CraftingActionType.CRAFT_ITEM

    def _validate_recipe(self, recipe: RecipeDefinition, state: GameState) -> str | None:
        for item_id in recipe.required_items:
            if not has_item(state, state.player.id, item_id):
                return f"Missing required item: {item_id}"
        for item_id in recipe.consumed_items:
            if not has_item(state, state.player.id, item_id):
                return f"Missing consumed material: {item_id}"
        if recipe.required_station_tags and self._matching_station(state, recipe) is None:
            return "Missing required crafting station."
        return None

    def _matching_station(self, state: GameState, recipe: RecipeDefinition) -> CraftingStationState | None:
        required = set(recipe.required_station_tags)
        for station in state.crafting_stations.values():
            if station.location_id != state.player.location_id:
                continue
            if not station.visible or (station.hidden and state.player.id not in station.discovered_by):
                continue
            if required.issubset(set(station.tags)):
                return station
        return None

    def _success_deltas(self, recipe: RecipeDefinition, event_id: str, state: GameState) -> list[StateDelta]:
        deltas: list[StateDelta] = []
        for item_id in recipe.consumed_items:
            deltas.extend(_consume_item_deltas(item_id, event_id))
        deltas.extend(_output_item_deltas(recipe.output_item_id, event_id, state))
        if recipe.time_cost > 0:
            deltas.append(make_time_delta(state, recipe.time_cost).model_copy(update={"caused_by_event_id": event_id}))
        return deltas

    def _failure_deltas(self, recipe: RecipeDefinition, event_id: str, state: GameState) -> list[StateDelta]:
        deltas: list[StateDelta] = []
        if recipe.failure_policy == CraftingFailurePolicy.CONSUME_TIME and recipe.time_cost > 0:
            deltas.append(make_time_delta(state, recipe.time_cost).model_copy(update={"caused_by_event_id": event_id}))
        if recipe.failure_policy == CraftingFailurePolicy.CONSUME_PARTIAL_MATERIALS and recipe.consumed_items:
            deltas.extend(_consume_item_deltas(recipe.consumed_items[0], event_id))
        return deltas

    def _result(
        self,
        recipe: RecipeDefinition | None,
        action_type: CraftingActionType,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
        level: SuccessLevel,
        reason: str,
        deltas: list[StateDelta],
        *,
        visible_to_player: bool,
        visible_facts: list[str] | None = None,
    ) -> CraftingAttemptResult:
        action_result = ActionResult(
            success_level=level,
            reason=reason,
            state_deltas=deltas,
            visible_facts=sorted(set(visible_facts or [])),
        )
        event = Event(
            event_id=event_id,
            turn=state.turn,
            actor_id=state.player.id,
            action_type=action_type.value,
            result=level.value,
            visible_to_player=visible_to_player,
            target_id=intent.target_id,
            input_text=intent.raw_text,
            state_deltas=deltas,
            allow_empty_delta=not deltas,
        )
        return CraftingAttemptResult(recipe_id=recipe.id if recipe else None, action_type=action_type, action_result=action_result, event=event)


def crafting_action_definitions(config: CraftingModuleConfig | None = None) -> list[DeclarativeActionDefinition]:
    return [
        DeclarativeActionDefinition(
            id=f"crafting.{action_type.value}",
            label=action_type.value.replace("_", " ").title(),
            aliases=[action_type.value.replace("_", " ")],
            category=DeclarativeActionCategory.CRAFTING,
            outcomes={
                SuccessLevel.SUCCESS: DeclarativeOutcome(
                    success_level=SuccessLevel.SUCCESS,
                    reason=f"{action_type.value} is resolved by deterministic crafting rules.",
                )
            },
            event_type=f"crafting.{action_type.value}.resolved",
            visibility_policy=DeclarativeVisibilityPolicy(hidden_outcome_player_visible=False),
        )
        for action_type in CraftingActionType
    ]


def _consume_item_deltas(item_id: str, event_id: str) -> list[StateDelta]:
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.owner_id",
            value=None,
            caused_by_event_id=event_id,
            reason="Crafting consumed item ownership.",
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.location_id",
            value=None,
            caused_by_event_id=event_id,
            reason="Crafting consumed item location.",
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.container_id",
            value=None,
            caused_by_event_id=event_id,
            reason="Crafting consumed item container.",
        ),
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"objects.{item_id}.tags",
            value="consumed",
            caused_by_event_id=event_id,
            reason="Crafting marked item as consumed.",
        ),
    ]


def _output_item_deltas(item_id: str, event_id: str, state: GameState) -> list[StateDelta]:
    existing = state.objects.get(item_id)
    if existing is None:
        crafted_item = WorldObjectState(
            id=item_id,
            name=item_id.replace("_", " ").title(),
            owner_id=state.player.id,
            portable=True,
            visible=True,
            tags=["crafted"],
        )
        return [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"objects.{item_id}",
                value=crafted_item.model_dump(mode="json"),
                caused_by_event_id=event_id,
                reason="Crafting created output item.",
            )
        ]
    if item_is_accessible(state, state.player.id, item_id):
        return [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"objects.{item_id}.owner_id",
                value=state.player.id,
                caused_by_event_id=event_id,
                reason="Crafting placed existing output item in inventory.",
            ),
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"objects.{item_id}.location_id",
                value=None,
                caused_by_event_id=event_id,
                reason="Crafted output no longer belongs to a location.",
            ),
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"objects.{item_id}.container_id",
                value=None,
                caused_by_event_id=event_id,
                reason="Crafted output no longer belongs to a container.",
            ),
        ]
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.owner_id",
            value=state.player.id,
            caused_by_event_id=event_id,
            reason="Crafting awarded output item.",
        )
    ]


def _normalized(value: str) -> str:
    return value.strip().lower().replace("_", " ")

