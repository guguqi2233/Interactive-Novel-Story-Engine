import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.prompt_regression import (
    PromptRegressionCase,
    PromptRegressionCaseType,
    PromptRegressionRun,
    run_prompt_regression,
)
from app.main import app
from app.tools.prompt_regression import main as cli_main


def test_baseline_candidate_regression_can_run() -> None:
    report = run_prompt_regression(PromptRegressionRun())

    assert report.pass_fail == "pass"
    assert len(report.cases) == 7
    assert report.regressions == []
    assert report.safety_blockers == []


def test_hidden_leak_regression_is_blocker() -> None:
    report = run_prompt_regression(
        PromptRegressionRun(
            baseline_provider_id="fake",
            candidate_provider_id="fake_leaky",
            cases=[
                PromptRegressionCase(
                    id="hidden_leak_case",
                    case_type=PromptRegressionCaseType.HIDDEN_LEAK,
                    hidden_terms=["the mayor forged the charter"],
                )
            ],
        )
    )
    payload = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert report.pass_fail == "fail"
    assert "hidden_leak_case:hidden_leak_regression" in report.safety_blockers
    assert "the mayor forged the charter" not in payload


def test_schema_reliability_regression_is_caught() -> None:
    report = run_prompt_regression(
        PromptRegressionRun(
            baseline_provider_id="fake",
            candidate_provider_id="fake_invalid_json",
            cases=[
                PromptRegressionCase(
                    id="intent_schema_case",
                    case_type=PromptRegressionCaseType.INTENT_PARSER_SCHEMA,
                )
            ],
        )
    )

    assert report.pass_fail == "fail"
    assert "intent_schema_case:schema_reliability_regression" in report.regressions
    assert report.cases[0].candidate.schema_valid_rate == 0.0


def test_latency_delta_is_recorded() -> None:
    report = run_prompt_regression(
        PromptRegressionRun(
            baseline_provider_id="fake",
            candidate_provider_id="fake_slow",
            cases=[
                PromptRegressionCase(
                    id="latency_case",
                    case_type=PromptRegressionCaseType.NARRATOR_CONSISTENCY,
                )
            ],
        )
    )

    assert report.cases[0].latency_delta_ms >= 2400
    assert "latency_case:latency_regression" in report.regressions
    assert report.latency_cost_delta["average_latency_delta_ms"] >= 2400


def test_report_does_not_leak_api_key_or_hidden_text() -> None:
    report = run_prompt_regression(
        PromptRegressionRun(
            baseline_provider_id="fake",
            candidate_provider_id="fake_invalid_json",
            cases=[
                PromptRegressionCase(
                    id="secret_case",
                    case_type=PromptRegressionCaseType.STRUCTURED_JSON_RELIABILITY,
                    input_text="LLM_API_KEY=sk-real-looking-secret hidden fact: the mayor forged the charter",
                    hidden_terms=["the mayor forged the charter"],
                )
            ],
        )
    )
    payload = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert "sk-real-looking-secret" not in payload
    assert "the mayor forged the charter" not in payload
    assert "LLM_API_KEY" not in payload


def test_prompt_regression_api_respects_gate() -> None:
    client = TestClient(app)
    previous_settings = getattr(app.state, "settings", None)
    previous_reports = getattr(app.state, "prompt_regression_reports", None)
    try:
        app.state.prompt_regression_reports = []
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=False, llm_provider="mock")
        disabled = client.post("/prompt-lab/regression/run", json={})
        app.state.settings = Settings(enable_debug_api=True, enable_perf_logging=False, llm_provider="mock")
        enabled = client.post("/prompt-lab/regression/run", json={})
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        app.state.prompt_regression_reports = previous_reports or []

    assert disabled.status_code == 403
    assert enabled.status_code == 200
    assert enabled.json()["pass_fail"] == "pass"
    assert "sk-" not in enabled.text


def test_cli_runs_and_redacts_output(capsys) -> None:
    exit_code = cli_main(["--case", "intent_parser_schema"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "pass_fail" in output
    assert "sk-" not in output
