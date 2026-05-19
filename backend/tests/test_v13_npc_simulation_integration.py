from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    ActorCondition,
    CrimeState,
    CrimeStatus,
    EmotionalState,
    FactState,
    FactVisibility,
    FactionState,
    GameState,
    GameTime,
    LocationState,
    NPCFactionDuty,
    NPCFactionDutyType,
    NPCGoalState,
    NPCIntent,
    NPCPlan,
    NPCPlanStatus,
    NPCPlanStep,
    NPCSocialDisposition,
    NPCState,
    PrimaryEmotion,
    RelationshipState,
    ReputationState,
    RumorState,
    RumorTruthStatus,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.npc_simulation_presets import NPCSimulationPresetApplyRequest, preview_npc_simulation_preset
from app.engine.content.validation_gate import AuthoringValidationGate, AuthoringValidationGateRequest, AuthoringValidationGateResult
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.npc_conflict_avoidance import resolve_conflict_avoidance
from app.engine.rules.npc_daily_replanning import run_daily_replanning
from app.engine.rules.npc_faction_duties import duty_to_intent
from app.engine.rules.npc_intents import enqueue_intent, prune_expired_intents, select_next_intent
from app.engine.rules.npc_memory_reactions import resolve_npc_memory_reactions
from app.engine.rules.npc_plans import advance_plan, build_plan_from_intent
from app.engine.rules.npc_relationship_behavior import resolve_relationship_behaviors
from app.engine.rules.npc_rumor_decisions import decide_npc_rumor_action
from app.engine.rules.npc_simulation_tick import NPCSimulationTickBudget, run_npc_simulation_tick
from app.llm.memory_store import MemoryRecord
from app.main import app
from app.playtesting.npc_simulation_regression import (
    NPCSimulationRegressionScenario,
    NPCSimulationRegressionScenarioType,
    run_npc_simulation_regression_suite,
)
from app.quality.npc_simulation_quality import analyze_npc_simulation_quality
from app.session_store import InMemorySessionStore, build_visible_state


def _base_state() -> GameState:
    return GameState(
        world_id="v13_integration",
        turn=0,
        current_time=GameTime(day=1, minutes_of_day=480),
        locations={
            "square": LocationState(id="square", name="Square", exits={"north": "road"}),
            "road": LocationState(id="road", name="Road", exits={"south": "square"}),
        },
        npcs={
            "guard": NPCState(
                id="guard",
                location_id="square",
                faction_id="watch",
                knowledge=["public_fact"],
                goals=[NPCGoalState(id="keep_watch", priority=10, allowed_actions=["guard_location"])],
            ),
            "friend": NPCState(id="friend", location_id="square", knowledge=["public_fact"]),
            "hidden_spy": NPCState(id="hidden_spy", location_id="square", hidden=True, visible=False, knowledge=["hidden_fact"]),
        },
        facts={
            "public_fact": FactState(id="public_fact", text="The old bridge is weak.", visibility=FactVisibility.PUBLIC),
            "hidden_fact": FactState(
                id="hidden_fact",
                text="The hidden spy works for the duke.",
                visibility=FactVisibility.HIDDEN,
                secret=True,
            ),
        },
        player_visible_facts={"public_fact"},
        npc_knowledge={"guard": {"public_fact"}, "friend": {"public_fact"}, "hidden_spy": {"hidden_fact"}},
        factions={"watch": FactionState(id="watch", name="Watch", reputation=ReputationState(value=10))},
    )


def test_v13_intent_plan_boundaries_and_dead_npc_skip() -> None:
    state = _base_state()
    intent = NPCIntent(
        id="visit-road",
        npc_id="guard",
        intent_type="visit_location",
        priority=5,
        target_id="road",
        target_type="location",
        created_turn=0,
    )

    queued = enqueue_intent(state, "guard", intent)
    assert queued.state_deltas
    assert state.npcs["guard"].intent_queue == []
    working = apply_delta(state, queued.state_deltas[0])
    assert select_next_intent(working, "guard") == intent

    plan_result = build_plan_from_intent(working, "guard", intent)
    assert plan_result.state_deltas
    assert working.npcs["guard"].plans == []
    working = apply_delta(working, plan_result.state_deltas[0])
    advanced = advance_plan(working, "guard", plan_result.plan.id)  # type: ignore[union-attr]
    assert advanced.state_deltas
    assert any(delta.path == "npcs.guard.location_id" for delta in advanced.state_deltas)

    expired = NPCIntent(id="old", npc_id="guard", intent_type="rest", created_turn=0, expires_turn=1)
    with_expired = working.model_copy(deep=True)
    with_expired.npcs["guard"].intent_queue.append(expired)
    with_expired.turn = 2
    pruned = prune_expired_intents(with_expired, "guard")
    assert pruned.events

    dead_state = _base_state()
    dead_state.npcs["guard"].alive = False
    dead_state.npcs["guard"].condition = ActorCondition.DEAD
    dead_state.npcs["guard"].plans = [
        NPCPlan(
            id="dead-plan",
            npc_id="guard",
            source_intent_id="visit-road",
            steps=[NPCPlanStep(step_type="move", target_id="road", expected_result="move")],
        )
    ]
    assert select_next_intent(dead_state, "guard") is None
    assert advance_plan(dead_state, "guard", "dead-plan").rejected_reason is None


