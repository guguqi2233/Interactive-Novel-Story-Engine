from enum import StrEnum
from random import Random
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactVisibility, GameState
from app.engine.actions.base import ActionHandler
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.time import make_time_delta
from app.engine.rules.visibility import get_visible_facts
from app.llm.schemas import PlayerActionType, PlayerIntent


class DeclarativeTargetKind(StrEnum):
    SELF = "self"
    CURRENT_LOCATION = "current_location"
    LOCATION = "location"
    OBJECT = "object"
    NPC = "npc"


class DeclarativeConditionType(StrEnum):
    ALWAYS = "always"
    FLAG_EQUALS = "flag_equals"
    FACT_VISIBLE = "fact_visible"
    TARGET_VISIBLE = "target_visible"
    AT_LOCATION = "at_location"


class DeclarativeCheckType(StrEnum):
    ALWAYS = "always"
    FLAG_EQUALS = "flag_equals"
    TARGET_VISIBLE = "target_visible"


class DeclarativeActionCategory(StrEnum):
    GENERAL = "general"
    MAGIC = "magic"
    HACKING = "hacking"
    CRAFTING = "crafting"
    INVESTIGATION = "investigation"
    TRAVEL = "travel"
    STEALTH = "stealth"
    COMBAT = "combat"
    SOCIAL = "social"
    FACTION = "faction"
    DOMAIN = "domain"


class DeclarativeActionTargetSpec(BaseModel):
    kind: DeclarativeTargetKind
    required: bool = True
    allowed_ids: list[str] = Field(default_factory=list)


class DeclarativeAffordanceRequirement(BaseModel):
    required_visible_facts: list[str] = Field(default_factory=list)
    required_flags: dict[str, bool | int | float | str] = Field(default_factory=dict)


class DeclarativeCondition(BaseModel):
    condition_type: DeclarativeConditionType
    key: str | None = None
    value: Any = None
    expected: Any = True


class DeclarativeCheck(BaseModel):
    check_type: DeclarativeCheckType
    key: str | None = None
    value: Any = None
    expected: Any = True


class DeclarativeStateDeltaTemplate(BaseModel):
    operation: StateDeltaOperation
    path: str
    value: Any = None
    reason: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("path")
    @classmethod
    def validate_template_path(cls, value: str) -> str:
        if value.startswith(("player_visible_facts", "npc_knowledge")):
            raise ValueError("Declarative action templates cannot directly write visibility or NPC knowledge")
        return value

    def to_delta(self, *, event_id: str, target_id: str | None) -> StateDelta:
        value = _replace_placeholders(self.value, target_id=target_id)
        metadata = {
            key: str(_replace_placeholders(value, target_id=target_id))
            for key, value in self.metadata.items()
        }
        return StateDelta(
            operation=self.operation,
            path=_replace_placeholders(self.path, target_id=target_id),
            value=value,
            caused_by_event_id=event_id,
            reason=self.reason,
            metadata=metadata,
        )


class DeclarativeOutcome(BaseModel):
    success_level: SuccessLevel
    reason: str
    state_delta_templates: list[DeclarativeStateDeltaTemplate] = Field(default_factory=list)
    visible_facts: list[str] = Field(default_factory=list)
    hidden_facts: list[str] = Field(default_factory=list)
    hidden_outcome: bool = False


class DeclarativeVisibilityPolicy(BaseModel):
    hidden_outcome_player_visible: bool = False
    include_target_in_visible_facts: bool = True
    include_current_location_in_visible_facts: bool = True


class DeclarativeNarratorHints(BaseModel):
    style: str = ""
    safe_summary: str = ""
    hidden_summary: str = ""


class DeclarativeActionDefinition(BaseModel):
    id: str
    label: str
    aliases: list[str] = Field(default_factory=list)
    category: DeclarativeActionCategory = DeclarativeActionCategory.GENERAL
    target_specs: list[DeclarativeActionTargetSpec] = Field(default_factory=list)
    affordance_requirements: DeclarativeAffordanceRequirement = Field(default_factory=DeclarativeAffordanceRequirement)
    time_cost: int = Field(default=0, ge=0)
    preconditions: list[DeclarativeCondition] = Field(default_factory=list)
    checks: list[DeclarativeCheck] = Field(default_factory=list)
    outcomes: dict[SuccessLevel, DeclarativeOutcome]
    state_delta_templates: list[DeclarativeStateDeltaTemplate] = Field(default_factory=list)
    event_type: str
    visibility_policy: DeclarativeVisibilityPolicy = Field(default_factory=DeclarativeVisibilityPolicy)
    narrator_hints: DeclarativeNarratorHints = Field(default_factory=DeclarativeNarratorHints)

    @field_validator("id", "event_type")
    @classmethod
    def validate_safe_id(cls, value: str) -> str:
        if not value or any(part in value for part in ["/", "\\", ".."]):
            raise ValueError("Declarative action ids must be safe local identifiers")
        return value


