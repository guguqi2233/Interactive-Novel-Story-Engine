from app.engine.actions.schemas import ActionResult
from app.llm.prompts import build_narrator_messages
from app.llm.prompt_profiles import PromptProfile
from app.llm.provider_base import LLMProvider
from app.llm.schemas import NarrativeResult


class Narrator:
    def __init__(self, provider: LLMProvider, prompt_profile: PromptProfile | None = None) -> None:
        self._provider = provider
        self._prompt_profile = prompt_profile

    def render(
        self,
        player_input: str,
        action_result: ActionResult,
        visible_facts: list[str],
        current_location: str,
        tone: str,
        scene_mood_summary: str = "",
    ) -> NarrativeResult:
        prompt_tone = f"{tone}; {scene_mood_summary}" if scene_mood_summary else tone
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
            tone=prompt_tone,
            narrator_style=self._prompt_profile.narrator_style if self._prompt_profile else "",
            prompt_variant=self._prompt_profile.narrator_prompt_variant if self._prompt_profile else "default",
        )
        temperature = (
            self._prompt_profile.temperature_overrides.narrator
            if self._prompt_profile and self._prompt_profile.temperature_overrides.narrator is not None
            else 0.7
        )
        return self._provider.generate_json(
            messages=messages,
            schema=NarrativeResult,
            temperature=temperature,
        )

    def scene_mood_preset_id(self) -> str | None:
        prompt_profile = getattr(self, "_prompt_profile", None)
        return prompt_profile.scene_mood_preset_id if prompt_profile else None

