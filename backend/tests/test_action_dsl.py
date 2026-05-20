import pytest

from app.core.state_delta import StateDeltaOperation, apply_delta
from app.core.world_state import (
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    NPCState,
    PlayerState,
    WorldObjectState,
)
from app.engine.actions.dsl import (
    ActionCheck,
    ActionCheckType,
    ActionDSLTargetType,
    ActionDSLValidationError,
    ActionEffect,
    ActionEffectType,
    ActionPrecondition,
    ActionPreconditionType,
    ActionStateDeltaTemplate,
    compile_effect,
    evaluate_check,
    evaluate_precondition,
)


def _state() -> GameState:
    return GameState(
        world_id="action-dsl-test",
        locations={
            "shrine": LocationState(
                id="shrine",
                name="Old Shrine",
                visible_objects=["visible_relic", "hidden_relic"],
            )
        },
        player=PlayerState(
            location_id="shrine",
            inventory=["candle"],
            status_effects=["focused"],
            stealth_modifier=4,
        ),
        objects={
            "visible_relic": WorldObjectState(
                id="visible_relic",
                location_id="shrine",
                visible=True,
                tags=["holy"],
            ),
            "hidden_relic": WorldObjectState(
                id="hidden_relic",
                location_id="shrine",
                visible=True,
                hidden=True,
                tags=["holy"],
            ),
        },
        npcs={
            "keeper": NPCState(
                id="keeper",
                location_id="shrine",
                knowledge=["old_oath"],
            )
        },
        facts={
            "old_oath": FactState(id="old_oath", visibility=FactVisibility.HIDDEN),
            "public_bell": FactState(id="public_bell", visibility=FactVisibility.PUBLIC),
            "dusty_clue": FactState(id="dusty_clue", visibility=FactVisibility.DISCOVERABLE),
        },
        player_visible_facts={"public_bell"},
    )


def test_actor_has_item_precondition_passes() -> None:
    result = evaluate_precondition(
        ActionPrecondition(
            precondition_type=ActionPreconditionType.ACTOR_HAS_ITEM,
            item_id="candle",
        ),
        _state(),
    )

    assert result.passed is True


def test_target_visible_precondition_respects_visibility() -> None:
    state = _state()

    visible = evaluate_precondition(
        ActionPrecondition(
            precondition_type=ActionPreconditionType.TARGET_VISIBLE,
            target_id="visible_relic",
            target_type=ActionDSLTargetType.OBJECT,
        ),
        state,
    )
    hidden = evaluate_precondition(
        ActionPrecondition(
            precondition_type=ActionPreconditionType.TARGET_VISIBLE,
            target_id="hidden_relic",
            target_type=ActionDSLTargetType.OBJECT,
        ),
        state,
    )

    assert visible.passed is True
    assert hidden.passed is False


def test_skill_check_is_deterministic_with_seed() -> None:
    state = _state()
    check = ActionCheck(
        check_type=ActionCheckType.SKILL_CHECK,
        skill="stealth",
        difficulty=10,
        seed=42,
    )

    first = evaluate_check(check, state)
    second = evaluate_check(check, state)

    assert first.details["roll"] == second.details["roll"]
    assert first.details["total"] == second.details["total"]


def test_state_delta_template_generates_legal_state_delta() -> None:
    effect = ActionEffect(
        effect_type=ActionEffectType.STATE_DELTA_TEMPLATE,
        state_delta_template=ActionStateDeltaTemplate(
            operation=StateDeltaOperation.SET,
            path="flags.prayed_at_{target_id}",
            value=True,
            reason="Test action DSL flag.",
        ),
    )

    deltas = compile_effect(effect, _state(), event_id="event-dsl", target_id="shrine")

    assert deltas[0].path == "flags.prayed_at_shrine"
    assert deltas[0].operation == StateDeltaOperation.SET


def test_forbidden_path_is_rejected() -> None:
    with pytest.raises((ActionDSLValidationError, ValueError)):
        ActionStateDeltaTemplate(
            operation=StateDeltaOperation.SET,
            path="player_visible_facts",
            value="old_oath",
        )


def test_invalid_path_template_is_rejected() -> None:
    with pytest.raises((ActionDSLValidationError, ValueError)):
        ActionStateDeltaTemplate(
            operation=StateDeltaOperation.SET,
            path="flags..bad",
            value=True,
        )


def test_effect_does_not_directly_modify_game_state() -> None:
    state = _state()
    before = state.model_dump(mode="json")
    effect = ActionEffect(
        effect_type=ActionEffectType.ADD_STATUS,
        status="blessed",
    )

    deltas = compile_effect(effect, state, event_id="event-dsl")

    assert state.model_dump(mode="json") == before
    assert deltas[0].path == "player.status_effects"


def test_compiled_effect_applies_only_through_state_delta() -> None:
    state = _state()
    effect = ActionEffect(
        effect_type=ActionEffectType.ADD_FACT_DISCOVERY,
        fact_id="dusty_clue",
    )
    deltas = compile_effect(effect, state, event_id="event-dsl")

    next_state = apply_delta(state, deltas[0])

    assert "dusty_clue" not in state.player_visible_facts
    assert "dusty_clue" in next_state.player_visible_facts


def test_fact_discovery_effect_rejects_hidden_fact() -> None:
    with pytest.raises(ActionDSLValidationError):
        compile_effect(
            ActionEffect(effect_type=ActionEffectType.ADD_FACT_DISCOVERY, fact_id="old_oath"),
            _state(),
            event_id="event-dsl",
        )
