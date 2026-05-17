from pathlib import Path

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    ActorCondition,
    FactionState,
    GameState,
    GameTime,
    LocationState,
    NPCScheduleEntry,
    NPCState,
    ReputationState,
    RumorState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.rules.crime import classify_crime, detect_witnesses
from app.engine.rules.life_state import apply_damage, can_talk, heal_damage, mark_dead
from app.engine.rules.rumors import propagate_rumors
from app.engine.rules.schedule import resolve_npc_schedules
from app.llm.schemas import PlayerIntent
from app.session_store import build_visible_state


def make_life_state(hidden_dead_npc: bool = False) -> GameState:
    return GameState(
        world_id="life-test",
        current_time=GameTime(day=1, minutes_of_day=18 * 60),
        locations={
            "square": LocationState(id="square", name="Square", exits={"east": "road"}),
            "road": LocationState(id="road", name="Road"),
        },
        player={"location_id": "square"},
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                faction_id="watch",
                schedule=[
                    NPCScheduleEntry(time_of_day="evening", location_id="road", activity="walking")
                ],
                hidden=hidden_dead_npc,
            ),
            "mira": NPCState(id="mira", location_id="square"),
        },
        factions={
            "watch": FactionState(
                id="watch",
                name="Watch",
                reputation=ReputationState(known_to_player=True),
            )
        },
    )


def test_damage_changes_healthy_to_wounded() -> None:
    state = make_life_state()

    for delta in apply_damage(state, "harlan", 3):
        state = apply_delta(state, delta)

    assert state.npcs["harlan"].hp == 7
    assert state.npcs["harlan"].condition == ActorCondition.WOUNDED
    assert "wounded" in state.npcs["harlan"].status_effects


def test_hp_zero_enters_incapacitated_by_default() -> None:
    state = make_life_state()

    for delta in apply_damage(state, "harlan", 99):
        state = apply_delta(state, delta)

    assert state.npcs["harlan"].hp == 0
    assert state.npcs["harlan"].condition == ActorCondition.INCAPACITATED
    assert state.npcs["harlan"].alive is True


def test_mark_dead_sets_dead_state() -> None:
    state = make_life_state()

    for delta in mark_dead(state, "harlan"):
        state = apply_delta(state, delta)

    assert state.npcs["harlan"].hp == 0
    assert state.npcs["harlan"].alive is False
    assert state.npcs["harlan"].condition == ActorCondition.DEAD
    assert "dead" in state.npcs["harlan"].status_effects


def test_dead_npc_does_not_execute_schedule() -> None:
    state = make_life_state()
    for delta in mark_dead(state, "harlan"):
        state = apply_delta(state, delta)

    deltas = resolve_npc_schedules(state)

    assert not any(delta.path == "npcs.harlan.location_id" for delta in deltas)


def test_dead_npc_cannot_talk() -> None:
    state = make_life_state()
    for delta in mark_dead(state, "harlan"):
        state = apply_delta(state, delta)

    assert can_talk(state, "harlan") is False
    result = ActionDispatcher().resolve(
        PlayerIntent(
            action_type="talk",
            target_id="harlan",
            raw_text="talk",
            confidence=1.0,
            requires_clarification=False,
        ),
        state,
    )
    assert result.success_level == "failure"


def test_dead_npc_does_not_propagate_rumor() -> None:
    state = make_life_state()
    state.rumors["rumor_1"] = RumorState(
        id="rumor_1",
        text_for_player="A rumor.",
        known_by_npcs={"harlan"},
    )
    for delta in mark_dead(state, "harlan"):
        state = apply_delta(state, delta)

    deltas = propagate_rumors(state)

    assert deltas == []


def test_dead_npc_cannot_be_new_witness() -> None:
    state = make_life_state()
    for delta in mark_dead(state, "harlan"):
        state = apply_delta(state, delta)
    event = Event(
        event_id="attack-event",
        turn=1,
        actor_id="player",
        action_type="attack",
        target_id="mira",
        result="success",
        visible_to_player=True,
        state_deltas=[],
        allow_empty_delta=True,
    )

    witnesses = detect_witnesses(event, state)

    assert [witness.npc_id for witness in witnesses] == ["mira"]


def test_killing_attack_classifies_as_murder() -> None:
    state = make_life_state()
    event = Event(
        event_id="attack-event",
        turn=1,
        actor_id="player",
        action_type="attack",
        target_id="harlan",
        result="success",
        visible_to_player=True,
        state_deltas=[
            StateDelta(
                operation=StateDeltaOperation.SET,
                path="npcs.harlan.condition",
                value=ActorCondition.DEAD,
            )
        ],
    )

    draft = classify_crime(event, state)

    assert draft is not None
    assert draft.crime_type == "murder"
    assert draft.severity == 5


def test_visible_state_does_not_leak_hidden_dead_npc() -> None:
    state = make_life_state(hidden_dead_npc=True)
    for delta in mark_dead(state, "harlan"):
        state = apply_delta(state, delta)

    visible_state = build_visible_state(state)

    assert "harlan" not in visible_state.model_dump_json()
    assert all(npc.id != "harlan" for npc in visible_state.visible_npcs)


def test_save_load_preserves_life_state(tmp_path: Path) -> None:
    state = make_life_state()
    for delta in mark_dead(state, "harlan"):
        state = apply_delta(state, delta)
    repository = SQLiteSaveRepository(Path(tmp_path) / "life.db")

    repository.create_save("save-1", state)
    loaded = repository.load_save("save-1")

    assert loaded.npcs["harlan"].condition == ActorCondition.DEAD
    assert loaded.npcs["harlan"].alive is False
    assert loaded.npcs["harlan"].status_effects == state.npcs["harlan"].status_effects


def test_dead_actor_cannot_be_healed() -> None:
    state = make_life_state()
    for delta in mark_dead(state, "harlan"):
        state = apply_delta(state, delta)

    import pytest

    with pytest.raises(ValueError, match="Dead actors cannot be healed"):
        heal_damage(state, "harlan", 1)
