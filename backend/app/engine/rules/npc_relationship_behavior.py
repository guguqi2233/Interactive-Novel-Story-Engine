from enum import StrEnum
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, NPCIntent, RelationshipState
from app.engine.rules.life_state import can_act
from app.engine.rules.npc_intents import enqueue_intent
from app.engine.rules.npc_simulation_boundary import NPCSimulationPolicy
from app.engine.rules.relationship_tone import RelationshipTone, derive_tone_from_relationship


class RelationshipBehaviorType(StrEnum):
    HELP_ACTOR = "help_actor"
    WARN_ACTOR = "warn_actor"
    AVOID_ACTOR = "avoid_actor"
    REPORT_ACTOR = "report_actor"
    LIE_TO_ACTOR = "lie_to_actor"
    WITHHOLD_INFORMATION = "withhold_information"
    SHARE_KNOWN_RUMOR = "share_known_rumor"
    SEEK_RECONCILIATION = "seek_reconciliation"


class RelationshipBehaviorRule(BaseModel):
    id: str
    behavior_type: RelationshipBehaviorType
    min_trust: int | None = None
    max_trust: int | None = None
    min_fear: int | None = None
    max_fear: int | None = None
    min_affinity: int | None = None
    max_affinity: int | None = None
    min_obligation: int | None = None
    max_obligation: int | None = None
    min_hostility: int | None = None
    required_fact_ids: list[str] = Field(default_factory=list)
    required_rumor_ids: list[str] = Field(default_factory=list)
    priority: int = 0
    target_id: str | None = None
    intent_type: str | None = None


class RelationshipBehaviorCandidate(BaseModel):
    rule_id: str
    behavior_type: RelationshipBehaviorType
    npc_id: str
    target_id: str
    intent: NPCIntent | None = None
    plan_candidate: dict[str, str] | None = None


class RelationshipBehaviorResult(BaseModel):
    state_deltas: list[StateDelta] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    candidates: list[RelationshipBehaviorCandidate] = Field(default_factory=list)
    skipped_rule_ids: list[str] = Field(default_factory=list)


DEFAULT_RELATIONSHIP_BEHAVIOR_RULES = [
    RelationshipBehaviorRule(
        id="trusted-help-player",
        behavior_type=RelationshipBehaviorType.HELP_ACTOR,
        min_trust=50,
        priority=5,
    ),
    RelationshipBehaviorRule(
        id="trusted-warn-player",
        behavior_type=RelationshipBehaviorType.WARN_ACTOR,
        min_trust=35,
        required_rumor_ids=[],
        priority=4,
    ),
    RelationshipBehaviorRule(
        id="fearful-avoid-player",
        behavior_type=RelationshipBehaviorType.AVOID_ACTOR,
        min_fear=50,
        priority=6,
    ),
    RelationshipBehaviorRule(
        id="hostile-report-player",
        behavior_type=RelationshipBehaviorType.REPORT_ACTOR,
        max_trust=-20,
        min_hostility=30,
        priority=5,
    ),
]


def resolve_relationship_behaviors(
    state: GameState,
    npc_id: str,
    target_id: str = "player",
    rules: list[RelationshipBehaviorRule] | None = None,
) -> RelationshipBehaviorResult:
    if npc_id not in state.npcs or not can_act(state, npc_id):
        return RelationshipBehaviorResult()
    relationship = _relationship_for_behavior(state, npc_id, target_id)
    if relationship is None:
        return RelationshipBehaviorResult()
    tone = derive_tone_from_relationship(relationship, emotional_state=state.npcs[npc_id].emotional_state)
    context = NPCSimulationPolicy().build_context(state, npc_id).npc_known_context
    result = RelationshipBehaviorResult()
    for rule in rules or DEFAULT_RELATIONSHIP_BEHAVIOR_RULES:
        if _already_processed(state, npc_id, target_id, rule.id):
            continue
        if not _rule_matches(rule, relationship, tone):
            result.skipped_rule_ids.append(rule.id)
            continue
        if not set(rule.required_fact_ids).issubset(context.fact_ids):
            result.skipped_rule_ids.append(rule.id)
            continue
        if not set(rule.required_rumor_ids).issubset(context.rumor_ids):
            result.skipped_rule_ids.append(rule.id)
            continue
        deltas, candidate = _behavior_output(state, npc_id, target_id, relationship, tone, rule)
        if not deltas:
            result.skipped_rule_ids.append(rule.id)
            continue
        marker = _behavior_marker(npc_id, target_id, rule.id)
        deltas.append(marker)
        result.state_deltas.extend(deltas)
        result.events.append(_build_behavior_event(state, npc_id, target_id, rule, deltas))
        result.candidates.append(candidate)
    return result


def _relationship_for_behavior(state: GameState, npc_id: str, target_id: str) -> RelationshipState | None:
    if npc_id not in state.npcs:
        return None
    for relationship in state.relationships.values():
        if relationship.source_id == npc_id and relationship.target_id == target_id:
            return relationship
    return None


def _rule_matches(rule: RelationshipBehaviorRule, relationship: RelationshipState, tone: RelationshipTone) -> bool:
    values = {
        "trust": relationship.trust,
        "fear": relationship.fear,
        "affinity": relationship.affinity,
        "obligation": relationship.obligation,
        "hostility": max(0, -relationship.trust) + tone.resentment,
    }
    bounds = [
        ("trust", rule.min_trust, rule.max_trust),
        ("fear", rule.min_fear, rule.max_fear),
        ("affinity", rule.min_affinity, rule.max_affinity),
        ("obligation", rule.min_obligation, rule.max_obligation),
        ("hostility", rule.min_hostility, None),
    ]
    for name, minimum, maximum in bounds:
        if minimum is not None and values[name] < minimum:
            return False
        if maximum is not None and values[name] > maximum:
            return False
    return True


