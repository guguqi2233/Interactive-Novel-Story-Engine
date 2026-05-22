from app.core.event_log import Event
from app.llm.prompts import build_memory_summarizer_messages
from app.llm.prompt_profiles import PromptProfile
from app.llm.provider_base import LLMProvider
from app.llm.schemas import MemorySummary


class MemorySummarizer:
    def __init__(self, provider: LLMProvider, prompt_profile: PromptProfile | None = None) -> None:
        self._provider = provider
        self._prompt_profile = prompt_profile

    def summarize_recent(self, events: list[Event], limit: int) -> MemorySummary:
        recent_events = events[-limit:] if limit > 0 else []
        events_payload = [
            {
                "event_id": event.event_id,
                "turn": event.turn,
                "actor_id": event.actor_id,
                "action_type": event.action_type,
                "target_id": event.target_id,
                "result": event.result,
                "input_text": event.input_text,
                "narrative_text": event.narrative_text,
                "state_delta_count": len(event.state_deltas),
            }
            for event in recent_events
        ]
        return self._provider.generate_json(
            messages=build_memory_summarizer_messages(
                events_payload,
                prompt_variant=self._prompt_profile.memory_prompt_variant if self._prompt_profile else "default",
            ),
            schema=MemorySummary,
            temperature=(
                self._prompt_profile.temperature_overrides.memory
                if self._prompt_profile and self._prompt_profile.temperature_overrides.memory is not None
                else 0.2
            ),
        )
