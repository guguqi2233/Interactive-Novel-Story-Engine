from random import Random

from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState
from app.engine.actions.base import ActionHandler
from app.engine.actions.combat import AttackActionHandler, DefendActionHandler, FleeActionHandler
from app.engine.actions.lockpick import LockpickActionHandler
from app.engine.actions.search import SearchActionHandler
from app.engine.actions.sneak import SneakActionHandler
from app.engine.actions.trade import BuyActionHandler, SellActionHandler
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.inventory import item_is_accessible
from app.engine.rules.knowledge import get_npc_context_for_dialogue
from app.engine.rules.life_state import can_talk
from app.engine.rules.social_manipulation import SocialManipulationActionHandler
from app.engine.rules.stealth import StealthActionHandler
from app.engine.rules.time import make_time_delta
from app.engine.rules.visibility import get_visible_facts
from app.llm.schemas import PlayerActionType, PlayerIntent


class ObserveActionHandler(ActionHandler):
    action_type = PlayerActionType.OBSERVE

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        location = state.locations.get(state.player.location_id)
        if location is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Current player location does not exist.",
                hidden_facts=[f"missing_location:{state.player.location_id}"],
            )

        return ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Observed current location.",
            state_deltas=[make_time_delta(state, 5)],
            visible_facts=get_visible_facts(state, state.player.id, location.id),
        )


class MoveActionHandler(ActionHandler):
    action_type = PlayerActionType.MOVE

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        if intent.target_id is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Move action requires a target location.",
            )

        location = state.locations.get(state.player.location_id)
        if location is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Current player location does not exist.",
                hidden_facts=[f"missing_location:{state.player.location_id}"],
            )

        allowed_targets = set(location.exits.values())
        if intent.target_id not in allowed_targets:
            return ActionResult(
                success_level=SuccessLevel.FAILURE,
                reason="Target location is not reachable from the current location.",
                visible_facts=[state.player.location_id],
            )

        return ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Moved to reachable location.",
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path="player.location_id",
                    value=intent.target_id,
                    reason="Player moved through a valid exit.",
                ),
                make_time_delta(state, 10),
            ],
            visible_facts=[intent.target_id],
        )


class TalkActionHandler(ActionHandler):
    action_type = PlayerActionType.TALK

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        if intent.target_id is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Talk action requires an NPC target.",
            )

        npc = state.npcs.get(intent.target_id)
        if npc is None:
            return ActionResult(
                success_level=SuccessLevel.FAILURE,
                reason="Target NPC does not exist.",
            )
        if npc.location_id != state.player.location_id:
            return ActionResult(
                success_level=SuccessLevel.FAILURE,
                reason="Target NPC is not present.",
            )
        if not can_talk(state, npc.id):
            return ActionResult(
                success_level=SuccessLevel.FAILURE,
                reason="Target NPC cannot talk.",
            )
        if "refuse_talk" in npc.status_effects:
            return ActionResult(
                success_level=SuccessLevel.FAILURE,
                reason="Target NPC refuses to talk.",
            )

        return ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Conversation can begin.",
            state_deltas=[make_time_delta(state, 10)],
            visible_facts=_dialogue_context_facts(state, npc.id),
        )


class UseItemActionHandler(ActionHandler):
    action_type = PlayerActionType.USE_ITEM

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        if intent.target_id is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Use item action requires an item target.",
            )
        if not item_is_accessible(state, state.player.id, intent.target_id):
            return ActionResult(
                success_level=SuccessLevel.FAILURE,
                reason="Target item is not owned or accessible.",
            )
        return ActionResult(
            success_level=SuccessLevel.PARTIAL_SUCCESS,
            reason="Item is available, but no item-specific rule is registered.",
            state_deltas=[make_time_delta(state, 5)],
            visible_facts=[intent.target_id],
            hidden_facts=["missing_item_rule"],
        )


class WaitActionHandler(ActionHandler):
    action_type = PlayerActionType.WAIT

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        return ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Time passes.",
            state_deltas=[make_time_delta(state, _wait_minutes(intent))],
            visible_facts=[f"time:{_wait_minutes(intent)}"],
        )


def default_action_handlers() -> list[ActionHandler]:
    return [
        ObserveActionHandler(),
        SearchActionHandler(),
        LockpickActionHandler(),
        SneakActionHandler(),
        StealthActionHandler(),
        AttackActionHandler(),
        DefendActionHandler(),
        FleeActionHandler(),
        BuyActionHandler(),
        SellActionHandler(),
        SocialManipulationActionHandler(),
        MoveActionHandler(),
        TalkActionHandler(),
        UseItemActionHandler(),
        WaitActionHandler(),
    ]


def _dialogue_context_facts(state: GameState, npc_id: str) -> list[str]:
    context = get_npc_context_for_dialogue(state, npc_id)
    return [
        context.npc_id,
        f"mood:{context.mood}",
        f"relationship_to_player:{context.relationship_to_player}",
        *context.knowledge,
        *[f"goal:{goal}" for goal in context.goals],
    ]


def _wait_minutes(intent: PlayerIntent) -> int:
    if intent.minutes is None:
        return 30
    return max(intent.minutes, 0)
