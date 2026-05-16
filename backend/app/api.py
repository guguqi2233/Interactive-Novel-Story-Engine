from pydantic import BaseModel, Field


class VisibleTimeResponse(BaseModel):
    day: int
    minutes_of_day: int
    time_of_day: str
    formatted: str


class VisibleLocationResponse(BaseModel):
    id: str
    name: str
    exits: dict[str, str] = Field(default_factory=dict)


class VisibleObjectResponse(BaseModel):
    id: str


class VisibleNPCResponse(BaseModel):
    id: str
    mood: str
    relationship_to_player: int


class KnownFactResponse(BaseModel):
    id: str
    text: str | None = None
    tags: list[str] = Field(default_factory=list)


class VisibleQuestResponse(BaseModel):
    id: str
    name: str
    status: str = "available"


class VisibleStateResponse(BaseModel):
    world_id: str
    turn: int
    time: VisibleTimeResponse
    location: VisibleLocationResponse
    inventory: list[VisibleObjectResponse] = Field(default_factory=list)
    visible_objects: list[VisibleObjectResponse] = Field(default_factory=list)
    visible_npcs: list[VisibleNPCResponse] = Field(default_factory=list)
    known_facts: list[KnownFactResponse] = Field(default_factory=list)
    quests: list[VisibleQuestResponse] = Field(default_factory=list)


class StartGameRequest(BaseModel):
    world_id: str | None = None


class StartGameResponse(BaseModel):
    session_id: str
    world_id: str
    visible_state: VisibleStateResponse
    turn: int


class GameInputRequest(BaseModel):
    session_id: str
    player_input: str = Field(min_length=1)


class GameInputResponse(BaseModel):
    narrative_text: str
    suggested_actions: list[str]
    visible_state: VisibleStateResponse
    turn: int


class GameStateResponse(BaseModel):
    session_id: str
    visible_state: VisibleStateResponse
    turn: int


class SaveSummaryResponse(BaseModel):
    save_id: str
    world_id: str
    turn: int
    created_at: str
    updated_at: str


class SaveListResponse(BaseModel):
    saves: list[SaveSummaryResponse] = Field(default_factory=list)


class SaveGameResponse(BaseModel):
    save_id: str
    session_id: str
    world_id: str
    turn: int


class LoadGameResponse(BaseModel):
    save_id: str
    session_id: str
    visible_state: VisibleStateResponse
    turn: int
