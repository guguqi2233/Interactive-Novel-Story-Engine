import json
import subprocess
import sys
from pathlib import Path
from random import Random

from app.core.world_state import FactState, FactVisibility
from app.playtesting.agents import RandomValidActionAgent
from app.playtesting.invariants import check_playtest_invariants
from app.playtesting.runner import PlaytestOptions, run_playtest
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
