from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, TypeAdapter, field_validator

from app.compatibility.contracts import STATEDELTA_CONTRACT_VERSION
from app.core.world_state import GameState


class StateDeltaError(ValueError):
    """Raised when a state delta cannot be applied safely."""


class StateDeltaOperation(StrEnum):
    SET = "set"
    INC = "inc"
    ADD = "add"
    REMOVE = "remove"


class StateDelta(BaseModel):
    operation: StateDeltaOperation
    path: str
    value: Any = None
    expected_old_value: Any = None
    caused_by_event_id: str | None = None
    reason: str | None = None
    source: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    contract_version: str = STATEDELTA_CONTRACT_VERSION

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        parts = value.split(".")
        if not value or any(part == "" for part in parts):
            raise ValueError("StateDelta path must be a non-empty dot path")
        return value


def apply_delta(state: GameState, delta: StateDelta) -> GameState:
    next_state = state.model_copy(deep=True)
    parent, key = _resolve_parent(next_state, delta.path)

    if delta.operation == StateDeltaOperation.SET:
        _set_value(parent, key, delta.value)
        return _validate_dict_entry_delta(next_state, delta.path)

    current_value = _get_value(parent, key)

    if delta.operation == StateDeltaOperation.INC:
        if not isinstance(current_value, int | float):
            raise StateDeltaError(f"Cannot inc non-numeric path: {delta.path}")
        if not isinstance(delta.value, int | float):
            raise StateDeltaError(f"Increment value must be numeric for path: {delta.path}")
        _set_value(parent, key, current_value + delta.value)
        return next_state

    if delta.operation == StateDeltaOperation.ADD:
        if isinstance(current_value, list):
            if delta.value not in current_value:
                current_value.append(delta.value)
            return next_state
        if isinstance(current_value, set):
            current_value.add(delta.value)
            return next_state
        raise StateDeltaError(f"Cannot add to non-collection path: {delta.path}")

    if delta.operation == StateDeltaOperation.REMOVE:
        if isinstance(current_value, list):
            if delta.value not in current_value:
                raise StateDeltaError(f"Cannot remove missing value from path: {delta.path}")
            current_value.remove(delta.value)
            return next_state
        if isinstance(current_value, set):
            if delta.value not in current_value:
                raise StateDeltaError(f"Cannot remove missing value from path: {delta.path}")
            current_value.remove(delta.value)
            return next_state
        raise StateDeltaError(f"Cannot remove from non-collection path: {delta.path}")

    raise StateDeltaError(f"Unsupported delta operation: {delta.operation}")


def inverse_delta(before_state: GameState, delta: StateDelta) -> StateDelta:
    parent, key = _resolve_parent(before_state, delta.path)
    previous_value = _get_value(parent, key)

    if delta.operation == StateDeltaOperation.SET:
        return StateDelta(
            operation=StateDeltaOperation.SET,
            path=delta.path,
            value=previous_value,
            caused_by_event_id=delta.caused_by_event_id,
            reason="Rollback set delta",
        )

    if delta.operation == StateDeltaOperation.INC:
        if not isinstance(delta.value, int | float):
            raise StateDeltaError(f"Increment value must be numeric for path: {delta.path}")
        return StateDelta(
            operation=StateDeltaOperation.INC,
            path=delta.path,
            value=-delta.value,
            caused_by_event_id=delta.caused_by_event_id,
            reason="Rollback inc delta",
        )

    if delta.operation == StateDeltaOperation.ADD:
        if _collection_contains(previous_value, delta.value):
            return StateDelta(
                operation=StateDeltaOperation.SET,
                path=delta.path,
                value=previous_value,
                caused_by_event_id=delta.caused_by_event_id,
                reason="Rollback no-op add delta",
            )
        return StateDelta(
            operation=StateDeltaOperation.REMOVE,
            path=delta.path,
            value=delta.value,
            caused_by_event_id=delta.caused_by_event_id,
            reason="Rollback add delta",
        )

    if delta.operation == StateDeltaOperation.REMOVE:
        return StateDelta(
            operation=StateDeltaOperation.ADD,
            path=delta.path,
            value=delta.value,
            caused_by_event_id=delta.caused_by_event_id,
            reason="Rollback remove delta",
        )

    raise StateDeltaError(f"Unsupported delta operation: {delta.operation}")


def rollback_delta(state: GameState, inverse: StateDelta) -> GameState:
    return apply_delta(state, inverse)


def _resolve_parent(state: GameState, path: str) -> tuple[Any, str]:
    parts = path.split(".")
    current: Any = state

    for part in parts[:-1]:
        current = _get_value(current, part)

    return current, parts[-1]


def _get_value(container: Any, key: str) -> Any:
    if isinstance(container, BaseModel):
        if not hasattr(container, key):
            raise StateDeltaError(f"Invalid state path segment: {key}")
        return getattr(container, key)

    if isinstance(container, dict):
        if key not in container:
            raise StateDeltaError(f"Invalid state path segment: {key}")
        return container[key]

    raise StateDeltaError(f"Cannot traverse through non-container path segment: {key}")


def _set_value(container: Any, key: str, value: Any) -> None:
    if isinstance(container, BaseModel):
        if not hasattr(container, key):
            raise StateDeltaError(f"Invalid state path segment: {key}")
        setattr(container, key, _validate_model_field_value(container, key, value))
        return

    if isinstance(container, dict):
        container[key] = value
        return

    raise StateDeltaError(f"Cannot set value on non-container path segment: {key}")


def _validate_model_field_value(container: BaseModel, key: str, value: Any) -> Any:
    field = container.__class__.model_fields.get(key)
    if field is None:
        return value
    try:
        return TypeAdapter(field.annotation).validate_python(value)
    except Exception as exc:
        raise StateDeltaError(f"Invalid value for state path segment: {key}") from exc


FORBIDDEN_CONTRACT_PATHS = {
    "debug",
    "debug_memory",
    "raw_env",
    "api_key",
    "secrets",
}


def validate_stable_delta_contract(delta: StateDelta) -> None:
    """Validate a delta against the stable v1.8 contract without applying it."""
    if delta.contract_version != STATEDELTA_CONTRACT_VERSION:
        raise StateDeltaError(f"Unsupported StateDelta contract_version: {delta.contract_version}")
    if not isinstance(delta.operation, StateDeltaOperation):
        raise StateDeltaError(f"Unsupported delta operation: {delta.operation}")
    parts = delta.path.split(".")
    if any(part in FORBIDDEN_CONTRACT_PATHS for part in parts):
        raise StateDeltaError(f"Forbidden StateDelta path: {delta.path}")
    if delta.path.startswith("player_visible_facts") and delta.metadata.get("hidden") == "true":
        raise StateDeltaError("Hidden facts cannot be written to player_visible_facts by StateDelta contract")


def _validate_dict_entry_delta(state: GameState, path: str) -> GameState:
    parts = path.split(".")
    if len(parts) != 2:
        return state
    field = GameState.model_fields.get(parts[0])
    if field is None:
        return state
    field_value = getattr(state, parts[0], None)
    if not isinstance(field_value, dict) or parts[1] not in field_value:
        return state
    try:
        field_value[parts[1]] = TypeAdapter(field.annotation).validate_python(field_value)[parts[1]]
        return state
    except Exception as exc:
        raise StateDeltaError(f"StateDelta produced invalid value for state path: {path}") from exc


def _collection_contains(collection: Any, value: Any) -> bool:
    if isinstance(collection, list | set):
        return value in collection
    raise StateDeltaError("Expected collection value for collection rollback")

