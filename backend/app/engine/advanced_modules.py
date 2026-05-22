from __future__ import annotations

from enum import StrEnum
from random import Random
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactVisibility, GameState
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.module_state import module_state_path, validate_module_state_delta


ECONOMY_PRICE_INDEX_MAX = 10.0
MAGIC_RESOURCE_MAX = 100


class AdvancedModuleId(StrEnum):
    TACTICAL_COMBAT = "tactical_combat"
    ECONOMY_SIM = "economy_sim"
    FACTION_WAR = "faction_war"
    MAGIC = "magic"
    HACKING = "hacking"
    CRAFTING = "crafting"
    DEDUCTION = "deduction"
    SURVIVAL_TRAVEL = "survival_travel"
    CULTIVATION = "cultivation"


class CombatantTacticalState(BaseModel):
    actor_id: str
    action_points: int = Field(default=2, ge=0)
    position_band: str = "near"
    range_band: str = "near"
    cover_level: int = Field(default=0, ge=0, le=5)
    stance: str = "neutral"
    status_effects: list[str] = Field(default_factory=list)
    hidden: bool = False


class CombatEncounter(BaseModel):
    encounter_id: str
    combatant_ids: list[str] = Field(default_factory=list)
    turn_order: list[str] = Field(default_factory=list)
    active_combatant_id: str | None = None
    round_index: int = Field(default=1, ge=1)
    public_combat: bool = True


class TacticalCombatState(BaseModel):
    encounters: dict[str, CombatEncounter] = Field(default_factory=dict)
    combatants: dict[str, CombatantTacticalState] = Field(default_factory=dict)


def tactical_combat_default_state() -> dict[str, Any]:
    return TacticalCombatState().model_dump(mode="json")


def start_tactical_encounter(encounter_id: str, combatant_ids: list[str], *, hidden_combatants: set[str] | None = None) -> list[StateDelta]:
    hidden = hidden_combatants or set()
    order = sorted(combatant_ids)
    encounter = CombatEncounter(
        encounter_id=encounter_id,
        combatant_ids=combatant_ids,
        turn_order=order,
        active_combatant_id=order[0] if order else None,
    )
    deltas = [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=module_state_path(AdvancedModuleId.TACTICAL_COMBAT, "encounters", encounter_id),
            value=encounter.model_dump(mode="json"),
            reason="Started tactical encounter.",
            metadata={"module_id": AdvancedModuleId.TACTICAL_COMBAT},
        )
    ]
    for actor_id in combatant_ids:
        combatant = CombatantTacticalState(actor_id=actor_id, hidden=actor_id in hidden)
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=module_state_path(AdvancedModuleId.TACTICAL_COMBAT, "combatants", actor_id),
                value=combatant.model_dump(mode="json"),
                reason="Initialized tactical combatant state.",
                metadata={"module_id": AdvancedModuleId.TACTICAL_COMBAT},
            )
        )
    return deltas


def tactical_visible_summary(state: GameState) -> dict[str, Any]:
    tactical = state.modules.get(AdvancedModuleId.TACTICAL_COMBAT, {})
    combatants = tactical.get("combatants", {}) if isinstance(tactical, dict) else {}
    return {
        "combatants": {
            actor_id: {key: value for key, value in data.items() if key != "hidden"}
            for actor_id, data in combatants.items()
            if isinstance(data, dict) and not data.get("hidden")
        }
    }


