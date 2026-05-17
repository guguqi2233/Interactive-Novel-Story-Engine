from enum import StrEnum
from random import Random

from pydantic import BaseModel, Field

from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    CombatState,
    CombatStatus,
    CombatantStance,
    CombatantState,
    GameState,
    NPCState,
    PlayerState,
)
from app.engine.rules.life_state import apply_damage as apply_life_damage
from app.engine.rules.life_state import can_act


class CombatRuleError(ValueError):
    """Raised when combat rules cannot resolve cleanly."""


class AttackOutcome(StrEnum):
    HIT = "hit"
    MISS = "miss"
    GLANCING = "glancing"
    CRITICAL = "critical"
    INVALID = "invalid"


class DamageResult(BaseModel):
    target_id: str
    damage: int = Field(ge=0)
    resulting_hp: int = Field(ge=0)
    status_effects: list[str] = Field(default_factory=list)


class AttackResult(BaseModel):
    outcome: AttackOutcome
    attacker_id: str
    target_id: str | None = None
    damage: DamageResult | None = None
    reason: str


def can_attack(state: GameState, attacker_id: str, target_id: str) -> tuple[bool, str]:
    if attacker_id != state.player.id:
        return False, "Only player attacks are supported in v0.4.7."
    target = state.npcs.get(target_id)
    if target is None:
        return False, "Attack target does not exist."
    if target.location_id != state.player.location_id:
        return False, "Attack target is not reachable."
    if target.hidden and state.player.id not in target.discovered_by:
        return False, "Attack target is not visible."
    if not can_act(state, target_id):
        return False, "Attack target is not able to fight."
    if not can_act(state, attacker_id):
        return False, "Attacker is not able to fight."
    return True, "Attack is valid."


def resolve_attack(state: GameState, attacker_id: str, target_id: str, rng: Random) -> tuple[AttackResult, list[StateDelta]]:
    allowed, reason = can_attack(state, attacker_id, target_id)
    if not allowed:
        return AttackResult(outcome=AttackOutcome.INVALID, attacker_id=attacker_id, target_id=target_id, reason=reason), []

    attacker = state.player
    target = state.npcs[target_id]
    roll = rng.randint(1, 10)
    attack_score = roll + attacker.attack
    defense_score = 6 + target.defense + (2 if target.combat_stance == CombatantStance.DEFENSIVE else 0)

    if attack_score >= defense_score + 6:
        outcome = AttackOutcome.CRITICAL
        damage = 5
    elif attack_score >= defense_score:
        outcome = AttackOutcome.HIT
        damage = 3
    elif attack_score >= defense_score - 2:
        outcome = AttackOutcome.GLANCING
        damage = 1
    else:
        outcome = AttackOutcome.MISS
        damage = 0

    deltas = [
        _combat_state_delta(state, attacker_id, target_id),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path="player.combat_stance",
            value=CombatantStance.AGGRESSIVE,
            reason="Player entered an aggressive combat stance.",
            metadata={"source": "combat", "combat_action": "attack"},
        ),
    ]
    if target_id not in target.hostile_to:
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path=f"npcs.{target_id}.hostile_to",
                value=attacker_id,
                reason="NPC became hostile after being attacked.",
                metadata={"source": "combat", "combat_action": "attack"},
            )
        )

    damage_result: DamageResult | None = None
    if damage > 0:
        damage_result, damage_deltas = apply_damage(state, target_id, damage)
        deltas.extend(damage_deltas)

    return (
        AttackResult(
            outcome=outcome,
            attacker_id=attacker_id,
            target_id=target_id,
            damage=damage_result,
            reason=f"Attack result: {outcome.value}.",
        ),
        deltas,
    )


