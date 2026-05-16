from random import Random

from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactState, FactVisibility, GameState, LockState, WorldObjectState
from app.engine.actions.base import ActionHandler
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.inventory import has_item
from app.engine.rules.time import make_time_delta
from app.llm.schemas import PlayerActionType, PlayerIntent

LOCKPICK_TOOL_TAG = "tool:lockpick"


class LockpickActionHandler(ActionHandler):
    action_type = PlayerActionType.LOCKPICK

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        if intent.target_id is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Lockpick action requires a target.",
            )

        target = state.objects.get(intent.target_id)
        if target is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Lockpick target does not exist.",
            )
        if not _target_visible_or_discovered(state, target):
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Lockpick target is not visible or discovered.",
            )
        if not target.locked:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Lockpick target is not locked.",
            )

        has_tool = _player_has_lockpick_tool(state)
        score = rng.randint(1, 10) + (4 if has_tool else 0)
        difficulty = target.lock_difficulty + (4 if not has_tool else 0)
        time_delta = make_time_delta(state, 10)

        if score >= difficulty + 3:
            return ActionResult(
                success_level=SuccessLevel.SUCCESS,
                reason="Lock opened.",
                state_deltas=[
                    time_delta,
                    StateDelta(
                        operation=StateDeltaOperation.SET,
                        path=f"objects.{target.id}.locked",
                        value=False,
                        reason="Successful lockpick opened target.",
                    ),
                    StateDelta(
                        operation=StateDeltaOperation.SET,
                        path=f"objects.{target.id}.lock_state",
                        value=LockState.OPENED,
                        reason="Successful lockpick changed lock state.",
                    ),
                ],
                visible_facts=[target.id, "lock_opened"],
            )

        fact_delta = _lock_scratched_fact_delta(state, target)
        if score >= difficulty:
            deltas = [
                time_delta,
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"objects.{target.id}.lock_state",
                    value=LockState.SCRATCHED,
                    reason="Partial lockpick left visible scratches.",
                ),
            ]
            if fact_delta is not None:
                deltas.append(fact_delta)
            return ActionResult(
                success_level=SuccessLevel.PARTIAL_SUCCESS,
                reason="Lock resisted, but the attempt left marks.",
                state_deltas=deltas,
                visible_facts=[target.id, _lock_scratched_fact_id(target.id)],
            )

        deltas = [
            time_delta,
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"objects.{target.id}.lock_state",
                value=LockState.DAMAGED,
                reason="Failed lockpick damaged the lock.",
            ),
        ]
        if fact_delta is not None:
            deltas.append(fact_delta)
        return ActionResult(
            success_level=SuccessLevel.FAILURE,
            reason="Lockpick failed and damaged the lock.",
            state_deltas=deltas,
            visible_facts=[target.id, _lock_scratched_fact_id(target.id)],
        )


def _target_visible_or_discovered(state: GameState, target: WorldObjectState) -> bool:
    if target.location_id != state.player.location_id and target.owner_id != state.player.id:
        return False
    if not target.visible:
        return False
    return not target.hidden or state.player.id in target.discovered_by


def _player_has_lockpick_tool(state: GameState) -> bool:
    return any(
        item.owner_id == state.player.id and LOCKPICK_TOOL_TAG in item.tags
        for item in state.objects.values()
    ) or any(
        has_item(state, state.player.id, item_id)
        for item_id, item in state.objects.items()
        if LOCKPICK_TOOL_TAG in item.tags
    )


def _lock_scratched_fact_id(target_id: str) -> str:
    return f"{target_id}_lock_scratched"


def _lock_scratched_fact_delta(state: GameState, target: WorldObjectState) -> StateDelta | None:
    fact_id = _lock_scratched_fact_id(target.id)
    if fact_id in state.facts:
        if fact_id in state.player_visible_facts:
            return None
        return StateDelta(
            operation=StateDeltaOperation.ADD,
            path="player_visible_facts",
            value=fact_id,
            reason="Lockpick marks became visible to the player.",
            metadata={"source": "lockpick", "fact_id": fact_id},
        )
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"facts.{fact_id}",
        value=FactState(
            id=fact_id,
            text=f"The lock on {target.id} has fresh scratches.",
            visibility=FactVisibility.PUBLIC,
            public=True,
            tags=[f"object:{target.id}", "lockpick"],
        ),
        reason="Lockpick created a visible lock mark fact.",
        metadata={"source": "lockpick", "fact_id": fact_id},
    )
