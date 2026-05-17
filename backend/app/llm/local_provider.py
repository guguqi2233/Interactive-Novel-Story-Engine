from pydantic import ValidationError

from app.config import Settings
from app.llm.provider_base import LLMProvider, LLMProviderError, Message, SchemaT
from app.llm.schemas import NarrativeResult, PlayerActionType, PlayerIntent


class LocalStubProvider(LLMProvider):
    """Mock-compatible local provider for tests and offline development."""

    def __init__(self, invalid_json: bool = False) -> None:
        self.invalid_json = invalid_json

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        return "local stub text"

    def generate_json(
        self,
        messages: list[Message],
        schema: type[SchemaT],
        temperature: float = 0.2,
    ) -> SchemaT:
        payload = self._payload_for_schema(messages, schema)
        try:
            return schema.model_validate(payload)
        except ValidationError as exc:
            raise LLMProviderError("LocalStubProvider JSON output failed schema validation") from exc

    def _payload_for_schema(self, messages: list[Message], schema: type[SchemaT]) -> dict[str, object]:
        if self.invalid_json:
            return {"invalid": "payload"}
        latest = messages[-1]["content"].lower() if messages else ""
        if schema is PlayerIntent:
            if "search" in latest:
                action_type = PlayerActionType.SEARCH
            elif "smithy" in latest or "blacksmith" in latest:
                return {
                    "action_type": PlayerActionType.MOVE.value,
                    "target_id": "blacksmith",
                    "raw_text": latest,
                    "confidence": 0.9,
                    "requires_clarification": False,
                }
            elif "wait" in latest:
                action_type = PlayerActionType.WAIT
            else:
                action_type = PlayerActionType.OBSERVE
            return {
                "action_type": action_type.value,
                "raw_text": latest,
                "confidence": 0.9,
                "requires_clarification": False,
            }
        if schema is NarrativeResult:
            return {
                "text": "本地模型占位叙事：世界规则已经完成结算。",
                "suggested_actions": ["observe", "search"],
                "short_summary": "Local stub narrator response.",
            }
        raise LLMProviderError(f"LocalStubProvider does not support schema: {schema.__name__}")


class LocalHTTPProvider(LLMProvider):
    """Configuration-checked placeholder for a future local HTTP model provider."""

    def __init__(self, settings: Settings) -> None:
        if not settings.local_llm_base_url:
            raise LLMProviderError("LOCAL_LLM_BASE_URL is required when LLM_PROVIDER=local_http")
        self.base_url = settings.local_llm_base_url
        self.model = settings.local_llm_model
        self.timeout_seconds = settings.local_llm_timeout_seconds

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        raise LLMProviderError(
            "LocalHTTPProvider is a v0.6 interface stub and does not call a local service yet"
        )

    def generate_json(
        self,
        messages: list[Message],
        schema: type[SchemaT],
        temperature: float = 0.2,
    ) -> SchemaT:
        raise LLMProviderError(
            "LocalHTTPProvider is a v0.6 interface stub and does not call a local service yet"
        )
