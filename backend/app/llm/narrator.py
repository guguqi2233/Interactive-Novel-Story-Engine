from app.engine.actions.schemas import ActionResult
from app.llm.prompts import build_narrator_messages
from app.llm.provider_base import LLMProvider
from app.llm.schemas import NarrativeResult


class Narrator:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def render(
        self,
        player_input: str,
        action_result: ActionResult,
        visible_facts: list[str],
        current_location: str,
        tone: str,
    ) -> NarrativeResult:
        safe_action_result = {
            "success_level": action_result.success_level.value,
            "reason": action_result.reason,
            "visible_facts": action_result.visible_facts,
        }
        messages = build_narrator_messages(
            player_input=player_input,
            action_result_payload=safe_action_result,
            visible_facts=visible_facts,
            current_location=current_location,
            tone=tone,
        )
        return self._provider.generate_json(
            messages=messages,
            schema=NarrativeResult,
            temperature=0.7,
        )

