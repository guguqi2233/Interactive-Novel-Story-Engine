from enum import StrEnum
from random import Random

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    CrimeState,
    CrimeStatus,
    FactVisibility,
    GameState,
    HackableState,
    HackingToolState,
    NetworkNodeState,
    WitnessRecord,
)
from app.engine.actions.base import ActionHandler
from app.engine.actions.declarative import (
    DeclarativeActionCategory,
    DeclarativeActionDefinition,
    DeclarativeActionTargetSpec,
    DeclarativeOutcome,
    DeclarativeTargetKind,
    DeclarativeVisibilityPolicy,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.visibility import get_visible_facts
from app.llm.schemas import PlayerActionType, PlayerIntent


class HackingActionType(StrEnum):
    HACK_TERMINAL = "hack_terminal"
    BYPASS_SECURITY_DOOR = "bypass_security_door"
    DISABLE_CAMERA = "disable_camera"
    ACCESS_LOGS = "access_logs"
    PLANT_TRACE = "plant_trace"


class HackingAttemptResult(BaseModel):
    action_type: HackingActionType
    target_id: str | None
    action_result: ActionResult
    event: Event


class HackingActionRule(BaseModel):
    action_type: HackingActionType
    label: str
    aliases: list[str] = Field(default_factory=list)
    required_target_types: list[str] = Field(default_factory=list)
    required_access_level: int = Field(default=0, ge=0)
    trace_on_failure: int = Field(default=1, ge=0)
    alarm_on_failure: int = Field(default=1, ge=0)
    monitored_is_crime: bool = True
    discover_logs: bool = False


class HackingModuleConfig(BaseModel):
    module_id: str = "hacking"
    actions: dict[HackingActionType, HackingActionRule] = Field(default_factory=dict)


def default_hacking_module_config() -> HackingModuleConfig:
    return HackingModuleConfig(
        actions={
            HackingActionType.HACK_TERMINAL: HackingActionRule(
                action_type=HackingActionType.HACK_TERMINAL,
                label="Hack Terminal",
                aliases=["hack terminal", "hack"],
                required_target_types=["terminal"],
            ),
            HackingActionType.BYPASS_SECURITY_DOOR: HackingActionRule(
                action_type=HackingActionType.BYPASS_SECURITY_DOOR,
                label="Bypass Security Door",
                aliases=["bypass security door", "bypass door"],
                required_target_types=["security_door", "door"],
            ),
            HackingActionType.DISABLE_CAMERA: HackingActionRule(
                action_type=HackingActionType.DISABLE_CAMERA,
                label="Disable Camera",
                aliases=["disable camera"],
                required_target_types=["camera"],
            ),
            HackingActionType.ACCESS_LOGS: HackingActionRule(
                action_type=HackingActionType.ACCESS_LOGS,
                label="Access Logs",
                aliases=["access logs", "read logs"],
                required_target_types=["terminal", "network_node"],
                discover_logs=True,
            ),
            HackingActionType.PLANT_TRACE: HackingActionRule(
                action_type=HackingActionType.PLANT_TRACE,
                label="Plant Trace",
                aliases=["plant trace"],
                required_target_types=["terminal", "network_node"],
            ),
        }
    )


class HackingActionHandler(ActionHandler):
    action_type = PlayerActionType.UNKNOWN

    def __init__(self, config: HackingModuleConfig | None = None) -> None:
        self.config = config or default_hacking_module_config()

    def can_handle(self, intent: PlayerIntent, state: GameState) -> bool:
        return self._rule_for_intent(intent) is not None

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        return self.resolve_with_event(intent, state, rng).action_result

    def resolve_with_event(self, intent: PlayerIntent, state: GameState, rng: Random | None = None) -> HackingAttemptResult:
        active_rng = rng or Random(0)
        rule = self._rule_for_intent(intent)
        if rule is None:
            return self._invalid(HackingActionType.HACK_TERMINAL, intent, state, "Unknown hacking action.")
        event_id = f"event-{rule.action_type.value}-{state.turn}"
        target = self._target(intent.target_id, state)
        if target is None:
            return self._result(rule, event_id, intent, state, SuccessLevel.INVALID, "Invalid hacking target.", [], visible_to_player=False)
        target_issue = self._validate_target(rule, target, state)
        if target_issue:
            return self._result(rule, event_id, intent, state, SuccessLevel.INVALID, target_issue, [], visible_to_player=False)

        tool_power = self._tool_power(state)
        roll = active_rng.randint(1, 20)
        total = roll + tool_power
        success = total >= target.difficulty and target.access_level >= rule.required_access_level
        if success:
            deltas = self._success_deltas(rule, target, event_id, state)
            visible_facts = [target.id]
            hidden_facts: list[str] = []
            if rule.discover_logs:
                visible_facts.extend(self._visible_log_facts(target, state))
                hidden_facts.extend(self._hidden_log_facts(target, state))
            return self._result(
                rule,
                event_id,
                intent,
                state,
                SuccessLevel.SUCCESS,
                "Hacking action resolved by deterministic local rules.",
                deltas,
                visible_to_player=not target.hidden,
                visible_facts=visible_facts,
                hidden_facts=hidden_facts,
            )

        deltas = self._failure_deltas(rule, target, event_id, intent, state)
        return self._result(
            rule,
            event_id,
            intent,
            state,
            SuccessLevel.FAILURE,
            "Hacking attempt failed and left a trace.",
            deltas,
            visible_to_player=not target.hidden,
        )

    def _rule_for_intent(self, intent: PlayerIntent) -> HackingActionRule | None:
        normalized = intent.raw_text.strip().lower()
        for rule in self.config.actions.values():
            aliases = {rule.action_type.value.replace("_", " "), rule.action_type.value, rule.label.lower(), *[alias.lower() for alias in rule.aliases]}
            if normalized in aliases or any(normalized.startswith(alias) for alias in aliases):
                return rule
        return None

    def _target(self, target_id: str | None, state: GameState) -> HackableState | None:
        if not target_id:
            return None
        return state.hackables.get(target_id)

    def _validate_target(self, rule: HackingActionRule, target: HackableState, state: GameState) -> str | None:
        if rule.required_target_types and target.target_type not in rule.required_target_types:
            return "Target type does not support this hacking action."
        visible = set(get_visible_facts(state, state.player.id, state.player.location_id))
        if target.hidden and state.player.id not in target.discovered_by:
            return "Hacking target is hidden."
        if target.location_id and target.location_id != state.player.location_id:
            return "Hacking target is not reachable from the current location."
        if target.location_id and target.id not in visible and target.id in state.objects:
            return "Hacking target is not visible."
        return None

    def _tool_power(self, state: GameState) -> int:
        tools = [tool for tool in state.hacking_tools.values() if tool.owner_id == state.player.id]
        return max((tool.power for tool in tools), default=0)

    def _success_deltas(
        self,
        rule: HackingActionRule,
        target: HackableState,
        event_id: str,
        state: GameState,
    ) -> list[StateDelta]:
        deltas: list[StateDelta] = []
        if rule.action_type in {HackingActionType.HACK_TERMINAL, HackingActionType.BYPASS_SECURITY_DOOR}:
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"hackables.{target.id}.security_state",
                    value="compromised",
                    caused_by_event_id=event_id,
                    reason=f"{rule.action_type.value} succeeded.",
                )
            )
        if rule.action_type == HackingActionType.DISABLE_CAMERA:
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"hackables.{target.id}.disabled",
                    value=True,
                    caused_by_event_id=event_id,
                    reason="Camera disabled by hacking action.",
                )
            )
        if rule.action_type == HackingActionType.PLANT_TRACE:
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.INC,
                    path=f"hackables.{target.id}.intrusion_trace",
                    value=1,
                    caused_by_event_id=event_id,
                    reason="Trace planted on hackable target.",
                )
            )
        if rule.discover_logs:
            for fact_id in target.linked_fact_ids:
                fact = state.facts.get(fact_id)
                if fact is None or (not fact.public and fact.visibility == FactVisibility.HIDDEN):
                    continue
                deltas.append(
                    StateDelta(
                        operation=StateDeltaOperation.ADD,
                        path="player_visible_facts",
                        value=fact_id,
                        caused_by_event_id=event_id,
                        reason="Hacking action discovered an accessible log fact.",
                    )
                )
        return deltas

    def _failure_deltas(
        self,
        rule: HackingActionRule,
        target: HackableState,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
    ) -> list[StateDelta]:
        deltas = [
            StateDelta(
                operation=StateDeltaOperation.INC,
                path=f"hackables.{target.id}.intrusion_trace",
                value=rule.trace_on_failure,
                caused_by_event_id=event_id,
                reason="Failed hacking attempt increased intrusion trace.",
            ),
            StateDelta(
                operation=StateDeltaOperation.INC,
                path=f"hackables.{target.id}.alarm_level",
                value=rule.alarm_on_failure,
                caused_by_event_id=event_id,
                reason="Failed hacking attempt increased alarm level.",
            ),
        ]
        if target.monitored and rule.monitored_is_crime:
            deltas.extend(self._crime_deltas(rule, target, event_id, intent, state))
        return deltas

    def _crime_deltas(
        self,
        rule: HackingActionRule,
        target: HackableState,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
    ) -> list[StateDelta]:
        witness_ids = sorted(
            npc.id
            for npc in state.npcs.values()
            if npc.location_id == state.player.location_id and npc.visible and not npc.hidden
        )
        crime_id = f"cyber_crime_{target.id}_{state.turn}"
        crime = CrimeState(
            id=crime_id,
            crime_type="cyber_crime",
            actor_id=state.player.id,
            target_id=intent.target_id,
            location_id=state.player.location_id,
            turn=state.turn,
            created_turn=state.turn,
            witness_ids=witness_ids,
            witnessed_by=witness_ids,
            severity=2,
            known_to_player=True,
            status=CrimeStatus.WITNESSED if witness_ids else CrimeStatus.HIDDEN,
            tags=["hacking", rule.action_type.value],
        )
        deltas: list[StateDelta] = [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"crimes.{crime_id}",
                value=crime.model_dump(mode="json"),
                caused_by_event_id=event_id,
                reason="Monitored hacking attempt created a cyber crime record.",
            )
        ]
        for witness_id in witness_ids:
            witness = WitnessRecord(
                id=f"{crime_id}:{witness_id}",
                npc_id=witness_id,
                crime_id=crime_id,
                certainty=75,
                confidence=75,
                saw_actor=True,
                saw_target=True,
                known_to_player=True,
            )
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"witnesses.{witness.id}",
                    value=witness.model_dump(mode="json"),
                    caused_by_event_id=event_id,
                    reason="Monitored hacking attempt created a witness record.",
                )
            )
        return deltas

    def _visible_log_facts(self, target: HackableState, state: GameState) -> list[str]:
        visible: list[str] = []
        for fact_id in target.linked_fact_ids:
            fact = state.facts.get(fact_id)
            if fact and (fact.public or fact_id in state.player_visible_facts):
                visible.append(fact_id)
        return visible

    def _hidden_log_facts(self, target: HackableState, state: GameState) -> list[str]:
        hidden: list[str] = []
        for fact_id in target.linked_fact_ids:
            fact = state.facts.get(fact_id)
            if fact and not fact.public and fact_id not in state.player_visible_facts:
                hidden.append(fact_id)
        return hidden

    def _result(
        self,
        rule: HackingActionRule,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
        level: SuccessLevel,
        reason: str,
        deltas: list[StateDelta],
        *,
        visible_to_player: bool,
        visible_facts: list[str] | None = None,
        hidden_facts: list[str] | None = None,
    ) -> HackingAttemptResult:
        action_result = ActionResult(
            success_level=level,
            reason=reason,
            state_deltas=deltas,
            visible_facts=sorted(set(visible_facts or [])),
            hidden_facts=sorted(set(hidden_facts or [])),
        )
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
        return HackingAttemptResult(action_type=rule.action_type, target_id=intent.target_id, action_result=action_result, event=event)

    def _invalid(self, action_type: HackingActionType, intent: PlayerIntent, state: GameState, reason: str) -> HackingAttemptResult:
        rule = HackingActionRule(action_type=action_type, label=action_type.value)
        return self._result(
            rule,
            f"event-{action_type.value}-{state.turn}",
            intent,
            state,
            SuccessLevel.INVALID,
            reason,
            [],
            visible_to_player=False,
        )


def hacking_action_definitions(config: HackingModuleConfig | None = None) -> list[DeclarativeActionDefinition]:
    active_config = config or default_hacking_module_config()
    return [
        DeclarativeActionDefinition(
            id=f"hacking.{rule.action_type.value}",
            label=rule.label,
            aliases=rule.aliases,
            category=DeclarativeActionCategory.HACKING,
            target_specs=[DeclarativeActionTargetSpec(kind=DeclarativeTargetKind.OBJECT)],
            outcomes={
                SuccessLevel.SUCCESS: DeclarativeOutcome(
                    success_level=SuccessLevel.SUCCESS,
                    reason=f"{rule.label} is resolved by deterministic hacking rules.",
                )
            },
            event_type=f"hacking.{rule.action_type.value}.resolved",
            visibility_policy=DeclarativeVisibilityPolicy(hidden_outcome_player_visible=False),
        )
        for rule in active_config.actions.values()
    ]


__all__ = [
    "HackableState",
    "HackingToolState",
    "HackingAttemptResult",
    "NetworkNodeState",
    "HackingActionHandler",
    "HackingModuleConfig",
    "default_hacking_module_config",
    "hacking_action_definitions",
]
