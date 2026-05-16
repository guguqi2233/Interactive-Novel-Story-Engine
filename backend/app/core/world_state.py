from enum import StrEnum

from pydantic import BaseModel, Field


class PlayerState(BaseModel):
    id: str = "player"
    location_id: str = "start"
    inventory: list[str] = Field(default_factory=list)
    health: int = 100


class NPCState(BaseModel):
    id: str
    location_id: str
    mood: str = "neutral"
    relationship_to_player: int = 0
    suspicion: int = 0
    knowledge: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)


class WorldObjectState(BaseModel):
    id: str
    location_id: str
    visible: bool = True
    hidden: bool = False
    discovered_by: list[str] = Field(default_factory=list)


class LocationState(BaseModel):
    id: str
    name: str
    exits: dict[str, str] = Field(default_factory=dict)
    visible_objects: list[str] = Field(default_factory=list)


class GameTime(BaseModel):
    day: int = 1
    minutes_of_day: int = Field(default=8 * 60, ge=0, lt=24 * 60)


class FactVisibility(StrEnum):
    PUBLIC = "public"
    HIDDEN = "hidden"
    DISCOVERABLE = "discoverable"


class FactState(BaseModel):
    id: str
    text: str | None = None
    visibility: FactVisibility = FactVisibility.HIDDEN
    public: bool = False
    secret: bool = False
    known_by: set[str] = Field(default_factory=set)
    tags: list[str] = Field(default_factory=list)


class GameState(BaseModel):
    world_id: str
    turn: int = 0
    current_time: GameTime = Field(default_factory=GameTime)
    player: PlayerState = Field(default_factory=PlayerState)
    locations: dict[str, LocationState] = Field(default_factory=dict)
    objects: dict[str, WorldObjectState] = Field(default_factory=dict)
    npcs: dict[str, NPCState] = Field(default_factory=dict)
    flags: dict[str, bool | int | float | str] = Field(default_factory=dict)
    facts: dict[str, FactState] = Field(default_factory=dict)
    player_visible_facts: set[str] = Field(default_factory=set)
    npc_knowledge: dict[str, set[str]] = Field(default_factory=dict)
