from app.llm.provider_base import LLMProvider, Message, SchemaT
from app.llm.schemas import NarrativeResult, PlayerActionType, PlayerIntent


class PlaytestLLMProvider(LLMProvider):
    """Deterministic provider used only by local playtesting.

    It parses a small command language so playtests exercise the normal
    IntentParser/Narrator/GameLoop path without calling a real model.
    """

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        return "playtest narration"

    def generate_json(
        self,
        messages: list[Message],
        schema: type[SchemaT],
        temperature: float = 0.2,
    ) -> SchemaT:
        latest = messages[-1]["content"] if messages else ""
        if schema is PlayerIntent:
            return schema.model_validate(_parse_intent(latest))
        if schema is NarrativeResult:
            return schema.model_validate(
                {
                    "text": "测试代理观察到一次规则结算。",
                    "suggested_actions": ["observe", "search"],
                    "short_summary": "Playtest step rendered.",
                }
            )
        return schema.model_validate({})


def _parse_intent(raw_text: str) -> dict[str, object]:
    text = raw_text.strip()
    lowered = text.lower()
    words = lowered.split()
    action_word = words[0] if words else ""
    target_id = words[1] if len(words) > 1 else None
    minutes = _extract_minutes(words)

    action_type = {
        "observe": PlayerActionType.OBSERVE,
        "look": PlayerActionType.OBSERVE,
        "search": PlayerActionType.SEARCH,
        "lockpick": PlayerActionType.LOCKPICK,
        "sneak": PlayerActionType.SNEAK,
        "attack": PlayerActionType.ATTACK,
        "defend": PlayerActionType.DEFEND,
        "flee": PlayerActionType.FLEE,
        "buy": PlayerActionType.BUY,
        "sell": PlayerActionType.SELL,
        "move": PlayerActionType.MOVE,
        "go": PlayerActionType.MOVE,
        "talk": PlayerActionType.TALK,
        "use": PlayerActionType.USE_ITEM,
        "wait": PlayerActionType.WAIT,
    }.get(action_word, PlayerActionType.UNKNOWN)

    if "smithy" in lowered or "blacksmith" in lowered:
        if action_type in {PlayerActionType.MOVE, PlayerActionType.UNKNOWN}:
            action_type = PlayerActionType.MOVE
        target_id = "blacksmith"
    if "square" in lowered:
        if action_type in {PlayerActionType.MOVE, PlayerActionType.UNKNOWN}:
            action_type = PlayerActionType.MOVE
        target_id = "village_square"

    return {
        "action_type": action_type,
        "raw_text": text,
        "confidence": 1.0,
        "requires_clarification": False,
        "target_id": target_id,
        "minutes": minutes,
    }


def _extract_minutes(words: list[str]) -> int | None:
    for word in words:
        if word.isdigit():
            return int(word)
    return None