def test_v13_memory_relationship_faction_rumor_and_social_rules() -> None:
    state = _base_state()
    state.crimes["theft"] = CrimeState(
        id="theft",
        crime_type="theft",
        actor_id="player",
        location_id="square",
        witnessed_by=["guard"],
        status=CrimeStatus.WITNESSED,
    )
    visible_memory = MemoryRecord(id="m1", content="I witnessed theft.", tags=["crime", "theft"], visibility="narrator_safe")
    hidden_memory = MemoryRecord(id="m2", content="The duke secret.", tags=["crime", "theft"], visibility="debug_only")

    reaction = resolve_npc_memory_reactions(state, "guard", [visible_memory])
    hidden_reaction = resolve_npc_memory_reactions(state, "guard", [hidden_memory])
    assert reaction.events
    assert hidden_reaction.events == []

    state.relationships["guard:player"] = RelationshipState(
        id="guard:player",
        source_id="guard",
        target_id="player",
        relation_type="ally",
        trust=80,
        affinity=60,
        known_by_player=True,
    )
    relationship = resolve_relationship_behaviors(state, "guard", "player")
    assert any("intent_queue" in delta.path for delta in relationship.state_deltas)

    duty = NPCFactionDuty(id="report-theft", duty_type=NPCFactionDutyType.REPORT_CRIME_TO_FACTION, target_id="theft", target_type="crime")
    state.npcs["guard"].knowledge.append("crime:theft")
    state.npc_knowledge["guard"].add("crime:theft")
    state.npcs["guard"].faction_duties = [duty]
    faction = duty_to_intent(state, "guard", duty)
    assert faction.intent is not None
    assert faction.intent.intent_type == "report_crime"

    state.rumors["bridge"] = RumorState(
        id="bridge",
        fact_id="public_fact",
        text_for_player="The old bridge is weak.",
        truth_status=RumorTruthStatus.TRUE,
        known_by_npcs={"guard"},
    )
    rumor = decide_npc_rumor_action(state, "guard", "bridge", target_actor_id="friend")
    repeat = decide_npc_rumor_action(state, "guard", "bridge", target_actor_id="friend")
    unknown = decide_npc_rumor_action(state, "friend", "bridge", target_actor_id="guard")
    assert rumor.decision is not None
    assert rumor.decision.decision == repeat.decision.decision  # type: ignore[union-attr]
    assert unknown.rejected_reason == "npc_unknown_rumor"


def test_v13_fear_trust_conflict_and_visibility_boundaries() -> None:
    state = _base_state()
    state.player.location_id = "square"
    state.npcs["guard"].social_disposition = NPCSocialDisposition(fear_player=80, risk_tolerance=10)
    avoidance = resolve_conflict_avoidance(state, "guard")
    assert avoidance.events
    assert avoidance.candidates[0].behavior_type.value in {"avoid_actor", "flee_from_actor"}

    injured = _base_state()
    injured.npcs["guard"].hp = 4
    injured.npcs["guard"].condition = ActorCondition.WOUNDED
    rest = resolve_conflict_avoidance(injured, "guard")
    assert rest.candidates[0].behavior_type.value == "rest"

    visible = build_visible_state(state)
    payload = visible.model_dump_json()
    assert "hidden_spy" not in payload
    assert "The hidden spy works for the duke." not in payload


def test_v13_daily_replanning_tick_budget_and_events() -> None:
    state = _base_state()
    state.npcs = {"guard": state.npcs["guard"]}
    state.current_time = state.current_time.model_copy(update={"day": 2})
    for npc_id in state.npcs:
        state.social_flags[f"npc_daily_replanning_day_1_{npc_id}"] = True
    state.npcs["guard"].faction_duties = [
        NPCFactionDuty(id="guard-square", duty_type=NPCFactionDutyType.GUARD_LOCATION, target_id="square", target_type="location")
    ]

    daily = run_daily_replanning(state, npc_ids=["guard"])
    assert daily.events
    tick = run_npc_simulation_tick(state, budget=NPCSimulationTickBudget(max_npcs_per_tick=1, max_intents_per_npc=1, max_plan_steps_per_tick=1, max_events_per_tick=2))
    assert tick.processed_npc_ids == ["guard"]
    assert len(tick.events) <= 2
    assert all(event.state_deltas for event in tick.events)


