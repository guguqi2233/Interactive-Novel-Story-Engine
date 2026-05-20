from enum import StrEnum
from random import Random

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import CampState, GameState, SurvivalState, TravelRouteState, WeatherState
from app.engine.actions.base import ActionHandler
from app.engine.actions.declarative import (
    DeclarativeActionCategory,
    DeclarativeActionDefinition,
    DeclarativeOutcome,
    DeclarativeVisibilityPolicy,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.inventory import has_item
from app.engine.rules.life_state import can_move
from app.engine.rules.time import make_time_delta
from app.llm.schemas import PlayerActionType, PlayerIntent


class SurvivalActionType(StrEnum):
    TRAVEL_ROUTE = "travel_route"
    REST = "rest"
    CAMP = "camp"
    FORAGE = "forage"
    CONSUME_FOOD = "consume_food"
    CONSUME_WATER = "consume_water"


class SurvivalActionRule(BaseModel):
    action_type: SurvivalActionType
    label: str
    aliases: list[str] = Field(default_factory=list)
    time_cost: int = Field(default=0, ge=0)


class SurvivalAttemptResult(BaseModel):
    action_type: SurvivalActionType
    target_id: str | None
    action_result: ActionResult
    event: Event


class SurvivalModuleConfig(BaseModel):
    module_id: str = "survival"
    actions: dict[SurvivalActionType, SurvivalActionRule] = Field(default_factory=dict)
    food_item_tags: list[str] = Field(default_factory=lambda: ["food"])
    water_item_tags: list[str] = Field(default_factory=lambda: ["water"])


def default_survival_module_config() -> SurvivalModuleConfig:
    return SurvivalModuleConfig(
        actions={
            SurvivalActionType.TRAVEL_ROUTE: SurvivalActionRule(action_type=SurvivalActionType.TRAVEL_ROUTE, label="Travel Route", aliases=["travel route", "travel"], time_cost=0),
            SurvivalActionType.REST: SurvivalActionRule(action_type=SurvivalActionType.REST, label="Rest", aliases=["rest"], time_cost=60),
            SurvivalActionType.CAMP: SurvivalActionRule(action_type=SurvivalActionType.CAMP, label="Camp", aliases=["camp"], time_cost=90),
            SurvivalActionType.FORAGE: SurvivalActionRule(action_type=SurvivalActionType.FORAGE, label="Forage", aliases=["forage"], time_cost=45),
            SurvivalActionType.CONSUME_FOOD: SurvivalActionRule(action_type=SurvivalActionType.CONSUME_FOOD, label="Consume Food", aliases=["consume food", "eat"], time_cost=5),
            SurvivalActionType.CONSUME_WATER: SurvivalActionRule(action_type=SurvivalActionType.CONSUME_WATER, label="Consume Water", aliases=["consume water", "drink"], time_cost=5),
        }
    )


class SurvivalActionHandler(ActionHandler):
    action_type = PlayerActionType.UNKNOWN

    def __init__(self, config: SurvivalModuleConfig | None = None) -> None:
        self.config = config or default_survival_module_config()

    def can_handle(self, intent: PlayerIntent, state: GameState) -> bool:
        return self._rule_for_intent(intent) is not None

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        return self.resolve_with_event(intent, state, rng).action_result

    def resolve_with_event(self, intent: PlayerIntent, state: GameState, rng: Random | None = None) -> SurvivalAttemptResult:
        active_rng = rng or Random(0)
        rule = self._rule_for_intent(intent)
        if rule is None:
            return self._invalid(intent, state, "Unknown survival action.")
        event_id = f"event-{rule.action_type.value}-{intent.target_id or state.player.location_id}-{state.turn}"
        if rule.action_type == SurvivalActionType.TRAVEL_ROUTE:
            return self._travel(rule, event_id, intent, state, active_rng)
        if rule.action_type == SurvivalActionType.REST:
            return self._rest(rule, event_id, intent, state)
        if rule.action_type == SurvivalActionType.CAMP:
            return self._camp(rule, event_id, intent, state)
        if rule.action_type == SurvivalActionType.FORAGE:
            return self._forage(rule, event_id, intent, state, active_rng)
        if rule.action_type == SurvivalActionType.CONSUME_FOOD:
            return self._consume(rule, event_id, intent, state, food=True)
        if rule.action_type == SurvivalActionType.CONSUME_WATER:
            return self._consume(rule, event_id, intent, state, food=False)
        return self._invalid(intent, state, "Unsupported survival action.")

    def _rule_for_intent(self, intent: PlayerIntent) -> SurvivalActionRule | None:
        normalized = _normalized(intent.raw_text)
        for rule in self.config.actions.values():
            aliases = {rule.action_type.value, rule.action_type.value.replace("_", " "), rule.label.lower(), *[_normalized(alias) for alias in rule.aliases]}
            if normalized in aliases or any(normalized.startswith(alias) for alias in aliases):
                return rule
        return None

    def _travel(
        self,
        rule: SurvivalActionRule,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
        rng: Random,
    ) -> SurvivalAttemptResult:
        if not can_move(state, state.player.id):
            return self._result(rule, event_id, intent, state, SuccessLevel.FAILURE, "Player cannot travel.", [], visible_to_player=True)
        route = state.travel_routes.get(intent.target_id or "")
        if route is None or route.from_location_id != state.player.location_id:
            return self._result(rule, event_id, intent, state, SuccessLevel.INVALID, "Travel route is unavailable.", [], visible_to_player=False)
        if route.hidden and state.player.id not in route.discovered_by:
            return self._result(rule, event_id, intent, state, SuccessLevel.INVALID, "Travel route is hidden.", [], visible_to_player=False)
        survival = _survival_for_player(state)
        weather = state.weather.get(route.from_location_id)
        weather_penalty = weather.severity // 25 if weather else 0
        risk_roll = rng.randint(1, 100)
        risk_triggered = risk_roll <= route.risk_level + (weather.severity if weather else 0)
        fatigue_gain = route.fatigue_cost + weather_penalty
        deltas = [
            make_time_delta(state, route.time_cost).model_copy(update={"caused_by_event_id": event_id}),
            StateDelta(operation=StateDeltaOperation.SET, path="player.location_id", value=route.to_location_id, caused_by_event_id=event_id, reason="Travel route moved player."),
            StateDelta(operation=StateDeltaOperation.SET, path="survival.player.fatigue", value=min(100, survival.fatigue + fatigue_gain), caused_by_event_id=event_id, reason="Travel increased fatigue."),
            StateDelta(operation=StateDeltaOperation.SET, path="survival.player.hunger", value=min(100, survival.hunger + route.hunger_cost), caused_by_event_id=event_id, reason="Travel increased hunger."),
            StateDelta(operation=StateDeltaOperation.SET, path="survival.player.thirst", value=min(100, survival.thirst + route.thirst_cost), caused_by_event_id=event_id, reason="Travel increased thirst."),
        ]
        if risk_triggered:
            deltas.append(StateDelta(operation=StateDeltaOperation.SET, path="flags.travel_risk_triggered", value=True, caused_by_event_id=event_id, reason="Seeded travel risk triggered."))
        reason = "Travel route resolved by deterministic survival rules."
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS, reason, deltas, visible_to_player=True, visible_facts=[route.to_location_id])

    def _rest(self, rule: SurvivalActionRule, event_id: str, intent: PlayerIntent, state: GameState) -> SurvivalAttemptResult:
        survival = _survival_for_player(state)
        deltas = [
            make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id}),
            StateDelta(operation=StateDeltaOperation.SET, path="survival.player.fatigue", value=max(0, survival.fatigue - 30), caused_by_event_id=event_id, reason="Rest reduced fatigue."),
            StateDelta(operation=StateDeltaOperation.SET, path="survival.player.last_rest_turn", value=state.turn, caused_by_event_id=event_id, reason="Rest updated survival state."),
        ]
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS, "Rest resolved by survival rules.", deltas, visible_to_player=True)

    def _camp(self, rule: SurvivalActionRule, event_id: str, intent: PlayerIntent, state: GameState) -> SurvivalAttemptResult:
        camp_id = f"camp_{state.player.location_id}_{state.turn}"
        camp = CampState(id=camp_id, location_id=state.player.location_id, established_by=state.player.id, quality=50)
        deltas = [
            make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id}),
            StateDelta(operation=StateDeltaOperation.SET, path=f"camps.{camp_id}", value=camp.model_dump(mode="json"), caused_by_event_id=event_id, reason="Camp established."),
        ]
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS, "Camp established by local rules.", deltas, visible_to_player=True, visible_facts=[camp_id])

    def _forage(
        self,
        rule: SurvivalActionRule,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
        rng: Random,
    ) -> SurvivalAttemptResult:
        found = rng.randint(1, 100) > 40
        food_id = f"foraged_food_{state.turn}"
        deltas = [make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id})]
        if found:
            from app.core.world_state import WorldObjectState

            food = WorldObjectState(id=food_id, name="Foraged Food", owner_id=state.player.id, portable=True, tags=["food"])
            deltas.append(StateDelta(operation=StateDeltaOperation.SET, path=f"objects.{food_id}", value=food.model_dump(mode="json"), caused_by_event_id=event_id, reason="Forage found food."))
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS if found else SuccessLevel.FAILURE, "Forage resolved by seeded survival rules.", deltas, visible_to_player=True, visible_facts=[food_id] if found else [])

    def _consume(
        self,
        rule: SurvivalActionRule,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
        *,
        food: bool,
    ) -> SurvivalAttemptResult:
        item_id = _find_consumable(state, self.config.food_item_tags if food else self.config.water_item_tags)
        if item_id is None:
            return self._result(rule, event_id, intent, state, SuccessLevel.FAILURE, f"Missing {'food' if food else 'water'}.", [], visible_to_player=True)
        survival = _survival_for_player(state)
        field = "hunger" if food else "thirst"
        current = survival.hunger if food else survival.thirst
        deltas = [
            make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id}),
            StateDelta(operation=StateDeltaOperation.SET, path=f"survival.player.{field}", value=max(0, current - 35), caused_by_event_id=event_id, reason=f"Consumed {'food' if food else 'water'} reduced {field}."),
            StateDelta(operation=StateDeltaOperation.SET, path=f"objects.{item_id}.owner_id", value=None, caused_by_event_id=event_id, reason="Survival consumed item ownership."),
            StateDelta(operation=StateDeltaOperation.ADD, path=f"objects.{item_id}.tags", value="consumed", caused_by_event_id=event_id, reason="Survival marked consumable item."),
        ]
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS, f"Consumed {'food' if food else 'water'}.", deltas, visible_to_player=True)

    def _result(
        self,
        rule: SurvivalActionRule,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
        level: SuccessLevel,
        reason: str,
        deltas: list[StateDelta],
        *,
        visible_to_player: bool,
        visible_facts: list[str] | None = None,
    ) -> SurvivalAttemptResult:
        result = ActionResult(success_level=level, reason=reason, state_deltas=deltas, visible_facts=sorted(set(visible_facts or [])))
        event = Event(
            event_id=event_id,
            turn=state.turn,
            actor_id=state.player.id,
            action_type=rule.action_type.value,
            result=level.value,
            visible_to_player=visible_to_player,
            target_id=intent.target_id,
            input_text=intent.raw_text,
            state_deltas=deltas,
            allow_empty_delta=not deltas,
        )
        return SurvivalAttemptResult(action_type=rule.action_type, target_id=intent.target_id, action_result=result, event=event)

    def _invalid(self, intent: PlayerIntent, state: GameState, reason: str) -> SurvivalAttemptResult:
        rule = SurvivalActionRule(action_type=SurvivalActionType.TRAVEL_ROUTE, label="Survival")
        return self._result(rule, f"event-survival-invalid-{state.turn}", intent, state, SuccessLevel.INVALID, reason, [], visible_to_player=False)


def survival_action_definitions(config: SurvivalModuleConfig | None = None) -> list[DeclarativeActionDefinition]:
    active = config or default_survival_module_config()
    return [
        DeclarativeActionDefinition(
            id=f"survival.{rule.action_type.value}",
            label=rule.label,
            aliases=rule.aliases,
            category=DeclarativeActionCategory.TRAVEL,
            outcomes={SuccessLevel.SUCCESS: DeclarativeOutcome(success_level=SuccessLevel.SUCCESS, reason=f"{rule.label} is resolved by deterministic survival rules.")},
            event_type=f"survival.{rule.action_type.value}.resolved",
            visibility_policy=DeclarativeVisibilityPolicy(hidden_outcome_player_visible=False),
        )
        for rule in active.actions.values()
    ]


def _survival_for_player(state: GameState) -> SurvivalState:
    return state.survival.get(state.player.id) or SurvivalState(actor_id=state.player.id)


def _find_consumable(state: GameState, tags: list[str]) -> str | None:
    wanted = set(tags)
    for item in state.objects.values():
        if item.owner_id == state.player.id and wanted.intersection(item.tags):
            return item.id
    return None


def _normalized(value: str) -> str:
    return value.strip().lower().replace("_", " ")

