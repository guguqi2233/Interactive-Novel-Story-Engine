from pydantic import BaseModel

from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import GameState, WorldObjectState


class InventoryRuleResult(BaseModel):
    allowed: bool
    reason: str


def has_item(state: GameState, actor_id: str, item_id: str) -> bool:
    item = state.objects.get(item_id)
    if item is not None:
        return item.owner_id == actor_id
    if actor_id == state.player.id:
        return item_id in state.player.inventory
    return False


def get_inventory(state: GameState, actor_id: str = "player") -> list[WorldObjectState]:
    return [
        item
        for item in state.objects.values()
        if item.owner_id == actor_id
    ]


def can_pick_up(state: GameState, actor_id: str, item_id: str) -> InventoryRuleResult:
    if actor_id != state.player.id:
        return InventoryRuleResult(allowed=False, reason="Only the player can pick up items in v0.3.3.")

    item = state.objects.get(item_id)
    if item is None:
        return InventoryRuleResult(allowed=False, reason="Item does not exist.")
    if _placement_count(item) > 1:
        return InventoryRuleResult(allowed=False, reason="Item has conflicting placement state.")
    if item.owner_id == actor_id:
        return InventoryRuleResult(allowed=False, reason="Player already has item.")
    if not item.portable:
        return InventoryRuleResult(allowed=False, reason="Item is not portable.")
    if item.location_id != state.player.location_id:
        return InventoryRuleResult(allowed=False, reason="Item is not in the current location.")
    if item.hidden and actor_id not in item.discovered_by:
        return InventoryRuleResult(allowed=False, reason="Item has not been discovered.")
    return InventoryRuleResult(allowed=True, reason="Item can be picked up.")


def pick_up_item(state: GameState, actor_id: str, item_id: str) -> list[StateDelta]:
    result = can_pick_up(state, actor_id, item_id)
    if not result.allowed:
        raise ValueError(result.reason)
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.location_id",
            value=None,
            reason="Picked up item no longer belongs to a location.",
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.container_id",
            value=None,
            reason="Picked up item no longer belongs to a container.",
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.owner_id",
            value=actor_id,
            reason="Player picked up item.",
        ),
    ]


def drop_item(state: GameState, actor_id: str, item_id: str) -> list[StateDelta]:
    if not has_item(state, actor_id, item_id):
        raise ValueError("Actor does not have item.")
    if actor_id != state.player.id:
        raise ValueError("Only the player can drop items in v0.3.3.")
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.owner_id",
            value=None,
            reason="Dropped item no longer belongs to player.",
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.container_id",
            value=None,
            reason="Dropped item no longer belongs to a container.",
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"objects.{item_id}.location_id",
            value=state.player.location_id,
            reason="Player dropped item at current location.",
        ),
    ]


def item_is_accessible(state: GameState, actor_id: str, item_id: str) -> bool:
    if has_item(state, actor_id, item_id):
        return True
    item = state.objects.get(item_id)
    if item is None:
        return False
    if item.location_id != state.player.location_id:
        return False
    if item.hidden and actor_id not in item.discovered_by:
        return False
    return item.visible


def _placement_count(item: WorldObjectState) -> int:
    return sum(
        [
            item.location_id is not None,
            item.owner_id is not None,
            item.container_id is not None,
        ]
    )
