from __future__ import annotations

from pathlib import Path
from random import Random

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import Event
from app.core.state_delta import StateDeltaOperation, apply_delta
from app.core.world_state import (
    CraftingStationState,
    EvidenceState,
    FactState,
    FactVisibility,
    FactionMissionDefinition,
    FactionMissionReward,
    FactionState,
    GameState,
    HackableState,
    HackingToolState,
    HypothesisState,
    LocationState,
    MagicResourceState,
    NPCState,
    PlayerState,
    QuestStage,
    QuestState,
    QuestStatus,
    QuestVisibility,
    RelationshipState,
    ReputationState,
    SurvivalState,
    TestimonyState as InvestigationTestimonyState,
    TravelRouteState,
    WeaponProfile,
    WeatherState,
    WorldObjectState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.action_mod_validator import validate_action_mod_files
from app.engine.action_registry import ActionRegistry
from app.engine.actions.declarative import (
    DeclarativeActionDefinition,
    DeclarativeActionHandler,
    DeclarativeActionTargetSpec,
    DeclarativeCondition,
    DeclarativeConditionType,
    DeclarativeOutcome,
    DeclarativeStateDeltaTemplate,
    DeclarativeTargetKind,
)
from app.engine.actions.dsl import (
    ActionCheck,
    ActionCheckType,
    ActionDSLValidationError,
    ActionEffect,
    ActionEffectType,
    ActionPrecondition,
    ActionPreconditionType,
    ActionStateDeltaTemplate,
    compile_effect,
    evaluate_check,
    evaluate_precondition,
)
from app.engine.actions.schemas import SuccessLevel
from app.engine.gameplay_module_debugger import ModuleActionDryRunRequest, dry_run_module_action
from app.engine.gameplay_module_loader import GameplayModuleLoader
from app.engine.gameplay_module_packages import (
    GameplayModulePackageImportRequest,
    export_gameplay_module_package,
    import_gameplay_module_package_dry_run,
)
from app.engine.rules.combat import CombatantStance, resolve_attack
from app.engine.rules.crafting import CraftingActionHandler, CraftingModuleConfig, RecipeDefinition
from app.engine.rules.domain import build_facility, claim_base, collect_income
from app.engine.rules.faction_missions import accept_faction_mission, complete_faction_mission, fail_faction_mission
from app.engine.rules.hacking import HackingActionHandler
from app.engine.rules.investigation import InvestigationActionHandler
from app.engine.rules.magic import (
    CastSpellActionHandler,
    MagicModuleConfig,
    SpellDefinition,
    SpellTargetType,
)
from app.engine.rules.social_manipulation import SocialManipulationActionHandler
from app.engine.rules.stealth import StealthActionHandler
from app.engine.rules.survival import SurvivalActionHandler
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.main import app
from app.playtesting.gameplay_module_regression import (
    GameplayModuleRegressionScenario,
    GameplayModuleRegressionScenarioType,
    run_gameplay_module_regression,
)
from app.quality.gameplay_module_quality import run_gameplay_module_quality_gate
from app.session_store import InMemorySessionStore, build_visible_state


SECRET_TRUTH = "The hidden heir controls the old shrine."


def test_v16_manifest_boundary_dependencies_conflicts_and_save_compatibility(tmp_path: Path) -> None:
    _write_module(tmp_path, "safe_magic", dependencies=["missing_mod"], conflicts=["rival_mod"])
    _write_module(tmp_path, "rival_mod")
    _write_module(tmp_path, "unsafe_exec", execute_code=True)
    _write_module(tmp_path, "bad_save", migration_required=True)

    loader = GameplayModuleLoader(tmp_path / "gameplay_modules")

    assert loader.validate_module("safe_magic").ok
    assert not loader.resolve_dependencies(["safe_magic"]).ok
    assert loader.detect_conflicts(["safe_magic", "rival_mod"]).conflicts == [("rival_mod", "safe_magic")]
    assert any(issue.code == "gameplay_module_forbidden_permission" for issue in loader.validate_module("unsafe_exec").errors)
    assert any(issue.code == "gameplay_module_missing_migration_defaults" for issue in loader.validate_module("bad_save").errors)


def test_v16_declarative_action_registry_dsl_state_delta_event_and_hidden_visibility() -> None:
    state = _base_state()
    before = state.model_dump(mode="json")
    definition = _pray_definition(hidden_outcome=True)
    registry = ActionRegistry(include_core=False)
    registry.register_module_action(definition, module_id="safe_magic")

    handler = registry.get_handler_for_intent(_intent("pray", "shrine"), state)
    execution = handler.resolve_with_event(_intent("pray", "shrine"), state, Random(7))  # type: ignore[union-attr]
    next_state = _apply_all(state, execution.action_result.state_deltas)
    item_precondition = evaluate_precondition(
        ActionPrecondition(precondition_type=ActionPreconditionType.ACTOR_HAS_ITEM, item_id="candle"),
        state,
    )
    check = evaluate_check(ActionCheck(check_type=ActionCheckType.FIXED_SUCCESS), state)
    effect_deltas = compile_effect(
        ActionEffect(
            effect_type=ActionEffectType.STATE_DELTA_TEMPLATE,
            state_delta_template=ActionStateDeltaTemplate(
                operation=StateDeltaOperation.SET,
                path="flags.dsl_checked",
                value=True,
            ),
        ),
        state,
        event_id="event-dsl",
    )
    assert handler is not None
    assert registry.available_action_aliases() == ["module.pray", "pray"]
    assert item_precondition.passed is True
    assert check.passed is True
    assert effect_deltas[0].path == "flags.dsl_checked"
    assert execution.action_result.success_level == SuccessLevel.SUCCESS
    assert isinstance(execution.event, Event)
    assert execution.event.state_deltas == execution.action_result.state_deltas
    assert state.model_dump(mode="json") == before
    assert next_state.flags["prayed_at_shrine"] is True
    assert execution.event.visible_to_player is False
    assert SECRET_TRUTH not in build_visible_state(next_state).model_dump_json()


def test_v16_action_dsl_and_declarative_visible_facts_block_hidden_fact_leaks() -> None:
    state = _base_state()

    with pytest.raises(ActionDSLValidationError):
        compile_effect(
            ActionEffect(effect_type=ActionEffectType.ADD_FACT_DISCOVERY, fact_id="hidden_oath"),
            state,
            event_id="event-hidden-fact",
        )

    public_deltas = compile_effect(
        ActionEffect(effect_type=ActionEffectType.ADD_FACT_DISCOVERY, fact_id="shrine_open"),
        state,
        event_id="event-public-fact",
    )
    assert public_deltas[0].path == "player_visible_facts"
    assert public_deltas[0].value == "shrine_open"

    definition = _pray_definition()
    definition.outcomes[SuccessLevel.SUCCESS].visible_facts.append("hidden_oath")
    execution = DeclarativeActionHandler(definition).resolve_with_event(_intent("pray", "shrine"), state, Random(7))

    assert "hidden_oath" not in execution.action_result.visible_facts
    assert SECRET_TRUTH not in execution.action_result.model_dump_json()


def test_v16_action_mod_validation_rejects_forbidden_state_delta_path(tmp_path: Path) -> None:
    module_path = _write_module(tmp_path, "bad_action", delta_path="player.hp")
    manifest = GameplayModuleLoader(tmp_path / "gameplay_modules").load_manifest_only("bad_action")

    report = validate_action_mod_files(module_path, manifest)

    assert not report.ok
    assert any(issue.code == "action_mod_forbidden_state_delta_path" for issue in report.errors)


def test_v16_magic_hacking_crafting_investigation_and_survival_smoke() -> None:
    magic_state = _base_state()
    magic_state.magic_resources["player"] = MagicResourceState(mana=5, max_mana=10)
    magic_state.npcs["guard"] = NPCState(id="guard", location_id="shrine", visible=True)
    magic_execution = CastSpellActionHandler(
        MagicModuleConfig(
            spells={
                "spark": SpellDefinition(
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
                                value=-1,
                            ),
                        )
                    ],
                    aliases=["cast spark"],
                )
            }
        )
    ).resolve_with_event(_intent("cast spark", "guard"), magic_state, Random(1))

    hack_state = _hacking_state(difficulty=10)
    hack_success = HackingActionHandler().resolve_with_event(_intent("hack terminal", "terminal"), hack_state, Random(1))
    hack_failure = HackingActionHandler().resolve_with_event(_intent("hack terminal", "terminal"), _hacking_state(difficulty=40), Random(1))

    craft_success = CraftingActionHandler(
        CraftingModuleConfig(recipes={"chair": _recipe()})
    ).resolve_with_event(_intent("craft chair"), _crafting_state(), Random(1))
    craft_failure = CraftingActionHandler(
        CraftingModuleConfig(recipes={"chair": _recipe()})
    ).resolve_with_event(_intent("craft chair"), _crafting_state(include_wood=False), Random(1))

    investigation_state = _investigation_state()
    weak_hypothesis = InvestigationActionHandler().resolve_with_event(
        _intent("form hypothesis", "avery_did_it"), investigation_state, Random(1)
    )

    survival_state = _survival_state()
    travel = SurvivalActionHandler().resolve_with_event(_intent("travel route", "village_to_pass"), survival_state, Random(1))
    after_travel = _apply_all(survival_state, travel.action_result.state_deltas)
    rest = SurvivalActionHandler().resolve_with_event(_intent("rest"), after_travel, Random(1))
    eat = SurvivalActionHandler().resolve_with_event(_intent("consume food"), _survival_state(), Random(1))

    assert magic_execution.action_result.success_level == SuccessLevel.SUCCESS
    assert any(delta.path == "magic_resources.player.mana" for delta in magic_execution.action_result.state_deltas)
    assert hack_success.action_result.success_level == SuccessLevel.SUCCESS
    assert hack_failure.action_result.success_level == SuccessLevel.FAILURE
    assert craft_success.action_result.success_level == SuccessLevel.SUCCESS
    assert craft_failure.action_result.success_level == SuccessLevel.FAILURE
    assert weak_hypothesis.action_result.success_level == SuccessLevel.FAILURE
    assert travel.action_result.success_level == SuccessLevel.SUCCESS
    assert rest.action_result.success_level == SuccessLevel.SUCCESS
    assert eat.action_result.success_level == SuccessLevel.SUCCESS
    assert all(result.event.state_deltas == result.action_result.state_deltas for result in [magic_execution, hack_success, craft_success, weak_hypothesis, travel])


