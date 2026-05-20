from random import Random

from app.core.state_delta import StateDeltaOperation, apply_delta
from app.core.world_state import FactState, FactVisibility, GameState, LocationState, PlayerState
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.actions.declarative import (
    DeclarativeActionDefinition,
    DeclarativeActionHandler,
    DeclarativeActionTargetSpec,
    DeclarativeCondition,
    DeclarativeConditionType,
    DeclarativeOutcome,
    DeclarativeStateDeltaTemplate,
    DeclarativeTargetKind,
    DeclarativeVisibilityPolicy,
)
from app.engine.actions.schemas import SuccessLevel
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.session_store import build_visible_state


def _state() -> GameState:
    return GameState(
        world_id="declarative-action-test",
        locations={"shrine": LocationState(id="shrine", name="Old Shrine")},
        player=PlayerState(location_id="shrine"),
        player_visible_facts={"shrine_open"},
        facts={
            "shrine_open": FactState(id="shrine_open", text="The shrine is open.", visibility=FactVisibility.PUBLIC),
            "hidden_blessing": FactState(id="hidden_blessing", text="The shrine chooses an heir.", visibility=FactVisibility.HIDDEN),
        },
    )


def _intent(target_id: str | None = "shrine", raw_text: str = "pray") -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.UNKNOWN,
        raw_text=raw_text,
        confidence=1.0,
        requires_clarification=False,
        target_id=target_id,
    )


def _pray_definition(*, hidden_outcome: bool = False) -> DeclarativeActionDefinition:
    return DeclarativeActionDefinition(
        id="module.pray",
        label="Pray",
        aliases=["pray", "offer prayer"],
        category="general",
        target_specs=[DeclarativeActionTargetSpec(kind=DeclarativeTargetKind.CURRENT_LOCATION)],
        affordance_requirements={"required_visible_facts": ["shrine_open"]},
        time_cost=3,
        preconditions=[
            DeclarativeCondition(condition_type=DeclarativeConditionType.AT_LOCATION, value="shrine"),
        ],
        checks=[{"check_type": "always"}],
        outcomes={
            SuccessLevel.SUCCESS: DeclarativeOutcome(
                success_level=SuccessLevel.SUCCESS,
                reason="The prayer is accepted by deterministic shrine rules.",
                visible_facts=["shrine_open"],
                hidden_facts=["hidden_blessing"],
                hidden_outcome=hidden_outcome,
                state_delta_templates=[
                    DeclarativeStateDeltaTemplate(
                        operation=StateDeltaOperation.SET,
                        path="flags.prayed_at_{target_id}",
                        value=True,
                        reason="Declarative pray action effect.",
                    )
                ],
            ),
            SuccessLevel.FAILURE: DeclarativeOutcome(
                success_level=SuccessLevel.FAILURE,
                reason="The prayer cannot take hold.",
            ),
        },
        state_delta_templates=[],
        event_type="module.pray_resolved",
        visibility_policy=DeclarativeVisibilityPolicy(hidden_outcome_player_visible=False),
        narrator_hints={"safe_summary": "A prayer was resolved."},
    )


def test_declarative_pray_action_can_register_with_dispatcher() -> None:
    handler = DeclarativeActionHandler(_pray_definition())
    dispatcher = ActionDispatcher([handler])

    result = dispatcher.resolve(_intent(), _state(), Random(1))

    assert result.success_level == SuccessLevel.SUCCESS
    assert result.state_deltas


def test_declarative_action_valid_target_succeeds() -> None:
    execution = DeclarativeActionHandler(_pray_definition()).resolve_with_event(_intent(), _state(), Random(1))

    assert execution.action_result.success_level == SuccessLevel.SUCCESS
    assert execution.event.action_type == "module.pray"
    assert execution.event.state_deltas == execution.action_result.state_deltas


def test_declarative_action_invalid_target_returns_invalid() -> None:
    execution = DeclarativeActionHandler(_pray_definition()).resolve_with_event(_intent("elsewhere"), _state(), Random(1))

    assert execution.action_result.success_level == SuccessLevel.INVALID
    assert execution.event.allow_empty_delta is True


def test_declarative_action_precondition_failure_returns_failure() -> None:
    state = _state().model_copy(update={"player": _state().player.model_copy(update={"location_id": "elsewhere"})})

    execution = DeclarativeActionHandler(_pray_definition()).resolve_with_event(_intent("elsewhere"), state, Random(1))

    assert execution.action_result.success_level in {SuccessLevel.FAILURE, SuccessLevel.INVALID}


def test_state_delta_templates_generate_legal_state_delta() -> None:
    state = _state()
    execution = DeclarativeActionHandler(_pray_definition()).resolve_with_event(_intent(), state, Random(1))

    next_state = apply_delta(state, execution.action_result.state_deltas[0])

    assert execution.action_result.state_deltas[0].path == "flags.prayed_at_shrine"
    assert next_state.flags["prayed_at_shrine"] is True


def test_declarative_action_does_not_directly_modify_game_state() -> None:
    state = _state()
    before = state.model_dump(mode="json")

    _ = DeclarativeActionHandler(_pray_definition()).resolve_with_event(_intent(), state, Random(1))

    assert state.model_dump(mode="json") == before


def test_declarative_action_records_event() -> None:
    execution = DeclarativeActionHandler(_pray_definition()).resolve_with_event(_intent(), _state(), Random(1))

    assert execution.event.event_id.startswith("event-module.pray")
    assert execution.event.state_deltas
    assert execution.event.result == "success"


def test_hidden_outcome_does_not_enter_visible_state() -> None:
    state = _state()
    execution = DeclarativeActionHandler(_pray_definition(hidden_outcome=True)).resolve_with_event(_intent(), state, Random(1))
    visible_payload = build_visible_state(state).model_dump_json()

    assert execution.event.visible_to_player is False
    assert execution.action_result.visible_facts == []
    assert "The shrine chooses an heir" not in visible_payload
