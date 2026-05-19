from pathlib import Path

import pytest

from app.config import Settings
from app.llm.provider_capabilities import ProviderCapabilityRegistry, ProviderType
from app.llm.provider_factory import create_llm_provider


def test_registry_lists_mock_local_and_openai_compatible() -> None:
    registry = ProviderCapabilityRegistry()

    provider_ids = {provider.provider_id for provider in registry.list_providers()}
    provider_types = {provider.provider_type for provider in registry.list_providers()}

    assert {"mock", "local_stub", "local_http", "openai", "openai_compatible"}.issubset(provider_ids)
    assert ProviderType.MOCK in provider_types
    assert ProviderType.LOCAL_STUB in provider_types
    assert ProviderType.LOCAL_HTTP in provider_types
    assert ProviderType.OPENAI_COMPATIBLE in provider_types


def test_validate_model_for_use_case() -> None:
    registry = ProviderCapabilityRegistry()

    structured = registry.validate_model_for_use_case("local_stub", "local_stub", "structured_output")
    embeddings = registry.validate_model_for_use_case("local_stub", "local_stub", "embeddings")
    unusual = registry.validate_model_for_use_case("local_stub", "local_stub", "rp_expression")

    assert structured.allowed
    assert not structured.blockers
    assert not embeddings.allowed
    assert "model_does_not_support_embeddings" in embeddings.blockers
    assert unusual.allowed
    assert "use_case_not_recommended" in unusual.warnings


def test_safe_summary_does_not_include_api_key_or_raw_base_url() -> None:
    registry = ProviderCapabilityRegistry()
    settings = Settings(
        llm_provider="local_http",
        llm_api_key="sk-real-looking-test-secret",
        local_llm_base_url="http://localhost:11434/v1?token=sk-secret",
        local_llm_model="local-test-model",
    )

    summary = registry.safe_summary_for_frontend(settings)
    rendered = str(summary)

    assert summary["api_key_configured"] is True
    assert summary["local_http_configured"] is True
    assert summary["current_model"] == "local-test-model"
    assert "sk-real-looking-test-secret" not in rendered
    assert "sk-secret" not in rendered
    assert "localhost:11434" not in rendered


def test_unknown_provider_returns_clear_error() -> None:
    registry = ProviderCapabilityRegistry()

    with pytest.raises(ValueError, match="Unknown provider capability: unknown"):
        registry.list_models("unknown")

    with pytest.raises(ValueError, match="Unknown model capability: local_stub/missing-model"):
        registry.get_capability("local_stub", "missing-model")


def test_provider_factory_reads_registry_and_remains_provider_entry() -> None:
    provider = create_llm_provider(Settings(llm_provider="local_stub"))

    assert provider.__class__.__name__ == "LocalStubProvider"


def test_business_code_still_does_not_directly_instantiate_concrete_providers() -> None:
    backend_root = Path(__file__).resolve().parents[1] / "app"
    allowed = {
        backend_root / "llm" / "local_provider.py",
        backend_root / "llm" / "openai_provider.py",
        backend_root / "llm" / "mock_provider.py",
        backend_root / "llm" / "fake_provider.py",
        backend_root / "llm" / "provider_factory.py",
    }
    concrete_calls = ("OpenAIProvider(", "LocalHTTPProvider(", "LocalStubProvider(", "MockLLMProvider(")

    offenders: list[str] = []
    for path in backend_root.rglob("*.py"):
        if path in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        if any(call in text for call in concrete_calls):
            offenders.append(str(path.relative_to(backend_root)))

    assert offenders == []
