from app.llm.provider_base import LLMProvider, Message, SchemaT
from app.llm.schemas import NarrativeResult, PlayerActionType, PlayerIntent


class MockLLMProvider(LLMProvider):
    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        return "这是一个本地 mock 叙事响应。"

    def generate_json(
        self,
        messages: list[Message],
        schema: type[SchemaT],
        temperature: float = 0.2,
    ) -> SchemaT:
        if schema is PlayerIntent:
            return schema.model_validate(self._intent_payload(messages))
        if schema is NarrativeResult:
            return schema.model_validate(self._narrative_payload())
        raise ValueError(f"MockLLMProvider does not support schema: {schema.__name__}")

    def _intent_payload(self, messages: list[Message]) -> dict[str, object]:
        text = messages[-1]["content"]
        if "观察" in text or "看" in text:
            return {
                "action_type": PlayerActionType.OBSERVE.value,
                "raw_text": text,
                "confidence": 0.9,
                "requires_clarification": False,
            }
        if "搜索" in text or "search" in text:
            return {
                "action_type": PlayerActionType.SEARCH.value,
                "raw_text": text,
                "confidence": 0.9,
                "requires_clarification": False,
            }
        if "撬锁" in text or "lockpick" in text:
            return {
                "action_type": PlayerActionType.LOCKPICK.value,
                "raw_text": text,
                "confidence": 0.9,
                "requires_clarification": False,
            }
        if "潜行" in text or "sneak" in text:
            return {
                "action_type": PlayerActionType.SNEAK.value,
                "raw_text": text,
                "confidence": 0.9,
                "requires_clarification": False,
            }
        if "铁匠" in text or "smithy" in text:
            return {
                "action_type": PlayerActionType.MOVE.value,
                "target_id": "blacksmith",
                "raw_text": text,
                "confidence": 0.9,
                "requires_clarification": False,
            }
        if "等待" in text or "休息" in text:
            return {
                "action_type": PlayerActionType.WAIT.value,
                "raw_text": text,
                "confidence": 0.8,
                "requires_clarification": False,
            }
        return {
            "action_type": PlayerActionType.UNKNOWN.value,
            "raw_text": text,
            "confidence": 0.1,
            "requires_clarification": False,
        }

    def _narrative_payload(self) -> dict[str, object]:
        return {
            "text": "你稳住脚步，眼前的世界继续展开。",
            "suggested_actions": ["观察四周", "等待片刻"],
            "short_summary": "玩家完成了一次行动。",
        }
