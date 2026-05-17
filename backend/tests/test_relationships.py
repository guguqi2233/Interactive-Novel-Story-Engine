from pathlib import Path

import pytest

from app.core.state_delta import apply_delta
from app.core.world_state import GameState, LocationState, NPCState, RelationshipState, RumorState
from app.db.repository import SQLiteSaveRepository
from app.engine.content.world_loader import WorldLoader, WorldLoaderError
from app.engine.rules.relationships import (
    build_relationship_event,
    change_trust,
    get_relationship,
    get_visible_relationships,
)
from app.engine.rules.rumors import propagate_rumors
from app.session_store import build_visible_state


def make_state() -> GameState:
    return GameState(
        world_id="relationship-test",
        locations={"square": LocationState(id="square", name="Square")},
        npcs={
            "harlan": NPCState(id="harlan", location_id="square"),
            "mira": NPCState(id="mira", location_id="square"),
            "tomas": NPCState(id="tomas", location_id="square"),
        },
        relationships={
            "harlan_mira_trust": RelationshipState(
                id="harlan_mira_trust",
                source_id="harlan",
                target_id="mira",
                relation_type="friend",
                trust=5,
                affinity=2,
                known_by_player=True,
            ),
            "harlan_tomas_distrust": RelationshipState(
                id="harlan_tomas_distrust",
                source_id="harlan",
                target_id="tomas",
                relation_type="rival",
                trust=-3,
                affinity=-1,
                known_by_player=False,
            ),
        },
    )


def test_relationships_yaml_loads() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()

    relationship = state.relationships["harlan_player_wary"]

    assert relationship.source_id == "harlan"
    assert relationship.target_id == "player"
    assert relationship.relation_type == "wary"
    assert relationship.known_by_player is True


def test_get_relationship_returns_structured_state() -> None:
    state = make_state()

    relationship = get_relationship(state, "harlan", "mira")

    assert relationship is not None
    assert relationship.trust == 5


def test_trust_change_uses_state_delta() -> None:
    state = make_state()
    [delta] = change_trust(state, "harlan", "mira", -2, "Mira broke a promise.")

    next_state = apply_delta(state, delta)

    assert delta.path == "relationships.harlan_mira_trust.trust"
    assert next_state.relationships["harlan_mira_trust"].trust == 3


def test_relationship_change_can_build_system_event() -> None:
    state = make_state()
    deltas = change_trust(state, "harlan", "mira", 1, "Mira helped Harlan.")

    event = build_relationship_event("relationship-event-1", state.turn, deltas)

    assert event.actor_id == "system"
    assert event.action_type == "relationship_change"
    assert event.state_deltas == deltas


def test_hidden_relationship_does_not_enter_visible_state() -> None:
    state = make_state()

    payload = build_visible_state(state).model_dump(mode="json")

    assert [item["id"] for item in payload["relationships"]] == ["harlan_mira_trust"]
    assert "harlan_tomas_distrust" not in str(payload)
    assert [item.id for item in get_visible_relationships(state)] == ["harlan_mira_trust"]


def test_rumor_spreads_to_high_trust_npc() -> None:
    state = make_state()
    state.rumors["bridge_rumor"] = RumorState(
        id="bridge_rumor",
        text_for_player="There is talk about the bridge.",
        known_by_npcs={"harlan"},
    )

    for delta in propagate_rumors(state):
        state = apply_delta(state, delta)

    assert "mira" in state.rumors["bridge_rumor"].known_by_npcs
    assert "tomas" not in state.rumors["bridge_rumor"].known_by_npcs


def test_low_trust_npc_does_not_receive_rumor() -> None:
    state = make_state()
    state.relationships["harlan_mira_trust"].trust = -1
    state.rumors["bridge_rumor"] = RumorState(
        id="bridge_rumor",
        text_for_player="There is talk about the bridge.",
        known_by_npcs={"harlan"},
    )

    assert propagate_rumors(state) == []


def test_save_load_preserves_relationships(tmp_path: Path) -> None:
    state = make_state()
    repository = SQLiteSaveRepository(tmp_path / "relationships.db")

    repository.create_save("save-1", state)
    loaded = repository.load_save("save-1")

    assert loaded.relationships == state.relationships


def test_invalid_relationship_npc_id_fails(tmp_path: Path) -> None:
    world_path = tmp_path / "bad_relationship"
    world_path.mkdir()
    (world_path / "manifest.yaml").write_text(
        """
world_id: bad_relationship
name: Bad Relationship
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
    (world_path / "relationships.yaml").write_text(
        """
relationships:
  - source_id: harlan
    target_id: missing_npc
    relation_type: rival
""",
        encoding="utf-8",
    )

    with pytest.raises(WorldLoaderError, match="target_id references missing NPC id"):
        WorldLoader(tmp_path).load("bad_relationship")
