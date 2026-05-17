from pathlib import Path

import pytest

from app.core.state_delta import apply_delta
from app.core.world_state import FactionState, GameState, ReputationState
from app.db.repository import SQLiteSaveRepository
from app.engine.content.world_loader import WorldLoader, WorldLoaderError
from app.engine.rules.factions import (
    FactionRuleError,
    ReputationBand,
    build_reputation_event,
    change_reputation,
    get_reputation,
    get_visible_factions,
    reputation_band,
    set_reputation,
)
from app.session_store import build_visible_state


def make_state() -> GameState:
    return GameState(
        world_id="faction-test",
        factions={
            "village_council": FactionState(
                id="village_council",
                name="Village Council",
                reputation=ReputationState(value=0, known_to_player=True),
            ),
            "hidden_circle": FactionState(
                id="hidden_circle",
                name="Hidden Circle",
                reputation=ReputationState(value=-20, known_to_player=False),
            ),
        },
    )


def test_mist_valley_factions_yaml_loads() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()

    assert state.factions["village_council"].name == "Village Council"
    assert state.factions["village_council"].reputation.value == 0
    assert state.factions["village_council"].reputation.known_to_player is True
    assert state.factions["old_road_smugglers"].reputation.known_to_player is False
    assert state.npcs["harlan"].faction_id == "village_council"


def test_default_reputation_enters_game_state(tmp_path: Path) -> None:
    write_faction_world(tmp_path)

    state = WorldLoader(tmp_path).load("faction_world").to_game_state()

    assert state.factions["watch"].reputation.value == 12
    assert state.factions["watch"].reputation.known_to_player is True


def test_change_reputation_returns_state_deltas() -> None:
    state = make_state()

    for delta in change_reputation(state, "village_council", 5, "helped with repairs"):
        state = apply_delta(state, delta)

    assert get_reputation(state, "village_council") == 5
    assert "helped with repairs" in state.factions["village_council"].reputation.recent_reasons


def test_reputation_change_can_be_recorded_as_event() -> None:
    state = make_state()
    deltas = change_reputation(state, "village_council", 5, "helped with repairs")

    event = build_reputation_event(
        event_id="rep-event-1",
        turn=state.turn,
        faction_id="village_council",
        state_deltas=deltas,
        visible_to_player=True,
    )

    assert event.actor_id == "system"
    assert event.action_type == "faction_reputation_changed"
    assert event.target_id == "village_council"
    assert event.state_deltas == deltas
    assert event.visible_to_player is True


def test_set_reputation_returns_state_deltas() -> None:
    state = make_state()

    for delta in set_reputation(state, "village_council", 30, "formal pardon"):
        state = apply_delta(state, delta)

    assert get_reputation(state, "village_council") == 30
    assert "formal pardon" in state.factions["village_council"].reputation.recent_reasons


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-50, ReputationBand.HOSTILE),
        (-10, ReputationBand.SUSPICIOUS),
        (0, ReputationBand.NEUTRAL),
        (25, ReputationBand.FRIENDLY),
        (60, ReputationBand.TRUSTED),
    ],
)
def test_reputation_band(value: int, expected: ReputationBand) -> None:
    assert reputation_band(value) == expected


def test_hidden_faction_does_not_enter_visible_state() -> None:
    state = make_state()

    visible_state = build_visible_state(state)
    visible_factions = visible_state.model_dump(mode="json")["factions"]

    assert [faction["id"] for faction in visible_factions] == ["village_council"]
    assert "hidden_circle" not in str(visible_state)
    assert "Hidden Circle" not in str(visible_state)


def test_get_visible_factions_returns_known_factions_only() -> None:
    visible_factions = get_visible_factions(make_state())

    assert [faction.id for faction in visible_factions] == ["village_council"]
    assert visible_factions[0].band == ReputationBand.NEUTRAL


def test_save_load_preserves_reputation(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "factions.db")
    state = make_state()
    for delta in change_reputation(state, "village_council", -15, "reported lockpicking"):
        state = apply_delta(state, delta)

    repository.create_save("save-1", state)
    loaded = repository.load_save("save-1")

    assert loaded.factions["village_council"].reputation.value == -15
    assert loaded.factions["village_council"].reputation.recent_reasons == ["reported lockpicking"]


def test_invalid_faction_id_errors_clearly() -> None:
    with pytest.raises(FactionRuleError, match="Unknown faction_id: missing"):
        change_reputation(make_state(), "missing", 1, "no such faction")


def test_npc_missing_faction_reference_errors(tmp_path: Path) -> None:
    write_faction_world(tmp_path, npc_faction_id="missing_faction")

    with pytest.raises(WorldLoaderError, match="NPC harlan references missing faction_id: missing_faction"):
        WorldLoader(tmp_path).load("faction_world")


def write_faction_world(tmp_path: Path, npc_faction_id: str = "watch") -> None:
    world_path = tmp_path / "faction_world"
    world_path.mkdir()
    (world_path / "manifest.yaml").write_text(
        """
world_id: faction_world
name: Faction World
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
        f"""
npcs:
  - id: harlan
    name: Harlan
    location_id: square
    faction_id: {npc_faction_id}
    personality: careful
    knowledge: []
""",
        encoding="utf-8",
    )
    (world_path / "factions.yaml").write_text(
        """
factions:
  - id: watch
    name: Watch
    description: Local guards.
    default_reputation: 12
    known_by_player: true
    tags: [law]
""",
        encoding="utf-8",
    )
