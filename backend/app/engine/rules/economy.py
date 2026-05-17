from enum import StrEnum

from pydantic import BaseModel

from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, NPCState, WorldObjectState
from app.engine.rules.factions import reputation_band


class TradeDirection(StrEnum):
    BUY = "buy"
    SELL = "sell"


class TradeRuleResult(BaseModel):
    allowed: bool
    reason: str
    price: int = 0


class EconomyRuleError(ValueError):
    """Raised when economy rules cannot resolve cleanly."""


def get_item_price(
    state: GameState,
    item_id: str,
    merchant_id: str | None = None,
    direction: TradeDirection | str = TradeDirection.BUY,
) -> int:
    item = _require_item(state, item_id)
    merchant = _require_merchant(state, merchant_id) if merchant_id else None
    trade_direction = TradeDirection(direction)
    modifier = _merchant_modifier(merchant, trade_direction)
    modifier *= _reputation_price_modifier(state, merchant, trade_direction)
    return max(0, round(item.base_price * modifier))


def get_shop_inventory(state: GameState, merchant_id: str) -> list[WorldObjectState]:
    merchant = _require_merchant(state, merchant_id)
    return [
        item
        for item_id in merchant.shop_inventory
        if (item := state.objects.get(item_id)) is not None
        and item.visible
        and not item.hidden
        and item.tradeable
    ]


def can_buy(state: GameState, merchant_id: str, item_id: str) -> TradeRuleResult:
    merchant = _require_merchant(state, merchant_id)
    item = state.objects.get(item_id)
    if item is None:
        return TradeRuleResult(allowed=False, reason="Item does not exist.")
    if item_id not in merchant.shop_inventory:
        return TradeRuleResult(allowed=False, reason="Item is not in shop inventory.")
    if item.hidden:
        return TradeRuleResult(allowed=False, reason="Item is hidden.")
    if not item.tradeable:
        return TradeRuleResult(allowed=False, reason="Item is not tradeable.")
    price = get_item_price(state, item_id, merchant_id, TradeDirection.BUY)
    if state.player.currency < price:
        return TradeRuleResult(allowed=False, reason="Not enough currency.", price=price)
    return TradeRuleResult(allowed=True, reason="Item can be bought.", price=price)


def buy_item(state: GameState, merchant_id: str, item_id: str) -> list[StateDelta]:
    result = can_buy(state, merchant_id, item_id)
    if not result.allowed:
        raise EconomyRuleError(result.reason)
    return [
        StateDelta(
            operation=StateDeltaOperation.INC,
            path="player.currency",
            value=-result.price,
            reason="Player paid merchant.",
            metadata={"source": "trade", "trade_type": "buy", "merchant_id": merchant_id, "item_id": item_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.REMOVE,
            path=f"npcs.{merchant_id}.shop_inventory",
            value=item_id,
            reason="Item left shop inventory.",
            metadata={"source": "trade", "trade_type": "buy", "merchant_id": merchant_id, "item_id": item_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.owner_id",
            value="player",
            reason="Player bought item.",
            metadata={"source": "trade", "trade_type": "buy", "merchant_id": merchant_id, "item_id": item_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.location_id",
            value=None,
            reason="Bought item no longer belongs to a location.",
            metadata={"source": "trade", "trade_type": "buy", "merchant_id": merchant_id, "item_id": item_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.container_id",
            value=None,
            reason="Bought item no longer belongs to a container.",
            metadata={"source": "trade", "trade_type": "buy", "merchant_id": merchant_id, "item_id": item_id},
        ),
    ]


def can_sell(state: GameState, merchant_id: str, item_id: str) -> TradeRuleResult:
    _require_merchant(state, merchant_id)
    item = state.objects.get(item_id)
    if item is None:
        return TradeRuleResult(allowed=False, reason="Item does not exist.")
    if item.owner_id != state.player.id:
        return TradeRuleResult(allowed=False, reason="Player does not own item.")
    if not item.tradeable:
        return TradeRuleResult(allowed=False, reason="Item is not tradeable.")
    if "stolen" in item.tags:
        return TradeRuleResult(allowed=False, reason="Merchant refuses stolen item.")
    price = get_item_price(state, item_id, merchant_id, TradeDirection.SELL)
    return TradeRuleResult(allowed=True, reason="Item can be sold.", price=price)


def sell_item(state: GameState, merchant_id: str, item_id: str) -> list[StateDelta]:
    result = can_sell(state, merchant_id, item_id)
    if not result.allowed:
        raise EconomyRuleError(result.reason)
    return [
        StateDelta(
            operation=StateDeltaOperation.INC,
            path="player.currency",
            value=result.price,
            reason="Merchant paid player.",
            metadata={"source": "trade", "trade_type": "sell", "merchant_id": merchant_id, "item_id": item_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.owner_id",
            value=merchant_id,
            reason="Player sold item to merchant.",
            metadata={"source": "trade", "trade_type": "sell", "merchant_id": merchant_id, "item_id": item_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.location_id",
            value=None,
            reason="Sold item no longer belongs to a location.",
            metadata={"source": "trade", "trade_type": "sell", "merchant_id": merchant_id, "item_id": item_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.container_id",
            value=None,
            reason="Sold item no longer belongs to a container.",
            metadata={"source": "trade", "trade_type": "sell", "merchant_id": merchant_id, "item_id": item_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"npcs.{merchant_id}.shop_inventory",
            value=item_id,
            reason="Sold item entered shop inventory.",
            metadata={"source": "trade", "trade_type": "sell", "merchant_id": merchant_id, "item_id": item_id},
        ),
    ]


def _require_item(state: GameState, item_id: str) -> WorldObjectState:
    item = state.objects.get(item_id)
    if item is None:
        raise EconomyRuleError(f"Unknown item_id: {item_id}")
    return item


def _require_merchant(state: GameState, merchant_id: str | None) -> NPCState:
    if not merchant_id:
        raise EconomyRuleError("Merchant id is required.")
    merchant = state.npcs.get(merchant_id)
    if merchant is None:
        raise EconomyRuleError(f"Unknown merchant_id: {merchant_id}")
    if not merchant.merchant:
        raise EconomyRuleError(f"NPC is not a merchant: {merchant_id}")
    return merchant


def _merchant_modifier(merchant: NPCState | None, direction: TradeDirection) -> float:
    if merchant is None:
        return 1.0
    if direction == TradeDirection.BUY:
        return merchant.buy_price_modifier
    return merchant.sell_price_modifier


def _reputation_price_modifier(state: GameState, merchant: NPCState | None, direction: TradeDirection) -> float:
    if merchant is None or merchant.faction_id is None:
        return 1.0
    faction = state.factions.get(merchant.faction_id)
    if faction is None:
        return 1.0
    band = reputation_band(faction.reputation.value)
    if direction == TradeDirection.BUY:
        return {
            "hostile": 1.5,
            "suspicious": 1.2,
            "neutral": 1.0,
            "friendly": 0.9,
            "trusted": 0.8,
        }[band.value]
    return {
        "hostile": 0.5,
        "suspicious": 0.8,
        "neutral": 1.0,
        "friendly": 1.1,
        "trusted": 1.2,
    }[band.value]
