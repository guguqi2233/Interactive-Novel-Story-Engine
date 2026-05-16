from app.core.event_log import Event
from app.llm.prompts import build_memory_summarizer_messages
from app.llm.provider_base import LLMProvider
from app.llm.schemas import MemorySummary


class MemorySummarizer:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

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
                "state_deltas": [delta.model_dump(mode="json") for delta in event.state_deltas],
            }
            for event in recent_events
        ]
        return self._provider.generate_json(
            messages=build_memory_summarizer_messages(events_payload),
            schema=MemorySummary,
            temperature=0.2,
        )
