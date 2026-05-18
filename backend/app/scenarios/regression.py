from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.db.repository import SQLiteSaveRepository
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.content.world_loader import WorldLoader
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.playtesting.invariants import check_playtest_invariants
from app.playtesting.provider import PlaytestLLMProvider
from app.session_store import build_visible_state, create_initial_state


class ScenarioRegressionCase(BaseModel):
    id: str
    world_id: str
    name: str
    description: str = ""
    initial_save: str | None = None
    input_sequence: list[str] = Field(default_factory=list)
    expected_visible_facts: list[str] = Field(default_factory=list)
    forbidden_visible_facts: list[str] = Field(default_factory=list)
    expected_quest_states: dict[str, str] = Field(default_factory=dict)
    expected_inventory: list[str] = Field(default_factory=list)
    max_turns: int = Field(default=20, ge=0)
    tags: list[str] = Field(default_factory=list)


class ScenarioRegressionCaseResult(BaseModel):
    case_id: str
    world_id: str
    name: str
    passed: bool
    failed_step: int | None = None
    failure_reasons: list[str] = Field(default_factory=list)
    expected_summary: dict[str, object] = Field(default_factory=dict)
    actual_summary: dict[str, object] = Field(default_factory=dict)
    hidden_leak_summary: list[str] = Field(default_factory=list)
    save_load_failure: str | None = None


class ScenarioRegressionRun(BaseModel):
    run_id: str
    created_at: str
    world_id: str | None = None
    total_cases: int
    passed: int
    failed: int
    case_results: list[ScenarioRegressionCaseResult] = Field(default_factory=list)


class ScenarioRegressionRunRequest(BaseModel):
    world_id: str | None = None
    scenario_ids: list[str] = Field(default_factory=list)


class ScenarioRegressionListResponse(BaseModel):
    local_only: bool = True
    cases: list[ScenarioRegressionCase] = Field(default_factory=list)


def sample_scenario_regression_cases() -> list[ScenarioRegressionCase]:
    return [
        ScenarioRegressionCase(
            id="mist_valley_opening_observe",
            world_id="mist_valley",
            name="Opening observe boundary",
            description="Start Mist Valley and observe without revealing hidden facts.",
            input_sequence=["observe"],
            expected_visible_facts=["village_square_is_misty"],
            forbidden_visible_facts=["sealed_letter_under_stone"],
            max_turns=3,
            tags=["opening", "visibility"],
        ),
        ScenarioRegressionCase(
            id="mist_valley_search_letter",
            world_id="mist_valley",
            name="Search discovers village clue",
            description="Search the opening location and verify the discoverable object path remains stable.",
            input_sequence=["search"],
            forbidden_visible_facts=["sealed_letter_under_stone"],
            max_turns=3,
            tags=["search", "hidden-boundary"],
        ),
    ]


def run_scenario_regression_suite(
    cases: list[ScenarioRegressionCase],
    *,
    worlds_root: str | Path = "worlds",
) -> ScenarioRegressionRun:
    results: list[ScenarioRegressionCaseResult] = []
    with TemporaryDirectory(prefix="llm_world_scenario_regression_", ignore_cleanup_errors=True) as temp_dir:
        repository = SQLiteSaveRepository(Path(temp_dir) / "scenario_regression.db")
        for case in cases:
            results.append(_run_case(case, worlds_root=worlds_root, repository=repository))
    passed = sum(1 for result in results if result.passed)
    return ScenarioRegressionRun(
        run_id=f"scenario-regression-{uuid4()}",
        created_at=datetime.now(timezone.utc).isoformat(),
        world_id=cases[0].world_id if cases and len({case.world_id for case in cases}) == 1 else None,
        total_cases=len(results),
        passed=passed,
        failed=len(results) - passed,
        case_results=results,
    )


