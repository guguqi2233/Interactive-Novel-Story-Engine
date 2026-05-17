from random import Random

from app.core.world_state import GameState
from app.engine.actions.base import ActionHandler
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.combat import AttackOutcome, defend, flee, resolve_attack
from app.engine.rules.time import make_time_delta
from app.llm.schemas import PlayerActionType, PlayerIntent


class AttackActionHandler(ActionHandler):
    action_type = PlayerActionType.ATTACK

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        if intent.target_id is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Attack action requires a target.",
            )
        attack_result, deltas = resolve_attack(state, state.player.id, intent.target_id, rng)
        if attack_result.outcome == AttackOutcome.INVALID:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason=attack_result.reason,
            )
        success_level = SuccessLevel.FAILURE if attack_result.outcome == AttackOutcome.MISS else SuccessLevel.SUCCESS
        return ActionResult(
            success_level=success_level,
            reason=attack_result.reason,
            state_deltas=[make_time_delta(state, 5), *deltas],
            visible_facts=[
                f"combat:{attack_result.outcome.value}",
                *(["damage:applied"] if attack_result.damage is not None else []),
                intent.target_id,
            ],
        )


class DefendActionHandler(ActionHandler):
    action_type = PlayerActionType.DEFEND

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        return ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Player defended.",
            state_deltas=[make_time_delta(state, 5), *defend(state, state.player.id)],
            visible_facts=["combat:defensive"],
        )


class FleeActionHandler(ActionHandler):
    action_type = PlayerActionType.FLEE

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        success, deltas, reason = flee(state, state.player.id, intent.target_id)
        if not success:
            return ActionResult(
                success_level=SuccessLevel.FAILURE,
                reason=reason,
                state_deltas=[make_time_delta(state, 5)],
                visible_facts=["combat:flee_failed"],
            )
        return ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason=reason,
            state_deltas=[make_time_delta(state, 5), *deltas],
            visible_facts=["combat:fled", state.player.location_id],
        )
