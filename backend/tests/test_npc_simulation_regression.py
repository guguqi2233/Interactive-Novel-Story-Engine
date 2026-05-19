from app.core.world_state import CrimeState, CrimeStatus, NPCIntent, NPCState
from app.playtesting.npc_simulation_regression import (
    NPCSimulationRegressionScenario,
    NPCSimulationRegressionScenarioType,
    run_npc_simulation_regression_suite,
)


def _run(scenario: NPCSimulationRegressionScenario):
    report = run_npc_simulation_regression_suite([scenario])
    return report.case_results[0]


def test_guard_patrol_scenario_passes() -> None:
    result = _run(
        NPCSimulationRegressionScenario(
            id="guard",
            name="Guard",
            scenario_type=NPCSimulationRegressionScenarioType.GUARD_PATROL,
            expected_intents=["guard_location"],
            expected_events=["npc_faction_duty", "npc_plan_built"],
            forbidden_visible_facts=["hidden_plot"],
        )
    )

    assert result.passed
    assert "guard_location" in result.observed_intents


def test_report_crime_scenario_passes() -> None:
    result = _run(
        NPCSimulationRegressionScenario(
            id="report",
            name="Report",
            scenario_type=NPCSimulationRegressionScenarioType.REPORT_CRIME,
            expected_intents=["report_crime"],
            expected_events=["npc_faction_duty"],
            forbidden_visible_facts=["hidden_plot"],
        )
    )

    assert result.passed
    assert "report_crime" in result.observed_intents


def test_unknown_crime_does_not_report() -> None:
    base = NPCSimulationRegressionScenario(
        id="unknown-crime-base",
        name="Unknown crime base",
        scenario_type=NPCSimulationRegressionScenarioType.GUARD_PATROL,
    )
    from app.playtesting.npc_simulation_regression import _initial_state_for_scenario

    state = _initial_state_for_scenario(base)
    state.crimes["unknown_theft"] = CrimeState(
        id="unknown_theft",
        crime_type="theft",
        actor_id="player",
        location_id="square",
        status=CrimeStatus.WITNESSED,
    )
    scenario = NPCSimulationRegressionScenario(
        id="unknown-crime",
        name="Unknown crime",
        scenario_type=NPCSimulationRegressionScenarioType.REPORT_CRIME,
        initial_state=state.model_dump(mode="json"),
        forbidden_intents=["report_crime"],
        forbidden_visible_facts=["hidden_plot"],
    )

    result = _run(scenario)

    assert result.passed
    assert "report_crime" not in result.observed_intents


def test_avoid_player_scenario_does_not_leak_hidden_npc() -> None:
    result = _run(
        NPCSimulationRegressionScenario(
            id="avoid",
            name="Avoid",
            scenario_type=NPCSimulationRegressionScenarioType.AVOID_PLAYER,
            expected_intents=["avoid_actor"],
            forbidden_visible_facts=["hidden_plot"],
        )
    )
    normal_payload = result.model_dump_normal()

    assert result.passed
    assert "avoid_actor" in result.observed_intents
    assert "hidden_spy" not in str(normal_payload)


def test_daily_replan_is_deterministic() -> None:
    scenario = NPCSimulationRegressionScenario(
        id="daily",
        name="Daily",
        scenario_type=NPCSimulationRegressionScenarioType.DAILY_REPLAN,
        expected_intents=["guard_location"],
        expected_events=["npc_daily_replanning"],
        forbidden_visible_facts=["hidden_plot"],
    )

    first = _run(scenario)
    second = _run(scenario)

    assert first.passed
    assert second.passed
    assert first.observed_intents == second.observed_intents
    assert first.observed_events == second.observed_events


def test_repeated_loop_is_reported() -> None:
    from app.playtesting.npc_simulation_regression import _initial_state_for_scenario

    state = _initial_state_for_scenario(
        NPCSimulationRegressionScenario(
            id="loop-base",
            name="Loop base",
            scenario_type=NPCSimulationRegressionScenarioType.GUARD_PATROL,
        )
    )
    state.npcs["guard"].intent_queue = [
        NPCIntent(
            id=f"loop-{index}",
            npc_id="guard",
            intent_type="spread_rumor",
            target_id="villager",
            target_type="npc",
            created_turn=index,
        )
        for index in range(5)
    ]
    scenario = NPCSimulationRegressionScenario(
        id="loop",
        name="Loop",
        scenario_type=NPCSimulationRegressionScenarioType.SPREAD_RUMOR,
        initial_state=state.model_dump(mode="json"),
    )

    result = _run(scenario)

    assert not result.passed
    assert "quality:repeated_intent_loop" in result.failure_reasons


def test_save_load_after_regression_continues_normally() -> None:
    result = _run(
        NPCSimulationRegressionScenario(
            id="save-load",
            name="Save Load",
            scenario_type=NPCSimulationRegressionScenarioType.INJURED_REST,
            expected_intents=["rest"],
            forbidden_visible_facts=["hidden_plot"],
            turns_to_run=2,
        )
    )

    assert result.passed
    assert result.save_load_failure is None
    assert result.turns_run >= 2
