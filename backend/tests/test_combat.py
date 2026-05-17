from pathlib import Path
from random import Random

from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.core.state_delta import apply_delta
from app.core.world_state import (
    CombatStatus,
    FactionState,
    GameState,
    LocationState,
    NPCState,
    ReputationState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.rules.combat import AttackOutcome, CombatantStance, flee, resolve_attack
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.llm.schemas import PlayerIntent
from app.session_store import build_visible_state


def make_combat_state(hidden_witness: bool = False) -> GameState:
    return GameState(
        world_id="combat-test",
        locations={
            "square": LocationState(id="square", name="Square", exits={"east": "road"}),
            "road": LocationState(id="road", name="Road", exits={"west": "square"}),
        },
        player={"location_id": "square", "attack": 4},
        npcs={
            "bandit": NPCState(id="bandit", location_id="square", hp=10, defense=0),
            "witness": NPCState(
                id="witness",
                location_id="square",
                faction_id="watch",
                hidden=hidden_witness,
                alertness=1,
            ),
        },
        factions={
            "watch": FactionState(
                id="watch",
                name="Watch",
                reputation=ReputationState(known_to_player=True),
            )
        },
    )


def test_attack_hit_lowers_target_hp() -> None:
    state = make_combat_state()

    attack_result, deltas = resolve_attack(state, "player", "bandit", Random(0))
    for delta in deltas:
        state = apply_delta(state, delta)

    assert attack_result.outcome in {AttackOutcome.HIT, AttackOutcome.CRITICAL}
    assert state.npcs["bandit"].hp < 10


def test_attack_miss_does_not_lower_hp_but_action_generates_event() -> None:
    state = make_combat_state()
    state.npcs["bandit"].defense = 99
    provider = FakeLLMProvider(
        json_responses=[
            {
                "action_type": "attack",
                "target_id": "bandit",
                "raw_text": "attack bandit",
                "confidence": 1.0,
                "requires_clarification": False,
            },
            {
                "text": "You swing and miss.",
                "suggested_actions": [],
                "short_summary": "Attack missed.",
            },
        ]
    )
    loop = GameLoop(
        state=state,
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(0),
    )

    result = loop.step("attack bandit")

    assert result.event is not None
    assert result.event.action_type == "attack"
    assert loop.state.npcs["bandit"].hp == 10


def test_invalid_attack_target_returns_invalid() -> None:
    state = make_combat_state()

    result = ActionDispatcher().resolve(
        intent=PlayerIntent.model_validate({
            "action_type": "attack",
            "target_id": "missing",
            "raw_text": "attack missing",
            "confidence": 1.0,
            "requires_clarification": False,
        }),
        state=state,
        rng=Random(0),
    )

    assert result.success_level == "invalid"


def test_defend_sets_defensive_state() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "action_type": "defend",
                "raw_text": "defend",
                "confidence": 1.0,
                "requires_clarification": False,
            },
            {"text": "You brace yourself.", "suggested_actions": [], "short_summary": "Defended."},
        ]
    )
    loop = GameLoop(
        state=make_combat_state(),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(0),
    )

    loop.step("defend")

    assert loop.state.player.combat_stance == CombatantStance.DEFENSIVE
    assert "guarded" in loop.state.player.status_effects


def test_flee_success_moves_player_and_ends_combat() -> None:
    state = make_combat_state()
    attack_result, deltas = resolve_attack(state, "player", "bandit", Random(0))
    assert attack_result.outcome != AttackOutcome.INVALID
    for delta in deltas:
        state = apply_delta(state, delta)

    success, flee_deltas, reason = flee(state, "player", "road")
    for delta in flee_deltas:
        state = apply_delta(state, delta)

    assert success is True
    assert reason == "Player fled combat."
    assert state.player.location_id == "road"
    assert next(iter(state.combats.values())).status == CombatStatus.ENDED


def test_hp_never_drops_below_zero() -> None:
    state = make_combat_state()
    state.npcs["bandit"].hp = 1

    _, deltas = resolve_attack(state, "player", "bandit", Random(0))
    for delta in deltas:
        state = apply_delta(state, delta)

    assert state.npcs["bandit"].hp == 0
    assert "incapacitated" in state.npcs["bandit"].status_effects


def test_public_attack_produces_assault_crime() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "action_type": "attack",
                "target_id": "bandit",
                "raw_text": "attack bandit",
                "confidence": 1.0,
                "requires_clarification": False,
            },
            {"text": "You strike.", "suggested_actions": [], "short_summary": "Attacked."},
        ]
    )
    loop = GameLoop(
        state=make_combat_state(),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(0),
    )

    loop.step("attack bandit")

    assert loop.state.crimes
    assert next(iter(loop.state.crimes.values())).crime_type == "assault"


def test_hidden_witness_not_visible_after_combat_crime() -> None:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "action_type": "attack",
                "target_id": "bandit",
                "raw_text": "attack bandit",
                "confidence": 1.0,
                "requires_clarification": False,
            },
            {"text": "You strike.", "suggested_actions": [], "short_summary": "Attacked."},
        ]
    )
    loop = GameLoop(
        state=make_combat_state(hidden_witness=True),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(0),
    )

    loop.step("attack bandit")
    visible_state = build_visible_state(loop.state)

    assert "witness" not in visible_state.model_dump_json()


def test_save_load_preserves_combat_state(tmp_path: Path) -> None:
    state = make_combat_state()
    _, deltas = resolve_attack(state, "player", "bandit", Random(0))
    for delta in deltas:
        state = apply_delta(state, delta)
    repository = SQLiteSaveRepository(Path(tmp_path) / "combat.db")

    repository.create_save("save-1", state)
    loaded = repository.load_save("save-1")

    assert loaded.combats == state.combats
    assert loaded.npcs["bandit"].hp == state.npcs["bandit"].hp
