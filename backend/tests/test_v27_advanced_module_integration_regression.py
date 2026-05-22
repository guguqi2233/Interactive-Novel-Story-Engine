from __future__ import annotations

import inspect
import io
import json
import zipfile
from pathlib import Path
from random import Random
from shutil import copytree

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import EventLog
from app.core.state_delta import StateDelta, StateDeltaError, StateDeltaOperation, apply_delta
from app.core.world_state import FactState, FactVisibility, GameState, LocationState, PlayerState, WorldObjectState
from app.db.repository import SQLiteSaveRepository
from app.engine import advanced_modules
from app.engine.advanced_modules import (
    AdvancedModuleId,
    BreakthroughRule,
    CasterState,
    CommodityState,
    CraftingState,
    CultivationState,
    CultivatorState,
    DeductionState,
    EvidenceRecord,
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
from app.engine.action_registry import ActionMetadata
from app.engine.module_state import (
    ModuleMigrationPlan,
    ModuleMigrationService,
    ModuleMigrationStep,
    ModuleMigrationType,
    ModuleStateExtension,
    ModuleStateField,
    apply_module_delta,
    inject_module_defaults,
    module_state_path,
)
from app.main import app
from app.platform.mod_import_export import ModImportExportService
from app.platform.module_permissions import ModulePermissionSet
from app.playtesting.module_playtest import run_all_module_playtests
from app.quality.module_compatibility_stress import run_module_compatibility_stress
from app.quality.module_quality_gate import run_module_quality_gate
from app.session_store import InMemorySessionStore


def test_v27_module_state_migration_and_save_boundaries() -> None:
    state = _base_state()
    extension = ModuleStateExtension(
        module_id="economy_sim",
        namespace="state.modules.economy_sim",
        fields=[ModuleStateField(name="markets", default={})],
        default_values={"markets": {}},
        migration_required=True,
    )
    with pytest.raises(ValueError):
        ModuleStateExtension(module_id="bad", namespace="state.player", fields=[ModuleStateField(name="hp", default=1)])
    with pytest.raises(ValueError):
        ModuleStateField(name="player", default={})

    defaulted = inject_module_defaults(state, extension)
    delta = StateDelta(operation=StateDeltaOperation.SET, path=module_state_path("economy_sim", "markets", "m1"), value={"region_id": "m1"})
    migrated = apply_module_delta(defaulted, "economy_sim", delta)
    assert "economy_sim" in migrated.modules
    assert state.modules == {}
    reloaded = GameState.model_validate_json(migrated.model_dump_json())
    assert reloaded.modules == migrated.modules

    service = ModuleMigrationService()
    plan = service.plan_module_migration(state=state, extension=extension, project_id="v27")
    dry_run = service.dry_run_module_migration(state, plan)
    assert dry_run.dry_run and not dry_run.applied
    assert state.modules == {}
    applied, report = service.apply_module_migration(state, plan, confirm=True)
    assert report.applied
    assert applied.module_migration_history

    remove_plan = ModuleMigrationPlan(
        plan_id="v27:remove",
        module_id="economy_sim",
        steps=[ModuleMigrationStep(step_id="remove", migration_type=ModuleMigrationType.REMOVE_MODULE_STATE, module_id="economy_sim", destructive=True)],
    )
    preserved, rejected = service.apply_module_migration(applied, remove_plan, confirm=True)
    assert not rejected.applied
    assert "economy_sim" in preserved.modules


def test_v27_tactical_combat_eventlog_visibility_and_state_delta_flow() -> None:
    state = _base_state()
    state.modules["tactical_combat"] = {"encounters": {}, "combatants": {}}
    event_log = EventLog()
    for delta in start_tactical_encounter("ambush", ["player", "hidden_sniper"], hidden_combatants={"hidden_sniper"}):
        state = apply_delta(state, delta)
    assert "hidden_sniper" not in tactical_visible_summary(state)["combatants"]
    state.modules["tactical_combat"]["encounters"]["ambush"]["active_combatant_id"] = "player"
    before = state.model_dump(mode="json")
    result, event = resolve_tactical_action("aim", state)
    assert state.model_dump(mode="json") == before
    assert all(delta.path.startswith("modules.tactical_combat") for delta in result.state_deltas)
    event_log.append(event)
    assert event_log.list_events()[0].state_deltas == result.state_deltas
    next_state = _apply_all(state, result.state_deltas)
    assert next_state.modules["tactical_combat"]["combatants"]["player"]["action_points"] == 1
    assert "aiming" in next_state.modules["tactical_combat"]["combatants"]["player"]["status_effects"]
    assert GameState.model_validate_json(next_state.model_dump_json()).modules == next_state.modules


def test_v27_economy_and_faction_world_tick_boundaries() -> None:
    state = _base_state()
    state.modules["economy_sim"] = EconomySimState(
        markets={
            "hidden_market": MarketRegionState(region_id="hidden_market", hidden=True, known_by_player=False, commodities={"ore": CommodityState(commodity_id="ore", supply=10, demand=90)}),
            "front": MarketRegionState(region_id="front", trade_route_status="blocked", commodities={"grain": CommodityState(commodity_id="grain", supply=20, demand=80)}),
        }
    ).model_dump(mode="json")
    deltas, economy_event = economy_sim_tick(state)
    event_log = EventLog([economy_event])
    next_state = _apply_all(state, deltas)
    assert economy_price_modifier(next_state, "front", "grain") > 1
    assert next_state.objects["bench"].base_price == 0
    assert "hidden_market" not in (economy_event.visible_summary or "")
    assert event_log.list_events()[0].event_type == "module_tick"

    next_state.modules["faction_war"] = FactionWarState(
        regions={
            "front": RegionConflictState(region_id="front", control_score=50, known_by_player=True),
            "secret_front": RegionConflictState(region_id="secret_front", known_by_player=False),
        }
    ).model_dump(mode="json")
    war_deltas, war_event = faction_war_tick(next_state)
    event_log.append(war_event)
    after_war = _apply_all(next_state, war_deltas)
    assert after_war.modules["faction_war"]["regions"]["front"]["supply_level"] < 50
    assert "secret_front" not in faction_war_visible_summary(after_war)["regions"]
    assert len(event_log.list_events()) == 2


def test_v27_magic_hacking_crafting_are_rule_determined_and_secret_safe() -> None:
    state = _base_state()
    state.modules["magic"] = MagicState(
        casters={"player": CasterState(actor_id="player", mana=3, focus=1, known_spell_ids=["spark"])},
        spells={"spark": SpellDefinition(spell_id="spark", cost=2, effects=[{"path": "modules.magic.casters.player.magical_status_effects", "value": ["sparked"]}])},
    ).model_dump(mode="json")
    magic_before = state.model_dump(mode="json")
    magic_result, magic_event = resolve_magic_action("cast_spell", state, spell_id="spark")
    assert state.model_dump(mode="json") == magic_before
    after_magic = _apply_all(state, magic_result.state_deltas)
    assert after_magic.modules["magic"]["casters"]["player"]["mana"] == 1
    assert "llm" not in magic_result.reason.lower()
    assert "hidden" not in (magic_event.visible_summary or "").lower()

    state.modules["hacking"] = HackingState(hackables={"terminal": HackableObjectState(object_id="terminal", security_level=1, known_log_ids=["public_log", "hidden_log"], hidden_log_ids=["hidden_log"])}).model_dump(mode="json")
    hack_result, hack_event = resolve_hacking_action("hack_terminal", state, target_id="terminal", rng=Random(5))
    after_hack = _apply_all(state, hack_result.state_deltas)
    assert after_hack.modules["hacking"]["hackables"]["terminal"]["access_state"] == "access_granted"
    logs_result, _ = resolve_hacking_action("extract_logs", state, target_id="terminal")
    assert logs_result.state_deltas[0].value == ["public_log"]
    assert "network" not in hack_result.reason.lower()
    assert "hidden_log" not in (hack_event.visible_summary or "")

    state.modules["crafting"] = CraftingState(recipes={"torch": RecipeDefinition(recipe_id="torch", input_items={"wood": 1}, output_items={"torch": 1}, required_workstation_tags=["workbench"])}).model_dump(mode="json")
    craft_result, craft_event = resolve_craft_item(state, "torch", rng=Random(1))
    after_craft = _apply_all(state, craft_result.state_deltas)
    assert "wood" not in after_craft.player.inventory
    assert "torch" in after_craft.player.inventory
    assert craft_event.state_deltas == craft_result.state_deltas


def test_v27_deduction_survival_cultivation_visibility_and_determinism() -> None:
    state = _base_state()
    state.facts["known"] = FactState(id="known", text="Known clue", visibility=FactVisibility.PUBLIC)
    state.facts["hidden_truth"] = FactState(id="hidden_truth", text="Hidden truth", visibility=FactVisibility.HIDDEN)
    state.modules["deduction"] = DeductionState(evidence={"hidden_evidence": EvidenceRecord(evidence_id="hidden_evidence", hidden=True)}).model_dump(mode="json")
    hidden_evidence_result, hidden_evidence_event = resolve_deduction_action("inspect_evidence", state, target_id="hidden_evidence")
    assert hidden_evidence_result.success_level.value == "invalid"
    hypothesis, _ = resolve_deduction_action("test_hypothesis", state)
    assert hypothesis.state_deltas[0].value == 1
    assert "Hidden truth" not in (hidden_evidence_event.visible_summary or "")

    state.modules["survival_travel"] = SurvivalTravelState(statuses={"player": SurvivalStatus(fatigue=20)}, routes={"ridge": TravelRouteModuleState(route_id="ridge", from_location_id="start", to_location_id="ridge", time_cost=3, fatigue_cost=7, hidden_danger="hidden ravine")}).model_dump(mode="json")
    travel, travel_event = resolve_survival_action("travel_route", state, route_id="ridge", rng=Random(9))
    after_travel = _apply_all(state, travel.state_deltas)
    assert after_travel.turn == 3
    assert after_travel.modules["survival_travel"]["statuses"]["player"]["fatigue"] == 27
    assert "hidden ravine" not in (travel_event.visible_summary or "")

    state.modules["cultivation"] = CultivationState(
        cultivators={"player": CultivatorState(actor_id="player", progress=100, known_technique_ids=["breath"])},
        techniques={
            "breath": TechniqueDefinition(technique_id="breath", progress_gain=5),
            "forbidden": TechniqueDefinition(technique_id="forbidden", hidden=True),
        },
        breakthrough_rules=[BreakthroughRule(from_realm="mortal", to_realm="qi_refining", required_progress=100, difficulty=1)],
    ).model_dump(mode="json")
    denied, denied_event = resolve_cultivation_action("practice_technique", state, technique_id="forbidden")
    assert denied.success_level.value == "invalid"
    first, _ = resolve_cultivation_action("attempt_breakthrough", state, rng=Random(2))
    second, _ = resolve_cultivation_action("attempt_breakthrough", state, rng=Random(2))
    assert [delta.model_dump(mode="json") for delta in first.state_deltas] == [delta.model_dump(mode="json") for delta in second.state_deltas]
    assert "forbidden" not in (denied_event.visible_summary or "")


def test_v27_module_authoring_api_and_dashboard_are_safe(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    dashboard = client.get("/authoring/worlds/mist_valley/modules/dashboard")
    assert dashboard.status_code == 200
    payload = dashboard.json()
    assert payload["local_only"] is True
    assert {"tactical_combat", "economy_sim", "faction_war"}.issubset({item["module_id"] for item in payload["modules"]})
    assert "api_key" not in dashboard.text.lower()
    assert "hidden_secret" not in dashboard.text

    tactical = client.get("/authoring/worlds/mist_valley/modules/tactical-combat/config")
    assert tactical.status_code == 200
    validation = client.post("/authoring/worlds/mist_valley/modules/tactical-combat/validate-draft", json={"draft": {"combatants": [{"id": "secret", "hidden": True}]}})
    assert validation.status_code == 200
    assert validation.json()["ok"] is False
    economy = client.post("/authoring/worlds/mist_valley/modules/economy-sim/validate-draft", json={"draft": {"markets": []}})
    faction = client.post("/authoring/worlds/mist_valley/modules/faction-war/validate-draft", json={"draft": {"regions": []}})
    assert economy.json()["ok"] is True
    assert faction.json()["ok"] is True


def test_v27_playtest_stress_quality_import_export_and_static_boundaries(tmp_path: Path) -> None:
    playtests = run_all_module_playtests()
    assert all(report.success for report in playtests)
    assert all(report.event_count > 0 and report.save_load_stable for report in playtests)

    stress = run_module_compatibility_stress(
        ["tactical_combat", "magic"],
        actions=[
            ActionMetadata(id="module.a", label="Shared", aliases=["shared"], module_id="a"),
            ActionMetadata(id="module.b", label="Shared", aliases=["shared"], module_id="b"),
        ],
    )
    assert not stress.passed
    assert any(issue.code == "alias_conflict" for issue in stress.issues)

    good_gate = run_module_quality_gate(playtest_reports=playtests)
    assert good_gate.passed
    bad_gate = run_module_quality_gate(permissions={"bad": ModulePermissionSet(state_permissions={"modify_game_state_directly": True})})
    assert not bad_gate.passed

    service = ModImportExportService(tmp_path)
    valid_package = _zip_package(
        {
            "package_manifest_v2.json": {"package_id": "module_pack", "name": "Module Pack", "version": "1.0.0", "package_type": "rule_module", "schema_version": "2.0"},
            "module_state.json": {"module_id": "magic", "namespace": "state.modules.magic", "migration_required": True},
        }
    )
    valid_dry_run = service.import_dry_run(valid_package)
    assert valid_dry_run.ok
    assert valid_dry_run.migration_required
    assert not service.import_dry_run(_zip_package({"../evil.txt": "x"})).ok
    assert not service.import_dry_run(_zip_package({"package_manifest_v2.json": {"package_id": "bad", "name": "Bad", "version": "1", "package_type": "rule_module", "schema_version": "2.0"}, "payload.py": "print('no')"})).ok
    assert not service.import_dry_run(_zip_package({"package_manifest_v2.json": {"package_id": "secret", "name": "Secret", "version": "1", "package_type": "rule_module", "schema_version": "2.0"}, "secret.txt": "api_key=sk_live_real_secret_value_1234567890"})).ok

    source = inspect.getsource(advanced_modules)
    assert "eval(" not in source
    assert "exec(" not in source
    assert "ProviderGateway" not in source
    assert "openai" not in source.lower()


def _base_state() -> GameState:
    return GameState(
        world_id="v27-integration",
        player=PlayerState(location_id="start", inventory=["wood", "cyberdeck"]),
        locations={"start": LocationState(id="start", name="Start")},
        objects={"bench": WorldObjectState(id="bench", location_id="start", visible=True, tags=["workbench"])},
    )


def _apply_all(state: GameState, deltas: list[StateDelta]) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def _make_client(tmp_path: Path) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v27_integration.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock", llm_api_key="sk-test-fake-not-real")
    return TestClient(app)


def _zip_package(files: dict[str, object]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, payload in files.items():
            data = json.dumps(payload) if not isinstance(payload, str) else payload
            archive.writestr(name, data)
    return buffer.getvalue()
