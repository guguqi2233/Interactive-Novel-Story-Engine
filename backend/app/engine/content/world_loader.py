from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

from app.core.world_state import GameState, LocationState, NPCState, PlayerState, WorldObjectState


class WorldLoaderError(ValueError):
    """Raised when a content pack is missing or internally inconsistent."""


class WorldManifest(BaseModel):
    world_id: str
    name: str
    version: str = "0.1.0"
    start_location_id: str
    description: str = ""


class LocationDef(BaseModel):
    id: str
    name: str
    description: str
    exits: dict[str, str] = Field(default_factory=dict)
    visible_objects: list[str] = Field(default_factory=list)


class NPCDef(BaseModel):
    id: str
    name: str
    location_id: str
    personality: str
    knowledge: list[str] = Field(default_factory=list)


class ItemDef(BaseModel):
    id: str
    name: str
    description: str = ""
    location_id: str | None = None
    owner_id: str | None = None
    visible: bool = True
    hidden: bool = False
    discovered_by: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_placement(self) -> "ItemDef":
        if self.location_id is None and self.owner_id is None:
            raise ValueError("ItemDef requires location_id or owner_id")
        return self


class QuestDef(BaseModel):
    id: str
    name: str
    description: str = ""
    starts_at: str | None = None


class WorldPack(BaseModel):
    manifest: WorldManifest
    locations: list[LocationDef]
    npcs: list[NPCDef]
    items: list[ItemDef] = Field(default_factory=list)
    quests: list[QuestDef] = Field(default_factory=list)

    def to_game_state(self) -> GameState:
        return GameState(
            world_id=self.manifest.world_id,
            player=PlayerState(location_id=self.manifest.start_location_id),
            locations={
                location.id: LocationState(
                    id=location.id,
                    name=location.name,
                    exits=location.exits,
                    visible_objects=location.visible_objects,
                )
                for location in self.locations
            },
            objects={
                item.id: WorldObjectState(
                    id=item.id,
                    location_id=item.location_id or item.owner_id or "",
                    visible=item.visible,
                    hidden=item.hidden,
                    discovered_by=item.discovered_by,
                )
                for item in self.items
            },
            npcs={
                npc.id: NPCState(
                    id=npc.id,
                    location_id=npc.location_id,
                    knowledge=npc.knowledge,
                )
                for npc in self.npcs
            },
            npc_knowledge={npc.id: set(npc.knowledge) for npc in self.npcs},
        )


class WorldLoader:
    def __init__(self, worlds_root: str | Path = "worlds") -> None:
        self.worlds_root = Path(worlds_root)

    def load(self, world_id: str) -> WorldPack:
        world_path = self.worlds_root / world_id
        if not world_path.exists():
            raise WorldLoaderError(f"World pack not found: {world_id}")

        try:
            pack = WorldPack(
                manifest=WorldManifest.model_validate(_read_yaml_file(world_path / "manifest.yaml")),
                locations=[
                    LocationDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "locations.yaml", "locations")
                ],
                npcs=[
                    NPCDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "npcs.yaml", "npcs")
                ],
                items=[
                    ItemDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "items.yaml", "items", required=False)
                ],
                quests=[
                    QuestDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "quests.yaml", "quests", required=False)
                ],
            )
        except ValidationError as exc:
            raise WorldLoaderError(f"World pack schema validation failed: {exc}") from exc

        self._validate_references(pack)
        return pack

    def _validate_references(self, pack: WorldPack) -> None:
        location_ids = {location.id for location in pack.locations}
        npc_ids = {npc.id for npc in pack.npcs}

        if pack.manifest.start_location_id not in location_ids:
            raise WorldLoaderError(
                f"Manifest start_location_id does not exist: {pack.manifest.start_location_id}"
            )

        for location in pack.locations:
            for direction, target_location_id in location.exits.items():
                if target_location_id not in location_ids:
                    raise WorldLoaderError(
                        f"Location {location.id} exit {direction} points to missing location: "
                        f"{target_location_id}"
                    )

        for npc in pack.npcs:
            if npc.location_id not in location_ids:
                raise WorldLoaderError(
                    f"NPC {npc.id} references missing location_id: {npc.location_id}"
                )

        for item in pack.items:
            has_valid_location = item.location_id in location_ids if item.location_id else False
            has_valid_owner = item.owner_id in npc_ids or item.owner_id == "player" if item.owner_id else False
            if not has_valid_location and not has_valid_owner:
                raise WorldLoaderError(
                    f"Item {item.id} must reference an existing location_id or owner_id"
                )


def _read_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise WorldLoaderError(f"Missing content file: {path.name}")
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise WorldLoaderError(f"Expected YAML mapping in file: {path.name}")
    return data


def _read_yaml_list(path: Path, key: str, required: bool = True) -> list[dict[str, Any]]:
    if not path.exists():
        if required:
            raise WorldLoaderError(f"Missing content file: {path.name}")
        return []
    data = _read_yaml_file(path)
    raw_items = data.get(key, [])
    if not isinstance(raw_items, list):
        raise WorldLoaderError(f"Expected list key '{key}' in file: {path.name}")
    return [_ensure_mapping(item, path.name) for item in raw_items]


def _ensure_mapping(item: Any, filename: str) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise WorldLoaderError(f"Expected mapping items in file: {filename}")
    return item
