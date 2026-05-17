import json
from pathlib import Path
from random import Random
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.db.repository import SQLiteSaveRepository, SaveRepositoryError
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.content.world_loader import WorldLoader
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.playtesting.agents import PlaytestingAgent, create_playtesting_agent
from app.playtesting.invariants import check_playtest_invariants
from app.playtesting.provider import PlaytestLLMProvider
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


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _canonical_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _canonical_json(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        items = [_canonical_json(item) for item in value]
        if all(not isinstance(item, dict | list) for item in items):
            return sorted(items, key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True))
        return items
    return value
