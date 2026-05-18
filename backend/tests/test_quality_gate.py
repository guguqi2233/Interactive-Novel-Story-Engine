from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.quality import QualityIssue, QualityIssueSeverity, WorldQualityReport
from app.quality.gate import QualityGateConfig, run_quality_gate
from app.session_store import InMemorySessionStore
from app.tools import quality_gate as quality_gate_cli


def make_client(tmp_path: Path, enabled: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "quality_gate_api.db")
    app.state.quality_gate_results = []
    app.state.settings = Settings(
        enable_eval_api=enabled,
        enable_playtest_api=enabled,
        enable_debug_api=False,
        llm_provider="mock",
    )
    return TestClient(app)


def test_quality_gate_valid_world_passes_with_release_tolerant_config() -> None:
    result = run_quality_gate(
        "mist_valley",
        QualityGateConfig(
            allow_warnings=True,
            fail_on_error=False,
            fail_on_blocker=True,
            min_health_score=0,
            benchmark_iterations=1,
            playtest_steps=2,
        ),
    )

    assert result.passed is True
    assert result.report_links
    assert "validate_world" in result.summary["checks"]


def test_quality_gate_blocker_issue_fails_and_redacts_hidden_details(monkeypatch) -> None:
    hidden_text = "A sealed letter is hidden beneath a loose paving stone."

    def fake_analysis(world_id: str, *, worlds_root: str = "worlds"):
        _ = (world_id, worlds_root)
        return SimpleNamespace(
            quality_report=WorldQualityReport(
                world_id="mist_valley",
                categories=["quest_completion"],
                issues=[
                    QualityIssue(
                        id="fake:blocker",
                        severity=QualityIssueSeverity.BLOCKER,
                        category="quest_completion",
                        message=f"Hidden leak: {hidden_text}",
                    )
                ],
            )
        )

    monkeypatch.setattr("app.quality.gate.analyze_quest_completion", fake_analysis)

    result = run_quality_gate(
        "mist_valley",
        QualityGateConfig(min_health_score=0, benchmark_iterations=1, playtest_steps=1),
    )

    assert result.passed is False
    assert result.blockers
    assert hidden_text not in str(result.model_dump_normal())


def test_quality_gate_warning_only_can_pass_or_fail_by_config(monkeypatch) -> None:
    def fake_analysis(world_id: str, *, worlds_root: str = "worlds"):
        _ = (world_id, worlds_root)
        return SimpleNamespace(
            quality_report=WorldQualityReport(
                world_id="mist_valley",
                categories=["quest_completion"],
                issues=[
                    QualityIssue(
                        id="fake:warning",
                        severity=QualityIssueSeverity.WARNING,
                        category="quest_completion",
                        message="Optional quality warning.",
                    )
                ],
            )
        )

    monkeypatch.setattr("app.quality.gate.analyze_quest_completion", fake_analysis)

    passing = run_quality_gate(
        "mist_valley",
        QualityGateConfig(allow_warnings=True, fail_on_error=False, min_health_score=0, benchmark_iterations=1, playtest_steps=1),
    )
    failing = run_quality_gate(
        "mist_valley",
        QualityGateConfig(allow_warnings=False, fail_on_error=False, min_health_score=0, benchmark_iterations=1, playtest_steps=1),
    )

    assert passing.passed is True
    assert failing.passed is False
    assert "Optional quality warning." in failing.warnings


def test_quality_gate_api_disabled(tmp_path: Path) -> None:
    client = make_client(tmp_path, enabled=False)

    response = client.post("/quality/worlds/mist_valley/gate/run", json={})

    assert response.status_code == 403


def test_quality_gate_api_runs(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/quality/worlds/mist_valley/gate/run",
        json={"allow_warnings": True, "fail_on_error": False, "min_health_score": 0, "playtest_steps": 1},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_id"] == "mist_valley"
    assert payload["report_links"]


def test_quality_gate_cli_runs() -> None:
    exit_code = quality_gate_cli.main(
        [
            "--world",
            "mist_valley",
            "--allow-errors",
            "--allow-blockers",
            "--min-health-score",
            "0",
            "--json",
        ]
    )

    assert exit_code == 0
