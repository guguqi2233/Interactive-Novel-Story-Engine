import json
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from random import Random
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.core.world_state import CURRENT_GAME_STATE_SCHEMA_VERSION
from app.db.migrations import CURRENT_ENGINE_VERSION
from app.db.repository import SQLiteSaveRepository, SaveRepositoryError
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.content.world_loader import WorldLoader
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.playtesting.agents import PlaytestingAgent, create_playtesting_agent
from app.playtesting.invariants import check_playtest_invariants
from app.playtesting.provider import PlaytestLLMProvider
from app.quality import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)
from app.session_store import build_visible_state, create_initial_state


class PlaytestOptions(BaseModel):
    world_id: str = "mist_valley"
    strategy: str = "random_valid_action_agent"
    max_steps: int = Field(default=25, ge=0)
    seed: int = 123
    save_every: int | None = Field(default=None, ge=1)
    database_path: str | None = None
    stop_on_error: bool = False
    worlds_root: str = "worlds"


class PlaytestActionRecord(BaseModel):
    step: int
    turn_before: int
    turn_after: int
    input_text: str
    action_type: str
    result: str
    event_id: str | None = None


class PlaytestFinalStateSummary(BaseModel):
    world_id: str
    turn: int
    location_id: str
    event_count: int


class PlaytestReport(BaseModel):
    strategy: str
    world_id: str
    seed: int
    turns_run: int
    actions_taken: list[PlaytestActionRecord] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    invariant_violations: list[str] = Field(default_factory=list)
    visibility_leaks: list[str] = Field(default_factory=list)
    save_load_failures: list[str] = Field(default_factory=list)
    final_state_summary: PlaytestFinalStateSummary


class PlaytestScenarioType(StrEnum):
    EXPLORATION = "exploration"
    QUEST_PATH = "quest_path"
    COMBAT_PATH = "combat_path"
    STEALTH_PATH = "stealth_path"
    ECONOMY_PATH = "economy_path"
    CRIME_SOCIAL_PATH = "crime_social_path"
    SAVE_LOAD_PATH = "save_load_path"
    MIGRATION_PATH = "migration_path"
    HIDDEN_LEAK_PROBE = "hidden_leak_probe"


class PlaytestScenario(BaseModel):
    id: str
    world_id: str = "mist_valley"
    name: str
    description: str = ""
    scenario_type: PlaytestScenarioType = PlaytestScenarioType.EXPLORATION
    initial_conditions: dict[str, Any] = Field(default_factory=dict)
    agent_type: str = "random_valid_action_agent"
    max_steps: int = Field(default=10, ge=0)
    seed: int = 123
    expected_outcomes: dict[str, Any] = Field(default_factory=dict)
    forbidden_outcomes: dict[str, Any] = Field(default_factory=dict)
    invariants: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class PlaytestScenarioReport(BaseModel):
    scenario_id: str
    scenario_type: PlaytestScenarioType
    world_id: str
    name: str
    passed: bool
    failure_reasons: list[str] = Field(default_factory=list)
    hidden_leak_summary: list[str] = Field(default_factory=list)
    playtest_report: PlaytestReport
    visible_summary: dict[str, Any] = Field(default_factory=dict)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return _strip_debug_only(payload)


