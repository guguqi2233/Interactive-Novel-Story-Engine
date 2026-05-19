from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity


class ItemEconomyAuthoringError(ValueError):
    """Raised when item/economy authoring input is invalid."""


class ItemEconomyItem(BaseModel):
    id: str
    name: str
    description: str = ""
    location_id: str | None = None
    owner_id: str | None = None
    container_id: str | None = None
    portable: bool = False
    visible: bool = True
    hidden: bool = False
    discoverable: bool = False
    discovered_by: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    base_price: int = 0
    tradeable: bool = True
    rarity: str = "common"
    locked: bool = False
    lock_difficulty: int = 0
    lock_state: str = "intact"
    stolen_item_policy: str = "refuse_stolen"


class MerchantEconomyNode(BaseModel):
    npc_id: str
    name: str
    hidden: bool = False
    merchant: bool = False
    shop_inventory: list[str] = Field(default_factory=list)
    buy_price_modifier: float = 1.0
    sell_price_modifier: float = 0.5


class ShopInventoryEdge(BaseModel):
    id: str
    merchant_id: str
    item_id: str
    buy_price: int = 0
    sell_price: int = 0
    player_visible: bool = True


class QuestRewardLink(BaseModel):
    id: str
    quest_id: str
    item_id: str
    reward_index: int = 0


class EconomyBalanceWarning(BaseModel):
    code: str
    path: str
    message: str
    ref_id: str | None = None


class ItemEconomyAuthoring(BaseModel):
    world_id: str
    items: list[ItemEconomyItem] = Field(default_factory=list)
    merchants: list[MerchantEconomyNode] = Field(default_factory=list)
    item_nodes: list[ItemEconomyItem] = Field(default_factory=list)
    merchant_nodes: list[MerchantEconomyNode] = Field(default_factory=list)
    shop_inventory_edges: list[ShopInventoryEdge] = Field(default_factory=list)
    price_modifier_fields: dict[str, dict[str, float]] = Field(default_factory=dict)
    stolen_item_policy: dict[str, str] = Field(default_factory=dict)
    quest_reward_links: list[QuestRewardLink] = Field(default_factory=list)
    balance_warnings: list[EconomyBalanceWarning] = Field(default_factory=list)

    def normalized(self) -> "ItemEconomyAuthoring":
        items = self.items or self.item_nodes
        merchants = self.merchants or self.merchant_nodes
        graph = self.model_copy(
            update={
                "items": items,
                "merchants": merchants,
                "item_nodes": items,
                "merchant_nodes": merchants,
            }
        )
        return _with_derived_fields(graph)


class ItemEconomyAuthoringPreview(BaseModel):
    graph: ItemEconomyAuthoring
    yaml_contents: dict[str, str]
    validation: ValidationReport
    confirmation_required: bool = False


def parse_item_economy_authoring(
    world_id: str,
    service: ContentAuthoringService,
) -> ItemEconomyAuthoring:
    items_data = _read_list_file(service, world_id, "items.yaml", "items")
    npc_data = _read_list_file(service, world_id, "npcs.yaml", "npcs")
    quests_data = _read_list_file(service, world_id, "quests.yaml", "quests")
    items = [_item_from_yaml(item) for item in items_data]
    merchants = [
        MerchantEconomyNode(
            npc_id=str(npc.get("id", "")),
            name=str(npc.get("name", npc.get("id", ""))),
            hidden=bool(npc.get("hidden", False)),
            merchant=bool(npc.get("merchant", False)),
            shop_inventory=[str(item_id) for item_id in npc.get("shop_inventory", [])],
            buy_price_modifier=float(npc.get("buy_price_modifier", 1.0)),
            sell_price_modifier=float(npc.get("sell_price_modifier", 0.5)),
        )
        for npc in npc_data
        if bool(npc.get("merchant", False)) or npc.get("shop_inventory")
    ]
    return _with_derived_fields(ItemEconomyAuthoring(world_id=world_id, items=items, merchants=merchants), quests_data)


def item_economy_to_yaml(
    world_id: str,
    graph: ItemEconomyAuthoring,
    service: ContentAuthoringService,
) -> dict[str, str]:
    if graph.world_id != world_id:
        raise ItemEconomyAuthoringError(
            f"Graph world_id does not match route world_id: {graph.world_id} != {world_id}"
        )

    graph = graph.normalized()
    npc_data = _read_list_file(service, world_id, "npcs.yaml", "npcs")
    merchants_by_id = {merchant.npc_id: merchant for merchant in graph.merchants}
    updated_npcs: list[dict[str, Any]] = []
    for npc in npc_data:
        npc_id = str(npc.get("id", ""))
        updated = dict(npc)
        if npc_id in merchants_by_id:
            merchant = merchants_by_id[npc_id]
            updated["merchant"] = merchant.merchant
            updated["shop_inventory"] = merchant.shop_inventory
            updated["buy_price_modifier"] = merchant.buy_price_modifier
            updated["sell_price_modifier"] = merchant.sell_price_modifier
        updated_npcs.append(_without_empty_optional_lists(updated))

    items_yaml = yaml.safe_dump(
        {"items": [_without_empty_optional_lists(item.model_dump(mode="json")) for item in graph.items]},
        sort_keys=False,
        allow_unicode=True,
    )
    npcs_yaml = yaml.safe_dump(
        {"npcs": updated_npcs},
        sort_keys=False,
        allow_unicode=True,
    )
    return {"items.yaml": items_yaml, "npcs.yaml": npcs_yaml}


