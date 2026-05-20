from __future__ import annotations

from enum import StrEnum
from random import Random
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.timeline_replay import replay_dry_run, state_checksum
from app.core.world_state import (
    CraftingStationState,
    FactState,
    FactVisibility,
    GameState,
    HackableState,
    HackingToolState,
    LocationState,
    MagicResourceState,
    NPCState,
    PlayerState,
    WorldObjectState,
)
from app.engine.actions.dsl import ActionCheck, ActionCheckType, ActionEffect, ActionEffectType, ActionStateDeltaTemplate
from app.engine.actions.schemas import SuccessLevel
from app.engine.rules.crafting import CraftingActionHandler, CraftingModuleConfig, RecipeDefinition
from app.engine.rules.hacking import HackingActionHandler
from app.engine.rules.magic import CastSpellActionHandler, MagicModuleConfig, SpellDefinition, SpellTargetType
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.session_store import build_visible_state


class GameplayModuleRegressionScenarioType(StrEnum):
    ACTION_SUCCESS = "action_success"
    ACTION_FAILURE = "action_failure"
    INVALID_TARGET = "invalid_target"
    HIDDEN_TARGET = "hidden_target"
    SAVE_LOAD = "save_load"
    REPLAY = "replay"
    QUALITY_GATE = "quality_gate"


class GameplayModuleRegressionScenario(BaseModel):
    id: str = Field(default_factory=lambda: f"gameplay-module-regression-{uuid4()}")
    scenario_type: GameplayModuleRegressionScenarioType
    module_id: str
    action_id: str
    input_sequence: list[str] = Field(default_factory=list)
    expected_result: str
    expected_deltas: list[str] = Field(default_factory=list)
    forbidden_visible_facts: list[str] = Field(default_factory=list)
    seed: int = 1


class GameplayModuleRegressionCaseResult(BaseModel):
    scenario_id: str
    module_id: str
    action_id: str
    scenario_type: GameplayModuleRegressionScenarioType
    passed: bool
    result: str
    delta_paths: list[str] = Field(default_factory=list)
    event_ids: list[str] = Field(default_factory=list)
    forbidden_visible_fact_hits: list[str] = Field(default_factory=list)
    save_load_passed: bool = True
    replay_passed: bool = True
    errors: list[str] = Field(default_factory=list)


