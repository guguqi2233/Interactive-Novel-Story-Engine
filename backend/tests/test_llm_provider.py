from pathlib import Path

import pytest
from pydantic import BaseModel

from app.config import Settings
from app.llm.fake_provider import FakeLLMProvider
from app.llm.local_provider import LocalHTTPProvider, LocalStubProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider_factory import create_llm_provider
from app.llm.provider_base import LLMProviderError
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.engine.actions.schemas import ActionResult, SuccessLevel


class ExampleSchema(BaseModel):
    intent_type: str
    confidence: float


def test_fake_llm_provider_can_return_fixed_json() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "intent_type": "move",
                "confidence": 0.9,
            }
        ]
    )

    result = provider.generate_json(
        messages=[{"role": "user", "content": "Go north."}],
        schema=ExampleSchema,
        temperature=0.0,
    )

    assert result == ExampleSchema(intent_type="move", confidence=0.9)


def test_fake_llm_provider_schema_validation_failure_raises_error() -> None:
    provider = FakeLLMProvider(json_responses=[{"intent_type": "move"}])

    with pytest.raises(LLMProviderError, match="schema validation"):
        provider.generate_json(
            messages=[{"role": "user", "content": "Go north."}],
            schema=ExampleSchema,
            temperature=0.0,
        )


def test_openai_provider_requires_api_key() -> None:
    settings = Settings(llm_provider="openai", llm_model="gpt-4.1-mini", llm_api_key=None)

    with pytest.raises(LLMProviderError, match="LLM_API_KEY is required"):
        OpenAIProvider(settings=settings)


def test_provider_factory_returns_mock_provider() -> None:
    settings = Settings(llm_provider="mock")

    provider = create_llm_provider(settings)

    assert isinstance(provider, MockLLMProvider)


def test_provider_factory_returns_openai_provider_with_config() -> None:
    settings = Settings(
        llm_provider="openai",
        llm_model="gpt-4.1-mini",
        llm_api_key="test-key-not-used",
    )

    provider = create_llm_provider(settings)

    assert isinstance(provider, OpenAIProvider)


def test_provider_factory_openai_without_api_key_fails_clearly() -> None:
    settings = Settings(llm_provider="openai", llm_model="gpt-4.1-mini", llm_api_key=None)

    with pytest.raises(LLMProviderError, match="LLM_API_KEY is required"):
        create_llm_provider(settings)


def test_provider_factory_unknown_provider_fails_clearly() -> None:
    settings = Settings(llm_provider="local-file")

    with pytest.raises(LLMProviderError, match="Unsupported LLM_PROVIDER: local-file"):
        create_llm_provider(settings)


def test_provider_factory_returns_local_stub_provider() -> None:
    settings = Settings(llm_provider="local_stub")

    provider = create_llm_provider(settings)

    assert isinstance(provider, LocalStubProvider)


def test_provider_factory_local_http_without_base_url_fails_clearly() -> None:
    settings = Settings(llm_provider="local_http", local_llm_base_url=None)

    with pytest.raises(LLMProviderError, match="LOCAL_LLM_BASE_URL is required"):
        create_llm_provider(settings)


def test_provider_factory_returns_local_http_with_config() -> None:
    settings = Settings(
        llm_provider="local_http",
        local_llm_base_url="http://127.0.0.1:11434",
        local_llm_model="local-test-model",
        local_llm_timeout_seconds=1.5,
        local_llm_json_mode=False,
    )

    provider = create_llm_provider(settings)

    assert isinstance(provider, LocalHTTPProvider)
    assert provider.base_url == "http://127.0.0.1:11434"
    assert provider.model == "local-test-model"
    assert provider.timeout_seconds == 1.5
    assert provider.json_mode is False