def run_playtest(
    options: PlaytestOptions,
    agent: PlaytestingAgent | None = None,
) -> PlaytestReport:
    rng = Random(options.seed)
    active_agent = agent or create_playtesting_agent(options.strategy)
    game_loop = _build_game_loop(options, rng)
    repository = _build_repository(options)

    actions_taken: list[PlaytestActionRecord] = []
    errors: list[str] = []
    invariant_violations: list[str] = []
    visibility_leaks: list[str] = []
    save_load_failures: list[str] = []

    for step in range(options.max_steps):
        previous_turn = game_loop.state.turn
        visible_state = build_visible_state(game_loop.state)
        player_input = active_agent.choose_action(visible_state, rng)
        events_before = len(game_loop.event_log.list_events())

        try:
            result = game_loop.step(player_input)
            latest_event = result.event
            if len(game_loop.event_log.list_events()) <= events_before:
                invariant_violations.append(f"agent_action_missing_event:step:{step}")
            actions_taken.append(
                PlaytestActionRecord(
                    step=step,
                    turn_before=previous_turn,
                    turn_after=result.state.turn,
                    input_text=player_input,
                    action_type=result.intent.action_type.value,
                    result=latest_event.result if latest_event else "missing_event",
                    event_id=latest_event.event_id if latest_event else None,
                )
            )
        except Exception as exc:
            errors.append(f"step:{step}:{type(exc).__name__}:{exc}")
            if options.stop_on_error:
                break
            continue

        check_result = check_playtest_invariants(
            game_loop.state,
            game_loop.event_log.list_events(),
            previous_turn=previous_turn,
            visible_payload=build_visible_state(game_loop.state).model_dump(mode="json"),
        )
        invariant_violations.extend(check_result.invariant_violations)
        visibility_leaks.extend(check_result.visibility_leaks)

        if repository is not None and options.save_every and (step + 1) % options.save_every == 0:
            save_load_failures.extend(_round_trip_save_load(repository, game_loop, "playtest-roundtrip"))

    final_check = check_playtest_invariants(game_loop.state, game_loop.event_log.list_events())
    invariant_violations.extend(final_check.invariant_violations)
    visibility_leaks.extend(final_check.visibility_leaks)

    return PlaytestReport(
        strategy=active_agent.strategy_name,
        world_id=game_loop.state.world_id,
        seed=options.seed,
        turns_run=len(actions_taken),
        actions_taken=actions_taken,
        errors=_dedupe(errors),
        invariant_violations=_dedupe(invariant_violations),
        visibility_leaks=_dedupe(visibility_leaks),
        save_load_failures=_dedupe(save_load_failures),
        final_state_summary=PlaytestFinalStateSummary(
            world_id=game_loop.state.world_id,
            turn=game_loop.state.turn,
            location_id=game_loop.state.player.location_id,
            event_count=len(game_loop.event_log.list_events()),
        ),
    )


def run_playtest_scenario(
    scenario: PlaytestScenario,
    *,
    database_path: str | None = None,
    worlds_root: str = "worlds",
) -> PlaytestScenarioReport:
    options = PlaytestOptions(
        world_id=scenario.world_id,
        strategy=scenario.agent_type,
        max_steps=scenario.max_steps,
        seed=scenario.seed,
        save_every=_scenario_save_every(scenario),
        database_path=database_path,
        worlds_root=worlds_root,
    )
    playtest_report = run_playtest(options)
    game_loop = _replay_for_visible_summary(scenario, worlds_root=worlds_root)
    visible_summary = _scenario_visible_summary(game_loop)
    failure_reasons = _evaluate_scenario_outcomes(
        scenario,
        playtest_report,
        visible_summary,
    )
    hidden_leaks = _scenario_hidden_leaks(scenario, visible_summary, playtest_report)
    failure_reasons.extend(hidden_leaks)
    quality_report = world_quality_report_from_playtest_scenario(
        scenario,
        playtest_report,
        failure_reasons=_dedupe(failure_reasons),
        hidden_leaks=_dedupe(hidden_leaks),
    )
    return PlaytestScenarioReport(
        scenario_id=scenario.id,
        scenario_type=scenario.scenario_type,
        world_id=scenario.world_id,
        name=scenario.name,
        passed=not failure_reasons and not playtest_report.errors,
        failure_reasons=_dedupe(failure_reasons),
        hidden_leak_summary=_dedupe(hidden_leaks),
        playtest_report=playtest_report,
        visible_summary=visible_summary,
        quality_report=quality_report,
    )


