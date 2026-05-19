import json
import re
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.api import (
    AuthoringCreateWorldRequest,
    AuthoringCreateWorldResponse,
    AuthoringFileListResponse,
    AuthoringMapGraphRequest,
    AuthoringMapGraphResponse,
    AuthoringMapPreviewResponse,
    AuthoringMapWriteResponse,
    AuthoringFilePreviewResponse,
    AuthoringFileResponse,
    AuthoringDraftFileRequest,
    AuthoringFileWriteRequest,
    AuthoringFileWriteResponse,
    WorldBranchCreateRequest,
    WorldBranchCreateResponse,
    WorldBranchListResponse,
    WorldDiffDraftRequest,
    WorldDiffResponse,
    AuthoringModListResponse,
    AuthoringModDetailResponse,
    AuthoringModLoadOrderResponse,
    AuthoringModSummaryResponse,
    AuthoringModValidationResponse,
    ArchiveExportResponse,
    ArchiveImportRequest,
    ArchiveImportResponse,
    PackageDryRunResponse,
    ScenarioTemplateListResponse,
    ScenarioTemplateOutputFileResponse,
    ScenarioTemplateApplyResponse,
    ScenarioTemplatePreviewResponse,
    ScenarioTemplateRenderRequest,
    ScenarioTemplateResponse,
    RPScenarioTemplateListResponse,
    RPScenarioTemplatePreviewResponse,
    RPScenarioTemplateRenderRequest,
    RenderedScenarioTemplateFileResponse,
    RenderedScenarioTemplateResponse,
    AuthoringDiffSummaryResponse,
    AuthoringImpactAnalysisResponse,
    AuthoringValidationIssueResponse,
    AuthoringValidationResponse,
    AuthoringWorldDetailResponse,
    AuthoringWorldListResponse,
    AuthoringWorldSummaryResponse,
    ItemEconomyAuthoringRequest,
    ItemEconomyAuthoringResponse,
    ItemEconomyAuthoringPreviewResponse,
    ItemEconomyAuthoringSaveResponse,
    RumorCrimeConsequenceAuthoringRequest,
    RumorCrimeConsequenceAuthoringResponse,
    RumorCrimeConsequencePreviewResponse,
    RumorCrimeConsequenceSaveResponse,
    ValidationGraphResponse,
    DeleteSaveResponse,
    GameInputRequest,
    GameInputResponse,
    GameStateResponse,
    DebugEventListResponse,
    DebugEventResponse,
    DebugNPCSimulationDetailResponse,
    DebugNPCSimulationDryRunResponse,
    DebugNPCSimulationListResponse,
    DebugNPCSimulationSummaryResponse,
    DebugNPCSimulationTickListResponse,
    NPCBehaviorTimelineEntryResponse,
    NPCBehaviorTimelineResponse,
    TimelineReplayResponse,
    DebugPerformanceRecentResponse,
    DebugPerformanceSampleResponse,
    DebugPerformanceSummaryEntryResponse,
    DebugPerformanceSummaryResponse,
    DialogueContinueRequest,
    DialogueContextResponse,
    DialogueEndRequest,
    DialogueModeResponse,
    DialogueSessionResponse,
    DialogueStartRequest,
    GroupDialogueEndRequest,
    GroupDialogueNextSpeakerRequest,
    GroupDialogueSceneModeResponse,
    GroupDialogueSceneResponse,
    GroupDialogueStartRequest,
    GroupParticipantContextResponse,
    LoadGameResponse,
    MigrationHistoryEntryResponse,
    MigrationInfoResponse,
    MigrationListResponse,
    NarrativeEvalCaseResultResponse,
    NarrativeEvalRecentResponse,
    NarrativeEvalReportResponse,
    NPCGoalAuthoringGraphRequest,
    NPCGoalAuthoringGraphResponse,
    NPCGoalAuthoringPreviewResponse,
    NPCGoalAuthoringSaveResponse,
    NPCSimulationPresetApplyRequest,
    NPCSimulationPresetListResponse,
    NPCSimulationPresetPreviewResponse,
    NPCSimulationPresetResponse,
    PlaytestRecentResponse,
    PlaytestReportResponse,
    PlaytestRunRequest,
    PromptProfileListResponse,
    PromptProfileResponse,
    RPPromptProfileResponse,
    PromptProfileSelectRequest,
    PromptProfileTemperatureOverridesResponse,
    QuestGraphPreviewRequest,
    QuestGraphPreviewResponse,
    QuestGraphResponse,
    QuestGraphScenarioDraftResponse,
    QuestGraphSaveResponse,
    SaveGameResponse,
    SaveListResponse,
    SaveMigrationResponse,
    SaveMigrationStatusResponse,
    SaveSummaryResponse,
    SocialAuthoringGraphRequest,
    SocialAuthoringGraphResponse,
    SocialAuthoringPreviewResponse,
    SocialAuthoringSaveResponse,
    StartGameRequest,
    StartGameResponse,
    StudioConfigSummaryResponse,
    StudioPlaytestSummaryResponse,
    StudioStatusResponse,
    StudioValidationSummaryResponse,
)
from app.config import get_settings
from app.core.event_log import Event
from app.core.state_delta import StateDelta
from app.core.instrumentation import (
    get_performance_recorder,
    performance_logging_enabled,
    set_performance_logging_enabled,
)
from app.core.timeline_replay import TimelineReplay, build_timeline_replay, replay_dry_run
from app.core.world_state import CURRENT_GAME_STATE_SCHEMA_VERSION
from app.core.world_state import GameState
from app.db.migrations import CURRENT_ENGINE_VERSION
from app.db.models import SaveGame
from app.db.migration_service import MigrationService
from app.db.repository import SaveRepositoryError, SQLiteSaveRepository
from app.db.save_service import SaveService
from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.authoring_boundary import (
    AuthoringBoundaryCheckRequest,
    AuthoringBoundaryCheckResponse,
    check_authoring_boundary,
    default_authoring_boundary_policy,
)
from app.engine.content.authoring_workflows import (
    AuthoringWorkflowError,
    AuthoringWorkflowPresetList,
    list_authoring_workflow_presets,
)
from app.engine.content.batch_character_card_import import (
    BatchCharacterCardImportReport,
    BatchCharacterCardImportRequest,
    apply_batch_character_card_import_draft,
    export_batch_character_card_pack,
    preview_batch_character_card_import,
)
from app.engine.content.batch_lorebook_classification import (
    BatchLorebookClassificationReport,
    BatchLorebookClassificationRequest,
    apply_batch_lorebook_classification_draft,
    preview_batch_lorebook_classification,
)
from app.engine.content.authoring_project_dashboard import (
    AuthoringProjectSummary,
    build_authoring_project_summary,
)
from app.engine.content.character_pack_builder import (
    CharacterPack,
    CharacterPackError,
    CharacterPackExportRequest,
    CharacterPackImportPreview,
    CharacterPackImportRequest,
    apply_character_pack_import,
    export_character_pack,
    import_character_pack_dry_run,
)
from app.engine.content.import_export_profiles import (
    ImportExportProfileCatalog,
    apply_export_profile_to_character_pack,
    get_export_profile,
    get_import_export_profile_catalog,
    get_import_profile,
    validate_character_pack_import_profile,
    character_pack_export_request_for_profile,
)
from app.engine.content.content_diff_review import (
    ContentDiffReview,
    ContentDiffReviewRequest,
    ContentDiffReviewService,
)
from app.engine.content.draft_history import (
    AuthoringDraftCompareRequest,
    AuthoringDraftHistory,
    AuthoringDraftHistoryError,
    AuthoringDraftHistoryService,
    AuthoringDraftRestoreResponse,
    AuthoringDraftSnapshot,
    AuthoringDraftSnapshotRequest,
)
from app.engine.content.world_branching import WorldBranchService
from app.engine.content.world_merge import (
    WorldMergeDraft,
    WorldMergePreviewRequest,
    WorldMergeSaveRequest,
    WorldMergeService,
)
from app.engine.content.import_export import ImportExportError, ImportExportService
from app.engine.content.local_content_library import (
    LocalContentLibrary,
    LocalContentLibraryError,
    LocalContentLibraryExportRequest,
    LocalContentLibraryImportRequest,
    LocalContentLibraryItem,
    LocalContentLibraryService,
    LocalContentLibraryDuplicateRequest,
    LocalContentLibrarySearchRequest,
    LocalContentLibraryBatchValidateRequest,
    LocalContentType,
)
from app.engine.content.item_economy_authoring import (
    ItemEconomyAuthoring,
    ItemEconomyAuthoringError,
    balance_check_item_economy_authoring,
    parse_item_economy_authoring,
    preview_item_economy_authoring,
    save_item_economy_authoring,
    validate_item_economy_authoring,
)
from app.engine.content.dialogue_scene_authoring import (
    DialogueSceneAuthoring,
    DialogueSceneAuthoringError,
    DialogueScenePreview,
    DialogueSceneSaveResponse,
    parse_dialogue_scene_authoring,
    preview_dialogue_scene_authoring,
    save_dialogue_scene_authoring,
    validate_dialogue_scene_authoring,
)
from app.engine.content.group_rp_scene_authoring import (
    GroupRPSceneAuthoring,
    GroupRPSceneAuthoringError,
    GroupRPScenePreview,
    GroupRPSceneSaveResponse,
    parse_group_rp_scene_authoring,
    preview_group_rp_scene_authoring,
    save_group_rp_scene_authoring,
    validate_group_rp_scene_authoring,
)
from app.engine.content.rumor_crime_authoring import (
    RumorCrimeAuthoringError,
    RumorCrimeConsequenceAuthoring,
    parse_rumor_crime_authoring,
    preview_rumor_crime_authoring,
    save_rumor_crime_authoring,
    validate_rumor_crime_authoring,
)
from app.engine.content.rp_character_authoring import (
    RPCharacterAuthoring,
    RPCharacterAuthoringError,
    RPCharacterAuthoringPreview,
    RPCharacterAuthoringSaveResponse,
    RPCharacterImportPreviewRequest,
    RPCharacterSafeExportRequest,
    RPCharacterSafeExportResponse,
    export_safe_character_card,
    parse_rp_character_authoring,
    preview_rp_character_authoring,
    preview_rp_character_import,
    save_rp_character_authoring,
    validate_rp_character_authoring,
)
from app.engine.content.reference_index import ReferenceIndex, build_reference_index
from app.engine.content.mod_loader import ModInfo, ModLoader, ModLoaderError, ModValidationReport
from app.engine.content.npc_goal_authoring import (
    NPCGoalAuthoringError,
    NPCGoalAuthoringGraph,
    parse_npc_goal_graph,
    preview_npc_goal_graph,
    save_npc_goal_graph,
    validate_npc_goal_graph,
)
from app.engine.content.npc_simulation_presets import (
    NPCSimulationPresetError,
    NPCSimulationPresetApplyRequest as NPCSimulationPresetServiceApplyRequest,
    NPCSimulationPresetPreview,
    apply_npc_simulation_preset_to_draft,
    list_npc_simulation_presets,
    preview_npc_simulation_preset,
)
from app.engine.content.npc_pack_generator import (
    NPCPackGeneratorApplyRequest,
    NPCPackGeneratorDraft,
    NPCPackGeneratorError,
    NPCPackGeneratorExportRequest,
    NPCPackGeneratorPreview,
    apply_npc_pack_generator,
    export_npc_pack_generator,
    preview_npc_pack_generator,
    validate_npc_pack_generator,
)
from app.engine.content.quest_pack_generator import (
    QuestPackGeneratorApplyRequest,
    QuestPackGeneratorDraft,
    QuestPackGeneratorError,
    QuestPackGeneratorPreview,
    apply_quest_pack_generator,
    preview_quest_pack_generator,
    validate_quest_pack_generator,
)
from app.engine.content.location_cluster_templates import (
    LocationClusterPreview,
    LocationClusterPreviewRequest,
    LocationClusterTemplateError,
    LocationClusterTemplateList,
    apply_location_cluster_draft,
    list_location_cluster_templates,
    preview_location_cluster,
)
from app.engine.content.mystery_templates import (
    MysteryTemplateError,
    MysteryTemplateList,
    MysteryTemplatePreview,
    MysteryTemplatePreviewRequest,
    apply_mystery_template,
    list_mystery_templates,
    preview_mystery_template,
)
from app.engine.content.faction_templates import (
    FactionTemplateError,
    FactionTemplateList,
    FactionTemplatePreview,
    FactionTemplatePreviewRequest,
    apply_faction_template,
    list_faction_templates,
    preview_faction_template,
)
from app.engine.content.content_batch_validator import (
    ContentBatchValidationReport,
    ContentBatchValidationRequest,
    validate_content_batch,
)
from app.engine.content.script_package_builder import (
    ScriptPackageBuildReport,
    ScriptPackageBuildRequest,
    ScriptPackageBuilderError,
    build_script_package,
    build_script_package_dry_run,
    export_script_package,
    validate_script_package,
)
from app.engine.content.campaign_starter_kit import (
    CampaignStarterKitBuildRequest,
    CampaignStarterKitDraft,
    CampaignStarterKitError,
    CampaignStarterKitPreview,
    build_campaign_starter_kit,
    export_campaign_starter_script_package,
    preview_campaign_starter_kit,
)
from app.engine.content.production_pipeline_dashboard import (
    ProductionPipelineSummary,
    build_production_pipeline_summary,
)
from app.engine.content.scenario_templates import (
    RenderedTemplate,
    ScenarioTemplate,
    ScenarioTemplateError,
    ScenarioTemplatePreview,
    ScenarioTemplateRenderer,
)
from app.engine.content.template_wizard import (
    TemplateWizardApplyRequest,
    TemplateWizardDraft,
    TemplateWizardError,
    TemplateWizardPreview,
    apply_template_wizard_draft,
    preview_template_wizard_draft,
    validate_template_wizard_draft,
)
from app.engine.content.world_pack_wizard import (
    WorldPackWizard,
    WorldPackWizardApplyRequest,
    WorldPackWizardDraft,
    WorldPackWizardError,
    WorldPackWizardPreview,
)
from app.engine.content.quest_graph import (
    QuestGraph,
    QuestGraphError,
    generate_scenario_regression_draft,
    parse_quest_graph,
    preview_quest_graph,
    save_quest_graph,
    validate_quest_graph,
)
from app.engine.content.social_graph_authoring import (
    SocialAuthoringGraph,
    SocialGraphAuthoringError,
    parse_social_authoring_graph,
    preview_social_authoring_graph,
    save_social_authoring_graph,
    validate_social_authoring_graph,
)
from app.engine.content.validator import ValidationReport
from app.engine.content.validation_graph import ValidationGraph, build_validation_graph
from app.engine.content.world_loader import WorldLoaderError
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.time import format_game_time
from app.engine.rules.npc_simulation_tick import run_npc_simulation_tick
from app.evals.narrative_quality import (
    NarrativeQualityReport,
    run_narrative_quality_evals,
    sample_narrative_quality_cases,
)
from app.engine.rules.graphs import (
    FactionGraph,
    RelationshipGraph,
    build_faction_graph,
    build_relationship_graph,
)
from app.llm.provider_base import LLMProviderError
from app.llm.provider_benchmark import (
    ProviderBenchmarkReport,
    ProviderBenchmarkRun,
    run_provider_benchmark,
)
from app.llm.provider_router import (
    ProviderRouter,
    ProviderRoutingConfig,
    ProviderRoutingDecision,
    ProviderRoutingRule,
    ProviderRoutingValidationReport,
    get_default_provider_router,
)
from app.llm.structured_output_reliability import (
    StructuredOutputReliabilityReport,
    StructuredOutputReliabilityRun,
    run_structured_output_reliability,
)
from app.llm.usage_tracker import (
    CostLatencySummary,
    ModelUsageRecord,
    get_model_usage_store,
    set_usage_tracking_enabled,
    usage_tracking_enabled,
)
from app.llm.token_budget import (
    BudgetReport,
    TokenBudgetRequest,
    build_default_token_budget_profiles,
    estimate_token_budget,
)
from app.llm.context_inspector import (
    ContextInspectRequest,
    ContextSnapshot,
    inspect_context,
)
from app.llm.local_model_diagnostics import (
    LocalModelDiagnosticReport,
    LocalModelDiagnosticRequest,
    run_local_model_diagnostics,
)
from app.llm.model_compatibility import (
    ModelCompatibilityMatrix,
    build_model_compatibility_matrix,
)
from app.llm.narrator_style_lab import (
    NarratorStyleExperiment,
    NarratorStyleReport,
    run_narrator_style_experiment,
)
from app.llm.npc_voice_style_lab import (
    NPCVoiceStyleExperiment,
    NPCVoiceStyleReport,
    run_npc_voice_style_experiment,
)
from app.llm.prompt_ab_test import (
    PromptABTestReport,
    PromptABTestRun,
    run_prompt_ab_test,
)
from app.llm.prompt_experiment_packages import (
    PromptExperimentPackage,
    PromptExperimentPackageExportRequest,
    PromptExperimentPackageImportReport,
    PromptExperimentPackageImportRequest,
    apply_prompt_experiment_package_import,
    export_prompt_experiment_package,
    import_prompt_experiment_package_dry_run,
)
from app.llm.prompt_diff import PromptDiffReport, PromptDiffRequest, review_prompt_diff
from app.llm.prompt_regression import (
    PromptRegressionReport,
    PromptRegressionRun,
    run_prompt_regression,
)
from app.llm.prompt_profiles import (
    PromptProfile,
    PromptProfileStore,
    get_default_prompt_profile_store,
    profile_matches_settings,
    set_default_prompt_profile_store,
)
from app.llm.provider_capabilities import get_default_provider_capability_registry
from app.playtesting.runner import PlaytestOptions, PlaytestReport, run_playtest
from app.playtesting.batch import PlaytestBatchRun, PlaytestBatchRunRequest, run_playtest_batch
from app.quality.dead_end_detector import (
    DeadEndAnalysis,
    DeadEndAnalysisRequest,
    analyze_dead_ends,
)
from app.quality.economy_balance import (
    EconomyBalanceAnalysisRequest,
    EconomyBalanceReport,
    analyze_economy_balance,
)
from app.quality.combat_balance import (
    CombatBalanceAnalysisRequest,
    CombatBalanceReport,
    analyze_combat_balance,
)
from app.quality.content_coverage import (
    ContentCoverageReport,
    ContentCoverageRequest,
    analyze_content_coverage,
)
from app.quality.content_coverage_planner import (
    ContentCoveragePlan,
    ContentCoveragePlanRequest,
    build_content_coverage_plan,
)
from app.quality.benchmarks import (
    BenchmarkReport,
    BenchmarkRunRequest,
    run_benchmark_suite,
)
from app.quality.batch_quality_gate import (
    BatchQualityGateReport,
    BatchQualityGateRequest,
    run_batch_quality_gate,
)
from app.quality.branch_diff_regression import (
    BranchRegressionReport,
    BranchRegressionRequest,
    run_branch_diff_regression,
)
from app.quality.health_score import (
    WorldHealthScore,
    build_world_health_score,
    empty_world_health_score,
)
from app.quality.gate import QualityGateConfig, QualityGateResult, run_quality_gate
from app.quality.mod_compat_stress import (
    ModCompatibilityStressReport,
    ModCompatibilityStressRequest,
    run_mod_compatibility_stress,
)
from app.quality.npc_behavior_coverage import (
    NPCBehaviorCoverageReport,
    NPCBehaviorCoverageRequest,
    analyze_npc_behavior_coverage,
)
from app.quality.npc_simulation_quality import analyze_npc_simulation_quality_for_world
from app.quality.quest_analysis import (
    QuestCompletionAnalysis,
    QuestCompletionAnalysisRequest,
    analyze_quest_completion,
)
from app.quality.schedule_conflict_detector import (
    ScheduleConflictAnalysisRequest,
    ScheduleConflictReport,
    analyze_schedule_conflicts,
)
from app.quality.social_consequence_coverage import (
    SocialConsequenceCoverageReport,
    SocialConsequenceCoverageRequest,
    analyze_social_consequence_coverage,
)
from app.quality.reports import WorldQualityReport, world_quality_report_from_validation_report
from app.roleplay.character_cards import (
    CharacterCardApplyReport,
    CharacterCardApplyRequest,
    CharacterCardImport,
    CharacterCardImportError,
    CharacterCardImportReport,
    apply_character_card_import,
    preview_character_card_import,
    validate_character_card_import,
)
from app.roleplay.lorebooks import (
    LorebookApplyReport,
    LorebookApplyRequest,
    LorebookImport,
    LorebookImportError,
    LorebookImportReport,
    apply_lorebook_import,
    preview_lorebook_import,
    validate_lorebook_import,
)
from app.roleplay.tavern_compat import (
    TavernCompatibilityApplyReport,
    TavernCompatibilityApplyRequest,
    TavernCompatibilityError,
    TavernCompatibilityExportRequest,
    TavernCompatibilityImportRequest,
    TavernCompatibilityReport,
    apply_tavern_import,
    export_tavern_resource,
    preview_tavern_import,
)
from app.roleplay.example_dialogues import (
    ExampleDialogueDraftRequest,
    ExampleDialogueListResponse,
    ExampleDialoguePreviewResponse,
    ExampleDialogueSaveResponse,
    list_example_dialogues,
    preview_example_dialogues,
    save_example_dialogues,
    validate_example_dialogues,
)
from app.roleplay.rp_scenario_templates import (
    RPScenarioTemplate,
    RPScenarioTemplateError,
    RPScenarioTemplatePreview,
    RPScenarioTemplateRenderer,
)
from app.roleplay.dialogue import (
    DialogueManager,
    DialogueMode,
    DialogueSession,
    DialogueContext,
    GroupDialogueManager,
    GroupDialogueScene,
    GroupParticipantContext,
)
from app.scenarios.regression import (
    ScenarioRegressionListResponse,
    ScenarioRegressionRun,
    ScenarioRegressionRunRequest,
    sample_scenario_regression_cases,
    run_scenario_regression_suite,
)
from app.scenarios.authoring import (
    ScenarioAuthoringError,
    ScenarioAuthoringListResponse,
    ScenarioAuthoringPreviewRequest,
    ScenarioAuthoringPreviewResponse,
    ScenarioAuthoringSaveResponse,
    ScenarioAuthoringService,
    _scenario_validation_response,
)
from app.session_store import InMemorySessionStore, build_visible_state