def _behavior_output(
    state: GameState,
    npc_id: str,
    target_id: str,
    relationship: RelationshipState,
    tone: RelationshipTone,
    rule: RelationshipBehaviorRule,
) -> tuple[list[StateDelta], RelationshipBehaviorCandidate]:
    intent = _intent_for_behavior(state, npc_id, target_id, rule)
    if intent is not None:
        queued = enqueue_intent(state, npc_id, intent)
        return queued.state_deltas, RelationshipBehaviorCandidate(
            rule_id=rule.id,
            behavior_type=rule.behavior_type,
            npc_id=npc_id,
            target_id=target_id,
            intent=queued.selected_intent,
            plan_candidate={"source": "relationship_behavior", "rule_id": rule.id},
        )
    path = f"npcs.{npc_id}.plan_state.relationship_behavior.{rule.behavior_type.value}:{target_id}"
    delta = StateDelta(
        operation=StateDeltaOperation.SET,
        path=path,
        value={"relationship_id": relationship.id, "tone": tone.trust_expression},
        reason="NPC relationship behavior recorded a bounded non-action signal.",
        metadata={"source": "npc_relationship_behavior", "npc_id": npc_id, "target_id": target_id, "rule_id": rule.id},
    )
    return [delta], RelationshipBehaviorCandidate(
        rule_id=rule.id,
        behavior_type=rule.behavior_type,
        npc_id=npc_id,
        target_id=target_id,
    )


def _intent_for_behavior(
    state: GameState,
    npc_id: str,
    target_id: str,
    rule: RelationshipBehaviorRule,
) -> NPCIntent | None:
    intent_type = rule.intent_type or _default_intent_type(rule.behavior_type)
    if intent_type is None:
        return None
    intent_target_id = rule.target_id or _default_intent_target(state, npc_id, target_id, rule)
    if intent_target_id is None:
        return None
    preconditions = [f"fact:{fact_id}" for fact_id in rule.required_fact_ids]
    preconditions.extend(f"rumor:{rumor_id}" for rumor_id in rule.required_rumor_ids)
    return NPCIntent(
        id=f"relationship-{rule.id}-{npc_id}-{target_id}",
        npc_id=npc_id,
        intent_type=intent_type,
        priority=rule.priority,
        target_id=intent_target_id,
        target_type=_target_type_for_intent(intent_type),
        created_turn=state.turn,
        preconditions=sorted(set(preconditions)),
        debug_reason=f"relationship_behavior:{rule.id}",
    )


def _default_intent_type(behavior: RelationshipBehaviorType) -> str | None:
    return {
        RelationshipBehaviorType.HELP_ACTOR: "talk_to_npc",
        RelationshipBehaviorType.WARN_ACTOR: "talk_to_npc",
        RelationshipBehaviorType.AVOID_ACTOR: "avoid_actor",
        RelationshipBehaviorType.REPORT_ACTOR: "report_crime",
        RelationshipBehaviorType.SHARE_KNOWN_RUMOR: "spread_rumor",
        RelationshipBehaviorType.SEEK_RECONCILIATION: "talk_to_npc",
    }.get(behavior)


def _default_intent_target(
    state: GameState,
    npc_id: str,
    target_id: str,
    rule: RelationshipBehaviorRule,
) -> str | None:
    if rule.behavior_type == RelationshipBehaviorType.REPORT_ACTOR:
        for crime in sorted(state.crimes.values(), key=lambda item: item.id):
            if crime.actor_id == target_id and (npc_id in crime.witnessed_by or f"crime:{crime.id}" in state.npcs[npc_id].knowledge):
                return crime.id
        return None
    if rule.behavior_type == RelationshipBehaviorType.SHARE_KNOWN_RUMOR:
        rumor_ids = rule.required_rumor_ids or sorted(
            rumor.id for rumor in state.rumors.values() if npc_id in rumor.known_by_npcs
        )
        return rumor_ids[0] if rumor_ids else None
    return target_id


def _target_type_for_intent(intent_type: str) -> str:
    return {
        "report_crime": "crime",
        "spread_rumor": "rumor",
        "avoid_actor": "npc",
        "talk_to_npc": "npc",
    }.get(intent_type, "npc")


def _build_behavior_event(
    state: GameState,
    npc_id: str,
    target_id: str,
    rule: RelationshipBehaviorRule,
    deltas: list[StateDelta],
) -> Event:
    return Event(
        event_id=f"npc-relationship-behavior-{state.turn}-{npc_id}-{target_id}-{rule.id}",
        turn=state.turn,
        actor_id="system",
        action_type="npc_relationship_behavior",
        target_id=npc_id,
        result=rule.behavior_type.value,
        state_deltas=deltas,
        visible_to_player=False,
        created_at=datetime.fromtimestamp(state.turn, timezone.utc),
    )


def _already_processed(state: GameState, npc_id: str, target_id: str, rule_id: str) -> bool:
    return state.social_flags.get(_behavior_key(npc_id, target_id, rule_id)) is True


def _behavior_marker(npc_id: str, target_id: str, rule_id: str) -> StateDelta:
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"social_flags.{_behavior_key(npc_id, target_id, rule_id)}",
        value=True,
        reason="NPC relationship behavior processed.",
        metadata={"source": "npc_relationship_behavior", "npc_id": npc_id, "target_id": target_id, "rule_id": rule_id},
    )


def _behavior_key(npc_id: str, target_id: str, rule_id: str) -> str:
    safe_rule = rule_id.replace(":", "_").replace("-", "_")
    return f"npc_relationship_behavior_{npc_id}_{target_id}_{safe_rule}"
