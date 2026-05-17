from pathlib import Path

from app.core.state_delta import apply_delta
from app.core.world_state import (
    CrimeState,
    FactionState,
    GameState,
    LocationState,
    NPCState,
    ReputationState,
    RumorState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.faction_conflict import (
    apply_faction_incident,
    build_faction_conflict_event,
    change_alert_level,
    change_faction_relation,
    get_faction_relation,
    get_visible_faction_conflicts,
    resolve_faction_conflicts_from_crimes,
    resolve_faction_conflicts_from_rumors,
)
from app.engine.rules.social_tick import run_social_consequence_tick
from app.session_store import build_visible_state


def make_state() -> GameState:
    return GameState(
        world_id="faction-conflict-test",
        locations={"square": LocationState(id="square", name="Square")},
        factions={
            "council": FactionState(
                id="council",
                name="Council",
                reputation=ReputationState(known_to_player=True),
                relationships_to_other_factions={"smugglers": -5},
                known_by_player=True,
                conflict_tags=["law"],
            ),
            "smugglers": FactionState(
                id="smugglers",
                name="Smugglers",
                reputation=ReputationState(known_to_player=False),
                relationships_to_other_factions={"council": -5},
                known_by_player=False,
                conflict_tags=["hidden"],
            ),
        },
        npcs={
            "harlan": NPCState(id="harlan", location_id="square", faction_id="council"),
            "shade": NPCState(id="shade", location_id="square", faction_id="smugglers"),
        },
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_factions_yaml_relations_load() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()

    assert state.factions["village_council"].relationships_to_other_factions["old_road_smugglers"] == -10
    assert state.factions["village_council"].conflict_tags == ["law_vs_smuggling"]
    assert state.factions["old_road_smugglers"].alert_level == 0


def test_faction_incident_increases_alert_level() -> None:
    state = make_state()
    deltas = apply_faction_incident(
        state,
        incident_id="rumor:bridge",
        faction_id="council",
        alert_delta=2,
        reason="A public rumor reached the council.",
    )
    next_state = apply_all(state, deltas)

    assert next_state.factions["council"].alert_level == 2
    assert next_state.social_flags["faction_conflict_processed_rumor_bridge_council_none"] is True


def test_crime_against_faction_member_affects_conflict() -> None:
    state = make_state()
    state.crimes["crime-1"] = CrimeState(
        id="crime-1",
        crime_type="assault",
        actor_id="player",
        victim_id="harlan",
        location_id="square",
        severity=4,
    )
    next_state = apply_all(state, resolve_faction_conflicts_from_crimes(state))

    assert next_state.factions["council"].alert_level == 4
    assert next_state.factions["council"].conflict_level == 2


def test_hidden_faction_conflict_does_not_enter_visible_state() -> None:
    state = make_state()
    for delta in apply_faction_incident(
        state,
        incident_id="hidden-smuggler-alert",
        faction_id="smugglers",
        alert_delta=5,
        conflict_delta=2,
        reason="Hidden faction incident.",
    ):
        state = apply_delta(state, delta)

    payload = build_visible_state(state).model_dump(mode="json")

    assert "smugglers" not in str(payload["faction_conflicts"])
    assert "Hidden faction incident" not in str(payload)


def test_public_rumor_can_raise_faction_alert() -> None:
    state = make_state()
    state.rumors["rumor-1"] = RumorState(
        id="rumor-1",
        text_for_player="A public fight happened.",
        known_by_factions={"council"},
        known_by_player=True,
        tags=["public", "combat"],
    )
    next_state = apply_all(state, resolve_faction_conflicts_from_rumors(state))

    assert next_state.factions["council"].alert_level == 1


def test_save_load_preserves_faction_conflict_state(tmp_path: Path) -> None:
    state = make_state()
    next_state = apply_all(
        state,
        [
            *change_alert_level(state, "council", 3, "Raised patrols."),
            *change_faction_relation(state, "council", "smugglers", -2, "Border clash."),
        ],
    )
    repository = SQLiteSaveRepository(tmp_path / "faction_conflict.db")

    repository.create_save("save-1", next_state)
    loaded = repository.load_save("save-1")

    assert loaded.factions["council"].alert_level == 3
    assert loaded.factions["council"].relationships_to_other_factions["smugglers"] == -7


def test_duplicate_incident_does_not_repeat_infinitely() -> None:
    state = make_state()
    first = apply_faction_incident(
        state,
        incident_id="crime:1",
        faction_id="council",
        alert_delta=2,
        conflict_delta=1,
        reason="Crime reported.",
    )
    next_state = apply_all(state, first)
    second = apply_faction_incident(
        next_state,
        incident_id="crime:1",
        faction_id="council",
        alert_delta=2,
        conflict_delta=1,
        reason="Crime reported.",
    )

    assert first
    assert second == []


def test_social_tick_runs_faction_conflict_and_event_can_be_built() -> None:
    state = make_state()
    state.rumors["rumor-1"] = RumorState(
        id="rumor-1",
        text_for_player="A public rumor.",
        known_by_factions={"council"},
        known_by_player=True,
        tags=["public"],
    )

    deltas = run_social_consequence_tick(state)
    event = build_faction_conflict_event("faction-event-1", state.turn, deltas)
    next_state = apply_all(state, deltas)

    assert next_state.factions["council"].alert_level == 1
    assert event.action_type == "faction_conflict"
    assert event.state_deltas == deltas
    assert get_visible_faction_conflicts(next_state)
    assert get_faction_relation(next_state, "council", "smugglers") == -5
