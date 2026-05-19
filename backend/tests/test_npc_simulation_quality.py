import json

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    ActorCondition,
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    NPCIntent,
    NPCPlan,
    NPCPlanStep,
    NPCPlanStatus,
    NPCState,
)
from app.engine.rules.npc_simulation_tick import NPCSimulationTickDebugEntry, NPCSimulationTickResult
from app.quality.npc_simulation_quality import analyze_npc_simulation_quality


def _state() -> GameState:
    return GameState(
        world_id="test_world",
        locations={"square": LocationState(id="square", name="Square")},
        npcs={
            "harlan": NPCState(id="harlan", location_id="square", knowledge=["public_fact"]),
            "dead_npc": NPCState(
                id="dead_npc",
                location_id="square",
                alive=False,
                condition=ActorCondition.DEAD,
            ),
        },
        facts={
            "public_fact": FactState(id="public_fact", text="The bridge is old.", visibility=FactVisibility.PUBLIC),
            "hidden_fact": FactState(
                id="hidden_fact",
                text="The duke poisoned the well.",
                visibility=FactVisibility.HIDDEN,
                secret=True,
            ),
        },
        npc_knowledge={"harlan": {"public_fact"}, "dead_npc": set()},
    )


def _event(
    event_id: str,
    *,
    npc_id: str = "harlan",
    action_type: str = "npc_simulation",
    result: str = "ok",
    visible_to_player: bool = False,
    delta: StateDelta | None = None,
    narrative_text: str | None = None,
) -> Event:
    return Event(
        event_id=event_id,
        turn=1,
        actor_id="system",
        target_id=npc_id,
        action_type=action_type,
        result=result,
        visible_to_player=visible_to_player,
        narrative_text=narrative_text,
        state_deltas=[
            delta
            or StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"npcs.{npc_id}.current_activity",
                value=result,
                reason="test",
                metadata={"source": "npc_simulation", "npc_id": npc_id},
            )
        ],
    )


def test_unknown_fact_usage_is_caught() -> None:
    state = _state()
    event = _event(
        "unknown-fact",
        delta=StateDelta(
            operation=StateDeltaOperation.SET,
            path="npcs.harlan.current_activity",
            value="acting",
            reason="used fact",
            metadata={"source": "npc_simulation", "npc_id": "harlan", "fact_id": "hidden_fact"},
        ),
    )

    report = analyze_npc_simulation_quality(state, events=[event])

    assert report.npc_unknown_fact_used
    assert report.npc_unknown_fact_used[0].safe_details["fact_id"] == "hidden_fact"


def test_dead_npc_acted_is_caught() -> None:
    state = _state()

    report = analyze_npc_simulation_quality(state, events=[_event("dead-action", npc_id="dead_npc")])

    assert report.dead_npc_actions
    assert report.dead_npc_actions[0].entity_id == "dead_npc"


def test_repeated_intent_loop_is_caught() -> None:
    state = _state()
    state.npcs["harlan"].intent_queue = [
        NPCIntent(
            id=f"repeat-{index}",
            npc_id="harlan",
            intent_type="spread_rumor",
            priority=1,
            target_id="player",
            target_type="npc",
            created_turn=index,
        )
        for index in range(5)
    ]

    report = analyze_npc_simulation_quality(state, repeated_intent_threshold=3)

    assert report.repeated_intent_loops
    assert report.repeated_intent_loops[0].safe_details["intent_type"] == "spread_rumor"


def test_hidden_leak_is_caught_and_normal_report_redacts_hidden_text() -> None:
    state = _state()
    event = _event(
        "hidden-leak",
        visible_to_player=True,
        narrative_text="The duke poisoned the well.",
    )

    report = analyze_npc_simulation_quality(state, events=[event])
    normal_payload = json.dumps(report.model_dump_normal(), ensure_ascii=False, sort_keys=True)
    debug_payload = json.dumps(report.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)

    assert report.hidden_fact_leaks
    assert "The duke poisoned the well." not in normal_payload
    assert "The duke poisoned the well." in debug_payload


def test_plan_budget_exceeded_is_caught() -> None:
    state = _state()
    tick = NPCSimulationTickResult(
        budget_exhausted=True,
        debug_output=[NPCSimulationTickDebugEntry(npc_id="system", phase="budget", detail="max_plan_steps_per_tick")],
    )

    report = analyze_npc_simulation_quality(state, tick_results=[tick])

    assert report.plan_budget_exceeded


def test_invalid_target_blocked_plan_and_missing_event_are_caught() -> None:
    state = _state()
    state.npcs["harlan"].plans = [
        NPCPlan(
            id="blocked-plan",
            npc_id="harlan",
            source_intent_id="intent-1",
            status=NPCPlanStatus.BLOCKED,
            steps=[
                NPCPlanStep(
                    step_type="move",
                    target_id="missing_location",
                    preconditions=[],
                    expected_result="move",
                )
            ],
        )
    ]
    tick = NPCSimulationTickResult(
        state_deltas=[
            StateDelta(
                operation=StateDeltaOperation.SET,
                path="npcs.harlan.current_activity",
                value="acting",
                reason="missing event",
                metadata={"source": "npc_simulation", "npc_id": "harlan"},
            )
        ],
        events=[],
    )
    events = [
        _event(
            f"blocked-{index}",
            result="blocked",
            delta=StateDelta(
                operation=StateDeltaOperation.SET,
                path="npcs.harlan.plans",
                value=[],
                reason="blocked",
                metadata={"source": "npc_plan", "npc_id": "harlan", "plan_id": "blocked-plan", "status": "blocked"},
            ),
        )
        for index in range(3)
    ]

    report = analyze_npc_simulation_quality(state, events=events, tick_results=[tick], blocked_plan_threshold=2)

    assert report.invalid_targets
    assert report.blocked_plan_loops
    assert report.no_event_recorded
