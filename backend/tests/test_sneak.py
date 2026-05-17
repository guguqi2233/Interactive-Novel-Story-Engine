from random import Random

from app.core.event_log import EventLog
from app.core.state_delta import apply_delta
from app.core.world_state import ActorCondition, GameState, LocationState, NPCState, PlayerState, WorldObjectState
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.actions.sneak import SneakActionHandler
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.session_store import build_visible_state


def make_state() -> GameState:
    return GameState(
        world_id="sneak-test",
        player=PlayerState(location_id="hall", stealth_modifier=2),
        locations={
            "hall": LocationState(
                id="hall",
                name="Hall",
                exits={"east": "garden", "west": "bright_room"},
                cover_level=1,
                light_level=5,
            ),
            "garden": LocationState(
                id="garden",
                name="Garden",
                exits={"west": "hall"},
                cover_level=5,
                light_level=2,
            ),
            "bright_room": LocationState(
                id="bright_room",
                name="Bright Room",
                exits={"east": "hall"},
                cover_level=0,
                light_level=9,
            ),
        },
        objects={
            "statue": WorldObjectState(id="statue", location_id="hall"),
        },
        npcs={
            "guard": NPCState(id="guard", location_id="garden", alertness=1),
            "captain": NPCState(id="captain", location_id="bright_room", alertness=8),
            "hidden_watcher": NPCState(
                id="hidden_watcher",
                location_id="hall",
                hidden=True,
                alertness=1,
            ),
        },
    )


def make_intent(target_id: str = "garden") -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.SNEAK,
        target_id=target_id,
        raw_text="sneak",
        confidence=0.9,
        requires_clarification=False,
    )


def apply_all(state: GameState, result) -> GameState:
    next_state = state
    for delta in result.state_deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_cover_improves_sneak_result() -> None:
    state = make_state()

    covered = SneakActionHandler().resolve(make_intent("garden"), state, Random(1))
    exposed = SneakActionHandler().resolve(make_intent("bright_room"), state, Random(1))

    assert covered.success_level in {"success", "partial_success"}
    assert exposed.success_level == "failure"


def test_high_alertness_npc_nearby_more_likely_to_fail() -> None:
    result = SneakActionHandler().resolve(make_intent("bright_room"), make_state(), Random(5))

    assert result.success_level == "failure"
    assert any(delta.path == "npcs.captain.suspicion" for delta in result.state_deltas)


def test_success_changes_player_location() -> None:
    state = make_state()
    result = SneakActionHandler().resolve(make_intent("garden"), state, Random(5))
    next_state = apply_all(state, result)

    assert result.success_level == "success"
    assert next_state.player.location_id == "garden"


def test_partial_success_increases_npc_suspicion() -> None:
    state = make_state()
    state.npcs["guard"].alertness = 6
    result = SneakActionHandler().resolve(make_intent("garden"), state, Random(1))
    next_state = apply_all(state, result)

    assert result.success_level == "partial_success"
    assert next_state.npcs["guard"].suspicion == 1


def test_failure_blocks_movement_and_raises_suspicion() -> None:
    state = make_state()
    result = SneakActionHandler().resolve(make_intent("bright_room"), state, Random(1))
    next_state = apply_all(state, result)

    assert result.success_level == "failure"
    assert next_state.player.location_id == "hall"
    assert next_state.npcs["captain"].suspicion == 2


def test_sneak_to_object_is_supported_without_movement() -> None:
    state = make_state()
    result = SneakActionHandler().resolve(make_intent("statue"), state, Random(5))

    assert result.success_level in {"success", "partial_success"}
    assert not any(delta.path == "player.location_id" for delta in result.state_deltas)


def test_hidden_npc_does_not_enter_visible_state() -> None:
    visible_state = build_visible_state(make_state())

    assert "hidden_watcher" not in visible_state.model_dump_json()


def test_dead_or_incapacitated_npcs_do_not_observe_sneak() -> None:
    state = make_state()
    state.npcs["guard"].condition = ActorCondition.DEAD
    state.npcs["guard"].alive = False
    state.npcs["guard"].alertness = 100
    state.npcs["hidden_watcher"].condition = ActorCondition.INCAPACITATED
    state.npcs["hidden_watcher"].alertness = 100

    result = SneakActionHandler().resolve(make_intent("garden"), state, Random(1))

    assert result.success_level == "success"
    assert not any(delta.path == "npcs.guard.suspicion" for delta in result.state_deltas)
    assert not any(delta.path == "npcs.hidden_watcher.suspicion" for delta in result.state_deltas)


def test_sneak_generates_event_and_consumes_time() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "action_type": "sneak",
                "target_id": "garden",
                "raw_text": "sneak",
                "confidence": 0.9,
                "requires_clarification": False,
            },
            {
                "text": "You move quietly.",
                "suggested_actions": [],
                "short_summary": "Sneaked.",
            },
        ]
    )
    game_loop = __import__("app.core.game_loop", fromlist=["GameLoop"]).GameLoop(
        state=make_state(),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(5),
    )

    result = game_loop.step("sneak")

    assert result.event is not None
    assert result.event.action_type == "sneak"
    assert any(delta.path == "current_time" for delta in result.event.state_deltas)


def test_invalid_sneak_target() -> None:
    result = SneakActionHandler().resolve(make_intent("missing"), make_state(), Random(1))

    assert result.success_level == "invalid"
    assert result.state_deltas == []