def _run_case(
    case: ScenarioRegressionCase,
    *,
    worlds_root: str | Path,
    repository: SQLiteSaveRepository,
) -> ScenarioRegressionCaseResult:
    provider = PlaytestLLMProvider()
    game_loop = GameLoop(
        state=create_initial_state(WorldLoader(worlds_root), case.world_id),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(123),
    )
    failure_reasons: list[str] = []
    failed_step: int | None = None
    inputs = case.input_sequence[: case.max_turns]
    for index, player_input in enumerate(inputs):
        try:
            game_loop.step(player_input)
        except Exception as exc:
            failed_step = index
            failure_reasons.append(f"step:{index}:{type(exc).__name__}:{exc}")
            break
    visible = build_visible_state(game_loop.state)
    visible_payload = visible.model_dump(mode="json")
    visible_fact_ids = {fact.id for fact in visible.known_facts}
    inventory_ids = {item.id for item in visible.inventory}
    quest_states = {quest.id: quest.status for quest in visible.quests}
    hidden_leaks: list[str] = []
    for fact_id in case.expected_visible_facts:
        if fact_id not in visible_fact_ids:
            failure_reasons.append(f"expected_visible_fact_missing:{fact_id}")
    for fact_id in case.forbidden_visible_facts:
        if fact_id in visible_fact_ids:
            reason = f"forbidden_visible_fact_present:{fact_id}"
            failure_reasons.append(reason)
            hidden_leaks.append(reason)
    for quest_id, expected_status in case.expected_quest_states.items():
        actual_status = quest_states.get(quest_id)
        if actual_status != expected_status:
            failure_reasons.append(f"quest_state_mismatch:{quest_id}:expected:{expected_status}:actual:{actual_status}")
    for item_id in case.expected_inventory:
        if item_id not in inventory_ids:
            failure_reasons.append(f"expected_inventory_missing:{item_id}")
    invariant_result = check_playtest_invariants(
        game_loop.state,
        game_loop.event_log.list_events(),
        visible_payload=visible_payload,
    )
    failure_reasons.extend(invariant_result.invariant_violations)
    hidden_leaks.extend(invariant_result.visibility_leaks)
    save_load_failure = _save_load_check(repository, game_loop, case.id)
    if save_load_failure:
        failure_reasons.append(save_load_failure)
    return ScenarioRegressionCaseResult(
        case_id=case.id,
        world_id=case.world_id,
        name=case.name,
        passed=not failure_reasons and not hidden_leaks,
        failed_step=failed_step,
        failure_reasons=_redact_hidden_text(_dedupe(failure_reasons)),
        expected_summary={
            "visible_facts": case.expected_visible_facts,
            "forbidden_visible_facts": case.forbidden_visible_facts,
            "quest_states": case.expected_quest_states,
            "inventory": case.expected_inventory,
        },
        actual_summary={
            "turn": game_loop.state.turn,
            "location_id": game_loop.state.player.location_id,
            "visible_facts": sorted(visible_fact_ids),
            "quest_states": quest_states,
            "inventory": sorted(inventory_ids),
            "event_count": len(game_loop.event_log.list_events()),
        },
        hidden_leak_summary=_redact_hidden_text(_dedupe(hidden_leaks)),
        save_load_failure=save_load_failure,
    )


def _save_load_check(repository: SQLiteSaveRepository, game_loop: GameLoop, case_id: str) -> str | None:
    save_id = f"scenario-regression-{case_id}"
    repository.save_snapshot(save_id, game_loop.state, game_loop.event_log.list_events())
    loaded_state = repository.load_save(save_id)
    if loaded_state.turn != game_loop.state.turn:
        return "save_load_turn_mismatch"
    if loaded_state.player.location_id != game_loop.state.player.location_id:
        return "save_load_location_mismatch"
    return None


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _redact_hidden_text(values: list[str]) -> list[str]:
    return [
        value.replace("A sealed letter is hidden beneath a loose paving stone.", "[hidden text redacted]")
        .replace("forbidden hidden text", "[hidden text redacted]")
        for value in values
    ]
