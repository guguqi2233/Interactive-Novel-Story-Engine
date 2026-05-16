from random import Random

from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, LocationState
from app.engine.actions.base import ActionHandler
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.time import make_time_delta
from app.llm.schemas import PlayerActionType, PlayerIntent


class SneakActionHandler(ActionHandler):
    action_type = PlayerActionType.SNEAK

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        target = _resolve_sneak_target(intent, state)
        if target is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Sneak target is not valid or reachable.",
            )

        observers = _possible_observers(state, target["destination_id"])
        score = _sneak_score(state, target["destination_id"], rng)
        difficulty = _sneak_difficulty(state, target["destination_id"], observers)
        time_delta = make_time_delta(state, 10)

        if score >= difficulty + 3:
            return ActionResult(
                success_level=SuccessLevel.SUCCESS,
                reason="Player sneaked without being noticed.",
                state_deltas=[
                    time_delta,
                    *_movement_deltas(state, target),
                ],
                visible_facts=[target["visible_target"]],
            )

        suspicion_deltas = _suspicion_deltas(observers, amount=1, reason="Sneak attempt raised suspicion.")
        if score >= difficulty:
            return ActionResult(
                success_level=SuccessLevel.PARTIAL_SUCCESS,
                reason="Player reached the target but left signs of movement.",
                state_deltas=[
                    time_delta,
                    *_movement_deltas(state, target),
                    *suspicion_deltas,
                ],
                visible_facts=[target["visible_target"], "suspicion:raised"],
            )

        failure_deltas = _suspicion_deltas(observers, amount=2, reason="Sneak attempt failed and raised suspicion.")
        return ActionResult(
            success_level=SuccessLevel.FAILURE,
            reason="Sneak attempt failed.",
            state_deltas=[time_delta, *failure_deltas],
            visible_facts=["sneak_failed"],
        )


def _resolve_sneak_target(intent: PlayerIntent, state: GameState) -> dict[str, str] | None:
    if intent.target_id is None:
        return None
    current_location = state.locations.get(state.player.location_id)
    if current_location is None:
        return None

    if intent.target_id in state.locations:
        if intent.target_id not in set(current_location.exits.values()):
            return None
        return {
            "kind": "location",
            "destination_id": intent.target_id,
            "visible_target": intent.target_id,
        }

    target_object = state.objects.get(intent.target_id)
    if target_object is not None:
        if target_object.location_id != state.player.location_id:
            return None
        if target_object.hidden and state.player.id not in target_object.discovered_by:
            return None
        return {
            "kind": "object",
            "destination_id": state.player.location_id,
            "visible_target": intent.target_id,
        }

    target_npc = state.npcs.get(intent.target_id)
    if target_npc is not None:
        if target_npc.location_id != state.player.location_id:
            return None
        if target_npc.hidden and state.player.id not in target_npc.discovered_by:
            return None
        return {
            "kind": "npc",
            "destination_id": state.player.location_id,
            "visible_target": intent.target_id,
        }

    return None


def _movement_deltas(state: GameState, target: dict[str, str]) -> list[StateDelta]:
    if target["kind"] != "location" or state.player.location_id == target["destination_id"]:
        return []
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path="player.location_id",
            value=target["destination_id"],
            reason="Player moved stealthily to reachable location.",
        )
    ]


def _possible_observers(state: GameState, destination_id: str) -> list[str]:
    return [
        npc.id
        for npc in state.npcs.values()
        if npc.location_id in {state.player.location_id, destination_id}
    ]


def _sneak_score(state: GameState, destination_id: str, rng: Random) -> int:
    destination = state.locations.get(destination_id)
    return rng.randint(1, 10) + state.player.stealth_modifier + _cover_bonus(destination)


def _sneak_difficulty(state: GameState, destination_id: str, observers: list[str]) -> int:
    destination = state.locations.get(destination_id)
    observer_pressure = sum(
        state.npcs[npc_id].alertness + state.npcs[npc_id].suspicion
        for npc_id in observers
    )
    return 6 + observer_pressure + _light_penalty(destination) - _cover_bonus(destination)


def _cover_bonus(location: LocationState | None) -> int:
    return location.cover_level if location is not None else 0


def _light_penalty(location: LocationState | None) -> int:
    if location is None:
        return 0
    return max(location.light_level - 5, 0)


def _suspicion_deltas(observers: list[str], amount: int, reason: str) -> list[StateDelta]:
    return [
        StateDelta(
            operation=StateDeltaOperation.INC,
            path=f"npcs.{npc_id}.suspicion",
            value=amount,
            reason=reason,
            metadata={"source": "sneak", "npc_id": npc_id},
        )
        for npc_id in observers
    ]
