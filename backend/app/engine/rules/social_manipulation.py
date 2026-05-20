from enum import StrEnum
from random import Random

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactVisibility, GameState, LeverageState, NPCState, SocialMoveResult
from app.engine.actions.base import ActionHandler
from app.engine.actions.declarative import (
    DeclarativeActionCategory,
    DeclarativeActionDefinition,
    DeclarativeOutcome,
    DeclarativeVisibilityPolicy,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.knowledge import npc_knows
from app.engine.rules.life_state import can_talk
from app.engine.rules.relationships import get_relationship
from app.engine.rules.time import make_time_delta
from app.llm.schemas import PlayerActionType, PlayerIntent


class SocialManipulationMove(StrEnum):
    PERSUADE = "persuade"
    THREATEN = "threaten"
    BRIBE = "bribe"
    DECEIVE = "deceive"
    PROVOKE = "provoke"
    COMFORT = "comfort"
    BLACKMAIL = "blackmail"
    EXTRACT_INFORMATION = "extract_information"


class SocialManipulationRule(BaseModel):
    move_type: SocialManipulationMove
    label: str
    aliases: list[str] = Field(default_factory=list)
    time_cost: int = Field(default=10, ge=0)
    difficulty: int = Field(default=10, ge=0)
    currency_cost: int = Field(default=0, ge=0)


class SocialManipulationAttemptResult(BaseModel):
    move_type: SocialManipulationMove
    target_id: str | None
    move_result: SocialMoveResult
    action_result: ActionResult
    event: Event


class SocialManipulationModuleConfig(BaseModel):
    module_id: str = "social_manipulation"
    actions: dict[SocialManipulationMove, SocialManipulationRule] = Field(default_factory=dict)


def default_social_manipulation_config() -> SocialManipulationModuleConfig:
    return SocialManipulationModuleConfig(
        actions={
            SocialManipulationMove.PERSUADE: SocialManipulationRule(move_type=SocialManipulationMove.PERSUADE, label="Persuade", aliases=["persuade"], difficulty=8),
            SocialManipulationMove.THREATEN: SocialManipulationRule(move_type=SocialManipulationMove.THREATEN, label="Threaten", aliases=["threaten"], difficulty=10),
            SocialManipulationMove.BRIBE: SocialManipulationRule(move_type=SocialManipulationMove.BRIBE, label="Bribe", aliases=["bribe"], difficulty=7, currency_cost=5),
            SocialManipulationMove.DECEIVE: SocialManipulationRule(move_type=SocialManipulationMove.DECEIVE, label="Deceive", aliases=["deceive", "lie"], difficulty=12),
            SocialManipulationMove.PROVOKE: SocialManipulationRule(move_type=SocialManipulationMove.PROVOKE, label="Provoke", aliases=["provoke"], difficulty=8),
            SocialManipulationMove.COMFORT: SocialManipulationRule(move_type=SocialManipulationMove.COMFORT, label="Comfort", aliases=["comfort", "soothe"], difficulty=6),
            SocialManipulationMove.BLACKMAIL: SocialManipulationRule(move_type=SocialManipulationMove.BLACKMAIL, label="Blackmail", aliases=["blackmail"], difficulty=7),
            SocialManipulationMove.EXTRACT_INFORMATION: SocialManipulationRule(move_type=SocialManipulationMove.EXTRACT_INFORMATION, label="Extract Information", aliases=["extract information", "question"], difficulty=7),
        }
    )


class SocialManipulationActionHandler(ActionHandler):
    action_type = PlayerActionType.UNKNOWN

    def __init__(self, config: SocialManipulationModuleConfig | None = None) -> None:
        self.config = config or default_social_manipulation_config()

    def can_handle(self, intent: PlayerIntent, state: GameState) -> bool:
        return self._rule_for_intent(intent) is not None

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        return self.resolve_with_event(intent, state, rng).action_result

    def resolve_with_event(self, intent: PlayerIntent, state: GameState, rng: Random | None = None) -> SocialManipulationAttemptResult:
        active_rng = rng or Random(0)
        rule = self._rule_for_intent(intent)
        if rule is None:
            return self._invalid(intent, state, "Unknown social manipulation action.")
        target = _visible_target_npc(state, intent.target_id)
        if target is None:
            return self._result(rule, f"event-social-invalid-{state.turn}", intent, state, SuccessLevel.INVALID, "Social target is unavailable.", [], visible_to_player=False)
        if rule.move_type == SocialManipulationMove.BRIBE:
            return self._bribe(rule, intent, state, target, active_rng)
        if rule.move_type == SocialManipulationMove.BLACKMAIL:
            return self._blackmail(rule, intent, state, target, active_rng)
        if rule.move_type == SocialManipulationMove.EXTRACT_INFORMATION:
            return self._extract_information(rule, intent, state, target, active_rng)
        return self._social_check(rule, intent, state, target, active_rng)

    def _rule_for_intent(self, intent: PlayerIntent) -> SocialManipulationRule | None:
        normalized = _normalized(intent.raw_text)
        for rule in self.config.actions.values():
            aliases = {rule.move_type.value, rule.move_type.value.replace("_", " "), rule.label.lower(), *[_normalized(alias) for alias in rule.aliases]}
            if normalized in aliases or any(normalized.startswith(alias) for alias in aliases):
                return rule
        return None

    def _social_check(
        self,
        rule: SocialManipulationRule,
        intent: PlayerIntent,
        state: GameState,
        target: NPCState,
        rng: Random,
    ) -> SocialManipulationAttemptResult:
        event_id = _event_id(rule, state, target.id)
        score = _social_score(state, target, rng)
        success = score >= rule.difficulty
        deltas = [make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id})]
        visible_facts: list[str] = [target.id, f"social:{rule.move_type.value}"]
        level = SuccessLevel.SUCCESS if success else SuccessLevel.FAILURE
        relationship_delta = 0
        suspicion_delta = 0
        if success and rule.move_type in {SocialManipulationMove.PERSUADE, SocialManipulationMove.COMFORT}:
            relationship_delta = 1
            deltas.extend(_relationship_delta(state, target.id, relationship_delta, event_id, "Social move improved trust."))
            if rule.move_type == SocialManipulationMove.COMFORT:
                deltas.append(StateDelta(operation=StateDeltaOperation.SET, path=f"npcs.{target.id}.emotional_state.stress", value=max(0, target.emotional_state.stress - 10), caused_by_event_id=event_id, reason="Comfort reduced NPC stress.", metadata={"source": "social_manipulation"}))
        elif success and rule.move_type in {SocialManipulationMove.THREATEN, SocialManipulationMove.PROVOKE}:
            relationship_delta = -1
            deltas.extend(_relationship_delta(state, target.id, relationship_delta, event_id, "Social move damaged trust."))
            deltas.append(StateDelta(operation=StateDeltaOperation.INC, path=f"npcs.{target.id}.emotional_state.stress", value=10, caused_by_event_id=event_id, reason="Threatening social move increased stress.", metadata={"source": "social_manipulation"}))
        elif not success:
            suspicion_delta = 1
            deltas.append(_suspicion_delta(target.id, 1, event_id, "Failed social move increased suspicion."))
        move_result = SocialMoveResult(move_type=rule.move_type.value, target_id=target.id, success=success, relationship_delta=relationship_delta, suspicion_delta=suspicion_delta, safe_summary=f"{rule.label} resolved by social rules.")
        return self._result(rule, event_id, intent, state, level, move_result.safe_summary, deltas, visible_to_player=True, visible_facts=visible_facts, move_result=move_result)

    def _bribe(
        self,
        rule: SocialManipulationRule,
        intent: PlayerIntent,
        state: GameState,
        target: NPCState,
        rng: Random,
    ) -> SocialManipulationAttemptResult:
        event_id = _event_id(rule, state, target.id)
        if state.player.currency < rule.currency_cost:
            return self._result(rule, event_id, intent, state, SuccessLevel.FAILURE, "Bribe failed: insufficient currency.", [], visible_to_player=True)
        score = _social_score(state, target, rng) + 3
        success = score >= rule.difficulty
        deltas = [
            make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id}),
            StateDelta(operation=StateDeltaOperation.INC, path="player.currency", value=-rule.currency_cost, caused_by_event_id=event_id, reason="Bribe spent player currency.", metadata={"source": "social_manipulation"}),
        ]
        if success:
            deltas.extend(_relationship_delta(state, target.id, 1, event_id, "Bribe increased obligation/trust."))
        else:
            deltas.append(_suspicion_delta(target.id, 1, event_id, "Failed bribe increased suspicion."))
        move_result = SocialMoveResult(move_type=rule.move_type.value, target_id=target.id, success=success, relationship_delta=1 if success else 0, suspicion_delta=0 if success else 1, safe_summary="Bribe resolved by currency and relationship rules.")
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS if success else SuccessLevel.FAILURE, move_result.safe_summary, deltas, visible_to_player=True, visible_facts=[target.id, "social:bribe"], move_result=move_result)

    def _blackmail(
        self,
        rule: SocialManipulationRule,
        intent: PlayerIntent,
        state: GameState,
        target: NPCState,
        rng: Random,
    ) -> SocialManipulationAttemptResult:
        event_id = _event_id(rule, state, target.id)
        leverage = _known_leverage_for_target(state, target.id)
        if leverage is None:
            return self._result(rule, event_id, intent, state, SuccessLevel.FAILURE, "Blackmail requires known leverage.", [], visible_to_player=True)
        score = _social_score(state, target, rng) + leverage.strength // 10
        success = score >= rule.difficulty
        deltas = [make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id})]
        if success:
            deltas.append(StateDelta(operation=StateDeltaOperation.SET, path=f"leverages.{leverage.id}.used", value=True, caused_by_event_id=event_id, reason="Blackmail used known leverage.", metadata={"source": "social_manipulation"}))
            deltas.extend(_relationship_delta(state, target.id, -2, event_id, "Blackmail damaged trust."))
            deltas.append(StateDelta(operation=StateDeltaOperation.INC, path=f"relationships.{_relationship_id_for_player(state, target.id)}.fear", value=2, caused_by_event_id=event_id, reason="Blackmail increased fear.", metadata={"source": "social_manipulation"}))
        else:
            deltas.append(_suspicion_delta(target.id, 2, event_id, "Failed blackmail increased suspicion."))
        move_result = SocialMoveResult(move_type=rule.move_type.value, target_id=target.id, success=success, relationship_delta=-2 if success else 0, suspicion_delta=0 if success else 2, safe_summary="Blackmail resolved using known leverage.")
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS if success else SuccessLevel.FAILURE, move_result.safe_summary, deltas, visible_to_player=True, visible_facts=[target.id, "social:blackmail"], move_result=move_result)

    def _extract_information(
        self,
        rule: SocialManipulationRule,
        intent: PlayerIntent,
        state: GameState,
        target: NPCState,
        rng: Random,
    ) -> SocialManipulationAttemptResult:
        event_id = _event_id(rule, state, target.id)
        score = _social_score(state, target, rng)
        revealable_fact = _first_revealable_known_fact(state, target.id)
        success = score >= rule.difficulty and revealable_fact is not None
        deltas = [make_time_delta(state, rule.time_cost).model_copy(update={"caused_by_event_id": event_id})]
        revealed: list[str] = []
        if success and revealable_fact is not None:
            deltas.append(StateDelta(operation=StateDeltaOperation.ADD, path="player_visible_facts", value=revealable_fact, caused_by_event_id=event_id, reason="NPC revealed a fact they knew.", metadata={"source": "social_manipulation"}))
            revealed.append(revealable_fact)
        elif not success:
            deltas.append(_suspicion_delta(target.id, 1, event_id, "Failed information extraction increased suspicion."))
        move_result = SocialMoveResult(move_type=rule.move_type.value, target_id=target.id, success=success, revealed_fact_ids=revealed, suspicion_delta=0 if success else 1, safe_summary="Information extraction used NPC knowledge boundaries.")
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS if success else SuccessLevel.FAILURE, move_result.safe_summary, deltas, visible_to_player=True, visible_facts=[target.id, *revealed], move_result=move_result)

    def _result(
        self,
        rule: SocialManipulationRule,
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
        move_result: SocialMoveResult | None = None,
    ) -> SocialManipulationAttemptResult:
        result = ActionResult(success_level=level, reason=reason, state_deltas=deltas, visible_facts=sorted(set(visible_facts or [])), hidden_facts=sorted(set(hidden_facts or [])))
        event = Event(
            event_id=event_id,
            turn=state.turn,
            actor_id=state.player.id,
            action_type=rule.move_type.value,
            result=level.value,
            visible_to_player=visible_to_player,
            target_id=intent.target_id,
            input_text=intent.raw_text,
            state_deltas=deltas,
            allow_empty_delta=not deltas,
        )
        return SocialManipulationAttemptResult(
            move_type=rule.move_type,
            target_id=intent.target_id,
            move_result=move_result or SocialMoveResult(move_type=rule.move_type.value, target_id=intent.target_id, success=level == SuccessLevel.SUCCESS, safe_summary=reason),
            action_result=result,
            event=event,
        )

    def _invalid(self, intent: PlayerIntent, state: GameState, reason: str) -> SocialManipulationAttemptResult:
        rule = SocialManipulationRule(move_type=SocialManipulationMove.PERSUADE, label="Social Manipulation")
        return self._result(rule, f"event-social-invalid-{state.turn}", intent, state, SuccessLevel.INVALID, reason, [], visible_to_player=False)