def preview_item_economy_authoring(
    world_id: str,
    graph: ItemEconomyAuthoring,
    service: ContentAuthoringService,
) -> ItemEconomyAuthoringPreview:
    graph = graph.normalized()
    yaml_contents = item_economy_to_yaml(world_id, graph, service)
    validation = service.validate_drafts(world_id, yaml_contents)
    _add_item_economy_authoring_validation(validation, graph)
    return ItemEconomyAuthoringPreview(
        graph=_with_derived_fields(graph),
        yaml_contents=yaml_contents,
        validation=validation,
        confirmation_required=validation.ok and bool(validation.warnings),
    )


def validate_item_economy_authoring(
    world_id: str,
    graph: ItemEconomyAuthoring,
    service: ContentAuthoringService,
) -> ValidationReport:
    return preview_item_economy_authoring(world_id, graph, service).validation


def save_item_economy_authoring(
    world_id: str,
    graph: ItemEconomyAuthoring,
    service: ContentAuthoringService,
    *,
    confirm_warnings: bool = False,
) -> ValidationReport:
    graph = graph.normalized()
    yaml_contents = item_economy_to_yaml(world_id, graph, service)
    validation = service.validate_drafts(world_id, yaml_contents)
    _add_item_economy_authoring_validation(validation, graph)
    if not validation.ok or (validation.warnings and not confirm_warnings):
        return validation
    return service.write_files(world_id, yaml_contents, confirm_warnings=confirm_warnings)


def balance_check_item_economy_authoring(
    world_id: str,
    graph: ItemEconomyAuthoring,
    service: ContentAuthoringService,
) -> ItemEconomyAuthoringPreview:
    return preview_item_economy_authoring(world_id, graph, service)


def _item_from_yaml(item: dict[str, Any]) -> ItemEconomyItem:
    tags = [str(tag) for tag in item.get("tags", []) if isinstance(tag, str)]
    policy = str(item.get("stolen_item_policy") or ("refuse_stolen" if "stolen" in tags else "refuse_stolen"))
    return ItemEconomyItem.model_validate({**item, "stolen_item_policy": policy})


def _with_derived_fields(
    graph: ItemEconomyAuthoring,
    quests_data: list[dict[str, Any]] | None = None,
) -> ItemEconomyAuthoring:
    items = graph.items or graph.item_nodes
    merchants = graph.merchants or graph.merchant_nodes
    item_by_id = {item.id: item for item in items}
    edges = [
        ShopInventoryEdge(
            id=f"{merchant.npc_id}:{item_id}",
            merchant_id=merchant.npc_id,
            item_id=item_id,
            buy_price=_preview_price(item_by_id.get(item_id), merchant.buy_price_modifier),
            sell_price=_preview_price(item_by_id.get(item_id), merchant.sell_price_modifier),
            player_visible=_is_player_visible_shop_item(item_by_id.get(item_id)),
        )
        for merchant in merchants
        for item_id in merchant.shop_inventory
    ]
    price_fields = {
        merchant.npc_id: {
            "buy_price_modifier": merchant.buy_price_modifier,
            "sell_price_modifier": merchant.sell_price_modifier,
        }
        for merchant in merchants
    }
    stolen_policy = {item.id: item.stolen_item_policy for item in items if "stolen" in item.tags or item.stolen_item_policy}
    reward_links = _derive_quest_reward_links(quests_data or [], item_by_id)
    graph = graph.model_copy(
        update={
            "items": items,
            "merchants": merchants,
            "item_nodes": items,
            "merchant_nodes": merchants,
            "shop_inventory_edges": edges,
            "price_modifier_fields": price_fields,
            "stolen_item_policy": stolen_policy,
            "quest_reward_links": reward_links if quests_data is not None else graph.quest_reward_links,
        }
    )
    return graph.model_copy(update={"balance_warnings": _economy_balance_warnings(graph)})


def _derive_quest_reward_links(
    quests_data: list[dict[str, Any]],
    item_by_id: dict[str, ItemEconomyItem],
) -> list[QuestRewardLink]:
    links: list[QuestRewardLink] = []
    for quest in quests_data:
        quest_id = str(quest.get("id", ""))
        rewards = quest.get("rewards", [])
        if not isinstance(rewards, list):
            continue
        for index, reward in enumerate(rewards):
            item_id = _reward_item_id(reward)
            if item_id and item_id in item_by_id:
                links.append(QuestRewardLink(id=f"{quest_id}:{index}:{item_id}", quest_id=quest_id, item_id=item_id, reward_index=index))
    return links


def _reward_item_id(reward: Any) -> str | None:
    if isinstance(reward, str):
        return reward
    if isinstance(reward, dict):
        value = reward.get("item_id") or reward.get("id")
        return str(value) if value else None
    return None