def test_v16_stealth_combat_social_faction_and_domain_smoke() -> None:
    stealth_state = _stealth_state()
    hide = StealthActionHandler().resolve_with_event(_intent("hide"), stealth_state, Random(5))
    noise = StealthActionHandler().resolve_with_event(_intent("create noise"), stealth_state, Random(1))
    follow = StealthActionHandler().resolve_with_event(_intent("shadow npc", "captain"), stealth_state, Random(1))

    combat_state = _combat_state(hidden_witness=True)
    combat_state.objects["sap"] = WorldObjectState(id="sap", owner_id="player", portable=True, tags=["non_lethal"])
    combat_state.player.inventory.append("sap")
    combat_state.weapon_profiles["sap"] = WeaponProfile(id="sap", tags=["non_lethal"], damage_bonus=10, non_lethal=True)
    attack_result, attack_deltas = resolve_attack(combat_state, "player", "bandit", Random(0))

    social_state = _social_state()
    persuade = SocialManipulationActionHandler().resolve_with_event(_intent("persuade", "harlan"), social_state, Random(0))
    bribe_fail = SocialManipulationActionHandler().resolve_with_event(
        _intent("bribe", "harlan"),
        social_state.model_copy(update={"player": social_state.player.model_copy(update={"currency": 0})}),
        Random(0),
    )
    blackmail_fail = SocialManipulationActionHandler().resolve_with_event(_intent("blackmail", "harlan"), social_state, Random(0))

    faction_state = _faction_mission_state()
    accepted = accept_faction_mission(faction_state, "watch_courier")
    after_accept = _apply_all(faction_state, accepted.state_deltas)
    completed = complete_faction_mission(after_accept, "watch_courier")
    failed = fail_faction_mission(_apply_all(faction_state, accept_faction_mission(faction_state, "watch_sabotage").state_deltas), "watch_sabotage", "missed_deadline")

    domain_state = _domain_state()
    claimed = claim_base(domain_state, "base_1", "hall")
    after_claim = _apply_all(domain_state, claimed.state_deltas)
    built = build_facility(after_claim, "base_1", "market", "market", cost=5, income=4)
    after_build = _apply_all(after_claim, built.state_deltas)
    income = collect_income(after_build, "base_1")

    visible_combat = build_visible_state(_apply_all(combat_state, attack_deltas)).model_dump_json()

    assert hide.action_result.success_level in {SuccessLevel.SUCCESS, SuccessLevel.FAILURE}
    assert noise.action_result.success_level == SuccessLevel.SUCCESS
    assert follow.action_result.success_level in {SuccessLevel.SUCCESS, SuccessLevel.FAILURE}
    assert attack_result.damage is not None
    assert "witness" not in visible_combat
    assert persuade.action_result.success_level == SuccessLevel.SUCCESS
    assert bribe_fail.action_result.success_level == SuccessLevel.FAILURE
    assert blackmail_fail.action_result.success_level == SuccessLevel.FAILURE
    assert accepted.accepted is True
    assert completed.completed is True
    assert failed.failed is True
    assert claimed.rejected_reason is None
    assert built.rejected_reason is None
    assert income.rejected_reason is None


