from __future__ import annotations

from enum import StrEnum
from random import Random
from typing import Any, Callable

from pydantic import BaseModel, Field

from app.core.state_delta import apply_delta
from app.core.world_state import GameState, LocationState, PlayerState, WorldObjectState
from app.engine.advanced_modules import (
    AdvancedModuleId,
    CultivatorState,
    CultivationState,
    EconomySimState,
    HackableObjectState,
    HackingState,
    MarketRegionState,
    CommodityState,
    RecipeDefinition,
    CraftingState,
    SpellDefinition,
    CasterState,
    MagicState,
    SurvivalStatus,
    SurvivalTravelState,
    TravelRouteModuleState,
    advanced_module_default_states,
    economy_sim_tick,
    faction_war_tick,
    RegionConflictState,
    FactionWarState,
    resolve_craft_item,
    resolve_cultivation_action,
    resolve_hacking_action,
    resolve_magic_action,
    resolve_survival_action,
    resolve_tactical_action,
    start_tactical_encounter,
)


class ModulePlaytestScenarioType(StrEnum):
    TACTICAL_COMBAT_PATH = "tactical_combat_path"
    ECONOMY_MARKET_TICK_PATH = "economy_market_tick_path"
    FACTION_WAR_TICK_PATH = "faction_war_tick_path"
    MAGIC_CAST_PATH = "magic_cast_path"
    HACKING_TERMINAL_PATH = "hacking_terminal_path"
    CRAFTING_RECIPE_PATH = "crafting_recipe_path"
    DEDUCTION_CASE_PATH = "deduction_case_path"
    SURVIVAL_TRAVEL_PATH = "survival_travel_path"
    CULTIVATION_PROGRESS_PATH = "cultivation_progress_path"


class ModulePlaytestScenario(BaseModel):
    scenario_id: str
    scenario_type: ModulePlaytestScenarioType
    module_id: str
    seed: int = 0
    expected_event_tags: list[str] = Field(default_factory=list)
    forbidden_visible_text_patterns: list[str] = Field(default_factory=lambda: ["hidden_secret", "api_key", "authorization:"])


class ModulePlaytestReport(BaseModel):
    scenario_id: str
    module_id: str
    success: bool
    event_count: int = 0
    state_delta_count: int = 0
    hidden_leak_detected: bool = False
    save_load_stable: bool = False
    errors: list[str] = Field(default_factory=list)


def run_module_playtest_scenario(scenario: ModulePlaytestScenario) -> ModulePlaytestReport:
    state = _base_state()
    state.modules.update(advanced_module_default_states())
    runner = _SCENARIO_RUNNERS[scenario.scenario_type]
    errors: list[str] = []
    events = []
    deltas = []
    try:
        produced_deltas, produced_events = runner(state, Random(scenario.seed))
        deltas.extend(produced_deltas)
        events.extend(produced_events)
        for delta in produced_deltas:
            state = apply_delta(state, delta)
        reloaded = GameState.model_validate_json(state.model_dump_json())
        save_load_stable = reloaded.model_dump(mode="json") == state.model_dump(mode="json")
    except Exception as exc:
        errors.append(str(exc))
        save_load_stable = False
    visible_text = " ".join(event.visible_summary or "" for event in events).lower()
    hidden_leak = any(pattern.lower() in visible_text for pattern in scenario.forbidden_visible_text_patterns)
    if hidden_leak:
        errors.append("hidden leak pattern found in module playtest visible text")
    if not events:
        errors.append("module playtest did not record an Event")
    return ModulePlaytestReport(
        scenario_id=scenario.scenario_id,
        module_id=scenario.module_id,
        success=not errors,
        event_count=len(events),
        state_delta_count=len(deltas),
        hidden_leak_detected=hidden_leak,
        save_load_stable=save_load_stable,
        errors=errors,
    )


def run_all_module_playtests() -> list[ModulePlaytestReport]:
    return [run_module_playtest_scenario(scenario) for scenario in default_module_playtest_scenarios()]


def default_module_playtest_scenarios() -> list[ModulePlaytestScenario]:
    return [
        ModulePlaytestScenario(scenario_id="tactical-basic", scenario_type=ModulePlaytestScenarioType.TACTICAL_COMBAT_PATH, module_id=AdvancedModuleId.TACTICAL_COMBAT),
        ModulePlaytestScenario(scenario_id="economy-basic", scenario_type=ModulePlaytestScenarioType.ECONOMY_MARKET_TICK_PATH, module_id=AdvancedModuleId.ECONOMY_SIM),
        ModulePlaytestScenario(scenario_id="faction-basic", scenario_type=ModulePlaytestScenarioType.FACTION_WAR_TICK_PATH, module_id=AdvancedModuleId.FACTION_WAR),
        ModulePlaytestScenario(scenario_id="magic-basic", scenario_type=ModulePlaytestScenarioType.MAGIC_CAST_PATH, module_id=AdvancedModuleId.MAGIC),
        ModulePlaytestScenario(scenario_id="hacking-basic", scenario_type=ModulePlaytestScenarioType.HACKING_TERMINAL_PATH, module_id=AdvancedModuleId.HACKING),
        ModulePlaytestScenario(scenario_id="crafting-basic", scenario_type=ModulePlaytestScenarioType.CRAFTING_RECIPE_PATH, module_id=AdvancedModuleId.CRAFTING),
        ModulePlaytestScenario(scenario_id="deduction-basic", scenario_type=ModulePlaytestScenarioType.DEDUCTION_CASE_PATH, module_id=AdvancedModuleId.DEDUCTION),
        ModulePlaytestScenario(scenario_id="survival-basic", scenario_type=ModulePlaytestScenarioType.SURVIVAL_TRAVEL_PATH, module_id=AdvancedModuleId.SURVIVAL_TRAVEL),
        ModulePlaytestScenario(scenario_id="cultivation-basic", scenario_type=ModulePlaytestScenarioType.CULTIVATION_PROGRESS_PATH, module_id=AdvancedModuleId.CULTIVATION),
    ]


