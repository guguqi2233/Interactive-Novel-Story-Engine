import json

from app.core.world_state import (
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    NPCState,
    PlayerState,
    WorldObjectState,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.evals.rp_boundary import (
    RPBoundaryEvalCase,
    RPBoundaryRule,
    evaluate_rp_boundary_case,
    run_rp_boundary_evals,
)
from app.roleplay.boundary import RoleplayOutputCandidate
from app.roleplay.dialogue import GroupDialogueManager


HIDDEN_FACT_TEXT = "the heir sleeps beneath the old chapel"
HIDDEN_FACT_ID = "hidden_heir_chapel"


def make_state() -> GameState:
    return GameState(
        world_id="rp-boundary-eval",
        player=PlayerState(location_id="square"),
        locations={
            "square": LocationState(id="square", name="Village Square"),
            "chapel": LocationState(id="chapel", name="Old Chapel"),
        },
        objects={"brass_key": WorldObjectState(id="brass_key", name="Brass Key", location_id="square")},
        facts={
            "public_square": FactState(
                id="public_square",
                text="the square is open",
                visibility=FactVisibility.PUBLIC,
                public=True,
            ),
            "known_to_harlan": FactState(
                id="known_to_harlan",
                text="harlan heard the bridge creak",
                visibility=FactVisibility.DISCOVERABLE,
                known_by={"harlan"},
            ),
            HIDDEN_FACT_ID: FactState(
                id=HIDDEN_FACT_ID,
                text=HIDDEN_FACT_TEXT,
                visibility=FactVisibility.HIDDEN,
                known_by={"harlan"},
                secret=True,
            ),
            "example_only_betrayal": FactState(
                id="example_only_betrayal",
                text="mira betrayed the village",
                visibility=FactVisibility.HIDDEN,
                secret=True,
            ),
        },
        player_visible_facts={"public_square"},
        npcs={
            "harlan": NPCState(id="harlan", location_id="square", visible=True, knowledge=[HIDDEN_FACT_ID, "known_to_harlan"]),
            "mira": NPCState(id="mira", location_id="square", visible=True, knowledge=["public_square"]),
        },
    )


def test_hidden_fact_leakage_case_fails_and_redacts_report() -> None:
    case = RPBoundaryEvalCase(
        id="hidden_fact_leak",
        rule=RPBoundaryRule.NO_HIDDEN_FACT_LEAKAGE,
        generated_text=f"Harlan says {HIDDEN_FACT_TEXT}.",
        state=make_state(),
        speaker_npc_id="harlan",
        npc_known_facts=[HIDDEN_FACT_ID],
        forbidden_hidden_terms=[HIDDEN_FACT_TEXT],
        expected_issue_codes=["hidden_fact_leakage"],
    )

    result = evaluate_rp_boundary_case(case)
    payload = json.dumps(result.model_dump(mode="json"), ensure_ascii=False)

    assert result.passed
    assert "hidden_fact_leakage" in result.issue_codes
    assert HIDDEN_FACT_TEXT not in payload


def test_unknown_fact_mention_case_fails() -> None:
    result = evaluate_rp_boundary_case(
        RPBoundaryEvalCase(
            id="unknown_fact",
            rule=RPBoundaryRule.NO_NPC_UNKNOWN_FACT,
            generated_text="Mira says harlan heard the bridge creak.",
            state=make_state(),
            speaker_npc_id="mira",
            visible_facts=["known_to_harlan"],
            npc_known_facts=["public_square"],
            expected_issue_codes=["npc_unknown_fact_mention"],
        )
    )

    assert result.passed


def test_example_dialogue_as_fact_case_fails() -> None:
    result = evaluate_rp_boundary_case(
        RPBoundaryEvalCase(
            id="example_as_fact",
            rule=RPBoundaryRule.NO_EXAMPLE_DIALOGUE_AS_FACT,
            generated_text="Mira confirms mira betrayed the village.",
            state=make_state(),
            speaker_npc_id="mira",
            npc_known_facts=["public_square"],
            forbidden_hidden_terms=["mira betrayed the village"],
            expected_issue_codes=["hidden_fact_leakage"],
        )
    )

    assert result.passed


def test_group_context_crossover_case_fails() -> None:
    state = make_state()
    scene = GroupDialogueManager().start_group_scene(state, participant_ids=["harlan", "mira"])
    assert scene.participant_ids == ["harlan", "mira"]
    result = evaluate_rp_boundary_case(
        RPBoundaryEvalCase(
            id="group_context_crossover",
            rule=RPBoundaryRule.NO_GROUP_CONTEXT_CROSSOVER,
            generated_text=f"Mira repeats Harlan's secret: {HIDDEN_FACT_TEXT}.",
            state=state,
            speaker_npc_id="mira",
            npc_known_facts=["public_square"],
            forbidden_hidden_terms=[HIDDEN_FACT_TEXT],
            expected_issue_codes=["hidden_fact_leakage", "npc_unknown_fact_mention"],
        )
    )

    assert result.passed


def test_scene_mood_fact_override_case_fails() -> None:
    result = evaluate_rp_boundary_case(
        RPBoundaryEvalCase(
            id="mood_fact_override",
            rule=RPBoundaryRule.NO_SCENE_MOOD_FACT_OVERRIDE,
            generated_text="The romantic mood means quest completed.",
            state=make_state(),
            action_result=ActionResult(success_level=SuccessLevel.SUCCESS, reason="Talked."),
            expected_issue_codes=["unauthorized_quest_completion"],
        )
    )

    assert result.passed


def test_profile_voice_emotion_and_tone_boundaries_fail_when_state_is_claimed() -> None:
    cases = [
        RPBoundaryEvalCase(
            id="profile_state_permission",
            rule=RPBoundaryRule.NO_PROFILE_STATE_PERMISSION,
            generated_text="The profile says to create a new fact.",
            state=make_state(),
            candidate=RoleplayOutputCandidate(text="", proposed_fact_creations=["new_canonical_fact"]),
            expected_issue_codes=["prohibited_fact_creation"],
        ),
        RPBoundaryEvalCase(
            id="voice_override_action_result",
            rule=RPBoundaryRule.NO_VOICE_ACTION_RESULT_OVERRIDE,
            generated_text="Her voice says the failed lockpick worked successfully.",
            state=make_state(),
            action_result=ActionResult(success_level=SuccessLevel.FAILURE, reason="The lock resisted."),
            expected_issue_codes=["contradiction_with_action_result"],
        ),
        RPBoundaryEvalCase(
            id="emotion_direct_write",
            rule=RPBoundaryRule.NO_LLM_EMOTIONAL_STATE_WRITE,
            generated_text="Mira's emotional_state is now affectionate.",
            state=make_state(),
            candidate=RoleplayOutputCandidate(text="", proposed_state_changes=["npcs.mira.emotional_state.primary_emotion=affectionate"]),
            expected_issue_codes=["prohibited_state_change"],
        ),
        RPBoundaryEvalCase(
            id="tone_as_value",
            rule=RPBoundaryRule.NO_TONE_AS_RELATIONSHIP_VALUE,
            generated_text="Mira smiles; trust increased by 10.",
            state=make_state(),
            action_result=ActionResult(success_level=SuccessLevel.SUCCESS, reason="Talked."),
            expected_issue_codes=["unauthorized_relationship_change"],
        ),
        RPBoundaryEvalCase(
            id="lorebook_hidden_prompt_entry",
            rule=RPBoundaryRule.NO_LOREBOOK_HIDDEN_PROMPT_ENTRY,
            generated_text=f"The lorebook reveals {HIDDEN_FACT_TEXT}.",
            state=make_state(),
            forbidden_hidden_terms=[HIDDEN_FACT_TEXT],
            expected_issue_codes=["hidden_fact_leakage"],
        ),
    ]

    results = [evaluate_rp_boundary_case(case) for case in cases]

    assert all(result.passed for result in results)


def test_safe_rp_output_passes_and_quality_report_is_safe() -> None:
    safe_case = RPBoundaryEvalCase(
        id="safe_output",
        rule=RPBoundaryRule.SAFE_RP_OUTPUT,
        generated_text="Mira answers carefully in the square, keeping her voice low and polite.",
        state=make_state(),
        speaker_npc_id="mira",
        npc_known_facts=["public_square"],
        allowed_flavor_terms=["voice"],
        should_pass=True,
    )
    report = run_rp_boundary_evals(
        [
            safe_case,
            RPBoundaryEvalCase(
                id="hidden_fact_eval",
                rule=RPBoundaryRule.NO_HIDDEN_FACT_LEAKAGE,
                generated_text=f"Harlan says {HIDDEN_FACT_TEXT}.",
                state=make_state(),
                forbidden_hidden_terms=[HIDDEN_FACT_TEXT],
                expected_issue_codes=["hidden_fact_leakage"],
            ),
        ]
    )
    normal_quality = report.quality_report.model_dump_normal() if report.quality_report else {}
    serialized = json.dumps(normal_quality, ensure_ascii=False, sort_keys=True)

    assert report.total_cases == 2
    assert report.failed == 0
    assert report.quality_report is not None
    assert HIDDEN_FACT_TEXT not in serialized
    assert "hidden_details_debug_only" not in serialized
