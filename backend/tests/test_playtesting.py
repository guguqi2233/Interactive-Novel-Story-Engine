import json
import subprocess
import sys
from pathlib import Path
from random import Random

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import FactState, FactVisibility
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.playtesting.agents import RandomValidActionAgent
from app.playtesting.invariants import check_playtest_invariants
from app.playtesting.runner import PlaytestOptions, PlaytestScenario, PlaytestScenarioType, run_playtest, run_playtest_scenario
from app.session_store import InMemorySessionStore
from app.session_store import build_visible_state, create_initial_state


def test_random_valid_action_agent_runs_fixed_steps() -> None:
    report = run_playtest(
        PlaytestOptions(
            world_id="mist_valley",
            strategy="random_valid_action_agent",
            max_steps=5,
            seed=7,
        )
    )

    assert report.turns_run == 5
    assert len(report.actions_taken) == 5
    assert report.errors == []
    assert report.final_state_summary.world_id == "mist_valley"
    assert report.final_state_summary.event_count >= 5


def test_playtest_report_has_required_sections() -> None:
    report = run_playtest(PlaytestOptions(max_steps=1, seed=1))
    payload = report.model_dump(mode="json")

    assert set(payload) >= {
        "turns_run",
        "actions_taken",
        "errors",
        "invariant_violations",
        "visibility_leaks",
        "save_load_failures",
        "final_state_summary",
    }


def test_fixed_seed_is_deterministic() -> None:
    options = PlaytestOptions(max_steps=8, seed=42, strategy="random_valid_action_agent")

    first = run_playtest(options)
    second = run_playtest(options)

    assert [action.input_text for action in first.actions_taken] == [
        action.input_text for action in second.actions_taken
    ]
    assert [action.action_type for action in first.actions_taken] == [
        action.action_type for action in second.actions_taken
    ]


def test_save_load_during_playtest(tmp_path: Path) -> None:
    report = run_playtest(
        PlaytestOptions(
            max_steps=4,
            seed=9,
            save_every=2,
            database_path=str(tmp_path / "playtest.db"),
        )
    )

    assert report.save_load_failures == []
    assert report.errors == []


def test_invariant_violation_is_captured() -> None:
    state = create_initial_state(world_id="mist_valley")
    item = next(iter(state.objects.values()))
    item.location_id = state.player.location_id
    item.owner_id = state.player.id

    result = check_playtest_invariants(state, events=[])

    assert any("item_in_multiple_places" in issue for issue in result.invariant_violations)


def test_hidden_fact_leak_is_reported() -> None:
    state = create_initial_state(world_id="mist_valley")
    state.facts["secret_test_fact"] = FactState(
        id="secret_test_fact",
        text="forbidden hidden text",
        visibility=FactVisibility.HIDDEN,
    )
    state.player_visible_facts.add("secret_test_fact")

    result = check_playtest_invariants(state, events=[])

    assert "hidden_fact_marked_visible:secret_test_fact" in result.visibility_leaks
    assert "hidden_fact_text_visible:secret_test_fact" in result.visibility_leaks


def test_agent_chooses_from_visible_state_only() -> None:
    state = create_initial_state(world_id="mist_valley")
    visible_state = build_visible_state(state)

    action = RandomValidActionAgent().choose_action(visible_state, Random(3))

    assert isinstance(action, str)
    assert "secret" not in action.lower()


def test_playtest_cli_runs() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.app.tools.playtest",
            "--world",
            "mist_valley",
            "--steps",
            "2",
            "--seed",
            "5",
            "--json",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["turns_run"] == 2
    assert payload["world_id"] == "mist_valley"


def test_exploration_playtest_scenario_runs() -> None:
    scenario = PlaytestScenario(
        id="opening_exploration",
        world_id="mist_valley",
        name="Opening exploration",
        scenario_type=PlaytestScenarioType.EXPLORATION,
        agent_type="explore_agent",
        max_steps=3,
        seed=17,
        invariants=["hidden_facts_not_visible", "agent_actions_have_events"],
        tags=["exploration"],
    )

    report = run_playtest_scenario(scenario)

    assert report.passed
    assert report.playtest_report.turns_run == 3
    assert report.quality_report.world_id == "mist_valley"
    assert "playtesting" in report.quality_report.categories


def test_quest_path_playtest_scenario_runs() -> None:
    scenario = PlaytestScenario(
        id="quest_path_smoke",
        world_id="mist_valley",
        name="Quest path smoke",
        scenario_type=PlaytestScenarioType.QUEST_PATH,
        agent_type="quest_following_agent",
        max_steps=2,
        seed=4,
        expected_outcomes={"min_turns": 2},
        tags=["quest"],
    )

    report = run_playtest_scenario(scenario)

    assert report.playtest_report.turns_run == 2
    assert report.playtest_report.errors == []
    assert all(action.event_id for action in report.playtest_report.actions_taken)


