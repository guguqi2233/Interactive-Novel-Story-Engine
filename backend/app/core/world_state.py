from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class PlayerState(BaseModel):
    id: str = "player"
    location_id: str = "start"
    inventory: list[str] = Field(default_factory=list)
    health: int = 100
    stealth_modifier: int = 0


class NPCState(BaseModel):
    id: str
    location_id: str
    visible: bool = True
    hidden: bool = False
    discovered_by: list[str] = Field(default_factory=list)
    mood: str = "neutral"
    relationship_to_player: int = 0
    alertness: int = 0
    suspicion: int = 0
    knowledge: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)
    schedule: list["NPCScheduleEntry"] = Field(default_factory=list)
    current_activity: str | None = None


class NPCScheduleEntry(BaseModel):
    time_of_day: str
    location_id: str
    activity: str


class LockState(StrEnum):
    INTACT = "intact"
    SCRATCHED = "scratched"
    DAMAGED = "damaged"
    BROKEN = "broken"
    OPENED = "opened"


class WorldObjectState(BaseModel):
    id: str
    name: str | None = None
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
    locked: bool = False
    lock_difficulty: int = Field(default=0, ge=0)
    lock_state: LockState = LockState.INTACT

    @model_validator(mode="after")
    def validate_single_placement(self) -> "WorldObjectState":
        placements = [
            self.location_id is not None,
            self.owner_id is not None,
            self.container_id is not None,
        ]
        if sum(placements) > 1:
            raise ValueError("WorldObjectState cannot have multiple placements")
        return self


class LocationState(BaseModel):
    id: str
    name: str
    exits: dict[str, str] = Field(default_factory=dict)
    visible_objects: list[str] = Field(default_factory=list)
    cover_level: int = Field(default=0, ge=0)
    light_level: int = Field(default=5, ge=0)


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


class QuestVisibility(StrEnum):
    PUBLIC = "public"
    HIDDEN = "hidden"


class QuestStatus(StrEnum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestTriggerType(StrEnum):
    FACT_DISCOVERED = "fact_discovered"
    ITEM_ACQUIRED = "item_acquired"
    NPC_TALKED = "npc_talked"
    LOCATION_VISITED = "location_visited"


class QuestTriggerAction(StrEnum):
    ACTIVATE = "activate"
    ADVANCE = "advance"
    COMPLETE_OBJECTIVE = "complete_objective"


class QuestTrigger(BaseModel):
    type: QuestTriggerType
    id: str
    action: QuestTriggerAction = QuestTriggerAction.ACTIVATE
    objective_id: str | None = None
    next_stage: str | None = None


class QuestStage(BaseModel):
    id: str
    title: str
    description: str = ""
    objectives: list[str] = Field(default_factory=list)
    next_stages: list[str] = Field(default_factory=list)


class QuestState(BaseModel):
    id: str
    title: str
    description: str = ""
    initial_stage: str
    current_stage: str
    stages: dict[str, QuestStage] = Field(default_factory=dict)
    visibility: QuestVisibility = QuestVisibility.HIDDEN
    status: QuestStatus = QuestStatus.INACTIVE
    known_to_player: bool = False
    completed_objectives: set[str] = Field(default_factory=set)
    triggers: list[QuestTrigger] = Field(default_factory=list)


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
    quests: dict[str, QuestState] = Field(default_factory=dict)
    delayed_consequences: list[dict[str, Any]] = Field(default_factory=list)
