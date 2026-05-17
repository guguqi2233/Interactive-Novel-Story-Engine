from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, NPCScheduleEntry
from app.engine.rules.life_state import can_move
from app.engine.rules.time import get_time_of_day


class ScheduleRuleError(ValueError):
    """Raised when an NPC schedule cannot be resolved safely."""


def resolve_npc_schedules(state: GameState) -> list[StateDelta]:
    time_of_day = get_time_of_day(state)
    deltas: list[StateDelta] = []

    for npc in state.npcs.values():
        if not can_move(state, npc.id):
            continue
        entry = _schedule_entry_for_time(npc.schedule, time_of_day)
        if entry is None:
            continue
        if entry.location_id not in state.locations:
            raise ScheduleRuleError(
                f"NPC {npc.id} schedule references missing location_id: {entry.location_id}"
            )
        if npc.location_id != entry.location_id:
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"npcs.{npc.id}.location_id",
                    value=entry.location_id,
                    reason=f"NPC {npc.id} follows {time_of_day} schedule.",
                    metadata={
                        "source": "npc_schedule",
                        "npc_id": npc.id,
                        "time_of_day": time_of_day,
                    },
                )
            )
        if npc.current_activity != entry.activity:
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"npcs.{npc.id}.current_activity",
                    value=entry.activity,
                    reason=f"NPC {npc.id} activity follows {time_of_day} schedule.",
                    metadata={
                        "source": "npc_schedule",
                        "npc_id": npc.id,
                        "time_of_day": time_of_day,
                    },
                )
            )

    return deltas


def _schedule_entry_for_time(
    schedule: list[NPCScheduleEntry],
    time_of_day: str,
) -> NPCScheduleEntry | None:
    for entry in schedule:
        if entry.time_of_day == time_of_day:
            return entry
    return None
