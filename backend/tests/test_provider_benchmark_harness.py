import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.provider_benchmark import (
    ProviderBenchmarkCase,
    ProviderBenchmarkRun,
    ProviderBenchmarkType,
    run_provider_benchmark,
)
from app.main import app
from app.tools.provider_benchmark import main as provider_benchmark_cli_main


def test_mock_benchmark_can_run() -> None:
    report = run_provider_benchmark(
        ProviderBenchmarkRun(
            provider_id="mock",
            benchmark_types=[ProviderBenchmarkType.GENERATE_TEXT_SMOKE],
        )
    )

    assert report.total_cases == 1
    assert report.ok_cases == 1
    assert report.error_rate == 0


def test_schema_benchmark_failure_reports_clearly() -> None:
    report = run_provider_benchmark(
        ProviderBenchmarkRun(
            provider_id="fake_invalid_json",
            benchmark_types=[ProviderBenchmarkType.GENERATE_JSON_SCHEMA],
        )
    )

    assert report.total_cases == 1
    assert report.ok_cases == 0
    assert report.cases[0].schema_valid is False
    assert report.cases[0].error_class == "LLMProviderError"
    assert "schema validation" in (report.cases[0].error_message_safe or "")


def test_allow_real_provider_false_blocks_real_provider() -> None:
    report = run_provider_benchmark(
        ProviderBenchmarkRun(
            provider_id="openai",
            allow_real_provider=False,
            benchmark_types=[ProviderBenchmarkType.GENERATE_TEXT_SMOKE],
        ),
        settings=Settings(llm_provider="openai", llm_api_key="sk-test-fake-not-real"),
    )

    assert report.real_provider_blocked
    assert report.total_cases == 0
    assert "real_external_provider_requires_explicit_opt_in" in report.blockers


def test_report_does_not_contain_api_key() -> None:
    report = run_provider_benchmark(
        ProviderBenchmarkRun(
            provider_id="fake",
            benchmark_types=[ProviderBenchmarkType.GENERATE_TEXT_SMOKE],
            cases=[
                ProviderBenchmarkCase(
                    id="secret-case",
                    benchmark_type=ProviderBenchmarkType.GENERATE_TEXT_SMOKE,
                    messages=[{"role": "user", "content": "hello LLM_API_KEY=sk-real-looking-secret"}],
                )
            ],
        )
    )

    rendered = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert "sk-real-looking-secret" not in rendered
    assert "LLM_API_KEY" not in rendered
    assert "[redacted-secret]" in rendered


def test_hidden_case_redacted() -> None:
    report = run_provider_benchmark(
        ProviderBenchmarkRun(
            provider_id="fake",
            benchmark_types=[ProviderBenchmarkType.HIDDEN_FACT_REFUSAL],
            cases=[
                ProviderBenchmarkCase(
                    id="hidden-case",
                    benchmark_type=ProviderBenchmarkType.HIDDEN_FACT_REFUSAL,
                    messages=[{"role": "user", "content": "Do not reveal the mayor forged the charter"}],
                    hidden_terms=["the mayor forged the charter"],
                )
            ],
        )
    )

    rendered = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert report.ok_cases == 1
    assert "the mayor forged the charter" not in rendered
    assert "[redacted-hidden]" in rendered


def test_provider_benchmark_cli_runs(capsys: object) -> None:
    exit_code = provider_benchmark_cli_main(
        [
            "--provider",
            "fake",
            "--benchmark",
            "generate_json_schema",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["provider_id"] == "fake"
    assert payload["cases"][0]["benchmark_type"] == "generate_json_schema"


def test_provider_benchmark_api_respects_gate_and_returns_run() -> None:
    previous_settings = getattr(app.state, "settings", None)
    previous_reports = getattr(app.state, "provider_benchmark_reports", None)
    client = TestClient(app)
    try:
        app.state.provider_benchmark_reports = []
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=False, llm_provider="mock")
        disabled = client.post(
            "/prompt-lab/providers/benchmark",
            json={"provider_id": "fake", "benchmark_types": ["generate_text_smoke"]},
        )
        app.state.settings = Settings(enable_debug_api=True, enable_perf_logging=False, llm_provider="mock")
        enabled = client.post(
            "/prompt-lab/providers/benchmark",
            json={"run_id": "provider-benchmark-api-test", "provider_id": "fake", "benchmark_types": ["generate_text_smoke"]},
        )
        fetched = client.get("/prompt-lab/providers/benchmark/provider-benchmark-api-test")
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        app.state.provider_benchmark_reports = previous_reports or []

    assert disabled.status_code == 403
    assert enabled.status_code == 200
    assert enabled.json()["provider_id"] == "fake"
    assert fetched.status_code == 200
    assert fetched.json()["run_id"] == "provider-benchmark-api-test"
