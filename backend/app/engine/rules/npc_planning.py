from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import ActorCondition, CrimeStatus, GameState, NPCGoalState
from app.engine.rules.knowledge import npc_knows
from app.engine.rules.life_state import can_act
from app.engine.rules.npc_goals import choose_goal, goal_is_allowed
from app.engine.rules.relationships import relationship_score
from app.engine.rules.rumors import add_rumor_to_npc, best_rumor_target


class NPCPlanStep(BaseModel):
    npc_id: str
    goal_id: str | None = None
    plan_type: str
    target_id: str | None = None
    reason_code: str
    visible_to_player: bool = False


class NPCPlanningResult(BaseModel):
    state_deltas: list[StateDelta] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)
    steps: list[NPCPlanStep] = Field(default_factory=list)


PLANNING_ACTIONS = {
    "move_to_location",
    "talk_to_npc",
    "report_crime",
    "spread_rumor",
    "flee_location",
    "guard_location",
    "rest_if_injured",
}


def resolve_npc_planning_tick(state: GameState) -> NPCPlanningResult:
    working_state = state
    result = NPCPlanningResult()
    for npc in sorted(state.npcs.values(), key=lambda item: item.id):
        if not can_act(working_state, npc.id):
            continue
        step = choose_plan_for_npc(working_state, npc.id)
        if step is None:
            continue
        deltas = resolve_plan_step(working_state, step)
        if not deltas:
            continue
        result.steps.append(step)
        result.state_deltas.extend(deltas)
        result.events.append(_build_plan_event(working_state, step, deltas))
        for delta in deltas:
            working_state = apply_delta(working_state, delta)
    return result


def choose_plan_for_npc(state: GameState, npc_id: str) -> NPCPlanStep | None:
    npc = state.npcs.get(npc_id)
    if npc is None or not can_act(state, npc_id):
        return None

    if npc.condition in {ActorCondition.WOUNDED, ActorCondition.CRITICAL}:
        return NPCPlanStep(
            npc_id=npc_id,
            plan_type="rest_if_injured",
            reason_code="injured",
            visible_to_player=_npc_visible_to_player(state, npc_id),
        )

    goal = choose_goal(state, npc_id)
    if goal is not None:
        goal_step = _plan_from_goal(state, npc_id, goal)
        if goal_step is not None:
            return goal_step

    crime_step = _report_crime_step(state, npc_id)
    if crime_step is not None:
        return crime_step

    rumor_step = _spread_rumor_step(state, npc_id, None)
    if rumor_step is not None:
        return rumor_step

    return None


def resolve_plan_step(state: GameState, step: NPCPlanStep) -> list[StateDelta]:
    if step.plan_type not in PLANNING_ACTIONS:
        return []
    if step.plan_type == "move_to_location" and step.target_id:
        return _move_to_location(state, step)
    if step.plan_type == "talk_to_npc" and step.target_id:
        return _talk_to_npc(state, step)
    if step.plan_type == "report_crime" and step.target_id:
        return _report_crime(state, step)
    if step.plan_type == "spread_rumor" and step.target_id:
        return _spread_rumor(state, step)
    if step.plan_type == "flee_location":
        return _flee_location(state, step)
    if step.plan_type == "guard_location":
        return _guard_location(state, step)
    if step.plan_type == "rest_if_injured":
        return _rest_if_injured(state, step)
    return []


def _plan_from_goal(state: GameState, npc_id: str, goal: NPCGoalState) -> NPCPlanStep | None:
    for action_type in goal.allowed_actions:
        if not goal_is_allowed(state, npc_id, goal.id, action_type):
            continue
        if action_type == "spread_rumor":
            return _spread_rumor_step(state, npc_id, goal)
        if action_type == "talk_to_npc":
            target = _same_location_npc(state, npc_id)
            if target:
                return NPCPlanStep(npc_id=npc_id, goal_id=goal.id, plan_type="talk_to_npc", target_id=target, reason_code="goal_talk")
        if action_type in {"move", "move_to_location"}:
            target_location = _goal_target_location(state, npc_id, goal)
            if target_location:
                return NPCPlanStep(npc_id=npc_id, goal_id=goal.id, plan_type="move_to_location", target_id=target_location, reason_code="goal_move")
        if action_type == "guard_location":
            return NPCPlanStep(npc_id=npc_id, goal_id=goal.id, plan_type="guard_location", target_id=state.npcs[npc_id].location_id, reason_code="goal_guard")
    return None


def _report_crime_step(state: GameState, npc_id: str) -> NPCPlanStep | None:
    for crime in sorted(state.crimes.values(), key=lambda item: item.id):
        if crime.status == CrimeStatus.REPORTED:
            continue
        if npc_id not in crime.witnessed_by and not npc_knows(state, npc_id, f"crime:{crime.id}"):
            continue
        return NPCPlanStep(npc_id=npc_id, plan_type="report_crime", target_id=crime.id, reason_code="known_crime")
    return None


def _spread_rumor_step(state: GameState, npc_id: str, goal: NPCGoalState | None) -> NPCPlanStep | None:
    for rumor in sorted(state.rumors.values(), key=lambda item: item.id):
        if npc_id not in rumor.known_by_npcs:
            continue
        target = best_rumor_target(state, npc_id, excluded_ids=set(rumor.known_by_npcs))
        if target:
            return NPCPlanStep(npc_id=npc_id, goal_id=goal.id if goal else None, plan_type="spread_rumor", target_id=rumor.id, reason_code="known_rumor")
    return None


