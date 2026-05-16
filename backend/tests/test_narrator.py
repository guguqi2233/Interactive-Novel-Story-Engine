from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.llm.fake_provider import FakeLLMProvider
from app.llm.narrator import Narrator
from app.llm.provider_base import LLMProviderError
from app.llm.schemas import NarrativeResult


def test_narrator_returns_valid_narrative_result() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "text": "你环顾广场，井沿覆着潮湿的苔痕。",
                "suggested_actions": ["查看水井", "前往铁匠铺"],
                "short_summary": "玩家观察了广场。",
            }
        ]
    )
    narrator = Narrator(provider)

    result = narrator.render(
        player_input="观察房间",
        action_result=ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Observed current location.",
            visible_facts=["square", "well"],
            hidden_facts=["secret_trapdoor"],
        ),
        visible_facts=["square", "well"],
        current_location="square",
        tone="冷静、克制",
    )

    assert result == NarrativeResult(
        text="你环顾广场，井沿覆着潮湿的苔痕。",
        suggested_actions=["查看水井", "前往铁匠铺"],
        short_summary="玩家观察了广场。",
    )


def test_narrator_does_not_send_hidden_facts_to_provider() -> None:
    provider = RecordingFakeNarratorProvider(
        json_response={
            "text": "你只看见水井。",
            "suggested_actions": ["查看水井"],
            "short_summary": "玩家看见水井。",
        }
    )
    narrator = Narrator(provider)

    narrator.render(
        player_input="观察",
        action_result=ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Observed current location.",
            visible_facts=["well"],
            hidden_facts=["secret_trapdoor"],
        ),
        visible_facts=["well"],
        current_location="square",
        tone="朴素",
    )

    prompt_text = str(provider.messages)
    assert "well" in prompt_text
    assert "secret_trapdoor" not in prompt_text
    assert "hidden_facts" not in prompt_text


def test_narrator_schema_error_is_not_silent() -> None:
    provider = FakeLLMProvider(json_responses=[{"text": "缺少摘要"}])
    narrator = Narrator(provider)

    try:
        narrator.render(
            player_input="等待",
            action_result=ActionResult(
                success_level=SuccessLevel.SUCCESS,
                reason="Time passes.",
                visible_facts=["turn:2"],
            ),
            visible_facts=["turn:2"],
            current_location="square",
            tone="简洁",
        )
    except LLMProviderError as exc:
        assert "schema validation" in str(exc)
    else:
        raise AssertionError("Narrator schema errors must not be silent")


class RecordingFakeNarratorProvider(FakeLLMProvider):
    def __init__(self, json_response: dict[str, object]) -> None:
        super().__init__(json_responses=[json_response])
        self.messages: list[dict[str, str]] = []

    def generate_json(
        self,
        messages: list[dict[str, str]],
        schema: type[NarrativeResult],
        temperature: float = 0.2,
    ) -> NarrativeResult:
        self.messages = messages
        return super().generate_json(messages, schema, temperature)

