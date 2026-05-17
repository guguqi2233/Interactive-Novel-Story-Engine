from random import Random

from app.core.world_state import GameState
from app.engine.actions.base import ActionHandler
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.combat import AttackOutcome, defend, flee, resolve_attack_with_options
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
        non_lethal = _is_non_lethal(intent.raw_text)
        attack_result, deltas = resolve_attack_with_options(
            state,
            state.player.id,
            intent.target_id,
            rng,
            lethal=not non_lethal,
        )
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
                *(["combat:non_lethal"] if non_lethal else []),
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
        success, deltas, reason = flee(state, state.player.id, intent.target_id, rng)
        if not success:
            return ActionResult(
                success_level=SuccessLevel.FAILURE,
                reason=reason,
                state_deltas=[make_time_delta(state, 5), *deltas],
                visible_facts=["combat:flee_failed"],
            )
        return ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason=reason,
            state_deltas=[make_time_delta(state, 5), *deltas],
            visible_facts=["combat:fled", state.player.location_id],
        )


def _is_non_lethal(raw_text: str) -> bool:
    text = raw_text.lower()
    return "non-lethal" in text or "nonlethal" in text or "non lethal" in text
