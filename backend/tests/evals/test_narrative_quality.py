import json
import subprocess
import sys
from pathlib import Path

from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.evals.narrative_quality import (
    NarrativeQualityCase,
    NarrativeQualityRule,
    evaluate_narrative_quality,
    run_narrative_quality_evals,
)
from app.llm.prompts import build_narrator_messages
from app.llm.schemas import NarrativeResult


def _case(
    narrative: NarrativeResult,
    *,
    success_level: SuccessLevel = SuccessLevel.SUCCESS,
    **kwargs: object,
) -> NarrativeQualityCase:
    return NarrativeQualityCase(
        id="case",
        action_result=ActionResult(
            success_level=success_level,
            reason="Rule outcome.",
            visible_facts=["visible_consequence"],
        ),
        narrative=narrative,
        allowed_suggested_actions=["observe", "search"],
        **kwargs,
    )


def test_valid_narrative_passes() -> None:
    result = evaluate_narrative_quality(
        _case(
            NarrativeResult(
                text="你注意到门锁已经松动，屋内仍然安静。",
                suggested_actions=["observe", "search"],
                short_summary="The lock changed visibly.",
            ),
            required_mentions=["门锁"],
            require_visible_consequence=True,
        )
    )

    assert result.passed
    assert result.failure_reasons == []


def test_invented_item_fails() -> None:
    result = evaluate_narrative_quality(
        _case(
            NarrativeResult(
                text="你捡起了不存在的王冠。",
                suggested_actions=["observe"],
                short_summary="Invented item.",
            ),
            invented_item_terms=["王冠"],
        )
    )

    assert not result.passed
    assert any(NarrativeQualityRule.NO_INVENTED_KEY_ITEM in reason for reason in result.failure_reasons)


def test_invented_npc_fails() -> None:
    result = evaluate_narrative_quality(
        _case(
            NarrativeResult(
                text="陌生的国王突然出现并向你点头。",
                suggested_actions=["observe"],
                short_summary="Invented NPC.",
            ),
            invented_npc_terms=["国王"],
        )
    )

    assert not result.passed
    assert any(NarrativeQualityRule.NO_INVENTED_NPC in reason for reason in result.failure_reasons)


def test_hidden_fact_leak_fails() -> None:
    result = evaluate_narrative_quality(
        _case(
            NarrativeResult(
                text="你立刻知道密信藏在松动石板下。",
                suggested_actions=["observe"],
                short_summary="Hidden leak.",
            ),
            hidden_fact_texts=["密信藏在松动石板下"],
        )
    )

    assert not result.passed
    assert any(NarrativeQualityRule.NO_HIDDEN_FACT_LEAKAGE in reason for reason in result.failure_reasons)


def test_contradiction_with_action_result_fails() -> None:
    result = evaluate_narrative_quality(
        _case(
            NarrativeResult(
                text="你成功打开了那扇门。",
                suggested_actions=["observe"],
                short_summary="Contradiction.",
            ),
            success_level=SuccessLevel.FAILURE,
        )
    )

    assert not result.passed
    assert any(
        NarrativeQualityRule.NO_CONTRADICTION_WITH_ACTION_RESULT in reason
        for reason in result.failure_reasons
    )


def test_illegal_suggested_action_is_marked() -> None:
    result = evaluate_narrative_quality(
        _case(
            NarrativeResult(
                text="你看清了四周。",
                suggested_actions=["teleport castle"],
                short_summary="Illegal suggestion.",
            )
        )
    )

    assert not result.passed
    assert any(NarrativeQualityRule.SUGGESTED_ACTIONS_ARE_LEGAL in reason for reason in result.failure_reasons)


def test_hidden_witness_fails() -> None:
    result = evaluate_narrative_quality(
        _case(
            NarrativeResult(
                text="暗处的 hidden_watcher 正盯着你。",
                suggested_actions=["observe"],
                short_summary="Hidden witness leak.",
            ),
            hidden_witness_ids=["hidden_watcher"],
        )
    )

    assert not result.passed
    assert any(
        NarrativeQualityRule.DOES_NOT_REVEAL_HIDDEN_WITNESS in reason
        for reason in result.failure_reasons
    )


def test_report_shape() -> None:
    report = run_narrative_quality_evals(
        [
            _case(
                NarrativeResult(
                    text="你看清了周围。",
                    suggested_actions=["observe"],
                    short_summary="Ok.",
                )
            ),
            _case(
                NarrativeResult(
                    text="你成功完成了失败动作。",
                    suggested_actions=["observe"],
                    short_summary="Bad.",
                ),
                success_level=SuccessLevel.FAILURE,
            ),
        ]
    )

    assert report.total_cases == 2
    assert report.passed == 1
    assert report.failed == 1
    assert "case" in report.failure_reasons


def test_narrator_prompt_input_is_safe_for_quality_context() -> None:
    messages = build_narrator_messages(
        player_input="observe",
        action_result_payload={
            "success_level": "success",
            "reason": "Observed current location.",
            "visible_facts": ["public_square"],
        },
        visible_facts=["public_square"],
        current_location="square",
        tone="plain",
    )
    snapshot = str(messages)

    assert "public_square" in snapshot
    assert "state_deltas" not in snapshot
    assert "hidden_facts" not in snapshot


def test_eval_narrative_quality_cli_outputs_report() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.app.tools.eval_narrative_quality",
            "--json",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["total_cases"] >= 1
    assert set(payload) >= {"total_cases", "passed", "failed", "failure_reasons"}