def test_v13_debug_timeline_redaction_and_player_api_boundary(tmp_path: Path) -> None:
    app.state.session_store = InMemorySessionStore(provider_factory=lambda: __import__("app.llm.mock_provider", fromlist=["MockLLMProvider"]).MockLLMProvider())
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "debug.db")
    app.state.settings = Settings(enable_debug_api=True, llm_provider="mock")
    session_id = "v13-debug"
    state = _base_state()
    session_id, loop = app.state.session_store.restore_session(state, [])
    client = TestClient(app)

    dry_run = client.post(f"/debug/sessions/{session_id}/npc-simulation/dry-run-tick")
    detail = client.get(f"/debug/sessions/{session_id}/npcs/hidden_spy/simulation")
    timeline = client.get(f"/debug/sessions/{session_id}/npcs/hidden_spy/behavior-timeline")
    player_state = client.get(f"/sessions/{session_id}/state")

    assert dry_run.status_code == 200
    assert app.state.session_store.get_session(session_id).state.model_dump(mode="json") == state.model_dump(mode="json")
    assert detail.status_code == 200
    assert timeline.status_code == 200
    assert "The hidden spy works for the duke." not in timeline.text
    assert "debug_output" not in player_state.text


def test_v13_authoring_preset_draft_gate_and_active_state(tmp_path: Path, monkeypatch) -> None:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    service = ContentAuthoringService(worlds_root)
    calls: list[AuthoringValidationGateRequest] = []
    original = AuthoringValidationGate.evaluate

    def wrapped(self: AuthoringValidationGate, request: AuthoringValidationGateRequest) -> AuthoringValidationGateResult:
        calls.append(request)
        return original(self, request)

    monkeypatch.setattr(AuthoringValidationGate, "evaluate", wrapped)
    before_yaml = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")
    before_state = WorldLoader(worlds_root).load("mist_valley").to_game_state()

    preview = preview_npc_simulation_preset(
        "mist_valley",
        "harlan",
        NPCSimulationPresetApplyRequest(preset_id="guard"),
        service,
    )
    after_state = WorldLoader(worlds_root).load("mist_valley").to_game_state()

    assert preview.validation.ok
    assert calls and calls[0].affected_files == ["npcs.yaml"]
    assert (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8") == before_yaml
    assert after_state.model_dump(mode="json") == before_state.model_dump(mode="json")


def test_v13_quality_and_regression_detect_boundaries() -> None:
    state = _base_state()
    state.npcs["guard"].intent_queue = [
        NPCIntent(id=f"loop-{index}", npc_id="guard", intent_type="spread_rumor", target_id="friend", target_type="npc", created_turn=index)
        for index in range(5)
    ]
    state.npcs["guard"].plans = [
        NPCPlan(
            id="blocked",
            npc_id="guard",
            source_intent_id="loop-1",
            status=NPCPlanStatus.BLOCKED,
            steps=[NPCPlanStep(step_type="move", target_id="missing_location", expected_result="move")],
        )
    ]
    dead_event = Event(
        event_id="dead-acted",
        turn=0,
        actor_id="system",
        target_id="hidden_spy",
        action_type="npc_simulation",
        result="acted",
        visible_to_player=False,
        state_deltas=[
            StateDelta(
                operation=StateDeltaOperation.SET,
                path="npcs.hidden_spy.current_activity",
                value="acting",
                reason="test",
                metadata={"source": "npc_simulation", "npc_id": "hidden_spy", "fact_id": "public_fact"},
            )
        ],
    )
    state.npcs["hidden_spy"].alive = False
    state.npcs["hidden_spy"].condition = ActorCondition.DEAD
    quality = analyze_npc_simulation_quality(state, events=[dead_event])
    assert quality.dead_npc_actions
    assert quality.repeated_intent_loops
    assert quality.invalid_targets

    scenario = NPCSimulationRegressionScenario(
        id="v13-regression",
        name="V13 Regression",
        scenario_type=NPCSimulationRegressionScenarioType.GUARD_PATROL,
        expected_intents=["guard_location"],
        expected_events=["npc_faction_duty"],
        forbidden_visible_facts=["hidden_plot"],
    )
    first = run_npc_simulation_regression_suite([scenario])
    second = run_npc_simulation_regression_suite([scenario])
    assert first.case_results[0].passed
    assert first.case_results[0].observed_intents == second.case_results[0].observed_intents
