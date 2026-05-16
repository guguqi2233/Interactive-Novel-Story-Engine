from pydantic import BaseModel, Field


class VisibleStateResponse(BaseModel):
    world_id: str
    location_id: str
    location_name: str
    visible_facts: list[str] = Field(default_factory=list)


class StartGameResponse(BaseModel):
    session_id: str
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
