from app.llm.provider_base import LLMProvider, LLMProviderError
from app.llm.prompts import build_intent_parser_messages
from app.llm.schemas import PlayerActionType, PlayerIntent


class IntentParser:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def parse(self, player_text: str) -> PlayerIntent:
        messages = build_intent_parser_messages(player_text)
        try:
            return self._provider.generate_json(
                messages=messages,
                schema=PlayerIntent,
                temperature=0.0,
            )
        except LLMProviderError:
            return PlayerIntent(
                action_type=PlayerActionType.UNKNOWN,
                raw_text=player_text,
                confidence=0.0,
                requires_clarification=True,
                clarification_question="What do you want to do?",
            )

