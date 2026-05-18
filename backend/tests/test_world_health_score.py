import json

from fastapi.testclient import TestClient

from app.main import app
from app.quality import QualityIssue, QualityIssueSeverity, WorldQualityReport
from app.quality.health_score import build_world_health_score, empty_world_health_score


def test_health_score_can_generate_from_reports() -> None:
    report = WorldQualityReport(
        world_id="mist_valley",
        categories=["validation"],
        issues=[
            QualityIssue(
                id="warning",
                severity=QualityIssueSeverity.WARNING,
                category="validation",
                message="A safe validation warning.",
            )
        ],
        recommended_actions=["Review validation warning."],
    )

    health = build_world_health_score("mist_valley", [report])

    assert health.world_id == "mist_valley"
    assert 0 <= health.overall_score <= 100
    assert health.category_scores
    assert "Review validation warning." in health.recommended_actions


def test_blocker_lowers_score() -> None:
    clean = build_world_health_score("mist_valley", [WorldQualityReport(world_id="mist_valley")])
    blocked = build_world_health_score(
        "mist_valley",
        [
            WorldQualityReport(
                world_id="mist_valley",
                issues=[
                    QualityIssue(
                        id="blocker",
                        severity=QualityIssueSeverity.BLOCKER,
                        category="dead_end",
                        message="Required item is unreachable.",
                    )
                ],
            )
        ],
    )

    assert blocked.overall_score < clean.overall_score
    assert blocked.blockers == ["dead_end: Required item is unreachable."]


def test_hidden_details_do_not_enter_health_score() -> None:
    hidden_text = "sealed hidden clue text"
    health = build_world_health_score(
        "mist_valley",
        [
            WorldQualityReport(
                world_id="mist_valley",
                issues=[
                    QualityIssue(
                        id="hidden",
                        severity=QualityIssueSeverity.ERROR,
                        category="visibility",
                        message="Visibility risk.",
                        safe_details={"safe": "summary"},
                        hidden_details_debug_only={"hidden_fact_text": hidden_text},
                    )
                ],
                summary={"hidden_details_debug_only": {"hidden_fact_text": hidden_text}},
            )
        ],
    )
    payload = json.dumps(health.model_dump(mode="json"), ensure_ascii=False)

    assert hidden_text not in payload
    assert "hidden_details_debug_only" not in payload


def test_empty_health_score_is_friendly() -> None:
    health = empty_world_health_score("mist_valley")

    assert health.overall_score == 100
    assert health.summary["source_reports"] == 0
    assert health.recommended_actions


def test_health_api_get_empty_and_run() -> None:
    app.state.world_health_scores = []
    app.state.benchmark_reports = []
    client = TestClient(app)

    empty = client.get("/quality/worlds/mist_valley/health")
    assert empty.status_code == 200
    assert empty.json()["summary"]["source_reports"] == 0

    run = client.post("/quality/worlds/mist_valley/health/run")
    assert run.status_code == 200
    payload = run.json()
    assert payload["world_id"] == "mist_valley"
    assert "category_scores" in payload
    assert "sealed hidden clue text" not in json.dumps(payload, ensure_ascii=False)

    latest = client.get("/quality/worlds/mist_valley/health")
    assert latest.status_code == 200
    assert latest.json()["health_id"] == payload["health_id"]