def resolve_tactical_action(action_id: str, state: GameState, *, actor_id: str = "player", target_id: str | None = None, rng: Random | None = None) -> tuple[ActionResult, Event]:
    rng = rng or Random(0)
    tactical = state.modules.get(AdvancedModuleId.TACTICAL_COMBAT, {})
    combatant = tactical.get("combatants", {}).get(actor_id) if isinstance(tactical, dict) else None
    encounter = next(iter(tactical.get("encounters", {}).values()), None) if isinstance(tactical, dict) else None
    if not combatant or not encounter:
        return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "No active tactical encounter.", [])
    if encounter.get("active_combatant_id") != actor_id:
        return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Actor is not the active tactical combatant.", [])
    if combatant.get("action_points", 0) <= 0:
        return _module_action_with_event(action_id, state, SuccessLevel.FAILURE, "No tactical action points remain.", [])
    deltas = [
        StateDelta(
            operation=StateDeltaOperation.INC,
            path=module_state_path(AdvancedModuleId.TACTICAL_COMBAT, "combatants", actor_id, "action_points"),
            value=-1,
            reason=f"{action_id} consumed tactical action points.",
            metadata={"module_id": AdvancedModuleId.TACTICAL_COMBAT},
        )
    ]
    if action_id == "tactical_move":
        deltas.append(_set_module_value(AdvancedModuleId.TACTICAL_COMBAT, f"combatants.{actor_id}.range_band", target_id or "mid"))
    elif action_id == "take_cover":
        deltas.append(_set_module_value(AdvancedModuleId.TACTICAL_COMBAT, f"combatants.{actor_id}.cover_level", min(5, int(combatant.get("cover_level", 0)) + 1)))
    elif action_id == "aim":
        deltas.append(_add_module_value(AdvancedModuleId.TACTICAL_COMBAT, f"combatants.{actor_id}.status_effects", "aiming"))
    elif action_id == "strike":
        score = 5 + int(combatant.get("cover_level", 0)) + rng.randint(0, 3)
        result = "hit" if score >= 6 else "miss"
        deltas.append(_set_module_value(AdvancedModuleId.TACTICAL_COMBAT, f"combatants.{actor_id}.last_strike_result", result))
    elif action_id in {"defend", "guard"}:
        deltas.append(_add_module_value(AdvancedModuleId.TACTICAL_COMBAT, f"combatants.{actor_id}.status_effects", action_id))
    elif action_id == "flee_tactical":
        success = rng.randint(0, 9) >= 3
        deltas.append(_set_module_value(AdvancedModuleId.TACTICAL_COMBAT, f"combatants.{actor_id}.stance", "fleeing" if success else "pressed"))
    else:
        return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Unsupported tactical action.", [])
    return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, f"{action_id} resolved by tactical rules.", deltas)


class CommodityState(BaseModel):
    commodity_id: str
    supply: int = Field(default=50, ge=0)
    demand: int = Field(default=50, ge=0)
    price_index: float = Field(default=1.0, ge=0)
    scarcity: int = Field(default=0, ge=0)


class MarketRegionState(BaseModel):
    region_id: str
    commodities: dict[str, CommodityState] = Field(default_factory=dict)
    trade_route_status: str = "open"
    last_updated_turn: int = Field(default=0, ge=0)
    hidden: bool = False
    known_by_player: bool = True


class EconomySimState(BaseModel):
    markets: dict[str, MarketRegionState] = Field(default_factory=dict)


def economy_sim_default_state() -> dict[str, Any]:
    return EconomySimState().model_dump(mode="json")


def economy_price_modifier(state: GameState, region_id: str, commodity_id: str) -> float | None:
    market = state.modules.get(AdvancedModuleId.ECONOMY_SIM, {}).get("markets", {}).get(region_id)
    if not market:
        return None
    commodity = market.get("commodities", {}).get(commodity_id)
    return float(commodity.get("price_index")) if commodity else None


def economy_sim_tick(state: GameState, *, turn: int | None = None) -> tuple[list[StateDelta], Event]:
    turn = state.turn if turn is None else turn
    deltas: list[StateDelta] = []
    markets = state.modules.get(AdvancedModuleId.ECONOMY_SIM, {}).get("markets", {})
    for region_id, market in markets.items():
        route_blocked = market.get("trade_route_status") == "blocked"
        for commodity_id, commodity in market.get("commodities", {}).items():
            supply = int(commodity.get("supply", 50))
            demand = int(commodity.get("demand", 50))
            scarcity = max(0, demand - supply + (20 if route_blocked else 0))
            price = min(ECONOMY_PRICE_INDEX_MAX, max(0.1, round(1.0 + scarcity / 100, 2)))
            deltas.extend(
                [
                    _set_module_value(AdvancedModuleId.ECONOMY_SIM, f"markets.{region_id}.commodities.{commodity_id}.scarcity", scarcity),
                    _set_module_value(AdvancedModuleId.ECONOMY_SIM, f"markets.{region_id}.commodities.{commodity_id}.price_index", price),
                    _set_module_value(AdvancedModuleId.ECONOMY_SIM, f"markets.{region_id}.last_updated_turn", turn),
                ]
            )
    return deltas, _module_event("economy_sim.tick", state, deltas, "Economy simulation tick resolved.")


