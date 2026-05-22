from __future__ import annotations

import io
import json
import zipfile
from random import Random

import pytest

from app.core.state_delta import StateDelta, StateDeltaError, StateDeltaOperation, apply_delta
from app.core.world_state import GameState, LocationState, PlayerState, WorldObjectState
from app.engine.action_registry import ActionMetadata, ActionRegistry
from app.engine.advanced_modules import (
    AdvancedModuleId,
    CasterState,
    CommodityState,
    CraftingState,
    CultivationState,
    CultivatorState,
    EconomySimState,
    FactionWarState,
    HackableObjectState,
    HackingState,
    MagicState,
    MarketRegionState,
    RecipeDefinition,
    RegionConflictState,
    SpellDefinition,
    SurvivalStatus,
    SurvivalTravelState,
    TechniqueDefinition,
    TravelRouteModuleState,
    BreakthroughRule,
    ECONOMY_PRICE_INDEX_MAX,
    economy_price_modifier,
    economy_sim_tick,
    faction_war_tick,
    faction_war_visible_summary,
    resolve_craft_item,
    resolve_cultivation_action,
    resolve_deduction_action,
    resolve_hacking_action,
    resolve_magic_action,
    resolve_survival_action,
    resolve_tactical_action,
    start_tactical_encounter,
    tactical_visible_summary,
)
from app.engine.module_state import (
    ModuleMigrationService,
    ModuleMigrationStep,
    ModuleMigrationType,
    ModuleMigrationPlan,
    ModuleStateExtension,
    ModuleStateField,
    apply_module_delta,
    inject_module_defaults,
    module_state_path,
    validate_module_state_delta,
)
from app.platform.mod_import_export import ModImportExportService
from app.platform.module_permissions import ModulePermissionSet
from app.playtesting.module_playtest import run_all_module_playtests
from app.quality.module_compatibility_stress import run_module_compatibility_stress
from app.quality.module_quality_gate import run_module_quality_gate


def test_module_state_extension_defaults_delta_and_migration() -> None:
    state = _base_state()
    extension = ModuleStateExtension(
        module_id="tactical_combat",
        namespace="state.modules.tactical_combat",
        fields=[ModuleStateField(name="encounters", default={}), ModuleStateField(name="combatants", default={})],
        default_values={"encounters": {}, "combatants": {}},
        migration_required=True,
    )
    migrated = inject_module_defaults(state, extension)
    assert migrated.modules["tactical_combat"] == {"encounters": {}, "combatants": {}}
    delta = StateDelta(operation=StateDeltaOperation.SET, path=module_state_path("tactical_combat", "encounters", "e1"), value={"encounter_id": "e1"})
    next_state = apply_module_delta(migrated, "tactical_combat", delta)
    assert next_state.modules["tactical_combat"]["encounters"]["e1"]["encounter_id"] == "e1"
    with pytest.raises(StateDeltaError):
        validate_module_state_delta(StateDelta(operation=StateDeltaOperation.SET, path="player.hp", value=9), "tactical_combat")
    reloaded = GameState.model_validate_json(next_state.model_dump_json())
    assert reloaded.modules == next_state.modules

    service = ModuleMigrationService()
    plan = service.plan_module_migration(state=state, extension=extension, project_id="p1")
    dry_run = service.dry_run_module_migration(state, plan)
    assert dry_run.dry_run and not dry_run.applied and "encounters" in dry_run.resulting_module_state
    assert "tactical_combat" not in state.modules
    applied_state, report = service.apply_module_migration(state, plan, confirm=True)
    assert report.applied
    assert applied_state.module_migration_history
    remove_plan = ModuleMigrationPlan(
        plan_id="p1:remove",
        module_id="tactical_combat",
        steps=[ModuleMigrationStep(step_id="remove", migration_type=ModuleMigrationType.REMOVE_MODULE_STATE, module_id="tactical_combat", destructive=True)],
    )
    preserved, remove_report = service.apply_module_migration(applied_state, remove_plan, confirm=True)
    assert not remove_report.applied
    assert "tactical_combat" in preserved.modules


def test_tactical_combat_core_actions_visibility_event_and_save_load() -> None:
    state = _base_state()
    state.modules["tactical_combat"] = {"encounters": {}, "combatants": {}}
    for delta in start_tactical_encounter("e1", ["player", "hidden_guard"], hidden_combatants={"hidden_guard"}):
        state = apply_delta(state, delta)
    assert state.modules["tactical_combat"]["encounters"]["e1"]["turn_order"] == ["hidden_guard", "player"]
    assert "hidden_guard" not in tactical_visible_summary(state)["combatants"]
    state.modules["tactical_combat"]["encounters"]["e1"]["active_combatant_id"] = "player"
    result, event = resolve_tactical_action("take_cover", state)
    assert result.success_level.value == "success"
    assert any(delta.path.endswith("action_points") for delta in result.state_deltas)
    assert event.state_deltas == result.state_deltas
    next_state = _apply_all(state, result.state_deltas)
    assert next_state.modules["tactical_combat"]["combatants"]["player"]["cover_level"] == 1
    assert GameState.model_validate_json(next_state.model_dump_json()).modules == next_state.modules


