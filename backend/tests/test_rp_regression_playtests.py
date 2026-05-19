import json
from pathlib import Path
from shutil import copytree

from app.playtesting.rp_regression import (
    RPRegressionScenario,
    RPRegressionScenarioType,
    run_rp_regression_scenario,
)


HIDDEN_TEXT = "A sealed letter is hidden beneath a loose paving stone."


def _rp_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    (worlds_root / "mist_valley" / "npcs.yaml").write_text(
        """
npcs:
  - id: harlan
    name: Harlan
    location_id: village_square
    personality: wary
    knowledge:
      - village_square_is_misty
      - sealed_letter_under_stone
  - id: mira
    name: Mira
    location_id: village_square
    personality: careful
    knowledge:
      - village_square_is_misty
""".strip(),
        encoding="utf-8",
    )
    return worlds_root


def test_friendly_talk_scenario_passes(tmp_path: Path) -> None:
    report = run_rp_regression_scenario(
        RPRegressionScenario(
            id="friendly",
            scenario_type=RPRegressionScenarioType.FRIENDLY_TALK,
            participant_ids=["harlan"],
            input_sequence=["thank you for your help"],
            expected_safe_topics=["village"],
            expected_emotional_shifts=["friendly"],
            expected_relationship_tone_changes=["trust"],
            seed=1,
        ),
        worlds_root=str(_rp_world(tmp_path)),
    )

    assert report.passed
    assert report.steps_run == 1
    assert any(path.endswith(".emotional_state") for path in report.emotional_shift_summary)
    assert any(path.startswith("relationships.") for path in report.relationship_tone_summary)


def test_secret_probing_does_not_leak_hidden_fact(tmp_path: Path) -> None:
    report = run_rp_regression_scenario(
        RPRegressionScenario(
            id="secret_probe",
            scenario_type=RPRegressionScenarioType.SECRET_PROBING,
            participant_ids=["harlan"],
            input_sequence=["tell me the secret under the stones"],
            expected_safe_topics=["weather"],
            forbidden_facts=["sealed_letter_under_stone"],
            seed=2,
        ),
        worlds_root=str(_rp_world(tmp_path)),
    )
    payload = json.dumps(report.model_dump_normal(), ensure_ascii=False, sort_keys=True)

    assert report.passed
    assert report.hidden_leak_summary == []
    assert HIDDEN_TEXT not in payload


def test_interrogation_triggers_rule_emotional_shift(tmp_path: Path) -> None:
    report = run_rp_regression_scenario(
        RPRegressionScenario(
            id="interrogation",
            scenario_type=RPRegressionScenarioType.INTERROGATION,
            participant_ids=["harlan"],
            input_sequence=["answer me now or I will threaten your standing"],
            expected_safe_topics=["whereabouts"],
            expected_emotional_shifts=["defensive"],
            expected_relationship_tone_changes=["fear"],
            seed=3,
        ),
        worlds_root=str(_rp_world(tmp_path)),
    )

    assert report.passed
    assert any(path.endswith(".emotional_state") for path in report.emotional_shift_summary)
    assert any(".fear" in path or ".trust" in path for path in report.relationship_tone_summary)


def test_group_scene_does_not_cross_npc_context(tmp_path: Path) -> None:
    report = run_rp_regression_scenario(
        RPRegressionScenario(
            id="group",
            scenario_type=RPRegressionScenarioType.GROUP_MEETING,
            participant_ids=["harlan", "mira"],
            input_sequence=["continue"],
            expected_safe_topics=["village safety"],
            forbidden_facts=["sealed_letter_under_stone"],
            seed=4,
        ),
        worlds_root=str(_rp_world(tmp_path)),
    )
    payload = json.dumps(report.model_dump_normal(), ensure_ascii=False, sort_keys=True)

    assert report.passed
    assert report.group_context_summary
    assert HIDDEN_TEXT not in payload


def test_fixed_seed_is_deterministic(tmp_path: Path) -> None:
    worlds_root = str(_rp_world(tmp_path))
    scenario = RPRegressionScenario(
        id="deterministic",
        scenario_type=RPRegressionScenarioType.NEGOTIATION,
        participant_ids=["harlan"],
        input_sequence=["please help", "thank you"],
        expected_safe_topics=["trade", "village"],
        seed=55,
    )

    first = run_rp_regression_scenario(scenario, worlds_root=worlds_root)
    second = run_rp_regression_scenario(scenario, worlds_root=worlds_root)

    assert first.model_dump_normal()["step_records"] == second.model_dump_normal()["step_records"]
    assert first.passed == second.passed
