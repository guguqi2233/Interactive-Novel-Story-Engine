from app.engine.actions.schemas import SuccessLevel
from app.playtesting.gameplay_module_regression import (
    GameplayModuleRegressionScenario,
    GameplayModuleRegressionScenarioType,
    run_gameplay_module_regression,
    sample_gameplay_module_regression_scenarios,
)


def test_magic_action_scenario_passes() -> None:
    scenario = GameplayModuleRegressionScenario(
        id="magic-success",
        scenario_type=GameplayModuleRegressionScenarioType.ACTION_SUCCESS,
        module_id="magic",
        action_id="magic.cast_spell",
        input_sequence=["cast spark"],
        expected_result=SuccessLevel.SUCCESS.value,
        expected_deltas=["magic_resources.player.mana", "npcs.guard.hp"],
        seed=1,
    )

    report = run_gameplay_module_regression([scenario])

    assert report.passed is True
    assert report.case_results[0].event_ids
    assert report.calls_real_llm is False
    assert report.modifies_real_save is False


def test_hacking_failure_scenario_passes() -> None:
    scenario = GameplayModuleRegressionScenario(
        id="hacking-failure",
        scenario_type=GameplayModuleRegressionScenarioType.ACTION_FAILURE,
        module_id="hacking",
        action_id="hacking.hack_terminal",
        input_sequence=["hack terminal"],
        expected_result=SuccessLevel.FAILURE.value,
        expected_deltas=["hackables.terminal.intrusion_trace", "hackables.terminal.alarm_level"],
        seed=1,
    )

    report = run_gameplay_module_regression([scenario])

    assert report.passed is True
    assert "hackables.terminal.intrusion_trace" in report.case_results[0].delta_paths


def test_crafting_missing_material_scenario_passes() -> None:
    scenario = GameplayModuleRegressionScenario(
        id="crafting-missing-material",
        scenario_type=GameplayModuleRegressionScenarioType.ACTION_FAILURE,
        module_id="crafting",
        action_id="crafting.craft_item",
        input_sequence=["craft chair"],
        expected_result=SuccessLevel.FAILURE.value,
        expected_deltas=[],
        seed=1,
    )

    report = run_gameplay_module_regression([scenario])

    assert report.passed is True
    assert report.case_results[0].result == SuccessLevel.FAILURE.value


def test_hidden_target_scenario_does_not_leak() -> None:
    scenario = GameplayModuleRegressionScenario(
        id="hidden-log",
        scenario_type=GameplayModuleRegressionScenarioType.HIDDEN_TARGET,
        module_id="hacking",
        action_id="hacking.access_logs",
        input_sequence=["access logs"],
        expected_result=SuccessLevel.SUCCESS.value,
        expected_deltas=["player_visible_facts"],
        forbidden_visible_facts=["hidden_root_log", "Root key is buried under admin"],
        seed=1,
    )

    report = run_gameplay_module_regression([scenario])

    assert report.passed is True
    assert report.case_results[0].forbidden_visible_fact_hits == []
    assert "Root key is buried under admin" not in str(report.model_dump_normal())


def test_save_load_scenario_passes() -> None:
    scenario = GameplayModuleRegressionScenario(
        id="magic-save-load",
        scenario_type=GameplayModuleRegressionScenarioType.SAVE_LOAD,
        module_id="magic",
        action_id="magic.cast_spell",
        input_sequence=["cast spark"],
        expected_result=SuccessLevel.SUCCESS.value,
        expected_deltas=["magic_resources.player.mana"],
        seed=1,
    )

    report = run_gameplay_module_regression([scenario])

    assert report.passed is True
    assert report.case_results[0].save_load_passed is True


def test_replay_scenario_is_deterministic() -> None:
    scenario = GameplayModuleRegressionScenario(
        id="magic-replay",
        scenario_type=GameplayModuleRegressionScenarioType.REPLAY,
        module_id="magic",
        action_id="magic.cast_spell",
        input_sequence=["cast spark"],
        expected_result=SuccessLevel.SUCCESS.value,
        expected_deltas=["magic_resources.player.mana"],
        seed=1,
    )

    first = run_gameplay_module_regression([scenario])
    second = run_gameplay_module_regression([scenario])

    assert first.passed is True
    assert second.passed is True
    assert first.case_results[0].delta_paths == second.case_results[0].delta_paths
    assert first.case_results[0].replay_passed is True


def test_sample_gameplay_module_regression_suite_passes() -> None:
    report = run_gameplay_module_regression(sample_gameplay_module_regression_scenarios())

    assert report.passed is True
    assert report.summary["total"] == 6
    assert report.summary["calls_real_llm"] is False
