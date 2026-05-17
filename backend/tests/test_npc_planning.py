from random import Random
from pathlib import Path

from app.core.state_delta import apply_delta
from app.core.world_state import (
    ActorCondition,
    CrimeState,
    CrimeStatus,
    GameState,
    LocationState,
    NPCGoalState,
    NPCGoalStatus,
    NPCState,
    RumorState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.rules.npc_planning import choose_plan_for_npc, resolve_npc_planning_tick
from app.engine.rules.world_tick import run_world_tick
from app.session_store import build_visible_state


def make_state() -> GameState:
    return GameState(
        world_id="npc-planning-test",
        locations={
            "square": LocationState(id="square", name="Square", exits={"east": "forge"}),
            "forge": LocationState(id="forge", name="Forge", exits={"west": "square"}),
        },
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                knowledge=["public_fact"],
                goals=[
                    NPCGoalState(
                        id="guard_square",
                        description="Guard the square.",
                        priority=5,
                        status=NPCGoalStatus.ACTIVE,
                        conditions=["knows:public_fact"],
                        allowed_actions=["guard_location"],
                    )
                ],
            ),
            "mira": NPCState(id="mira", location_id="square"),
        },
        npc_knowledge={"harlan": {"public_fact"}},
    )


def apply_all(state: GameState, deltas):
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_npc_with_active_goal_selects_legal_planning_action() -> None:
    state = make_state()

    step = choose_plan_for_npc(state, "harlan")

    assert step is not None
    assert step.plan_type == "guard_location"
    assert step.goal_id == "guard_square"


def test_npc_without_crime_knowledge_does_not_report_crime() -> None:
    state = make_state()
    state.crimes["crime-1"] = CrimeState(
        id="crime-1",
        crime_type="theft",
        location_id="square",
        actor_id="player",
        severity=2,
        status=CrimeStatus.WITNESSED,
        witnessed_by=["mira"],
        created_turn=1,
    )

    step = choose_plan_for_npc(state, "harlan")

    assert step is not None
    assert step.plan_type != "report_crime"


def test_npc_knowing_crime_can_report_crime() -> None:
    state = make_state()
    state.npcs["harlan"].goals = []
    state.npcs["harlan"].knowledge.append("crime:crime-1")
    state.crimes["crime-1"] = CrimeState(
        id="crime-1",
        crime_type="theft",
        location_id="square",
        actor_id="player",
        severity=2,
        status=CrimeStatus.WITNESSED,
        witnessed_by=["mira"],
        created_turn=1,
    )

    result = resolve_npc_planning_tick(state)
    next_state = apply_all(state, result.state_deltas)

    assert next_state.crimes["crime-1"].status == CrimeStatus.REPORTED
    assert result.events


def test_npc_knowing_rumor_can_spread_rumor() -> None:
    state = make_state()
    state.npcs["harlan"].goals = [
        NPCGoalState(
            id="share_rumor",
            priority=5,
            status=NPCGoalStatus.ACTIVE,
            allowed_actions=["spread_rumor"],
        )
    ]
    state.rumors["rumor-1"] = RumorState(
        id="rumor-1",
        text_for_player="A safe rumor.",
        known_by_npcs={"harlan"},
    )

    result = resolve_npc_planning_tick(state)
    next_state = apply_all(state, result.state_deltas)

    assert "mira" in next_state.rumors["rumor-1"].known_by_npcs
    assert any(delta.path == "rumors.rumor-1.spread_level" for delta in result.state_deltas)


def test_injured_npc_can_rest_if_injured() -> None:
    state = make_state()
    state.npcs["harlan"].condition = ActorCondition.WOUNDED

    result = resolve_npc_planning_tick(state)
    next_state = apply_all(state, result.state_deltas)

    assert next_state.npcs["harlan"].current_activity == "resting"
    assert "resting" in next_state.npcs["harlan"].status_effects


def test_dead_or_incapacitated_npc_does_not_plan() -> None:
    state = make_state()
    state.npcs["harlan"].alive = False
    state.npcs["harlan"].condition = ActorCondition.DEAD

    result = resolve_npc_planning_tick(state)

    assert result.state_deltas == []
    assert result.events == []


def test_world_tick_runs_planning_and_records_system_event() -> None:
    state = make_state()

    result = run_world_tick(state, Random(1))

    assert result.event is not None
    assert result.event.action_type == "world_tick"
    assert any(delta.metadata.get("source") == "npc_planning" for delta in result.state_deltas)


def test_hidden_npc_planning_does_not_leak_to_player_visible_state() -> None:
    state = make_state()
    state.npcs["harlan"].hidden = True
    state.npcs["harlan"].visible = True

    result = resolve_npc_planning_tick(state)
    next_state = apply_all(state, result.state_deltas)
    visible_state = build_visible_state(next_state)

    assert "harlan" not in visible_state.model_dump_json()


def test_save_load_after_planning_still_works(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(Path(tmp_path) / "npc_planning.db")
    state = make_state()
    result = resolve_npc_planning_tick(state)
    next_state = apply_all(state, result.state_deltas)

    repository.save_snapshot("save-1", next_state, result.events)
    loaded = repository.load_save("save-1")
    loaded_result = resolve_npc_planning_tick(loaded)

    assert loaded.npcs["harlan"].current_activity == "guarding:square"
    assert loaded_result.state_deltas