def test_v16_hidden_content_save_load_and_replay_boundaries(tmp_path: Path) -> None:
    state = _hacking_state()
    access = HackingActionHandler().resolve_with_event(_intent("access logs", "terminal"), state, Random(1))
    next_state = _apply_all(state, access.action_result.state_deltas)
    repository = SQLiteSaveRepository(tmp_path / "v16_save.db")
    repository.create_save("save-1", next_state)
    loaded = repository.load_save("save-1")
    first = HackingActionHandler().resolve_with_event(_intent("hack terminal", "terminal"), _hacking_state(difficulty=40), Random(3))
    second = HackingActionHandler().resolve_with_event(_intent("hack terminal", "terminal"), _hacking_state(difficulty=40), Random(3))

    assert "hidden_root_log" not in next_state.player_visible_facts
    assert SECRET_TRUTH not in build_visible_state(next_state).model_dump_json()
    assert loaded.hackables["terminal"].security_state == next_state.hackables["terminal"].security_state
    assert first.action_result.model_dump(mode="json") == second.action_result.model_dump(mode="json")


def test_v16_quality_regression_debug_and_import_export_are_safe(tmp_path: Path) -> None:
    module_path = _write_module(tmp_path, "package_pray")
    quality = run_gameplay_module_quality_gate("package_pray", modules_root=tmp_path / "gameplay_modules")
    regression = run_gameplay_module_regression(
        [
            GameplayModuleRegressionScenario(
                id="magic_action",
                module_id="magic",
                action_id="magic.cast_spell",
                scenario_type=GameplayModuleRegressionScenarioType.ACTION_SUCCESS,
                input_sequence=["cast spark"],
                expected_result="success",
                expected_deltas=["magic_resources.player.mana"],
                seed=1,
            )
        ]
    )
    debug_state = _base_state()
    debug = dry_run_module_action(
        "package_pray",
        "package_pray.pray",
        ModuleActionDryRunRequest(input_text="pray", seed=1),
        modules_root=tmp_path / "gameplay_modules",
    )
    exported = export_gameplay_module_package("package_pray", modules_root=tmp_path / "gameplay_modules")
    dry_run = import_gameplay_module_package_dry_run(GameplayModulePackageImportRequest(archive_base64=exported.archive_base64))

    module_path.joinpath("evil.py").write_text("print('no')\n", encoding="utf-8")
    unsafe_quality = run_gameplay_module_quality_gate("package_pray", modules_root=tmp_path / "gameplay_modules")

    assert quality.passed is True
    assert regression.passed is True
    assert debug.state_unchanged is True
    assert debug.state_delta_preview
    assert exported.exported is True
    assert dry_run.ok is True
    assert dry_run.imported is False
    assert dry_run.writes_to_disk is False
    assert "api_key" not in exported.archive_base64.lower()
    assert unsafe_quality.passed is False


