import json
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.model_compatibility import (
    ModelCompatibilityUseCase,
    build_model_compatibility_matrix,
)
from app.llm.provider_benchmark import ProviderBenchmarkReport
from app.llm.provider_capabilities import (
    ModelCapability,
    ProviderCapability,
    ProviderCapabilityRegistry,
    ProviderType,
)
from app.llm.structured_output_reliability import StructuredOutputReliabilityReport
from app.llm.usage_tracker import ModelUsageRecord
from app.main import app


def test_matrix_can_be_generated_from_declared_capabilities() -> None:
    matrix = build_model_compatibility_matrix()

    assert matrix.rows
    assert ModelCompatibilityUseCase.INTENT_PARSER in matrix.use_cases
    assert any(row.provider_id == "local_stub" and row.model_id == "local_stub" for row in matrix.rows)
    assert matrix.source_summary["real_provider_calls_performed"] is False


def test_unsupported_embedding_use_case_is_marked() -> None:
    matrix = build_model_compatibility_matrix()

    row = _row(matrix, "local_stub", "local_stub", ModelCompatibilityUseCase.EMBEDDING)

    assert row.unsupported is True
    assert row.supported is False
    assert "model_does_not_support_embeddings" in row.reason


def test_structured_json_low_reliability_model_is_caution() -> None:
    registry = ProviderCapabilityRegistry(
        providers=[ProviderCapability(provider_id="low_json", provider_type=ProviderType.MOCK)],
        models=[
            ModelCapability(
                provider_id="low_json",
                provider_type=ProviderType.MOCK,
                model_id="low-json-model",
                recommended_use_cases=["structured_output"],
                supports_json=True,
            )
        ],
    )
    structured_report = StructuredOutputReliabilityReport(
        run_id="low-json-report",
        provider_id="low_json",
        model_id="low-json-model",
        total_cases=10,
        schema_valid_rate=0.7,
    )

    matrix = build_model_compatibility_matrix(
        registry=registry,
        structured_reports=[structured_report],
    )
    row = _row(matrix, "low_json", "low-json-model", ModelCompatibilityUseCase.STRUCTURED_JSON)

    assert row.supported is True
    assert row.caution is True
    assert "structured_output_reliability_low" in row.reason
    assert row.last_tested_at is not None


def test_high_latency_model_is_caution() -> None:
    registry = ProviderCapabilityRegistry(
        providers=[ProviderCapability(provider_id="slow", provider_type=ProviderType.LOCAL_STUB)],
        models=[
            ModelCapability(
                provider_id="slow",
                provider_type=ProviderType.LOCAL_STUB,
                model_id="slow-model",
                recommended_use_cases=["narration"],
            )
        ],
    )
    usage_record = ModelUsageRecord(
        provider_id="slow",
        model_id="slow-model",
        use_case="generate_text",
        started_at=datetime.now(timezone.utc),
        duration_ms=2500.0,
    )

    matrix = build_model_compatibility_matrix(registry=registry, usage_records=[usage_record])
    row = _row(matrix, "slow", "slow-model", ModelCompatibilityUseCase.NARRATOR)

    assert row.supported is True
    assert row.caution is True
    assert "latency_high" in row.reason


def test_benchmark_hidden_leak_report_marks_caution_and_safe_dump_redacts() -> None:
    registry = ProviderCapabilityRegistry(
        providers=[ProviderCapability(provider_id="mock_hidden", provider_type=ProviderType.MOCK)],
        models=[
            ModelCapability(
                provider_id="mock_hidden",
                provider_type=ProviderType.MOCK,
                model_id="mock_hidden",
                recommended_use_cases=["structured_output"],
            )
        ],
    )
    report = ProviderBenchmarkReport(
        run_id="bench-hidden",
        provider_id="mock_hidden",
        model_id="mock_hidden",
        hidden_leak_risk_count=1,
        warnings=["hidden fact: the mayor forged the charter", "sk-real-looking-secret"],
    )

    matrix = build_model_compatibility_matrix(registry=registry, benchmark_reports=[report])
    row = _row(matrix, "mock_hidden", "mock_hidden", ModelCompatibilityUseCase.STRUCTURED_JSON)
    payload = json.dumps(matrix.model_dump_safe(), ensure_ascii=False)

    assert row.caution is True
    assert "hidden_leak_risk_reported" in row.reason
    assert "the mayor forged the charter" not in payload
    assert "sk-real-looking-secret" not in payload


def test_model_compatibility_api_respects_gate_and_returns_safe_payload() -> None:
    client = TestClient(app)
    previous_settings = getattr(app.state, "settings", None)
    previous_benchmarks = getattr(app.state, "provider_benchmark_reports", None)
    previous_structured = getattr(app.state, "structured_output_reports", None)
    previous_matrix = getattr(app.state, "model_compatibility_reports", None)
    try:
        app.state.provider_benchmark_reports = []
        app.state.structured_output_reports = []
        app.state.model_compatibility_reports = []
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=False, llm_provider="mock")
        disabled = client.get("/prompt-lab/model-compatibility")
        app.state.settings = Settings(enable_debug_api=True, enable_perf_logging=False, llm_provider="mock")
        fetched = client.get("/prompt-lab/model-compatibility")
        recomputed = client.post("/prompt-lab/model-compatibility/recompute")
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        app.state.provider_benchmark_reports = previous_benchmarks or []
        app.state.structured_output_reports = previous_structured or []
        app.state.model_compatibility_reports = previous_matrix or []

    assert disabled.status_code == 403
    assert fetched.status_code == 200
    assert recomputed.status_code == 200
    assert fetched.json()["local_only"] is True
    assert fetched.json()["rows"]
    assert "sk-" not in fetched.text
    assert "api_key" not in fetched.text.lower()


def _row(matrix, provider_id: str, model_id: str, use_case: ModelCompatibilityUseCase):
    for row in matrix.rows:
        if row.provider_id == provider_id and row.model_id == model_id and row.use_case == use_case:
            return row
    raise AssertionError(f"Missing compatibility row: {provider_id}/{model_id}/{use_case.value}")