class RegionConflictState(BaseModel):
    region_id: str
    controlling_faction_id: str | None = None
    contested_factions: list[str] = Field(default_factory=list)
    control_score: int = Field(default=50, ge=0, le=100)
    front_pressure: int = Field(default=0, ge=0, le=100)
    morale: int = Field(default=50, ge=0, le=100)
    supply_level: int = Field(default=50, ge=0, le=100)
    war_phase: str = "quiet"
    known_by_player: bool = False


class FactionWarResourceState(BaseModel):
    faction_id: str
    manpower: int = Field(default=0, ge=0)
    supplies: int = Field(default=0, ge=0)


class FactionWarState(BaseModel):
    regions: dict[str, RegionConflictState] = Field(default_factory=dict)
    resources: dict[str, FactionWarResourceState] = Field(default_factory=dict)


def faction_war_default_state() -> dict[str, Any]:
    return FactionWarState().model_dump(mode="json")


def faction_war_visible_summary(state: GameState) -> dict[str, Any]:
    regions = state.modules.get(AdvancedModuleId.FACTION_WAR, {}).get("regions", {})
    return {"regions": {region_id: data for region_id, data in regions.items() if data.get("known_by_player")}}


def faction_war_tick(state: GameState) -> tuple[list[StateDelta], Event]:
    deltas: list[StateDelta] = []
    regions = state.modules.get(AdvancedModuleId.FACTION_WAR, {}).get("regions", {})
    for region_id, region in regions.items():
        rumor_pressure = sum(1 for rumor in state.rumors.values() if region_id in rumor.tags and rumor.known_by_player)
        route_penalty = _economy_route_penalty(state, region_id)
        morale = max(0, min(100, int(region.get("morale", 50)) + rumor_pressure - route_penalty))
        supply = max(0, min(100, int(region.get("supply_level", 50)) - route_penalty))
        pressure = max(0, min(100, int(region.get("front_pressure", 0)) + (1 if supply < 40 else 0)))
        deltas.extend(
            [
                _set_module_value(AdvancedModuleId.FACTION_WAR, f"regions.{region_id}.morale", morale),
                _set_module_value(AdvancedModuleId.FACTION_WAR, f"regions.{region_id}.supply_level", supply),
                _set_module_value(AdvancedModuleId.FACTION_WAR, f"regions.{region_id}.front_pressure", pressure),
            ]
        )
    return deltas, _module_event("faction_war.tick", state, deltas, "Faction war regional conflict tick resolved.")


class SpellDefinition(BaseModel):
    spell_id: str
    school: str = "general"
    cost: int = Field(default=1, ge=0)
    target_types: list[str] = Field(default_factory=lambda: ["actor"])
    range_band: str = "near"
    effects: list[dict[str, Any]] = Field(default_factory=list)
    visibility_policy: str = "public"
    illegal_in_public: bool = False


class CasterState(BaseModel):
    actor_id: str
    mana: int = Field(default=0, ge=0)
    focus: int = Field(default=0, ge=0)
    known_spell_ids: list[str] = Field(default_factory=list)
    magical_status_effects: list[str] = Field(default_factory=list)


class MagicState(BaseModel):
    casters: dict[str, CasterState] = Field(default_factory=dict)
    spells: dict[str, SpellDefinition] = Field(default_factory=dict)


def magic_default_state() -> dict[str, Any]:
    return MagicState().model_dump(mode="json")