def test_local_http_generate_text_uses_fake_transport() -> None:
    requests: list[tuple[str, dict[str, object], float]] = []

    def fake_transport(url: str, payload: dict[str, object], timeout: float) -> dict[str, object]:
        requests.append((url, payload, timeout))
        return {"choices": [{"message": {"content": "local hello"}}]}

    provider = LocalHTTPProvider(
        settings=Settings(
            llm_provider="local_http",
            local_llm_base_url="http://localhost:9999/",
            local_llm_model="test-local",
            local_llm_timeout_seconds=2.0,
        ),
        transport=fake_transport,
    )

    text = provider.generate_text(messages=[{"role": "user", "content": "hello"}], temperature=0.1)

    assert text == "local hello"
    assert requests[0][0] == "http://localhost:9999/chat/completions"
    assert requests[0][1]["model"] == "test-local"
    assert requests[0][1]["messages"] == [{"role": "user", "content": "hello"}]
    assert "response_format" not in requests[0][1]
    assert requests[0][2] == 2.0


def test_local_http_generate_json_uses_schema_validation() -> None:
    requests: list[dict[str, object]] = []

    def fake_transport(url: str, payload: dict[str, object], timeout: float) -> dict[str, object]:
        requests.append(payload)
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"intent_type": "observe", "confidence": 0.88}',
                    }
                }
            ]
        }

    provider = LocalHTTPProvider(
        settings=Settings(
            llm_provider="local_http",
            local_llm_base_url="http://localhost:9999",
            local_llm_json_mode=True,
        ),
        transport=fake_transport,
    )

    result = provider.generate_json(
        messages=[{"role": "user", "content": "look"}],
        schema=ExampleSchema,
        temperature=0.0,
    )

    assert result == ExampleSchema(intent_type="observe", confidence=0.88)
    assert requests[0]["response_format"] == {"type": "json_object"}


def test_local_http_generate_json_schema_failure_is_clear() -> None:
    def fake_transport(url: str, payload: dict[str, object], timeout: float) -> dict[str, object]:
        return {"choices": [{"message": {"content": '{"intent_type": "observe"}'}}]}

    provider = LocalHTTPProvider(
        settings=Settings(
            llm_provider="local_http",
            local_llm_base_url="http://localhost:9999",
        ),
        transport=fake_transport,
    )

    with pytest.raises(LLMProviderError, match="schema validation"):
        provider.generate_json(
            messages=[{"role": "user", "content": "look"}],
            schema=ExampleSchema,
        )


def test_local_http_generate_json_parse_failure_is_clear() -> None:
    def fake_transport(url: str, payload: dict[str, object], timeout: float) -> dict[str, object]:
        return {"choices": [{"message": {"content": "not json"}}]}

    provider = LocalHTTPProvider(
        settings=Settings(
            llm_provider="local_http",
            local_llm_base_url="http://localhost:9999",
        ),
        transport=fake_transport,
    )

    with pytest.raises(LLMProviderError, match="could not be parsed"):
        provider.generate_json(
            messages=[{"role": "user", "content": "look"}],
            schema=ExampleSchema,
        )


def test_business_code_does_not_directly_instantiate_local_http_provider() -> None:
    backend_root = Path(__file__).resolve().parents[1] / "app"
    allowed = {
        backend_root / "llm" / "local_provider.py",
        backend_root / "llm" / "provider_factory.py",
    }

    offenders: list[str] = []
    for path in backend_root.rglob("*.py"):
        if path in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        if "LocalHTTPProvider(" in text:
            offenders.append(str(path.relative_to(backend_root)))

    assert offenders == []


def test_local_stub_can_parse_intent_and_render_narrative() -> None:
    provider = LocalStubProvider()

    intent = IntentParser(provider).parse("search the square")
    narrative = Narrator(provider).render(
        player_input="search the square",
        action_result=ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Search resolved by rules.",
            visible_facts=["square"],
        ),
        visible_facts=["square"],
        current_location="village_square",
        tone="quiet",
    )

    assert intent.action_type == "search"
    assert "本地模型占位叙事" in narrative.text


def test_local_stub_schema_validation_failure_is_clear() -> None:
    provider = LocalStubProvider(invalid_json=True)

    with pytest.raises(LLMProviderError, match="schema validation"):
        provider.generate_json(
            messages=[{"role": "user", "content": "search"}],
            schema=ExampleSchema,
        )

