from app.config import Settings, get_settings
from app.llm.local_provider import LocalHTTPProvider, LocalStubProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider_base import LLMProvider, LLMProviderError


def create_llm_provider(settings: Settings | None = None) -> LLMProvider:
    resolved_settings = settings or get_settings()
    provider_name = resolved_settings.llm_provider.strip().lower()

    if provider_name == "mock":
        return MockLLMProvider()
    if provider_name == "local_stub":
        return LocalStubProvider()
    if provider_name == "local_http":
        return LocalHTTPProvider(settings=resolved_settings)
    if provider_name == "openai":
        return OpenAIProvider(settings=resolved_settings)

    raise LLMProviderError(
        f"Unsupported LLM_PROVIDER: {resolved_settings.llm_provider}. "
        "Supported providers: mock, local_stub, local_http, openai"
    )
