from app.core.event_log import Event
from app.core.state_delta import apply_delta
from app.core.world_state import (
    CrimeState,
    FactionMissionDefinition,
    FactionMissionReward,
    FactionMissionState,
    FactionState,
    GameState,
    NPCState,
    ReputationState,
)
from app.engine.rules.faction_missions import (
    accept_faction_mission,
    available_faction_missions,
    complete_faction_mission,
    fail_faction_mission,
    mission_available,
)


def make_state() -> GameState:
    return GameState(
        world_id="faction-mission-test",
        factions={
            "watch": FactionState(id="watch", name="Watch", reputation=ReputationState(value=15, known_to_player=True), known_by_player=True, conflict_tags=["smugglers"]),
            "hidden_circle": FactionState(id="hidden_circle", name="Hidden Circle", reputation=ReputationState(value=20, known_to_player=False), known_by_player=False),
        },
        npcs={"harlan": NPCState(id="harlan", location_id="square", faction_id="watch")},
        faction_mission_definitions={
            "watch_courier": FactionMissionDefinition(
                id="watch_courier",
                faction_id="watch",
                mission_type="courier",
                title="Carry the writ",
                min_reputation=10,
                reward=FactionMissionReward(reputation_delta=5, currency=7),
            ),
            "watch_sabotage": FactionMissionDefinition(
                id="watch_sabotage",
                faction_id="watch",
                mission_type="sabotage",
                title="Disrupt smugglers",
                min_reputation=5,
                required_conflict_tags=["smugglers"],
                failure_reputation_delta=-4,
            ),
            "hidden_job": FactionMissionDefinition(
                id="hidden_job",
                faction_id="hidden_circle",
                mission_type="infiltration",
                title="Secret Infiltration",
                min_reputation=0,
                hidden=True,
            ),
        },
    )


def apply_all(state: GameState, deltas) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_reputation_threshold_controls_mission_availability() -> None:
    state = make_state()
    state.factions["watch"].reputation.value = 9

    unavailable = mission_available(state, "watch_courier")
    state.factions["watch"].reputation.value = 10
    available = mission_available(state, "watch_courier")

    assert unavailable.available is False
    assert unavailable.reason == "reputation_below_threshold"
    assert available.available is True


def test_hostile_faction_refuses_mission() -> None:
    state = make_state()
    state.factions["watch"].reputation.value = -60

    availability = mission_available(state, "watch_courier")

    assert availability.available is False
    assert availability.reason == "hostile_faction"


def test_mission_accept_creates_quest_and_mission_state() -> None:
    state = make_state()

    result = accept_faction_mission(state, "watch_courier")
    next_state = apply_all(state, result.state_deltas)

    assert result.accepted is True
    assert isinstance(result.event, Event)
    assert result.event.state_deltas == result.state_deltas
    assert next_state.faction_missions["watch_courier"].status == "accepted"
    assert next_state.quests["faction_mission_watch_courier"].status == "active"
    assert next_state.quests["faction_mission_watch_courier"].known_to_player is True


def test_mission_completion_grants_reward_and_reputation() -> None:
    state = make_state()
    state = apply_all(state, accept_faction_mission(state, "watch_courier").state_deltas)

    result = complete_faction_mission(state, "watch_courier")
    next_state = apply_all(state, result.state_deltas)

    assert result.completed is True
    assert next_state.faction_missions["watch_courier"].status == "completed"
    assert next_state.quests["faction_mission_watch_courier"].status == "completed"
    assert next_state.factions["watch"].reputation.value == state.factions["watch"].reputation.value + 5
    assert next_state.player.currency == state.player.currency + 7


def test_mission_failure_creates_consequence() -> None:
    state = make_state()
    state = apply_all(state, accept_faction_mission(state, "watch_sabotage").state_deltas)

    result = fail_faction_mission(state, "watch_sabotage", "missed_deadline")
    next_state = apply_all(state, result.state_deltas)

    assert result.failed is True
    assert next_state.faction_missions["watch_sabotage"].status == "failed"
    assert next_state.quests["faction_mission_watch_sabotage"].status == "failed"
    assert "faction_mission_failure_watch_sabotage" in next_state.social_consequences
    assert next_state.factions["watch"].reputation.value == state.factions["watch"].reputation.value - 4


def test_hidden_faction_mission_not_available_to_player_ui() -> None:
    state = make_state()

    visible = available_faction_missions(state)

    assert "hidden_job" not in [mission.id for mission in visible]


def test_player_crime_can_block_mission() -> None:
    state = make_state()
    state.faction_mission_definitions["watch_courier"].blocked_by_player_crime = True
    state.crimes["crime_1"] = CrimeState(id="crime_1", crime_type="assault", actor_id="player", victim_id="harlan", location_id="square")

    availability = mission_available(state, "watch_courier")

    assert availability.available is False
    assert availability.reason == "player_crime_block"


def test_save_load_preserves_faction_mission_state() -> None:
    state = make_state()
    state.faction_missions["watch_courier"] = FactionMissionState(id="watch_courier", definition_id="watch_courier", faction_id="watch", status="accepted", quest_id="faction_mission_watch_courier", known_to_player=True)

    loaded = GameState.model_validate_json(state.model_dump_json())

    assert loaded.faction_mission_definitions["watch_courier"].mission_type == "courier"
    assert loaded.faction_missions["watch_courier"].status == "accepted"