def apply_damage(state: GameState, target_id: str, damage: int) -> tuple[DamageResult, list[StateDelta]]:
    target = state.npcs.get(target_id)
    if target is None:
        raise CombatRuleError(f"Damage target does not exist: {target_id}")
    resulting_hp = max(target.hp - damage, 0)
    status_effects = _status_effects_for_hp(resulting_hp)
    deltas = [
        delta.model_copy(
            update={
                "metadata": {
                    **delta.metadata,
                    "source": "combat",
                    "target_id": target_id,
                }
            }
        )
        for delta in apply_life_damage(state, target_id, damage)
    ]
    return DamageResult(target_id=target_id, damage=damage, resulting_hp=resulting_hp, status_effects=status_effects), deltas


def defend(state: GameState, actor_id: str) -> list[StateDelta]:
    if actor_id != state.player.id:
        raise CombatRuleError("Only player defend is supported in v0.4.7.")
    deltas = [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path="player.combat_stance",
            value=CombatantStance.DEFENSIVE,
            reason="Player took a defensive stance.",
            metadata={"source": "combat", "combat_action": "defend"},
        )
    ]
    if "guarded" not in state.player.status_effects:
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path="player.status_effects",
                value="guarded",
                reason="Player is guarded after defending.",
                metadata={"source": "combat", "combat_action": "defend"},
            )
        )
    return deltas


def flee(state: GameState, actor_id: str, target_location_id: str | None = None) -> tuple[bool, list[StateDelta], str]:
    if actor_id != state.player.id:
        return False, [], "Only player flee is supported in v0.4.7."
    location = state.locations.get(state.player.location_id)
    if location is None:
        return False, [], "Current location does not exist."
    destination = target_location_id or next(iter(location.exits.values()), None)
    if destination is None or destination not in set(location.exits.values()):
        return False, [], "No reachable flee destination."
    deltas = [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path="player.location_id",
            value=destination,
            reason="Player fled to a reachable location.",
            metadata={"source": "combat", "combat_action": "flee"},
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path="player.combat_stance",
            value=CombatantStance.FLEEING,
            reason="Player is fleeing combat.",
            metadata={"source": "combat", "combat_action": "flee"},
        ),
    ]
    for combat_id, combat in state.combats.items():
        if state.player.id in combat.combatant_ids and combat.status == CombatStatus.ACTIVE:
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"combats.{combat_id}.status",
                    value=CombatStatus.ENDED,
                    reason="Player fled active combat.",
                    metadata={"source": "combat", "combat_action": "flee", "combat_id": combat_id},
                )
            )
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"combats.{combat_id}.ended_turn",
                    value=state.turn,
                    reason="Combat ended when player fled.",
                    metadata={"source": "combat", "combat_action": "flee", "combat_id": combat_id},
                )
            )
    return True, deltas, "Player fled combat."


def combatant_from_actor(state: GameState, actor_id: str) -> CombatantState:
    actor = state.player if actor_id == state.player.id else state.npcs.get(actor_id)
    if actor is None:
        raise CombatRuleError(f"Unknown combatant actor_id: {actor_id}")
    try:
        stance = CombatantStance(actor.combat_stance)
    except ValueError:
        stance = CombatantStance.AGGRESSIVE
    return CombatantState(
        actor_id=actor_id,
        hp=actor.hp,
        max_hp=actor.max_hp,
        stamina=actor.stamina,
        status_effects=actor.status_effects,
        stance=stance,
    )


def _combat_state_delta(state: GameState, attacker_id: str, target_id: str) -> StateDelta:
    combat_id = _combat_id(state.player.location_id, attacker_id, target_id)
    combat = state.combats.get(combat_id) or CombatState(
        id=combat_id,
        location_id=state.player.location_id,
        combatant_ids=[attacker_id, target_id],
        status=CombatStatus.ACTIVE,
        started_turn=state.turn,
    )
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"combats.{combat_id}",
        value=combat,
        reason="Combat state opened or refreshed.",
        metadata={"source": "combat", "combat_id": combat_id},
    )


def _combat_id(location_id: str, attacker_id: str, target_id: str) -> str:
    return f"combat_{location_id}_{attacker_id}_{target_id}"


def _status_effects_for_hp(hp: int) -> list[str]:
    if hp == 0:
        return ["incapacitated"]
    return ["injured"]
