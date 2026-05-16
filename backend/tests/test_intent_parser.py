from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.schemas import PlayerActionType


def test_observe_room_parses_as_observe() -> None:
    parser = IntentParser(
        FakeLLMProvider(
            json_responses=[
                {
                    "action_type": "observe",
                    "raw_text": "观察房间",
                    "confidence": 0.95,
                    "requires_clarification": False,
                }
            ]
        )
    )

    intent = parser.parse("观察房间")

    assert intent.action_type == PlayerActionType.OBSERVE
    assert intent.raw_text == "观察房间"


def test_go_to_blacksmith_parses_as_move() -> None:
    parser = IntentParser(
        FakeLLMProvider(
            json_responses=[
                {
                    "action_type": "move",
                    "target_id": "blacksmith",
                    "raw_text": "去铁匠铺",
                    "confidence": 0.92,
                    "requires_clarification": False,
                }
            ]
        )
    )

    intent = parser.parse("去铁匠铺")

    assert intent.action_type == PlayerActionType.MOVE
    assert intent.target_id == "blacksmith"


def test_ambiguous_input_can_require_clarification() -> None:
    parser = IntentParser(
        FakeLLMProvider(
            json_responses=[
                {
                    "action_type": "unknown",
                    "raw_text": "那个",
                    "confidence": 0.2,
                    "requires_clarification": True,
                    "clarification_question": "你想检查、移动，还是和某人交谈？",
                }
            ]
        )
    )

    intent = parser.parse("那个")

    assert intent.action_type == PlayerActionType.UNKNOWN
    assert intent.requires_clarification is True
    assert intent.clarification_question == "你想检查、移动，还是和某人交谈？"


def test_schema_error_is_caught_as_unknown_intent() -> None:
    parser = IntentParser(
        FakeLLMProvider(
            json_responses=[
                {
                    "action_type": "move",
                    "raw_text": "去铁匠铺",
                    "requires_clarification": False,
                }
            ]
        )
    )

    intent = parser.parse("去铁匠铺")

    assert intent.action_type == PlayerActionType.UNKNOWN
    assert intent.requires_clarification is True
    assert intent.confidence == 0.0

