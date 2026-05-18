import json

from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.evals.narrative_consistency import (
    NarrativeConsistencyCase,
    NarrativeConsistencyRule,
    evaluate_narrative_consistency,
    run_narrative_consistency_evals,
)
from app.llm.prompts import build_narrator_messages
from app.llm.schemas import NarrativeResult


HIDDEN_WITNESS_ID = "hidden_watcher"
HIDDEN_WITNESS_TEXT = "hidden witness saw the theft"


def _case(text: str, **kwargs: object) -> NarrativeConsistencyCase:
    return NarrativeConsistencyCase(
        id="case",
        action_result=ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="The action succeeded.",
            visible_facts=["public_square"],
        ),
        narrative=NarrativeResult(text=text, suggested_actions=["observe"], short_summary="Test narrative."),
        known_items=["brass_key"],
        known_locations=["square"],
        known_quest_stages=["quest:start"],
        **kwargs,
    )


def test_correct_narrative_passes() -> None:
    result = evaluate_narrative_consistency(
        _case(
            "The player unlocks the gate in the square with the brass_key. The quest remains at quest:start.",
            timeline_facts=["gate_unlocked"],
            authoritative_facts=["gate_unlocked"],
        )
    )

    assert result.passed
    assert result.failure_reasons == []


def test_dead_npc_speaking_fails() -> None:
    result = evaluate_narrative_consistency(
        _case("harlan says the path is safe.", dead_npc_ids=["harlan"])
    )

    assert not result.passed
    assert any(NarrativeConsistencyRule.NO_DEAD_NPC_SPEAKING in reason for reason in result.failure_reasons)


def test_invented_item_fails() -> None:
    result = evaluate_narrative_consistency(
        _case("The player raises the moon_sword.", invented_item_terms=["moon_sword"])
    )

    assert not result.passed
    assert any(NarrativeConsistencyRule.NO_ITEM_INVENTED in reason for reason in result.failure_reasons)


def test_invented_location_fails() -> None:
    result = evaluate_narrative_consistency(
        _case("The path opens into the crystal_palace.", invented_location_terms=["crystal_palace"])
    )

    assert not result.passed
    assert any(NarrativeConsistencyRule.NO_LOCATION_INVENTED in reason for reason in result.failure_reasons)


def test_invented_quest_stage_fails() -> None:
    result = evaluate_narrative_consistency(
        _case("The quest advances to quest:royal_banquet.", invented_quest_stage_terms=["quest:royal_banquet"])
    )

    assert not result.passed
    assert any(NarrativeConsistencyRule.NO_QUEST_STAGE_INVENTED in reason for reason in result.failure_reasons)


def test_hidden_witness_reveal_fails_and_redacts_reason() -> None:
    result = evaluate_narrative_consistency(
        _case(
            f"The narrator reveals {HIDDEN_WITNESS_ID}: {HIDDEN_WITNESS_TEXT}.",
            hidden_witness_ids=[HIDDEN_WITNESS_ID, HIDDEN_WITNESS_TEXT],
        )
    )

    joined = " ".join(result.failure_reasons)
    assert not result.passed
    assert NarrativeConsistencyRule.NO_HIDDEN_WITNESS_REVEALED in joined
    assert HIDDEN_WITNESS_ID not in joined
    assert HIDDEN_WITNESS_TEXT not in joined
    assert "[redacted:" in joined


def test_memory_as_authority_fails() -> None:
    result = evaluate_narrative_consistency(
        _case(
            "It is certain that harlan betrayed the town.",
            memory_only_facts=["harlan betrayed the town"],
            authoritative_facts=[],
        )
    )

    assert not result.passed
    assert any(NarrativeConsistencyRule.NO_MEMORY_AS_AUTHORITATIVE_FACT in reason for reason in result.failure_reasons)


def test_npc_unknown_fact_fails() -> None:
    result = evaluate_narrative_consistency(
        _case(
            "mira tells you about sealed_letter.",
            npc_known_facts={"mira": ["public_square"]},
            npc_fact_mentions={"mira": ["sealed_letter"]},
        )
    )

    assert not result.passed
    assert any(NarrativeConsistencyRule.NO_NPC_KNOWING_UNKNOWN_FACT in reason for reason in result.failure_reasons)


def test_report_can_output_world_quality_report_without_hidden_text() -> None:
    report = run_narrative_consistency_evals(
        [
            _case("The square is quiet."),
            _case(
                f"{HIDDEN_WITNESS_ID} speaks from hiding.",
                hidden_witness_ids=[HIDDEN_WITNESS_ID],
                dead_npc_ids=[HIDDEN_WITNESS_ID],
            ),
        ]
    )
    payload = report.model_dump(mode="json")
    quality_payload = report.quality_report.model_dump_normal() if report.quality_report else {}
    serialized_quality = json.dumps(quality_payload, ensure_ascii=False, sort_keys=True)

    assert report.total_cases == 2
    assert report.passed == 1
    assert report.failed == 1
    assert report.quality_report is not None
    assert payload["case_results"][1]["passed"] is False
    assert HIDDEN_WITNESS_ID not in serialized_quality
    assert "hidden_details_debug_only" not in serialized_quality


def test_narrator_prompt_context_builder_input_remains_visible_only() -> None:
    messages = build_narrator_messages(
        player_input="observe",
        action_result_payload={
            "success_level": "success",
            "reason": "Observed public square.",
            "visible_facts": ["public_square"],
        },
        visible_facts=["public_square"],
        current_location="square",
        tone="plain",
    )
    snapshot = json.dumps(messages, ensure_ascii=False)

    assert "public_square" in snapshot
    assert "state_deltas" not in snapshot
    assert "hidden_facts" not in snapshot
    assert HIDDEN_WITNESS_ID not in snapshot
