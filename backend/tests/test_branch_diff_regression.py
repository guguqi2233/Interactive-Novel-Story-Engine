import json

from fastapi.testclient import TestClient

from app.engine.content.world_branching import WorldDiff, WorldEntityRef
from app.main import app
from app.quality.branch_diff_regression import run_branch_diff_regression, select_regression_cases
from app.scenarios.regression import ScenarioRegressionCase


def _case(case_id: str, tags: list[str]) -> ScenarioRegressionCase:
    return ScenarioRegressionCase(
        id=case_id,
        world_id="mist_valley",
        name=case_id,
        input_sequence=[],
        max_turns=0,
        tags=tags,
    )


def test_changed_quest_triggers_quest_regression() -> None:
    diff = WorldDiff(
        world_id="mist_valley",
        other="branch",
        changed_entities=[
            {
                "file": "quests.yaml",
                "entity_id": "missing_tools",
                "entity_type": "quest",
                "before_hash": "a",
                "after_hash": "b",
            }
        ],
    )
    cases = [_case("quest-case", ["quest"]), _case("nav-case", ["navigation"])]

    selected = select_regression_cases(diff, cases)

    assert [item.scenario_id for item in selected] == ["quest-case"]
    assert selected[0].reason == "changed quest content"


def test_removed_location_triggers_navigation_regression() -> None:
    diff = WorldDiff(
        world_id="mist_valley",
        other="branch",
        removed_entities=[
            WorldEntityRef(file="locations.yaml", entity_id="old_bridge", entity_type="location")
        ],
    )
    cases = [_case("nav-case", ["navigation"]), _case("trade-case", ["trade"])]

    selected = select_regression_cases(diff, cases)

    assert [item.scenario_id for item in selected] == ["nav-case"]


def test_hidden_fact_change_triggers_leak_regression() -> None:
    diff = WorldDiff(
        world_id="mist_valley",
        other="branch",
        changed_entities=[
            {
                "file": "facts.yaml",
                "entity_id": "sealed_letter_under_stone",
                "entity_type": "fact",
                "before_hash": "a",
                "after_hash": "b",
            }
        ],
        visibility_risks=["hidden fact changed"],
    )
    cases = [_case("leak-case", ["hidden-boundary"]), _case("quest-case", ["quest"])]

    selected = select_regression_cases(diff, cases)

    assert [item.scenario_id for item in selected] == ["leak-case"]


def test_branch_regression_runs_selected_cases_without_hidden_detail_leak() -> None:
    hidden_text = "A sealed letter is hidden beneath a loose paving stone."
    diff = WorldDiff(
        world_id="mist_valley",
        other="branch",
        visibility_risks=[hidden_text],
    )
    report = run_branch_diff_regression(
        world_id="mist_valley",
        diff=diff,
        scenario_cases=[_case("leak-case", ["leak"])],
    )
    payload = json.dumps(report.model_dump_normal(), ensure_ascii=False)

    assert report.regression_run is not None
    assert report.regression_run.total_cases == 1
    assert report.passed
    assert hidden_text not in payload


def test_branch_regression_api_uses_temp_regression_run() -> None:
    app.state.branch_regression_reports = []
    client = TestClient(app)
    response = client.post(
        "/quality/worlds/mist_valley/branch-regression/run",
        json={
            "base_branch": "base",
            "target_branch": "branch",
            "diff": {
                "world_id": "mist_valley",
                "other": "branch",
                "added_entities": [],
                "removed_entities": [
                    {
                        "file": "locations.yaml",
                        "entity_id": "old_bridge",
                        "entity_type": "location",
                    }
                ],
                "changed_entities": [],
                "renamed_candidates": [],
                "broken_references": [],
                "migration_impacts": [],
                "visibility_risks": [],
            },
            "scenario_cases": [
                {
                    "id": "nav-case",
                    "world_id": "mist_valley",
                    "name": "Navigation case",
                    "input_sequence": [],
                    "max_turns": 0,
                    "tags": ["navigation"],
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["selected"][0]["scenario_id"] == "nav-case"
    assert payload["regression_run"]["total_cases"] == 1
    assert payload["quality_report"]["categories"] == ["branch_diff_regression"]