def test_hidden_leak_probe_detects_forbidden_visible_fact_without_text() -> None:
    scenario = PlaytestScenario(
        id="hidden_probe_visible_fact",
        world_id="mist_valley",
        name="Hidden probe detects forbidden visible fact",
        scenario_type=PlaytestScenarioType.HIDDEN_LEAK_PROBE,
        agent_type="random_valid_action_agent",
        max_steps=0,
        seed=1,
        forbidden_outcomes={"visible_facts": ["village_square_is_misty"]},
        tags=["hidden-leak"],
    )

    report = run_playtest_scenario(scenario)
    normal_payload = json.dumps(report.model_dump_normal(), ensure_ascii=False)

    assert not report.passed
    assert "hidden_leak_probe_forbidden_visible_fact:village_square_is_misty" in report.hidden_leak_summary
    assert "A sealed letter is hidden beneath a loose paving stone." not in normal_payload
    assert "hidden_details_debug_only" not in normal_payload


def test_save_load_path_scenario_round_trips(tmp_path: Path) -> None:
    scenario = PlaytestScenario(
        id="save_load_smoke",
        world_id="mist_valley",
        name="Save load path smoke",
        scenario_type=PlaytestScenarioType.SAVE_LOAD_PATH,
        agent_type="random_valid_action_agent",
        max_steps=4,
        seed=21,
        tags=["save-load"],
    )

    report = run_playtest_scenario(scenario, database_path=str(tmp_path / "scenario-playtest.db"))

    assert report.playtest_report.save_load_failures == []
    assert report.failure_reasons == []


def test_playtest_scenario_fixed_seed_is_deterministic() -> None:
    scenario = PlaytestScenario(
        id="deterministic_scenario",
        world_id="mist_valley",
        name="Deterministic scenario",
        scenario_type=PlaytestScenarioType.EXPLORATION,
        agent_type="random_valid_action_agent",
        max_steps=5,
        seed=99,
    )

    first = run_playtest_scenario(scenario)
    second = run_playtest_scenario(scenario)

    assert [action.input_text for action in first.playtest_report.actions_taken] == [
        action.input_text for action in second.playtest_report.actions_taken
    ]
    assert first.visible_summary == second.visible_summary


def test_playtest_scenario_does_not_mutate_external_game_state() -> None:
    state = create_initial_state(world_id="mist_valley")
    before = state.model_dump(mode="json")
    scenario = PlaytestScenario(
        id="external_state_boundary",
        world_id="mist_valley",
        name="External state boundary",
        scenario_type=PlaytestScenarioType.EXPLORATION,
        agent_type="explore_agent",
        max_steps=1,
        seed=2,
    )

    _ = run_playtest_scenario(scenario)

    assert state.model_dump(mode="json") == before


def make_playtest_client(tmp_path: Path, *, enabled: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "playtest_api.db")
    app.state.playtest_reports = []
    app.state.settings = Settings(
        enable_debug_api=False,
        enable_playtest_api=enabled,
        llm_provider="mock",
        llm_api_key="sk-test-fake-not-real",
    )
    return TestClient(app)


def test_playtest_api_disabled_when_debug_and_playtest_disabled(tmp_path: Path) -> None:
    client = make_playtest_client(tmp_path, enabled=False)

    response = client.get("/playtests/recent")

    assert response.status_code == 403
    assert response.json()["detail"] == "Playtest API is disabled"


def test_playtest_api_run_is_deterministic_and_sanitized(tmp_path: Path) -> None:
    client = make_playtest_client(tmp_path)
    request = {
        "world_id": "mist_valley",
        "agent_type": "random_valid_action_agent",
        "steps": 4,
        "seed": 11,
        "save_load_check": True,
    }

    first = client.post("/playtests/run", json=request)
    second = client.post("/playtests/run", json=request)
    recent = client.get("/playtests/recent")

    assert first.status_code == 200
    assert second.status_code == 200
    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["turns_run"] == 4
    assert first_payload["final_state_summary"]["world_id"] == "mist_valley"
    assert [action["input_text"] for action in first_payload["actions_taken"]] == [
        action["input_text"] for action in second_payload["actions_taken"]
    ]
    assert first_payload["save_load_failures"] == []
    assert recent.status_code == 200
    assert len(recent.json()["reports"]) == 2
    serialized = json.dumps(first_payload, ensure_ascii=False)
    assert "forbidden hidden text" not in serialized
    assert "sk-test-fake-not-real" not in serialized
    assert "state_json" not in serialized
    assert "state_deltas" not in serialized


def test_playtest_api_get_report_and_unknown_run(tmp_path: Path) -> None:
    client = make_playtest_client(tmp_path)
    created = client.post(
        "/playtests/run",
        json={
            "world_id": "mist_valley",
            "agent_type": "explore_agent",
            "steps": 2,
            "seed": 3,
            "save_load_check": False,
        },
    ).json()

    response = client.get(f"/playtests/{created['run_id']}")
    missing = client.get("/playtests/missing")

    assert response.status_code == 200
    assert response.json()["run_id"] == created["run_id"]
    assert missing.status_code == 404


def test_frontend_playtesting_dashboard_contracts() -> None:
    app_source = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    api_source = Path("frontend/src/api.ts").read_text(encoding="utf-8")

    assert "Automated Playtesting" in app_source
    assert "Run Playtest" in app_source
    assert "Invariant Violations" in app_source
    assert "Visibility / Save Checks" in app_source
    assert "ENABLE_PLAYTEST_API=true" in app_source
    assert "fetchPlaytestRecent" in api_source
    assert "runPlaytest" in api_source
    assert "/playtests/run" in api_source
    assert "/playtests/recent" in api_source