def social_manipulation_action_definitions(config: SocialManipulationModuleConfig | None = None) -> list[DeclarativeActionDefinition]:
    active = config or default_social_manipulation_config()
    return [
        DeclarativeActionDefinition(
            id=f"social_manipulation.{rule.move_type.value}",
            label=rule.label,
            aliases=rule.aliases,
            category=DeclarativeActionCategory.SOCIAL,
            outcomes={SuccessLevel.SUCCESS: DeclarativeOutcome(success_level=SuccessLevel.SUCCESS, reason=f"{rule.label} is resolved by deterministic social rules.")},
            event_type=f"social_manipulation.{rule.move_type.value}.resolved",
            visibility_policy=DeclarativeVisibilityPolicy(hidden_outcome_player_visible=False),
        )
        for rule in active.actions.values()
    ]


def _visible_target_npc(state: GameState, npc_id: str | None) -> NPCState | None:
    if npc_id is None:
        return None
    npc = state.npcs.get(npc_id)
    if npc is None or npc.location_id != state.player.location_id or not can_talk(state, npc.id):
        return None
    if npc.hidden and state.player.id not in npc.discovered_by:
        return None
    return npc


def _social_score(state: GameState, target: NPCState, rng: Random) -> int:
    relationship = get_relationship(state, target.id, state.player.id) or get_relationship(state, state.player.id, target.id)
    relationship_score = 0
    if relationship is not None:
        relationship_score = relationship.trust + relationship.affinity + relationship.obligation - relationship.fear
    faction_bonus = 0
    if target.faction_id and target.faction_id in state.factions:
        faction_bonus = state.factions[target.faction_id].reputation.value // 10
    emotion_penalty = target.emotional_state.stress // 25
    return rng.randint(1, 10) + relationship_score + faction_bonus - emotion_penalty