def world_quality_report_from_playtest_scenario(
    scenario: PlaytestScenario,
    playtest_report: PlaytestReport,
    *,
    failure_reasons: list[str] | None = None,
    hidden_leaks: list[str] | None = None,
) -> WorldQualityReport:
    failures = failure_reasons or []
    leaks = hidden_leaks or []
    issues = [
        QualityIssue(
            id=f"playtest:{scenario.id}:error:{index}",
            severity=QualityIssueSeverity.ERROR,
            category="playtesting",
            entity_id=scenario.id,
            message=reason,
            safe_details={"scenario_type": scenario.scenario_type.value},
        )
        for index, reason in enumerate([*playtest_report.errors, *failures])
    ]
    issues.extend(
        QualityIssue(
            id=f"playtest:{scenario.id}:visibility:{index}",
            severity=QualityIssueSeverity.BLOCKER,
            category="visibility",
            entity_id=scenario.id,
            message=leak,
            safe_details={"scenario_type": scenario.scenario_type.value},
        )
        for index, leak in enumerate(leaks)
    )
    status = QualityMetricStatus.OK if not issues else QualityMetricStatus.ERROR
    if leaks:
        status = QualityMetricStatus.BLOCKER
    return WorldQualityReport(
        run_id=f"playtest-scenario-{uuid4()}",
        world_id=scenario.world_id,
        created_at=datetime.now(timezone.utc),
        engine_version=CURRENT_ENGINE_VERSION,
        schema_version=CURRENT_GAME_STATE_SCHEMA_VERSION,
        categories=["playtesting", scenario.scenario_type.value],
        metrics=[
            QualityMetric(
                name="turns_run",
                value=playtest_report.turns_run,
                category="playtesting",
                status=QualityMetricStatus.OK,
            ),
            QualityMetric(
                name="actions_taken",
                value=len(playtest_report.actions_taken),
                category="playtesting",
                status=QualityMetricStatus.OK,
            ),
            QualityMetric(
                name="scenario_failures",
                value=len(issues),
                category="playtesting",
                threshold=0,
                status=status,
            ),
        ],
        issues=issues,
        summary={
            "scenario_id": scenario.id,
            "scenario_type": scenario.scenario_type.value,
            "passed": not issues,
            "errors": len(playtest_report.errors),
            "invariant_violations": len(playtest_report.invariant_violations),
            "visibility_leaks": len(playtest_report.visibility_leaks) + len(leaks),
            "save_load_failures": len(playtest_report.save_load_failures),
        },
        recommended_actions=_scenario_recommended_actions(issues, leaks),
    )


def _build_game_loop(options: PlaytestOptions, rng: Random) -> GameLoop:
    provider = PlaytestLLMProvider()
    state = create_initial_state(WorldLoader(options.worlds_root), options.world_id)
    return GameLoop(
        state=state,
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=rng,
    )


