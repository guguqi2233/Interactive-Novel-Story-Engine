import json
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.world_state import ActorCondition, FactVisibility, GameState
from app.session_store import build_visible_state


class InvariantCheckResult(BaseModel):
    invariant_violations: list[str] = Field(default_factory=list)
    visibility_leaks: list[str] = Field(default_factory=list)


def check_playtest_invariants(
    state: GameState,
    events: list[Event],
    previous_turn: int | None = None,
    visible_payload: Mapping[str, Any] | None = None,
) -> InvariantCheckResult:
    violations: list[str] = []
    leaks: list[str] = []

    violations.extend(_check_item_placement(state))
    violations.extend(_check_dead_npc_actions(state, events))
    violations.extend(_check_event_delta_integrity(events))
    if previous_turn is not None and state.turn < previous_turn:
        violations.append(f"turn_decreased:{previous_turn}->{state.turn}")

    payload = visible_payload or build_visible_state(state).model_dump(mode="json")
    leaks.extend(_check_hidden_fact_visibility(state, payload))
    leaks.extend(_check_raw_state_deltas_absent(payload))

    return InvariantCheckResult(
        invariant_violations=violations,
        visibility_leaks=leaks,
    )


def _check_item_placement(state: GameState) -> list[str]:
    violations: list[str] = []
    for item in state.objects.values():
        placements = [
            item.location_id is not None,
            item.owner_id is not None,
            item.container_id is not None,
        ]
        if sum(placements) > 1:
            violations.append(f"item_in_multiple_places:{item.id}")
    return violations


def _check_dead_npc_actions(state: GameState, events: list[Event]) -> list[str]:
    violations: list[str] = []
    dead_npc_ids = {
        npc.id
        for npc in state.npcs.values()
        if not npc.alive or npc.condition == ActorCondition.DEAD
    }
    for event in events:
        if event.actor_id in dead_npc_ids and event.action_type != "system":
            violations.append(f"dead_npc_acted:{event.actor_id}:{event.event_id}")
    return violations


def _check_event_delta_integrity(events: list[Event]) -> list[str]:
    violations: list[str] = []
    for event in events:
        if not event.state_deltas and not event.allow_empty_delta:
            violations.append(f"event_missing_state_deltas:{event.event_id}")
    return violations


def _check_hidden_fact_visibility(state: GameState, visible_payload: Mapping[str, Any]) -> list[str]:
    leaks: list[str] = []
    visible_json = json.dumps(visible_payload, ensure_ascii=False)
    for fact in state.facts.values():
        if fact.visibility != FactVisibility.HIDDEN:
            continue
        if fact.id in state.player_visible_facts:
            leaks.append(f"hidden_fact_marked_visible:{fact.id}")
        if fact.text and fact.text in visible_json:
            leaks.append(f"hidden_fact_text_visible:{fact.id}")
    return leaks


def _check_raw_state_deltas_absent(visible_payload: Mapping[str, Any]) -> list[str]:
    visible_json = json.dumps(visible_payload, ensure_ascii=False)
    if "state_deltas" in visible_json:
        return ["raw_state_deltas_in_player_payload"]
    return []