class DeclarativeActionExecution(BaseModel):
    action_result: ActionResult
    event: Event


class DeclarativeActionHandler(ActionHandler):
    action_type = PlayerActionType.UNKNOWN

    def __init__(self, definition: DeclarativeActionDefinition) -> None:
        self.definition = definition

    def can_handle(self, intent: PlayerIntent, state: GameState) -> bool:
        normalized = intent.raw_text.strip().lower()
        return normalized in {self.definition.id.lower(), *[alias.lower() for alias in self.definition.aliases]}

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        return self.resolve_with_event(intent, state, rng).action_result

    def resolve_with_event(self, intent: PlayerIntent, state: GameState, rng: Random | None = None) -> DeclarativeActionExecution:
        event_id = f"event-{self.definition.id}-{state.turn}"
        target_issue = self._validate_target(intent, state)
        if target_issue:
            return self._execution(event_id, state, intent, SuccessLevel.INVALID, target_issue, [])

        precondition_issue = self._check_preconditions(intent, state)
        if precondition_issue:
            return self._execution(event_id, state, intent, SuccessLevel.FAILURE, precondition_issue, [])

        check_issue = self._run_checks(intent, state)
        selected_level = SuccessLevel.FAILURE if check_issue else SuccessLevel.SUCCESS
        outcome = self.definition.outcomes.get(selected_level) or self.definition.outcomes.get(SuccessLevel.SUCCESS)
        if outcome is None:
            return self._execution(event_id, state, intent, SuccessLevel.INVALID, "Declarative action has no usable outcome.", [])

        deltas = self._deltas_for_outcome(event_id, intent.target_id, outcome, state)
        visible_facts = self._visible_facts(intent, state, outcome)
        hidden_facts = list(outcome.hidden_facts)
        reason = check_issue or outcome.reason
        if outcome.hidden_outcome and not self.definition.visibility_policy.hidden_outcome_player_visible:
            visible_facts = []
            hidden_facts = sorted(set([*hidden_facts, "module_hidden_outcome"]))

        action_result = ActionResult(
            success_level=outcome.success_level if not check_issue else SuccessLevel.FAILURE,
            reason=reason,
            state_deltas=deltas,
            visible_facts=visible_facts,
            hidden_facts=hidden_facts,
        )
        event = Event(
            event_id=event_id,
            turn=state.turn,
            actor_id=state.player.id,
            action_type=self.definition.id,
            result=action_result.success_level.value,
            visible_to_player=not outcome.hidden_outcome,
            target_id=intent.target_id,
            input_text=intent.raw_text,
            state_deltas=deltas,
            allow_empty_delta=not deltas,
        )
        return DeclarativeActionExecution(action_result=action_result, event=event)

    def _execution(
        self,
        event_id: str,
        state: GameState,
        intent: PlayerIntent,
        level: SuccessLevel,
        reason: str,
        deltas: list[StateDelta],
    ) -> DeclarativeActionExecution:
        result = ActionResult(success_level=level, reason=reason, state_deltas=deltas)
        event = Event(
            event_id=event_id,
            turn=state.turn,
            actor_id=state.player.id,
            action_type=self.definition.id,
            result=level.value,
            visible_to_player=False,
            target_id=intent.target_id,
            input_text=intent.raw_text,
            state_deltas=deltas,
            allow_empty_delta=not deltas,
        )
        return DeclarativeActionExecution(action_result=result, event=event)

    def _validate_target(self, intent: PlayerIntent, state: GameState) -> str | None:
        if not self.definition.target_specs:
            return None
        target_id = intent.target_id
        for spec in self.definition.target_specs:
            if spec.required and not target_id and spec.kind not in {DeclarativeTargetKind.SELF, DeclarativeTargetKind.CURRENT_LOCATION}:
                return "Declarative action requires a target."
            if spec.allowed_ids and target_id not in spec.allowed_ids:
                return "Target is not allowed for this declarative action."
            if spec.kind == DeclarativeTargetKind.SELF:
                continue
            if spec.kind == DeclarativeTargetKind.CURRENT_LOCATION:
                if target_id and target_id != state.player.location_id:
                    return "Target is not the current location."
                continue
            if spec.kind == DeclarativeTargetKind.LOCATION:
                if target_id not in state.locations:
                    return "Target location does not exist."
                continue
            if spec.kind == DeclarativeTargetKind.OBJECT:
                if target_id not in state.objects or target_id not in get_visible_facts(state, state.player.id, state.player.location_id):
                    return "Target object is not visible."
                continue
            if spec.kind == DeclarativeTargetKind.NPC:
                if target_id not in state.npcs or target_id not in get_visible_facts(state, state.player.id, state.player.location_id):
                    return "Target NPC is not visible."
        return None

    def _check_preconditions(self, intent: PlayerIntent, state: GameState) -> str | None:
        visible_facts = set(get_visible_facts(state, state.player.id, state.player.location_id))
        for fact_id in self.definition.affordance_requirements.required_visible_facts:
            if fact_id not in visible_facts:
                return f"Required visible fact is missing: {fact_id}"
        for key, expected in self.definition.affordance_requirements.required_flags.items():
            if state.flags.get(key) != expected:
                return f"Required flag is not satisfied: {key}"
        for condition in self.definition.preconditions:
            if not _condition_passes(condition, intent, state, visible_facts):
                return f"Precondition failed: {condition.condition_type.value}"
        return None

    def _run_checks(self, intent: PlayerIntent, state: GameState) -> str | None:
        visible_facts = set(get_visible_facts(state, state.player.id, state.player.location_id))
        for check in self.definition.checks:
            condition = DeclarativeCondition(
                condition_type=DeclarativeConditionType(check.check_type.value),
                key=check.key,
                value=check.value,
                expected=check.expected,
            )
            if not _condition_passes(condition, intent, state, visible_facts):
                return f"Check failed: {check.check_type.value}"
        return None

    def _deltas_for_outcome(
        self,
        event_id: str,
        target_id: str | None,
        outcome: DeclarativeOutcome,
        state: GameState,
    ) -> list[StateDelta]:
        deltas = [
            template.to_delta(event_id=event_id, target_id=target_id)
            for template in [*self.definition.state_delta_templates, *outcome.state_delta_templates]
        ]
        if self.definition.time_cost > 0:
            deltas.append(make_time_delta(state, self.definition.time_cost))
        return deltas

    def _visible_facts(self, intent: PlayerIntent, state: GameState, outcome: DeclarativeOutcome) -> list[str]:
        visible = [
            fact_id
            for fact_id in outcome.visible_facts
            if _action_visible_fact_is_player_safe(state, fact_id)
        ]
        if self.definition.visibility_policy.include_target_in_visible_facts and intent.target_id:
            visible.append(intent.target_id)
        if self.definition.visibility_policy.include_current_location_in_visible_facts:
            visible.append(state.player.location_id)
        return sorted(set(visible))


