from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.state_delta import StateDelta


class SuccessLevel(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    INVALID = "invalid"


class ActionResult(BaseModel):
    success_level: SuccessLevel
    reason: str
    state_deltas: list[StateDelta] = Field(default_factory=list)
    visible_facts: list[str] = Field(default_factory=list)
    hidden_facts: list[str] = Field(default_factory=list)
