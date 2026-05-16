from random import Random

from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.core.state_delta import apply_delta
from app.core.world_state import (
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    NPCState,
    PlayerState,
    WorldObjectState,
)
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.actions.search import SearchActionHandler
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.session_store import build_visible_state


def make_state() -> GameState:
    return GameState(
        world_id="search-test",
        player=PlayerState(location_id="square"),
        locations={
            "square": LocationState(
                id="square",
                name="Square",
                visible_objects=["fountain"],
            )
        },
        objects={
            "fountain": WorldObjectState(id="fountain", location_id="square"),
            "loose_stone": WorldObjectState(
                id="loose_stone",
                location_id="square",
                hidden=True,
                discoverable=True,
            ),
            "sealed_cache": WorldObjectState(
                id="sealed_cache",
                location_id="loose_stone",
                hidden=True,
                discoverable=True,
            ),
            "buried_blade": WorldObjectState(
                id="buried_blade",
                location_id="square",
                hidden=True,
                discoverable=False,
            ),
        },
        npcs={
            "harlan": NPCState(id="harlan", location_id="square"),
        },
        facts={
            "stone_is_loose": FactState(
                id="stone_is_loose",
                text="One paving stone rocks under pressure.",
                visibility=FactVisibility.DISCOVERABLE,
                tags=["location:square"],
            ),
            "harlan_tracks_mud": FactState(
                id="harlan_tracks_mud",
                text="Harlan's boots carry river mud.",
                visibility=FactVisibility.DISCOVERABLE,
                tags=["npc:harlan"],
            ),
            "blade_under_square": FactState(
                id="blade_under_square",
                text="A blade is buried beneath the square.",
                visibility=FactVisibility.HIDDEN,
                secret=True,
                tags=["location:square"],
            ),
        },
    )


def make_intent(target_id: str | None = None) -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.SEARCH,
        target_id=target_id,
        raw_text="search",
        confidence=0.9,
        requires_clarification=False,
    )


def test_search_current_location_discovers_clues() -> None:
    state = make_state()

    result = SearchActionHandler().resolve(make_intent(), state, Random(1))

    assert result.success_level == "success"
    assert "loose_stone" in str(result.visible_facts)
    assert "stone_is_loose" in str(result.visible_facts)


def test_search_success_makes_discoverable_object_visible() -> None:
    state = make_state()
    result = SearchActionHandler().resolve(make_intent(), state, Random(1))
    next_state = state
    for delta in result.state_deltas:
        next_state = apply_delta(next_state, delta)

    visible_state = build_visible_state(next_state)

    assert any(item.id == "loose_stone" for item in visible_state.visible_objects)


def test_search_success_makes_discoverable_fact_known() -> None:
    state = make_state()
    result = SearchActionHandler().resolve(make_intent(), state, Random(1))
    next_state = state
    for delta in result.state_deltas:
        next_state = apply_delta(next_state, delta)

    visible_state = build_visible_state(next_state)

    assert any(fact.id == "stone_is_loose" for fact in visible_state.known_facts)


def test_search_object_target_discovers_nearby_object() -> None:
    state = make_state()
    state.objects["loose_stone"].discovered_by.append("player")

    result = SearchActionHandler().resolve(make_intent("loose_stone"), state, Random(1))

    assert result.success_level == "success"
    assert any(delta.path == "objects.sealed_cache.discovered_by" for delta in result.state_deltas)


def test_search_npc_target_discovers_npc_scoped_fact() -> None:
    result = SearchActionHandler().resolve(make_intent("harlan"), make_state(), Random(1))

    assert result.success_level == "success"
    assert any(delta.value == "harlan_tracks_mud" for delta in result.state_deltas)


def test_search_failure_does_not_leak_hidden_fact() -> None:
    state = make_state()
    state.objects["loose_stone"].discoverable = False
    state.facts["stone_is_loose"].visibility = FactVisibility.HIDDEN

    result = SearchActionHandler().resolve(make_intent(), state, Random(1))

    assert result.success_level == "failure"
    assert "blade_under_square" not in str(result.visible_facts)
    assert "blade_under_square" not in str(result.model_dump())


def test_search_invalid_target_returns_invalid() -> None:
    result = SearchActionHandler().resolve(make_intent("missing"), make_state(), Random(1))

    assert result.success_level == "invalid"
    assert result.state_deltas == []


def test_search_consumes_time() -> None:
    result = SearchActionHandler().resolve(make_intent(), make_state(), Random(1))

    assert result.state_deltas[0].path == "current_time"


def test_search_state_delta_records_discovery() -> None:
    result = SearchActionHandler().resolve(make_intent(), make_state(), Random(1))

    assert any(delta.path == "objects.loose_stone.discovered_by" for delta in result.state_deltas)
    assert any(delta.path == "player_visible_facts" and delta.value == "stone_is_loose" for delta in result.state_deltas)


def test_search_generates_event_through_game_loop() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "action_type": "search",
                "raw_text": "search",
                "confidence": 0.9,
                "requires_clarification": False,
            },
            {
                "text": "You find a clue.",
                "suggested_actions": [],
                "short_summary": "Searched.",
            },
        ]
    )
    game_loop = GameLoop(
        state=make_state(),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(1),
    )

    result = game_loop.step("search")

    assert result.event is not None
    assert result.event.action_type == "search"
    assert any(delta.path == "objects.loose_stone.discovered_by" for delta in result.event.state_deltas)
