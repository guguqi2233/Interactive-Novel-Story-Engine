import hashlib
import json
from collections import defaultdict
from typing import Iterable

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaError, apply_delta
from app.core.world_state import GameState


class TimelineStateDiff(BaseModel):
    path: str
    operation: str
    reason: str | None = None
    visible_to_player: bool = False


class TimelineEventView(BaseModel):
    turn: int
    event_id: str
    actor_id: str
    action_type: str
    result: str
    target_id: str | None = None
    visible_to_player: bool
    event_kind: str
    state_deltas: list[StateDelta] = Field(default_factory=list)
    visible_changes: list[TimelineStateDiff] = Field(default_factory=list)
    delta_count: int = 0
    created_at: str


class TimelineTurnGroup(BaseModel):
    turn: int
    events: list[TimelineEventView] = Field(default_factory=list)
    event_count: int = 0
    delta_count: int = 0


class ReplayCheckpoint(BaseModel):
    turn: int
    event_id: str
    checksum: str
    delta_count: int


class ReplaySummary(BaseModel):
    event_count: int
    final_state_checksum: str
    invariant_violations: list[str] = Field(default_factory=list)
    failed_event_id: str | None = None
    checkpoints: list[ReplayCheckpoint] = Field(default_factory=list)


class TimelineReplay(BaseModel):
    local_only: bool = True
    source_type: str
    source_id: str
    turns: list[TimelineTurnGroup] = Field(default_factory=list)
    event_count: int = 0
    delta_count: int = 0
    replay_summary: ReplaySummary | None = None


def build_timeline_replay(
    events: Iterable[Event],
    *,
    source_type: str,
    source_id: str,
    turn_from: int | None = None,
    turn_to: int | None = None,
    event_filter: str | None = None,
) -> TimelineReplay:
    filtered_events = [
        event
        for event in sorted(events, key=lambda item: (item.turn, item.created_at.isoformat(), item.event_id))
        if _turn_matches(event, turn_from, turn_to) and _filter_matches(event, event_filter)
    ]
    grouped: dict[int, list[TimelineEventView]] = defaultdict(list)
    for event in filtered_events:
        grouped[event.turn].append(_event_view(event))
    turns = [
        TimelineTurnGroup(
            turn=turn,
            events=views,
            event_count=len(views),
            delta_count=sum(view.delta_count for view in views),
        )
        for turn, views in sorted(grouped.items())
    ]
    return TimelineReplay(
        source_type=source_type,
        source_id=source_id,
        turns=turns,
        event_count=len(filtered_events),
        delta_count=sum(turn.delta_count for turn in turns),
    )


def replay_dry_run(initial_state: GameState, events: Iterable[Event]) -> ReplaySummary:
    state = initial_state.model_copy(deep=True)
    checkpoints: list[ReplayCheckpoint] = []
    event_count = 0
    failed_event_id: str | None = None
    invariant_violations: list[str] = []
    for event in sorted(events, key=lambda item: (item.turn, item.created_at.isoformat(), item.event_id)):
        event_count += 1
        try:
            for delta in event.state_deltas:
                state = apply_delta(state, delta)
        except StateDeltaError as exc:
            failed_event_id = event.event_id
            invariant_violations.append(f"Failed to apply event {event.event_id}: {exc}")
            break
        invariant_violations.extend(_state_invariants(state))
        checkpoints.append(
            ReplayCheckpoint(
                turn=event.turn,
                event_id=event.event_id,
                checksum=state_checksum(state),
                delta_count=len(event.state_deltas),
            )
        )
    return ReplaySummary(
        event_count=event_count,
        final_state_checksum=state_checksum(state),
        invariant_violations=sorted(set(invariant_violations)),
        failed_event_id=failed_event_id,
        checkpoints=checkpoints,
    )


def state_checksum(state: GameState) -> str:
    payload = state.model_dump(mode="json")
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _event_view(event: Event) -> TimelineEventView:
    visible_changes = [
        TimelineStateDiff(
            path=delta.path,
            operation=str(delta.operation),
            reason=delta.reason,
            visible_to_player=delta.metadata.get("visible_to_player") == "true" or event.visible_to_player,
        )
        for delta in event.state_deltas
        if delta.metadata.get("visible_to_player") == "true" or event.visible_to_player
    ]
    return TimelineEventView(
        turn=event.turn,
        event_id=event.event_id,
        actor_id=event.actor_id,
        action_type=event.action_type,
        result=event.result,
        target_id=event.target_id,
        visible_to_player=event.visible_to_player,
        event_kind=_event_kind(event),
        state_deltas=event.state_deltas,
        visible_changes=visible_changes,
        delta_count=len(event.state_deltas),
        created_at=event.created_at.isoformat(),
    )


def _event_kind(event: Event) -> str:
    if event.actor_id == "player":
        return "player"
    if event.action_type in {"world_tick", "system_tick", "schedule_tick", "crime_consequence"}:
        return "tick"
    if event.action_type.startswith("quest"):
        return "quest"
    if "migration" in event.action_type:
        return "migration"
    if event.actor_id == "system":
        return "system"
    return "npc"


def _filter_matches(event: Event, event_filter: str | None) -> bool:
    if event_filter in {None, "", "all"}:
        return True
    return _event_kind(event) == event_filter


def _turn_matches(event: Event, turn_from: int | None, turn_to: int | None) -> bool:
    if turn_from is not None and event.turn < turn_from:
        return False
    if turn_to is not None and event.turn > turn_to:
        return False
    return True


def _state_invariants(state: GameState) -> list[str]:
    violations: list[str] = []
    for item in state.objects.values():
        placements = sum(
            [
                item.location_id is not None,
                item.owner_id is not None,
                item.container_id is not None,
            ]
        )
        if placements > 1:
            violations.append(f"Item has multiple placements: {item.id}")
    for npc in state.npcs.values():
        if npc.condition == "dead" and npc.alive:
            violations.append(f"Dead NPC marked alive: {npc.id}")
    return violations
