from app.llm.provider_base import LLMProvider, LLMProviderError
from app.llm.prompts import build_intent_parser_messages
from app.llm.prompt_profiles import PromptProfile
from app.llm.schemas import PlayerActionType, PlayerIntent


class IntentParser:
    def __init__(self, provider: LLMProvider, prompt_profile: PromptProfile | None = None) -> None:
        self._provider = provider
        self._prompt_profile = prompt_profile

    def parse(self, player_text: str) -> PlayerIntent:
        messages = build_intent_parser_messages(
            player_text,
            prompt_variant=self._prompt_profile.intent_parser_prompt_variant if self._prompt_profile else "default",
        )
        temperature = (
            self._prompt_profile.temperature_overrides.intent_parser
            if self._prompt_profile and self._prompt_profile.temperature_overrides.intent_parser is not None
            else 0.0
        )
        try:
            return self._provider.generate_json(
                messages=messages,
                schema=PlayerIntent,
                temperature=temperature,
            )
        except LLMProviderError:
            return PlayerIntent(
                action_type=PlayerActionType.UNKNOWN,
                raw_text=player_text,
                confidence=0.0,
                requires_clarification=True,
                clarification_question="What do you want to do?",
            )

