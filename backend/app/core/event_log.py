from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator

from app.compatibility.contracts import EVENTLOG_CONTRACT_VERSION
from app.core.state_delta import StateDelta


class EventLogError(ValueError):
    """Raised when an event log operation would break event history rules."""


class Event(BaseModel):
    event_id: str
    turn: int = Field(ge=0)
    event_type: str = "player_action"
    actor_id: str
    action_type: str
    result: str
    visible_to_player: bool
    target_id: str | None = None
    input_text: str | None = None
    state_deltas: list[StateDelta] = Field(default_factory=list)
    allow_empty_delta: bool = False
    visible_summary: str | None = None
    debug_summary: str | None = None
    narrative_text: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    contract_version: str = EVENTLOG_CONTRACT_VERSION

    @model_validator(mode="after")
    def validate_state_delta_presence(self) -> "Event":
        if not self.state_deltas and not self.allow_empty_delta:
            raise ValueError("Event must include state_deltas unless allow_empty_delta is true")
        if self.contract_version != EVENTLOG_CONTRACT_VERSION:
            raise ValueError(f"Unsupported Event contract_version: {self.contract_version}")
        if self.visible_to_player:
            visible_text = " ".join(
                value or ""
                for value in [self.visible_summary, self.narrative_text, self.input_text]
            ).lower()
            if any(secret_term in visible_text for secret_term in ["api_key", "authorization:", "raw env"]):
                raise ValueError("Player-visible events cannot contain secrets or raw env markers")
        return self


class EventLog:
    def __init__(self, events: list[Event] | None = None) -> None:
        self._events: list[Event] = []
        for event in events or []:
            self.append(event)

    def append(self, event: Event) -> None:
        if self._events and event.turn < self._events[-1].turn:
            raise EventLogError(
                f"Event turn cannot move backwards: latest={self._events[-1].turn}, new={event.turn}"
            )
        self._events.append(event)

    def list_events(self) -> list[Event]:
        return list(self._events)

    def get_events_since(self, turn: int) -> list[Event]:
        return [event for event in self._events if event.turn >= turn]

    def get_latest(self, n: int) -> list[Event]:
        if n < 0:
            raise EventLogError("Latest event count must be non-negative")
        if n == 0:
            return []
        return self._events[-n:]
