from datetime import datetime, timezone

from pydantic import BaseModel, Field


class SaveGame(BaseModel):
    save_id: str
    state_json: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StoredEvent(BaseModel):
    event_id: str
    save_id: str
    turn: int
    event_json: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