def test_v16_action_mod_and_module_debugger_api_disabled_states_are_safe(tmp_path: Path) -> None:
    _write_module(tmp_path, "package_pray")
    app.state.session_store = InMemorySessionStore()
    app.state.settings = Settings(enable_authoring_api=False, enable_debug_api=False, llm_provider="mock")
    app.state.gameplay_modules_root = str(tmp_path / "gameplay_modules")
    client = TestClient(app)

    authoring_response = client.post("/authoring/action-mods/validate", json={"actions": []})
    debug_response = client.get("/debug/modules")

    assert authoring_response.status_code == 403
    assert debug_response.status_code == 403


def _intent(raw_text: str, target_id: str | None = None) -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.UNKNOWN,
        raw_text=raw_text,
        target_id=target_id,
        confidence=1.0,
        requires_clarification=False,
    )


def _apply_all(state: GameState, deltas: list) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def _base_state() -> GameState:
    return GameState(
        world_id="v16-integration",
        turn=8,
        player=PlayerState(location_id="shrine", inventory=["candle"], currency=20),
        locations={"shrine": LocationState(id="shrine", name="Old Shrine")},
        facts={
            "shrine_open": FactState(id="shrine_open", text="The shrine is open.", visibility=FactVisibility.PUBLIC),
            "hidden_oath": FactState(id="hidden_oath", text=SECRET_TRUTH, visibility=FactVisibility.HIDDEN),
        },
        player_visible_facts={"shrine_open"},
    )


