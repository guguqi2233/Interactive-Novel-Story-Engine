from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import apply_delta
from app.core.world_state import (
    ActorCondition,
    CrimeState,
    CrimeStatus,
    EmotionalState,
    FactState,
    FactVisibility,
    FactionState,
    GameState,
    LocationState,
    NPCFactionDuty,
    NPCFactionDutyType,
    NPCGoalState,
    NPCIntent,
    NPCState,
    NPCSocialDisposition,
    PlayerState,
    PrimaryEmotion,
    RelationshipState,
    ReputationState,
    RumorState,
    RumorTruthStatus,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.rules.npc_simulation_tick import NPCSimulationTickBudget, NPCSimulationTickResult, run_npc_simulation_tick
from app.quality.npc_simulation_quality import NPCSimulationQualityReport, analyze_npc_simulation_quality
from app.session_store import build_visible_state


class NPCSimulationRegressionScenarioType(StrEnum):
    GUARD_PATROL = "guard_patrol"
    REPORT_CRIME = "report_crime"
    SPREAD_RUMOR = "spread_rumor"
    AVOID_PLAYER = "avoid_player"
    SEEK_HELP = "seek_help"
    DAILY_REPLAN = "daily_replan"
    RELATIONSHIP_RESPONSE = "relationship_response"
    FACTION_DUTY = "faction_duty"
    INJURED_REST = "injured_rest"


class NPCSimulationRegressionScenario(BaseModel):
    id: str
    name: str
    scenario_type: NPCSimulationRegressionScenarioType
    initial_state: dict[str, Any] = Field(default_factory=dict)
    turns_to_run: int = Field(default=3, ge=0, le=50)
    expected_intents: list[str] = Field(default_factory=list)
    forbidden_intents: list[str] = Field(default_factory=list)
    expected_events: list[str] = Field(default_factory=list)
    forbidden_visible_facts: list[str] = Field(default_factory=list)
    max_plan_failures: int = Field(default=0, ge=0)
    seed: int = 123


class NPCSimulationRegressionCaseResult(BaseModel):
    scenario_id: str
    scenario_type: NPCSimulationRegressionScenarioType
    name: str
    passed: bool
    turns_run: int
    failure_reasons: list[str] = Field(default_factory=list)
    observed_intents: list[str] = Field(default_factory=list)
    observed_events: list[str] = Field(default_factory=list)
    hidden_leak_summary: list[str] = Field(default_factory=list)
    save_load_failure: str | None = None
    quality_report: NPCSimulationQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return _strip_debug_only(payload)


class NPCSimulationRegressionReport(BaseModel):
    run_id: str = Field(default_factory=lambda: f"npc-simulation-regression-{uuid4()}")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_cases: int
    passed: int
    failed: int
    case_results: list[NPCSimulationRegressionCaseResult] = Field(default_factory=list)

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["case_results"] = [result.model_dump_normal() for result in self.case_results]
        return _strip_debug_only(payload)


def sample_npc_simulation_regression_scenarios() -> list[NPCSimulationRegressionScenario]:
    return [
        NPCSimulationRegressionScenario(
            id="npc_guard_patrol",
            name="Guard patrol intent",
            scenario_type=NPCSimulationRegressionScenarioType.GUARD_PATROL,
            expected_intents=["guard_location"],
            expected_events=["npc_faction_duty", "npc_plan_built"],
            forbidden_visible_facts=["hidden_plot"],
        ),
        NPCSimulationRegressionScenario(
            id="npc_report_crime",
            name="Report known crime",
            scenario_type=NPCSimulationRegressionScenarioType.REPORT_CRIME,
            expected_intents=["report_crime"],
            expected_events=["npc_faction_duty"],
            forbidden_visible_facts=["hidden_plot"],
        ),
        NPCSimulationRegressionScenario(
            id="npc_spread_rumor",
            name="Spread known rumor",
            scenario_type=NPCSimulationRegressionScenarioType.SPREAD_RUMOR,
            expected_intents=["spread_rumor"],
            expected_events=["npc_rumor_decision"],
            forbidden_visible_facts=["hidden_plot"],
        ),
        NPCSimulationRegressionScenario(
            id="npc_avoid_player",
            name="Avoid feared player",
            scenario_type=NPCSimulationRegressionScenarioType.AVOID_PLAYER,
            expected_intents=["avoid_actor"],
            forbidden_visible_facts=["hidden_plot"],
        ),
        NPCSimulationRegressionScenario(
            id="npc_seek_help",
            name="Guard seeks help",
            scenario_type=NPCSimulationRegressionScenarioType.SEEK_HELP,
            expected_intents=["call_for_help"],
            forbidden_visible_facts=["hidden_plot"],
        ),
        NPCSimulationRegressionScenario(
            id="npc_daily_replan",
            name="Daily replanning",
            scenario_type=NPCSimulationRegressionScenarioType.DAILY_REPLAN,
            expected_intents=["guard_location"],
            expected_events=["npc_daily_replanning"],
            forbidden_visible_facts=["hidden_plot"],
        ),
        NPCSimulationRegressionScenario(
            id="npc_relationship_response",
            name="Relationship response",
            scenario_type=NPCSimulationRegressionScenarioType.RELATIONSHIP_RESPONSE,
            expected_intents=["warn_actor"],
            forbidden_visible_facts=["hidden_plot"],
        ),
        NPCSimulationRegressionScenario(
            id="npc_faction_duty",
            name="Faction duty",
            scenario_type=NPCSimulationRegressionScenarioType.FACTION_DUTY,
            expected_intents=["guard_location"],
            expected_events=["npc_faction_duty"],
            forbidden_visible_facts=["hidden_plot"],
        ),
        NPCSimulationRegressionScenario(
            id="npc_injured_rest",
            name="Injured NPC rests",
            scenario_type=NPCSimulationRegressionScenarioType.INJURED_REST,
            expected_intents=["rest"],
            forbidden_visible_facts=["hidden_plot"],
        ),
    ]


def run_npc_simulation_regression_suite(
    scenarios: list[NPCSimulationRegressionScenario],
) -> NPCSimulationRegressionReport:
    with TemporaryDirectory(prefix="llm_world_npc_sim_regression_", ignore_cleanup_errors=True) as temp_dir:
        repository = SQLiteSaveRepository(Path(temp_dir) / "npc_simulation_regression.db")
        results = [_run_scenario(scenario, repository) for scenario in scenarios]
    passed = sum(1 for result in results if result.passed)
    return NPCSimulationRegressionReport(
        total_cases=len(results),
        passed=passed,
        failed=len(results) - passed,
        case_results=results,
    )


def _run_scenario(
    scenario: NPCSimulationRegressionScenario,
    repository: SQLiteSaveRepository,
) -> NPCSimulationRegressionCaseResult:
    state = _initial_state_for_scenario(scenario)
    events: list[Event] = []
    tick_results: list[NPCSimulationTickResult] = []
    failure_reasons: list[str] = []
    save_load_failure: str | None = None
    budget = NPCSimulationTickBudget(max_npcs_per_tick=6, max_intents_per_npc=4, max_plan_steps_per_tick=4, max_events_per_tick=20)

    for turn_index in range(scenario.turns_to_run):
        tick = run_npc_simulation_tick(state, budget=budget)
        tick_results.append(tick)
        events.extend(tick.events)
        for delta in tick.state_deltas:
            state = apply_delta(state, delta)
        state = state.model_copy(update={"turn": state.turn + 1})
        save_load_failure = _save_load_check(repository, scenario.id, turn_index, state, events)
        if save_load_failure:
            failure_reasons.append(save_load_failure)
            break
        loaded = repository.load_save(f"npc-sim-regression-{scenario.id}-{turn_index}")
        if loaded.turn != state.turn:
            failure_reasons.append("save_load_turn_mismatch")
            break

    visible = build_visible_state(state)
    visible_fact_ids = {fact.id for fact in visible.known_facts}
    hidden_leaks: list[str] = []
    for fact_id in scenario.forbidden_visible_facts:
        if fact_id in visible_fact_ids:
            reason = f"forbidden_visible_fact_present:{fact_id}"
            hidden_leaks.append(reason)
            failure_reasons.append(reason)

    observed_intents = _observed_intents(state, events)
    observed_events = sorted({event.action_type for event in events})
    for intent in scenario.expected_intents:
        if intent not in observed_intents:
            failure_reasons.append(f"expected_intent_missing:{intent}")
    for intent in scenario.forbidden_intents:
        if intent in observed_intents:
            failure_reasons.append(f"forbidden_intent_present:{intent}")
    for event_type in scenario.expected_events:
        if event_type not in observed_events:
            failure_reasons.append(f"expected_event_missing:{event_type}")
    plan_failures = sum(1 for event in events if event.action_type in {"npc_plan_blocked", "npc_plan_failed"})
    if plan_failures > scenario.max_plan_failures:
        failure_reasons.append(f"plan_failures_exceeded:{plan_failures}:max:{scenario.max_plan_failures}")

    quality = analyze_npc_simulation_quality(state, events=events, tick_results=tick_results, budget=budget)
    for issue in quality.quality_report.issues:
        if issue.severity.value in {"blocker", "error"}:
            failure_reasons.append(f"quality:{issue.category}:{issue.id}")
    if quality.repeated_intent_loops:
        failure_reasons.append("quality:repeated_intent_loop")
    if quality.hidden_fact_leaks:
        hidden_leaks.append("quality:hidden_fact_leak")

    return NPCSimulationRegressionCaseResult(
        scenario_id=scenario.id,
        scenario_type=scenario.scenario_type,
        name=scenario.name,
        passed=not failure_reasons and not hidden_leaks,
        turns_run=state.turn,
        failure_reasons=_dedupe(_redact_hidden_text(failure_reasons)),
        observed_intents=observed_intents,
        observed_events=observed_events,
        hidden_leak_summary=_dedupe(_redact_hidden_text(hidden_leaks)),
        save_load_failure=save_load_failure,
        quality_report=quality,
    )


def _initial_state_for_scenario(scenario: NPCSimulationRegressionScenario) -> GameState:
    if scenario.initial_state:
        return GameState.model_validate(scenario.initial_state)
    state = _base_state()
    if scenario.scenario_type in {NPCSimulationRegressionScenarioType.GUARD_PATROL, NPCSimulationRegressionScenarioType.FACTION_DUTY}:
        state.npcs["guard"].faction_duties = [
            NPCFactionDuty(id="guard-square", duty_type=NPCFactionDutyType.GUARD_LOCATION, priority=80, target_id="square", target_type="location")
        ]
    elif scenario.scenario_type == NPCSimulationRegressionScenarioType.REPORT_CRIME:
        state.crimes["theft"] = CrimeState(
            id="theft",
            crime_type="theft",
            actor_id="player",
            location_id="square",
            witnessed_by=["guard"],
            status=CrimeStatus.WITNESSED,
        )
        state.npcs["guard"].knowledge.append("crime:theft")
        state.npc_knowledge["guard"].add("crime:theft")
        state.npcs["guard"].faction_duties = [
            NPCFactionDuty(id="report-theft", duty_type=NPCFactionDutyType.REPORT_CRIME_TO_FACTION, priority=90, target_id="theft", target_type="crime")
        ]
    elif scenario.scenario_type == NPCSimulationRegressionScenarioType.SPREAD_RUMOR:
        state.rumors["bridge"] = RumorState(
            id="bridge",
            fact_id="public_tip",
            text_for_player="The bridge is weak.",
            truth_status=RumorTruthStatus.TRUE,
            known_by_npcs={"guard"},
            spread_level=1,
        )
    elif scenario.scenario_type == NPCSimulationRegressionScenarioType.AVOID_PLAYER:
        state.npcs["guard"].social_disposition = NPCSocialDisposition(fear_player=80, risk_tolerance=10)
    elif scenario.scenario_type == NPCSimulationRegressionScenarioType.SEEK_HELP:
        state.player.combat_stance = "aggressive"
        state.npcs["guard"].faction_duties = [
            NPCFactionDuty(id="guard-square", duty_type=NPCFactionDutyType.GUARD_LOCATION, priority=80, target_id="square", target_type="location")
        ]
    elif scenario.scenario_type == NPCSimulationRegressionScenarioType.DAILY_REPLAN:
        state.turn = 24
        state.current_time = state.current_time.model_copy(update={"day": 2})
        for npc_id in state.npcs:
            state.social_flags[f"npc_daily_replanning_day_1_{npc_id}"] = True
        state.npcs["guard"].faction_duties = [
            NPCFactionDuty(id="guard-square", duty_type=NPCFactionDutyType.GUARD_LOCATION, priority=80, target_id="square", target_type="location")
        ]
    elif scenario.scenario_type == NPCSimulationRegressionScenarioType.RELATIONSHIP_RESPONSE:
        state.relationships["guard:player"] = RelationshipState(
            id="guard:player",
            source_id="guard",
            target_id="player",
            relation_type="ally",
            trust=80,
            affinity=60,
            known_by_player=True,
        )
        state.facts["public_tip"] = FactState(id="public_tip", text="The bridge is weak.", visibility=FactVisibility.PUBLIC)
        state.npcs["guard"].knowledge.append("public_tip")
        state.npc_knowledge["guard"].add("public_tip")
    elif scenario.scenario_type == NPCSimulationRegressionScenarioType.INJURED_REST:
        state.npcs["guard"].hp = 4
        state.npcs["guard"].condition = ActorCondition.WOUNDED
    return state


def _base_state() -> GameState:
    return GameState(
        world_id="npc_sim_regression",
        player=PlayerState(location_id="square"),
        locations={
            "square": LocationState(id="square", name="Square", exits={"north": "road"}),
            "road": LocationState(id="road", name="Road", exits={"south": "square"}),
        },
        npcs={
            "guard": NPCState(
                id="guard",
                location_id="square",
                faction_id="watch",
                knowledge=["public_tip"],
                goals=[
                    NPCGoalState(
                        id="keep_watch",
                        description="Keep watch.",
                        priority=10,
                        allowed_actions=["guard_location"],
                    )
                ],
            ),
            "villager": NPCState(id="villager", location_id="square", knowledge=[]),
            "hidden_spy": NPCState(id="hidden_spy", location_id="square", hidden=True, visible=False, knowledge=["hidden_plot"]),
        },
        facts={
            "public_tip": FactState(id="public_tip", text="The bridge is weak.", visibility=FactVisibility.PUBLIC),
            "hidden_plot": FactState(
                id="hidden_plot",
                text="The hidden spy works for the duke.",
                visibility=FactVisibility.HIDDEN,
                secret=True,
            ),
        },
        player_visible_facts={"public_tip"},
        npc_knowledge={"guard": {"public_tip"}, "villager": set(), "hidden_spy": {"hidden_plot"}},
        factions={
            "watch": FactionState(id="watch", name="Village Watch", reputation=ReputationState(value=20)),
        },
    )


def _observed_intents(state: GameState, events: list[Event]) -> list[str]:
    intents = {intent.intent_type for npc in state.npcs.values() for intent in npc.intent_queue}
    for event in events:
        if event.action_type == "npc_plan_built" and event.result.startswith("plan-"):
            pass
        for delta in event.state_deltas:
            intent_type = delta.metadata.get("intent_type") or delta.metadata.get("plan_type")
            if intent_type:
                intents.add(str(intent_type))
            value = delta.value
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and item.get("intent_type"):
                        intents.add(str(item["intent_type"]))
    return sorted(intents)


def _save_load_check(
    repository: SQLiteSaveRepository,
    scenario_id: str,
    turn_index: int,
    state: GameState,
    events: list[Event],
) -> str | None:
    save_id = f"npc-sim-regression-{scenario_id}-{turn_index}"
    repository.save_snapshot(save_id, state, _events_for_save(save_id, events))
    loaded = repository.load_save(save_id)
    if loaded.world_id != state.world_id:
        return "save_load_world_mismatch"
    if loaded.turn != state.turn:
        return "save_load_turn_mismatch"
    return None


def _events_for_save(save_id: str, events: list[Event]) -> list[Event]:
    return [
        event.model_copy(update={"event_id": f"{save_id}-{index}-{event.event_id}"})
        for index, event in enumerate(events)
    ]


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _redact_hidden_text(values: list[str]) -> list[str]:
    return [
        value.replace("The hidden spy works for the duke.", "[hidden text redacted]")
        for value in values
    ]


def _strip_debug_only(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_debug_only(item)
            for key, item in value.items()
            if key != "hidden_details_debug_only" and not str(key).endswith("_debug_only")
        }
    if isinstance(value, list):
        return [_strip_debug_only(item) for item in value]
    if isinstance(value, str):
        return value.replace("The hidden spy works for the duke.", "[hidden text redacted]")
    return value
