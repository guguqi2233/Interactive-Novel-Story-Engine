from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.scenarios.regression import ScenarioRegressionCase, run_scenario_regression_suite
from app.session_store import InMemorySessionStore


def make_client(tmp_path: Path, enabled: bool = True) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "scenario_api.db")
    app.state.worlds_root = worlds_root
    app.state.scenario_regression_runs = []
    app.state.settings = Settings(
        enable_playtest_api=enabled,
        enable_eval_api=False,
        enable_debug_api=False,
        llm_provider="mock",
        llm_api_key="test-api-key-placeholder",
    )
    return TestClient(app)


def test_scenario_regression_api_disabled(tmp_path: Path) -> None:
    client = make_client(tmp_path, enabled=False)

    response = client.get("/scenarios/regression")

    assert response.status_code == 403
    assert "Scenario regression API is disabled" in response.json()["detail"]


def test_scenario_regression_case_can_run(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    list_response = client.get("/scenarios/regression")
    run_response = client.post(
        "/scenarios/regression/run",
        json={"world_id": "mist_valley", "scenario_ids": ["mist_valley_opening_observe"]},
    )

    assert list_response.status_code == 200
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["total_cases"] == 1
    assert payload["case_results"][0]["case_id"] == "mist_valley_opening_observe"
    assert "test-api-key-placeholder" not in run_response.text
    assert "A sealed letter is hidden beneath a loose paving stone." not in run_response.text


def test_expected_visible_facts_and_quest_state_checks(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    case = ScenarioRegressionCase(
        id="custom_expectations",
        world_id="mist_valley",
        name="Custom expectations",
        input_sequence=["observe"],
        expected_visible_facts=["village_square_is_misty"],
        expected_quest_states={"missing_quest": "active"},
    )

    run = run_scenario_regression_suite([case], worlds_root=worlds_root)

    assert run.failed == 1
    assert any("quest_state_mismatch:missing_quest" in reason for reason in run.case_results[0].failure_reasons)


def test_forbidden_visible_fact_leak_fails_safely(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    case = ScenarioRegressionCase(
        id="forbidden_public_fact",
        world_id="mist_valley",
        name="Forbidden visible fact",
        input_sequence=["observe"],
        forbidden_visible_facts=["village_square_is_misty"],
    )

    run = run_scenario_regression_suite([case], worlds_root=worlds_root)

    assert run.failed == 1
    assert run.case_results[0].hidden_leak_summary == [
        "forbidden_visible_fact_present:village_square_is_misty"
    ]


def test_run_does_not_modify_real_save_repository(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    start_response = client.post("/game/start", json={"world_id": "mist_valley"})
    save_response = client.post(f"/game/{start_response.json()['session_id']}/save")
    saves_before = client.get("/game/saves").json()["saves"]

    run_response = client.post(
        "/scenarios/regression/run",
        json={"world_id": "mist_valley"},
    )
    saves_after = client.get("/game/saves").json()["saves"]

    assert save_response.status_code == 200
    assert run_response.status_code == 200
    assert [save["save_id"] for save in saves_after] == [save["save_id"] for save in saves_before]
