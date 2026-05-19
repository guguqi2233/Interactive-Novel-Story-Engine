import json

from app.core.world_state import (
    ActorCondition,
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    NPCState,
    PlayerState,
    WorldObjectState,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.roleplay.dialogue import DialogueManager
from app.roleplay.output_consistency import (
    RPConsistencyDecision,
    RPOutputConsistencyChecker,
)


HIDDEN_TEXT = "the mayor buried the red ledger"


def make_rp_state() -> GameState:
    return GameState(
        world_id="rp-output-test",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Square")},
        objects={
            "brass_key": WorldObjectState(id="brass_key", name="Brass Key", location_id="square", visible=True),
        },
        facts={
            "public_square": FactState(
                id="public_square",
                text="the square is crowded",
                visibility=FactVisibility.PUBLIC,
                public=True,
            ),
            "visible_ribbon": FactState(
                id="visible_ribbon",
                text="the blue ribbon marks the east door",
                visibility=FactVisibility.DISCOVERABLE,
            ),
            "hidden_ledger": FactState(
                id="hidden_ledger",
                text=HIDDEN_TEXT,
                visibility=FactVisibility.HIDDEN,
                secret=True,
            ),
        },
        player_visible_facts={"public_square", "visible_ribbon"},
        npcs={
            "mira": NPCState(
                id="mira",
                location_id="square",
                visible=True,
                knowledge=["public_square"],
            ),
            "old_guard": NPCState(
                id="old_guard",
                location_id="square",
                visible=True,
                alive=False,
                condition=ActorCondition.DEAD,
            ),
        },
    )


def test_hidden_fact_mention_is_caught_and_redacted() -> None:
    state = make_rp_state()
    report = RPOutputConsistencyChecker().check(
        generated_text=f"Mira whispers that {HIDDEN_TEXT}.",
        state=state,
        npc_known_facts=["public_square"],
        forbidden_hidden_terms=[HIDDEN_TEXT],
    )
    payload = json.dumps(report.model_dump(mode="json"), ensure_ascii=False)

    assert report.ok is False
    assert report.decision == RPConsistencyDecision.FALLBACK_SAFE_SUMMARY
    assert "hidden_fact_leakage" in {issue.code for issue in report.issues}
    assert HIDDEN_TEXT not in payload
    assert "[redacted:" in payload or "hidden_ledger" in payload


def test_npc_unknown_fact_mention_is_caught() -> None:
    state = make_rp_state()
    report = RPOutputConsistencyChecker().check(
        generated_text="Mira tells you the blue ribbon marks the east door.",
        state=state,
        visible_facts=["visible_ribbon"],
        npc_known_facts=["public_square"],
        speaker_npc_id="mira",
    )

    assert report.ok is False
    assert any(issue.code == "npc_unknown_fact_mention" for issue in report.issues)


def test_invented_item_is_caught() -> None:
    state = make_rp_state()
    report = RPOutputConsistencyChecker().check(
        generated_text="Mira hands you item:moon_key.",
        state=state,
        npc_known_facts=["public_square"],
        speaker_npc_id="mira",
    )

    assert report.ok is False
    assert any(issue.code == "invented_key_item" for issue in report.issues)


def test_dead_npc_speaking_is_caught() -> None:
    state = make_rp_state()
    report = RPOutputConsistencyChecker().check(
        generated_text="The old guard says the gate is open.",
        state=state,
        speaker_npc_id="old_guard",
    )

    assert report.ok is False
    assert any(issue.code == "dead_or_incapacitated_npc_speaking" for issue in report.issues)


def test_relationship_change_text_without_delta_is_flagged() -> None:
    state = make_rp_state()
    report = RPOutputConsistencyChecker().check(
        generated_text="Mira smiles. Trust increased by 10.",
        state=state,
        speaker_npc_id="mira",
        action_result=ActionResult(success_level=SuccessLevel.SUCCESS, reason="Talked."),
    )

    assert report.ok is False
    assert report.decision == RPConsistencyDecision.REQUEST_RETRY
    assert any(issue.code == "unauthorized_relationship_change" for issue in report.issues)


def test_safe_flavor_text_passes() -> None:
    state = make_rp_state()
    report = RPOutputConsistencyChecker().check(
        generated_text="Mira speaks quietly beside the lantern-light, staying careful and calm.",
        state=state,
        npc_known_facts=["public_square"],
        speaker_npc_id="mira",
        allowed_flavor_terms=["lantern-light"],
    )

    assert report.ok is True
    assert report.issues == []


def test_fallback_safe_summary_is_available() -> None:
    state = make_rp_state()
    checker = RPOutputConsistencyChecker()
    report = checker.check(
        generated_text=f"The response exposes {HIDDEN_TEXT}.",
        state=state,
        forbidden_hidden_terms=[HIDDEN_TEXT],
    )
    fallback = checker.fallback_safe_summary(report)

    assert report.ok is False
    assert "withheld" in fallback
    assert HIDDEN_TEXT not in fallback


def test_dialogue_manager_can_run_consistency_checker_without_mutating_state() -> None:
    state = make_rp_state()
    before = state.model_copy(deep=True)
    manager = DialogueManager()
    session = manager.start_dialogue(state, game_session_id="game-1", focus_npc_id="mira")
    context = manager.build_dialogue_context(state, focus_npc_id="mira", session=session)

    report = manager.check_dialogue_output_consistency(
        generated_text="Mira tells you about item:moon_key.",
        state=state,
        context=context,
    )

    assert state == before
    assert report.ok is False
    assert any(issue.code == "invented_key_item" for issue in report.issues)
