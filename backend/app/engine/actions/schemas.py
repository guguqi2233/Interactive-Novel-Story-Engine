from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.core.state_delta import StateDelta


class SuccessLevel(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    INVALID = "invalid"


class ActionResult(BaseModel):
    success_level: SuccessLevel
    reason: str
    state_delta: StateDelta | None = Field(default=None, description="Deprecated; use state_deltas.")
    state_deltas: list[StateDelta] = Field(default_factory=list)
    visible_facts: list[str] = Field(default_factory=list)
    hidden_facts: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def sync_legacy_state_delta(self) -> "ActionResult":
        if self.state_delta is None and self.state_deltas:
            self.state_delta = self.state_deltas[0]
        if self.state_delta is not None and not self.state_deltas:
            self.state_deltas = [self.state_delta]
        return self
