import pytest
from pydantic import BaseModel

from app.config import Settings
from app.llm.fake_provider import FakeLLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider_base import LLMProviderError


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