def resolve_magic_action(action_id: str, state: GameState, *, actor_id: str = "player", spell_id: str | None = None, target_id: str | None = None) -> tuple[ActionResult, Event]:
    magic = state.modules.get(AdvancedModuleId.MAGIC, {})
    caster = magic.get("casters", {}).get(actor_id)
    if action_id == "inspect_magic":
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Visible magical traces inspected.", [])
    if action_id == "rest_focus":
        delta = _set_module_value(AdvancedModuleId.MAGIC, f"casters.{actor_id}.focus", int((caster or {}).get("focus", 0)) + 1)
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Focus restored by rule.", [delta])
    if not caster:
        return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Actor has no caster state.", [])
    if action_id == "prepare_spell":
        delta = _add_module_value(AdvancedModuleId.MAGIC, f"casters.{actor_id}.magical_status_effects", "prepared")
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Spell prepared.", [delta])
    spell = magic.get("spells", {}).get(spell_id or "")
    if action_id != "cast_spell" or not spell:
        return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Unknown spell action or spell.", [])
    if spell_id not in caster.get("known_spell_ids", []):
        return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Actor does not know that spell.", [])
    if int(caster.get("mana", 0)) < int(spell.get("cost", 0)):
        return _module_action_with_event(action_id, state, SuccessLevel.FAILURE, "Not enough mana.", [])
    effect_deltas: list[StateDelta] = []
    for effect in spell.get("effects", []):
        effect_delta = _magic_effect_delta(effect)
        if effect_delta is None:
            return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Spell effect path or value is not allowed.", [])
        effect_deltas.append(effect_delta)
    deltas = [_set_module_value(AdvancedModuleId.MAGIC, f"casters.{actor_id}.mana", int(caster.get("mana", 0)) - int(spell.get("cost", 0))), *effect_deltas]
    if spell.get("illegal_in_public"):
        deltas.append(StateDelta(operation=StateDeltaOperation.SET, path="flags.public_illegal_magic_witnessed", value=True, reason="Public illegal magic consequence proposal.", metadata={"module_id": AdvancedModuleId.MAGIC}))
    return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Spell resolved by local magic rules.", deltas, target_id=target_id)


class HackableObjectState(BaseModel):
    object_id: str
    security_level: int = Field(default=1, ge=0)
    access_state: str = "locked"
    trace_level: int = Field(default=0, ge=0)
    known_log_ids: list[str] = Field(default_factory=list)
    locked_functions: list[str] = Field(default_factory=list)
    hidden_log_ids: list[str] = Field(default_factory=list)


class DigitalAccessState(BaseModel):
    actor_id: str
    object_id: str
    access_level: int = Field(default=0, ge=0)


class HackingState(BaseModel):
    hackables: dict[str, HackableObjectState] = Field(default_factory=dict)
    access: dict[str, DigitalAccessState] = Field(default_factory=dict)


def hacking_default_state() -> dict[str, Any]:
    return HackingState().model_dump(mode="json")


def resolve_hacking_action(action_id: str, state: GameState, *, actor_id: str = "player", target_id: str | None = None, rng: Random | None = None) -> tuple[ActionResult, Event]:
    rng = rng or Random(0)
    target_id = target_id or ""
    hacking = state.modules.get(AdvancedModuleId.HACKING, {})
    target = hacking.get("hackables", {}).get(target_id)
    if not target:
        return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Target is not hackable.", [])
    if action_id == "scan_terminal":
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Terminal scan returned safe metadata.", [])
    if action_id == "extract_logs":
        visible_logs = [log_id for log_id in target.get("known_log_ids", []) if log_id not in target.get("hidden_log_ids", [])]
        deltas = [_set_module_value(AdvancedModuleId.HACKING, f"hackables.{target_id}.last_visible_logs", visible_logs)]
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Visible digital logs extracted.", deltas)
    if action_id == "erase_trace":
        level = max(0, int(target.get("trace_level", 0)) - 1)
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Trace reduced by local rule.", [_set_module_value(AdvancedModuleId.HACKING, f"hackables.{target_id}.trace_level", level)])
    if action_id == "disable_lock":
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "In-world lock disabled.", [_set_module_value(AdvancedModuleId.HACKING, f"hackables.{target_id}.access_state", "disabled")])
    score = rng.randint(1, 10) + (2 if "cyberdeck" in state.player.inventory else 0)
    if score >= int(target.get("security_level", 1)):
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Hack succeeded deterministically.", [_set_module_value(AdvancedModuleId.HACKING, f"hackables.{target_id}.access_state", "access_granted")])
    return _module_action_with_event(action_id, state, SuccessLevel.FAILURE, "Hack failed and trace increased.", [_set_module_value(AdvancedModuleId.HACKING, f"hackables.{target_id}.trace_level", int(target.get("trace_level", 0)) + 1)])


