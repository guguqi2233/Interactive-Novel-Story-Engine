import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.playtesting import batch as batch_module
from app.playtesting.batch import PlaytestBatchRunRequest, run_playtest_batch
from app.playtesting.runner import PlaytestFinalStateSummary, PlaytestReport
from app.session_store import InMemorySessionStore
from app.tools import playtest_batch as playtest_batch_cli


def make_client(tmp_path: Path, enabled: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "batch_api.db")
    app.state.playtest_reports = []
    app.state.playtest_batch_reports = []
    app.state.settings = Settings(enable_playtest_api=enabled, enable_debug_api=enabled, llm_provider="mock")
    return TestClient(app)


def test_playtest_batch_multiple_seeds_is_structurally_deterministic() -> None:
    request = PlaytestBatchRunRequest(
        world_id="mist_valley",
        agent_types=["random_valid_action_agent"],
        seeds=[1, 2],
        steps=4,
        save_load_check=True,
    )

    first = run_playtest_batch(request)
    second = run_playtest_batch(request)

    assert first.total_runs == 2
    assert first.failed == 0
    assert first.blockers == 0
    assert first.coverage_summary.seeds_run == [1, 2]
    assert [item.report.final_state_summary for item in first.run_items] == [
        item.report.final_state_summary for item in second.run_items
    ]


def test_playtest_batch_stop_on_blocker(monkeypatch) -> None:
    def fake_run_playtest(options):
        _ = options
        return PlaytestReport(
            strategy="random_valid_action_agent",
            world_id="mist_valley",
            seed=123,
            turns_run=0,
            visibility_leaks=["hidden fact leak detected: [hidden text redacted]"],
            final_state_summary=PlaytestFinalStateSummary(
                world_id="mist_valley",
                turn=0,
                location_id="village_square",
                event_count=0,
            ),
        )

    monkeypatch.setattr(batch_module, "run_playtest", fake_run_playtest)

    report = run_playtest_batch(
        PlaytestBatchRunRequest(
            world_id="mist_valley",
            agent_types=["random_valid_action_agent"],
            seeds=[1, 2, 3],
            steps=1,
            stop_on_blocker=True,
        )
    )

    assert report.total_runs == 1
    assert report.failed == 1
    assert report.blockers == 1


def test_playtest_batch_aggregate_report_is_safe() -> None:
    report = run_playtest_batch(
        PlaytestBatchRunRequest(
            world_id="mist_valley",
            agent_types=["explore_agent", "quest_following_agent"],
            seeds=[7],
            steps=3,
        )
    )

    assert report.total_runs == 2
    assert report.coverage_summary.agents_run == ["explore_agent", "quest_following_agent"]
    assert report.quality_report.categories == ["playtest_batch"]
    normal_payload = json.dumps(report.model_dump_normal())
    assert "A sealed letter is hidden beneath a loose paving stone." not in normal_payload


def test_playtest_batch_api_and_lookup(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/playtests/batch/run",
        json={
            "world_id": "mist_valley",
            "agent_types": ["random_valid_action_agent"],
            "seeds": [11, 12],
            "steps": 2,
            "save_load_check": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_runs"] == 2
    fetched = client.get(f"/playtests/batch/{payload['run_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["run_id"] == payload["run_id"]


def test_playtest_batch_api_disabled(tmp_path: Path) -> None:
    client = make_client(tmp_path, enabled=False)

    response = client.post("/playtests/batch/run", json={"world_id": "mist_valley"})

    assert response.status_code == 403


def test_playtest_batch_cli_runs() -> None:
    exit_code = playtest_batch_cli.main(["--world", "mist_valley", "--seeds", "1,2", "--steps", "1", "--json"])

    assert exit_code == 0