def _pray_definition(*, hidden_outcome: bool = False) -> DeclarativeActionDefinition:
    return DeclarativeActionDefinition(
        id="module.pray",
        label="Pray",
        aliases=["pray"],
        category="general",
        target_specs=[DeclarativeActionTargetSpec(kind=DeclarativeTargetKind.CURRENT_LOCATION)],
        preconditions=[DeclarativeCondition(condition_type=DeclarativeConditionType.AT_LOCATION, value="shrine")],
        checks=[{"check_type": "always"}],
        outcomes={
            SuccessLevel.SUCCESS: DeclarativeOutcome(
                success_level=SuccessLevel.SUCCESS,
                reason="The deterministic shrine rules accept the prayer.",
                visible_facts=["shrine_open"],
                hidden_facts=["hidden_oath"],
                hidden_outcome=hidden_outcome,
                state_delta_templates=[
                    DeclarativeStateDeltaTemplate(
                        operation=StateDeltaOperation.SET,
                        path="flags.prayed_at_{target_id}",
                        value=True,
                    )
                ],
            )
        },
        event_type="module.pray",
    )


def _hacking_state(*, difficulty: int = 10) -> GameState:
    return GameState(
        world_id="v16-hacking",
        turn=2,
        player=PlayerState(location_id="server_room"),
        locations={"server_room": LocationState(id="server_room", name="Server Room")},
        hackables={
            "terminal": HackableState(
                id="terminal",
                target_type="terminal",
                location_id="server_room",
                difficulty=difficulty,
                linked_fact_ids=["public_log", "hidden_root_log"],
            )
        },
        hacking_tools={"deck": HackingToolState(id="deck", owner_id="player", power=10)},
        facts={
            "public_log": FactState(id="public_log", text="The public access log names a courier.", visibility=FactVisibility.DISCOVERABLE),
            "hidden_root_log": FactState(id="hidden_root_log", text=SECRET_TRUTH, visibility=FactVisibility.HIDDEN),
        },
    )


