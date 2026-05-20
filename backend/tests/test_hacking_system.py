from random import Random

from app.core.state_delta import StateDeltaOperation, apply_delta
from app.core.world_state import (
    FactState,
    FactVisibility,
    GameState,
    HackableState,
    HackingToolState,
    LocationState,
    NPCState,
    PlayerState,
)
from app.engine.action_registry import ActionRegistry
from app.engine.actions.schemas import SuccessLevel
from app.engine.rules.hacking import HackingActionHandler, hacking_action_definitions
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.session_store import build_visible_state


def _state(*, difficulty: int = 10, monitored: bool = False) -> GameState:
    return GameState(
        world_id="hacking-test",
        turn=2,
        player=PlayerState(location_id="server_room"),
        locations={"server_room": LocationState(id="server_room", name="Server Room")},
        hackables={
            "terminal": HackableState(
                id="terminal",
                target_type="terminal",
                location_id="server_room",
                difficulty=difficulty,
                access_level=0,
                monitored=monitored,
                linked_fact_ids=["public_log", "hidden_root_log"],
            ),
            "camera": HackableState(id="camera", target_type="camera", location_id="server_room", difficulty=difficulty),
            "hidden_node": HackableState(id="hidden_node", target_type="network_node", location_id="server_room", hidden=True),
        },
        hacking_tools={"deck": HackingToolState(id="deck", owner_id="player", power=10)},
        facts={
            "public_log": FactState(id="public_log", text="The access log names a courier.", visibility=FactVisibility.DISCOVERABLE),
            "hidden_root_log": FactState(id="hidden_root_log", text="Root key is buried under admin.", visibility=FactVisibility.HIDDEN),
        },
        npcs={"guard": NPCState(id="guard", location_id="server_room", visible=True)},
    )


def _intent(raw_text: str = "hack terminal", target_id: str | None = "terminal") -> PlayerIntent:
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


def test_hack_terminal_success_modifies_security_state() -> None:
    state = _state()

    execution = HackingActionHandler().resolve_with_event(_intent(), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.SUCCESS
    assert any(delta.path == "hackables.terminal.security_state" for delta in execution.action_result.state_deltas)
    assert next_state.hackables["terminal"].security_state == "compromised"
    assert state.hackables["terminal"].security_state == "locked"


def test_access_logs_discovers_visible_fact_only() -> None:
    state = _state()

    execution = HackingActionHandler().resolve_with_event(_intent("access logs"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.SUCCESS
    assert "public_log" in next_state.player_visible_facts
    assert "hidden_root_log" not in next_state.player_visible_facts
    assert "hidden_root_log" in execution.action_result.hidden_facts


def test_failure_produces_trace_and_alarm() -> None:
    state = _state(difficulty=40)

    execution = HackingActionHandler().resolve_with_event(_intent(), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.FAILURE
    assert next_state.hackables["terminal"].intrusion_trace == 1
    assert next_state.hackables["terminal"].alarm_level == 1


def test_monitored_hacking_failure_produces_cyber_crime() -> None:
    state = _state(difficulty=40, monitored=True)

    execution = HackingActionHandler().resolve_with_event(_intent(), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert "cyber_crime_terminal_2" in next_state.crimes
    assert next_state.crimes["cyber_crime_terminal_2"].crime_type == "cyber_crime"
    assert "cyber_crime_terminal_2:guard" in next_state.witnesses


def test_invalid_target_returns_invalid() -> None:
    execution = HackingActionHandler().resolve_with_event(_intent(target_id="missing_terminal"), _state(), Random(1))

    assert execution.action_result.success_level == SuccessLevel.INVALID
    assert execution.event.allow_empty_delta is True


def test_hidden_logs_do_not_leak_to_visible_state() -> None:
    state = _state()

    execution = HackingActionHandler().resolve_with_event(_intent("access logs"), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)
    visible_payload = build_visible_state(next_state).model_dump_json()

    assert "Root key is buried under admin" not in visible_payload
    assert "hidden_root_log" not in execution.action_result.visible_facts


def test_save_load_preserves_hacking_state() -> None:
    state = _state()
    state = state.model_copy(update={"hackables": {"terminal": state.hackables["terminal"].model_copy(update={"security_state": "compromised"})}})

    restored = GameState.model_validate_json(state.model_dump_json())

    assert restored.hackables["terminal"].security_state == "compromised"
    assert restored.hacking_tools["deck"].power == 10


def test_hacking_actions_register_through_action_registry() -> None:
    registry = ActionRegistry(include_core=False)
    handler = HackingActionHandler()
    for definition in hacking_action_definitions():
        registry.register_module_action(definition, module_id="hacking", handler=handler)

    resolved = registry.get_handler_for_intent(_intent("disable camera", "camera"), _state())

    assert resolved is not None
    assert registry.get_action_definition("hacking.disable_camera") is not None