def test_economy_and_faction_ticks_are_deterministic_and_visible_safe() -> None:
    state = _base_state()
    state.modules["economy_sim"] = EconomySimState(
        markets={"valley": MarketRegionState(region_id="valley", commodities={"grain": CommodityState(commodity_id="grain", supply=10, demand=90)}, trade_route_status="blocked")}
    ).model_dump(mode="json")
    first_deltas, first_event = economy_sim_tick(state)
    second_deltas, _ = economy_sim_tick(state)
    assert [delta.model_dump(mode="json") for delta in first_deltas] == [delta.model_dump(mode="json") for delta in second_deltas]
    next_state = _apply_all(state, first_deltas)
    assert economy_price_modifier(next_state, "valley", "grain") and economy_price_modifier(next_state, "valley", "grain") > 1
    assert state.objects["bench"].base_price == 0
    assert first_event.state_deltas == first_deltas

    next_state.modules["faction_war"] = FactionWarState(
        regions={
            "hidden": RegionConflictState(region_id="hidden", known_by_player=False),
            "known": RegionConflictState(region_id="known", known_by_player=True),
        }
    ).model_dump(mode="json")
    deltas, event = faction_war_tick(next_state)
    assert deltas and event.event_type == "module_tick"
    summary = faction_war_visible_summary(next_state)
    assert "known" in summary["regions"]
    assert "hidden" not in summary["regions"]


def test_v27_release_blockers_are_rejected() -> None:
    state = _base_state()
    with pytest.raises(ValueError):
        RecipeDefinition(recipe_id="free_gold", input_items={}, output_items={"gold": 1})
    with pytest.raises(ValueError):
        RecipeDefinition(recipe_id="dupe_gold", input_items={"gold": 1}, output_items={"gold": 2})

    state.modules["economy_sim"] = EconomySimState(
        markets={"boom": MarketRegionState(region_id="boom", commodities={"ore": CommodityState(commodity_id="ore", supply=0, demand=100000)})}
    ).model_dump(mode="json")
    deltas, _ = economy_sim_tick(state)
    next_state = _apply_all(state, deltas)
    assert economy_price_modifier(next_state, "boom", "ore") == ECONOMY_PRICE_INDEX_MAX

    state.modules["magic"] = MagicState(
        casters={"player": CasterState(actor_id="player", mana=5, known_spell_ids=["bad"])},
        spells={"bad": SpellDefinition(spell_id="bad", cost=1, effects=[{"path": "modules.magic.casters.player.mana", "value": -100}])},
    ).model_dump(mode="json")
    result, event = resolve_magic_action("cast_spell", state, spell_id="bad")
    assert result.success_level.value == "invalid"
    assert result.state_deltas == []
    assert event.state_deltas == []


