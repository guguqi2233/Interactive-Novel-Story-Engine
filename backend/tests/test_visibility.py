from app.core.world_state import GameState, LocationState, PlayerState, WorldObjectState
from app.engine.rules.visibility import get_visible_facts


def make_state() -> GameState:
    return GameState(
        world_id="visibility-test",
        player=PlayerState(id="player", location_id="square"),
        locations={
            "square": LocationState(id="square", name="Town Square"),
            "cellar": LocationState(id="cellar", name="Cellar"),
        },
        objects={
            "lamp": WorldObjectState(id="lamp", location_id="square"),
            "trapdoor": WorldObjectState(
                id="trapdoor",
                location_id="square",
                hidden=True,
            ),
            "loose_brick": WorldObjectState(
                id="loose_brick",
                location_id="square",
                hidden=True,
                discovered_by=["player"],
            ),
            "cellar_note": WorldObjectState(id="cellar_note", location_id="cellar"),
        },
        npc_knowledge={"harlan": {"trapdoor"}},
        player_visible_facts={"lamp"},
    )


def test普通对象可见() -> None:
    facts = get_visible_facts(make_state(), actor_id="player", location_id="square")

    assert "lamp" in facts


def test_hidden_object_is_not_visible_by_default() -> None:
    facts = get_visible_facts(make_state(), actor_id="player", location_id="square")

    assert "trapdoor" not in facts


def test_discovered_hidden_object_is_visible() -> None:
    facts = get_visible_facts(make_state(), actor_id="player", location_id="square")

    assert "loose_brick" in facts


def test_object_in_other_location_is_not_visible() -> None:
    facts = get_visible_facts(make_state(), actor_id="player", location_id="square")

    assert "cellar_note" not in facts


def test_npc_knowledge_does_not_make_fact_visible_to_player() -> None:
    facts = get_visible_facts(make_state(), actor_id="player", location_id="square")

    assert "trapdoor" not in facts

