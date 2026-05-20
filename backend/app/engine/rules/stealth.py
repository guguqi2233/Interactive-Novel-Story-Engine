from enum import StrEnum
from random import Random

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    CoverState,
    DetectionCheckResult,
    GameState,
    LocationState,
    NoiseEvent,
    NPCState,
    StealthState,
)
from app.engine.actions.base import ActionHandler
from app.engine.actions.declarative import (
    DeclarativeActionCategory,
    DeclarativeActionDefinition,
    DeclarativeOutcome,
    DeclarativeVisibilityPolicy,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.life_state import can_act, can_move
from app.engine.rules.time import make_time_delta
from app.llm.schemas import PlayerActionType, PlayerIntent


class StealthActionType(StrEnum):
    HIDE = "hide"
    SNEAK_FOLLOW = "sneak_follow"
    DISTRACT = "distract"
    CREATE_NOISE = "create_noise"
    SET_DECOY = "set_decoy"
    SHADOW_NPC = "shadow_npc"


class StealthActionRule(BaseModel):
    action_type: StealthActionType
    label: str
    aliases: list[str] = Field(default_factory=list)
    time_cost: int = Field(default=5, ge=0)
    base_volume: int = Field(default=0, ge=0, le=100)


class StealthAttemptResult(BaseModel):
    action_type: StealthActionType
    target_id: str | None
    action_result: ActionResult
    event: Event
    detection: DetectionCheckResult | None = None


class StealthModuleConfig(BaseModel):
    module_id: str = "stealth"
    actions: dict[StealthActionType, StealthActionRule] = Field(default_factory=dict)
    hidden_status: str = "hidden"
    distracted_status: str = "distracted"


def default_stealth_module_config() -> StealthModuleConfig:
    return StealthModuleConfig(
        actions={
            StealthActionType.HIDE: StealthActionRule(action_type=StealthActionType.HIDE, label="Hide", aliases=["hide", "take cover"], time_cost=5),
            StealthActionType.SNEAK_FOLLOW: StealthActionRule(action_type=StealthActionType.SNEAK_FOLLOW, label="Sneak Follow", aliases=["sneak follow", "follow quietly"], time_cost=10),
            StealthActionType.DISTRACT: StealthActionRule(action_type=StealthActionType.DISTRACT, label="Distract", aliases=["distract"], time_cost=5, base_volume=20),
            StealthActionType.CREATE_NOISE: StealthActionRule(action_type=StealthActionType.CREATE_NOISE, label="Create Noise", aliases=["create noise", "make noise"], time_cost=5, base_volume=45),
            StealthActionType.SET_DECOY: StealthActionRule(action_type=StealthActionType.SET_DECOY, label="Set Decoy", aliases=["set decoy", "place decoy"], time_cost=10, base_volume=25),
            StealthActionType.SHADOW_NPC: StealthActionRule(action_type=StealthActionType.SHADOW_NPC, label="Shadow NPC", aliases=["shadow npc", "tail npc", "shadow"], time_cost=10),
        }
    )


class StealthActionHandler(ActionHandler):
    action_type = PlayerActionType.UNKNOWN

    def __init__(self, config: StealthModuleConfig | None = None) -> None:
        self.config = config or default_stealth_module_config()

    def can_handle(self, intent: PlayerIntent, state: GameState) -> bool:
        return self._rule_for_intent(intent) is not None

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        return self.resolve_with_event(intent, state, rng).action_result

    def resolve_with_event(self, intent: PlayerIntent, state: GameState, rng: Random | None = None) -> StealthAttemptResult:
        active_rng = rng or Random(0)
        rule = self._rule_for_intent(intent)
        if rule is None:
            return self._invalid(intent, state, "Unknown stealth action.")
        event_id = f"event-{rule.action_type.value}-{intent.target_id or state.player.location_id}-{state.turn}"
        if rule.action_type == StealthActionType.HIDE:
            return self._hide(rule, event_id, intent, state, active_rng)
        if rule.action_type == StealthActionType.CREATE_NOISE:
            return self._create_noise(rule, event_id, intent, state)
        if rule.action_type == StealthActionType.DISTRACT:
            return self._distract(rule, event_id, intent, state)
        if rule.action_type == StealthActionType.SET_DECOY:
            return self._set_decoy(rule, event_id, intent, state)
        if rule.action_type in {StealthActionType.SHADOW_NPC, StealthActionType.SNEAK_FOLLOW}:
            return self._shadow(rule, event_id, intent, state, active_rng)
        return self._invalid(intent, state, "Unsupported stealth action.")

    def _rule_for_intent(self, intent: PlayerIntent) -> StealthActionRule | None:
        normalized = _normalized(intent.raw_text)
        for rule in self.config.actions.values():
            aliases = {rule.action_type.value, rule.action_type.value.replace("_", " "), rule.label.lower(), *[_normalized(alias) for alias in rule.aliases]}
            if normalized in aliases or any(normalized.startswith(alias) for alias in aliases):
                return rule
        return None

    def _hide(self, rule: StealthActionRule, event_id: str, intent: PlayerIntent, state: GameState, rng: Random) -> StealthAttemptResult:
        if not can_move(state, state.player.id):
            return self._result(rule, event_id, intent, state, SuccessLevel.FAILURE, "Actor cannot hide right now.", [], visible_to_player=True)
        detection = run_detection_check(state, state.player.id, state.player.location_id, rng)
        current = _stealth_for_actor(state, state.player.id)
        next_stealth = current.model_copy(
            update={
                "hidden": not detection.detected,
                "stealth_score": min(100, detection.score),
                "last_detection_result": "detected" if detection.detected else "hidden",
            }
        )
        deltas = [
            make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id}),
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"stealth.{state.player.id}",
                value=next_stealth.model_dump(mode="json"),
                caused_by_event_id=event_id,
                reason="Hide action updated stealth state.",
            ),
        ]
        if not detection.detected:
            level = SuccessLevel.SUCCESS
            reason = "Player hid using local cover and light rules."
            visible_facts = ["stealth:hidden"]
        else:
            level = SuccessLevel.FAILURE
            reason = detection.safe_summary or "Player failed to hide."
            visible_facts = ["stealth:detected"]
            deltas.extend(_observer_suspicion_deltas(state, detection, 1, event_id, "Failed hide attempt raised observer suspicion."))
        return self._result(rule, event_id, intent, state, level, reason, deltas, visible_to_player=True, visible_facts=visible_facts, detection=detection)

    def _create_noise(self, rule: StealthActionRule, event_id: str, intent: PlayerIntent, state: GameState) -> StealthAttemptResult:
        location_id = state.player.location_id
        attracted = _visible_npcs_at_location(state, location_id)
        noise_id = f"noise_{location_id}_{state.turn}"
        noise = NoiseEvent(id=noise_id, location_id=location_id, source_actor_id=state.player.id, volume=rule.base_volume, turn=state.turn, attracts_npc_ids=attracted, hidden_source=False)
        current = _stealth_for_actor(state, state.player.id)
        next_stealth = current.model_copy(update={"last_noise_event_id": noise_id, "last_detection_result": "noise_created"})
        deltas = [
            make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id}),
            StateDelta(operation=StateDeltaOperation.SET, path=f"noise_events.{noise_id}", value=noise.model_dump(mode="json"), caused_by_event_id=event_id, reason="Noise event recorded."),
            StateDelta(operation=StateDeltaOperation.SET, path=f"stealth.{state.player.id}", value=next_stealth.model_dump(mode="json"), caused_by_event_id=event_id, reason="Stealth state recorded noise source."),
            *_alertness_deltas(attracted, 1, event_id, "Noise increased NPC alertness."),
        ]
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS, "Noise drew local attention by rule.", deltas, visible_to_player=True, visible_facts=["noise:created"])

    def _distract(self, rule: StealthActionRule, event_id: str, intent: PlayerIntent, state: GameState) -> StealthAttemptResult:
        target = _visible_target_npc(state, intent.target_id)
        if target is None:
            return self._result(rule, event_id, intent, state, SuccessLevel.INVALID, "Distract target is unavailable.", [], visible_to_player=False)
        current = _stealth_for_actor(state, state.player.id)
        distracted = sorted({*current.distracted_npc_ids, target.id})
        next_stealth = current.model_copy(update={"distracted_npc_ids": distracted, "last_detection_result": "distracted"})
        deltas = [
            make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id}),
            StateDelta(operation=StateDeltaOperation.SET, path=f"stealth.{state.player.id}", value=next_stealth.model_dump(mode="json"), caused_by_event_id=event_id, reason="Distract updated stealth state."),
            StateDelta(operation=StateDeltaOperation.ADD, path=f"npcs.{target.id}.status_effects", value=self.config.distracted_status, caused_by_event_id=event_id, reason="NPC was distracted."),
        ]
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS, "Target was distracted by rule.", deltas, visible_to_player=True, visible_facts=[target.id, "stealth:distracted"])

    def _set_decoy(self, rule: StealthActionRule, event_id: str, intent: PlayerIntent, state: GameState) -> StealthAttemptResult:
        decoy_id = intent.target_id or f"decoy_{state.turn}"
        location_id = state.player.location_id
        attracted = _visible_npcs_at_location(state, location_id)
        noise_id = f"decoy_noise_{location_id}_{state.turn}"
        noise = NoiseEvent(id=noise_id, location_id=location_id, source_actor_id=state.player.id, volume=rule.base_volume, turn=state.turn, attracts_npc_ids=attracted, hidden_source=True)
        current = _stealth_for_actor(state, state.player.id)
        next_stealth = current.model_copy(update={"decoy_item_id": decoy_id, "last_noise_event_id": noise_id, "last_detection_result": "decoy_set"})
        deltas = [
            make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id}),
            StateDelta(operation=StateDeltaOperation.SET, path=f"noise_events.{noise_id}", value=noise.model_dump(mode="json"), caused_by_event_id=event_id, reason="Decoy noise event recorded."),
            StateDelta(operation=StateDeltaOperation.SET, path=f"stealth.{state.player.id}", value=next_stealth.model_dump(mode="json"), caused_by_event_id=event_id, reason="Decoy updated stealth state."),
            *_alertness_deltas(attracted, 1, event_id, "Decoy increased NPC alertness."),
        ]
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS, "Decoy created a controlled distraction.", deltas, visible_to_player=True, visible_facts=["stealth:decoy"])

    def _shadow(self, rule: StealthActionRule, event_id: str, intent: PlayerIntent, state: GameState, rng: Random) -> StealthAttemptResult:
        target = _visible_target_npc(state, intent.target_id)
        if target is None:
            return self._result(rule, event_id, intent, state, SuccessLevel.INVALID, "Shadow target is unavailable.", [], visible_to_player=False)
        detection = run_detection_check(state, state.player.id, target.location_id, rng, target_id=target.id)
        current = _stealth_for_actor(state, state.player.id)
        next_stealth = current.model_copy(
            update={
                "hidden": not detection.detected,
                "stealth_score": min(100, detection.score),
                "shadowing_target_id": None if detection.detected else target.id,
                "last_detection_result": "shadow_detected" if detection.detected else "shadowing",
            }
        )
        deltas = [
            make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id}),
            StateDelta(operation=StateDeltaOperation.SET, path=f"stealth.{state.player.id}", value=next_stealth.model_dump(mode="json"), caused_by_event_id=event_id, reason="Shadow action updated stealth state."),
        ]
        if detection.detected:
            deltas.append(StateDelta(operation=StateDeltaOperation.INC, path=f"npcs.{target.id}.suspicion", value=2, caused_by_event_id=event_id, reason="Failed shadowing increased target suspicion.", metadata={"source": "stealth", "npc_id": target.id}))
            deltas.extend(_observer_suspicion_deltas(state, detection, 1, event_id, "Failed shadowing raised observer suspicion."))
            return self._result(rule, event_id, intent, state, SuccessLevel.FAILURE, "Shadowing failed and raised suspicion.", deltas, visible_to_player=True, visible_facts=["stealth:shadow_failed"], detection=detection)
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS, "Shadowing remained unnoticed.", deltas, visible_to_player=True, visible_facts=[target.id, "stealth:shadowing"], detection=detection)

    def _result(
        self,
        rule: StealthActionRule,
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
        detection: DetectionCheckResult | None = None,
    ) -> StealthAttemptResult:
        result = ActionResult(
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
        return StealthAttemptResult(action_type=rule.action_type, target_id=intent.target_id, action_result=result, event=event, detection=detection)

    def _invalid(self, intent: PlayerIntent, state: GameState, reason: str) -> StealthAttemptResult:
        rule = StealthActionRule(action_type=StealthActionType.HIDE, label="Stealth")
        return self._result(rule, f"event-stealth-invalid-{state.turn}", intent, state, SuccessLevel.INVALID, reason, [], visible_to_player=False)


def run_detection_check(
    state: GameState,
    actor_id: str,
    location_id: str,
    rng: Random,
    *,
    target_id: str | None = None,
) -> DetectionCheckResult:
    observers = _possible_observers(state, location_id, target_id=target_id)
    cover, light = _cover_and_light(state, location_id)
    roll = rng.randint(1, 10)
    score = max(0, roll + state.player.stealth_modifier + cover * 2 - max(light - 5, 0) * 2)
    if not observers:
        return DetectionCheckResult(detected=False, score=score, difficulty=6, safe_summary="No observer had a line of detection.")
    best = max(observers, key=lambda npc: npc.alertness + npc.suspicion)
    shadowing_pressure = 10 if target_id and best.id == target_id else 0
    difficulty = 6 + best.alertness + best.suspicion + shadowing_pressure + max(light - 5, 0) - cover
    detected = score < difficulty
    hidden_observer = best.hidden and actor_id not in best.discovered_by
    if not detected:
        summary = "Stealth check passed against local observers."
    elif hidden_observer:
        summary = "A hidden observer noticed signs of stealth activity."
    else:
        summary = f"{best.id} noticed signs of stealth activity."
    return DetectionCheckResult(observer_id=None if hidden_observer else best.id, detected=detected, score=score, difficulty=difficulty, hidden_observer=hidden_observer, safe_summary=summary)


def stealth_action_definitions(config: StealthModuleConfig | None = None) -> list[DeclarativeActionDefinition]:
    active = config or default_stealth_module_config()
    return [
        DeclarativeActionDefinition(
            id=f"stealth.{rule.action_type.value}",
            label=rule.label,
            aliases=rule.aliases,
            category=DeclarativeActionCategory.STEALTH,
            outcomes={SuccessLevel.SUCCESS: DeclarativeOutcome(success_level=SuccessLevel.SUCCESS, reason=f"{rule.label} is resolved by deterministic stealth rules.")},
            event_type=f"stealth.{rule.action_type.value}.resolved",
            visibility_policy=DeclarativeVisibilityPolicy(hidden_outcome_player_visible=False),
        )
        for rule in active.actions.values()
    ]


def _stealth_for_actor(state: GameState, actor_id: str) -> StealthState:
    return state.stealth.get(actor_id) or StealthState(actor_id=actor_id)


def _cover_and_light(state: GameState, location_id: str) -> tuple[int, int]:
    cover_state = state.cover_states.get(location_id)
    if cover_state is not None:
        return cover_state.cover_level, cover_state.light_level
    location = state.locations.get(location_id)
    if location is None:
        return 0, 5
    return _cover_bonus(location), _light_level(location)


def _cover_bonus(location: LocationState | CoverState | None) -> int:
    return location.cover_level if location is not None else 0


def _light_level(location: LocationState | CoverState | None) -> int:
    return location.light_level if location is not None else 5


def _possible_observers(state: GameState, location_id: str, *, target_id: str | None = None) -> list[NPCState]:
    location_ids = {location_id, state.player.location_id}
    if target_id and target_id in state.npcs:
        location_ids.add(state.npcs[target_id].location_id)
    return [
        npc
        for npc in state.npcs.values()
        if npc.location_id in location_ids and can_act(state, npc.id)
    ]


def _visible_npcs_at_location(state: GameState, location_id: str) -> list[str]:
    return sorted(
        npc.id
        for npc in state.npcs.values()
        if npc.location_id == location_id
        and can_act(state, npc.id)
        and (not npc.hidden or state.player.id in npc.discovered_by)
    )


def _visible_target_npc(state: GameState, npc_id: str | None) -> NPCState | None:
    if npc_id is None:
        return None
    npc = state.npcs.get(npc_id)
    if npc is None or npc.location_id != state.player.location_id:
        return None
    if npc.hidden and state.player.id not in npc.discovered_by:
        return None
    if not can_act(state, npc.id):
        return None
    return npc


def _observer_suspicion_deltas(
    state: GameState,
    detection: DetectionCheckResult,
    amount: int,
    event_id: str,
    reason: str,
) -> list[StateDelta]:
    if detection.observer_id is None or detection.observer_id not in state.npcs:
        return []
    return [
        StateDelta(
            operation=StateDeltaOperation.INC,
            path=f"npcs.{detection.observer_id}.suspicion",
            value=amount,
            caused_by_event_id=event_id,
            reason=reason,
            metadata={"source": "stealth", "npc_id": detection.observer_id},
        )
    ]


def _alertness_deltas(npc_ids: list[str], amount: int, event_id: str, reason: str) -> list[StateDelta]:
    return [
        StateDelta(
            operation=StateDeltaOperation.INC,
            path=f"npcs.{npc_id}.alertness",
            value=amount,
            caused_by_event_id=event_id,
            reason=reason,
            metadata={"source": "stealth", "npc_id": npc_id},
        )
        for npc_id in npc_ids
    ]


def _normalized(value: str) -> str:
    return value.strip().lower().replace("_", " ")