def _build_repository(options: PlaytestOptions) -> SQLiteSaveRepository | None:
    if options.database_path is None:
        return None
    database_path = Path(options.database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return SQLiteSaveRepository(database_path)


def _round_trip_save_load(
    repository: SQLiteSaveRepository,
    game_loop: GameLoop,
    save_id: str | None = None,
) -> list[str]:
    active_save_id = save_id or f"playtest-{uuid4()}"
    try:
        repository.save_snapshot(active_save_id, game_loop.state, game_loop.event_log.list_events())
        loaded_state = repository.load_save(active_save_id)
        loaded_events = repository.list_events(active_save_id)
    except SaveRepositoryError as exc:
        return [f"save_load_error:{exc}"]

    failures: list[str] = []
    if _canonical_json(loaded_state.model_dump(mode="json")) != _canonical_json(game_loop.state.model_dump(mode="json")):
        failures.append("save_load_state_mismatch")
    if len(loaded_events) != len(game_loop.event_log.list_events()):
        failures.append("save_load_event_count_mismatch")
    return failures


def _replay_for_visible_summary(scenario: PlaytestScenario, *, worlds_root: str) -> GameLoop:
    rng = Random(scenario.seed)
    game_loop = _build_game_loop(
        PlaytestOptions(
            world_id=scenario.world_id,
            strategy=scenario.agent_type,
            max_steps=scenario.max_steps,
            seed=scenario.seed,
            worlds_root=worlds_root,
        ),
        rng,
    )
    agent = create_playtesting_agent(scenario.agent_type)
    for _step in range(scenario.max_steps):
        visible_state = build_visible_state(game_loop.state)
        game_loop.step(agent.choose_action(visible_state, rng))
    return game_loop


def _scenario_visible_summary(game_loop: GameLoop) -> dict[str, Any]:
    visible = build_visible_state(game_loop.state)
    return {
        "turn": game_loop.state.turn,
        "location_id": game_loop.state.player.location_id,
        "visible_facts": sorted(fact.id for fact in visible.known_facts),
        "inventory": sorted(item.id for item in visible.inventory),
        "quests": {quest.id: quest.status for quest in visible.quests},
        "action_types": [event.action_type for event in game_loop.event_log.list_events()],
        "event_count": len(game_loop.event_log.list_events()),
    }


def _evaluate_scenario_outcomes(
    scenario: PlaytestScenario,
    report: PlaytestReport,
    visible_summary: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    failures.extend(report.errors)
    failures.extend(report.invariant_violations)
    failures.extend(report.save_load_failures)
    failures.extend(_check_expected_outcomes(scenario.expected_outcomes, visible_summary))
    failures.extend(_check_forbidden_outcomes(scenario.forbidden_outcomes, visible_summary))
    return _dedupe(failures)


def _check_expected_outcomes(expected: dict[str, Any], visible_summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for fact_id in expected.get("visible_facts", []):
        if fact_id not in visible_summary["visible_facts"]:
            failures.append(f"expected_visible_fact_missing:{fact_id}")
    for item_id in expected.get("inventory", []):
        if item_id not in visible_summary["inventory"]:
            failures.append(f"expected_inventory_missing:{item_id}")
    for action_type in expected.get("action_types", []):
        if action_type not in visible_summary["action_types"]:
            failures.append(f"expected_action_type_missing:{action_type}")
    expected_location = expected.get("location_id")
    if expected_location and visible_summary["location_id"] != expected_location:
        failures.append(f"expected_location_mismatch:{expected_location}:actual:{visible_summary['location_id']}")
    for quest_id, expected_status in expected.get("quest_states", {}).items():
        actual_status = visible_summary["quests"].get(quest_id)
        if actual_status != expected_status:
            failures.append(f"expected_quest_state_mismatch:{quest_id}:{expected_status}:actual:{actual_status}")
    min_turns = expected.get("min_turns")
    if min_turns is not None and visible_summary["turn"] < min_turns:
        failures.append(f"expected_min_turns_not_met:{min_turns}:actual:{visible_summary['turn']}")
    return failures


def _check_forbidden_outcomes(forbidden: dict[str, Any], visible_summary: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for fact_id in forbidden.get("visible_facts", []):
        if fact_id in visible_summary["visible_facts"]:
            failures.append(f"forbidden_visible_fact_present:{fact_id}")
    for item_id in forbidden.get("inventory", []):
        if item_id in visible_summary["inventory"]:
            failures.append(f"forbidden_inventory_present:{item_id}")
    for action_type in forbidden.get("action_types", []):
        if action_type in visible_summary["action_types"]:
            failures.append(f"forbidden_action_type_present:{action_type}")
    return failures


def _scenario_hidden_leaks(
    scenario: PlaytestScenario,
    visible_summary: dict[str, Any],
    report: PlaytestReport,
) -> list[str]:
    leaks = list(report.visibility_leaks)
    if scenario.scenario_type == PlaytestScenarioType.HIDDEN_LEAK_PROBE:
        for fact_id in scenario.forbidden_outcomes.get("visible_facts", []):
            if fact_id in visible_summary["visible_facts"]:
                leaks.append(f"hidden_leak_probe_forbidden_visible_fact:{fact_id}")
    return _dedupe(leaks)


def _scenario_save_every(scenario: PlaytestScenario) -> int | None:
    if scenario.scenario_type in {PlaytestScenarioType.SAVE_LOAD_PATH, PlaytestScenarioType.MIGRATION_PATH}:
        return max(1, scenario.max_steps // 2) if scenario.max_steps else 1
    return scenario.initial_conditions.get("save_every")


def _scenario_recommended_actions(issues: list[QualityIssue], leaks: list[str]) -> list[str]:
    actions: list[str] = []
    if leaks:
        actions.append("Review visibility rules and hidden fact boundaries for this scenario.")
    if issues:
        actions.append("Inspect playtest failures before using this world pack for regression acceptance.")
    return actions


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _strip_debug_only(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_debug_only(item)
            for key, item in value.items()
            if key != "hidden_details_debug_only" and not str(key).endswith("_debug_only")
        }
    if isinstance(value, list):
        return [_strip_debug_only(item) for item in value]
    return value


def _canonical_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _canonical_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        items = [_canonical_json(item) for item in value]
        if all(not isinstance(item, dict | list) for item in items):
            return sorted(items, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
        return items
    return value
