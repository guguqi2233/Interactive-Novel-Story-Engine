import json
from pathlib import Path

from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    CrimeState,
    FactionState,
    GameState,
    LocationState,
    ReputationState,
    RumorState,
    WitnessRecord,
    load_game_state_payload,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.content.world_loader import WorldLoader
from app.session_store import build_visible_state


def test_new_game_state_has_default_social_fields() -> None:
    state = GameState(world_id="social-test")

    assert state.factions == {}
    assert state.rumors == {}
    assert state.crimes == {}
    assert state.witnesses == {}
    assert state.social_consequences == {}
    assert state.social_flags == {}


def test_old_game_state_json_missing_social_fields_loads_with_defaults() -> None:
    old_payload = {
        "world_id": "v03-save",
        "turn": 2,
        "locations": {"square": {"id": "square", "name": "Square"}},
        "player": {"id": "player", "location_id": "square", "inventory": []},
    }

    state = load_game_state_payload(old_payload)

    assert state.world_id == "v03-save"
    assert state.factions == {}
    assert state.rumors == {}
    assert state.crimes == {}
    assert state.witnesses == {}
    assert state.social_flags == {}


def test_save_load_preserves_social_fields(tmp_path: Path) -> None:
    state = GameState(
        world_id="social-save",
        factions={
            "town_watch": FactionState(
                id="town_watch",
                name="Town Watch",
                reputation=ReputationState(value=-3, known_to_player=False),
            )
        },
        rumors={
            "rumor_1": RumorState(
                id="rumor_1",
                fact_id="fact_1",
                text="A quiet internal rumor.",
                known_by={"harlan"},
                credibility=2,
            )
        },
        crimes={
            "crime_1": CrimeState(
                id="crime_1",
                crime_type="lockpicking",
                actor_id="player",
                location_id="square",
                turn=1,
                witness_ids=["harlan"],
            )
        },
        witnesses={
            "witness_1": WitnessRecord(
                id="witness_1",
                npc_id="harlan",
                crime_id="crime_1",
                confidence=4,
            )
        },
        social_flags={"watch_alerted": True},
    )
    repository = SQLiteSaveRepository(tmp_path / "social.db")

    repository.create_save("save-1", state)
    loaded = repository.load_save("save-1")

    assert loaded.factions == state.factions
    assert loaded.rumors == state.rumors
    assert loaded.crimes == state.crimes
    assert loaded.witnesses == state.witnesses
    assert loaded.social_flags == {"watch_alerted": True}


def test_repository_loads_old_state_json_with_missing_social_fields(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "old-save.db")
    old_payload = {
        "world_id": "old-world",
        "locations": {"square": {"id": "square", "name": "Square"}},
        "player": {"id": "player", "location_id": "square", "inventory": []},
    }
    with repository._connect() as connection:
        connection.execute(
            """
            INSERT INTO save_games (save_id, state_json, created_at, updated_at)
            VALUES (?, ?, datetime('now'), datetime('now'))
            """,
            ("old-save", json.dumps(old_payload)),
        )

    loaded = repository.load_save("old-save")

    assert loaded.world_id == "old-world"
    assert loaded.factions == {}
    assert loaded.social_flags == {}


def test_visible_state_does_not_expose_hidden_social_data() -> None:
    state = GameState(
        world_id="social-visible",
        player_visible_facts=set(),
        locations={"square": LocationState(id="square", name="Square")},
        player={"location_id": "square"},
        factions={
            "secret_court": FactionState(
                id="secret_court",
                name="Secret Court",
                reputation=ReputationState(value=-10, known_to_player=False),
            )
        },
        rumors={
            "hidden_rumor": RumorState(
                id="hidden_rumor",
                text="Hidden rumor text",
                known_by={"harlan"},
                known_to_player=False,
            )
        },
        crimes={
            "hidden_crime": CrimeState(
                id="hidden_crime",
                crime_type="theft",
                actor_id="player",
                location_id="square",
                turn=1,
                witness_ids=["hidden_npc"],
            )
        },
    )

    visible_state = build_visible_state(state)
    payload = visible_state.model_dump(mode="json")

    assert payload["factions"] == []
    assert payload["known_rumors"] == []
    assert "crimes" not in payload
    assert "Secret Court" not in json.dumps(payload)
    assert "Hidden rumor text" not in json.dumps(payload)


def test_state_delta_can_modify_social_paths() -> None:
    state = GameState(
        world_id="social-delta",
        factions={
            "town_watch": FactionState(
                id="town_watch",
                name="Town Watch",
                reputation=ReputationState(value=0),
            )
        },
        rumors={"rumor_1": RumorState(id="rumor_1", credibility=1)},
        crimes={
            "crime_1": CrimeState(
                id="crime_1",
                crime_type="trespass",
                actor_id="player",
                location_id="square",
                turn=1,
            )
        },
    )

    state = apply_delta(
        state,
        StateDelta(
            operation=StateDeltaOperation.INC,
            path="factions.town_watch.reputation.value",
            value=-2,
        ),
    )
    state = apply_delta(
        state,
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path="rumors.rumor_1.known_by",
            value="harlan",
        ),
    )
    state = apply_delta(
        state,
        StateDelta(
            operation=StateDeltaOperation.SET,
            path="crimes.crime_1.status",
            value="witnessed",
        ),
    )

    assert state.factions["town_watch"].reputation.value == -2
    assert state.rumors["rumor_1"].known_by == {"harlan"}
    assert state.crimes["crime_1"].status == "witnessed"


def test_world_loader_accepts_optional_factions_and_rumors_yaml(tmp_path: Path) -> None:
    world_path = tmp_path / "social_world"
    world_path.mkdir()
    (world_path / "manifest.yaml").write_text(
        """
world_id: social_world
name: Social World
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
    (world_path / "facts.yaml").write_text(
        """
facts:
  - id: public_notice
    text: Everyone knows the watch keeps order.
    visibility: public
    known_by: []
    tags: [law]
""",
        encoding="utf-8",
    )
    (world_path / "factions.yaml").write_text(
        """
factions:
  - id: town_watch
    name: Town Watch
    description: Local guards.
    initial_reputation: 1
    known_to_player: true
    tags: [law]
""",
        encoding="utf-8",
    )
    (world_path / "rumors.yaml").write_text(
        """
rumors:
  - id: watch_notice_rumor
    fact_id: public_notice
    text: The watch is paying attention.
    known_by: [harlan, town_watch]
    credibility: 2
    known_to_player: false
    tags: [law]
""",
        encoding="utf-8",
    )

    state = WorldLoader(tmp_path).load("social_world").to_game_state()

    assert state.factions["town_watch"].reputation.value == 1
    assert state.factions["town_watch"].reputation.known_to_player is True
    assert state.rumors["watch_notice_rumor"].known_by == {"harlan", "town_watch"}
