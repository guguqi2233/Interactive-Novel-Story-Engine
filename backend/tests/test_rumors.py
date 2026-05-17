from pathlib import Path
from uuid import UUID

from app.core.state_delta import apply_delta
from app.core.world_state import (
    FactState,
    FactVisibility,
    FactionState,
    GameState,
    LocationState,
    NPCState,
    ReputationState,
    RumorState,
    RumorTruthStatus,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.rumors import (
    add_rumor_to_npc,
    build_rumor_event,
    create_rumor,
    get_visible_rumors,
    mark_rumor_known_by_player,
    propagate_rumors,
)
from app.engine.rules.world_tick import run_world_tick
from app.session_store import build_visible_state


def make_state() -> GameState:
    return GameState(
        world_id="rumor-test",
        turn=3,
        locations={"square": LocationState(id="square", name="Square")},
        npcs={
            "harlan": NPCState(id="harlan", location_id="square"),
            "mira": NPCState(id="mira", location_id="square"),
            "distant": NPCState(id="distant", location_id="road"),
        },
        factions={
            "watch": FactionState(
                id="watch",
                name="Watch",
                reputation=ReputationState(known_to_player=True),
            )
        },
        facts={
            "hidden_fact": FactState(
                id="hidden_fact",
                text="The mayor hid the missing tools under the shrine.",
                visibility=FactVisibility.HIDDEN,
                secret=True,
            )
        },
    )


def test_mist_valley_rumors_yaml_loads() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()

    rumor = state.rumors["forge_tools_missing_rumor"]
    assert rumor.fact_id == "sealed_letter_under_stone"
    assert rumor.text_for_player == "People mutter that the missing tools may not be simple bad luck."
    assert rumor.known_by_npcs == {"harlan"}
    assert rumor.known_by_factions == {"village_council"}
    assert rumor.known_by_player is False


def test_create_rumor_writes_state_through_delta() -> None:
    state = make_state()
    deltas = create_rumor(
        state,
        rumor_id="crime_rumor",
        fact_id="hidden_fact",
        text_for_player="Someone is whispering about trouble near the shrine.",
        source_event_id="event-1",
        truth_status=RumorTruthStatus.UNKNOWN,
        known_by_npcs=["harlan"],
        known_by_factions=["watch"],
        spread_level=1,
        tags=["crime"],
    )

    next_state = apply_delta(state, deltas[0])

    rumor = next_state.rumors["crime_rumor"]
    assert rumor.source_event_id == "event-1"
    assert rumor.known_by_npcs == {"harlan"}
    assert rumor.known_by_factions == {"watch"}
    assert rumor.created_turn == 3


def test_npc_can_spread_known_rumor_to_npc_in_same_location() -> None:
    state = make_state()
    state.rumors["crime_rumor"] = RumorState(
        id="crime_rumor",
        text_for_player="Someone is whispering about trouble.",
        known_by_npcs={"harlan"},
        spread_level=0,
    )

    for delta in propagate_rumors(state):
        state = apply_delta(state, delta)

    assert "mira" in state.rumors["crime_rumor"].known_by_npcs
    assert "distant" not in state.rumors["crime_rumor"].known_by_npcs
    assert state.rumors["crime_rumor"].spread_level == 1


def test_add_rumor_to_npc_is_idempotent() -> None:
    state = make_state()
    state.rumors["crime_rumor"] = RumorState(
        id="crime_rumor",
        text_for_player="Someone is whispering about trouble.",
        known_by_npcs={"harlan"},
    )

    assert add_rumor_to_npc(state, "crime_rumor", "harlan") == []


def test_hidden_fact_text_does_not_leak_through_visible_rumor() -> None:
    state = make_state()
    state.rumors["crime_rumor"] = RumorState(
        id="crime_rumor",
        fact_id="hidden_fact",
        known_by_player=True,
    )

    visible_state = build_visible_state(state)
    payload = visible_state.model_dump(mode="json")

    assert payload["known_rumors"][0]["text_for_player"] == (
        "You have heard a vague rumor, but not enough to confirm the details."
    )
    assert "mayor hid the missing tools" not in str(payload)


def test_player_known_rumor_enters_visible_state() -> None:
    state = make_state()
    state.rumors["crime_rumor"] = RumorState(
        id="crime_rumor",
        text_for_player="Someone is whispering about trouble.",
        known_by_player=False,
    )

    for delta in mark_rumor_known_by_player(state, "crime_rumor"):
        state = apply_delta(state, delta)

    visible_rumors = get_visible_rumors(state)
    assert [rumor.id for rumor in visible_rumors] == ["crime_rumor"]
    assert build_visible_state(state).known_rumors[0].text_for_player == (
        "Someone is whispering about trouble."
    )


def test_rumor_propagation_builds_system_event() -> None:
    state = make_state()
    state.rumors["crime_rumor"] = RumorState(
        id="crime_rumor",
        text_for_player="Someone is whispering about trouble.",
        known_by_npcs={"harlan"},
    )
    deltas = propagate_rumors(state)

    event = build_rumor_event("00000000-0000-0000-0000-000000000001", state.turn, deltas)

    assert UUID(event.event_id)
    assert event.actor_id == "system"
    assert event.action_type == "rumor_spread"
    assert event.state_deltas == deltas


def test_world_tick_runs_rumor_propagation() -> None:
    state = make_state()
    state.rumors["crime_rumor"] = RumorState(
        id="crime_rumor",
        text_for_player="Someone is whispering about trouble.",
        known_by_npcs={"harlan"},
    )

    tick = run_world_tick(state)

    assert tick.event is not None
    assert tick.event.actor_id == "system"
    assert any(delta.path == "rumors.crime_rumor.known_by_npcs" for delta in tick.state_deltas)


def test_save_load_preserves_rumor_state(tmp_path: Path) -> None:
    state = make_state()
    state.rumors["crime_rumor"] = RumorState(
        id="crime_rumor",
        source_event_id="event-1",
        fact_id="hidden_fact",
        text_for_player="Someone is whispering about trouble.",
        truth_status=RumorTruthStatus.DISTORTED,
        known_by_npcs={"harlan", "mira"},
        known_by_factions={"watch"},
        known_by_player=True,
        spread_level=2,
        created_turn=1,
        tags=["crime"],
    )
    repository = SQLiteSaveRepository(tmp_path / "rumors.db")

    repository.create_save("save-1", state)
    loaded = repository.load_save("save-1")

    assert loaded.rumors["crime_rumor"] == state.rumors["crime_rumor"]


def test_rumors_yaml_is_optional_for_content_pack(tmp_path: Path) -> None:
    world_path = tmp_path / "no_rumors"
    world_path.mkdir()
    (world_path / "manifest.yaml").write_text(
        """
world_id: no_rumors
name: No Rumors
start_location_id: square
""",
        encoding="utf-8",
    )
    (world_path / "locations.yaml").write_text(
        """
locations:
  - id: square
    name: Square
    description: A square.
    exits: {}
""",
        encoding="utf-8",
    )
    (world_path / "npcs.yaml").write_text(
        """
npcs:
  - id: harlan
    name: Harlan
    location_id: square
    personality: careful
    knowledge: []
""",
        encoding="utf-8",
    )

    state = WorldLoader(tmp_path).load("no_rumors").to_game_state()

    assert state.rumors == {}