def _move_to_location(state: GameState, step: NPCPlanStep) -> list[StateDelta]:
    npc = state.npcs[step.npc_id]
    current = state.locations.get(npc.location_id)
    if current is None or step.target_id not in current.exits.values():
        return []
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"npcs.{step.npc_id}.location_id",
            value=step.target_id,
            reason="NPC planning moved to a reachable location.",
            metadata=_metadata(step),
        )
    ]


def _talk_to_npc(state: GameState, step: NPCPlanStep) -> list[StateDelta]:
    target = state.npcs.get(step.target_id or "")
    npc = state.npcs[step.npc_id]
    if target is None or target.location_id != npc.location_id or not can_act(state, target.id):
        return []
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"npcs.{step.npc_id}.current_activity",
            value=f"talking_to:{target.id}",
            reason="NPC planning started a conversation.",
            metadata=_metadata(step),
        )
    ]


def _report_crime(state: GameState, step: NPCPlanStep) -> list[StateDelta]:
    crime = state.crimes.get(step.target_id or "")
    if crime is None or step.npc_id not in crime.witnessed_by and not npc_knows(state, step.npc_id, f"crime:{crime.id}"):
        return []
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"crimes.{crime.id}.status",
            value=CrimeStatus.REPORTED,
            reason="NPC planning reported a known crime.",
            metadata=_metadata(step),
        ),
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"crimes.{crime.id}.reported_to",
            value="local_authority",
            reason="Crime was reported to local authority.",
            metadata=_metadata(step),
        ),
    ]


def _spread_rumor(state: GameState, step: NPCPlanStep) -> list[StateDelta]:
    rumor = state.rumors.get(step.target_id or "")
    if rumor is None or step.npc_id not in rumor.known_by_npcs:
        return []
    target = best_rumor_target(state, step.npc_id, excluded_ids=set(rumor.known_by_npcs))
    if target is None:
        return []
    return [
        *add_rumor_to_npc(state, rumor.id, target),
        StateDelta(
            operation=StateDeltaOperation.INC,
            path=f"rumors.{rumor.id}.spread_level",
            value=1,
            reason="NPC planning spread a known rumor.",
            metadata={**_metadata(step), "to_npc_id": target},
        ),
    ]


def _flee_location(state: GameState, step: NPCPlanStep) -> list[StateDelta]:
    npc = state.npcs[step.npc_id]
    location = state.locations.get(npc.location_id)
    if location is None or not location.exits:
        return []
    destination = next(iter(location.exits.values()))
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"npcs.{step.npc_id}.location_id",
            value=destination,
            reason="NPC planning fled to a reachable location.",
            metadata=_metadata(step),
        )
    ]


def _guard_location(state: GameState, step: NPCPlanStep) -> list[StateDelta]:
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"npcs.{step.npc_id}.current_activity",
            value=f"guarding:{state.npcs[step.npc_id].location_id}",
            reason="NPC planning guards the current location.",
            metadata=_metadata(step),
        )
    ]


def _rest_if_injured(state: GameState, step: NPCPlanStep) -> list[StateDelta]:
    npc = state.npcs[step.npc_id]
    if npc.condition not in {ActorCondition.WOUNDED, ActorCondition.CRITICAL}:
        return []
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"npcs.{step.npc_id}.current_activity",
            value="resting",
            reason="NPC planning rests while injured.",
            metadata=_metadata(step),
        ),
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"npcs.{step.npc_id}.status_effects",
            value="resting",
            reason="NPC is resting.",
            metadata=_metadata(step),
        ),
    ]


def _same_location_npc(state: GameState, npc_id: str, excluded_ids: set[str] | None = None) -> str | None:
    npc = state.npcs[npc_id]
    blocked = excluded_ids or set()
    candidates = []
    for target in state.npcs.values():
        if target.id == npc_id or target.id in blocked:
            continue
        if target.location_id == npc.location_id and can_act(state, target.id):
            candidates.append(target)
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-relationship_score(state, npc_id, item.id), item.id))
    return candidates[0].id


def _goal_target_location(state: GameState, npc_id: str, goal: NPCGoalState) -> str | None:
    target = goal.desired_state.get("location_id") or goal.desired_state.get("location")
    if not isinstance(target, str):
        return None
    current = state.locations.get(state.npcs[npc_id].location_id)
    if current is None or target not in current.exits.values():
        return None
    return target


def _npc_visible_to_player(state: GameState, npc_id: str) -> bool:
    npc = state.npcs[npc_id]
    return npc.location_id == state.player.location_id and npc.visible and (not npc.hidden or state.player.id in npc.discovered_by)


def _metadata(step: NPCPlanStep) -> dict[str, str]:
    metadata = {
        "source": "npc_planning",
        "npc_id": step.npc_id,
        "plan_type": step.plan_type,
        "reason_code": step.reason_code,
    }
    if step.goal_id:
        metadata["goal_id"] = step.goal_id
    if step.target_id:
        metadata["target_id"] = step.target_id
    if step.visible_to_player:
        metadata["visible_to_player"] = "true"
    return metadata


def _build_plan_event(state: GameState, step: NPCPlanStep, deltas: list[StateDelta]) -> Event:
    return Event(
        event_id=f"npc-plan-{state.turn}-{step.npc_id}-{step.plan_type}-{step.target_id or 'none'}",
        turn=state.turn,
        actor_id="system",
        action_type="npc_planning",
        target_id=step.npc_id,
        result=step.plan_type,
        state_deltas=deltas,
        visible_to_player=any(delta.metadata.get("visible_to_player") == "true" for delta in deltas),
    )
