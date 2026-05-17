from random import Random

from app.core.state_delta import apply_delta
from app.core.world_state import (
    ActorCondition,
    CrimeState,
    CrimeStatus,
    FactionState,
    GameState,
    LocationState,
    NPCState,
    ReputationState,
    RumorState,
)
from app.engine.rules.npc_reactions import resolve_npc_reactions
from app.engine.rules.world_tick import run_world_tick
from app.session_store import build_visible_state


def make_reaction_state(hidden_npc: bool = False) -> GameState:
    return GameState(
        world_id="reaction-test",
        locations={
            "square": LocationState(id="square", name="Square", exits={"east": "road"}),
            "road": LocationState(id="road", name="Road"),
        },
        player={"location_id": "square"},
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                faction_id="watch",
                hidden=hidden_npc,
            )
        },
        factions={
            "watch": FactionState(
                id="watch",
                name="Watch",
                reputation=ReputationState(value=0, known_to_player=True),
            )
        },
    )


def apply_reactions(state: GameState) -> GameState:
    for delta in resolve_npc_reactions(state):
        state = apply_delta(state, delta)
    return state


def test_witnessed_theft_increases_suspicion() -> None:
    state = make_reaction_state()
    state.crimes["crime_1"] = CrimeState(
        id="crime_1",
        crime_type="theft",
        actor_id="player",
        location_id="square",
        witnessed_by=["harlan"],
        witness_ids=["harlan"],
        severity=2,
        status=CrimeStatus.WITNESSED,
    )

    state = apply_reactions(state)

    assert state.npcs["harlan"].suspicion == 2
    assert state.social_flags["npc_reaction_harlan_increase_suspicion_crime_crime_1"] is True


def test_hostile_reputation_makes_npc_hostile_and_refuse_talk() -> None:
    state = make_reaction_state()
    state.factions["watch"].reputation.value = -60

    state = apply_reactions(state)

    assert state.npcs["harlan"].mood == "hostile"
    assert "player" in state.npcs["harlan"].hostile_to
    assert "refuse_talk" in state.npcs["harlan"].status_effects


def test_npc_knowing_rumor_adds_spread_goal() -> None:
    state = make_reaction_state()
    state.rumors["rumor_1"] = RumorState(
        id="rumor_1",
        text_for_player="A rumor.",
        known_by_npcs={"harlan"},
    )

    state = apply_reactions(state)

    assert "spread_rumor" in state.npcs["harlan"].goals


def test_npc_without_rumor_does_not_spread_unknown_rumor() -> None:
    state = make_reaction_state()
    state.rumors["rumor_1"] = RumorState(
        id="rumor_1",
        text_for_player="A rumor.",
        known_by_npcs=set(),
    )

    state = apply_reactions(state)

    assert "spread_rumor" not in state.npcs["harlan"].goals


def test_injured_npc_can_flee() -> None:
    state = make_reaction_state()
    state.npcs["harlan"].condition = ActorCondition.WOUNDED
    state.npcs["harlan"].hp = 5

    state = apply_reactions(state)

    assert state.npcs["harlan"].location_id == "road"
    assert state.npcs["harlan"].combat_stance == "fleeing"


def test_dead_or_incapacitated_npc_does_not_react() -> None:
    state = make_reaction_state()
    state.npcs["harlan"].condition = ActorCondition.DEAD
    state.npcs["harlan"].alive = False
    state.factions["watch"].reputation.value = -60
    state.rumors["rumor_1"] = RumorState(id="rumor_1", text_for_player="A rumor.", known_by_npcs={"harlan"})

    state = apply_reactions(state)

    assert state.npcs["harlan"].mood == "neutral"
    assert state.npcs["harlan"].goals == []
    assert state.social_flags == {}


def test_reaction_generates_system_event_through_world_tick() -> None:
    state = make_reaction_state()
    state.factions["watch"].reputation.value = -60

    tick = run_world_tick(state, Random(0))

    assert tick.event is not None
    assert tick.event.actor_id == "system"
    assert any(delta.metadata.get("source") == "npc_reaction" for delta in tick.event.state_deltas)


def test_hidden_npc_reaction_does_not_enter_visible_state() -> None:
    state = make_reaction_state(hidden_npc=True)
    state.factions["watch"].reputation.value = -60

    state = apply_reactions(state)
    visible_state = build_visible_state(state)

    assert "harlan" not in visible_state.model_dump_json()


def test_reaction_does_not_repeat_for_same_source() -> None:
    state = make_reaction_state()
    state.factions["watch"].reputation.value = -60

    state = apply_reactions(state)
    first_flags = dict(state.social_flags)
    state = apply_reactions(state)

    assert state.social_flags == first_flags
    assert state.npcs["harlan"].hostile_to == ["player"]
