from random import Random

from app.core.world_state import FactState, GameState, LocationState, NPCState, PlayerState
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.rules.knowledge import (
    add_npc_knowledge,
    get_npc_context_for_dialogue,
    npc_knows,
)
from app.llm.schemas import PlayerActionType, PlayerIntent


def make_state() -> GameState:
    return GameState(
        world_id="knowledge-test",
        player=PlayerState(location_id="smithy"),
        locations={"smithy": LocationState(id="smithy", name="Smithy")},
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="smithy",
                mood="wary",
                relationship_to_player=-1,
                knowledge=["forge_is_cold"],
                goals=["recover_missing_tools"],
                secrets=["stole_mayors_key"],
            )
        },
        npc_knowledge={"harlan": {"old_bridge_creaks"}},
        facts={
            "old_bridge_creaks": FactState(
                id="old_bridge_creaks",
                public=True,
            ),
            "stole_mayors_key": FactState(
                id="stole_mayors_key",
                secret=True,
                known_by={"harlan"},
            ),
        },
        player_visible_facts={"forge_is_cold"},
    )


def test_npc_unknown_fact_is_not_in_dialogue_context() -> None:
    context = get_npc_context_for_dialogue(make_state(), "harlan")

    assert "missing_tunnel" not in context.knowledge
    assert npc_knows(make_state(), "harlan", "missing_tunnel") is False


def test_add_npc_knowledge_makes_fact_known() -> None:
    state = add_npc_knowledge(make_state(), "harlan", "missing_tunnel")
    context = get_npc_context_for_dialogue(state, "harlan")

    assert npc_knows(state, "harlan", "missing_tunnel") is True
    assert "missing_tunnel" in context.knowledge


def test_secrets_are_hidden_by_default() -> None:
    context = get_npc_context_for_dialogue(make_state(), "harlan")

    assert "stole_mayors_key" not in context.knowledge
    assert "stole_mayors_key" not in context.model_dump_json()


def test_secret_can_enter_context_after_public_fact() -> None:
    state = make_state().model_copy(deep=True)
    state.npcs["harlan"].knowledge.append("stole_mayors_key")
    state.player_visible_facts.add("stole_mayors_key")

    context = get_npc_context_for_dialogue(state, "harlan")

    assert "stole_mayors_key" in context.knowledge


def test_secret_fact_in_knowledge_is_hidden_even_if_not_in_npc_secrets() -> None:
    state = make_state()
    state.npcs["harlan"].secrets = []
    state.npcs["harlan"].knowledge.append("stole_mayors_key")

    context = get_npc_context_for_dialogue(state, "harlan")

    assert "stole_mayors_key" not in context.knowledge


def test_talk_does_not_leak_hidden_facts() -> None:
    state = make_state()
    state.npcs["harlan"].knowledge.append("stole_mayors_key")
    intent = PlayerIntent(
        action_type=PlayerActionType.TALK,
        target_id="harlan",
        raw_text="和哈兰谈话",
        confidence=0.9,
        requires_clarification=False,
    )

    result = ActionDispatcher().resolve(intent, state, Random(1))

    assert "forge_is_cold" in str(result.visible_facts)
    assert "old_bridge_creaks" in str(result.visible_facts)
    assert "stole_mayors_key" not in str(result.visible_facts)
    assert "secrets" not in str(result.visible_facts)