class RecipeDefinition(BaseModel):
    recipe_id: str
    input_items: dict[str, int] = Field(default_factory=dict)
    output_items: dict[str, int] = Field(default_factory=dict)
    required_workstation_tags: list[str] = Field(default_factory=list)
    required_skill: str | None = None
    time_cost: int = Field(default=0, ge=0)
    failure_outcomes: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_recipe_economy(self) -> "RecipeDefinition":
        if not self.output_items:
            raise ValueError("crafting recipe must produce at least one output item")
        for item_id, count in {**self.input_items, **self.output_items}.items():
            if int(count) <= 0:
                raise ValueError(f"crafting recipe item count must be positive: {item_id}")
        if not self.input_items:
            raise ValueError("crafting recipe with outputs requires at least one input item")
        for item_id, output_count in self.output_items.items():
            input_count = int(self.input_items.get(item_id, 0))
            if input_count and int(output_count) > input_count:
                raise ValueError(f"crafting recipe cannot increase same-item count: {item_id}")
        return self


class CraftingJob(BaseModel):
    job_id: str
    recipe_id: str
    actor_id: str = "player"
    remaining_time: int = Field(default=0, ge=0)
    status: str = "draft"


class CraftingState(BaseModel):
    recipes: dict[str, RecipeDefinition] = Field(default_factory=dict)
    jobs: dict[str, CraftingJob] = Field(default_factory=dict)


def crafting_default_state() -> dict[str, Any]:
    return CraftingState().model_dump(mode="json")


def resolve_craft_item(state: GameState, recipe_id: str, *, actor_id: str = "player", rng: Random | None = None) -> tuple[ActionResult, Event]:
    rng = rng or Random(0)
    recipe = state.modules.get(AdvancedModuleId.CRAFTING, {}).get("recipes", {}).get(recipe_id)
    if not recipe:
        return _module_action_with_event("craft_item", state, SuccessLevel.INVALID, "Recipe not found.", [])
    inventory = list(state.player.inventory)
    for item_id, count in recipe.get("input_items", {}).items():
        if inventory.count(item_id) < int(count):
            return _module_action_with_event("craft_item", state, SuccessLevel.FAILURE, "Missing required material.", [])
    if recipe.get("required_workstation_tags"):
        if not any(set(recipe["required_workstation_tags"]).intersection(obj.tags) for obj in state.objects.values() if obj.location_id == state.player.location_id):
            return _module_action_with_event("craft_item", state, SuccessLevel.FAILURE, "Missing required workstation.", [])
    deltas: list[StateDelta] = []
    for item_id, count in recipe.get("input_items", {}).items():
        for _ in range(int(count)):
            deltas.append(StateDelta(operation=StateDeltaOperation.REMOVE, path="player.inventory", value=item_id, reason="Crafting consumed material.", metadata={"module_id": AdvancedModuleId.CRAFTING}))
    if rng.randint(0, 9) < 8:
        for item_id, count in recipe.get("output_items", {}).items():
            for _ in range(int(count)):
                deltas.append(StateDelta(operation=StateDeltaOperation.ADD, path="player.inventory", value=item_id, reason="Crafting produced item.", metadata={"module_id": AdvancedModuleId.CRAFTING}))
        level = SuccessLevel.SUCCESS
        reason = "Crafting succeeded deterministically."
    else:
        level = SuccessLevel.FAILURE
        reason = "Crafting failed deterministically."
    return _module_action_with_event("craft_item", state, level, reason, deltas)


class EvidenceRecord(BaseModel):
    evidence_id: str
    fact_id: str | None = None
    discovered: bool = False
    hidden: bool = False


class ClaimState(BaseModel):
    claim_id: str
    speaker_id: str
    fact_ids: list[str] = Field(default_factory=list)
    contradiction_ids: list[str] = Field(default_factory=list)
    known_to_player: bool = False


class HypothesisRecord(BaseModel):
    hypothesis_id: str
    evidence_ids: list[str] = Field(default_factory=list)
    status: str = "draft"


