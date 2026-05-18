import json

from fastapi.testclient import TestClient

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.main import app
from app.quality.content_coverage import analyze_content_coverage


def test_content_coverage_report_can_generate() -> None:
    report = analyze_content_coverage("mist_valley")

    assert report.world_id == "mist_valley"
    assert report.locations.total >= 1
    assert 0 <= report.locations.coverage_percent <= 100
    assert report.quality_report.categories == ["content_coverage"]


def test_visited_location_talked_npc_and_triggered_quest_stage_are_covered() -> None:
    events = [
        Event(
            event_id="evt-location",
            turn=1,
            actor_id="player",
            action_type="move",
            result="Moved to blacksmith.",
            visible_to_player=True,
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path="player.location_id",
                    value="blacksmith",
                )
            ],
        ),
        Event(
            event_id="evt-talk",
            turn=2,
            actor_id="player",
            action_type="talk",
            target_id="harlan",
            result="Talked to Harlan.",
            visible_to_player=True,
            allow_empty_delta=True,
        ),
        Event(
            event_id="evt-quest",
            turn=3,
            actor_id="system",
            action_type="quest",
            result="Quest advanced.",
            visible_to_player=True,
            state_deltas=[
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path="quests.missing_tools.current_stage",
                    value="follow_bridge_clue",
                )
            ],
        ),
    ]

    report = analyze_content_coverage("mist_valley", events=events)

    assert "blacksmith" in report.locations.covered_ids
    assert "harlan" in report.npcs.covered_ids
    assert "missing_tools:follow_bridge_clue" in report.quests.covered_ids


def test_hidden_entities_do_not_enter_normal_report_details() -> None:
    report = analyze_content_coverage("mist_valley")
    payload = json.dumps(report.model_dump_normal(), ensure_ascii=False)

    assert "sealed_letter:find_letter" not in payload
    assert "sealed_letter_under_stone" not in payload
    assert report.hidden_entities_redacted["items"] >= 1
    assert report.hidden_entities_redacted["quests"] >= 1


def test_content_coverage_api_get_and_run() -> None:
    app.state.content_coverage_reports = []
    app.state.playtest_reports = []
    app.state.scenario_regression_runs = []
    client = TestClient(app)

    initial = client.get("/quality/worlds/mist_valley/coverage")
    assert initial.status_code == 200
    assert initial.json()["world_id"] == "mist_valley"

    run = client.post(
        "/quality/worlds/mist_valley/coverage/run",
        json={
            "events": [
                {
                    "event_id": "evt-api",
                    "turn": 1,
                    "actor_id": "player",
                    "action_type": "move",
                    "result": "Moved to blacksmith.",
                    "visible_to_player": True,
                    "state_deltas": [
                        {
                            "operation": "set",
                            "path": "player.location_id",
                            "value": "blacksmith",
                            "metadata": {},
                        }
                    ],
                    "allow_empty_delta": False,
                }
            ],
            "playtest_reports": [],
            "scenario_reports": [],
        },
    )
    assert run.status_code == 200
    payload = run.json()
    assert "blacksmith" in payload["locations"]["covered_ids"]

    latest = client.get("/quality/worlds/mist_valley/coverage")
    assert latest.status_code == 200
    assert latest.json()["locations"]["covered_ids"] == payload["locations"]["covered_ids"]
