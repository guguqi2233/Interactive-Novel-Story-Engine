from random import Random

from app.core.world_state import GameState
from app.engine.actions.base import ActionHandler
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.economy import buy_item, can_buy, can_sell, sell_item
from app.engine.rules.time import make_time_delta
from app.llm.schemas import PlayerActionType, PlayerIntent


class BuyActionHandler(ActionHandler):
    action_type = PlayerActionType.BUY

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        item_id, merchant_id = _parse_trade_target(intent.target_id)
        if item_id is None or merchant_id is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Buy action requires target_id formatted as item_id@merchant_id.",
            )
        result = can_buy(state, merchant_id, item_id)
        if not result.allowed:
            return ActionResult(success_level=SuccessLevel.FAILURE, reason=result.reason)
        return ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason=f"Bought {item_id} for {result.price}.",
            state_deltas=[*buy_item(state, merchant_id, item_id), make_time_delta(state, 5)],
            visible_facts=[f"trade:buy:{item_id}", f"price:{result.price}"],
        )


class SellActionHandler(ActionHandler):
    action_type = PlayerActionType.SELL

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        item_id, merchant_id = _parse_trade_target(intent.target_id)
        if item_id is None or merchant_id is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Sell action requires target_id formatted as item_id@merchant_id.",
            )
        result = can_sell(state, merchant_id, item_id)
        if not result.allowed:
            return ActionResult(success_level=SuccessLevel.FAILURE, reason=result.reason)
        return ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason=f"Sold {item_id} for {result.price}.",
            state_deltas=[*sell_item(state, merchant_id, item_id), make_time_delta(state, 5)],
            visible_facts=[f"trade:sell:{item_id}", f"price:{result.price}"],
        )


def _parse_trade_target(target_id: str | None) -> tuple[str | None, str | None]:
    if not target_id or "@" not in target_id:
        return None, None
    item_id, merchant_id = target_id.split("@", 1)
    if not item_id or not merchant_id:
        return None, None
    return item_id, merchant_id