def _recipe() -> RecipeDefinition:
    return RecipeDefinition(
        id="chair",
        output_item_id="chair",
        required_items=["hammer", "wood"],
        consumed_items=["wood"],
        required_station_tags=["workbench"],
        aliases=["craft chair"],
    )


def _crafting_state(*, include_wood: bool = True) -> GameState:
    objects = {"hammer": WorldObjectState(id="hammer", owner_id="player", portable=True, tags=["tool"])}
    if include_wood:
        objects["wood"] = WorldObjectState(id="wood", owner_id="player", portable=True)
    return GameState(
        world_id="v16-crafting",
        player=PlayerState(location_id="workshop"),
        locations={"workshop": LocationState(id="workshop", name="Workshop")},
        objects=objects,
        crafting_stations={"bench": CraftingStationState(id="bench", location_id="workshop", tags=["workbench"])},
    )


def _investigation_state() -> GameState:
    return GameState(
        world_id="v16-investigation",
        player=PlayerState(location_id="study"),
        locations={"study": LocationState(id="study", name="Study")},
        facts={"mud_fact": FactState(id="mud_fact", text="Mud is on the sill.", visibility=FactVisibility.DISCOVERABLE)},
        evidence={"mud": EvidenceState(id="mud", fact_id="mud_fact", location_id="study", visible=True)},
        testimonies={
            "avery_testimony": InvestigationTestimonyState(
                id="avery_testimony",
                npc_id="avery",
                fact_ids=[],
                known_to_player=True,
            )
        },
        hypotheses={
            "avery_did_it": HypothesisState(
                id="avery_did_it",
                suspect_id="avery",
                correct_suspect_id="avery",
                required_evidence_ids=["mud"],
                quest_id="case",
                quest_objective_id="accuse_avery",
            )
        },
        quests={
            "case": QuestState(
                id="case",
                title="Case",
                initial_stage="investigate",
                current_stage="investigate",
                stages={"investigate": QuestStage(id="investigate", title="Investigate", objectives=["accuse_avery"])},
                visibility=QuestVisibility.PUBLIC,
                status=QuestStatus.ACTIVE,
                known_to_player=True,
            )
        },
    )


def _survival_state() -> GameState:
    return GameState(
        world_id="v16-survival",
        player=PlayerState(location_id="village"),
        locations={"village": LocationState(id="village", name="Village"), "pass": LocationState(id="pass", name="Pass")},
        objects={"rations": WorldObjectState(id="rations", owner_id="player", tags=["food"])},
        survival={"player": SurvivalState(actor_id="player", fatigue=20, hunger=40, thirst=30)},
        travel_routes={"village_to_pass": TravelRouteState(id="village_to_pass", from_location_id="village", to_location_id="pass", time_cost=60, fatigue_cost=5)},
        weather={"village": WeatherState(location_id="village", condition="clear", severity=0)},
    )


def _stealth_state() -> GameState:
    return GameState(
        world_id="v16-stealth",
        player=PlayerState(location_id="alley", stealth_modifier=4),
        locations={"alley": LocationState(id="alley", name="Alley", cover_level=6, light_level=1)},
        npcs={
            "guard": NPCState(id="guard", location_id="alley", alertness=1),
            "captain": NPCState(id="captain", location_id="alley", alertness=10),
            "hidden_observer": NPCState(id="hidden_observer", location_id="alley", hidden=True, alertness=12),
        },
    )


def _combat_state(*, hidden_witness: bool = False) -> GameState:
    return GameState(
        world_id="v16-combat",
        player=PlayerState(location_id="square", attack=4),
        locations={"square": LocationState(id="square", name="Square")},
        npcs={
            "bandit": NPCState(id="bandit", location_id="square", hp=1, combat_stance=CombatantStance.DEFENSIVE),
            "witness": NPCState(id="witness", location_id="square", hidden=hidden_witness),
        },
    )


