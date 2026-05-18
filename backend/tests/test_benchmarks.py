import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.quality.benchmarks import (
    BenchmarkReport,
    BenchmarkRunRequest,
    BenchmarkSample,
    load_performance_budget,
    run_benchmark_suite,
)
from app.tools.benchmark import main as benchmark_cli_main


def test_benchmark_report_schema_and_safe_summary() -> None:
    report = run_benchmark_suite(
        BenchmarkRunRequest(
            world_id="mist_valley",
            iterations=1,
            benchmarks=["validate_world", "memory_search"],
        )
    )

    payload = report.model_dump_safe()
    encoded = json.dumps(payload, ensure_ascii=False)

    assert report.benchmark_id.startswith("benchmark-")
    assert report.p50["validate_world"] >= 0
    assert report.max["memory_search"] >= 0
    assert payload["environment_summary_safe"]["telemetry"] == "not uploaded"
    assert "api_key" not in encoded.lower()
    assert "sk-" not in encoded.lower()
    assert "prompt" not in encoded.lower()
    assert "hidden fact" not in encoded.lower()


def test_benchmark_thresholds_report_regressions() -> None:
    report = run_benchmark_suite(
        BenchmarkRunRequest(
            world_id="mist_valley",
            iterations=1,
            benchmarks=["memory_search"],
            thresholds_ms={"memory_search": -1},
        )
    )

    assert report.thresholds["memory_search"] == -1
    assert report.regressions
    assert report.regressions[0].benchmark_type == "memory_search"


def test_benchmark_loads_v1_budget_and_reports_warning(tmp_path: Path) -> None:
    budget_path = tmp_path / "budget.json"
    budget_path.write_text(
        json.dumps(
            {
                "budgets": {
                    "memory_search": {
                        "target_ms": 0,
                        "warning_ms": 0,
                        "blocker_ms": 999999,
                        "measurement_method": "test budget",
                        "known_caveats": ["test only"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    loaded = load_performance_budget(budget_path)
    report = run_benchmark_suite(
        BenchmarkRunRequest(
            world_id="mist_valley",
            iterations=1,
            benchmarks=["memory_search"],
            budget_path=str(budget_path),
        )
    )

    assert loaded["memory_search"].measurement_method == "test budget"
    assert report.budgets["memory_search"].warning_ms == 0
    assert any(
        regression.benchmark_type == "memory_search"
        and regression.severity == "warning"
        for regression in report.regressions
    )


def test_benchmark_budget_blocker_regression(tmp_path: Path) -> None:
    budget_path = tmp_path / "budget.json"
    budget_path.write_text(
        json.dumps(
            {
                "memory_search": {
                    "target_ms": 0,
                    "warning_ms": 0,
                    "blocker_ms": 0,
                    "measurement_method": "test budget",
                }
            }
        ),
        encoding="utf-8",
    )

    report = run_benchmark_suite(
        BenchmarkRunRequest(
            world_id="mist_valley",
            iterations=1,
            benchmarks=["memory_search"],
            budget_path=str(budget_path),
        )
    )

    assert any(regression.severity == "blocker" for regression in report.regressions)


def test_benchmark_uses_temporary_db_for_save_load() -> None:
    report = run_benchmark_suite(
        BenchmarkRunRequest(
            world_id="mist_valley",
            iterations=1,
            benchmarks=["save_load", "migration_dry_run"],
        )
    )

    assert all(sample.ok for sample in report.samples)
    payload = json.dumps(report.model_dump_safe(), ensure_ascii=False).lower()
    assert "world_engine.db" not in payload
    assert "database_url" not in payload


def test_benchmark_cli_runs(capsys: object) -> None:
    exit_code = benchmark_cli_main(
        [
            "--world",
            "mist_valley",
            "--iterations",
            "1",
            "--benchmark",
            "memory_search",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["world_id"] == "mist_valley"
    assert payload["samples"][0]["benchmark_type"] == "memory_search"


def test_benchmark_api_respects_debug_or_perf_gate(tmp_path: Path) -> None:
    previous_settings = getattr(app.state, "settings", None)
    previous_worlds_root = getattr(app.state, "worlds_root", None)
    previous_reports = getattr(app.state, "benchmark_reports", None)
    client = TestClient(app)
    try:
        app.state.worlds_root = "worlds"
        app.state.benchmark_reports = []
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=False, llm_provider="mock")
        disabled = client.post(
            "/quality/benchmarks/run",
            json={"world_id": "mist_valley", "iterations": 1, "benchmarks": ["memory_search"]},
        )
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=True, llm_provider="mock")
        enabled = client.post(
            "/quality/benchmarks/run",
            json={"world_id": "mist_valley", "iterations": 1, "benchmarks": ["memory_search"]},
        )
        app.state.benchmark_reports.append(
            BenchmarkReport(
                world_id="mist_valley",
                samples=[
                    BenchmarkSample(
                        benchmark_type="memory_search",
                        duration_ms=1,
                        ok=False,
                        error="prompt leaked hidden fact with api_key sk-test-fake-not-real",
                    )
                ],
            )
        )
        recent = client.get("/quality/benchmarks/recent")
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        app.state.worlds_root = previous_worlds_root or "worlds"
        app.state.benchmark_reports = previous_reports or []
        _ = tmp_path

    assert disabled.status_code == 403
    assert enabled.status_code == 200
    assert enabled.json()["samples"][0]["benchmark_type"] == "memory_search"
    assert recent.status_code == 200
    assert recent.json()
    recent_payload = json.dumps(recent.json(), ensure_ascii=False).lower()
    assert "prompt leaked hidden fact" not in recent_payload
    assert "api_key" not in recent_payload
    assert "sk-test" not in recent_payload