class GameplayModuleRegressionReport(BaseModel):
    run_id: str = Field(default_factory=lambda: f"gameplay-module-regression-{uuid4()}")
    passed: bool
    provider_id: str = "local_stub"
    calls_real_llm: bool = False
    modifies_real_save: bool = False
    executes_module_code: bool = False
    case_results: list[GameplayModuleRegressionCaseResult] = Field(default_factory=list)
    summary: dict[str, int | bool | str] = Field(default_factory=dict)

    def model_dump_normal(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


def sample_gameplay_module_regression_scenarios() -> list[GameplayModuleRegressionScenario]:
    return [
        GameplayModuleRegressionScenario(
            id="magic-action-success",
            scenario_type=GameplayModuleRegressionScenarioType.ACTION_SUCCESS,
            module_id="magic",
            action_id="magic.cast_spell",
            input_sequence=["cast spark"],
            expected_result=SuccessLevel.SUCCESS.value,
            expected_deltas=["magic_resources.player.mana", "npcs.guard.hp"],
            seed=1,
        ),
        GameplayModuleRegressionScenario(
            id="hacking-action-failure",
            scenario_type=GameplayModuleRegressionScenarioType.ACTION_FAILURE,
            module_id="hacking",
            action_id="hacking.hack_terminal",
            input_sequence=["hack terminal"],
            expected_result=SuccessLevel.FAILURE.value,
            expected_deltas=["hackables.terminal.intrusion_trace", "hackables.terminal.alarm_level"],
            seed=1,
        ),
        GameplayModuleRegressionScenario(
            id="crafting-missing-material",
            scenario_type=GameplayModuleRegressionScenarioType.ACTION_FAILURE,
            module_id="crafting",
            action_id="crafting.craft_item",
            input_sequence=["craft chair"],
            expected_result=SuccessLevel.FAILURE.value,
            expected_deltas=[],
            seed=1,
        ),
        GameplayModuleRegressionScenario(
            id="hacking-hidden-target",
            scenario_type=GameplayModuleRegressionScenarioType.HIDDEN_TARGET,
            module_id="hacking",
            action_id="hacking.access_logs",
            input_sequence=["access logs"],
            expected_result=SuccessLevel.SUCCESS.value,
            expected_deltas=["player_visible_facts"],
            forbidden_visible_facts=["hidden_root_log", "Root key is buried under admin"],
            seed=1,
        ),
        GameplayModuleRegressionScenario(
            id="magic-save-load",
            scenario_type=GameplayModuleRegressionScenarioType.SAVE_LOAD,
            module_id="magic",
            action_id="magic.cast_spell",
            input_sequence=["cast spark"],
            expected_result=SuccessLevel.SUCCESS.value,
            expected_deltas=["magic_resources.player.mana"],
            seed=1,
        ),
        GameplayModuleRegressionScenario(
            id="magic-replay",
            scenario_type=GameplayModuleRegressionScenarioType.REPLAY,
            module_id="magic",
            action_id="magic.cast_spell",
            input_sequence=["cast spark"],
            expected_result=SuccessLevel.SUCCESS.value,
            expected_deltas=["magic_resources.player.mana"],
            seed=1,
        ),
    ]


def run_gameplay_module_regression(
    scenarios: list[GameplayModuleRegressionScenario] | None = None,
) -> GameplayModuleRegressionReport:
    active_scenarios = scenarios or sample_gameplay_module_regression_scenarios()
    results = [_run_scenario(scenario) for scenario in active_scenarios]
    passed = all(result.passed for result in results)
    return GameplayModuleRegressionReport(
        passed=passed,
        case_results=results,
        summary={
            "total": len(results),
            "passed": sum(1 for result in results if result.passed),
            "failed": sum(1 for result in results if not result.passed),
            "calls_real_llm": False,
            "modifies_real_save": False,
            "executes_module_code": False,
        },
    )


def _run_scenario(scenario: GameplayModuleRegressionScenario) -> GameplayModuleRegressionCaseResult:
    initial_state = _initial_state(scenario)
    state = initial_state.model_copy(deep=True)
    events: list[Event] = []
    all_delta_paths: list[str] = []
    errors: list[str] = []
    result_value = SuccessLevel.INVALID.value

    for raw_input in scenario.input_sequence or [_default_input(scenario)]:
        execution = _execute_action(scenario, raw_input, state)
        action_result = execution["action_result"]
        event = execution["event"]
        result_value = action_result.success_level.value
        events.append(event)
        all_delta_paths.extend(delta.path for delta in action_result.state_deltas)
        for delta in action_result.state_deltas:
            state = apply_delta(state, delta)

    if result_value != scenario.expected_result:
        errors.append(f"Expected result {scenario.expected_result}, got {result_value}.")
    missing_deltas = [
        path
        for path in scenario.expected_deltas
        if not any(delta_path == path or delta_path.startswith(f"{path}.") for delta_path in all_delta_paths)
    ]
    if missing_deltas:
        errors.append(f"Missing expected StateDelta paths: {', '.join(missing_deltas)}.")

    visible_payload = build_visible_state(state).model_dump_json()
    visible_event_payload = " ".join(
        " ".join([*[delta.path for delta in event.state_deltas], event.action_type, event.result])
        for event in events
        if event.visible_to_player
    )
    forbidden_hits = [
        fact
        for fact in scenario.forbidden_visible_facts
        if fact in visible_payload or fact in visible_event_payload
    ]
    if forbidden_hits:
        errors.append("Forbidden hidden content appeared in visible regression output.")

    save_load_passed = True
    if scenario.scenario_type == GameplayModuleRegressionScenarioType.SAVE_LOAD:
        restored = GameState.model_validate_json(state.model_dump_json())
        save_load_passed = state_checksum(restored) == state_checksum(state)
        if not save_load_passed:
            errors.append("Save/load roundtrip changed module state.")

    replay_passed = True
    if scenario.scenario_type == GameplayModuleRegressionScenarioType.REPLAY:
        first = replay_dry_run(initial_state, events)
        second = replay_dry_run(initial_state, events)
        replay_passed = (
            first.final_state_checksum == second.final_state_checksum
            and not first.invariant_violations
            and not second.invariant_violations
        )
        if not replay_passed:
            errors.append("Replay dry-run was not deterministic or violated invariants.")

    return GameplayModuleRegressionCaseResult(
        scenario_id=scenario.id,
        module_id=scenario.module_id,
        action_id=scenario.action_id,
        scenario_type=scenario.scenario_type,
        passed=not errors,
        result=result_value,
        delta_paths=sorted(set(all_delta_paths)),
        event_ids=[event.event_id for event in events],
        forbidden_visible_fact_hits=forbidden_hits,
        save_load_passed=save_load_passed,
        replay_passed=replay_passed,
        errors=errors,
    )


def _execute_action(
    scenario: GameplayModuleRegressionScenario,
    raw_input: str,
    state: GameState,
) -> dict[str, Any]:
    intent = PlayerIntent(
        action_type=PlayerActionType.UNKNOWN,
        raw_text=raw_input,
        confidence=1.0,
        requires_clarification=False,
        target_id=_target_for_scenario(scenario),
    )
    rng = Random(scenario.seed)
    if scenario.module_id == "magic":
        execution = _magic_handler(scenario).resolve_with_event(intent, state, rng)
        return {"action_result": execution.action_result, "event": execution.event}
    if scenario.module_id == "hacking":
        execution = HackingActionHandler().resolve_with_event(intent, state, rng)
        return {"action_result": execution.action_result, "event": execution.event}
    if scenario.module_id == "crafting":
        execution = _crafting_handler().resolve_with_event(intent, state, rng)
        return {"action_result": execution.action_result, "event": execution.event}
    raise ValueError(f"Unsupported gameplay regression module: {scenario.module_id}")


def _initial_state(scenario: GameplayModuleRegressionScenario) -> GameState:
    if scenario.module_id == "magic":
        return _magic_state()
    if scenario.module_id == "hacking":
        return _hacking_state(difficulty=40 if scenario.scenario_type == GameplayModuleRegressionScenarioType.ACTION_FAILURE else 10)
    if scenario.module_id == "crafting":
        return _crafting_state(include_wood=scenario.scenario_type != GameplayModuleRegressionScenarioType.ACTION_FAILURE)
    raise ValueError(f"Unsupported gameplay regression module: {scenario.module_id}")


def _magic_state() -> GameState:
    return GameState(
        world_id="gameplay-module-regression",
        turn=3,
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Town Square")},
        npcs={"guard": NPCState(id="guard", location_id="square", visible=True)},
        magic_resources={"player": MagicResourceState(mana=5, max_mana=10, focus=2, max_focus=2)},
    )


def _hacking_state(*, difficulty: int) -> GameState:
    return GameState(
        world_id="gameplay-module-regression",
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
                linked_fact_ids=["public_log", "hidden_root_log"],
            )
        },
        hacking_tools={"deck": HackingToolState(id="deck", owner_id="player", power=10)},
        facts={
            "public_log": FactState(id="public_log", text="The access log names a courier.", visibility=FactVisibility.DISCOVERABLE),
            "hidden_root_log": FactState(id="hidden_root_log", text="Root key is buried under admin.", visibility=FactVisibility.HIDDEN),
        },
    )