class DeductionState(BaseModel):
    evidence: dict[str, EvidenceRecord] = Field(default_factory=dict)
    claims: dict[str, ClaimState] = Field(default_factory=dict)
    hypotheses: dict[str, HypothesisRecord] = Field(default_factory=dict)


def deduction_default_state() -> dict[str, Any]:
    return DeductionState().model_dump(mode="json")


def resolve_deduction_action(action_id: str, state: GameState, *, target_id: str | None = None) -> tuple[ActionResult, Event]:
    data = state.modules.get(AdvancedModuleId.DEDUCTION, {})
    if action_id == "inspect_evidence":
        evidence = data.get("evidence", {}).get(target_id or "")
        if not evidence or evidence.get("hidden"):
            return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Evidence is not visible.", [])
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Evidence discovered.", [_set_module_value(AdvancedModuleId.DEDUCTION, f"evidence.{target_id}.discovered", True)])
    if action_id == "compare_claims":
        known = [claim for claim in data.get("claims", {}).values() if claim.get("known_to_player")]
        contradictions = [cid for claim in known for cid in claim.get("contradiction_ids", [])]
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Known claims compared.", [_set_module_value(AdvancedModuleId.DEDUCTION, "last_contradictions", contradictions)])
    if action_id == "form_hypothesis":
        hid = target_id or "hypothesis_player"
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Hypothesis drafted; it is not a world fact.", [_set_module_value(AdvancedModuleId.DEDUCTION, f"hypotheses.{hid}", HypothesisRecord(hypothesis_id=hid).model_dump(mode="json"))])
    if action_id == "test_hypothesis":
        known_fact_ids = {fact.id for fact in state.facts.values() if fact.visibility == FactVisibility.PUBLIC or "player" in fact.known_by}
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Hypothesis tested against known facts only.", [_set_module_value(AdvancedModuleId.DEDUCTION, "last_known_fact_count", len(known_fact_ids))])
    return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Unknown deduction action.", [])


class SurvivalStatus(BaseModel):
    actor_id: str = "player"
    fatigue: int = Field(default=0, ge=0, le=100)
    hunger: int = Field(default=0, ge=0, le=100)
    thirst: int = Field(default=0, ge=0, le=100)


class TravelRouteModuleState(BaseModel):
    route_id: str
    from_location_id: str
    to_location_id: str
    time_cost: int = Field(default=0, ge=0)
    fatigue_cost: int = Field(default=0, ge=0)
    risk_level: int = Field(default=0, ge=0)
    hidden_danger: str | None = None


class SurvivalTravelState(BaseModel):
    statuses: dict[str, SurvivalStatus] = Field(default_factory=dict)
    routes: dict[str, TravelRouteModuleState] = Field(default_factory=dict)


def survival_travel_default_state() -> dict[str, Any]:
    return SurvivalTravelState().model_dump(mode="json")


def resolve_survival_action(action_id: str, state: GameState, *, route_id: str | None = None, rng: Random | None = None) -> tuple[ActionResult, Event]:
    rng = rng or Random(0)
    data = state.modules.get(AdvancedModuleId.SURVIVAL_TRAVEL, {})
    status = data.get("statuses", {}).get("player", {"fatigue": 0, "hunger": 0, "thirst": 0})
    deltas: list[StateDelta] = []
    if action_id == "travel_route":
        route = data.get("routes", {}).get(route_id or "")
        if not route:
            return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Travel route not found.", [])
        deltas.extend([
            StateDelta(operation=StateDeltaOperation.INC, path="turn", value=max(1, int(route.get("time_cost", 1))), reason="Travel consumed time.", metadata={"module_id": AdvancedModuleId.SURVIVAL_TRAVEL}),
            _set_module_value(AdvancedModuleId.SURVIVAL_TRAVEL, "statuses.player.fatigue", min(100, int(status.get("fatigue", 0)) + int(route.get("fatigue_cost", 0)))),
        ])
        if rng.randint(0, 99) < int(route.get("risk_level", 0)):
            deltas.append(_set_module_value(AdvancedModuleId.SURVIVAL_TRAVEL, "last_travel_risk_triggered", True))
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Travel resolved by route rules.", deltas)
    if action_id in {"make_camp", "rest_travel"}:
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Travel rest reduced fatigue.", [_set_module_value(AdvancedModuleId.SURVIVAL_TRAVEL, "statuses.player.fatigue", max(0, int(status.get("fatigue", 0)) - 20))])
    if action_id == "forage":
        success = rng.randint(0, 9) >= 3
        if success:
            deltas.append(StateDelta(operation=StateDeltaOperation.ADD, path="player.inventory", value="supplies", reason="Forage found supplies.", metadata={"module_id": AdvancedModuleId.SURVIVAL_TRAVEL}))
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS if success else SuccessLevel.FAILURE, "Forage resolved deterministically.", deltas)
    return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Unknown survival action.", [])