def _base_state() -> GameState:
    return GameState(
        world_id="module-playtest",
        player=PlayerState(location_id="start", inventory=["cyberdeck", "wood"]),
        locations={"start": LocationState(id="start", name="Start")},
        objects={"bench": WorldObjectState(id="bench", location_id="start", visible=True, tags=["workbench"])},
    )


def _run_tactical(state: GameState, rng: Random) -> tuple[list[Any], list[Any]]:
    deltas = start_tactical_encounter("enc1", ["player", "guard"])
    for delta in deltas:
        state = apply_delta(state, delta)
    result, event = resolve_tactical_action("take_cover", state, rng=rng)
    return [*deltas, *result.state_deltas], [event]


def _run_economy(state: GameState, rng: Random) -> tuple[list[Any], list[Any]]:
    state.modules[AdvancedModuleId.ECONOMY_SIM] = EconomySimState(markets={"market": MarketRegionState(region_id="market", commodities={"grain": CommodityState(commodity_id="grain", supply=20, demand=80)}, trade_route_status="blocked")}).model_dump(mode="json")
    deltas, event = economy_sim_tick(state)
    return deltas, [event]


def _run_faction(state: GameState, rng: Random) -> tuple[list[Any], list[Any]]:
    state.modules[AdvancedModuleId.FACTION_WAR] = FactionWarState(regions={"valley": RegionConflictState(region_id="valley", known_by_player=True)}).model_dump(mode="json")
    deltas, event = faction_war_tick(state)
    return deltas, [event]


def _run_magic(state: GameState, rng: Random) -> tuple[list[Any], list[Any]]:
    state.modules[AdvancedModuleId.MAGIC] = MagicState(casters={"player": CasterState(actor_id="player", mana=3, known_spell_ids=["spark"])}, spells={"spark": SpellDefinition(spell_id="spark", cost=1)}).model_dump(mode="json")
    result, event = resolve_magic_action("cast_spell", state, spell_id="spark")
    return result.state_deltas, [event]


def _run_hacking(state: GameState, rng: Random) -> tuple[list[Any], list[Any]]:
    state.modules[AdvancedModuleId.HACKING] = HackingState(hackables={"terminal": HackableObjectState(object_id="terminal", security_level=1)}).model_dump(mode="json")
    result, event = resolve_hacking_action("hack_terminal", state, target_id="terminal", rng=rng)
    return result.state_deltas, [event]


def _run_crafting(state: GameState, rng: Random) -> tuple[list[Any], list[Any]]:
    state.modules[AdvancedModuleId.CRAFTING] = CraftingState(recipes={"chair": RecipeDefinition(recipe_id="chair", input_items={"wood": 1}, output_items={"chair": 1}, required_workstation_tags=["workbench"])}).model_dump(mode="json")
    result, event = resolve_craft_item(state, "chair", rng=Random(1))
    return result.state_deltas, [event]


def _run_deduction(state: GameState, rng: Random) -> tuple[list[Any], list[Any]]:
    from app.engine.advanced_modules import resolve_deduction_action

    result, event = resolve_deduction_action("form_hypothesis", state, target_id="h1")
    return result.state_deltas, [event]


def _run_survival(state: GameState, rng: Random) -> tuple[list[Any], list[Any]]:
    state.modules[AdvancedModuleId.SURVIVAL_TRAVEL] = SurvivalTravelState(statuses={"player": SurvivalStatus()}, routes={"road": TravelRouteModuleState(route_id="road", from_location_id="start", to_location_id="out", time_cost=1, fatigue_cost=5, hidden_danger="hidden_secret")}).model_dump(mode="json")
    result, event = resolve_survival_action("travel_route", state, route_id="road", rng=rng)
    return result.state_deltas, [event]


def _run_cultivation(state: GameState, rng: Random) -> tuple[list[Any], list[Any]]:
    state.modules[AdvancedModuleId.CULTIVATION] = CultivationState(cultivators={"player": CultivatorState(actor_id="player", progress=0)}).model_dump(mode="json")
    result, event = resolve_cultivation_action("meditate", state)
    return result.state_deltas, [event]


_SCENARIO_RUNNERS: dict[ModulePlaytestScenarioType, Callable[[GameState, Random], tuple[list[Any], list[Any]]]] = {
    ModulePlaytestScenarioType.TACTICAL_COMBAT_PATH: _run_tactical,
    ModulePlaytestScenarioType.ECONOMY_MARKET_TICK_PATH: _run_economy,
    ModulePlaytestScenarioType.FACTION_WAR_TICK_PATH: _run_faction,
    ModulePlaytestScenarioType.MAGIC_CAST_PATH: _run_magic,
    ModulePlaytestScenarioType.HACKING_TERMINAL_PATH: _run_hacking,
    ModulePlaytestScenarioType.CRAFTING_RECIPE_PATH: _run_crafting,
    ModulePlaytestScenarioType.DEDUCTION_CASE_PATH: _run_deduction,
    ModulePlaytestScenarioType.SURVIVAL_TRAVEL_PATH: _run_survival,
    ModulePlaytestScenarioType.CULTIVATION_PROGRESS_PATH: _run_cultivation,
}
