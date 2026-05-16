from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class PlayerActionType(StrEnum):
    OBSERVE = "observe"
    MOVE = "move"
    TALK = "talk"
    USE_ITEM = "use_item"
    WAIT = "wait"
    UNKNOWN = "unknown"


class PlayerIntent(BaseModel):
    action_type: PlayerActionType
    raw_text: str
    confidence: float = Field(ge=0.0, le=1.0)
    requires_clarification: bool
    target_id: str | None = None
    minutes: int | None = Field(default=None, ge=0)
    clarification_question: str | None = None

    @model_validator(mode="after")
    def validate_clarification_question(self) -> "PlayerIntent":
        if self.requires_clarification and not self.clarification_question:
            raise ValueError("clarification_question is required when requires_clarification is true")
        return self


class NarrativeResult(BaseModel):
    text: str
    suggested_actions: list[str] = Field(default_factory=list)
    short_summary: str


class MemorySummary(BaseModel):
    summary: str
    important_facts: list[str] = Field(default_factory=list)
    open_threads: list[str] = Field(default_factory=list)
    npc_relationship_changes: list[str] = Field(default_factory=list)