class TechniqueDefinition(BaseModel):
    technique_id: str
    realm_required: str = "mortal"
    progress_gain: int = Field(default=1, ge=0)
    hidden: bool = False


class BreakthroughRule(BaseModel):
    from_realm: str
    to_realm: str
    required_progress: int = Field(default=100, ge=0)
    difficulty: int = Field(default=5, ge=0)


class CultivatorState(BaseModel):
    actor_id: str = "player"
    realm: str = "mortal"
    stage: int = Field(default=1, ge=1)
    progress: int = Field(default=0, ge=0)
    qi: int = Field(default=0, ge=0)
    known_technique_ids: list[str] = Field(default_factory=list)
    status_effects: list[str] = Field(default_factory=list)


class CultivationState(BaseModel):
    cultivators: dict[str, CultivatorState] = Field(default_factory=dict)
    techniques: dict[str, TechniqueDefinition] = Field(default_factory=dict)
    breakthrough_rules: list[BreakthroughRule] = Field(default_factory=list)


def cultivation_default_state() -> dict[str, Any]:
    return CultivationState().model_dump(mode="json")


def resolve_cultivation_action(action_id: str, state: GameState, *, actor_id: str = "player", technique_id: str | None = None, rng: Random | None = None) -> tuple[ActionResult, Event]:
    rng = rng or Random(0)
    data = state.modules.get(AdvancedModuleId.CULTIVATION, {})
    cultivator = data.get("cultivators", {}).get(actor_id)
    if not cultivator:
        return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Actor has no cultivation state.", [])
    if action_id == "meditate":
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Meditation increased cultivation progress.", [_set_module_value(AdvancedModuleId.CULTIVATION, f"cultivators.{actor_id}.progress", int(cultivator.get("progress", 0)) + 5)])
    if action_id == "practice_technique":
        technique = data.get("techniques", {}).get(technique_id or "")
        if not technique or technique.get("hidden") or technique_id not in cultivator.get("known_technique_ids", []):
            return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Technique is not known.", [])
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Technique practice increased progress.", [_set_module_value(AdvancedModuleId.CULTIVATION, f"cultivators.{actor_id}.progress", int(cultivator.get("progress", 0)) + int(technique.get("progress_gain", 1)))])
    if action_id == "consume_pill":
        return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Pill modifier applied.", [_add_module_value(AdvancedModuleId.CULTIVATION, f"cultivators.{actor_id}.status_effects", "pill_modifier")])
    if action_id == "attempt_breakthrough":
        rule = next((item for item in data.get("breakthrough_rules", []) if item.get("from_realm") == cultivator.get("realm")), None)
        if not rule or int(cultivator.get("progress", 0)) < int(rule.get("required_progress", 100)):
            return _module_action_with_event(action_id, state, SuccessLevel.FAILURE, "Breakthrough requirements are not met.", [])
        success = rng.randint(0, 9) >= int(rule.get("difficulty", 5))
        if success:
            deltas = [_set_module_value(AdvancedModuleId.CULTIVATION, f"cultivators.{actor_id}.realm", rule.get("to_realm")), _set_module_value(AdvancedModuleId.CULTIVATION, f"cultivators.{actor_id}.progress", 0)]
            return _module_action_with_event(action_id, state, SuccessLevel.SUCCESS, "Breakthrough succeeded by seeded rule.", deltas)
        return _module_action_with_event(action_id, state, SuccessLevel.FAILURE, "Breakthrough failed with backlash.", [_add_module_value(AdvancedModuleId.CULTIVATION, f"cultivators.{actor_id}.status_effects", "backlash")])
    return _module_action_with_event(action_id, state, SuccessLevel.INVALID, "Unknown cultivation action.", [])