def test_magic_hacking_crafting_deduction_survival_cultivation_paths() -> None:
    state = _base_state()
    state.modules["magic"] = MagicState(
        casters={"player": CasterState(actor_id="player", mana=2, known_spell_ids=["spark"])},
        spells={"spark": SpellDefinition(spell_id="spark", cost=1, illegal_in_public=True)},
    ).model_dump(mode="json")
    magic_result, magic_event = resolve_magic_action("cast_spell", state, spell_id="spark")
    assert magic_result.success_level.value == "success"
    assert any(delta.path == "flags.public_illegal_magic_witnessed" for delta in magic_result.state_deltas)
    assert magic_event.state_deltas == magic_result.state_deltas

    state.modules["hacking"] = HackingState(hackables={"terminal": HackableObjectState(object_id="terminal", security_level=1, known_log_ids=["public", "hidden"], hidden_log_ids=["hidden"])}).model_dump(mode="json")
    hack_result, _ = resolve_hacking_action("extract_logs", state, target_id="terminal")
    assert hack_result.state_deltas[0].value == ["public"]
    fail_result, _ = resolve_hacking_action("hack_terminal", state.model_copy(update={"player": PlayerState(location_id="start", inventory=[])}), target_id="terminal", rng=Random(0))
    assert fail_result.success_level.value in {"success", "failure"}

    state.modules["crafting"] = CraftingState(recipes={"chair": RecipeDefinition(recipe_id="chair", input_items={"wood": 1}, output_items={"chair": 1}, required_workstation_tags=["workbench"])}).model_dump(mode="json")
    craft_result, craft_event = resolve_craft_item(state, "chair", rng=Random(1))
    assert craft_result.success_level.value == "success"
    assert craft_event.state_deltas == craft_result.state_deltas

    deduction_result, _ = resolve_deduction_action("form_hypothesis", state, target_id="h1")
    assert not any(delta.path.startswith("facts.") for delta in deduction_result.state_deltas)

    state.modules["survival_travel"] = SurvivalTravelState(statuses={"player": SurvivalStatus(fatigue=10)}, routes={"road": TravelRouteModuleState(route_id="road", from_location_id="start", to_location_id="out", time_cost=2, fatigue_cost=5, hidden_danger="hidden_secret")}).model_dump(mode="json")
    travel_result, travel_event = resolve_survival_action("travel_route", state, route_id="road", rng=Random(2))
    assert any(delta.path == "turn" for delta in travel_result.state_deltas)
    assert "hidden_secret" not in (travel_event.visible_summary or "")

    state.modules["cultivation"] = CultivationState(
        cultivators={"player": CultivatorState(actor_id="player", progress=100, known_technique_ids=["breath"])},
        techniques={"breath": TechniqueDefinition(technique_id="breath", progress_gain=5)},
        breakthrough_rules=[BreakthroughRule(from_realm="mortal", to_realm="qi_refining", required_progress=100, difficulty=1)],
    ).model_dump(mode="json")
    meditate, _ = resolve_cultivation_action("meditate", state)
    assert meditate.state_deltas
    practice, _ = resolve_cultivation_action("practice_technique", state, technique_id="breath")
    assert practice.success_level.value == "success"
    breakthrough, _ = resolve_cultivation_action("attempt_breakthrough", state, rng=Random(2))
    assert breakthrough.success_level.value in {"success", "failure"}


def test_action_registry_conflicts_playtests_stress_quality_and_import_export(tmp_path) -> None:
    registry = ActionRegistry()
    assert registry.get_action_definition("attack")
    assert run_all_module_playtests()
    reports = run_all_module_playtests()
    assert all(report.success for report in reports)
    stress = run_module_compatibility_stress(
        ["tactical_combat", "magic"],
        actions=[
            ActionMetadata(id="module.one", label="Shared", aliases=["shared"], module_id="one"),
            ActionMetadata(id="module.two", label="Other", aliases=["shared"], module_id="two"),
        ],
    )
    assert not stress.passed
    assert any(issue.code == "alias_conflict" for issue in stress.issues)
    danger = run_module_quality_gate(permissions={"bad": ModulePermissionSet(file_permissions={"execute_code": True})})
    assert not danger.passed
    gate = run_module_quality_gate(playtest_reports=reports)
    assert gate.passed

    package = _zip_package(
        {
            "package_manifest_v2.json": {
                "package_id": "advanced_pack",
                "name": "Advanced Pack",
                "version": "1.0.0",
                "package_type": "rule_module",
                "schema_version": "2.0",
                "included_files": [{"path": "module_state.json"}],
            },
            "module_state.json": {"module_id": "tactical_combat", "namespace": "state.modules.tactical_combat", "migration_required": True},
        }
    )
    service = ModImportExportService(tmp_path)
    dry_run = service.import_dry_run(package)
    assert dry_run.ok
    assert dry_run.migration_required
    assert not dry_run.writes_to_disk
    with pytest.raises(ValueError):
        service.import_apply(package, confirm=False)
    assert service.disable_module_preserve_state("advanced_pack")["state_preserved"] is True
    with pytest.raises(ValueError):
        service.remove_module_state("advanced_pack")

    assert not service.import_dry_run(_zip_package({"../evil.txt": "x"})).ok
    assert not service.import_dry_run(_zip_package({"package_manifest_v2.json": {"package_id": "bad", "name": "Bad", "version": "1", "package_type": "script_pack", "schema_version": "2.0"}, "run.exe": "x"})).ok
    assert not service.import_dry_run(_zip_package({"package_manifest_v2.json": {"package_id": "secret", "name": "Secret", "version": "1", "package_type": "script_pack", "schema_version": "2.0"}, "secret.txt": "api_key=sk_live_real_secret_value_1234567890"})).ok


def _base_state() -> GameState:
    return GameState(
        world_id="v27-test",
        player=PlayerState(location_id="start", inventory=["wood", "cyberdeck"]),
        locations={"start": LocationState(id="start", name="Start")},
        objects={"bench": WorldObjectState(id="bench", location_id="start", visible=True, tags=["workbench"])},
    )


def _apply_all(state: GameState, deltas: list[StateDelta]) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def _zip_package(files: dict[str, object]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, payload in files.items():
            data = json.dumps(payload) if not isinstance(payload, str) else payload
            archive.writestr(name, data)
    return buffer.getvalue()
