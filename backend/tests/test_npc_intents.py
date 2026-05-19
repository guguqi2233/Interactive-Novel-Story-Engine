from app.core.state_delta import apply_delta
from app.core.world_state import ActorCondition, FactState, FactVisibility, NPCIntent, NPCIntentStatus, load_game_state_payload
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.npc_intents import (
    cancel_intent,
    complete_intent,
    enqueue_intent,
    prune_expired_intents,
    select_next_intent,
)


def test_enqueue_intent_uses_state_delta() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    intent = NPCIntent(
        id="guard-blacksmith",
        npc_id="harlan",
        intent_type="guard_location",
        priority=3,
        target_id="blacksmith",
        target_type="location",
        created_turn=state.turn,
    )

    result = enqueue_intent(state, "harlan", intent)

    assert len(result.state_deltas) == 1
    assert result.state_deltas[0].path == "npcs.harlan.intent_queue"
    assert result.state_deltas[0].metadata["source"] == "npc_intent"
    assert state.npcs["harlan"].intent_queue == []

    next_state = apply_delta(state, result.state_deltas[0])
    assert next_state.npcs["harlan"].intent_queue[0].id == "guard-blacksmith"


def test_select_next_intent_uses_priority_then_created_turn_then_id() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={
            "intent_queue": [
                NPCIntent(id="later", npc_id="harlan", intent_type="guard_location", priority=5, created_turn=2),
                NPCIntent(id="earlier-b", npc_id="harlan", intent_type="guard_location", priority=5, created_turn=1),
                NPCIntent(id="earlier-a", npc_id="harlan", intent_type="guard_location", priority=5, created_turn=1),
                NPCIntent(id="low", npc_id="harlan", intent_type="guard_location", priority=1, created_turn=0),
            ]
        }
    )

    selected = select_next_intent(state, "harlan")

    assert selected is not None
    assert selected.id == "earlier-a"


def test_prune_expired_intents_removes_open_expired_intents() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state = state.model_copy(update={"turn": 5})
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={
            "intent_queue": [
                NPCIntent(id="expired", npc_id="harlan", intent_type="guard_location", created_turn=1, expires_turn=5),
                NPCIntent(id="future", npc_id="harlan", intent_type="guard_location", created_turn=1, expires_turn=8),
                NPCIntent(
                    id="completed-expired",
                    npc_id="harlan",
                    intent_type="guard_location",
                    status=NPCIntentStatus.COMPLETED,
                    created_turn=1,
                    expires_turn=5,
                ),
            ]
        }
    )

    result = prune_expired_intents(state, "harlan")
    next_state = apply_delta(state, result.state_deltas[0])

    assert [intent.id for intent in next_state.npcs["harlan"].intent_queue] == ["future", "completed-expired"]
    assert result.events[0].action_type == "npc_intents_pruned"


def test_dead_npc_does_not_select_intent() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={
            "alive": False,
            "condition": ActorCondition.DEAD,
            "intent_queue": [
                NPCIntent(id="guard", npc_id="harlan", intent_type="guard_location", priority=10, created_turn=0)
            ],
        }
    )

    assert select_next_intent(state, "harlan") is None


def test_dead_npc_cannot_enqueue_intent() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={"alive": False, "condition": ActorCondition.DEAD}
    )
    intent = NPCIntent(
        id="dead-guard",
        npc_id="harlan",
        intent_type="guard_location",
        priority=10,
        target_id="blacksmith",
        target_type="location",
        created_turn=state.turn,
    )

    result = enqueue_intent(state, "harlan", intent)

    assert result.rejected_reason == "npc_inactive"
    assert result.state_deltas == []
    assert result.events == []


def test_unknown_fact_intent_is_not_enqueued() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.facts["unknown_hidden_cache"] = FactState(
        id="unknown_hidden_cache",
        text="A hidden cache nobody in this test knows about.",
        visibility=FactVisibility.HIDDEN,
        known_by=set(),
    )
    intent = NPCIntent(
        id="seek-hidden-cache",
        npc_id="harlan",
        intent_type="seek_item",
        target_id="unknown_hidden_cache",
        target_type="fact",
        created_turn=state.turn,
        preconditions=["fact:unknown_hidden_cache"],
    )

    result = enqueue_intent(state, "harlan", intent)

    assert result.rejected_reason == "npc_unknown_fact"
    assert result.state_deltas == []
    assert result.events == []


def test_intent_status_changes_record_system_event() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={
            "intent_queue": [
                NPCIntent(id="guard", npc_id="harlan", intent_type="guard_location", priority=1, created_turn=0)
            ]
        }
    )

    completed = complete_intent(state, "harlan", "guard")
    cancelled = cancel_intent(state, "harlan", "guard")

    assert completed.events[0].actor_id == "system"
    assert completed.events[0].action_type == "npc_intent_completed"
    assert completed.events[0].state_deltas == completed.state_deltas
    assert cancelled.events[0].action_type == "npc_intent_cancelled"


def test_save_load_preserves_intent_queue() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.npcs["harlan"] = state.npcs["harlan"].model_copy(
        update={
            "intent_queue": [
                NPCIntent(
                    id="talk-to-player",
                    npc_id="harlan",
                    intent_type="talk_to_npc",
                    priority=4,
                    target_id="player",
                    target_type="npc",
                    created_turn=2,
                    preconditions=["fact:old_bridge_creaks_at_midnight"],
                )
            ]
        }
    )

    restored = load_game_state_payload(state.model_dump(mode="json"))

    assert restored.npcs["harlan"].intent_queue[0].id == "talk-to-player"
    assert restored.npcs["harlan"].intent_queue[0].preconditions == ["fact:old_bridge_creaks_at_midnight"]