def _social_state() -> GameState:
    return GameState(
        world_id="v16-social",
        player=PlayerState(location_id="square", currency=20),
        locations={"square": LocationState(id="square", name="Square")},
        npcs={"harlan": NPCState(id="harlan", location_id="square", knowledge=["public_clue"])},
        relationships={
            "harlan_player": RelationshipState(
                id="harlan_player",
                source_id="harlan",
                target_id="player",
                relation_type="general",
                trust=2,
                known_by_player=True,
            )
        },
        facts={"public_clue": FactState(id="public_clue", text="The gate was open.", visibility=FactVisibility.DISCOVERABLE)},
    )


def _faction_mission_state() -> GameState:
    return GameState(
        world_id="v16-faction",
        factions={"watch": FactionState(id="watch", name="Watch", reputation=ReputationState(value=15, known_to_player=True), known_by_player=True, conflict_tags=["smugglers"])},
        faction_mission_definitions={
            "watch_courier": FactionMissionDefinition(
                id="watch_courier",
                faction_id="watch",
                mission_type="courier",
                title="Carry the writ",
                min_reputation=10,
                reward=FactionMissionReward(reputation_delta=5, currency=7),
            ),
            "watch_sabotage": FactionMissionDefinition(
                id="watch_sabotage",
                faction_id="watch",
                mission_type="sabotage",
                title="Disrupt smugglers",
                min_reputation=5,
                failure_reputation_delta=-4,
            ),
        },
    )


def _domain_state() -> GameState:
    return GameState(
        world_id="v16-domain",
        player=PlayerState(location_id="hall", currency=50),
        locations={"hall": LocationState(id="hall", name="Hall")},
        npcs={"mira": NPCState(id="mira", location_id="hall")},
    )


def _write_module(
    root: Path,
    module_id: str,
    *,
    dependencies: list[str] | None = None,
    conflicts: list[str] | None = None,
    execute_code: bool = False,
    migration_required: bool = False,
    delta_path: str = "flags.package_prayed",
) -> Path:
    module_path = root / "gameplay_modules" / module_id
    module_path.joinpath("action_mods").mkdir(parents=True, exist_ok=True)
    module_path.joinpath("docs").mkdir(exist_ok=True)
    module_path.joinpath("gameplay_module.yaml").write_text(
        f"""
id: {module_id}
name: {module_id}
version: 0.1.0
module_type: action_pack
engine_version_min: 0.1.0
schema_version: "0.6"
dependencies: {dependencies or []}
conflicts: {conflicts or []}
provided_actions:
  - id: {module_id}.pray
    action_type: {module_id}.pray
state_schema_extensions:
  - path_prefix: module_state.{module_id}.enabled
    default_value: false
event_types:
  - id: {module_id}.pray.resolved
    visible_to_player_by_default: true
permissions:
  execute_code: {str(execute_code).lower()}
  access_network: false
  access_filesystem: false
  call_llm: false
  modify_game_state_directly: false
save_compatibility:
  safe_to_add_mid_save: true
  migration_required: {str(migration_required).lower()}
  requires_new_game: false
  migration_defaults: {{}}
quality_tests: [action_mod_validation, hidden_leak_suite, module_regression]
""",
        encoding="utf-8",
    )
    module_path.joinpath("action_mods", "actions.yaml").write_text(
        f"""
actions:
  - id: {module_id}.pray
    label: Pray
    aliases: [pray]
    category: general
    outcomes:
      success:
        success_level: success
        reason: Safe integrated action.
        state_delta_templates:
          - operation: set
            path: {delta_path}
            value: true
    event_type: {module_id}.pray.resolved
""",
        encoding="utf-8",
    )
    module_path.joinpath("docs", "README.md").write_text("# Safe Module\n", encoding="utf-8")
    return module_path
