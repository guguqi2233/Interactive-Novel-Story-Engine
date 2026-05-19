import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.fake_provider import FakeLLMProvider
from app.llm.provider_base import LLMProvider, Message, SchemaT
from app.llm.provider_factory import create_llm_provider
from app.llm.schemas import NarrativeResult
from app.llm.usage_tracker import get_model_usage_store, wrap_provider_for_usage_tracking
from app.main import app


def setup_function() -> None:
    store = get_model_usage_store()
    store.clear()
    store.enabled = False


def teardown_function() -> None:
    store = get_model_usage_store()
    store.clear()
    store.enabled = False


def test_tracking_disabled_has_no_side_effect() -> None:
    provider = wrap_provider_for_usage_tracking(
        FakeLLMProvider(text_responses=["safe output"]),
        provider_id="fake",
        model_id="fake",
        enabled=False,
    )

    assert provider.generate_text([{"role": "user", "content": "hello"}]) == "safe output"
    assert get_model_usage_store().recent() == []


def test_tracking_enabled_records_usage() -> None:
    provider = wrap_provider_for_usage_tracking(
        FakeLLMProvider(text_responses=["safe output"]),
        provider_id="fake",
        model_id="fake-model",
        enabled=True,
        input_cost_per_1k=0.1,
        output_cost_per_1k=0.2,
    )

    provider.generate_text([{"role": "user", "content": "hello world"}])
    records = get_model_usage_store().recent()

    assert len(records) == 1
    assert records[0].provider_id == "fake"
    assert records[0].model_id == "fake-model"
    assert records[0].use_case == "generate_text"
    assert records[0].input_tokens_estimated > 0
    assert records[0].output_tokens_estimated > 0
    assert records[0].success is True


def test_summary_is_correct() -> None:
    provider = wrap_provider_for_usage_tracking(
        FakeLLMProvider(text_responses=["one", "two"]),
        provider_id="fake",
        model_id="fake",
        enabled=True,
    )

    provider.generate_text([{"role": "user", "content": "first"}])
    provider.generate_text([{"role": "user", "content": "second"}])
    summary = get_model_usage_store().summary()

    assert summary.enabled is True
    assert summary.total_calls == 2
    assert summary.successes == 2
    assert summary.failures == 0
    assert summary.by_use_case[0].use_case == "generate_text"
    assert summary.by_use_case[0].count == 2


def test_tracker_does_not_record_api_key_or_raw_prompt() -> None:
    provider = wrap_provider_for_usage_tracking(
        FakeLLMProvider(text_responses=["safe output"]),
        provider_id="fake",
        model_id="fake",
        enabled=True,
    )

    provider.generate_text([{"role": "user", "content": "LLM_API_KEY=sk-real-looking-secret hidden fact text"}])
    payload = json.dumps([record.safe_dict() for record in get_model_usage_store().recent()], ensure_ascii=False)

    assert "sk-real-looking-secret" not in payload
    assert "hidden fact text" not in payload
    assert "LLM_API_KEY" not in payload


def test_failure_records_error_type() -> None:
    provider = wrap_provider_for_usage_tracking(
        _FailingProvider(),
        provider_id="fake",
        model_id="fake",
        enabled=True,
    )

    with pytest.raises(RuntimeError):
        provider.generate_text([{"role": "user", "content": "safe"}])
    records = get_model_usage_store().recent()

    assert len(records) == 1
    assert records[0].success is False
    assert records[0].error_type == "RuntimeError"


def test_provider_factory_wraps_only_when_enabled() -> None:
    disabled = create_llm_provider(Settings(llm_provider="local_stub", enable_usage_tracking=False))
    enabled = create_llm_provider(Settings(llm_provider="local_stub", enable_usage_tracking=True))

    assert disabled.__class__.__name__ != "UsageTrackingProvider"
    assert enabled.__class__.__name__ == "UsageTrackingProvider"


def test_usage_api_returns_safe_summary() -> None:
    client = TestClient(app)
    previous_settings = getattr(app.state, "settings", None)
    try:
        app.state.settings = Settings(enable_debug_api=False, enable_usage_tracking=False, llm_provider="mock")
        disabled = client.get("/prompt-lab/usage/summary")
        app.state.settings = Settings(enable_debug_api=False, enable_usage_tracking=True, llm_provider="mock")
        provider = wrap_provider_for_usage_tracking(
            FakeLLMProvider(text_responses=["safe output"]),
            provider_id="fake",
            model_id="fake",
            enabled=True,
        )
        provider.generate_text([{"role": "user", "content": "LLM_API_KEY=sk-real-looking-secret"}])
        recent = client.get("/prompt-lab/usage/recent")
        summary = client.get("/prompt-lab/usage/summary")
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")

    assert disabled.status_code == 403
    assert recent.status_code == 200
    assert summary.status_code == 200
    assert "sk-real-looking-secret" not in recent.text
    assert summary.json()["total_calls"] >= 1


class _FailingProvider(LLMProvider):
    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        _ = messages, temperature
        raise RuntimeError("provider failed without prompt")

    def generate_json(self, messages: list[Message], schema: type[SchemaT], temperature: float = 0.2) -> SchemaT:
        _ = messages, temperature
        return schema.model_validate({"text": "safe", "suggested_actions": [], "short_summary": "safe"})  # type: ignore[return-value]
