import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.structured_output_reliability import (
    StructuredOutputReliabilityRun,
    StructuredOutputSchemaName,
    StructuredOutputTestCase,
    run_structured_output_reliability,
)
from app.main import app
from app.tools.structured_output_reliability import main as cli_main


def test_fake_valid_json_passes_all_default_schemas() -> None:
    report = run_structured_output_reliability(StructuredOutputReliabilityRun(provider_id="fake"))

    assert report.total_cases == 7
    assert report.valid_json_rate == 1.0
    assert report.schema_valid_rate == 1.0
    assert all(case.ok for case in report.cases)


def test_fake_invalid_json_is_recorded() -> None:
    report = run_structured_output_reliability(
        StructuredOutputReliabilityRun(
            provider_id="fake_invalid_json",
            cases=[
                StructuredOutputTestCase(
                    id="intent_invalid_json",
                    schema_name=StructuredOutputSchemaName.PLAYER_INTENT,
                    retry_once=False,
                )
            ],
        )
    )

    assert report.valid_json_rate == 0.0
    assert report.cases[0].valid_json is False
    assert report.cases[0].schema_valid is False


def test_schema_violation_is_recorded() -> None:
    report = run_structured_output_reliability(
        StructuredOutputReliabilityRun(
            provider_id="fake_schema_violation",
            cases=[
                StructuredOutputTestCase(
                    id="narrator_schema_violation",
                    schema_name=StructuredOutputSchemaName.NARRATIVE_RESULT,
                    retry_once=False,
                )
            ],
        )
    )

    assert report.schema_valid_rate == 0.0
    assert report.invalid_field_rate == 1.0
    assert report.cases[0].invalid_field is True


def test_retry_path_can_succeed() -> None:
    report = run_structured_output_reliability(
        StructuredOutputReliabilityRun(
            provider_id="fake_retry",
            cases=[
                StructuredOutputTestCase(
                    id="retry_intent",
                    schema_name=StructuredOutputSchemaName.PLAYER_INTENT,
                    retry_once=True,
                )
            ],
        )
    )

    assert report.cases[0].retried is True
    assert report.cases[0].retry_succeeded is True
    assert report.retry_success_rate == 1.0
    assert report.schema_valid_rate == 1.0


def test_hidden_policy_violation_is_recorded_and_redacted() -> None:
    report = run_structured_output_reliability(
        StructuredOutputReliabilityRun(
            provider_id="fake_hidden_violation",
            cases=[
                StructuredOutputTestCase(
                    id="hidden_case",
                    schema_name=StructuredOutputSchemaName.MEMORY_SUMMARY,
                    hidden_terms=["the mayor forged the charter"],
                    retry_once=False,
                )
            ],
        )
    )
    payload = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert report.hidden_policy_violation_rate == 1.0
    assert report.cases[0].hidden_policy_violation is True
    assert "the mayor forged the charter" not in payload


def test_structured_output_api_respects_gate() -> None:
    previous_settings = getattr(app.state, "settings", None)
    previous_reports = getattr(app.state, "structured_output_reports", None)
    client = TestClient(app)
    try:
        app.state.structured_output_reports = []
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=False, llm_provider="mock")
        disabled = client.post("/prompt-lab/structured-output/run", json={"provider_id": "fake"})
        app.state.settings = Settings(enable_debug_api=True, enable_perf_logging=False, llm_provider="mock")
        enabled = client.post("/prompt-lab/structured-output/run", json={"provider_id": "fake"})
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        app.state.structured_output_reports = previous_reports or []

    assert disabled.status_code == 403
    assert enabled.status_code == 200
    assert enabled.json()["schema_valid_rate"] == 1.0


def test_cli_runs_and_redacts_output(capsys) -> None:
    exit_code = cli_main(["--provider", "fake", "--schema", "PlayerIntent"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "valid_json_rate" in output
    assert "sk-" not in output
