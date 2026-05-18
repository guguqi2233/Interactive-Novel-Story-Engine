from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport


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


class MerchantEconomyNode(BaseModel):
    npc_id: str
    name: str
    hidden: bool = False
    merchant: bool = False
    shop_inventory: list[str] = Field(default_factory=list)
    buy_price_modifier: float = 1.0
    sell_price_modifier: float = 0.5


class ItemEconomyAuthoring(BaseModel):
    world_id: str
    items: list[ItemEconomyItem] = Field(default_factory=list)
    merchants: list[MerchantEconomyNode] = Field(default_factory=list)


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
    items = [ItemEconomyItem.model_validate(item) for item in items_data]
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
    return ItemEconomyAuthoring(world_id=world_id, items=items, merchants=merchants)


def item_economy_to_yaml(
    world_id: str,
    graph: ItemEconomyAuthoring,
    service: ContentAuthoringService,
) -> dict[str, str]:
    if graph.world_id != world_id:
        raise ItemEconomyAuthoringError(
            f"Graph world_id does not match route world_id: {graph.world_id} != {world_id}"
        )

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
    yaml_contents = item_economy_to_yaml(world_id, graph, service)
    validation = service.validate_drafts(world_id, yaml_contents)
    return ItemEconomyAuthoringPreview(
        graph=graph,
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
) -> ValidationReport:
    yaml_contents = item_economy_to_yaml(world_id, graph, service)
    return service.write_files(world_id, yaml_contents)


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
        if value is not None and value != []
    }
