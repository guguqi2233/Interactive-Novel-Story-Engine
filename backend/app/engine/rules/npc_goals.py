from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import GameState, NPCGoalState, NPCGoalStatus
from app.engine.rules.knowledge import npc_knows
from app.engine.rules.life_state import can_act


class NPCGoalRuleError(ValueError):
    """Raised when NPC goal rules cannot resolve a request."""


def get_active_goals(state: GameState, npc_id: str) -> list[NPCGoalState]:
    npc = _get_npc(state, npc_id)
    return [
        goal
        for goal in _structured_goals(npc.goals)
        if goal.status == NPCGoalStatus.ACTIVE and _goal_conditions_met(state, npc_id, goal)
    ]


def activate_goal(state: GameState, npc_id: str, goal_id: str) -> list[StateDelta]:
    return _set_goal_status(state, npc_id, goal_id, NPCGoalStatus.ACTIVE, "NPC goal activated.")


def complete_goal(state: GameState, npc_id: str, goal_id: str) -> list[StateDelta]:
    return _set_goal_status(state, npc_id, goal_id, NPCGoalStatus.COMPLETED, "NPC goal completed.")


def fail_goal(state: GameState, npc_id: str, goal_id: str) -> list[StateDelta]:
    return _set_goal_status(state, npc_id, goal_id, NPCGoalStatus.FAILED, "NPC goal failed.")


def choose_goal(state: GameState, npc_id: str) -> NPCGoalState | None:
    if not can_act(state, npc_id):
        return None
    active_goals = get_active_goals(state, npc_id)
    if not active_goals:
        return None
    return sorted(active_goals, key=lambda goal: (-goal.priority, goal.id))[0]


def goal_is_allowed(state: GameState, npc_id: str, goal_id: str, action_type: str) -> bool:
    goal = _get_goal(state, npc_id, goal_id)
    if action_type in goal.forbidden_actions:
        return False
    if goal.allowed_actions and action_type not in goal.allowed_actions:
        return False
    return _goal_conditions_met(state, npc_id, goal)


def build_goal_event(
    event_id: str,
    turn: int,
    npc_id: str,
    action_type: str,
    state_deltas: list[StateDelta],
) -> Event:
    return Event(
        event_id=event_id,
        turn=turn,
        actor_id="system",
        action_type=action_type,
        target_id=npc_id,
        result="npc_goal_changed",
        state_deltas=state_deltas,
        visible_to_player=False,
    )


def _set_goal_status(
    state: GameState,
    npc_id: str,
    goal_id: str,
    status: NPCGoalStatus,
    reason: str,
) -> list[StateDelta]:
    npc = _get_npc(state, npc_id)
    updated_goals: list[str | NPCGoalState] = []
    found = False
    for goal in npc.goals:
        if isinstance(goal, str):
            updated_goals.append(goal)
            continue
        if goal.id == goal_id:
            found = True
            updated_goals.append(goal.model_copy(update={"status": status}))
        else:
            updated_goals.append(goal)
    if not found:
        raise NPCGoalRuleError(f"NPC goal not found: {npc_id}.{goal_id}")

    deltas = [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"npcs.{npc_id}.goals",
            value=[_dump_goal(goal) for goal in updated_goals],
            reason=reason,
            metadata={"source": "npc_goal", "npc_id": npc_id, "goal_id": goal_id, "status": status.value},
        )
    ]
    if status == NPCGoalStatus.ACTIVE:
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"npcs.{npc_id}.current_goal_id",
                value=goal_id,
                reason="NPC current goal set.",
                metadata={"source": "npc_goal", "npc_id": npc_id, "goal_id": goal_id},
            )
        )
    return deltas


def _goal_conditions_met(state: GameState, npc_id: str, goal: NPCGoalState) -> bool:
    return all(_condition_met(state, npc_id, condition) for condition in goal.conditions)


def _condition_met(state: GameState, npc_id: str, condition: str) -> bool:
    if condition.startswith("knows:"):
        return npc_knows(state, npc_id, condition.removeprefix("knows:"))
    if condition.startswith("fact:"):
        return npc_knows(state, npc_id, condition.removeprefix("fact:"))
    if condition.startswith("flag:"):
        return bool(state.flags.get(condition.removeprefix("flag:")))
    return condition in state.npcs[npc_id].knowledge or condition in state.npc_knowledge.get(npc_id, set())


def _get_npc(state: GameState, npc_id: str):
    npc = state.npcs.get(npc_id)
    if npc is None:
        raise NPCGoalRuleError(f"NPC not found: {npc_id}")
    return npc


def _get_goal(state: GameState, npc_id: str, goal_id: str) -> NPCGoalState:
    npc = _get_npc(state, npc_id)
    for goal in _structured_goals(npc.goals):
        if goal.id == goal_id:
            return goal
    raise NPCGoalRuleError(f"NPC goal not found: {npc_id}.{goal_id}")


def _structured_goals(goals: list[str | NPCGoalState]) -> list[NPCGoalState]:
    return [goal for goal in goals if isinstance(goal, NPCGoalState)]


def _dump_goal(goal: str | NPCGoalState):
    if isinstance(goal, NPCGoalState):
        return goal.model_dump(mode="json")
    return goal


def apply_goal_deltas(state: GameState, deltas: list[StateDelta]) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state
