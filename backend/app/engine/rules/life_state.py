from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import ActorCondition, GameState, NPCState, PlayerState


class LifeStateRuleError(ValueError):
    """Raised when life state rules cannot resolve cleanly."""


def apply_damage(state: GameState, actor_id: str, amount: int, lethal: bool = False) -> list[StateDelta]:
    actor = _get_actor(state, actor_id)
    new_hp = max(actor.hp - max(amount, 0), 0)
    deltas = [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=_actor_path(actor_id, "hp"),
            value=new_hp,
            reason="Damage changed actor HP.",
            metadata={"source": "life_state", "actor_id": actor_id},
        )
    ]
    updated_condition = condition_for_hp(new_hp, actor.max_hp, lethal=lethal)
    deltas.extend(update_condition(state, actor_id, updated_condition))
    return deltas


def heal_damage(state: GameState, actor_id: str, amount: int) -> list[StateDelta]:
    actor = _get_actor(state, actor_id)
    if actor.condition == ActorCondition.DEAD:
        raise LifeStateRuleError("Dead actors cannot be healed in v0.4.8.")
    new_hp = min(actor.hp + max(amount, 0), actor.max_hp)
    deltas = [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=_actor_path(actor_id, "hp"),
            value=new_hp,
            reason="Healing changed actor HP.",
            metadata={"source": "life_state", "actor_id": actor_id},
        )
    ]
    deltas.extend(update_condition(state, actor_id, condition_for_hp(new_hp, actor.max_hp)))
    return deltas


def update_condition(state: GameState, actor_id: str, condition: ActorCondition) -> list[StateDelta]:
    _get_actor(state, actor_id)
    deltas = [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=_actor_path(actor_id, "condition"),
            value=condition,
            reason="Actor condition updated.",
            metadata={"source": "life_state", "actor_id": actor_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=_actor_path(actor_id, "alive"),
            value=condition != ActorCondition.DEAD,
            reason="Actor alive state updated.",
            metadata={"source": "life_state", "actor_id": actor_id},
        ),
    ]
    if condition in {ActorCondition.INCAPACITATED, ActorCondition.DEAD}:
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=_actor_path(actor_id, "combat_stance"),
                value="incapacitated",
                reason="Actor can no longer keep an active stance.",
                metadata={"source": "life_state", "actor_id": actor_id},
            )
        )
        status_effect = "dead" if condition == ActorCondition.DEAD else "incapacitated"
        actor = _get_actor(state, actor_id)
        if status_effect not in actor.status_effects:
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.ADD,
                    path=_actor_path(actor_id, "status_effects"),
                    value=status_effect,
                    reason="Actor gained life-state status effect.",
                    metadata={"source": "life_state", "actor_id": actor_id},
                )
            )
    elif condition == ActorCondition.WOUNDED:
        actor = _get_actor(state, actor_id)
        if "wounded" not in actor.status_effects:
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.ADD,
                    path=_actor_path(actor_id, "status_effects"),
                    value="wounded",
                    reason="Actor became wounded.",
                    metadata={"source": "life_state", "actor_id": actor_id},
                )
            )
    elif condition == ActorCondition.CRITICAL:
        actor = _get_actor(state, actor_id)
        if "critical" not in actor.status_effects:
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.ADD,
                    path=_actor_path(actor_id, "status_effects"),
                    value="critical",
                    reason="Actor became critically injured.",
                    metadata={"source": "life_state", "actor_id": actor_id},
                )
            )
    return deltas


def mark_incapacitated(state: GameState, actor_id: str) -> list[StateDelta]:
    return update_condition(state, actor_id, ActorCondition.INCAPACITATED)


def mark_dead(state: GameState, actor_id: str) -> list[StateDelta]:
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=_actor_path(actor_id, "hp"),
            value=0,
            reason="Dead actor HP set to zero.",
            metadata={"source": "life_state", "actor_id": actor_id},
        ),
        *update_condition(state, actor_id, ActorCondition.DEAD),
    ]


def can_act(state: GameState, actor_id: str) -> bool:
    actor = _get_actor(state, actor_id)
    return actor.alive and actor.condition not in {ActorCondition.INCAPACITATED, ActorCondition.DEAD}


def can_move(state: GameState, actor_id: str) -> bool:
    return can_act(state, actor_id)


def can_talk(state: GameState, actor_id: str) -> bool:
    return can_act(state, actor_id)


def condition_for_hp(hp: int, max_hp: int, lethal: bool = False) -> ActorCondition:
    if hp <= 0:
        return ActorCondition.DEAD if lethal else ActorCondition.INCAPACITATED
    if hp <= max(max_hp // 4, 1):
        return ActorCondition.CRITICAL
    if hp < max_hp:
        return ActorCondition.WOUNDED
    return ActorCondition.HEALTHY


def _get_actor(state: GameState, actor_id: str) -> PlayerState | NPCState:
    if actor_id == state.player.id:
        return state.player
    actor = state.npcs.get(actor_id)
    if actor is None:
        raise LifeStateRuleError(f"Unknown actor_id: {actor_id}")
    return actor


def _actor_path(actor_id: str, field_name: str) -> str:
    if actor_id == "player":
        return f"player.{field_name}"
    return f"npcs.{actor_id}.{field_name}"