def _sqlite_path_from_url(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        return database_url.removeprefix("sqlite:///")
    if database_url.startswith("sqlite://"):
        return database_url.removeprefix("sqlite://")
    return database_url


settings = get_settings()
set_performance_logging_enabled(settings.enable_perf_logging)
set_usage_tracking_enabled(settings.enable_usage_tracking)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.state.session_store = InMemorySessionStore()
app.state.save_repository = SQLiteSaveRepository(_sqlite_path_from_url(settings.database_url))
app.state.narrative_eval_reports = []
app.state.playtest_reports = []
app.state.playtest_batch_reports = []
app.state.benchmark_reports = []
app.state.provider_benchmark_reports = []
app.state.structured_output_reports = []
app.state.prompt_ab_test_reports = []
app.state.narrator_style_reports = []
app.state.npc_voice_style_reports = []
app.state.world_health_scores = []
app.state.content_coverage_reports = []
app.state.branch_regression_reports = []
app.state.mod_compat_stress_reports = []
app.state.quality_gate_results = []
app.state.scenario_template_renderer = ScenarioTemplateRenderer()
app.state.prompt_profile_store = get_default_prompt_profile_store()
app.state.dialogue_manager = DialogueManager()
app.state.group_dialogue_manager = GroupDialogueManager()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


@app.get("/studio/status", response_model=StudioStatusResponse)
def get_studio_status() -> StudioStatusResponse:
    sync_runtime_settings()
    active_settings = getattr(app.state, "settings", settings)
    authoring_service = get_authoring_service()
    worlds = authoring_service.list_worlds()
    recent_saves: list[SaveSummaryResponse] = []
    try:
        recent_saves = [_save_summary_response(save) for save in get_save_repository().list_saves()[:5]]
    except SaveRepositoryError:
        recent_saves = []

    validation_summaries: list[StudioValidationSummaryResponse] = []
    for world in worlds:
        try:
            report = authoring_service.validate_world(world.world_id)
            validation_summaries.append(
                StudioValidationSummaryResponse(
                    world_id=world.world_id,
                    ok=report.ok,
                    error_count=len(report.errors),
                    warning_count=len(report.warnings),
                )
            )
        except Exception:
            validation_summaries.append(
                StudioValidationSummaryResponse(
                    world_id=world.world_id,
                    ok=False,
                    error_count=1,
                    warning_count=0,
                )
            )

    playtest_reports = get_playtest_reports()
    latest_playtest = playtest_reports[-1] if playtest_reports else None

    return StudioStatusResponse(
        engine_version=CURRENT_ENGINE_VERSION,
        schema_version=CURRENT_GAME_STATE_SCHEMA_VERSION,
        backend_status="ok",
        worlds_count=len(worlds),
        recent_saves=recent_saves,
        authoring_api_enabled=bool(active_settings.enable_authoring_api),
        debug_api_enabled=bool(active_settings.enable_debug_api),
        performance_logging_enabled=performance_logging_enabled(),
        llm_provider=active_settings.llm_provider,
        local_model_provider_status=_local_model_provider_status(active_settings),
        validation_summaries=validation_summaries,
        playtest_summary=StudioPlaytestSummaryResponse(
            available=playtest_api_enabled(),
            recent_runs=len(playtest_reports),
            latest_status=_playtest_status_label(latest_playtest) if latest_playtest else None,
        ),
    )


def _local_model_provider_status(active_settings: object) -> str | None:
    provider = str(getattr(active_settings, "llm_provider", "mock")).lower()
    if provider == "local_stub":
        return "local_stub ready"
    if provider == "local_http":
        base_url = getattr(active_settings, "local_llm_base_url", None)
        if not base_url:
            return "missing LOCAL_LLM_BASE_URL"
        json_mode = "json_mode=on" if getattr(active_settings, "local_llm_json_mode", True) else "json_mode=off"
        return f"configured ({json_mode})"
    return None


def _playtest_status_label(report: PlaytestReportResponse | None) -> str | None:
    if report is None:
        return None
    if report.errors or report.invariant_violations or report.visibility_leaks or report.save_load_failures:
        return "issues found"
    return "passed"


@app.get("/studio/config-summary", response_model=StudioConfigSummaryResponse)
def get_studio_config_summary() -> StudioConfigSummaryResponse:
    sync_runtime_settings()
    active_settings = getattr(app.state, "settings", settings)
    provider = str(active_settings.llm_provider).strip().lower()
    prompt_store = get_prompt_profile_store()
    return StudioConfigSummaryResponse(
        llm_provider=provider,
        provider_status=_provider_status_label(active_settings),
        provider_sends_prompts_off_machine=provider in {"openai", "local_http"},
        authoring_api_enabled=bool(active_settings.enable_authoring_api),
        debug_api_enabled=bool(active_settings.enable_debug_api),
        performance_logging_enabled=performance_logging_enabled(),
        playtest_api_enabled=playtest_api_enabled(),
        eval_api_enabled=bool(getattr(active_settings, "enable_eval_api", False) or active_settings.enable_debug_api),
        database_configured=bool(active_settings.database_url),
        database_path_hint=_redacted_database_hint(active_settings.database_url),
        api_key_configured=bool(active_settings.llm_api_key),
        selected_prompt_profile_id=prompt_store.selected_profile_id(),
        prompt_profiles=[
            _prompt_profile_response(profile, active_settings)
            for profile in prompt_store.list_profiles()
        ],
        privacy_notes=[
            "GameState, saves, memory records, and content packs are stored locally.",
            "Only the configured LLM provider may receive prompts; API keys are never returned by this endpoint.",
            "Prompt profiles may adjust style and temperature but cannot add hidden facts or change GameState authority.",
            "Authoring, debug, performance, playtest, and eval APIs are local studio tools.",
            "Mods are validated as local YAML/content packages and are not executed as code.",
        ],
    )


@app.get("/studio/prompt-profiles", response_model=PromptProfileListResponse)
def list_prompt_profiles() -> PromptProfileListResponse:
    sync_runtime_settings()
    active_settings = getattr(app.state, "settings", settings)
    store = get_prompt_profile_store()
    return PromptProfileListResponse(
        selected_profile_id=store.selected_profile_id(),
        profiles=[_prompt_profile_response(profile, active_settings) for profile in store.list_profiles()],
    )


@app.post("/studio/prompt-profiles/select", response_model=PromptProfileListResponse)
def select_prompt_profile(request: PromptProfileSelectRequest) -> PromptProfileListResponse:
    sync_runtime_settings()
    active_settings = getattr(app.state, "settings", settings)
    store = get_prompt_profile_store()
    try:
        store.select_profile(request.profile_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    set_default_prompt_profile_store(store)
    return PromptProfileListResponse(
        selected_profile_id=store.selected_profile_id(),
        profiles=[_prompt_profile_response(profile, active_settings) for profile in store.list_profiles()],
    )


@app.get("/authoring/pro/boundary")
def get_authoring_pro_boundary() -> dict[str, object]:
    require_authoring_api()
    return default_authoring_boundary_policy().model_dump(mode="json")


@app.post("/authoring/pro/boundary/check", response_model=AuthoringBoundaryCheckResponse)
def check_authoring_pro_boundary(
    request: AuthoringBoundaryCheckRequest,
) -> AuthoringBoundaryCheckResponse:
    require_authoring_api()
    return check_authoring_boundary(request)


def _provider_status_label(active_settings: object) -> str:
    provider = str(getattr(active_settings, "llm_provider", "mock")).strip().lower()
    if provider == "mock":
        return "mock provider; no external LLM calls"
    if provider == "local_stub":
        return "local stub provider; no network calls"
    if provider == "local_http":
        if not getattr(active_settings, "local_llm_base_url", None):
            return "local_http missing LOCAL_LLM_BASE_URL"
        return "local_http configured; prompts are sent to the configured local endpoint"
    if provider == "openai":
        if not getattr(active_settings, "llm_api_key", None):
            return "openai selected but LLM_API_KEY is not configured"
        return "openai configured; prompts may be sent to the provider API"
    return f"unsupported provider: {provider}"


def _prompt_profile_response(profile: PromptProfile, active_settings: object) -> PromptProfileResponse:
    return PromptProfileResponse(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        provider_filter=profile.provider_filter,
        model_filter=profile.model_filter,
        narrator_style=profile.narrator_style,
        intent_parser_prompt_variant=profile.intent_parser_prompt_variant,
        narrator_prompt_variant=profile.narrator_prompt_variant,
        memory_prompt_variant=profile.memory_prompt_variant,
        temperature_overrides=PromptProfileTemperatureOverridesResponse(
            narrator=profile.temperature_overrides.narrator,
            intent_parser=profile.temperature_overrides.intent_parser,
            memory=profile.temperature_overrides.memory,
        ),
        max_output_tokens=profile.max_output_tokens,
        scene_mood_preset_id=profile.scene_mood_preset_id,
        rp_profile=RPPromptProfileResponse(
            id=profile.rp_profile.id,
            name=profile.rp_profile.name,
            description=profile.rp_profile.description,
            dialogue_depth=profile.rp_profile.dialogue_depth,
            emotional_intensity=profile.rp_profile.emotional_intensity,
            prose_density=profile.rp_profile.prose_density,
            response_length_policy=profile.rp_profile.response_length_policy,
            perspective=profile.rp_profile.perspective,
            inner_thought_policy=profile.rp_profile.inner_thought_policy,
            sensuality_policy=profile.rp_profile.sensuality_policy,
            hidden_fact_policy=profile.rp_profile.hidden_fact_policy,
            state_modification_policy=profile.rp_profile.state_modification_policy,
        ),
        enabled=profile.enabled,
        matches_current_provider=profile_matches_settings(profile, active_settings),
    )


def _redacted_database_hint(database_url: str) -> str:
    if not database_url:
        return "not configured"
    if database_url.startswith("sqlite:///") or database_url.startswith("sqlite://"):
        path = Path(_sqlite_path_from_url(database_url))
        return f"sqlite local file: {path.name or '[configured]'}"
    return "database URL configured (redacted)"


def get_session_store() -> InMemorySessionStore:
    return app.state.session_store


def get_save_repository() -> SQLiteSaveRepository:
    return app.state.save_repository


def get_migration_service() -> MigrationService:
    return MigrationService(get_save_repository())


def debug_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(active_settings.enable_debug_api)


def sync_runtime_settings() -> None:
    active_settings = getattr(app.state, "settings", settings)
    set_performance_logging_enabled(bool(active_settings.enable_perf_logging))
    set_usage_tracking_enabled(bool(getattr(active_settings, "enable_usage_tracking", False)))


def authoring_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(active_settings.enable_authoring_api)


def require_debug_api() -> None:
    sync_runtime_settings()
    if not debug_api_enabled():
        raise HTTPException(status_code=403, detail="Debug API is disabled")


def playtest_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(getattr(active_settings, "enable_playtest_api", False) or active_settings.enable_debug_api)


def scenario_regression_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(
        getattr(active_settings, "enable_playtest_api", False)
        or getattr(active_settings, "enable_eval_api", False)
        or active_settings.enable_debug_api
    )


def benchmark_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(active_settings.enable_debug_api or active_settings.enable_perf_logging or getattr(active_settings, "enable_usage_tracking", False))


def usage_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(active_settings.enable_debug_api or getattr(active_settings, "enable_usage_tracking", False))


def quality_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(
        getattr(active_settings, "enable_eval_api", False)
        or getattr(active_settings, "enable_playtest_api", False)
        or active_settings.enable_perf_logging
        or active_settings.enable_debug_api
    )


def require_playtest_api() -> None:
    sync_runtime_settings()
    if not playtest_api_enabled():
        raise HTTPException(status_code=403, detail="Playtest API is disabled")


def require_benchmark_api() -> None:
    sync_runtime_settings()
    if not benchmark_api_enabled():
        raise HTTPException(status_code=403, detail="Benchmark API is disabled")


def require_usage_api() -> None:
    sync_runtime_settings()
    if not usage_api_enabled():
        raise HTTPException(status_code=403, detail="Usage API is disabled")


def require_scenario_regression_api() -> None:
    sync_runtime_settings()
    if not scenario_regression_api_enabled():
        raise HTTPException(status_code=403, detail="Scenario regression API is disabled")


def require_quality_api() -> None:
    sync_runtime_settings()
    if not quality_api_enabled():
        raise HTTPException(status_code=403, detail="Quality API is disabled")


def _quality_api_payload(value: object) -> dict[str, Any]:
    """Serialize quality responses for normal local UI without debug-only payloads."""
    if hasattr(value, "model_dump_normal"):
        payload = value.model_dump_normal()  # type: ignore[attr-defined]
    elif hasattr(value, "model_dump"):
        payload = value.model_dump(mode="json", exclude_none=True)  # type: ignore[attr-defined]
    else:
        payload = value
    safe_payload = _strip_quality_debug_only(payload)
    return safe_payload if isinstance(safe_payload, dict) else {"value": safe_payload}


def _strip_quality_debug_only(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): _strip_quality_debug_only(item)
            for key, item in value.items()
            if str(key) != "hidden_details_debug_only" and not str(key).endswith("_debug_only")
        }
    if isinstance(value, list):
        return [_strip_quality_debug_only(item) for item in value]
    return value


def get_narrative_eval_reports() -> list[NarrativeQualityReport]:
    reports = getattr(app.state, "narrative_eval_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.narrative_eval_reports = reports
    return reports


def get_playtest_reports() -> list[PlaytestReportResponse]:
    reports = getattr(app.state, "playtest_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.playtest_reports = reports
    return reports


def get_playtest_batch_reports() -> list[PlaytestBatchRun]:
    reports = getattr(app.state, "playtest_batch_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.playtest_batch_reports = reports
    return reports


def get_benchmark_reports() -> list[BenchmarkReport]:
    reports = getattr(app.state, "benchmark_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.benchmark_reports = reports
    return reports


def get_provider_benchmark_reports() -> list[ProviderBenchmarkReport]:
    reports = getattr(app.state, "provider_benchmark_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.provider_benchmark_reports = reports
    return reports


def get_structured_output_reports() -> list[StructuredOutputReliabilityReport]:
    reports = getattr(app.state, "structured_output_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.structured_output_reports = reports
    return reports


def get_model_compatibility_reports() -> list[ModelCompatibilityMatrix]:
    reports = getattr(app.state, "model_compatibility_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.model_compatibility_reports = reports
    return reports


def get_provider_router() -> ProviderRouter:
    router = getattr(app.state, "provider_router", None)
    if not isinstance(router, ProviderRouter):
        router = get_default_provider_router()
        app.state.provider_router = router
    return router


def get_prompt_ab_test_reports() -> list[PromptABTestReport]:
    reports = getattr(app.state, "prompt_ab_test_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.prompt_ab_test_reports = reports
    return reports


def get_narrator_style_reports() -> list[NarratorStyleReport]:
    reports = getattr(app.state, "narrator_style_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.narrator_style_reports = reports
    return reports


def get_npc_voice_style_reports() -> list[NPCVoiceStyleReport]:
    reports = getattr(app.state, "npc_voice_style_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.npc_voice_style_reports = reports
    return reports


def get_prompt_regression_reports() -> list[PromptRegressionReport]:
    reports = getattr(app.state, "prompt_regression_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.prompt_regression_reports = reports
    return reports


def get_local_model_diagnostic_reports() -> list[LocalModelDiagnosticReport]:
    reports = getattr(app.state, "local_model_diagnostic_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.local_model_diagnostic_reports = reports
    return reports


def get_token_budget_reports() -> list[BudgetReport]:
    reports = getattr(app.state, "token_budget_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.token_budget_reports = reports
    return reports


def get_world_health_scores() -> list[WorldHealthScore]:
    reports = getattr(app.state, "world_health_scores", None)
    if not isinstance(reports, list):
        reports = []
        app.state.world_health_scores = reports
    return reports


def get_content_coverage_reports() -> list[ContentCoverageReport]:
    reports = getattr(app.state, "content_coverage_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.content_coverage_reports = reports
    return reports


def get_branch_regression_reports() -> list[BranchRegressionReport]:
    reports = getattr(app.state, "branch_regression_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.branch_regression_reports = reports
    return reports


def get_mod_compat_stress_reports() -> list[ModCompatibilityStressReport]:
    reports = getattr(app.state, "mod_compat_stress_reports", None)
    if not isinstance(reports, list):
        reports = []
        app.state.mod_compat_stress_reports = reports
    return reports


def get_quality_gate_results() -> list[QualityGateResult]:
    reports = getattr(app.state, "quality_gate_results", None)
    if not isinstance(reports, list):
        reports = []
        app.state.quality_gate_results = reports
    return reports


def get_scenario_regression_runs() -> list[ScenarioRegressionRun]:
    runs = getattr(app.state, "scenario_regression_runs", None)
    if not isinstance(runs, list):
        runs = []
        app.state.scenario_regression_runs = runs
    return runs


def require_authoring_api() -> None:
    if not authoring_api_enabled():
        raise HTTPException(status_code=403, detail="Authoring API is disabled")


def get_worlds_root() -> str:
    return str(getattr(app.state, "worlds_root", "worlds"))


def get_mods_root() -> str:
    return str(getattr(app.state, "mods_root", "mods"))


def get_authoring_service() -> ContentAuthoringService:
    return ContentAuthoringService(get_worlds_root())


def get_world_branch_service() -> WorldBranchService:
    return WorldBranchService(get_worlds_root())


def get_world_merge_service() -> WorldMergeService:
    return WorldMergeService(get_worlds_root())


def get_content_diff_review_service() -> ContentDiffReviewService:
    return ContentDiffReviewService(get_worlds_root())


def get_draft_history_service() -> AuthoringDraftHistoryService:
    return AuthoringDraftHistoryService(get_worlds_root())


def get_authoring_project_summary(
    world_id: str | None = None,
    branch_id: str | None = None,
) -> AuthoringProjectSummary:
    return build_authoring_project_summary(
        world_id=world_id,
        branch_id=branch_id,
        authoring_service=get_authoring_service(),
        branch_service=get_world_branch_service(),
        library_service=get_local_content_library_service(),
        quality_gate_results=get_quality_gate_results(),
    )


def get_production_pipeline_summary(world_id: str | None = None) -> ProductionPipelineSummary:
    return build_production_pipeline_summary(
        worlds_root=get_worlds_root(),
        library_service=get_local_content_library_service(),
        quality_gate_results=get_quality_gate_results(),
        active_world=world_id,
    )


def get_scenario_template_renderer() -> ScenarioTemplateRenderer:
    renderer = getattr(app.state, "scenario_template_renderer", None)
    if isinstance(renderer, ScenarioTemplateRenderer):
        return renderer
    renderer = ScenarioTemplateRenderer(worlds_root=get_worlds_root())
    app.state.scenario_template_renderer = renderer
    return renderer


def get_rp_scenario_template_renderer() -> RPScenarioTemplateRenderer:
    renderer = getattr(app.state, "rp_scenario_template_renderer", None)
    if isinstance(renderer, RPScenarioTemplateRenderer):
        return renderer
    renderer = RPScenarioTemplateRenderer()
    app.state.rp_scenario_template_renderer = renderer
    return renderer


def get_scenario_authoring_service() -> ScenarioAuthoringService:
    scenarios_root = getattr(app.state, "scenarios_root", "scenarios")
    return ScenarioAuthoringService(scenarios_root, get_worlds_root())


def get_prompt_profile_store() -> PromptProfileStore:
    store = getattr(app.state, "prompt_profile_store", None)
    if isinstance(store, PromptProfileStore):
        return store
    store = get_default_prompt_profile_store()
    app.state.prompt_profile_store = store
    return store


def get_dialogue_manager() -> DialogueManager:
    manager = getattr(app.state, "dialogue_manager", None)
    if isinstance(manager, DialogueManager):
        manager.set_prompt_profile(get_prompt_profile_store().get_selected_profile())
        return manager
    manager = DialogueManager(prompt_profile=get_prompt_profile_store().get_selected_profile())
    app.state.dialogue_manager = manager
    return manager


def get_group_dialogue_manager() -> GroupDialogueManager:
    manager = getattr(app.state, "group_dialogue_manager", None)
    if isinstance(manager, GroupDialogueManager):
        manager.set_prompt_profile(get_prompt_profile_store().get_selected_profile())
        return manager
    manager = GroupDialogueManager(prompt_profile=get_prompt_profile_store().get_selected_profile())
    app.state.group_dialogue_manager = manager
    return manager


def get_mod_loader() -> ModLoader:
    return ModLoader(get_mods_root())


def get_import_export_service() -> ImportExportService:
    return ImportExportService(
        worlds_root=get_worlds_root(),
        mods_root=get_mods_root(),
        templates_root=Path("templates"),
        repository=get_save_repository(),
    )


def get_local_content_library_service() -> LocalContentLibraryService:
    return LocalContentLibraryService(get_import_export_service())


@app.post("/game/start", response_model=StartGameResponse)
def start_game(request: StartGameRequest | None = None) -> StartGameResponse:
    world_id = request.world_id if request else None
    try:
        session_id, game_loop = get_session_store().create_session(world_id)
    except WorldLoaderError as exc:
        status_code = 404 if str(exc).startswith("World pack not found:") else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return StartGameResponse(
        session_id=session_id,
        world_id=game_loop.state.world_id,
        visible_state=build_visible_state(game_loop.state),
        turn=game_loop.state.turn,
    )


@app.post("/game/input", response_model=GameInputResponse)
def submit_game_input(request: GameInputRequest) -> GameInputResponse:
    sync_runtime_settings()
    game_loop = get_session_store().get_session(request.session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {request.session_id}")

    try:
        result = game_loop.step(request.player_input)
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GameInputResponse(
        narrative_text=result.narrative.text,
        suggested_actions=result.narrative.suggested_actions,
        visible_state=build_visible_state(result.state),
        turn=result.state.turn,
    )


@app.get("/game/state/{session_id}", response_model=GameStateResponse)
def get_game_state(session_id: str) -> GameStateResponse:
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")

    return GameStateResponse(
        session_id=session_id,
        visible_state=build_visible_state(game_loop.state),
        turn=game_loop.state.turn,
    )


@app.post("/game/dialogue/start", response_model=DialogueModeResponse)
def start_dialogue_mode(request: DialogueStartRequest) -> DialogueModeResponse:
    game_loop = get_session_store().get_session(request.game_session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {request.game_session_id}")
    try:
        mode = DialogueMode(request.dialogue_mode)
        session = get_dialogue_manager().start_dialogue(
            game_loop.state,
            game_session_id=request.game_session_id,
            focus_npc_id=request.focus_npc_id,
            dialogue_mode=mode,
            active_topics=request.active_topics,
            scene_mood_preset_id=request.scene_mood_preset_id,
            event_log=game_loop.event_log,
        )
        context = get_dialogue_manager().build_dialogue_context(
            game_loop.state,
            focus_npc_id=session.focus_npc_id,
            session=session,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _dialogue_mode_response(
        session=session,
        context=context,
        state=game_loop.state,
        narrative_text=f"Dialogue started with {session.focus_npc_id}.",
    )


@app.post("/game/dialogue/continue", response_model=DialogueModeResponse)
def continue_dialogue_mode(request: DialogueContinueRequest) -> DialogueModeResponse:
    session = get_dialogue_manager().get_session(request.dialogue_session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Unknown dialogue session: {request.dialogue_session_id}")
    if session.game_session_id is None:
        raise HTTPException(status_code=400, detail="Dialogue session is not attached to a game session")
    game_loop = get_session_store().get_session(session.game_session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session.game_session_id}")
    try:
        result = get_dialogue_manager().continue_dialogue(
            game_loop.state,
            game_loop.event_log,
            dialogue_session_id=request.dialogue_session_id,
            player_input=request.player_input,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    game_loop.state = result.state
    return _dialogue_mode_response(
        session=result.session,
        context=result.context,
        state=result.state,
        narrative_text=f"{result.session.focus_npc_id} responds within the current dialogue constraints.",
        output_ok=result.output_check.ok,
        output_issues=[issue.code for issue in result.output_check.issues],
    )


@app.post("/game/dialogue/end", response_model=DialogueModeResponse)
def end_dialogue_mode(request: DialogueEndRequest) -> DialogueModeResponse:
    session = get_dialogue_manager().get_session(request.dialogue_session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Unknown dialogue session: {request.dialogue_session_id}")
    game_loop = get_session_store().get_session(session.game_session_id) if session.game_session_id else None
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session.game_session_id}")
    ended = get_dialogue_manager().end_dialogue(request.dialogue_session_id, game_loop.state.turn)
    game_loop.event_log.append(
        Event(
            event_id=str(uuid4()),
            turn=game_loop.state.turn,
            actor_id="player",
            action_type="dialogue_end",
            target_id=ended.focus_npc_id,
            result="success",
            state_deltas=[],
            allow_empty_delta=True,
            visible_to_player=True,
            narrative_text="Dialogue ended.",
        )
    )
    context = get_dialogue_manager().build_dialogue_context(game_loop.state, focus_npc_id=ended.focus_npc_id, session=ended)
    return _dialogue_mode_response(
        session=ended,
        context=context,
        state=game_loop.state,
        narrative_text=f"Dialogue ended with {ended.focus_npc_id}.",
    )


@app.post("/game/group-dialogue/start", response_model=GroupDialogueSceneModeResponse)
def start_group_dialogue_scene(request: GroupDialogueStartRequest) -> GroupDialogueSceneModeResponse:
    game_loop = get_session_store().get_session(request.game_session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {request.game_session_id}")
    try:
        scene = get_group_dialogue_manager().start_group_scene(
            game_loop.state,
            participant_ids=request.participant_ids,
            game_session_id=request.game_session_id,
            scene_topic=request.scene_topic,
            scene_mood=request.scene_mood,
            scene_mood_preset_id=request.scene_mood_preset_id,
            active_speaker_id=request.active_speaker_id,
            event_log=game_loop.event_log,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _group_dialogue_response(
        scene=scene,
        state=game_loop.state,
        narrative_text=f"Group scene started at {scene.location_id}.",
    )


@app.post("/game/group-dialogue/next-speaker", response_model=GroupDialogueSceneModeResponse)
def select_group_dialogue_next_speaker(request: GroupDialogueNextSpeakerRequest) -> GroupDialogueSceneModeResponse:
    scene = get_group_dialogue_manager().get_scene(request.scene_id)
    if scene is None:
        raise HTTPException(status_code=404, detail=f"Unknown group dialogue scene: {request.scene_id}")
    # Group scenes are tied to live in-memory state by location and participants;
    # the active game loop is found by matching a participant location.
    game_loop = _find_group_scene_game_loop(scene)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Game session not found for group dialogue scene: {scene.scene_id}")
    try:
        get_group_dialogue_manager().select_next_speaker(
            game_loop.state,
            scene.scene_id,
            manual_focus_id=request.manual_focus_id,
            event_log=game_loop.event_log,
        )
        updated = get_group_dialogue_manager().get_scene(scene.scene_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Unknown group dialogue scene: {scene.scene_id}")
    return _group_dialogue_response(
        scene=updated,
        state=game_loop.state,
        narrative_text=f"{updated.active_speaker_id} is ready to speak.",
    )


@app.post("/game/group-dialogue/end", response_model=GroupDialogueSceneModeResponse)
def end_group_dialogue_scene(request: GroupDialogueEndRequest) -> GroupDialogueSceneModeResponse:
    scene = get_group_dialogue_manager().get_scene(request.scene_id)
    if scene is None:
        raise HTTPException(status_code=404, detail=f"Unknown group dialogue scene: {request.scene_id}")
    game_loop = _find_group_scene_game_loop(scene)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Game session not found for group dialogue scene: {scene.scene_id}")
    ended = get_group_dialogue_manager().end_group_scene(scene.scene_id, event_log=game_loop.event_log, state=game_loop.state)
    return _group_dialogue_response(
        scene=ended,
        state=game_loop.state,
        narrative_text=f"Group scene ended at {ended.location_id}.",
    )


@app.get("/game/{session_id}/graphs/relationships", response_model=RelationshipGraph)
def get_player_relationship_graph(session_id: str) -> RelationshipGraph:
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_relationship_graph(game_loop.state, debug=False)


@app.get("/game/{session_id}/graphs/factions", response_model=FactionGraph)
def get_player_faction_graph(session_id: str) -> FactionGraph:
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_faction_graph(game_loop.state, debug=False)


@app.get("/game/saves", response_model=SaveListResponse)
def list_saves(world_id: str | None = None) -> SaveListResponse:
    try:
        saves = get_save_repository().list_saves(world_id=world_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return SaveListResponse(
        saves=[
            _save_summary_response(save)
            for save in saves
        ]
    )


def _save_summary_response(save: SaveGame) -> SaveSummaryResponse:
    state = GameState.model_validate_json(save.state_json)
    location = state.locations.get(state.player.location_id)
    return SaveSummaryResponse(
        save_id=save.save_id,
        world_id=state.world_id,
        world_name=_world_name_for_state(state),
        turn=state.turn,
        current_location_name=location.name if location else state.player.location_id,
        formatted_time=format_game_time(state),
        created_at=save.created_at.isoformat(),
        updated_at=save.updated_at.isoformat(),
        player_summary=f"Turn {state.turn} at {location.name if location else state.player.location_id}",
        enabled_mods=_enabled_mods_from_save(save),
    )


def _enabled_mods_from_save(save: SaveGame) -> dict[str, str]:
    try:
        payload = json.loads(save.enabled_mods)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, list):
        return {}
    result: dict[str, str] = {}
    for item in payload:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            result[item["id"]] = str(item.get("version", "unknown"))
    return result


def _dialogue_mode_response(
    *,
    session: DialogueSession,
    context: DialogueContext,
    state: GameState,
    narrative_text: str,
    output_ok: bool = True,
    output_issues: list[str] | None = None,
) -> DialogueModeResponse:
    return DialogueModeResponse(
        dialogue_session=DialogueSessionResponse(
            session_id=session.session_id,
            save_id=session.save_id,
            game_session_id=session.game_session_id,
            participant_ids=session.participant_ids,
            focus_npc_id=session.focus_npc_id,
            started_turn=session.started_turn,
            last_turn=session.last_turn,
            dialogue_mode=session.dialogue_mode.value,
            active_topics=session.active_topics,
            scene_mood_preset_id=session.scene_mood_preset_id,
            safe_context_summary=session.safe_context_summary,
            status=session.status.value,
        ),
        dialogue_context=DialogueContextResponse(
            npc_known_facts=context.npc_known_facts,
            emotional_summary=context.emotional_summary,
            relationship_tone_summary=context.relationship_tone_summary,
            scene_mood_summary=context.scene_mood_summary,
            example_dialogue_summaries=context.example_dialogue_summaries,
            rp_memory_summaries=context.rp_memory_summaries,
            rp_prompt_style_summary=context.rp_prompt_style_summary,
            safe_context_summary=context.safe_context_summary,
        ),
        narrative_text=narrative_text,
        visible_state=build_visible_state(state),
        turn=state.turn,
        output_ok=output_ok,
        output_issues=output_issues or [],
    )


def _group_dialogue_response(
    *,
    scene: GroupDialogueScene,
    state: GameState,
    narrative_text: str,
) -> GroupDialogueSceneModeResponse:
    contexts = [
        _group_participant_context_response(get_group_dialogue_manager().build_participant_context(state, scene.scene_id, npc_id))
        for npc_id in scene.participant_ids
        if npc_id in state.npcs
    ]
    return GroupDialogueSceneModeResponse(
        scene=GroupDialogueSceneResponse(
            scene_id=scene.scene_id,
            game_session_id=scene.game_session_id,
            participant_ids=scene.participant_ids,
            location_id=scene.location_id,
            active_speaker_id=scene.active_speaker_id,
            turn_order=scene.turn_order,
            scene_topic=scene.scene_topic,
            scene_mood=scene.scene_mood,
            scene_mood_preset_id=scene.scene_mood_preset_id,
            visibility_scope=scene.visibility_scope,
            status=scene.status.value,
        ),
        participant_contexts=contexts,
        narrative_text=narrative_text,
        visible_state=build_visible_state(state),
        turn=state.turn,
    )


def _group_participant_context_response(context: GroupParticipantContext) -> GroupParticipantContextResponse:
    return GroupParticipantContextResponse(
        npc_id=context.npc_id,
        emotional_summary=context.emotional_summary,
        relationship_tone_summary=context.relationship_tone_summary,
        scene_mood_summary=context.scene_mood_summary,
        example_dialogue_summaries=context.example_dialogue_summaries,
        rp_prompt_style_summary=context.rp_prompt_style_summary,
        safe_context_summary=context.safe_context_summary,
    )


def _find_group_scene_game_loop(scene: GroupDialogueScene) -> object | None:
    if scene.game_session_id:
        return get_session_store().get_session(scene.game_session_id)
    return None


def _world_name_for_state(state: GameState) -> str:
    try:
        pack = WorldLoader(get_worlds_root()).load(state.world_id)
    except Exception:
        return state.world_id
    return pack.manifest.name


@app.post("/game/{session_id}/save", response_model=SaveGameResponse)
def save_game(session_id: str) -> SaveGameResponse:
    sync_runtime_settings()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")

    save_id = str(uuid4())
    try:
        SaveService(get_save_repository()).save_game_loop(save_id, game_loop)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return SaveGameResponse(
        save_id=save_id,
        session_id=session_id,
        world_id=game_loop.state.world_id,
        turn=game_loop.state.turn,
    )


@app.delete("/game/saves/{save_id}", response_model=DeleteSaveResponse)
def delete_save(save_id: str) -> DeleteSaveResponse:
    try:
        get_save_repository().delete_save(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DeleteSaveResponse(save_id=save_id)


@app.post("/game/load/{save_id}", response_model=LoadGameResponse)
def load_game(save_id: str) -> LoadGameResponse:
    sync_runtime_settings()
    repository = get_save_repository()
    try:
        state = repository.load_save(save_id)
        events = repository.list_events(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    session_id, game_loop = get_session_store().restore_session(state, events)
    return LoadGameResponse(
        save_id=save_id,
        session_id=session_id,
        visible_state=build_visible_state(game_loop.state),
        turn=game_loop.state.turn,
    )


@app.get("/game/saves/{save_id}/migration-status", response_model=SaveMigrationStatusResponse)
def get_save_migration_status(save_id: str) -> SaveMigrationStatusResponse:
    return _get_save_migration_status(save_id)


@app.get("/saves/{save_id}/migration-status", response_model=SaveMigrationStatusResponse)
def get_save_migration_status_alias(save_id: str) -> SaveMigrationStatusResponse:
    return _get_save_migration_status(save_id)


def _get_save_migration_status(save_id: str) -> SaveMigrationStatusResponse:
    try:
        status = get_migration_service().status(
            save_id,
            available_mod_versions={
                mod.manifest.id: mod.manifest.version
                for mod in get_mod_loader().discover_mods()
            },
        )
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SaveMigrationStatusResponse(
        save_id=status.save_id,
        engine_version=status.engine_version,
        schema_version=status.schema_version,
        world_id=status.world_id,
        world_version=status.world_version,
        content_pack_version=status.content_pack_version,
        needs_migration=status.needs_migration,
        target_schema_version=status.target_schema_version,
        migration_path=[item.migration_id for item in status.migration_path],
        warnings=status.warnings,
    )


@app.post("/game/saves/{save_id}/migrate-dry-run", response_model=SaveMigrationResponse)
def dry_run_save_migration(save_id: str) -> SaveMigrationResponse:
    return _dry_run_save_migration(save_id)


@app.post("/saves/{save_id}/migrate-dry-run", response_model=SaveMigrationResponse)
def dry_run_save_migration_alias(save_id: str) -> SaveMigrationResponse:
    return _dry_run_save_migration(save_id)


def _dry_run_save_migration(save_id: str) -> SaveMigrationResponse:
    try:
        report = get_migration_service().dry_run(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _migration_response(report)


@app.post("/game/saves/{save_id}/migrate", response_model=SaveMigrationResponse)
def migrate_save(save_id: str) -> SaveMigrationResponse:
    return _migrate_save(save_id)


@app.post("/saves/{save_id}/migrate", response_model=SaveMigrationResponse)
def migrate_save_alias(save_id: str) -> SaveMigrationResponse:
    return _migrate_save(save_id)


def _migrate_save(save_id: str) -> SaveMigrationResponse:
    try:
        report = get_migration_service().apply(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _migration_response(report)


@app.get("/migrations", response_model=MigrationListResponse)
def list_migrations() -> MigrationListResponse:
    return MigrationListResponse(
        migrations=[
            MigrationInfoResponse(
                migration_id=migration.migration_id,
                source_version=migration.source_version,
                target_version=migration.target_version,
                description=migration.description,
            )
            for migration in get_migration_service().list_available_migrations()
        ]
    )


@app.get("/debug/sessions/{session_id}/events", response_model=DebugEventListResponse)
def get_debug_session_events(session_id: str) -> DebugEventListResponse:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return DebugEventListResponse(
        events=[_debug_event_response(event) for event in game_loop.event_log.list_events()]
    )


@app.get("/debug/sessions/{session_id}/timeline", response_model=TimelineReplayResponse)
def get_debug_session_timeline(
    session_id: str,
    turn_from: int | None = None,
    turn_to: int | None = None,
    event_filter: str | None = None,
) -> TimelineReplayResponse:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    timeline = build_timeline_replay(
        game_loop.event_log.list_events(),
        source_type="session",
        source_id=session_id,
        turn_from=turn_from,
        turn_to=turn_to,
        event_filter=event_filter,
    )
    return _timeline_replay_response(timeline)


@app.get("/debug/sessions/{session_id}/graphs/relationships", response_model=RelationshipGraph)
def get_debug_relationship_graph(session_id: str) -> RelationshipGraph:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_relationship_graph(game_loop.state, debug=True)


@app.get("/debug/sessions/{session_id}/graphs/factions", response_model=FactionGraph)
def get_debug_faction_graph(session_id: str) -> FactionGraph:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_faction_graph(game_loop.state, debug=True)


@app.get("/debug/sessions/{session_id}/npc-simulation", response_model=DebugNPCSimulationListResponse)
def get_debug_npc_simulation(session_id: str) -> DebugNPCSimulationListResponse:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return DebugNPCSimulationListResponse(
        npcs=[
            _debug_npc_simulation_summary(game_loop.state, npc_id)
            for npc_id in sorted(game_loop.state.npcs)
        ]
    )


@app.get("/debug/sessions/{session_id}/npcs/{npc_id}/simulation", response_model=DebugNPCSimulationDetailResponse)
def get_debug_npc_simulation_detail(session_id: str, npc_id: str) -> DebugNPCSimulationDetailResponse:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    if npc_id not in game_loop.state.npcs:
        raise HTTPException(status_code=404, detail=f"Unknown NPC: {npc_id}")
    return _debug_npc_simulation_detail(game_loop.state, npc_id)


@app.get("/debug/sessions/{session_id}/npc-simulation/ticks", response_model=DebugNPCSimulationTickListResponse)
def get_debug_npc_simulation_ticks(session_id: str) -> DebugNPCSimulationTickListResponse:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    events = [
        event
        for event in game_loop.event_log.list_events()
        if event.action_type
        in {
            "npc_daily_replanning",
            "npc_memory_reaction",
            "npc_relationship_behavior",
            "npc_faction_duty",
            "npc_rumor_decision",
            "npc_conflict_avoidance",
            "npc_plan_built",
            "npc_plan_advanced",
            "npc_intent_enqueued",
            "npc_intents_pruned",
        }
    ]
    return DebugNPCSimulationTickListResponse(
        ticks=[_debug_event_response(event) for event in events]
    )


@app.post("/debug/sessions/{session_id}/npc-simulation/dry-run-tick", response_model=DebugNPCSimulationDryRunResponse)
def dry_run_debug_npc_simulation_tick(session_id: str) -> DebugNPCSimulationDryRunResponse:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    before = game_loop.state.model_dump(mode="json")
    result = run_npc_simulation_tick(game_loop.state)
    after = game_loop.state.model_dump(mode="json")
    return DebugNPCSimulationDryRunResponse(
        result=_redact_debug_payload(result.model_dump(mode="json")),
        state_unchanged=before == after,
    )


@app.get("/debug/sessions/{session_id}/npcs/{npc_id}/behavior-timeline", response_model=NPCBehaviorTimelineResponse)
def get_debug_session_npc_behavior_timeline(
    session_id: str,
    npc_id: str,
    turn_from: int | None = None,
    turn_to: int | None = None,
) -> NPCBehaviorTimelineResponse:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    if npc_id not in game_loop.state.npcs:
        raise HTTPException(status_code=404, detail=f"Unknown NPC: {npc_id}")
    return _npc_behavior_timeline_response(
        game_loop.event_log.list_events(),
        source_type="session",
        source_id=session_id,
        npc_id=npc_id,
        turn_from=turn_from,
        turn_to=turn_to,
    )


@app.get("/debug/saves/{save_id}/npcs/{npc_id}/behavior-timeline", response_model=NPCBehaviorTimelineResponse)
def get_debug_save_npc_behavior_timeline(
    save_id: str,
    npc_id: str,
    turn_from: int | None = None,
    turn_to: int | None = None,
) -> NPCBehaviorTimelineResponse:
    require_debug_api()
    try:
        events = get_save_repository().list_events(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _npc_behavior_timeline_response(
        events,
        source_type="save",
        source_id=save_id,
        npc_id=npc_id,
        turn_from=turn_from,
        turn_to=turn_to,
    )


@app.get("/debug/saves/{save_id}/events", response_model=DebugEventListResponse)
def get_debug_save_events(save_id: str) -> DebugEventListResponse:
    require_debug_api()
    try:
        events = get_save_repository().list_events(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DebugEventListResponse(
        events=[_debug_event_response(event) for event in events]
    )


@app.get("/debug/saves/{save_id}/timeline", response_model=TimelineReplayResponse)
def get_debug_save_timeline(
    save_id: str,
    turn_from: int | None = None,
    turn_to: int | None = None,
    event_filter: str | None = None,
) -> TimelineReplayResponse:
    require_debug_api()
    try:
        events = get_save_repository().list_events(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    timeline = build_timeline_replay(
        events,
        source_type="save",
        source_id=save_id,
        turn_from=turn_from,
        turn_to=turn_to,
        event_filter=event_filter,
    )
    return _timeline_replay_response(timeline)


@app.post("/debug/saves/{save_id}/replay-dry-run", response_model=TimelineReplayResponse)
def replay_debug_save_dry_run(save_id: str) -> TimelineReplayResponse:
    require_debug_api()
    repository = get_save_repository()
    try:
        save = repository.get_save(save_id)
        events = repository.list_events(save_id)
        initial_state = WorldLoader(get_worlds_root()).load(save.world_id).to_game_state()
    except (SaveRepositoryError, WorldLoaderError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    timeline = build_timeline_replay(events, source_type="save", source_id=save_id)
    timeline.replay_summary = replay_dry_run(initial_state, events)
    return _timeline_replay_response(timeline)


@app.get("/debug/performance/recent", response_model=DebugPerformanceRecentResponse)
def get_debug_performance_recent(limit: int = 50) -> DebugPerformanceRecentResponse:
    require_debug_api()
    recorder = get_performance_recorder()
    return DebugPerformanceRecentResponse(
        enabled=performance_logging_enabled(),
        samples=[
            DebugPerformanceSampleResponse(
                sample_id=sample.sample_id,
                name=sample.name,
                duration_ms=sample.duration_ms,
                started_at=sample.started_at.isoformat(),
                stage_durations_ms=sample.stage_durations_ms,
                tags=sample.tags,
            )
            for sample in recorder.recent(limit)
        ],
    )


@app.get("/debug/performance/summary", response_model=DebugPerformanceSummaryResponse)
def get_debug_performance_summary() -> DebugPerformanceSummaryResponse:
    require_debug_api()
    summary = get_performance_recorder().summary()
    return DebugPerformanceSummaryResponse(
        enabled=summary.enabled,
        sample_count=summary.sample_count,
        entries=[
            DebugPerformanceSummaryEntryResponse(
                name=entry.name,
                count=entry.count,
                total_duration_ms=entry.total_duration_ms,
                average_duration_ms=entry.average_duration_ms,
                max_duration_ms=entry.max_duration_ms,
            )
            for entry in summary.entries
        ],
    )


@app.get("/evals/narrative/recent", response_model=NarrativeEvalRecentResponse)
def get_recent_narrative_evals() -> NarrativeEvalRecentResponse:
    require_debug_api()
    return NarrativeEvalRecentResponse(
        reports=[_narrative_eval_report_response(report) for report in get_narrative_eval_reports()[-10:]]
    )


@app.post("/evals/narrative/run", response_model=NarrativeEvalReportResponse)
def run_narrative_evals() -> NarrativeEvalReportResponse:
    require_debug_api()
    report = run_narrative_quality_evals(sample_narrative_quality_cases())
    get_narrative_eval_reports().append(report)
    return _narrative_eval_report_response(report)


@app.get("/evals/narrative/{run_id}", response_model=NarrativeEvalReportResponse)
def get_narrative_eval(run_id: str) -> NarrativeEvalReportResponse:
    require_debug_api()
    for report in get_narrative_eval_reports():
        if report.run_id == run_id:
            return _narrative_eval_report_response(report)
    raise HTTPException(status_code=404, detail=f"Narrative eval run not found: {run_id}")


@app.get("/playtests/recent", response_model=PlaytestRecentResponse)
def get_recent_playtests() -> PlaytestRecentResponse:
    require_playtest_api()
    return PlaytestRecentResponse(reports=get_playtest_reports()[-10:])


@app.post("/playtests/run", response_model=PlaytestReportResponse)
def run_playtest_api(request: PlaytestRunRequest) -> PlaytestReportResponse:
    require_playtest_api()
    try:
        with TemporaryDirectory(prefix="llm_world_playtest_", ignore_cleanup_errors=True) as temp_dir:
            options = PlaytestOptions(
                world_id=request.world_id,
                strategy=request.agent_type,
                max_steps=request.steps,
                seed=request.seed,
                save_every=1 if request.save_load_check and request.steps > 0 else None,
                database_path=str(Path(temp_dir) / "playtest.db") if request.save_load_check else None,
                worlds_root=get_worlds_root(),
            )
            report = run_playtest(options)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorldLoaderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    response = _playtest_report_response(report, steps_requested=request.steps)
    get_playtest_reports().append(response)
    return response


@app.post("/playtests/batch/run", response_model=PlaytestBatchRun)
def run_playtest_batch_api(request: PlaytestBatchRunRequest) -> PlaytestBatchRun:
    require_playtest_api()
    try:
        report = run_playtest_batch(request, worlds_root=get_worlds_root())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorldLoaderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    get_playtest_batch_reports().append(report)
    return report


@app.get("/playtests/batch/{run_id}", response_model=PlaytestBatchRun)
def get_playtest_batch(run_id: str) -> PlaytestBatchRun:
    require_playtest_api()
    for report in get_playtest_batch_reports():
        if report.run_id == run_id:
            return report
    raise HTTPException(status_code=404, detail=f"Playtest batch run not found: {run_id}")


@app.get("/playtests/{run_id}", response_model=PlaytestReportResponse)
def get_playtest(run_id: str) -> PlaytestReportResponse:
    require_playtest_api()
    for report in get_playtest_reports():
        if report.run_id == run_id:
            return report
    raise HTTPException(status_code=404, detail=f"Playtest run not found: {run_id}")


@app.post("/quality/benchmarks/run", response_model=dict[str, Any])
def run_benchmarks_api(request: BenchmarkRunRequest) -> dict[str, Any]:
    require_benchmark_api()
    benchmark_request = request.model_copy(update={"worlds_root": get_worlds_root()})
    try:
        report = run_benchmark_suite(benchmark_request)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    get_benchmark_reports().append(report)
    return report.model_dump_safe()


@app.get("/quality/benchmarks/recent", response_model=list[dict[str, Any]])
def get_recent_benchmarks() -> list[dict[str, Any]]:
    require_benchmark_api()
    return [report.model_dump_safe() for report in get_benchmark_reports()[-10:]]


@app.post("/prompt-lab/providers/benchmark", response_model=dict[str, Any])
def run_prompt_lab_provider_benchmark(request: ProviderBenchmarkRun) -> dict[str, Any]:
    require_benchmark_api()
    active_settings = getattr(app.state, "settings", settings)
    report = run_provider_benchmark(request, settings=active_settings)
    get_provider_benchmark_reports().append(report)
    return report.model_dump_safe()


@app.get("/prompt-lab/providers/benchmark/{run_id}", response_model=dict[str, Any])
def get_prompt_lab_provider_benchmark(run_id: str) -> dict[str, Any]:
    require_benchmark_api()
    for report in get_provider_benchmark_reports():
        if report.run_id == run_id:
            return report.model_dump_safe()
    raise HTTPException(status_code=404, detail=f"Provider benchmark run not found: {run_id}")


@app.post("/prompt-lab/structured-output/run", response_model=dict[str, Any])
def run_prompt_lab_structured_output(request: StructuredOutputReliabilityRun) -> dict[str, Any]:
    require_benchmark_api()
    active_settings = getattr(app.state, "settings", settings)
    report = run_structured_output_reliability(request, settings=active_settings)
    get_structured_output_reports().append(report)
    return report.model_dump_safe()


@app.get("/prompt-lab/provider-capabilities", response_model=dict[str, Any])
def get_prompt_lab_provider_capabilities() -> dict[str, Any]:
    require_benchmark_api()
    active_settings = getattr(app.state, "settings", settings)
    return {"local_only": True, **get_default_provider_capability_registry().safe_summary_for_frontend(active_settings)}


@app.get("/prompt-lab/usage/recent", response_model=dict[str, Any])
def get_prompt_lab_usage_recent(
    limit: int = 50,
    provider_id: str | None = None,
    model_id: str | None = None,
    use_case: str | None = None,
) -> dict[str, Any]:
    require_usage_api()
    records = get_model_usage_store().recent(limit, provider_id=provider_id, model_id=model_id, use_case=use_case)
    return {
        "local_only": True,
        "enabled": usage_tracking_enabled(),
        "records": [record.safe_dict() for record in records],
    }


@app.get("/prompt-lab/usage/summary", response_model=dict[str, Any])
def get_prompt_lab_usage_summary(provider_id: str | None = None, model_id: str | None = None, use_case: str | None = None) -> dict[str, Any]:
    require_usage_api()
    summary = get_model_usage_store().summary(provider_id=provider_id, model_id=model_id, use_case=use_case)
    return {
        "local_only": True,
        **summary.model_dump(mode="json"),
    }


@app.get("/prompt-lab/usage/by-use-case", response_model=dict[str, Any])
def get_prompt_lab_usage_by_use_case(provider_id: str | None = None, model_id: str | None = None) -> dict[str, Any]:
    require_usage_api()
    summary = get_model_usage_store().summary(provider_id=provider_id, model_id=model_id)
    return {
        "local_only": True,
        "enabled": usage_tracking_enabled(),
        "by_use_case": [item.model_dump(mode="json") for item in summary.by_use_case],
    }


@app.get("/prompt-lab/model-compatibility", response_model=dict[str, Any])
def get_prompt_lab_model_compatibility() -> dict[str, Any]:
    require_benchmark_api()
    matrix = build_model_compatibility_matrix(
        benchmark_reports=get_provider_benchmark_reports(),
        structured_reports=get_structured_output_reports(),
        usage_records=get_model_usage_store().recent(500),
    )
    return {"local_only": True, **matrix.model_dump_safe()}


@app.post("/prompt-lab/model-compatibility/recompute", response_model=dict[str, Any])
def recompute_prompt_lab_model_compatibility() -> dict[str, Any]:
    require_benchmark_api()
    matrix = build_model_compatibility_matrix(
        benchmark_reports=get_provider_benchmark_reports(),
        structured_reports=get_structured_output_reports(),
        usage_records=get_model_usage_store().recent(500),
    )
    get_model_compatibility_reports().append(matrix)
    return {"local_only": True, **matrix.model_dump_safe()}


@app.get("/prompt-lab/provider-routing", response_model=dict[str, Any])
def get_prompt_lab_provider_routing() -> dict[str, Any]:
    require_benchmark_api()
    return get_provider_router().safe_summary().model_dump_safe()


@app.post("/prompt-lab/provider-routing/validate", response_model=dict[str, Any])
def validate_prompt_lab_provider_routing(rule: ProviderRoutingRule) -> dict[str, Any]:
    require_benchmark_api()
    report = get_provider_router().validate_routing_rule(rule)
    return report.model_dump_safe()


@app.post("/prompt-lab/provider-routing/preview", response_model=dict[str, Any])
def preview_prompt_lab_provider_routing(rule: ProviderRoutingRule) -> dict[str, Any]:
    require_benchmark_api()
    router = get_provider_router()
    report = router.validate_routing_rule(rule)
    decision: ProviderRoutingDecision | None = None
    if report.ok or rule.fallback_provider_id:
        try:
            preview_router = ProviderRouter(config=ProviderRoutingConfig(rules=[rule]))
            decision = preview_router.select_model_for_use_case(rule.use_case)
        except ValueError:
            decision = None
    return {
        "local_only": True,
        "validation": report.model_dump_safe(),
        "decision": decision.model_dump_safe() if decision is not None else None,
    }


@app.post("/prompt-lab/provider-routing/save", response_model=dict[str, Any])
def save_prompt_lab_provider_routing(config: ProviderRoutingConfig) -> dict[str, Any]:
    require_benchmark_api()
    summary = get_provider_router().apply_routing_config(config)
    if any(not report.ok for report in summary.validation_reports):
        raise HTTPException(status_code=400, detail=summary.model_dump_safe())
    return summary.model_dump_safe()


@app.post("/prompt-lab/context/inspect", response_model=dict[str, Any])
def inspect_prompt_lab_context(request: ContextInspectRequest) -> dict[str, Any]:
    require_benchmark_api()
    snapshot = inspect_context(request)
    return {"local_only": True, **snapshot.model_dump_safe()}


@app.post("/prompt-lab/prompt-profiles/ab-test", response_model=dict[str, Any])
def run_prompt_lab_prompt_ab_test(request: PromptABTestRun) -> dict[str, Any]:
    require_benchmark_api()
    active_settings = getattr(app.state, "settings", settings)
    report = run_prompt_ab_test(
        request,
        prompt_store=get_prompt_profile_store(),
        settings=active_settings,
    )
    get_prompt_ab_test_reports().append(report)
    return report.model_dump_safe()


@app.get("/prompt-lab/prompt-profiles/ab-test/{run_id}", response_model=dict[str, Any])
def get_prompt_lab_prompt_ab_test(run_id: str) -> dict[str, Any]:
    require_benchmark_api()
    for report in get_prompt_ab_test_reports():
        if report.run_id == run_id:
            return report.model_dump_safe()
    raise HTTPException(status_code=404, detail=f"Prompt A/B test run not found: {run_id}")


@app.post("/prompt-lab/narrator-style/run", response_model=dict[str, Any])
def run_prompt_lab_narrator_style(request: NarratorStyleExperiment) -> dict[str, Any]:
    require_benchmark_api()
    active_settings = getattr(app.state, "settings", settings)
    report = run_narrator_style_experiment(
        request,
        prompt_store=get_prompt_profile_store(),
        settings=active_settings,
    )
    get_narrator_style_reports().append(report)
    return report.model_dump_safe()


@app.get("/prompt-lab/narrator-style/{run_id}", response_model=dict[str, Any])
def get_prompt_lab_narrator_style(run_id: str) -> dict[str, Any]:
    require_benchmark_api()
    for report in get_narrator_style_reports():
        if report.run_id == run_id:
            return report.model_dump_safe()
    raise HTTPException(status_code=404, detail=f"Narrator style run not found: {run_id}")


@app.post("/prompt-lab/npc-voice-style/run", response_model=dict[str, Any])
def run_prompt_lab_npc_voice_style(request: NPCVoiceStyleExperiment) -> dict[str, Any]:
    require_benchmark_api()
    active_settings = getattr(app.state, "settings", settings)
    report = run_npc_voice_style_experiment(
        request,
        prompt_store=get_prompt_profile_store(),
        settings=active_settings,
    )
    get_npc_voice_style_reports().append(report)
    return report.model_dump_safe()


@app.get("/prompt-lab/npc-voice-style/{run_id}", response_model=dict[str, Any])
def get_prompt_lab_npc_voice_style(run_id: str) -> dict[str, Any]:
    require_benchmark_api()
    for report in get_npc_voice_style_reports():
        if report.run_id == run_id:
            return report.model_dump_safe()
    raise HTTPException(status_code=404, detail=f"NPC voice style run not found: {run_id}")


@app.post("/prompt-lab/regression/run", response_model=dict[str, Any])
def run_prompt_lab_regression(request: PromptRegressionRun) -> dict[str, Any]:
    require_benchmark_api()
    active_settings = getattr(app.state, "settings", settings)
    report = run_prompt_regression(
        request,
        prompt_store=get_prompt_profile_store(),
        settings=active_settings,
    )
    get_prompt_regression_reports().append(report)
    return report.model_dump_safe()


@app.post("/prompt-lab/prompt-diff/review", response_model=dict[str, Any])
def review_prompt_lab_prompt_diff(request: PromptDiffRequest) -> dict[str, Any]:
    require_benchmark_api()
    report = review_prompt_diff(request)
    return {"local_only": True, **report.model_dump_safe()}


@app.post("/prompt-lab/experiment-packages/export", response_model=PromptExperimentPackage)
def export_prompt_lab_experiment_package(request: PromptExperimentPackageExportRequest) -> PromptExperimentPackage:
    require_benchmark_api()
    try:
        return export_prompt_experiment_package(request, prompt_store=get_prompt_profile_store())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/prompt-lab/experiment-packages/import-dry-run", response_model=PromptExperimentPackageImportReport)
def dry_run_prompt_lab_experiment_package_import(request: PromptExperimentPackageImportRequest) -> PromptExperimentPackageImportReport:
    require_benchmark_api()
    return import_prompt_experiment_package_dry_run(request, prompt_store=get_prompt_profile_store())


@app.post("/prompt-lab/experiment-packages/import-apply", response_model=PromptExperimentPackageImportReport)
def apply_prompt_lab_experiment_package_import(request: PromptExperimentPackageImportRequest) -> PromptExperimentPackageImportReport:
    require_benchmark_api()
    return apply_prompt_experiment_package_import(request, prompt_store=get_prompt_profile_store())


@app.post("/prompt-lab/local-model/diagnose", response_model=dict[str, Any])
def run_prompt_lab_local_model_diagnostics(request: LocalModelDiagnosticRequest) -> dict[str, Any]:
    require_benchmark_api()
    active_settings = getattr(app.state, "settings", settings)
    report = run_local_model_diagnostics(request, settings=active_settings)
    get_local_model_diagnostic_reports().append(report)
    return {"local_only": True, **report.model_dump_safe()}


@app.get("/prompt-lab/token-budget/profiles", response_model=dict[str, Any])
def get_prompt_lab_token_budget_profiles() -> dict[str, Any]:
    require_benchmark_api()
    return {
        "local_only": True,
        "profiles": [profile.model_dump(mode="json") for profile in build_default_token_budget_profiles()],
    }


@app.post("/prompt-lab/token-budget/estimate", response_model=dict[str, Any])
def estimate_prompt_lab_token_budget(request: TokenBudgetRequest) -> dict[str, Any]:
    require_benchmark_api()
    report = estimate_token_budget(request)
    get_token_budget_reports().append(report)
    return {"local_only": True, **report.model_dump_safe()}


@app.get("/quality/worlds/{world_id}/health", response_model=dict[str, Any])
def get_world_health(world_id: str) -> dict[str, Any]:
    require_quality_api()
    for report in reversed(get_world_health_scores()):
        if report.world_id == world_id:
            return _quality_api_payload(report)
    return _quality_api_payload(empty_world_health_score(world_id))


@app.post("/quality/worlds/{world_id}/health/run", response_model=dict[str, Any])
def run_world_health(world_id: str) -> dict[str, Any]:
    require_quality_api()
    try:
        reports = _build_world_health_source_reports(world_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World pack not found: {world_id}") from exc
    benchmark_reports = [report for report in get_benchmark_reports() if report.world_id == world_id][-3:]
    health = build_world_health_score(world_id, reports, benchmark_reports=benchmark_reports)
    get_world_health_scores().append(health)
    return _quality_api_payload(health)


@app.get("/quality/worlds/{world_id}/coverage", response_model=dict[str, Any])
def get_content_coverage(world_id: str) -> dict[str, Any]:
    require_quality_api()
    for report in reversed(get_content_coverage_reports()):
        if report.world_id == world_id:
            return _quality_api_payload(report)
    try:
        return _quality_api_payload(analyze_content_coverage(world_id, worlds_root=get_worlds_root()))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World pack not found: {world_id}") from exc


@app.post("/quality/worlds/{world_id}/coverage/run", response_model=dict[str, Any])
def run_content_coverage(
    world_id: str,
    request: ContentCoverageRequest | None = None,
) -> dict[str, Any]:
    require_quality_api()
    request = request or ContentCoverageRequest()
    try:
        report = analyze_content_coverage(
            world_id,
            worlds_root=get_worlds_root(),
            events=request.events,
            playtest_reports=[*request.playtest_reports, *get_playtest_reports()],
            scenario_reports=[*request.scenario_reports, *get_scenario_regression_runs()],
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World pack not found: {world_id}") from exc
    get_content_coverage_reports().append(report)
    return _quality_api_payload(report)


@app.post("/production/content-coverage-plan", response_model=ContentCoveragePlan)
def plan_production_content_coverage(request: ContentCoveragePlanRequest) -> ContentCoveragePlan:
    require_authoring_api()
    try:
        return build_content_coverage_plan(request, worlds_root=get_worlds_root())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World pack not found: {request.target_world}") from exc


@app.post("/production/characters/batch-import/preview", response_model=BatchCharacterCardImportReport)
def preview_production_batch_character_cards(request: BatchCharacterCardImportRequest) -> BatchCharacterCardImportReport:
    require_authoring_api()
    try:
        return preview_batch_character_card_import(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/characters/batch-import/apply-draft", response_model=BatchCharacterCardImportReport)
def apply_production_batch_character_cards_draft(request: BatchCharacterCardImportRequest) -> BatchCharacterCardImportReport:
    require_authoring_api()
    try:
        return apply_batch_character_card_import_draft(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/characters/batch-import/export-pack", response_model=CharacterPack)
def export_production_batch_character_cards_pack(request: BatchCharacterCardImportRequest) -> CharacterPack:
    require_authoring_api()
    try:
        return export_batch_character_card_pack(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/lorebooks/batch-classify/preview", response_model=BatchLorebookClassificationReport)
def preview_production_batch_lorebooks(request: BatchLorebookClassificationRequest) -> BatchLorebookClassificationReport:
    require_authoring_api()
    try:
        return preview_batch_lorebook_classification(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/lorebooks/batch-classify/apply-draft", response_model=BatchLorebookClassificationReport)
def apply_production_batch_lorebooks_draft(request: BatchLorebookClassificationRequest) -> BatchLorebookClassificationReport:
    require_authoring_api()
    try:
        return apply_batch_lorebook_classification_draft(request, get_authoring_service())
    except (AuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/quality/worlds/{world_id}/branch-regression/run", response_model=dict[str, Any])
def run_branch_regression(
    world_id: str,
    request: BranchRegressionRequest,
) -> dict[str, Any]:
    require_quality_api()
    try:
        diff = request.diff or get_world_branch_service().diff_world(world_id, request.target_branch)
        cases = request.scenario_cases or [
            case for case in sample_scenario_regression_cases() if case.world_id == world_id
        ]
        report = run_branch_diff_regression(
            world_id=world_id,
            diff=diff,
            scenario_cases=cases,
            base_branch=request.base_branch,
            target_branch=request.target_branch,
            worlds_root=get_worlds_root(),
        )
    except (AuthoringError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    get_branch_regression_reports().append(report)
    return _quality_api_payload(report)


@app.post("/quality/mods/compatibility-stress/run", response_model=dict[str, Any])
def run_mod_compatibility_stress_api(
    request: ModCompatibilityStressRequest,
) -> dict[str, Any]:
    require_quality_api()
    try:
        report = run_mod_compatibility_stress(request, mods_root=get_mods_root())
    except ModLoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    get_mod_compat_stress_reports().append(report)
    return _quality_api_payload(report)


@app.post("/quality/worlds/{world_id}/gate/run", response_model=QualityGateResult)
def run_quality_gate_api(
    world_id: str,
    config: QualityGateConfig | None = None,
) -> QualityGateResult:
    require_quality_api()
    try:
        result = run_quality_gate(
            world_id,
            config or QualityGateConfig(),
            worlds_root=get_worlds_root(),
            mods_root=get_mods_root(),
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    get_quality_gate_results().append(result)
    return result


def _build_world_health_source_reports(world_id: str) -> list[WorldQualityReport]:
    worlds_root = get_worlds_root()
    validation_report = get_authoring_service().validate_world(world_id)
    source_reports: list[WorldQualityReport] = [
        world_quality_report_from_validation_report(validation_report),
        analyze_quest_completion(world_id, worlds_root=worlds_root).quality_report,
        analyze_dead_ends(world_id, worlds_root=worlds_root).quality_report,
        analyze_npc_behavior_coverage(world_id, worlds_root=worlds_root).quality_report,
        analyze_npc_simulation_quality_for_world(world_id, worlds_root=worlds_root).quality_report,
        analyze_economy_balance(world_id, worlds_root=worlds_root).quality_report,
        analyze_combat_balance(world_id, worlds_root=worlds_root).quality_report,
        analyze_social_consequence_coverage(world_id, worlds_root=worlds_root).quality_report,
    ]
    return [report.normal_copy() for report in source_reports]


@app.get("/quality/worlds/{world_id}/quests", response_model=dict[str, Any])
def get_quest_completion_analysis(world_id: str) -> dict[str, Any]:
    require_quality_api()
    try:
        return _quality_api_payload(analyze_quest_completion(world_id, worlds_root=get_worlds_root()))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World quest file not found: {world_id}") from exc


@app.post("/quality/worlds/{world_id}/quests/analyze", response_model=dict[str, Any])
def post_quest_completion_analysis(
    world_id: str,
    request: QuestCompletionAnalysisRequest,
) -> dict[str, Any]:
    require_quality_api()
    try:
        return _quality_api_payload(
            analyze_quest_completion(world_id, worlds_root=get_worlds_root(), coverage=request.coverage)
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World quest file not found: {world_id}") from exc


@app.post("/quality/worlds/{world_id}/dead-ends/analyze", response_model=dict[str, Any])
def post_dead_end_analysis(
    world_id: str,
    request: DeadEndAnalysisRequest,
) -> dict[str, Any]:
    require_quality_api()
    try:
        return _quality_api_payload(analyze_dead_ends(world_id, worlds_root=get_worlds_root(), coverage=request.coverage))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World pack not found: {world_id}") from exc


@app.get("/quality/worlds/{world_id}/npc-coverage", response_model=dict[str, Any])
def get_npc_behavior_coverage(world_id: str) -> dict[str, Any]:
    require_quality_api()
    try:
        return _quality_api_payload(analyze_npc_behavior_coverage(world_id, worlds_root=get_worlds_root()))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World pack not found: {world_id}") from exc


@app.post("/quality/worlds/{world_id}/npc-coverage/analyze", response_model=dict[str, Any])
def post_npc_behavior_coverage(
    world_id: str,
    request: NPCBehaviorCoverageRequest,
) -> dict[str, Any]:
    require_quality_api()
    try:
        return _quality_api_payload(
            analyze_npc_behavior_coverage(
                world_id,
                worlds_root=get_worlds_root(),
                events=request.events,
                playtest_reports=request.playtest_reports,
                scenario_reports=request.scenario_reports,
            )
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World pack not found: {world_id}") from exc


@app.post("/quality/worlds/{world_id}/schedules/analyze", response_model=dict[str, Any])
def post_schedule_conflict_analysis(
    world_id: str,
    request: ScheduleConflictAnalysisRequest,
) -> dict[str, Any]:
    require_quality_api()
    _ = request
    try:
        return _quality_api_payload(analyze_schedule_conflicts(world_id, worlds_root=get_worlds_root()))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World pack not found: {world_id}") from exc


@app.post("/quality/worlds/{world_id}/economy/analyze", response_model=dict[str, Any])
def post_economy_balance_analysis(
    world_id: str,
    request: EconomyBalanceAnalysisRequest,
) -> dict[str, Any]:
    require_quality_api()
    try:
        return _quality_api_payload(
            analyze_economy_balance(
                world_id,
                worlds_root=get_worlds_root(),
                playtest_reports=request.playtest_reports,
            )
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World pack not found: {world_id}") from exc


@app.post("/quality/worlds/{world_id}/combat/analyze", response_model=dict[str, Any])
def post_combat_balance_analysis(
    world_id: str,
    request: CombatBalanceAnalysisRequest,
) -> dict[str, Any]:
    require_quality_api()
    try:
        return _quality_api_payload(
            analyze_combat_balance(
                world_id,
                worlds_root=get_worlds_root(),
                playtest_reports=request.playtest_reports,
            )
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World pack not found: {world_id}") from exc


@app.post("/quality/worlds/{world_id}/social-consequences/analyze", response_model=dict[str, Any])
def post_social_consequence_coverage_analysis(
    world_id: str,
    request: SocialConsequenceCoverageRequest,
) -> dict[str, Any]:
    require_quality_api()
    try:
        return _quality_api_payload(
            analyze_social_consequence_coverage(
                world_id,
                worlds_root=get_worlds_root(),
                events=request.events,
                playtest_reports=request.playtest_reports,
                scenario_reports=request.scenario_reports,
            )
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"World pack not found: {world_id}") from exc


@app.get("/scenarios/regression", response_model=ScenarioRegressionListResponse)
def list_scenario_regressions() -> ScenarioRegressionListResponse:
    require_scenario_regression_api()
    return ScenarioRegressionListResponse(cases=sample_scenario_regression_cases())


@app.post("/scenarios/regression/run", response_model=ScenarioRegressionRun)
def run_scenario_regressions(request: ScenarioRegressionRunRequest) -> ScenarioRegressionRun:
    require_scenario_regression_api()
    cases = sample_scenario_regression_cases()
    if request.world_id:
        cases = [case for case in cases if case.world_id == request.world_id]
    if request.scenario_ids:
        selected = set(request.scenario_ids)
        cases = [case for case in cases if case.id in selected]
    if not cases:
        raise HTTPException(status_code=404, detail="No matching scenario regression cases")
    try:
        run = run_scenario_regression_suite(cases, worlds_root=get_worlds_root())
    except WorldLoaderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    get_scenario_regression_runs().append(run)
    return run


@app.get("/scenarios/regression/{run_id}", response_model=ScenarioRegressionRun)
def get_scenario_regression(run_id: str) -> ScenarioRegressionRun:
    require_scenario_regression_api()
    for run in get_scenario_regression_runs():
        if run.run_id == run_id:
            return run
    raise HTTPException(status_code=404, detail=f"Scenario regression run not found: {run_id}")


@app.get("/authoring/scenarios", response_model=ScenarioAuthoringListResponse)
def list_authoring_scenarios() -> ScenarioAuthoringListResponse:
    require_authoring_api()
    return ScenarioAuthoringListResponse(scenarios=get_scenario_authoring_service().list_scenarios())


@app.get("/authoring/scenarios/{scenario_id}", response_model=ScenarioAuthoringPreviewResponse)
def get_authoring_scenario(scenario_id: str) -> ScenarioAuthoringPreviewResponse:
    require_authoring_api()
    try:
        scenario = get_scenario_authoring_service().get_scenario(scenario_id)
        return ScenarioAuthoringPreviewResponse(
            scenario=scenario,
            validation=_scenario_validation_response(get_scenario_authoring_service().validate_scenario(scenario)),
            writes_to_disk=False,
        )
    except ScenarioAuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/authoring/scenarios/preview", response_model=ScenarioAuthoringPreviewResponse)
def preview_authoring_scenario(request: ScenarioAuthoringPreviewRequest) -> ScenarioAuthoringPreviewResponse:
    require_authoring_api()
    return get_scenario_authoring_service().preview_scenario(request.scenario)


@app.post("/authoring/scenarios/{scenario_id}/validate", response_model=ScenarioAuthoringPreviewResponse)
def validate_authoring_scenario(
    scenario_id: str,
    request: ScenarioAuthoringPreviewRequest,
) -> ScenarioAuthoringPreviewResponse:
    require_authoring_api()
    if scenario_id != request.scenario.id:
        raise HTTPException(status_code=400, detail="Path scenario_id must match scenario.id")
    return get_scenario_authoring_service().preview_scenario(request.scenario)


@app.post("/authoring/characters/import/preview", response_model=CharacterCardImportReport)
def preview_authoring_character_card_import(request: CharacterCardImport) -> CharacterCardImportReport:
    require_authoring_api()
    try:
        return preview_character_card_import(request)
    except CharacterCardImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/characters/import/validate", response_model=CharacterCardImportReport)
def validate_authoring_character_card_import(request: CharacterCardImport) -> CharacterCardImportReport:
    require_authoring_api()
    try:
        return validate_character_card_import(request)
    except CharacterCardImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/characters/import/apply", response_model=CharacterCardApplyReport)
def apply_authoring_character_card_import(request: CharacterCardApplyRequest) -> CharacterCardApplyReport:
    require_authoring_api()
    try:
        return apply_character_card_import(request, get_authoring_service())
    except (CharacterCardImportError, AuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/lorebook/import/preview", response_model=LorebookImportReport)
def preview_authoring_lorebook_import(request: LorebookImport) -> LorebookImportReport:
    require_authoring_api()
    try:
        return preview_lorebook_import(request)
    except LorebookImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/lorebook/import/validate", response_model=LorebookImportReport)
def validate_authoring_lorebook_import(request: LorebookImport) -> LorebookImportReport:
    require_authoring_api()
    try:
        return validate_lorebook_import(request)
    except LorebookImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/lorebook/import/apply", response_model=LorebookApplyReport)
def apply_authoring_lorebook_import(request: LorebookApplyRequest) -> LorebookApplyReport:
    require_authoring_api()
    try:
        return apply_lorebook_import(request, get_authoring_service())
    except (LorebookImportError, AuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/tavern/import/preview", response_model=TavernCompatibilityReport)
def preview_authoring_tavern_import(request: TavernCompatibilityImportRequest) -> TavernCompatibilityReport:
    require_authoring_api()
    try:
        return preview_tavern_import(request)
    except (TavernCompatibilityError, CharacterCardImportError, LorebookImportError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/tavern/import/apply", response_model=TavernCompatibilityApplyReport)
def apply_authoring_tavern_import(request: TavernCompatibilityApplyRequest) -> TavernCompatibilityApplyReport:
    require_authoring_api()
    try:
        return apply_tavern_import(request, get_authoring_service())
    except (TavernCompatibilityError, CharacterCardImportError, LorebookImportError, AuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/tavern/export", response_model=TavernCompatibilityReport)
def export_authoring_tavern_resource(request: TavernCompatibilityExportRequest) -> TavernCompatibilityReport:
    require_authoring_api()
    try:
        return export_tavern_resource(request, get_authoring_service(), get_prompt_profile_store().list_profiles())
    except (TavernCompatibilityError, AuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/authoring/worlds/{world_id}/example-dialogue", response_model=ExampleDialogueListResponse)
def get_authoring_example_dialogues(world_id: str) -> ExampleDialogueListResponse:
    require_authoring_api()
    try:
        return list_example_dialogues(world_id, get_authoring_service())
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/example-dialogue/preview", response_model=ExampleDialoguePreviewResponse)
def preview_authoring_example_dialogues(
    world_id: str,
    request: ExampleDialogueDraftRequest,
) -> ExampleDialoguePreviewResponse:
    require_authoring_api()
    try:
        return preview_example_dialogues(world_id, request, get_authoring_service())
    except (AuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/example-dialogue/validate", response_model=ExampleDialoguePreviewResponse)
def validate_authoring_example_dialogues(
    world_id: str,
    request: ExampleDialogueDraftRequest,
) -> ExampleDialoguePreviewResponse:
    require_authoring_api()
    try:
        return validate_example_dialogues(world_id, request, get_authoring_service())
    except (AuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/authoring/worlds/{world_id}/example-dialogue", response_model=ExampleDialogueSaveResponse)
def save_authoring_example_dialogues(
    world_id: str,
    request: ExampleDialogueDraftRequest,
) -> ExampleDialogueSaveResponse:
    require_authoring_api()
    try:
        return save_example_dialogues(world_id, request, get_authoring_service())
    except (AuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/authoring/worlds/{world_id}/rp/characters/pro", response_model=RPCharacterAuthoring)
def get_authoring_rp_characters(world_id: str) -> RPCharacterAuthoring:
    require_authoring_api()
    try:
        return parse_rp_character_authoring(world_id, get_authoring_service())
    except (AuthoringError, RPCharacterAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/rp/characters/pro/import-preview", response_model=CharacterCardImportReport)
def preview_authoring_rp_character_import(
    world_id: str,
    request: RPCharacterImportPreviewRequest,
) -> CharacterCardImportReport:
    require_authoring_api()
    try:
        return preview_rp_character_import(request)
    except (CharacterCardImportError, RPCharacterAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/rp/characters/pro/preview", response_model=RPCharacterAuthoringPreview)
def preview_authoring_rp_characters(
    world_id: str,
    graph: RPCharacterAuthoring,
) -> RPCharacterAuthoringPreview:
    require_authoring_api()
    try:
        return preview_rp_character_authoring(world_id, graph, get_authoring_service())
    except (AuthoringError, RPCharacterAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/rp/characters/pro/validate", response_model=RPCharacterAuthoringPreview)
def validate_authoring_rp_characters(
    world_id: str,
    graph: RPCharacterAuthoring,
) -> RPCharacterAuthoringPreview:
    require_authoring_api()
    try:
        return validate_rp_character_authoring(world_id, graph, get_authoring_service())
    except (AuthoringError, RPCharacterAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/authoring/worlds/{world_id}/rp/characters/pro", response_model=RPCharacterAuthoringSaveResponse)
def save_authoring_rp_characters(
    world_id: str,
    graph: RPCharacterAuthoring,
    confirm_warnings: bool = False,
) -> RPCharacterAuthoringSaveResponse:
    require_authoring_api()
    try:
        return save_rp_character_authoring(world_id, graph, get_authoring_service(), confirm_warnings=confirm_warnings)
    except (AuthoringError, RPCharacterAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/rp/characters/pro/safe-export", response_model=RPCharacterSafeExportResponse)
def export_authoring_rp_character_safe_card(
    world_id: str,
    request: RPCharacterSafeExportRequest,
) -> RPCharacterSafeExportResponse:
    require_authoring_api()
    try:
        return export_safe_character_card(world_id, request, get_authoring_service())
    except (AuthoringError, RPCharacterAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/authoring/worlds/{world_id}/dialogue-scenes", response_model=DialogueSceneAuthoring)
def get_authoring_dialogue_scenes(world_id: str) -> DialogueSceneAuthoring:
    require_authoring_api()
    try:
        return parse_dialogue_scene_authoring(world_id, get_authoring_service())
    except (AuthoringError, DialogueSceneAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/dialogue-scenes/preview", response_model=DialogueScenePreview)
def preview_authoring_dialogue_scenes(
    world_id: str,
    graph: DialogueSceneAuthoring,
) -> DialogueScenePreview:
    require_authoring_api()
    try:
        return preview_dialogue_scene_authoring(world_id, graph, get_authoring_service())
    except (AuthoringError, DialogueSceneAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/dialogue-scenes/validate", response_model=DialogueScenePreview)
def validate_authoring_dialogue_scenes(
    world_id: str,
    graph: DialogueSceneAuthoring,
) -> DialogueScenePreview:
    require_authoring_api()
    try:
        return validate_dialogue_scene_authoring(world_id, graph, get_authoring_service())
    except (AuthoringError, DialogueSceneAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/authoring/worlds/{world_id}/dialogue-scenes", response_model=DialogueSceneSaveResponse)
def save_authoring_dialogue_scenes(
    world_id: str,
    graph: DialogueSceneAuthoring,
    confirm_warnings: bool = False,
) -> DialogueSceneSaveResponse:
    require_authoring_api()
    try:
        return save_dialogue_scene_authoring(world_id, graph, get_authoring_service(), confirm_warnings=confirm_warnings)
    except (AuthoringError, DialogueSceneAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/authoring/worlds/{world_id}/group-rp-scenes", response_model=GroupRPSceneAuthoring)
def get_authoring_group_rp_scenes(world_id: str) -> GroupRPSceneAuthoring:
    require_authoring_api()
    try:
        return parse_group_rp_scene_authoring(world_id, get_authoring_service())
    except (AuthoringError, GroupRPSceneAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/group-rp-scenes/preview", response_model=GroupRPScenePreview)
def preview_authoring_group_rp_scenes(
    world_id: str,
    graph: GroupRPSceneAuthoring,
) -> GroupRPScenePreview:
    require_authoring_api()
    try:
        return preview_group_rp_scene_authoring(world_id, graph, get_authoring_service())
    except (AuthoringError, GroupRPSceneAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/group-rp-scenes/validate", response_model=GroupRPScenePreview)
def validate_authoring_group_rp_scenes(
    world_id: str,
    graph: GroupRPSceneAuthoring,
) -> GroupRPScenePreview:
    require_authoring_api()
    try:
        return validate_group_rp_scene_authoring(world_id, graph, get_authoring_service())
    except (AuthoringError, GroupRPSceneAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/authoring/worlds/{world_id}/group-rp-scenes", response_model=GroupRPSceneSaveResponse)
def save_authoring_group_rp_scenes(
    world_id: str,
    graph: GroupRPSceneAuthoring,
    confirm_warnings: bool = False,
) -> GroupRPSceneSaveResponse:
    require_authoring_api()
    try:
        return save_group_rp_scene_authoring(world_id, graph, get_authoring_service(), confirm_warnings=confirm_warnings)
    except (AuthoringError, GroupRPSceneAuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/character-packs/export", response_model=CharacterPack)
def export_authoring_character_pack(request: CharacterPackExportRequest) -> CharacterPack:
    require_authoring_api()
    try:
        profile = get_export_profile(request.export_profile_id or "safe")
        profiled_request = character_pack_export_request_for_profile(request, profile)
        pack = export_character_pack(profiled_request, get_authoring_service())
        return apply_export_profile_to_character_pack(pack, profile)
    except (AuthoringError, CharacterPackError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/authoring/import-export-profiles", response_model=ImportExportProfileCatalog)
def list_authoring_import_export_profiles() -> ImportExportProfileCatalog:
    require_authoring_api()
    return get_import_export_profile_catalog()


@app.post("/authoring/character-packs/import-dry-run", response_model=CharacterPackImportPreview)
def dry_run_authoring_character_pack_import(request: CharacterPackImportRequest) -> CharacterPackImportPreview:
    require_authoring_api()
    try:
        profile_report = validate_character_pack_import_profile(request, get_import_profile(request.import_profile_id or "safe"))
        preview = import_character_pack_dry_run(request, get_authoring_service())
        preview.validation.errors = profile_report.errors + preview.validation.errors
        preview.validation.warnings = profile_report.warnings + preview.validation.warnings
        preview.validation.suggestions = profile_report.suggestions + preview.validation.suggestions
        return preview
    except (AuthoringError, CharacterPackError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/character-packs/import-apply", response_model=CharacterPackImportPreview)
def apply_authoring_character_pack_import(request: CharacterPackImportRequest) -> CharacterPackImportPreview:
    require_authoring_api()
    try:
        profile_report = validate_character_pack_import_profile(request, get_import_profile(request.import_profile_id or "safe"))
        if profile_report.errors:
            return CharacterPackImportPreview(
                world_id=request.world_id,
                pack_id=request.pack.manifest.pack_id,
                validation=profile_report,
                confirmation_required=False,
                applied=False,
            )
        return apply_character_pack_import(request, get_authoring_service())
    except (AuthoringError, CharacterPackError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/authoring/scenarios/{scenario_id}", response_model=ScenarioAuthoringSaveResponse)
def save_authoring_scenario(
    scenario_id: str,
    request: ScenarioAuthoringPreviewRequest,
) -> ScenarioAuthoringSaveResponse:
    require_authoring_api()
    try:
        return get_scenario_authoring_service().save_scenario(scenario_id, request.scenario)
    except ScenarioAuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _playtest_report_response(report: PlaytestReport, steps_requested: int) -> PlaytestReportResponse:
    return PlaytestReportResponse(
        run_id=f"playtest-{uuid4()}",
        created_at=datetime.now(UTC).isoformat(),
        agent_type=report.strategy,
        world_id=report.world_id,
        seed=report.seed,
        steps_requested=steps_requested,
        turns_run=report.turns_run,
        actions_taken=[action.model_dump(mode="json") for action in report.actions_taken],
        errors=[_safe_report_text(value) for value in report.errors],
        invariant_violations=[_safe_report_text(value) for value in report.invariant_violations],
        visibility_leaks=[_safe_report_text(value) for value in report.visibility_leaks],
        save_load_failures=[_safe_report_text(value) for value in report.save_load_failures],
        final_state_summary=report.final_state_summary.model_dump(mode="json"),
    )


def _safe_report_text(value: str) -> str:
    return (
        re.sub(r":forbidden:(?:\[[^\]]+\]|[^,\]\s]+)", ":forbidden:[redacted]", value)
        .replace("forbidden hidden text", "[hidden text redacted]")
        .replace("sk-", "sk-[redacted]-")
    )


def _narrative_eval_report_response(report: NarrativeQualityReport) -> NarrativeEvalReportResponse:
    return NarrativeEvalReportResponse(
        run_id=report.run_id,
        created_at=report.created_at,
        total_cases=report.total_cases,
        passed=report.passed,
        failed=report.failed,
        skipped=report.skipped,
        failure_reasons={
            case_id: [_safe_report_text(reason) for reason in reasons]
            for case_id, reasons in report.failure_reasons.items()
        },
        categories=report.categories,
        case_results=[
            NarrativeEvalCaseResultResponse(
                case_id=result.case_id,
                category=result.category,
                passed=result.passed,
                skipped=result.skipped,
                failure_reasons=[_safe_report_text(reason) for reason in result.failure_reasons],
            )
            for result in report.case_results
        ],
    )


def _debug_event_response(event: Event) -> DebugEventResponse:
    return DebugEventResponse(
        turn=event.turn,
        event_id=event.event_id,
        actor_id=event.actor_id,
        action_type=event.action_type,
        result=event.result,
        state_deltas=event.state_deltas,
        visible_to_player=event.visible_to_player,
        created_at=event.created_at.isoformat(),
    )


def _npc_behavior_timeline_response(
    events: list[Event],
    *,
    source_type: str,
    source_id: str,
    npc_id: str,
    turn_from: int | None = None,
    turn_to: int | None = None,
) -> NPCBehaviorTimelineResponse:
    entries = [
        entry
        for event in sorted(events, key=lambda item: (item.turn, item.created_at.isoformat(), item.event_id))
        if _event_turn_in_range(event, turn_from, turn_to)
        for entry in [_npc_behavior_entry(event, npc_id)]
        if entry is not None
    ]
    return NPCBehaviorTimelineResponse(
        source_type=source_type,
        source_id=source_id,
        npc_id=npc_id,
        entries=entries,
    )


def _npc_behavior_entry(event: Event, npc_id: str) -> NPCBehaviorTimelineEntryResponse | None:
    related_deltas = [
        delta
        for delta in event.state_deltas
        if delta.path.startswith(f"npcs.{npc_id}.") or delta.metadata.get("npc_id") == npc_id
    ]
    if event.target_id != npc_id and not related_deltas:
        return None
    behavior_type = _behavior_type_for_event(event, related_deltas)
    if behavior_type is None:
        return None
    intent_id = _first_delta_metadata(related_deltas, "intent_id") or _extract_id_from_event(event.event_id, "intent")
    plan_id = _first_delta_metadata(related_deltas, "plan_id") or _extract_id_from_event(event.event_id, "plan")
    location_id = _location_from_deltas(related_deltas)
    debug_reason = _first_delta_metadata(related_deltas, "reason_code") or _first_delta_metadata(related_deltas, "debug_reason")
    return NPCBehaviorTimelineEntryResponse(
        turn=event.turn,
        event_id=event.event_id,
        behavior_type=behavior_type,
        intent_id=intent_id,
        plan_id=plan_id,
        location_id=location_id,
        safe_summary=_safe_behavior_summary(event, behavior_type, location_id),
        debug_reason_redacted=_redact_behavior_reason(debug_reason),
    )


def _behavior_type_for_event(event: Event, deltas: list[StateDelta]) -> str | None:
    action = event.action_type
    if action.startswith("npc_"):
        return action.removeprefix("npc_")
    for delta in deltas:
        if delta.path.endswith(".location_id"):
            return "location"
        if ".intent_queue" in delta.path:
            return "intent"
        if ".plans" in delta.path:
            return "plan"
        if ".current_goal_id" in delta.path or ".goals" in delta.path:
            return "goal"
        if "rumor" in delta.path or "rumor" in delta.metadata.get("source", ""):
            return "rumor"
        if "crime" in delta.path or "crime" in delta.metadata.get("source", ""):
            return "crime_report"
    return None


def _safe_behavior_summary(event: Event, behavior_type: str, location_id: str | None) -> str:
    parts = [behavior_type.replace("_", " ")]
    if location_id:
        parts.append(f"location {location_id}")
    if event.result:
        parts.append(str(_redact_sensitive_text(event.result)))
    return " / ".join(parts)


def _redact_behavior_reason(value: str | None) -> str | None:
    if value is None:
        return None
    redacted = str(_redact_sensitive_text(value))
    if len(redacted) > 120:
        return f"{redacted[:117]}..."
    return redacted


def _first_delta_metadata(deltas: list[StateDelta], key: str) -> str | None:
    for delta in deltas:
        value = delta.metadata.get(key)
        if value:
            return str(value)
    return None


def _location_from_deltas(deltas: list[StateDelta]) -> str | None:
    for delta in deltas:
        if delta.path.endswith(".location_id") and isinstance(delta.value, str):
            return delta.value
    return None


def _extract_id_from_event(event_id: str, prefix: str) -> str | None:
    marker = f"{prefix}-"
    if marker not in event_id:
        return None
    return event_id.split(marker, 1)[-1] or None


def _event_turn_in_range(event: Event, turn_from: int | None, turn_to: int | None) -> bool:
    if turn_from is not None and event.turn < turn_from:
        return False
    if turn_to is not None and event.turn > turn_to:
        return False
    return True


def _debug_npc_simulation_summary(state: GameState, npc_id: str) -> DebugNPCSimulationSummaryResponse:
    npc = state.npcs[npc_id]
    known_fact_ids = sorted(set(npc.knowledge) | set(state.npc_knowledge.get(npc_id, set())))
    hidden_fact_ids = [
        fact_id
        for fact_id in known_fact_ids
        if fact_id in state.facts and not state.facts[fact_id].public and fact_id not in state.player_visible_facts
    ]
    return DebugNPCSimulationSummaryResponse(
        npc_id=npc.id,
        location_id=npc.location_id,
        alive=npc.alive,
        condition=npc.condition.value,
        intent_count=len(npc.intent_queue),
        plan_count=len(npc.plans),
        active_goal_id=npc.current_goal_id,
        known_fact_ids=known_fact_ids,
        hidden_fact_ids=hidden_fact_ids,
        debug_reason_count=sum(1 for intent in npc.intent_queue if intent.debug_reason),
    )


def _debug_npc_simulation_detail(state: GameState, npc_id: str) -> DebugNPCSimulationDetailResponse:
    npc = state.npcs[npc_id]
    summary = _debug_npc_simulation_summary(state, npc_id)
    return DebugNPCSimulationDetailResponse(
        **summary.model_dump(mode="json"),
        intent_queue=[
            _redact_debug_payload(intent.model_dump(mode="json"))
            for intent in npc.intent_queue
        ],
        plans=[
            _redact_debug_payload(plan.model_dump(mode="json"))
            for plan in npc.plans
        ],
        goals=[
            _redact_debug_payload(goal.model_dump(mode="json") if hasattr(goal, "model_dump") else {"id": str(goal)})
            for goal in npc.goals
        ],
        emotional_state=_redact_debug_payload(npc.emotional_state.model_dump(mode="json")),
        social_disposition=_redact_debug_payload(npc.social_disposition.model_dump(mode="json")),
        faction_duties=[
            _redact_debug_payload(duty.model_dump(mode="json"))
            for duty in npc.faction_duties
        ],
        relationship_behavior_summary={
            "visible_relationship_ids": sorted(
                relationship.id
                for relationship in state.relationships.values()
                if relationship.source_id == npc_id or relationship.target_id == npc_id
            ),
            "current_goal_id": npc.current_goal_id,
        },
        known_rumor_ids=sorted(rumor.id for rumor in state.rumors.values() if npc_id in rumor.known_by_npcs),
        known_crime_ids=sorted(
            crime.id
            for crime in state.crimes.values()
            if npc_id in crime.witnessed_by or f"crime:{crime.id}" in npc.knowledge
        ),
        debug_decision_reasons=[
            {"intent_id": intent.id, "debug_only_reason": intent.debug_reason}
            for intent in npc.intent_queue
            if intent.debug_reason
        ],
    )


def _redact_debug_payload(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            if lowered in {"llm_api_key", "api_key", "raw_env", "env"} or "secret" in lowered:
                redacted[key_text] = "[redacted]"
            elif lowered in {"text", "content", "narrative_text"}:
                redacted[key_text] = _redact_sensitive_text(item)
            else:
                redacted[key_text] = _redact_debug_payload(item)
        return redacted
    if isinstance(value, list):
        return [_redact_debug_payload(item) for item in value]
    if isinstance(value, str):
        return _redact_sensitive_text(value)
    return value


def _redact_sensitive_text(value: object) -> object:
    if not isinstance(value, str):
        return value
    if "sk-" in value.lower():
        return "[redacted]"
    return value


def _migration_response(report: object) -> SaveMigrationResponse:
    return SaveMigrationResponse(
        save_id=getattr(report, "save_id"),
        source_version=getattr(report, "source_version"),
        target_version=getattr(report, "target_version"),
        dry_run=getattr(report, "dry_run"),
        backup_save_id=getattr(report, "backup_save_id"),
        success=getattr(report, "success"),
        warnings=getattr(report, "warnings"),
        applied_migrations=[
            MigrationHistoryEntryResponse(
                migration_id=entry.migration_id,
                source_version=entry.source_version,
                target_version=entry.target_version,
                description=entry.description,
                applied_at=entry.applied_at,
            )
            for entry in getattr(report, "applied_migrations")
        ],
    )


@app.get("/authoring/worlds", response_model=AuthoringWorldListResponse)
def list_authoring_worlds() -> AuthoringWorldListResponse:
    require_authoring_api()
    service = get_authoring_service()
    return AuthoringWorldListResponse(
        worlds=[_authoring_world_response(world) for world in service.list_worlds()]
    )


@app.post("/authoring/worlds", response_model=AuthoringCreateWorldResponse)
def create_authoring_world(request: AuthoringCreateWorldRequest) -> AuthoringCreateWorldResponse:
    require_authoring_api()
    try:
        world, report = get_authoring_service().create_world(
            request.world_id,
            request.name,
            request.description,
            request.start_location_id,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringCreateWorldResponse(
        world=_authoring_world_response(world),
        validation=_authoring_validation_response(report),
    )


@app.get("/authoring/worlds/{world_id}/branches", response_model=WorldBranchListResponse)
def list_world_branches(world_id: str) -> WorldBranchListResponse:
    require_authoring_api()
    try:
        branches = get_world_branch_service().list_branches(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WorldBranchListResponse(world_id=world_id, branches=branches)


@app.post("/authoring/worlds/{world_id}/branches", response_model=WorldBranchCreateResponse)
def create_world_branch(world_id: str, request: WorldBranchCreateRequest) -> WorldBranchCreateResponse:
    require_authoring_api()
    try:
        branch = get_world_branch_service().create_branch(world_id, request)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WorldBranchCreateResponse(branch=branch)


@app.get("/authoring/worlds/{world_id}/diff", response_model=WorldDiffResponse)
def diff_world_branch(world_id: str, other: str) -> WorldDiffResponse:
    require_authoring_api()
    try:
        diff = get_world_branch_service().diff_world(world_id, other)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WorldDiffResponse(diff=diff)


@app.post("/authoring/worlds/{world_id}/diff-draft", response_model=WorldDiffResponse)
def diff_world_draft(world_id: str, request: WorldDiffDraftRequest) -> WorldDiffResponse:
    require_authoring_api()
    try:
        diff = get_world_branch_service().diff_draft(world_id, request)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return WorldDiffResponse(diff=diff)


@app.post("/authoring/worlds/{world_id}/merge/preview", response_model=WorldMergeDraft)
def preview_world_merge(world_id: str, request: WorldMergePreviewRequest) -> WorldMergeDraft:
    require_authoring_api()
    try:
        return get_world_merge_service().preview_merge(world_id, request)
    except (AuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/merge/validate", response_model=WorldMergeDraft)
def validate_world_merge(world_id: str, request: WorldMergePreviewRequest) -> WorldMergeDraft:
    require_authoring_api()
    try:
        return get_world_merge_service().preview_merge(world_id, request)
    except (AuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/worlds/{world_id}/merge/save", response_model=WorldMergeDraft)
def save_world_merge(world_id: str, request: WorldMergeSaveRequest) -> WorldMergeDraft:
    require_authoring_api()
    try:
        return get_world_merge_service().save_merge(world_id, request)
    except (AuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/diff/review", response_model=ContentDiffReview)
def review_authoring_content_diff(request: ContentDiffReviewRequest) -> ContentDiffReview:
    require_authoring_api()
    try:
        return get_content_diff_review_service().review(request)
    except (AuthoringError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/authoring/drafts", response_model=AuthoringDraftHistory)
def list_authoring_drafts(world_id: str | None = None) -> AuthoringDraftHistory:
    require_authoring_api()
    try:
        return get_draft_history_service().list_history(world_id)
    except AuthoringDraftHistoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/drafts/snapshot", response_model=AuthoringDraftSnapshot)
def create_authoring_draft_snapshot(request: AuthoringDraftSnapshotRequest) -> AuthoringDraftSnapshot:
    require_authoring_api()
    try:
        return get_draft_history_service().create_snapshot(request)
    except AuthoringDraftHistoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/drafts/compare", response_model=ContentDiffReview)
def compare_authoring_draft_snapshots(request: AuthoringDraftCompareRequest) -> ContentDiffReview:
    require_authoring_api()
    try:
        return get_draft_history_service().compare_snapshots(request)
    except (AuthoringDraftHistoryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/drafts/{draft_id}/restore", response_model=AuthoringDraftRestoreResponse)
def restore_authoring_draft_snapshot(draft_id: str) -> AuthoringDraftRestoreResponse:
    require_authoring_api()
    try:
        return get_draft_history_service().restore_snapshot(draft_id)
    except AuthoringDraftHistoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/authoring/drafts/{draft_id}", response_model=AuthoringDraftHistory)
def discard_authoring_draft_snapshot(draft_id: str) -> AuthoringDraftHistory:
    require_authoring_api()
    try:
        return get_draft_history_service().discard_snapshot(draft_id)
    except AuthoringDraftHistoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/authoring/workflow-presets", response_model=AuthoringWorkflowPresetList)
def get_authoring_workflow_presets() -> AuthoringWorkflowPresetList:
    require_authoring_api()
    try:
        return list_authoring_workflow_presets()
    except AuthoringWorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/authoring/project-summary", response_model=AuthoringProjectSummary)
def read_authoring_project_summary(
    world_id: str | None = None,
    branch_id: str | None = None,
) -> AuthoringProjectSummary:
    require_authoring_api()
    try:
        return get_authoring_project_summary(world_id=world_id, branch_id=branch_id)
    except (AuthoringError, ImportExportError, LocalContentLibraryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/production/pipeline-summary", response_model=ProductionPipelineSummary)
def read_production_pipeline_summary(world_id: str | None = None) -> ProductionPipelineSummary:
    require_authoring_api()
    try:
        return get_production_pipeline_summary(world_id=world_id)
    except (AuthoringError, ImportExportError, LocalContentLibraryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/batch-quality-gate", response_model=BatchQualityGateReport)
def run_production_batch_quality_gate(request: BatchQualityGateRequest) -> BatchQualityGateReport:
    require_authoring_api()
    try:
        return run_batch_quality_gate(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/authoring/worlds/{world_id}/references", response_model=ReferenceIndex)
def get_authoring_reference_index(world_id: str) -> ReferenceIndex:
    require_authoring_api()
    try:
        return build_reference_index(
            world_id,
            worlds_root=get_worlds_root(),
            prompt_profile_store=get_prompt_profile_store(),
        )
    except (WorldLoaderError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/authoring/worlds/{world_id}", response_model=AuthoringWorldDetailResponse)
def get_authoring_world(world_id: str) -> AuthoringWorldDetailResponse:
    require_authoring_api()
    service = get_authoring_service()
    try:
        world = service.get_world_summary(world_id)
        report = service.validate_world(world_id)
        files = service.list_files(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthoringWorldDetailResponse(
        world=_authoring_world_response(world),
        files=files,
        validation=_authoring_validation_response(report),
    )


@app.get("/authoring/worlds/{world_id}/files", response_model=AuthoringFileListResponse)
def list_authoring_files(world_id: str) -> AuthoringFileListResponse:
    require_authoring_api()
    try:
        files = get_authoring_service().list_files(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthoringFileListResponse(world_id=world_id, files=files)


@app.get("/authoring/worlds/{world_id}/files/{file_name}", response_model=AuthoringFileResponse)
def read_authoring_file(world_id: str, file_name: str) -> AuthoringFileResponse:
    require_authoring_api()
    try:
        content = get_authoring_service().read_file(world_id, file_name)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringFileResponse(world_id=world_id, file_name=file_name, content=content)


@app.put("/authoring/worlds/{world_id}/files/{file_name}", response_model=AuthoringFileWriteResponse)
def write_authoring_file(
    world_id: str,
    file_name: str,
    request: AuthoringFileWriteRequest,
) -> AuthoringFileWriteResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().write_file(
            world_id,
            file_name,
            request.content,
            confirm_warnings=request.confirm_warnings,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not report.ok:
        raise HTTPException(
            status_code=400,
            detail=_authoring_validation_response(report).model_dump(mode="json"),
        )
    confirmation_required = bool(report.warnings) and not request.confirm_warnings
    if confirmation_required:
        return AuthoringFileWriteResponse(
            world_id=world_id,
            file_name=file_name,
            validation=_authoring_validation_response(report),
            confirmation_required=True,
            saved=False,
        )
    return AuthoringFileWriteResponse(
        world_id=world_id,
        file_name=file_name,
        validation=_authoring_validation_response(report),
        confirmation_required=False,
        saved=True,
    )


@app.post(
    "/authoring/worlds/{world_id}/preview-file-change",
    response_model=AuthoringFilePreviewResponse,
)
def preview_authoring_file_change(
    world_id: str,
    request: AuthoringDraftFileRequest,
) -> AuthoringFilePreviewResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().preview_file_change(
            world_id,
            request.file_name,
            request.proposed_content,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_preview_response(world_id, request.file_name, report)


@app.post(
    "/authoring/worlds/{world_id}/validate-draft",
    response_model=AuthoringValidationResponse,
)
def validate_authoring_draft(
    world_id: str,
    request: AuthoringDraftFileRequest,
) -> AuthoringValidationResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().validate_draft(
            world_id,
            request.file_name,
            request.proposed_content,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_validation_response(report)


@app.post(
    "/authoring/worlds/{world_id}/impact-analysis",
    response_model=AuthoringImpactAnalysisResponse,
)
def analyze_authoring_draft_impact(
    world_id: str,
    request: AuthoringDraftFileRequest,
) -> AuthoringImpactAnalysisResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().analyze_file_impact(
            world_id,
            request.file_name,
            request.proposed_content,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_impact_response(report)


@app.post("/authoring/worlds/{world_id}/validate", response_model=AuthoringValidationResponse)
def validate_authoring_world(world_id: str) -> AuthoringValidationResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().validate_world(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _authoring_validation_response(report)


@app.get("/authoring/worlds/{world_id}/validation-graph", response_model=ValidationGraphResponse)
def get_authoring_validation_graph(world_id: str) -> ValidationGraphResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().validate_world(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _validation_graph_response(build_validation_graph(report))


@app.post("/authoring/worlds/{world_id}/validation-graph", response_model=ValidationGraphResponse)
def post_authoring_validation_graph(world_id: str) -> ValidationGraphResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().validate_world(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _validation_graph_response(build_validation_graph(report))


@app.get("/authoring/worlds/{world_id}/map", response_model=AuthoringMapGraphResponse)
def get_authoring_map(world_id: str) -> AuthoringMapGraphResponse:
    require_authoring_api()
    try:
        graph = get_authoring_service().get_map_graph(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringMapGraphResponse(world_id=world_id, graph=graph)


@app.post("/authoring/worlds/{world_id}/map/preview", response_model=AuthoringMapPreviewResponse)
def preview_authoring_map(
    world_id: str,
    request: AuthoringMapGraphRequest,
) -> AuthoringMapPreviewResponse:
    require_authoring_api()
    try:
        service = get_authoring_service()
        preview = service.preview_map_graph(world_id, request.graph)
        yaml_content = service.map_graph_to_locations_yaml(world_id, request.graph)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    validation = _authoring_validation_response(preview.validation_report)
    return AuthoringMapPreviewResponse(
        world_id=world_id,
        graph=request.graph,
        yaml_content=yaml_content,
        validation=validation,
        confirmation_required=validation.ok and bool(validation.warnings),
        diff_summary=AuthoringDiffSummaryResponse.model_validate(
            preview.diff_summary.model_dump(mode="json")
        ),
        impact=_authoring_impact_response(preview.impact),
    )


@app.post("/authoring/worlds/{world_id}/map/validate", response_model=AuthoringValidationResponse)
def validate_authoring_map(
    world_id: str,
    request: AuthoringMapGraphRequest,
) -> AuthoringValidationResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().validate_map_graph(world_id, request.graph)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_validation_response(report)


@app.put("/authoring/worlds/{world_id}/map", response_model=AuthoringMapWriteResponse)
def write_authoring_map(
    world_id: str,
    request: AuthoringMapGraphRequest,
) -> AuthoringMapWriteResponse:
    require_authoring_api()
    try:
        service = get_authoring_service()
        report = service.write_map_graph(
            world_id,
            request.graph,
            confirm_warnings=request.confirm_warnings,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    validation = _authoring_validation_response(report)
    if not report.ok:
        raise HTTPException(
            status_code=400,
            detail=validation.model_dump(mode="json"),
        )
    if validation.warnings and not request.confirm_warnings:
        return AuthoringMapWriteResponse(
            world_id=world_id,
            graph=request.graph,
            validation=validation,
            confirmation_required=True,
            saved=False,
        )
    return AuthoringMapWriteResponse(
        world_id=world_id,
        graph=service.get_map_graph(world_id),
        validation=validation,
        confirmation_required=False,
        saved=True,
    )


@app.get("/authoring/templates", response_model=ScenarioTemplateListResponse)
def list_authoring_templates() -> ScenarioTemplateListResponse:
    require_authoring_api()
    try:
        templates = get_scenario_template_renderer().list_templates()
    except ScenarioTemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ScenarioTemplateListResponse(
        templates=[_scenario_template_response(template) for template in templates]
    )


@app.get("/authoring/templates/{template_id}", response_model=ScenarioTemplateResponse)
def get_authoring_template(template_id: str) -> ScenarioTemplateResponse:
    require_authoring_api()
    try:
        template = get_scenario_template_renderer().get_template(template_id)
    except ScenarioTemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _scenario_template_response(template)


@app.post("/authoring/templates/{template_id}/preview", response_model=ScenarioTemplatePreviewResponse)
def preview_authoring_template(
    template_id: str,
    request: ScenarioTemplateRenderRequest,
) -> ScenarioTemplatePreviewResponse:
    require_authoring_api()
    try:
        preview = get_scenario_template_renderer().preview_template(
            template_id,
            request.variables,
            target_world_id=request.target_world_id,
        )
    except ScenarioTemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _scenario_template_preview_response(preview)


@app.post("/authoring/templates/{template_id}/apply", response_model=ScenarioTemplateApplyResponse)
def apply_authoring_template(
    template_id: str,
    request: ScenarioTemplateRenderRequest,
) -> ScenarioTemplateApplyResponse:
    require_authoring_api()
    try:
        preview = get_scenario_template_renderer().apply_template(
            template_id,
            request.variables,
            target_world_id=request.target_world_id,
            confirm_apply=request.confirm_apply,
        )
    except ScenarioTemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = _scenario_template_preview_response(preview)
    return ScenarioTemplateApplyResponse(
        template=response.template,
        rendered=response.rendered,
        validation_report=response.validation_report,
        writes_to_disk=response.writes_to_disk,
        target_world_id=response.target_world_id,
        applied=True,
    )


@app.post("/authoring/templates/{template_id}/render", response_model=RenderedScenarioTemplateResponse)
def render_authoring_template(
    template_id: str,
    request: ScenarioTemplateRenderRequest,
) -> RenderedScenarioTemplateResponse:
    require_authoring_api()
    try:
        template = get_scenario_template_renderer().get_template(template_id)
        rendered = get_scenario_template_renderer().render_template(template, request.variables)
    except ScenarioTemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _rendered_template_response(rendered)


@app.post("/authoring/template-wizard/preview", response_model=TemplateWizardPreview)
def preview_authoring_template_wizard(draft: TemplateWizardDraft) -> TemplateWizardPreview:
    require_authoring_api()
    try:
        return preview_template_wizard_draft(draft, get_authoring_service())
    except (AuthoringError, TemplateWizardError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/template-wizard/validate", response_model=TemplateWizardPreview)
def validate_authoring_template_wizard(draft: TemplateWizardDraft) -> TemplateWizardPreview:
    require_authoring_api()
    try:
        return validate_template_wizard_draft(draft, get_authoring_service())
    except (AuthoringError, TemplateWizardError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/template-wizard/apply", response_model=TemplateWizardPreview)
def apply_authoring_template_wizard(request: TemplateWizardApplyRequest) -> TemplateWizardPreview:
    require_authoring_api()
    try:
        return apply_template_wizard_draft(request, get_authoring_service())
    except (AuthoringError, TemplateWizardError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def get_world_pack_wizard() -> WorldPackWizard:
    return WorldPackWizard(get_worlds_root())


@app.post("/authoring/production/world-pack/create-draft", response_model=WorldPackWizardDraft)
def create_authoring_world_pack_wizard_draft(draft: WorldPackWizardDraft) -> WorldPackWizardDraft:
    require_authoring_api()
    try:
        return get_world_pack_wizard().create_draft(**draft.model_dump())
    except (WorldPackWizardError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/production/world-pack/preview", response_model=WorldPackWizardPreview)
def preview_authoring_world_pack_wizard(draft: WorldPackWizardDraft) -> WorldPackWizardPreview:
    require_authoring_api()
    try:
        return get_world_pack_wizard().preview_files(draft)
    except (WorldPackWizardError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/production/world-pack/validate", response_model=WorldPackWizardPreview)
def validate_authoring_world_pack_wizard(draft: WorldPackWizardDraft) -> WorldPackWizardPreview:
    require_authoring_api()
    try:
        return get_world_pack_wizard().validate_draft(draft)
    except (WorldPackWizardError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/production/world-pack/apply", response_model=WorldPackWizardPreview)
def apply_authoring_world_pack_wizard(request: WorldPackWizardApplyRequest) -> WorldPackWizardPreview:
    require_authoring_api()
    try:
        return get_world_pack_wizard().apply_to_worlds_directory(request)
    except (WorldPackWizardError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/npc-pack/preview", response_model=NPCPackGeneratorPreview)
def preview_production_npc_pack(draft: NPCPackGeneratorDraft) -> NPCPackGeneratorPreview:
    require_authoring_api()
    try:
        return preview_npc_pack_generator(draft, get_authoring_service())
    except (AuthoringError, NPCPackGeneratorError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/npc-pack/validate", response_model=NPCPackGeneratorPreview)
def validate_production_npc_pack(draft: NPCPackGeneratorDraft) -> NPCPackGeneratorPreview:
    require_authoring_api()
    try:
        return validate_npc_pack_generator(draft, get_authoring_service())
    except (AuthoringError, NPCPackGeneratorError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/npc-pack/apply", response_model=NPCPackGeneratorPreview)
def apply_production_npc_pack(request: NPCPackGeneratorApplyRequest) -> NPCPackGeneratorPreview:
    require_authoring_api()
    try:
        return apply_npc_pack_generator(request, get_authoring_service())
    except (AuthoringError, NPCPackGeneratorError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/npc-pack/export", response_model=NPCPackGeneratorPreview)
def export_production_npc_pack(request: NPCPackGeneratorExportRequest) -> NPCPackGeneratorPreview:
    require_authoring_api()
    try:
        return export_npc_pack_generator(request, get_authoring_service())
    except (AuthoringError, NPCPackGeneratorError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/quest-pack/preview", response_model=QuestPackGeneratorPreview)
def preview_production_quest_pack(draft: QuestPackGeneratorDraft) -> QuestPackGeneratorPreview:
    require_authoring_api()
    try:
        return preview_quest_pack_generator(draft, get_authoring_service())
    except (AuthoringError, QuestPackGeneratorError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/quest-pack/validate", response_model=QuestPackGeneratorPreview)
def validate_production_quest_pack(draft: QuestPackGeneratorDraft) -> QuestPackGeneratorPreview:
    require_authoring_api()
    try:
        return validate_quest_pack_generator(draft, get_authoring_service())
    except (AuthoringError, QuestPackGeneratorError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/quest-pack/apply", response_model=QuestPackGeneratorPreview)
def apply_production_quest_pack(request: QuestPackGeneratorApplyRequest) -> QuestPackGeneratorPreview:
    require_authoring_api()
    try:
        return apply_quest_pack_generator(request, get_authoring_service())
    except (AuthoringError, QuestPackGeneratorError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/production/location-clusters", response_model=LocationClusterTemplateList)
def list_production_location_clusters() -> LocationClusterTemplateList:
    require_authoring_api()
    return LocationClusterTemplateList(templates=list_location_cluster_templates())


@app.post("/production/location-clusters/{template_id}/preview", response_model=LocationClusterPreview)
def preview_production_location_cluster(
    template_id: str,
    request: LocationClusterPreviewRequest,
) -> LocationClusterPreview:
    require_authoring_api()
    try:
        return preview_location_cluster(template_id, request, get_authoring_service())
    except (AuthoringError, LocationClusterTemplateError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/location-clusters/{template_id}/apply-draft", response_model=LocationClusterPreview)
def apply_production_location_cluster(
    template_id: str,
    request: LocationClusterPreviewRequest,
) -> LocationClusterPreview:
    require_authoring_api()
    try:
        return apply_location_cluster_draft(template_id, request, get_authoring_service())
    except (AuthoringError, LocationClusterTemplateError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/production/mystery-templates", response_model=MysteryTemplateList)
def list_production_mystery_templates() -> MysteryTemplateList:
    require_authoring_api()
    return MysteryTemplateList(templates=list_mystery_templates())


@app.post("/production/mystery-templates/{template_id}/preview", response_model=MysteryTemplatePreview)
def preview_production_mystery_template(
    template_id: str,
    request: MysteryTemplatePreviewRequest,
) -> MysteryTemplatePreview:
    require_authoring_api()
    try:
        return preview_mystery_template(template_id, request, get_authoring_service())
    except (AuthoringError, MysteryTemplateError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/mystery-templates/{template_id}/apply-draft", response_model=MysteryTemplatePreview)
def apply_production_mystery_template(
    template_id: str,
    request: MysteryTemplatePreviewRequest,
) -> MysteryTemplatePreview:
    require_authoring_api()
    try:
        return apply_mystery_template(template_id, request, get_authoring_service())
    except (AuthoringError, MysteryTemplateError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/production/faction-templates", response_model=FactionTemplateList)
def list_production_faction_templates() -> FactionTemplateList:
    require_authoring_api()
    return FactionTemplateList(templates=list_faction_templates())


@app.post("/production/faction-templates/{template_id}/preview", response_model=FactionTemplatePreview)
def preview_production_faction_template(
    template_id: str,
    request: FactionTemplatePreviewRequest,
) -> FactionTemplatePreview:
    require_authoring_api()
    try:
        return preview_faction_template(template_id, request, get_authoring_service())
    except (AuthoringError, FactionTemplateError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/faction-templates/{template_id}/apply-draft", response_model=FactionTemplatePreview)
def apply_production_faction_template(
    template_id: str,
    request: FactionTemplatePreviewRequest,
) -> FactionTemplatePreview:
    require_authoring_api()
    try:
        return apply_faction_template(template_id, request, get_authoring_service())
    except (AuthoringError, FactionTemplateError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/batch-validate", response_model=ContentBatchValidationReport)
def batch_validate_production_content(request: ContentBatchValidationRequest) -> ContentBatchValidationReport:
    require_authoring_api()
    try:
        return validate_content_batch(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/script-packages/build-dry-run", response_model=ScriptPackageBuildReport)
def dry_run_production_script_package(request: ScriptPackageBuildRequest) -> ScriptPackageBuildReport:
    require_authoring_api()
    try:
        return build_script_package_dry_run(request)
    except (ScriptPackageBuilderError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/script-packages/build", response_model=ScriptPackageBuildReport)
def build_production_script_package(request: ScriptPackageBuildRequest) -> ScriptPackageBuildReport:
    require_authoring_api()
    try:
        return build_script_package(request)
    except (ScriptPackageBuilderError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/script-packages/validate", response_model=ScriptPackageBuildReport)
def validate_production_script_package(request: ScriptPackageBuildRequest) -> ScriptPackageBuildReport:
    require_authoring_api()
    try:
        return validate_script_package(request)
    except (ScriptPackageBuilderError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/script-packages/export", response_model=ScriptPackageBuildReport)
def export_production_script_package(request: ScriptPackageBuildRequest) -> ScriptPackageBuildReport:
    require_authoring_api()
    try:
        return export_script_package(request)
    except (ScriptPackageBuilderError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/campaign-starter/preview", response_model=CampaignStarterKitPreview)
def preview_production_campaign_starter(draft: CampaignStarterKitDraft) -> CampaignStarterKitPreview:
    require_authoring_api()
    try:
        return preview_campaign_starter_kit(draft, worlds_root=str(get_worlds_root()))
    except (CampaignStarterKitError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/campaign-starter/build", response_model=CampaignStarterKitPreview)
def build_production_campaign_starter(request: CampaignStarterKitBuildRequest) -> CampaignStarterKitPreview:
    require_authoring_api()
    try:
        return build_campaign_starter_kit(request, worlds_root=str(get_worlds_root()))
    except (CampaignStarterKitError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/production/campaign-starter/export-script", response_model=ScriptPackageBuildReport)
def export_production_campaign_starter_script(draft: CampaignStarterKitDraft) -> ScriptPackageBuildReport:
    require_authoring_api()
    try:
        return export_campaign_starter_script_package(draft)
    except (CampaignStarterKitError, ScriptPackageBuilderError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/authoring/rp-scenario-templates", response_model=RPScenarioTemplateListResponse)
def list_authoring_rp_scenario_templates() -> RPScenarioTemplateListResponse:
    require_authoring_api()
    try:
        templates = get_rp_scenario_template_renderer().list_templates()
    except RPScenarioTemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RPScenarioTemplateListResponse(templates=templates)


@app.get("/authoring/rp-scenario-templates/{template_id}", response_model=RPScenarioTemplate)
def get_authoring_rp_scenario_template(template_id: str) -> RPScenarioTemplate:
    require_authoring_api()
    try:
        return get_rp_scenario_template_renderer().get_template(template_id)
    except RPScenarioTemplateError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/authoring/rp-scenario-templates/{template_id}/preview", response_model=RPScenarioTemplatePreviewResponse)
def preview_authoring_rp_scenario_template(
    template_id: str,
    request: RPScenarioTemplateRenderRequest,
) -> RPScenarioTemplatePreviewResponse:
    require_authoring_api()
    state = _state_for_optional_game_session(request.game_session_id)
    try:
        preview = get_rp_scenario_template_renderer().preview_template(
            template_id,
            participant_ids=request.participant_ids,
            game_session_id=request.game_session_id,
            state=state,
        )
    except RPScenarioTemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _rp_scenario_template_preview_response(preview)


@app.post("/authoring/rp-scenario-templates/{template_id}/apply", response_model=RPScenarioTemplatePreviewResponse)
def apply_authoring_rp_scenario_template(
    template_id: str,
    request: RPScenarioTemplateRenderRequest,
) -> RPScenarioTemplatePreviewResponse:
    require_authoring_api()
    state = _state_for_optional_game_session(request.game_session_id)
    try:
        preview = get_rp_scenario_template_renderer().apply_template(
            template_id,
            participant_ids=request.participant_ids,
            game_session_id=request.game_session_id,
            state=state,
            confirm_apply=request.confirm_apply,
        )
    except RPScenarioTemplateError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _rp_scenario_template_preview_response(preview)


@app.get("/authoring/worlds/{world_id}/quests/graph", response_model=QuestGraphResponse)
def get_authoring_quest_graph(world_id: str) -> QuestGraphResponse:
    require_authoring_api()
    try:
        graph = parse_quest_graph(world_id, get_authoring_service())
    except (AuthoringError, QuestGraphError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _quest_graph_response(graph)


@app.post("/authoring/worlds/{world_id}/quests/graph/preview", response_model=QuestGraphPreviewResponse)
def preview_authoring_quest_graph(
    world_id: str,
    request: QuestGraphPreviewRequest,
) -> QuestGraphPreviewResponse:
    require_authoring_api()
    try:
        graph = QuestGraph.model_validate(request.graph.model_dump(mode="json", exclude={"local_only"}))
        preview = preview_quest_graph(world_id, graph, get_authoring_service())
    except (AuthoringError, QuestGraphError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return QuestGraphPreviewResponse(
        world_id=world_id,
        graph=_quest_graph_response(preview.graph),
        yaml_content=preview.yaml_content,
        validation=_authoring_validation_response(preview.validation),
        confirmation_required=preview.confirmation_required,
    )


@app.post("/authoring/worlds/{world_id}/quests/graph/validate", response_model=QuestGraphPreviewResponse)
def validate_authoring_quest_graph(
    world_id: str,
    request: QuestGraphPreviewRequest,
) -> QuestGraphPreviewResponse:
    require_authoring_api()
    try:
        graph = QuestGraph.model_validate(request.graph.model_dump(mode="json", exclude={"local_only"}))
        preview = preview_quest_graph(world_id, graph, get_authoring_service())
        validation = validate_quest_graph(world_id, graph, get_authoring_service())
    except (AuthoringError, QuestGraphError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return QuestGraphPreviewResponse(
        world_id=world_id,
        graph=_quest_graph_response(graph),
        yaml_content=preview.yaml_content,
        validation=_authoring_validation_response(validation),
        confirmation_required=validation.ok and bool(validation.warnings),
    )


@app.put("/authoring/worlds/{world_id}/quests/graph", response_model=QuestGraphSaveResponse)
def save_authoring_quest_graph(
    world_id: str,
    request: QuestGraphPreviewRequest,
) -> QuestGraphSaveResponse:
    require_authoring_api()
    try:
        graph = QuestGraph.model_validate(request.graph.model_dump(mode="json", exclude={"local_only"}))
        preview = preview_quest_graph(world_id, graph, get_authoring_service())
        report = save_quest_graph(
            world_id,
            graph,
            get_authoring_service(),
            confirm_warnings=request.confirm_warnings,
        )
    except (AuthoringError, QuestGraphError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return QuestGraphSaveResponse(
        world_id=world_id,
        graph=_quest_graph_response(graph),
        yaml_content=preview.yaml_content,
        validation=_authoring_validation_response(report),
        saved=report.ok and not (report.warnings and not request.confirm_warnings),
        confirmation_required=report.ok and bool(report.warnings) and not request.confirm_warnings,
    )


@app.post("/authoring/worlds/{world_id}/quests/graph/scenario-draft", response_model=QuestGraphScenarioDraftResponse)
def generate_authoring_quest_graph_scenario_draft(
    world_id: str,
    request: QuestGraphPreviewRequest,
) -> QuestGraphScenarioDraftResponse:
    require_authoring_api()
    try:
        graph = QuestGraph.model_validate(request.graph.model_dump(mode="json", exclude={"local_only"}))
        scenario = generate_scenario_regression_draft(world_id, graph)
        validation = get_scenario_authoring_service().validate_scenario(scenario)
    except (AuthoringError, QuestGraphError, ScenarioAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return QuestGraphScenarioDraftResponse(
        world_id=world_id,
        scenario=scenario.model_dump(mode="json"),
        validation=_authoring_validation_response(validation),
    )


@app.get("/authoring/worlds/{world_id}/npcs/goals", response_model=NPCGoalAuthoringGraphResponse)
def get_authoring_npc_goal_graph(world_id: str) -> NPCGoalAuthoringGraphResponse:
    require_authoring_api()
    try:
        graph = parse_npc_goal_graph(world_id, get_authoring_service())
    except (AuthoringError, NPCGoalAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _npc_goal_graph_response(graph)


@app.post("/authoring/worlds/{world_id}/npcs/goals/preview", response_model=NPCGoalAuthoringPreviewResponse)
def preview_authoring_npc_goal_graph(
    world_id: str,
    request: NPCGoalAuthoringGraphRequest,
) -> NPCGoalAuthoringPreviewResponse:
    require_authoring_api()
    try:
        graph = NPCGoalAuthoringGraph.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_npc_goal_graph(world_id, graph, get_authoring_service())
    except (AuthoringError, NPCGoalAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return NPCGoalAuthoringPreviewResponse(
        world_id=world_id,
        graph=_npc_goal_graph_response(preview.graph),
        yaml_content=preview.yaml_content,
        validation=_authoring_validation_response(preview.validation),
        confirmation_required=preview.confirmation_required,
    )


@app.post("/authoring/worlds/{world_id}/npcs/goals/validate", response_model=NPCGoalAuthoringPreviewResponse)
def validate_authoring_npc_goal_graph(
    world_id: str,
    request: NPCGoalAuthoringGraphRequest,
) -> NPCGoalAuthoringPreviewResponse:
    require_authoring_api()
    try:
        graph = NPCGoalAuthoringGraph.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_npc_goal_graph(world_id, graph, get_authoring_service())
        validation = validate_npc_goal_graph(world_id, graph, get_authoring_service())
    except (AuthoringError, NPCGoalAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return NPCGoalAuthoringPreviewResponse(
        world_id=world_id,
        graph=_npc_goal_graph_response(graph),
        yaml_content=preview.yaml_content,
        validation=_authoring_validation_response(validation),
        confirmation_required=validation.ok and bool(validation.warnings),
    )


@app.put("/authoring/worlds/{world_id}/npcs/goals", response_model=NPCGoalAuthoringSaveResponse)
def save_authoring_npc_goal_graph(
    world_id: str,
    request: NPCGoalAuthoringGraphRequest,
) -> NPCGoalAuthoringSaveResponse:
    require_authoring_api()
    try:
        graph = NPCGoalAuthoringGraph.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_npc_goal_graph(world_id, graph, get_authoring_service())
        report = save_npc_goal_graph(world_id, graph, get_authoring_service())
    except (AuthoringError, NPCGoalAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return NPCGoalAuthoringSaveResponse(
        world_id=world_id,
        graph=_npc_goal_graph_response(graph),
        yaml_content=preview.yaml_content,
        validation=_authoring_validation_response(report),
        confirmation_required=report.ok and bool(report.warnings),
        saved=report.ok,
    )


@app.get("/authoring/npc-simulation-presets", response_model=NPCSimulationPresetListResponse)
def get_authoring_npc_simulation_presets() -> NPCSimulationPresetListResponse:
    require_authoring_api()
    return NPCSimulationPresetListResponse(
        presets=[
            NPCSimulationPresetResponse.model_validate(preset.model_dump(mode="json"))
            for preset in list_npc_simulation_presets()
        ]
    )


@app.post(
    "/authoring/worlds/{world_id}/npcs/{npc_id}/simulation-preset/preview",
    response_model=NPCSimulationPresetPreviewResponse,
)
def preview_authoring_npc_simulation_preset(
    world_id: str,
    npc_id: str,
    request: NPCSimulationPresetApplyRequest,
) -> NPCSimulationPresetPreviewResponse:
    require_authoring_api()
    try:
        service_request = NPCSimulationPresetServiceApplyRequest.model_validate(
            request.model_dump(mode="json")
        )
        preview = preview_npc_simulation_preset(
            world_id,
            npc_id,
            service_request,
            get_authoring_service(),
        )
    except (AuthoringError, NPCGoalAuthoringError, NPCSimulationPresetError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _npc_simulation_preset_preview_response(preview)


@app.post(
    "/authoring/worlds/{world_id}/npcs/{npc_id}/simulation-preset/apply-draft",
    response_model=NPCSimulationPresetPreviewResponse,
)
def apply_authoring_npc_simulation_preset_to_draft(
    world_id: str,
    npc_id: str,
    request: NPCSimulationPresetApplyRequest,
) -> NPCSimulationPresetPreviewResponse:
    require_authoring_api()
    try:
        service_request = NPCSimulationPresetServiceApplyRequest.model_validate(
            request.model_dump(mode="json")
        )
        preview = apply_npc_simulation_preset_to_draft(
            world_id,
            npc_id,
            service_request,
            get_authoring_service(),
        )
    except (AuthoringError, NPCGoalAuthoringError, NPCSimulationPresetError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _npc_simulation_preset_preview_response(preview)


@app.get("/authoring/worlds/{world_id}/social/graph", response_model=SocialAuthoringGraphResponse)
def get_authoring_social_graph(world_id: str) -> SocialAuthoringGraphResponse:
    require_authoring_api()
    try:
        graph = parse_social_authoring_graph(world_id, get_authoring_service())
    except (AuthoringError, SocialGraphAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _social_authoring_graph_response(graph)


@app.post("/authoring/worlds/{world_id}/social/graph/preview", response_model=SocialAuthoringPreviewResponse)
def preview_authoring_social_graph(
    world_id: str,
    request: SocialAuthoringGraphRequest,
) -> SocialAuthoringPreviewResponse:
    require_authoring_api()
    try:
        graph = SocialAuthoringGraph.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_social_authoring_graph(world_id, graph, get_authoring_service())
    except (AuthoringError, SocialGraphAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SocialAuthoringPreviewResponse(
        world_id=world_id,
        graph=_social_authoring_graph_response(preview.graph),
        yaml_contents=preview.yaml_contents,
        validation=_authoring_validation_response(preview.validation),
        confirmation_required=preview.confirmation_required,
    )


@app.post("/authoring/worlds/{world_id}/social/graph/validate", response_model=SocialAuthoringPreviewResponse)
def validate_authoring_social_graph(
    world_id: str,
    request: SocialAuthoringGraphRequest,
) -> SocialAuthoringPreviewResponse:
    require_authoring_api()
    try:
        graph = SocialAuthoringGraph.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_social_authoring_graph(world_id, graph, get_authoring_service())
        validation = validate_social_authoring_graph(world_id, graph, get_authoring_service())
    except (AuthoringError, SocialGraphAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SocialAuthoringPreviewResponse(
        world_id=world_id,
        graph=_social_authoring_graph_response(preview.graph),
        yaml_contents=preview.yaml_contents,
        validation=_authoring_validation_response(validation),
        confirmation_required=validation.ok and bool(validation.warnings),
    )


@app.put("/authoring/worlds/{world_id}/social/graph", response_model=SocialAuthoringSaveResponse)
def save_authoring_social_graph(
    world_id: str,
    request: SocialAuthoringGraphRequest,
) -> SocialAuthoringSaveResponse:
    require_authoring_api()
    try:
        graph = SocialAuthoringGraph.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_social_authoring_graph(world_id, graph, get_authoring_service())
        report = save_social_authoring_graph(
            world_id,
            graph,
            get_authoring_service(),
            confirm_warnings=request.confirm_warnings,
        )
    except (AuthoringError, SocialGraphAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SocialAuthoringSaveResponse(
        world_id=world_id,
        graph=_social_authoring_graph_response(preview.graph),
        yaml_contents=preview.yaml_contents,
        validation=_authoring_validation_response(report),
        confirmation_required=report.ok and bool(report.warnings) and not request.confirm_warnings,
        saved=report.ok and not (report.warnings and not request.confirm_warnings),
    )


@app.get("/authoring/worlds/{world_id}/economy", response_model=ItemEconomyAuthoringResponse)
def get_authoring_item_economy(world_id: str) -> ItemEconomyAuthoringResponse:
    require_authoring_api()
    try:
        graph = parse_item_economy_authoring(world_id, get_authoring_service())
    except (AuthoringError, ItemEconomyAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _item_economy_authoring_response(graph)


@app.post("/authoring/worlds/{world_id}/economy/preview", response_model=ItemEconomyAuthoringPreviewResponse)
def preview_authoring_item_economy(
    world_id: str,
    request: ItemEconomyAuthoringRequest,
) -> ItemEconomyAuthoringPreviewResponse:
    require_authoring_api()
    try:
        graph = ItemEconomyAuthoring.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_item_economy_authoring(world_id, graph, get_authoring_service())
    except (AuthoringError, ItemEconomyAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ItemEconomyAuthoringPreviewResponse(
        world_id=world_id,
        graph=_item_economy_authoring_response(preview.graph),
        yaml_contents=preview.yaml_contents,
        validation=_authoring_validation_response(preview.validation),
        confirmation_required=preview.confirmation_required,
    )


@app.post("/authoring/worlds/{world_id}/economy/validate", response_model=ItemEconomyAuthoringPreviewResponse)
def validate_authoring_item_economy(
    world_id: str,
    request: ItemEconomyAuthoringRequest,
) -> ItemEconomyAuthoringPreviewResponse:
    require_authoring_api()
    try:
        graph = ItemEconomyAuthoring.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_item_economy_authoring(world_id, graph, get_authoring_service())
        validation = validate_item_economy_authoring(world_id, graph, get_authoring_service())
    except (AuthoringError, ItemEconomyAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ItemEconomyAuthoringPreviewResponse(
        world_id=world_id,
        graph=_item_economy_authoring_response(graph),
        yaml_contents=preview.yaml_contents,
        validation=_authoring_validation_response(validation),
        confirmation_required=validation.ok and bool(validation.warnings),
    )


@app.post("/authoring/worlds/{world_id}/economy/balance-check", response_model=ItemEconomyAuthoringPreviewResponse)
def balance_check_authoring_item_economy(
    world_id: str,
    request: ItemEconomyAuthoringRequest,
) -> ItemEconomyAuthoringPreviewResponse:
    require_authoring_api()
    try:
        graph = ItemEconomyAuthoring.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = balance_check_item_economy_authoring(world_id, graph, get_authoring_service())
    except (AuthoringError, ItemEconomyAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ItemEconomyAuthoringPreviewResponse(
        world_id=world_id,
        graph=_item_economy_authoring_response(preview.graph),
        yaml_contents=preview.yaml_contents,
        validation=_authoring_validation_response(preview.validation),
        confirmation_required=preview.confirmation_required,
    )


@app.put("/authoring/worlds/{world_id}/economy", response_model=ItemEconomyAuthoringSaveResponse)
def save_authoring_item_economy(
    world_id: str,
    request: ItemEconomyAuthoringRequest,
) -> ItemEconomyAuthoringSaveResponse:
    require_authoring_api()
    try:
        graph = ItemEconomyAuthoring.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_item_economy_authoring(world_id, graph, get_authoring_service())
        report = save_item_economy_authoring(
            world_id,
            graph,
            get_authoring_service(),
            confirm_warnings=request.confirm_warnings,
        )
    except (AuthoringError, ItemEconomyAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ItemEconomyAuthoringSaveResponse(
        world_id=world_id,
        graph=_item_economy_authoring_response(graph),
        yaml_contents=preview.yaml_contents,
        validation=_authoring_validation_response(report),
        confirmation_required=report.ok and bool(report.warnings) and not request.confirm_warnings,
        saved=report.ok and not (report.warnings and not request.confirm_warnings),
    )


@app.get("/authoring/worlds/{world_id}/rumor-crime", response_model=RumorCrimeConsequenceAuthoringResponse)
def get_authoring_rumor_crime(world_id: str) -> RumorCrimeConsequenceAuthoringResponse:
    require_authoring_api()
    try:
        graph = parse_rumor_crime_authoring(world_id, get_authoring_service())
    except (AuthoringError, RumorCrimeAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _rumor_crime_authoring_response(graph)


@app.post("/authoring/worlds/{world_id}/rumor-crime/preview", response_model=RumorCrimeConsequencePreviewResponse)
def preview_authoring_rumor_crime(
    world_id: str,
    request: RumorCrimeConsequenceAuthoringRequest,
) -> RumorCrimeConsequencePreviewResponse:
    require_authoring_api()
    try:
        graph = RumorCrimeConsequenceAuthoring.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_rumor_crime_authoring(world_id, graph, get_authoring_service())
    except (AuthoringError, RumorCrimeAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RumorCrimeConsequencePreviewResponse(
        world_id=world_id,
        graph=_rumor_crime_authoring_response(preview.graph),
        yaml_contents=preview.yaml_contents,
        validation=_authoring_validation_response(preview.validation),
        confirmation_required=preview.confirmation_required,
    )


@app.post("/authoring/worlds/{world_id}/rumor-crime/validate", response_model=RumorCrimeConsequencePreviewResponse)
def validate_authoring_rumor_crime(
    world_id: str,
    request: RumorCrimeConsequenceAuthoringRequest,
) -> RumorCrimeConsequencePreviewResponse:
    require_authoring_api()
    try:
        graph = RumorCrimeConsequenceAuthoring.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_rumor_crime_authoring(world_id, graph, get_authoring_service())
        validation = validate_rumor_crime_authoring(world_id, graph, get_authoring_service())
    except (AuthoringError, RumorCrimeAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RumorCrimeConsequencePreviewResponse(
        world_id=world_id,
        graph=_rumor_crime_authoring_response(preview.graph),
        yaml_contents=preview.yaml_contents,
        validation=_authoring_validation_response(validation),
        confirmation_required=validation.ok and bool(validation.warnings),
    )


@app.put("/authoring/worlds/{world_id}/rumor-crime", response_model=RumorCrimeConsequenceSaveResponse)
def save_authoring_rumor_crime(
    world_id: str,
    request: RumorCrimeConsequenceAuthoringRequest,
) -> RumorCrimeConsequenceSaveResponse:
    require_authoring_api()
    try:
        graph = RumorCrimeConsequenceAuthoring.model_validate(
            request.graph.model_dump(mode="json", exclude={"local_only"})
        )
        preview = preview_rumor_crime_authoring(world_id, graph, get_authoring_service())
        report = save_rumor_crime_authoring(
            world_id,
            graph,
            get_authoring_service(),
            confirm_warnings=request.confirm_warnings,
        )
    except (AuthoringError, RumorCrimeAuthoringError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RumorCrimeConsequenceSaveResponse(
        world_id=world_id,
        graph=_rumor_crime_authoring_response(preview.graph),
        yaml_contents=preview.yaml_contents,
        validation=_authoring_validation_response(report),
        confirmation_required=report.ok and bool(report.warnings) and not request.confirm_warnings,
        saved=report.ok and not (report.warnings and not request.confirm_warnings),
    )


@app.get("/authoring/mods", response_model=AuthoringModListResponse)
def list_authoring_mods() -> AuthoringModListResponse:
    require_authoring_api()
    try:
        mods = get_mod_loader().discover_mods()
    except ModLoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringModListResponse(mods=[_authoring_mod_response(mod) for mod in mods])


@app.get("/authoring/mods/load-order", response_model=AuthoringModLoadOrderResponse)
def get_authoring_mod_load_order() -> AuthoringModLoadOrderResponse:
    require_authoring_api()
    try:
        report = get_mod_loader().resolve_load_order()
    except ModLoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringModLoadOrderResponse(
        ok=report.ok,
        load_order=report.load_order,
        errors=report.errors,
    )


@app.get("/authoring/mods/{mod_id}", response_model=AuthoringModDetailResponse)
def get_authoring_mod(mod_id: str) -> AuthoringModDetailResponse:
    require_authoring_api()
    try:
        mod = next((item for item in get_mod_loader().discover_mods() if item.manifest.id == mod_id), None)
        if mod is None:
            raise ModLoaderError(f"Mod not found: {mod_id}")
        validation = get_mod_loader().validate_mod(mod_id)
    except ModLoaderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthoringModDetailResponse(
        mod=_authoring_mod_response(mod),
        validation=_authoring_mod_validation_response(validation),
    )


@app.post("/authoring/mods/{mod_id}/validate", response_model=AuthoringModValidationResponse)
def validate_authoring_mod(mod_id: str) -> AuthoringModValidationResponse:
    require_authoring_api()
    try:
        report = get_mod_loader().validate_mod(mod_id)
    except ModLoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_mod_validation_response(report)


@app.get("/authoring/export/worlds/{world_id}", response_model=ArchiveExportResponse)
def export_authoring_world(world_id: str) -> ArchiveExportResponse:
    require_authoring_api()
    try:
        exported = get_import_export_service().export_world(world_id)
    except ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveExportResponse(export_type="world", id=world_id, file_name=exported.file_name, archive_base64=exported.archive_base64)


@app.post("/authoring/import/worlds", response_model=ArchiveImportResponse)
def import_authoring_world(request: ArchiveImportRequest) -> ArchiveImportResponse:
    require_authoring_api()
    try:
        profile = get_import_profile(request.import_profile_id or "safe")
        if request.import_profile_id and request.overwrite and not profile.allow_overwrite:
            raise ImportExportError("Selected import profile does not allow overwrite.")
        result = get_import_export_service().import_world(request.archive_base64, overwrite=request.overwrite)
    except ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveImportResponse(**result.model_dump(mode="json"))


@app.get("/authoring/export/mods/{mod_id}", response_model=ArchiveExportResponse)
def export_authoring_mod(mod_id: str) -> ArchiveExportResponse:
    require_authoring_api()
    try:
        exported = get_import_export_service().export_mod(mod_id)
    except ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveExportResponse(export_type="mod", id=mod_id, file_name=exported.file_name, archive_base64=exported.archive_base64)


@app.post("/authoring/import/mods", response_model=ArchiveImportResponse)
def import_authoring_mod(request: ArchiveImportRequest) -> ArchiveImportResponse:
    require_authoring_api()
    try:
        profile = get_import_profile(request.import_profile_id or "safe")
        if request.import_profile_id and request.overwrite and not profile.allow_overwrite:
            raise ImportExportError("Selected import profile does not allow overwrite.")
        result = get_import_export_service().import_mod(request.archive_base64, overwrite=request.overwrite)
    except ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveImportResponse(**result.model_dump(mode="json"))


@app.get("/authoring/export/saves/{save_id}", response_model=ArchiveExportResponse)
def export_authoring_save(save_id: str) -> ArchiveExportResponse:
    require_authoring_api()
    try:
        exported = get_import_export_service().export_save(save_id)
    except (ImportExportError, SaveRepositoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveExportResponse(export_type="save", id=save_id, file_name=exported.file_name, archive_base64=exported.archive_base64)


@app.get("/authoring/export/templates/{pack_id}", response_model=ArchiveExportResponse)
def export_authoring_template_pack(pack_id: str = "local_templates") -> ArchiveExportResponse:
    require_authoring_api()
    try:
        exported = get_import_export_service().export_template_pack(pack_id)
    except ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveExportResponse(export_type="template_pack", id=pack_id, file_name=exported.file_name, archive_base64=exported.archive_base64)


@app.get("/authoring/export/scenarios/{suite_id}", response_model=ArchiveExportResponse)
def export_authoring_scenario_suite(suite_id: str = "local_scenarios") -> ArchiveExportResponse:
    require_authoring_api()
    try:
        exported = get_import_export_service().export_scenario_suite(suite_id)
    except ImportExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveExportResponse(export_type="scenario_suite", id=suite_id, file_name=exported.file_name, archive_base64=exported.archive_base64)


@app.get("/library/items", response_model=LocalContentLibrary)
def list_library_items(content_type: str | None = None, query: str = "", tag: str | None = None) -> LocalContentLibrary:
    require_authoring_api()
    try:
        parsed_type = LocalContentType(content_type) if content_type else None
        if query or tag:
            return get_local_content_library_service().search_items(
                LocalContentLibrarySearchRequest(
                    query=query,
                    content_types=[parsed_type] if parsed_type else [],
                    tags=[tag] if tag else [],
                )
            )
        return get_local_content_library_service().list_items(parsed_type)
    except (ImportExportError, LocalContentLibraryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/library/items/search", response_model=LocalContentLibrary)
def search_library_items(request: LocalContentLibrarySearchRequest) -> LocalContentLibrary:
    require_authoring_api()
    try:
        return get_local_content_library_service().search_items(request)
    except (ImportExportError, LocalContentLibraryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/library/items/{item_id}", response_model=LocalContentLibraryItem)
def inspect_library_item(item_id: str) -> LocalContentLibraryItem:
    require_authoring_api()
    try:
        return get_local_content_library_service().inspect_item(item_id)
    except (ImportExportError, LocalContentLibraryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/library/items/{item_id}/validate", response_model=ValidationReport)
def validate_library_item(item_id: str) -> ValidationReport:
    require_authoring_api()
    try:
        return get_local_content_library_service().validate_item(item_id)
    except (ImportExportError, LocalContentLibraryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/library/items/batch-validate")
def batch_validate_library_items(request: LocalContentLibraryBatchValidateRequest) -> dict[str, Any]:
    require_authoring_api()
    try:
        return get_local_content_library_service().batch_validate(request).model_dump(mode="json")
    except (ImportExportError, LocalContentLibraryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/library/import")
def import_library_item(request: LocalContentLibraryImportRequest) -> dict[str, Any]:
    require_authoring_api()
    try:
        result = get_local_content_library_service().import_archive(request)
    except (ImportExportError, LocalContentLibraryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result.model_dump(mode="json")


@app.post("/library/export", response_model=ArchiveExportResponse)
def export_library_item(request: LocalContentLibraryExportRequest) -> ArchiveExportResponse:
    require_authoring_api()
    try:
        exported = get_local_content_library_service().export_item(request)
    except (ImportExportError, LocalContentLibraryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveExportResponse(export_type=request.content_type.value, id=request.item_id, file_name=exported.file_name, archive_base64=exported.archive_base64)


@app.post("/library/duplicate", response_model=LocalContentLibraryItem)
def duplicate_library_item(request: LocalContentLibraryDuplicateRequest) -> LocalContentLibraryItem:
    require_authoring_api()
    try:
        return get_local_content_library_service().duplicate_item(request)
    except (ImportExportError, LocalContentLibraryError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/authoring/import/packages/dry-run", response_model=PackageDryRunResponse)
def dry_run_authoring_package_import(request: ArchiveImportRequest) -> PackageDryRunResponse:
    require_authoring_api()
    result = get_import_export_service().dry_run_import_package(
        request.archive_base64,
        overwrite=request.overwrite,
    )
    return PackageDryRunResponse.model_validate(result.model_dump(mode="json"))


@app.post("/authoring/import/packages/apply", response_model=ArchiveImportResponse)
def apply_authoring_package_import(request: ArchiveImportRequest) -> ArchiveImportResponse:
    require_authoring_api()
    try:
        profile = get_import_profile(request.import_profile_id or "safe")
        if request.import_profile_id and request.overwrite and not profile.allow_overwrite:
            raise ImportExportError("Selected import profile does not allow overwrite.")
        result = get_import_export_service().apply_import_package(
            request.archive_base64,
            overwrite=request.overwrite,
            confirm_apply=request.confirm_apply,
        )
    except (ImportExportError, SaveRepositoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveImportResponse(**result.model_dump(mode="json"))


@app.post("/authoring/import/saves", response_model=ArchiveImportResponse)
def import_authoring_save(request: ArchiveImportRequest) -> ArchiveImportResponse:
    require_authoring_api()
    try:
        profile = get_import_profile(request.import_profile_id or "safe")
        if request.import_profile_id and request.overwrite and not profile.allow_overwrite:
            raise ImportExportError("Selected import profile does not allow overwrite.")
        result = get_import_export_service().import_save(request.archive_base64, overwrite=request.overwrite)
    except (ImportExportError, SaveRepositoryError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArchiveImportResponse(**result.model_dump(mode="json"))


def _state_for_optional_game_session(game_session_id: str | None) -> GameState | None:
    if not game_session_id:
        return None
    game_loop = get_session_store().get_session(game_session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {game_session_id}")
    return game_loop.state


def _authoring_world_response(world: object) -> AuthoringWorldSummaryResponse:
    return AuthoringWorldSummaryResponse(
        world_id=getattr(world, "world_id"),
        name=getattr(world, "name"),
        description=getattr(world, "description"),
        version=getattr(world, "version"),
        file_count=getattr(world, "file_count"),
    )


def _authoring_mod_response(mod: ModInfo) -> AuthoringModSummaryResponse:
    manifest = mod.manifest
    return AuthoringModSummaryResponse(
        id=manifest.id,
        name=manifest.name,
        version=manifest.version,
        engine_version_min=manifest.engine_version_min,
        engine_version_max=manifest.engine_version_max,
        content_schema_version=manifest.content_schema_version,
        dependencies=manifest.dependencies,
        optional_dependencies=manifest.optional_dependencies,
        conflicts=manifest.conflicts,
        load_order_hint=manifest.load_order_hint,
        compatible_worlds=manifest.compatible_worlds,
        migration_notes=manifest.migration_notes,
        entry_worlds=manifest.entry_worlds,
        content_paths=manifest.content_paths,
        author=manifest.author,
        description=manifest.description,
    )


def _authoring_mod_validation_response(report: ModValidationReport) -> AuthoringModValidationResponse:
    return AuthoringModValidationResponse(
        mod_id=report.mod_id,
        ok=report.ok,
        errors=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.errors
        ],
        warnings=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.warnings
        ],
        suggestions=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.suggestions
        ],
        world_report_ids=sorted(report.world_reports),
    )


def _scenario_template_response(template: ScenarioTemplate) -> ScenarioTemplateResponse:
    return ScenarioTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        template_type=template.template_type.value,
        required_variables=template.required_variables,
        optional_variables=template.optional_variables,
        output_files=[
            ScenarioTemplateOutputFileResponse(
                file_name=output_file.file_name,
                content=output_file.content,
            )
            for output_file in template.output_files
        ],
        validation_rules=template.validation_rules,
        tags=template.tags,
    )


def _rendered_template_response(rendered: RenderedTemplate) -> RenderedScenarioTemplateResponse:
    return RenderedScenarioTemplateResponse(
        template_id=rendered.template_id,
        template_type=rendered.template_type.value,
        files=[
            RenderedScenarioTemplateFileResponse(
                file_name=rendered_file.file_name,
                content=rendered_file.content,
            )
            for rendered_file in rendered.files
        ],
    )


def _scenario_template_preview_response(preview: ScenarioTemplatePreview) -> ScenarioTemplatePreviewResponse:
    return ScenarioTemplatePreviewResponse(
        template=_scenario_template_response(preview.template),
        rendered=_rendered_template_response(preview.rendered),
        validation_report=(
            _authoring_validation_response(preview.validation_report)
            if preview.validation_report is not None
            else None
        ),
        writes_to_disk=preview.writes_to_disk,
        target_world_id=preview.target_world_id,
    )


def _rp_scenario_template_preview_response(preview: RPScenarioTemplatePreview) -> RPScenarioTemplatePreviewResponse:
    return RPScenarioTemplatePreviewResponse.model_validate(preview.model_dump(mode="json"))


def _quest_graph_response(graph: QuestGraph) -> QuestGraphResponse:
    return QuestGraphResponse.model_validate(graph.model_dump(mode="json"))


def _npc_goal_graph_response(graph: NPCGoalAuthoringGraph) -> NPCGoalAuthoringGraphResponse:
    return NPCGoalAuthoringGraphResponse.model_validate(graph.model_dump(mode="json"))


def _npc_simulation_preset_preview_response(
    preview: NPCSimulationPresetPreview,
) -> NPCSimulationPresetPreviewResponse:
    return NPCSimulationPresetPreviewResponse(
        world_id=preview.world_id,
        npc_id=preview.npc_id,
        preset=NPCSimulationPresetResponse.model_validate(preview.preset.model_dump(mode="json")),
        graph=_npc_goal_graph_response(preview.graph),
        yaml_content=preview.yaml_content,
        validation=_authoring_validation_response(preview.validation),
        gate_allowed_to_save=preview.validation_gate.allowed_to_save,
        confirmation_required=preview.validation_gate.confirmation_required,
        applied_fields=preview.applied_fields,
    )


def _social_authoring_graph_response(graph: SocialAuthoringGraph) -> SocialAuthoringGraphResponse:
    return SocialAuthoringGraphResponse.model_validate(graph.model_dump(mode="json"))


def _item_economy_authoring_response(graph: ItemEconomyAuthoring) -> ItemEconomyAuthoringResponse:
    return ItemEconomyAuthoringResponse.model_validate(graph.normalized().model_dump(mode="json"))


def _rumor_crime_authoring_response(
    graph: RumorCrimeConsequenceAuthoring,
) -> RumorCrimeConsequenceAuthoringResponse:
    return RumorCrimeConsequenceAuthoringResponse.model_validate(graph.model_dump(mode="json"))


def _validation_graph_response(graph: ValidationGraph) -> ValidationGraphResponse:
    return ValidationGraphResponse.model_validate(graph.model_dump(mode="json"))


def _timeline_replay_response(timeline: TimelineReplay) -> TimelineReplayResponse:
    return TimelineReplayResponse.model_validate(timeline.model_dump(mode="json"))


def _authoring_preview_response(
    world_id: str,
    file_name: str,
    report: object,
) -> AuthoringFilePreviewResponse:
    return AuthoringFilePreviewResponse(
        world_id=world_id,
        file_name=file_name,
        parsed_ok=getattr(report, "parsed_ok"),
        validation_report=_authoring_validation_response(getattr(report, "validation_report")),
        normalized_yaml=getattr(report, "normalized_yaml"),
        diff_summary=AuthoringDiffSummaryResponse.model_validate(
            getattr(report, "diff_summary").model_dump(mode="json")
        ),
        affected_refs=getattr(report, "affected_refs"),
        potential_save_migration_required=getattr(
            report,
            "potential_save_migration_required",
        ),
        impact=_authoring_impact_response(getattr(report, "impact")),
    )


def _authoring_impact_response(report: object) -> AuthoringImpactAnalysisResponse:
    return AuthoringImpactAnalysisResponse.model_validate(report.model_dump(mode="json"))


def _authoring_validation_response(report: ValidationReport) -> AuthoringValidationResponse:
    return AuthoringValidationResponse(
        world_id=report.world_id,
        ok=report.ok,
        errors=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.errors
        ],
        warnings=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.warnings
        ],
        suggestions=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.suggestions
        ],
    )
