from pathlib import Path
from random import Random

from app.core.event_log import Event, EventLog
from app.core.game_loop import GameLoop
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    CrimeStatus,
    FactionState,
    GameState,
    LocationState,
    NPCState,
    ReputationState,
    WitnessReportIntent,
    WorldObjectState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.rules.crime import (
    classify_crime,
    detect_witnesses,
    get_player_known_crimes,
    resolve_crime_from_event,
)
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.session_store import build_visible_state


def make_state(hidden_witness: bool = False) -> GameState:
    return GameState(
        world_id="crime-test",
        locations={
            "square": LocationState(id="square", name="Square", light_level=5, cover_level=0),
        },
        player={"location_id": "square"},
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                faction_id="watch",
                hidden=hidden_witness,
                discovered_by=[],
                alertness=1,
            )
        },
        factions={
            "watch": FactionState(
                id="watch",
                name="Watch",
                reputation=ReputationState(value=0, known_to_player=True),
            )
        },
        objects={
            "coin": WorldObjectState(id="coin", location_id="square", portable=True),
            "locked_box": WorldObjectState(
                id="locked_box",
                location_id="square",
                visible=True,
                locked=True,
                lock_difficulty=99,
            ),
        },
    )


def theft_event() -> Event:
    return Event(
        event_id="event-theft",
        turn=1,
        actor_id="player",
        action_type="use_item",
        target_id="coin",
        result="success",
        visible_to_player=True,
        state_deltas=[
            StateDelta(
                operation=StateDeltaOperation.SET,
                path="objects.coin.owner_id",
                value="player",
            )
        ],
    )


def test_theft_event_classifies_as_theft_crime() -> None:
    draft = classify_crime(theft_event(), make_state())

    assert draft is not None
    assert draft.crime_type == "theft"
    assert draft.target_id == "coin"


def test_seen_crime_creates_witness_record() -> None:
    state = make_state()
    event = theft_event()

    witnesses = detect_witnesses(event, state)

    assert witnesses[0].npc_id == "harlan"
    assert witnesses[0].saw_actor is True
    assert witnesses[0].report_intent in {WitnessReportIntent.LATER, WitnessReportIntent.IMMEDIATE}


def test_unseen_crime_can_remain_hidden() -> None:
    state = make_state()
    state.npcs = {}
    event = theft_event()

    deltas = resolve_crime_from_event(event, state)
    for delta in deltas:
        state = apply_delta(state, delta)

    crime = next(iter(state.crimes.values()))
    assert crime.status == CrimeStatus.HIDDEN
    assert state.witnesses == {}


def test_hidden_witness_does_not_enter_visible_state() -> None:
    state = make_state(hidden_witness=True)
    event = theft_event()

    for delta in resolve_crime_from_event(event, state):
        state = apply_delta(state, delta)
    visible_state = build_visible_state(state)

    assert not visible_state.visible_npcs
    assert "harlan" not in str(visible_state)


def test_witnessed_crime_can_generate_rumor() -> None:
    state = make_state()
    event = theft_event()

    for delta in resolve_crime_from_event(event, state):
        state = apply_delta(state, delta)

    assert state.rumors
    rumor = next(iter(state.rumors.values()))
    assert "harlan" in rumor.known_by_npcs
    assert rumor.known_by_player is False


def test_reported_crime_lowers_faction_reputation() -> None:
    state = make_state()
    event = theft_event()

    for delta in resolve_crime_from_event(event, state):
        state = apply_delta(state, delta)

    assert state.factions["watch"].reputation.value < 0
    assert next(iter(state.crimes.values())).status == CrimeStatus.REPORTED


def test_lockpick_failure_with_witness_generates_crime_event() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "action_type": "lockpick",
                "target_id": "locked_box",
                "raw_text": "撬锁",
                "confidence": 1.0,
                "requires_clarification": False,
            },
            {
                "text": "锁发出刺耳声响。",
                "suggested_actions": [],
                "short_summary": "撬锁失败。",
            },
        ]
    )
    loop = GameLoop(
        state=make_state(),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(0),
    )

    result = loop.step("撬锁")

    assert result.system_events
    assert any(event.action_type == "crime_consequence" for event in result.system_events)
    assert loop.state.crimes


def test_sneak_success_metadata_can_avoid_witness_saw_actor() -> None:
    state = make_state()
    event = Event(
        event_id="event-sneak-crime",
        turn=1,
        actor_id="player",
        action_type="use_item",
        target_id="coin",
        result="success",
        visible_to_player=True,
        state_deltas=[
            StateDelta(
                operation=StateDeltaOperation.SET,
                path="objects.coin.owner_id",
                value="player",
                metadata={"sneak_result": "success"},
            )
        ],
    )

    witnesses = detect_witnesses(event, state)

    assert witnesses[0].npc_id == "harlan"
    assert witnesses[0].saw_actor is False


def test_save_load_preserves_crime_and_witness_state(tmp_path: Path) -> None:
    state = make_state()
    for delta in resolve_crime_from_event(theft_event(), state):
        state = apply_delta(state, delta)
    repository = SQLiteSaveRepository(tmp_path / "crime.db")

    repository.create_save("save-1", state)
    loaded = repository.load_save("save-1")

    assert loaded.crimes == state.crimes
    assert loaded.witnesses == state.witnesses


def test_player_known_crimes_only_include_reported_or_known() -> None:
    state = make_state()
    assert get_player_known_crimes(state) == []

    for delta in resolve_crime_from_event(theft_event(), state):
        state = apply_delta(state, delta)

    assert get_player_known_crimes(state)