def _crafting_state(*, include_wood: bool) -> GameState:
    objects = {
        "hammer": WorldObjectState(id="hammer", owner_id="player", portable=True, tags=["tool"]),
        "plank": WorldObjectState(id="plank", owner_id="player", portable=True),
    }
    if include_wood:
        objects["wood"] = WorldObjectState(id="wood", owner_id="player", portable=True)
    return GameState(
        world_id="gameplay-module-regression",
        turn=4,
        player=PlayerState(location_id="workshop"),
        locations={"workshop": LocationState(id="workshop", name="Workshop")},
        objects=objects,
        crafting_stations={"bench": CraftingStationState(id="bench", location_id="workshop", tags=["workbench"])},
    )


def _magic_handler(scenario: GameplayModuleRegressionScenario) -> CastSpellActionHandler:
    spell = SpellDefinition(
        id="spark",
        name="Spark",
        school="fire",
        cost=2,
        target_types=[SpellTargetType.NPC],
        checks=[ActionCheck(check_type=ActionCheckType.FIXED_SUCCESS)],
        effects=[
            ActionEffect(
                effect_type=ActionEffectType.STATE_DELTA_TEMPLATE,
                state_delta_template=ActionStateDeltaTemplate(
                    operation=StateDeltaOperation.INC,
                    path="npcs.{target_id}.hp",
                    value=-2,
                    reason="Spell damage.",
                ),
            )
        ],
        aliases=["cast spark", "spark"],
        hidden_effect=scenario.scenario_type == GameplayModuleRegressionScenarioType.HIDDEN_TARGET,
    )
    return CastSpellActionHandler(MagicModuleConfig(spells={spell.id: spell}))


def _crafting_handler() -> CraftingActionHandler:
    recipe = RecipeDefinition(
        id="make_chair",
        output_item_id="chair",
        required_items=["hammer", "wood"],
        consumed_items=["wood"],
        required_station_tags=["workbench"],
        time_cost=30,
        aliases=["craft chair"],
    )
    return CraftingActionHandler(CraftingModuleConfig(recipes={recipe.id: recipe}))


def _target_for_scenario(scenario: GameplayModuleRegressionScenario) -> str | None:
    if scenario.scenario_type == GameplayModuleRegressionScenarioType.INVALID_TARGET:
        return "missing_target"
    if scenario.module_id == "magic":
        return "guard"
    if scenario.module_id == "hacking":
        return "terminal"
    return None


def _default_input(scenario: GameplayModuleRegressionScenario) -> str:
    if scenario.module_id == "magic":
        return "cast spark"
    if scenario.module_id == "hacking":
        return "hack terminal"
    if scenario.module_id == "crafting":
        return "craft chair"
    return scenario.action_id