def _preview_price(item: ItemEconomyItem | None, modifier: float) -> int:
    if item is None:
        return 0
    return max(0, round(item.base_price * modifier))


def _is_player_visible_shop_item(item: ItemEconomyItem | None) -> bool:
    return bool(item and item.visible and not item.hidden and item.tradeable)


def _add_item_economy_authoring_validation(report: ValidationReport, graph: ItemEconomyAuthoring) -> None:
    seen: set[str] = set()
    for item in graph.items:
        if item.id in seen:
            report.add(ValidationSeverity.ERROR, f"items.yaml.{item.id}", "Item id must be unique.", code="item_duplicate_id", ref_id=item.id)
        seen.add(item.id)
        if item.base_price < 0:
            report.add(ValidationSeverity.ERROR, f"items.yaml.{item.id}.base_price", "Item base_price must be non-negative.", code="item_negative_base_price", ref_id=item.id)
        placements = [value for value in (item.location_id, item.owner_id, item.container_id) if value]
        if len(placements) > 1:
            report.add(ValidationSeverity.ERROR, f"items.yaml.{item.id}", "Item cannot have multiple ownership/location placements.", code="item_conflicting_ownership", ref_id=item.id)
        if item.tradeable not in {True, False}:
            report.add(ValidationSeverity.ERROR, f"items.yaml.{item.id}.tradeable", "Item tradeable policy must be boolean.", code="item_invalid_tradeable_policy", ref_id=item.id)
        if item.stolen_item_policy not in {"refuse_stolen", "allow_with_risk", "quest_only"}:
            report.add(ValidationSeverity.ERROR, f"items.yaml.{item.id}.stolen_item_policy", "Stolen item policy is not supported.", code="item_invalid_stolen_policy", ref_id=item.id)

    item_by_id = {item.id: item for item in graph.items}
    for merchant in graph.merchants:
        for item_id in merchant.shop_inventory:
            item = item_by_id.get(item_id)
            if item is None:
                report.add(ValidationSeverity.ERROR, f"npcs.yaml.{merchant.npc_id}.shop_inventory", "Merchant shop inventory references a missing item.", code="npc_shop_inventory_missing_item", ref_id=item_id)
                continue
            if not _is_player_visible_shop_item(item):
                report.add(ValidationSeverity.ERROR, f"npcs.yaml.{merchant.npc_id}.shop_inventory", "Hidden or non-player-visible item cannot enter player shop inventory.", code="hidden_item_in_player_shop", ref_id=item_id)

    for warning in _economy_balance_warnings(graph):
        report.add(ValidationSeverity.WARNING, warning.path, warning.message, code=warning.code, ref_id=warning.ref_id)


def _economy_balance_warnings(graph: ItemEconomyAuthoring) -> list[EconomyBalanceWarning]:
    warnings: list[EconomyBalanceWarning] = []
    for merchant in graph.merchants:
        if merchant.sell_price_modifier > merchant.buy_price_modifier:
            warnings.append(EconomyBalanceWarning(code="economy_arbitrage_risk", path=f"npcs.yaml.{merchant.npc_id}.sell_price_modifier", message="Merchant sell modifier exceeds buy modifier and may allow arbitrage.", ref_id=merchant.npc_id))
        if merchant.buy_price_modifier < 0 or merchant.sell_price_modifier < 0:
            warnings.append(EconomyBalanceWarning(code="economy_negative_price_modifier", path=f"npcs.yaml.{merchant.npc_id}", message="Merchant price modifiers should not be negative.", ref_id=merchant.npc_id))
    for item in graph.items:
        if item.tradeable and item.base_price == 0:
            warnings.append(EconomyBalanceWarning(code="economy_zero_price_tradeable", path=f"items.yaml.{item.id}.base_price", message="Tradeable item has zero base_price.", ref_id=item.id))
        if item.tradeable and "stolen" in item.tags and item.stolen_item_policy == "refuse_stolen":
            warnings.append(EconomyBalanceWarning(code="economy_stolen_item_default_policy", path=f"items.yaml.{item.id}.tags", message="Stolen tradeable item relies on the default refusal policy.", ref_id=item.id))
    return warnings


def _read_list_file(
    service: ContentAuthoringService,
    world_id: str,
    file_name: str,
    root_key: str,
) -> list[dict[str, Any]]:
    try:
        content = service.read_file(world_id, file_name)
    except Exception as exc:
        raise ItemEconomyAuthoringError(str(exc)) from exc
    data = yaml.safe_load(content) or {}
    if not isinstance(data, dict):
        raise ItemEconomyAuthoringError(f"Expected YAML mapping in {file_name}")
    raw_items = data.get(root_key, [])
    if not isinstance(raw_items, list):
        raise ItemEconomyAuthoringError(f"Expected list key {root_key} in {file_name}")
    return [dict(item) for item in raw_items if isinstance(item, dict)]


def _without_empty_optional_lists(data: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if value is not None and value != [] and (key != "stolen_item_policy" or value != "refuse_stolen")
    }
