from random import Random

from app.core.state_delta import apply_delta
from app.core.world_state import (
    EvidenceState,
    FactState,
    FactVisibility,
    GameState,
    HypothesisState,
    HypothesisStatus,
    LocationState,
    PlayerState,
    QuestStage,
    QuestState,
    QuestStatus,
    QuestVisibility,
    TestimonyState as InvestigationTestimonyState,
)
from app.engine.action_registry import ActionRegistry
from app.engine.actions.schemas import SuccessLevel
from app.engine.rules.investigation import InvestigationActionHandler, investigation_action_definitions
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.session_store import build_visible_state


def _state() -> GameState:
    return GameState(
        world_id="investigation-test",
        turn=6,
        player=PlayerState(location_id="study"),
        locations={"study": LocationState(id="study", name="Study")},
        facts={
            "mud_fact": FactState(id="mud_fact", text="Mud from the garden is on the sill.", visibility=FactVisibility.DISCOVERABLE),
            "contradiction_fact": FactState(id="contradiction_fact", text="The alibi contradicts the clock.", visibility=FactVisibility.PUBLIC, public=True),
            "truth_fact": FactState(id="truth_fact", text="Avery stole the seal.", visibility=FactVisibility.HIDDEN),
        },
        evidence={
            "mud": EvidenceState(id="mud", fact_id="mud_fact", location_id="study", visible=True),
            "truth_note": EvidenceState(id="truth_note", fact_id="truth_fact", location_id="study", visible=True),
        },
        testimonies={
            "avery_testimony": InvestigationTestimonyState(
                id="avery_testimony",
                npc_id="avery",
                fact_ids=["contradiction_fact"],
                contradiction_ids=["mud"],
                known_to_player=True,
            )
        },
        hypotheses={
            "avery_did_it": HypothesisState(
                id="avery_did_it",
                suspect_id="avery",
                correct_suspect_id="avery",
                required_evidence_ids=["mud"],
                quest_id="case",
                quest_objective_id="accuse_avery",
                hidden_truth_fact_id="truth_fact",
            ),
            "blake_did_it": HypothesisState(
                id="blake_did_it",
                suspect_id="blake",
                correct_suspect_id="avery",
                required_evidence_ids=["mud"],
                hidden_truth_fact_id="truth_fact",
            ),
        },
        quests={
            "case": QuestState(
                id="case",
                title="The Missing Seal",
                initial_stage="investigate",
                current_stage="investigate",
                stages={"investigate": QuestStage(id="investigate", title="Investigate", objectives=["accuse_avery"])},
                visibility=QuestVisibility.PUBLIC,
                status=QuestStatus.ACTIVE,
                known_to_player=True,
            )
        },
    )


def _intent(raw_text: str, target_id: str | None) -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.UNKNOWN,
        raw_text=raw_text,
        confidence=1.0,
        requires_clarification=False,
        target_id=target_id,
    )


def _apply_all(state: GameState, deltas: list) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_examine_evidence_discovers_fact() -> None:
    state = _state()

    execution = InvestigationActionHandler().resolve_with_event(_intent("examine evidence", "mud"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.SUCCESS
    assert next_state.evidence["mud"].discovered is True
    assert "mud_fact" in next_state.player_visible_facts


def test_compare_testimony_finds_contradiction() -> None:
    state = _state().model_copy(deep=True)
    state.evidence["mud"] = state.evidence["mud"].model_copy(update={"discovered": True})

    execution = InvestigationActionHandler().resolve_with_event(_intent("compare testimony", "avery_testimony"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.SUCCESS
    assert next_state.flags["contradiction_avery_testimony"] is True
    assert "mud" in execution.action_result.visible_facts


def test_hypothesis_missing_evidence_marked_weak() -> None:
    state = _state()

    execution = InvestigationActionHandler().resolve_with_event(_intent("form hypothesis", "avery_did_it"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.FAILURE
    assert next_state.hypotheses["avery_did_it"].status == HypothesisStatus.WEAK


def test_correct_accusation_triggers_quest_progress() -> None:
    state = _state().model_copy(deep=True)
    state.evidence["mud"] = state.evidence["mud"].model_copy(update={"discovered": True})

    execution = InvestigationActionHandler().resolve_with_event(_intent("accuse suspect", "avery_did_it"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.SUCCESS
    assert next_state.hypotheses["avery_did_it"].status == HypothesisStatus.CORRECT
    assert "accuse_avery" in next_state.quests["case"].completed_objectives


def test_wrong_accusation_creates_social_consequence() -> None:
    state = _state().model_copy(deep=True)
    state.evidence["mud"] = state.evidence["mud"].model_copy(update={"discovered": True})

    execution = InvestigationActionHandler().resolve_with_event(_intent("accuse suspect", "blake_did_it"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.FAILURE
    assert next_state.hypotheses["blake_did_it"].status == HypothesisStatus.WRONG
    assert "wrong_accusation_blake_did_it_6" in next_state.social_consequences


def test_hidden_truth_does_not_leak() -> None:
    state = _state()

    execution = InvestigationActionHandler().resolve_with_event(_intent("examine evidence", "truth_note"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)
    visible_payload = build_visible_state(next_state).model_dump_json()

    assert "truth_fact" not in next_state.player_visible_facts
    assert "truth_fact" in execution.action_result.hidden_facts
    assert "Avery stole the seal" not in visible_payload


def test_save_load_preserves_investigation_state() -> None:
    state = _state().model_copy(deep=True)
    state.evidence["mud"] = state.evidence["mud"].model_copy(update={"discovered": True})
    restored = GameState.model_validate_json(state.model_dump_json())

    assert restored.evidence["mud"].discovered is True
    assert restored.hypotheses["avery_did_it"].hidden_truth_fact_id == "truth_fact"


def test_investigation_actions_register_through_action_registry() -> None:
    registry = ActionRegistry(include_core=False)
    handler = InvestigationActionHandler()
    for definition in investigation_action_definitions():
        registry.register_module_action(definition, module_id="investigation", handler=handler)

    resolved = registry.get_handler_for_intent(_intent("form hypothesis", "avery_did_it"), _state())

    assert resolved is not None
    assert registry.get_action_definition("investigation.accuse_suspect") is not None