def _condition_passes(
    condition: DeclarativeCondition,
    intent: PlayerIntent,
    state: GameState,
    visible_facts: set[str],
) -> bool:
    if condition.condition_type == DeclarativeConditionType.ALWAYS:
        return True
    if condition.condition_type == DeclarativeConditionType.FLAG_EQUALS:
        return bool(condition.key) and state.flags.get(condition.key) == condition.expected
    if condition.condition_type == DeclarativeConditionType.FACT_VISIBLE:
        fact_id = str(condition.value or condition.key or "")
        return fact_id in visible_facts
    if condition.condition_type == DeclarativeConditionType.TARGET_VISIBLE:
        return bool(intent.target_id) and intent.target_id in visible_facts
    if condition.condition_type == DeclarativeConditionType.AT_LOCATION:
        return state.player.location_id == str(condition.value or condition.key or "")
    return False


def _action_visible_fact_is_player_safe(state: GameState, fact_id: str) -> bool:
    fact = state.facts.get(fact_id)
    if fact is None:
        return True
    return (
        fact_id in state.player_visible_facts
        or fact.public
        or fact.visibility in {FactVisibility.PUBLIC, FactVisibility.DISCOVERABLE}
    )


def _replace_placeholders(value: Any, *, target_id: str | None) -> Any:
    if isinstance(value, str):
        return value.replace("{target_id}", target_id or "")
    if isinstance(value, list):
        return [_replace_placeholders(item, target_id=target_id) for item in value]
    if isinstance(value, dict):
        return {
            str(_replace_placeholders(key, target_id=target_id)): _replace_placeholders(item, target_id=target_id)
            for key, item in value.items()
        }
    return value
