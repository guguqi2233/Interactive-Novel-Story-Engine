import json

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactState, FactVisibility, GameState, LocationState
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.gameplay_modules import (
    GameplayModuleBoundaryCheckRequest,
    GameplayModuleDecision,
    GameplayModuleOperation,
    ModuleActionCandidate,
    ModuleDebugData,
    ModulePermission,
    check_gameplay_module_boundary,
    default_gameplay_module_policy,
)
from app.session_store import build_visible_state


def _state() -> GameState:
    return GameState(
        world_id="gameplay-module-boundary-test",
        locations={"start": LocationState(id="start", name="Start")},
    )


def _delta(event_id: str = "event-module-cast") -> StateDelta:
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path="flags.module_effect_applied",
        value=True,
        caused_by_event_id=event_id,
        reason="Gameplay module declared effect.",
        metadata={"module_id": "test_magic"},
    )


def _candidate(*, with_delta: bool = True, with_event: bool = True) -> ModuleActionCandidate:
    event_id = "event-module-cast"
    deltas = [_delta(event_id)] if with_delta else []
    return ModuleActionCandidate(
        module_id="test_magic",
        action_id="test_magic.cast_spark",
        action_result=ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Rules resolved spark spell.",
            state_deltas=deltas,
            visible_facts=["spell:spark"],
            hidden_facts=["hidden_arcane_trace"],
        ),
        event=(
            Event(
                event_id=event_id,
                turn=1,
                actor_id="player",
                action_type="test_magic.cast_spark",
                result="success",
                visible_to_player=True,
                state_deltas=deltas,
            )
            if with_event
            else None
        ),
    )


def test_module_cannot_directly_modify_game_state() -> None:
    state = _state()
    before = state.model_dump(mode="json")

    result = check_gameplay_module_boundary(
        GameplayModuleBoundaryCheckRequest(
            operation=GameplayModuleOperation.EXECUTE_ACTION,
            attempts_direct_game_state_mutation=True,
        )
    )

    assert result.decision == GameplayModuleDecision.BLOCK_DIRECT_GAME_STATE_MUTATION
    assert result.modifies_active_game_state is True
    assert state.model_dump(mode="json") == before


def test_module_effect_must_return_state_delta() -> None:
    result = check_gameplay_module_boundary(
        GameplayModuleBoundaryCheckRequest(
            operation=GameplayModuleOperation.EXECUTE_ACTION,
            action_candidate=_candidate(with_delta=False, with_event=False),
        )
    )

    assert result.requires_state_delta is True
    assert result.decision == GameplayModuleDecision.BLOCK_MISSING_STATE_DELTA


def test_module_action_must_record_event() -> None:
    result = check_gameplay_module_boundary(
        GameplayModuleBoundaryCheckRequest(
            operation=GameplayModuleOperation.EXECUTE_ACTION,
            action_candidate=_candidate(with_delta=True, with_event=False),
        )
    )

    assert result.requires_event is True
    assert result.decision == GameplayModuleDecision.BLOCK_MISSING_EVENT


def test_valid_module_action_boundary_allows_structured_delta_and_event() -> None:
    result = check_gameplay_module_boundary(
        GameplayModuleBoundaryCheckRequest(
            operation=GameplayModuleOperation.EXECUTE_ACTION,
            action_candidate=_candidate(),
        )
    )

    assert result.decision == GameplayModuleDecision.ALLOW
    assert result.forbidden_permissions == []


def test_module_hidden_output_does_not_enter_player_api() -> None:
    secret = "The spell marks the true heir with an invisible sigil."
    state = _state()
    state.facts["hidden_arcane_trace"] = FactState(
        id="hidden_arcane_trace",
        text=secret,
        visibility=FactVisibility.HIDDEN,
        public=False,
        secret=True,
    )
    debug_data = ModuleDebugData(
        module_id="test_magic",
        safe_summary="Spark spell resolved.",
        hidden_output={"hidden_arcane_trace": secret},
        debug_reasons=["hidden roll trace"],
    )

    player_payload = build_visible_state(state).model_dump_json()
    normal_report = json.dumps(debug_data.normal_report(), ensure_ascii=False)

    assert secret not in player_payload
    assert secret not in normal_report
    assert "hidden_arcane_trace" in normal_report


def test_module_permission_execute_arbitrary_code_is_rejected() -> None:
    result = check_gameplay_module_boundary(
        GameplayModuleBoundaryCheckRequest(
            operation=GameplayModuleOperation.IMPORT,
            permissions_requested=[ModulePermission.EXECUTE_ARBITRARY_CODE],
        )
    )

    assert result.decision == GameplayModuleDecision.BLOCK_FORBIDDEN_PERMISSION
    assert ModulePermission.EXECUTE_ARBITRARY_CODE in result.forbidden_permissions
    assert default_gameplay_module_policy().arbitrary_code_execution_allowed is False