def _relationship_id_for_player(state: GameState, target_id: str) -> str:
    relationship = get_relationship(state, target_id, state.player.id) or get_relationship(state, state.player.id, target_id)
    if relationship is None:
        raise ValueError(f"Missing relationship for social move target: {target_id}")
    return relationship.id


def _relationship_delta(state: GameState, target_id: str, amount: int, event_id: str, reason: str) -> list[StateDelta]:
    relationship_id = _relationship_id_for_player(state, target_id)
    return [
        StateDelta(operation=StateDeltaOperation.INC, path=f"relationships.{relationship_id}.trust", value=amount, caused_by_event_id=event_id, reason=reason, metadata={"source": "social_manipulation", "relationship_id": relationship_id})
    ]


def _suspicion_delta(target_id: str, amount: int, event_id: str, reason: str) -> StateDelta:
    return StateDelta(operation=StateDeltaOperation.INC, path=f"npcs.{target_id}.suspicion", value=amount, caused_by_event_id=event_id, reason=reason, metadata={"source": "social_manipulation", "npc_id": target_id})


def _known_leverage_for_target(state: GameState, target_id: str) -> LeverageState | None:
    for leverage in sorted(state.leverages.values(), key=lambda item: item.id):
        if leverage.target_npc_id == target_id and leverage.known_by_player and leverage.fact_id in state.player_visible_facts and not leverage.used:
            return leverage
    return None


def _first_revealable_known_fact(state: GameState, npc_id: str) -> str | None:
    known = sorted(set(state.npcs[npc_id].knowledge) | state.npc_knowledge.get(npc_id, set()))
    for fact_id in known:
        if fact_id in state.player_visible_facts:
            continue
        fact = state.facts.get(fact_id)
        if fact is None:
            continue
        if not npc_knows(state, npc_id, fact_id):
            continue
        if fact.visibility == FactVisibility.HIDDEN and not fact.public:
            continue
        return fact_id
    return None


def _event_id(rule: SocialManipulationRule, state: GameState, target_id: str) -> str:
    return f"event-{rule.move_type.value}-{target_id}-{state.turn}"


def _normalized(value: str) -> str:
    return value.strip().lower().replace("_", " ")