def advanced_module_default_states() -> dict[str, dict[str, Any]]:
    return {
        AdvancedModuleId.TACTICAL_COMBAT: tactical_combat_default_state(),
        AdvancedModuleId.ECONOMY_SIM: economy_sim_default_state(),
        AdvancedModuleId.FACTION_WAR: faction_war_default_state(),
        AdvancedModuleId.MAGIC: magic_default_state(),
        AdvancedModuleId.HACKING: hacking_default_state(),
        AdvancedModuleId.CRAFTING: crafting_default_state(),
        AdvancedModuleId.DEDUCTION: deduction_default_state(),
        AdvancedModuleId.SURVIVAL_TRAVEL: survival_travel_default_state(),
        AdvancedModuleId.CULTIVATION: cultivation_default_state(),
    }


def _set_module_value(module_id: str, dotted_path: str, value: Any) -> StateDelta:
    delta = StateDelta(
        operation=StateDeltaOperation.SET,
        path=module_state_path(module_id, *dotted_path.split(".")),
        value=value,
        reason=f"{module_id} module state updated.",
        metadata={"module_id": module_id},
    )
    validate_module_state_delta(delta, module_id)
    return delta


def _add_module_value(module_id: str, dotted_path: str, value: Any) -> StateDelta:
    delta = StateDelta(
        operation=StateDeltaOperation.ADD,
        path=module_state_path(module_id, *dotted_path.split(".")),
        value=value,
        reason=f"{module_id} module list updated.",
        metadata={"module_id": module_id},
    )
    validate_module_state_delta(delta, module_id)
    return delta


def _magic_effect_delta(effect: dict[str, Any]) -> StateDelta | None:
    path = effect.get("path")
    if not isinstance(path, str) or not path.startswith("modules.magic."):
        return None
    parts = path.split(".")
    if any(part in {"secrets", "api_key", "authorization", "raw_env", "debug_memory"} for part in parts):
        return None
    value = effect.get("value")
    if len(parts) >= 5 and parts[2] == "casters":
        field_name = parts[-1]
        if field_name in {"mana", "focus"}:
            if not isinstance(value, int) or value < 0 or value > MAGIC_RESOURCE_MAX:
                return None
        elif field_name == "magical_status_effects":
            if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
                return None
        else:
            return None
    else:
        return None
    delta = StateDelta(
        operation=StateDeltaOperation.SET,
        path=path,
        value=value,
        reason="Spell effect resolved.",
        metadata={"module_id": AdvancedModuleId.MAGIC},
    )
    validate_module_state_delta(delta, AdvancedModuleId.MAGIC)
    return delta


def _module_action_with_event(
    action_id: str,
    state: GameState,
    level: SuccessLevel,
    reason: str,
    deltas: list[StateDelta],
    *,
    target_id: str | None = None,
) -> tuple[ActionResult, Event]:
    return ActionResult(success_level=level, reason=reason, state_deltas=deltas), _module_event(action_id, state, deltas, reason, target_id=target_id)


def _module_event(action_id: str, state: GameState, deltas: list[StateDelta], reason: str, *, target_id: str | None = None) -> Event:
    return Event(
        event_id=f"{action_id}:{state.turn}:{len(deltas)}",
        turn=state.turn,
        event_type="module_action" if ".tick" not in action_id else "module_tick",
        actor_id="system" if ".tick" in action_id else "player",
        action_type=action_id,
        result="resolved",
        visible_to_player=True,
        target_id=target_id,
        state_deltas=deltas,
        allow_empty_delta=not deltas,
        visible_summary=reason,
    )


def _economy_route_penalty(state: GameState, region_id: str) -> int:
    market = state.modules.get(AdvancedModuleId.ECONOMY_SIM, {}).get("markets", {}).get(region_id)
    return 10 if market and market.get("trade_route_status") == "blocked" else 0
