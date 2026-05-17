from random import Random
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import GameState
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.npc_planning import resolve_npc_planning_tick
from app.engine.rules.npc_reactions import resolve_npc_reactions
from app.engine.rules.quests import resolve_quest_triggers
from app.engine.rules.schedule import resolve_npc_schedules
from app.engine.rules.social_tick import run_social_consequence_tick
from app.llm.schemas import PlayerActionType, PlayerIntent


class WorldTickResult(BaseModel):
    state_deltas: list[StateDelta] = Field(default_factory=list)
    event: Event | None = None


def run_world_tick(
    before_tick_state: GameState,
    rng: Random | None = None,
) -> WorldTickResult:
    active_rng = rng or Random(0)
    _ = active_rng.random()
    deltas: list[StateDelta] = []
    working_state = before_tick_state

    for delta in resolve_npc_schedules(working_state):
        deltas.append(delta)
        working_state = apply_delta(working_state, delta)

    quest_deltas = _resolve_quest_tick(before_tick_state, working_state)
    for delta in quest_deltas:
        deltas.append(delta)
        working_state = apply_delta(working_state, delta)

    for delta in run_social_consequence_tick(working_state):
        deltas.append(delta)
        working_state = apply_delta(working_state, delta)

    for delta in resolve_npc_reactions(working_state):
        deltas.append(delta)
        working_state = apply_delta(working_state, delta)

    planning_result = resolve_npc_planning_tick(working_state)
    for delta in planning_result.state_deltas:
        deltas.append(delta)
        working_state = apply_delta(working_state, delta)

    for delta in _resolve_suspicion_decay(working_state):
        deltas.append(delta)
        working_state = apply_delta(working_state, delta)

    delayed_deltas = _resolve_due_delayed_consequences(working_state)
    for delta in delayed_deltas:
        deltas.append(delta)
        working_state = apply_delta(working_state, delta)

    post_delayed_quest_deltas = _resolve_quest_tick(before_tick_state, working_state)
    for delta in post_delayed_quest_deltas:
        deltas.append(delta)
        working_state = apply_delta(working_state, delta)

    if not deltas:
        return WorldTickResult()

    return WorldTickResult(
        state_deltas=deltas,
        event=Event(
            event_id=str(uuid4()),
            turn=working_state.turn,
            actor_id="system",
            action_type="world_tick",
            result="success",
            state_deltas=deltas,
            visible_to_player=_has_player_visible_delta(deltas),
            narrative_text=None,
        ),
    )


def _resolve_suspicion_decay(state: GameState) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    for npc in state.npcs.values():
        if npc.suspicion > 0:
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.INC,
                    path=f"npcs.{npc.id}.suspicion",
                    value=-1,
                    reason=f"NPC {npc.id} suspicion decays during world tick.",
                    metadata={"source": "npc_suspicion_decay", "npc_id": npc.id},
                )
            )
    return deltas


def _resolve_quest_tick(before_state: GameState, working_state: GameState) -> list[StateDelta]:
    return resolve_quest_triggers(
        before_state,
        working_state,
        _system_intent(),
        ActionResult(success_level=SuccessLevel.SUCCESS, reason="System tick."),
    )


def _resolve_due_delayed_consequences(state: GameState) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    for consequence in state.delayed_consequences:
        if not _consequence_is_due(state, consequence):
            continue
        for raw_delta in consequence.get("state_deltas", []):
            delta = StateDelta.model_validate(raw_delta)
            deltas.append(
                delta.model_copy(
                    update={
                        "metadata": {
                            **delta.metadata,
                            "source": "delayed_consequence",
                            "consequence_id": str(consequence.get("id", "")),
                        }
                    }
                )
            )
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.REMOVE,
                path="delayed_consequences",
                value=consequence,
                reason=f"Delayed consequence resolved: {consequence.get('id', 'unknown')}.",
                metadata={
                    "source": "delayed_consequence",
                    "consequence_id": str(consequence.get("id", "")),
                },
            )
        )
    return deltas


def _consequence_is_due(state: GameState, consequence: dict[str, object]) -> bool:
    due_day = consequence.get("due_day")
    due_minutes = consequence.get("due_minutes_of_day")
    if not isinstance(due_day, int) or not isinstance(due_minutes, int):
        return False
    current_total = state.current_time.day * 24 * 60 + state.current_time.minutes_of_day
    due_total = due_day * 24 * 60 + due_minutes
    return current_total >= due_total


def _system_intent() -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.WAIT,
        raw_text="system_tick",
        confidence=1.0,
        requires_clarification=False,
    )


def _has_player_visible_delta(deltas: list[StateDelta]) -> bool:
    return any(delta.metadata.get("visible_to_player") == "true" for delta in deltas)
