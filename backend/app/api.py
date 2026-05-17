from pydantic import BaseModel, Field

from app.core.state_delta import StateDelta


class VisibleTimeResponse(BaseModel):
    day: int
    minutes_of_day: int
    time_of_day: str
    formatted: str


class VisibleLocationResponse(BaseModel):
    id: str
    name: str
    exits: dict[str, str] = Field(default_factory=dict)


class VisibleObjectResponse(BaseModel):
    id: str


class VisibleNPCResponse(BaseModel):
    id: str
    mood: str
    relationship_to_player: int
    condition: str = "healthy"


class KnownFactResponse(BaseModel):
    id: str
    text: str | None = None
    tags: list[str] = Field(default_factory=list)


class VisibleQuestObjectiveResponse(BaseModel):
    id: str
    completed: bool = False


class VisibleQuestResponse(BaseModel):
    id: str
    title: str
    name: str
    description: str = ""
    status: str
    current_stage: str
    stage_title: str
    stage_description: str = ""
    objectives: list[VisibleQuestObjectiveResponse] = Field(default_factory=list)


class VisibleFactionResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    reputation: int
    band: str
    tags: list[str] = Field(default_factory=list)


class VisibleRumorResponse(BaseModel):
    id: str
    text_for_player: str
    truth_status: str
    spread_level: int
    tags: list[str] = Field(default_factory=list)


class VisibleCrimeResponse(BaseModel):
    id: str
    crime_type: str
    location_id: str
    severity: int
    status: str
    created_turn: int


class VisibleRelationshipResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    trust: int
    fear: int
    affinity: int
    obligation: int
    tags: list[str] = Field(default_factory=list)


class VisibleFactionConflictResponse(BaseModel):
    faction_id: str
    alert_level: int
    conflict_level: int
    relationships_to_other_factions: dict[str, int] = Field(default_factory=dict)
    conflict_tags: list[str] = Field(default_factory=list)


class VisibleCombatSummaryResponse(BaseModel):
    combat_id: str
    location_id: str
    status: str
    player_stance: str
    player_condition: str
    player_status_effects: list[str] = Field(default_factory=list)
    visible_combatants: list[str] = Field(default_factory=list)


class VisibleStateResponse(BaseModel):
    world_id: str
    turn: int
    time: VisibleTimeResponse
    location: VisibleLocationResponse
    inventory: list[VisibleObjectResponse] = Field(default_factory=list)
    visible_objects: list[VisibleObjectResponse] = Field(default_factory=list)
    visible_npcs: list[VisibleNPCResponse] = Field(default_factory=list)
    known_facts: list[KnownFactResponse] = Field(default_factory=list)
    quests: list[VisibleQuestResponse] = Field(default_factory=list)
    factions: list[VisibleFactionResponse] = Field(default_factory=list)
    known_rumors: list[VisibleRumorResponse] = Field(default_factory=list)
    known_crimes: list[VisibleCrimeResponse] = Field(default_factory=list)
    relationships: list[VisibleRelationshipResponse] = Field(default_factory=list)
    faction_conflicts: list[VisibleFactionConflictResponse] = Field(default_factory=list)
    active_combat: VisibleCombatSummaryResponse | None = None


class StartGameRequest(BaseModel):
    world_id: str | None = None


class StartGameResponse(BaseModel):
    session_id: str
    world_id: str
    visible_state: VisibleStateResponse
    turn: int


class GameInputRequest(BaseModel):
    session_id: str
    player_input: str = Field(min_length=1)


class GameInputResponse(BaseModel):
    narrative_text: str
    suggested_actions: list[str]
    visible_state: VisibleStateResponse
    turn: int


class GameStateResponse(BaseModel):
    session_id: str
    visible_state: VisibleStateResponse
    turn: int


class SaveSummaryResponse(BaseModel):
    save_id: str
    world_id: str
    world_name: str
    turn: int
    current_location_name: str
    formatted_time: str
    created_at: str
    updated_at: str
    player_summary: str | None = None
    enabled_mods: dict[str, str] = Field(default_factory=dict)


class SaveListResponse(BaseModel):
    saves: list[SaveSummaryResponse] = Field(default_factory=list)


class StudioValidationSummaryResponse(BaseModel):
    world_id: str
    ok: bool
    error_count: int = 0
    warning_count: int = 0


class StudioPlaytestSummaryResponse(BaseModel):
    available: bool = False
    recent_runs: int = 0
    latest_status: str | None = None


class StudioStatusResponse(BaseModel):
    local_only: bool = True
    engine_version: str
    schema_version: str
    backend_status: str
    worlds_count: int
    recent_saves: list[SaveSummaryResponse] = Field(default_factory=list)
    authoring_api_enabled: bool
    debug_api_enabled: bool
    performance_logging_enabled: bool
    llm_provider: str
    local_model_provider_status: str | None = None
    validation_summaries: list[StudioValidationSummaryResponse] = Field(default_factory=list)
    playtest_summary: StudioPlaytestSummaryResponse = Field(default_factory=StudioPlaytestSummaryResponse)


class StudioConfigSummaryResponse(BaseModel):
    local_only: bool = True
    llm_provider: str
    provider_status: str
    provider_sends_prompts_off_machine: bool
    authoring_api_enabled: bool
    debug_api_enabled: bool
    performance_logging_enabled: bool
    playtest_api_enabled: bool
    eval_api_enabled: bool
    database_configured: bool
    database_path_hint: str
    api_key_configured: bool
    privacy_notes: list[str] = Field(default_factory=list)


class NarrativeEvalCaseResultResponse(BaseModel):
    case_id: str
    category: str
    passed: bool
    skipped: bool = False
    failure_reasons: list[str] = Field(default_factory=list)


class NarrativeEvalReportResponse(BaseModel):
    run_id: str
    created_at: str
    total_cases: int
    passed: int
    failed: int
    skipped: int = 0
    failure_reasons: dict[str, list[str]] = Field(default_factory=dict)
    categories: dict[str, dict[str, int]] = Field(default_factory=dict)
    case_results: list[NarrativeEvalCaseResultResponse] = Field(default_factory=list)


class NarrativeEvalRecentResponse(BaseModel):
    local_only: bool = True
    reports: list[NarrativeEvalReportResponse] = Field(default_factory=list)


class SaveGameResponse(BaseModel):
    save_id: str
    session_id: str
    world_id: str
    turn: int


class DeleteSaveResponse(BaseModel):
    save_id: str
    deleted: bool = True


class LoadGameResponse(BaseModel):
    save_id: str
    session_id: str
    visible_state: VisibleStateResponse
    turn: int


class MigrationHistoryEntryResponse(BaseModel):
    migration_id: str
    source_version: str
    target_version: str
    description: str
    applied_at: str


class SaveMigrationStatusResponse(BaseModel):
    save_id: str
    engine_version: str
    schema_version: str
    world_id: str
    world_version: str
    content_pack_version: str
    needs_migration: bool
    target_schema_version: str
    migration_path: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MigrationInfoResponse(BaseModel):
    migration_id: str
    source_version: str
    target_version: str
    description: str


class MigrationListResponse(BaseModel):
    migrations: list[MigrationInfoResponse] = Field(default_factory=list)


class SaveMigrationResponse(BaseModel):
    save_id: str
    source_version: str
    target_version: str
    dry_run: bool
    backup_save_id: str | None = None
    success: bool
    warnings: list[str] = Field(default_factory=list)
    applied_migrations: list[MigrationHistoryEntryResponse] = Field(default_factory=list)


class DebugEventResponse(BaseModel):
    turn: int
    event_id: str
    actor_id: str
    action_type: str
    result: str
    state_deltas: list[StateDelta] = Field(default_factory=list)
    visible_to_player: bool
    created_at: str


class DebugEventListResponse(BaseModel):
    local_only: bool = True
    events: list[DebugEventResponse] = Field(default_factory=list)


class DebugPerformanceSampleResponse(BaseModel):
    sample_id: str
    name: str
    duration_ms: float
    started_at: str
    stage_durations_ms: dict[str, float] = Field(default_factory=dict)
    tags: dict[str, str] = Field(default_factory=dict)


class DebugPerformanceRecentResponse(BaseModel):
    local_only: bool = True
    enabled: bool
    samples: list[DebugPerformanceSampleResponse] = Field(default_factory=list)


class DebugPerformanceSummaryEntryResponse(BaseModel):
    name: str
    count: int
    total_duration_ms: float
    average_duration_ms: float
    max_duration_ms: float


class DebugPerformanceSummaryResponse(BaseModel):
    local_only: bool = True
    enabled: bool
    sample_count: int
    entries: list[DebugPerformanceSummaryEntryResponse] = Field(default_factory=list)


class PlaytestRunRequest(BaseModel):
    world_id: str = "mist_valley"
    agent_type: str = "random_valid_action_agent"
    steps: int = Field(default=25, ge=0, le=250)
    seed: int = 123
    save_load_check: bool = False


class PlaytestActionRecordResponse(BaseModel):
    step: int
    turn_before: int
    turn_after: int
    input_text: str
    action_type: str
    result: str
    event_id: str | None = None


class PlaytestFinalStateSummaryResponse(BaseModel):
    world_id: str
    turn: int
    location_id: str
    event_count: int


class PlaytestReportResponse(BaseModel):
    local_only: bool = True
    run_id: str
    created_at: str
    agent_type: str
    world_id: str
    seed: int
    steps_requested: int
    turns_run: int
    actions_taken: list[PlaytestActionRecordResponse] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    invariant_violations: list[str] = Field(default_factory=list)
    visibility_leaks: list[str] = Field(default_factory=list)
    save_load_failures: list[str] = Field(default_factory=list)
    final_state_summary: PlaytestFinalStateSummaryResponse


class PlaytestRecentResponse(BaseModel):
    local_only: bool = True
    reports: list[PlaytestReportResponse] = Field(default_factory=list)


class AuthoringValidationIssueResponse(BaseModel):
    severity: str
    file: str
    path: str
    code: str
    message: str
    ref_id: str | None = None
    suggestion: str | None = None


class AuthoringValidationResponse(BaseModel):
    world_id: str
    ok: bool
    errors: list[AuthoringValidationIssueResponse] = Field(default_factory=list)
    warnings: list[AuthoringValidationIssueResponse] = Field(default_factory=list)
    suggestions: list[AuthoringValidationIssueResponse] = Field(default_factory=list)


class AuthoringWorldSummaryResponse(BaseModel):
    world_id: str
    name: str | None = None
    description: str = ""
    version: str | None = None
    file_count: int = 0


class AuthoringWorldListResponse(BaseModel):
    local_only: bool = True
    worlds: list[AuthoringWorldSummaryResponse] = Field(default_factory=list)


class AuthoringWorldDetailResponse(BaseModel):
    local_only: bool = True
    world: AuthoringWorldSummaryResponse
    files: list[str] = Field(default_factory=list)
    validation: AuthoringValidationResponse


class AuthoringFileListResponse(BaseModel):
    local_only: bool = True
    world_id: str
    files: list[str] = Field(default_factory=list)


class AuthoringFileResponse(BaseModel):
    local_only: bool = True
    world_id: str
    file_name: str
    content: str


class AuthoringFileWriteRequest(BaseModel):
    content: str


class AuthoringDraftFileRequest(BaseModel):
    file_name: str
    proposed_content: str


class AuthoringDiffSummaryResponse(BaseModel):
    added_ids: list[str] = Field(default_factory=list)
    removed_ids: list[str] = Field(default_factory=list)
    changed_ids: list[str] = Field(default_factory=list)
    line_count_before: int = 0
    line_count_after: int = 0


class AuthoringImpactAnalysisResponse(BaseModel):
    removed_ids: list[str] = Field(default_factory=list)
    renamed_ids: list[str] = Field(default_factory=list)
    changed_location_exits: list[str] = Field(default_factory=list)
    removed_locations: list[str] = Field(default_factory=list)
    removed_npcs: list[str] = Field(default_factory=list)
    removed_items: list[str] = Field(default_factory=list)
    removed_facts: list[str] = Field(default_factory=list)
    removed_quests: list[str] = Field(default_factory=list)
    removed_factions: list[str] = Field(default_factory=list)
    may_break_saves: bool = False
    notes: list[str] = Field(default_factory=list)


class AuthoringFilePreviewResponse(BaseModel):
    local_only: bool = True
    world_id: str
    file_name: str
    parsed_ok: bool
    validation_report: AuthoringValidationResponse
    normalized_yaml: str | None = None
    diff_summary: AuthoringDiffSummaryResponse
    affected_refs: list[str] = Field(default_factory=list)
    potential_save_migration_required: bool = False
    impact: AuthoringImpactAnalysisResponse


class AuthoringFileWriteResponse(BaseModel):
    local_only: bool = True
    world_id: str
    file_name: str
    validation: AuthoringValidationResponse


class ScenarioTemplateOutputFileResponse(BaseModel):
    file_name: str
    content: str


class ScenarioTemplateResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    template_type: str
    required_variables: list[str] = Field(default_factory=list)
    optional_variables: dict[str, str] = Field(default_factory=dict)
    output_files: list[ScenarioTemplateOutputFileResponse] = Field(default_factory=list)
    validation_rules: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ScenarioTemplateListResponse(BaseModel):
    local_only: bool = True
    templates: list[ScenarioTemplateResponse] = Field(default_factory=list)


class ScenarioTemplateRenderRequest(BaseModel):
    variables: dict[str, str] = Field(default_factory=dict)
    target_world_id: str | None = None


class RenderedScenarioTemplateFileResponse(BaseModel):
    file_name: str
    content: str


class RenderedScenarioTemplateResponse(BaseModel):
    template_id: str
    template_type: str
    files: list[RenderedScenarioTemplateFileResponse] = Field(default_factory=list)


class ScenarioTemplatePreviewResponse(BaseModel):
    local_only: bool = True
    template: ScenarioTemplateResponse
    rendered: RenderedScenarioTemplateResponse
    validation_report: AuthoringValidationResponse | None = None
    writes_to_disk: bool = False


class QuestObjectiveNodeResponse(BaseModel):
    id: str
    text: str


class QuestStageNodeResponse(BaseModel):
    id: str
    title: str
    description: str = ""
    objectives: list[QuestObjectiveNodeResponse] = Field(default_factory=list)
    next_stages: list[str] = Field(default_factory=list)


class QuestTriggerNodeResponse(BaseModel):
    type: str
    id: str
    action: str
    objective_id: str | None = None
    next_stage: str | None = None


class QuestGraphNodeResponse(BaseModel):
    id: str
    title: str
    description: str = ""
    initial_stage: str
    visibility: str
    stages: list[QuestStageNodeResponse] = Field(default_factory=list)
    triggers: list[QuestTriggerNodeResponse] = Field(default_factory=list)


class QuestGraphEdgeResponse(BaseModel):
    source: str
    target: str
    type: str
    quest_id: str
    label: str | None = None


class QuestGraphResponse(BaseModel):
    local_only: bool = True
    world_id: str
    quests: list[QuestGraphNodeResponse] = Field(default_factory=list)
    edges: list[QuestGraphEdgeResponse] = Field(default_factory=list)


class QuestGraphPreviewRequest(BaseModel):
    graph: QuestGraphResponse


class QuestGraphPreviewResponse(BaseModel):
    local_only: bool = True
    world_id: str
    graph: QuestGraphResponse
    yaml_content: str
    validation: AuthoringValidationResponse


class AuthoringCreateWorldRequest(BaseModel):
    world_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    description: str = ""
    start_location_id: str = Field(default="start", pattern=r"^[A-Za-z0-9_-]+$")


class AuthoringCreateWorldResponse(BaseModel):
    local_only: bool = True
    world: AuthoringWorldSummaryResponse
    validation: AuthoringValidationResponse


class AuthoringModSummaryResponse(BaseModel):
    id: str
    name: str
    version: str
    engine_version_min: str
    engine_version_max: str | None = None
    content_schema_version: str = ""
    dependencies: list[str] = Field(default_factory=list)
    optional_dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    load_order_hint: int = 0
    compatible_worlds: list[str] = Field(default_factory=list)
    migration_notes: str = ""
    entry_worlds: list[str] = Field(default_factory=list)
    content_paths: list[str] = Field(default_factory=list)
    author: str | None = None
    description: str = ""


class AuthoringModListResponse(BaseModel):
    local_only: bool = True
    mods: list[AuthoringModSummaryResponse] = Field(default_factory=list)


class AuthoringModDetailResponse(BaseModel):
    local_only: bool = True
    mod: AuthoringModSummaryResponse
    validation: "AuthoringModValidationResponse | None" = None


class AuthoringModLoadOrderResponse(BaseModel):
    local_only: bool = True
    ok: bool
    load_order: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ArchiveExportResponse(BaseModel):
    local_only: bool = True
    export_type: str
    id: str
    file_name: str
    archive_base64: str


class ArchiveImportRequest(BaseModel):
    archive_base64: str
    overwrite: bool = False


class ArchiveImportResponse(BaseModel):
    local_only: bool = True
    imported: bool
    import_type: str
    id: str
    validation_ok: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    migration_needed: bool = False
    migration_warnings: list[str] = Field(default_factory=list)


class AuthoringModValidationResponse(BaseModel):
    local_only: bool = True
    mod_id: str
    ok: bool
    errors: list[AuthoringValidationIssueResponse] = Field(default_factory=list)
    warnings: list[AuthoringValidationIssueResponse] = Field(default_factory=list)
    suggestions: list[AuthoringValidationIssueResponse] = Field(default_factory=list)
    world_report_ids: list[str] = Field(default_factory=list)
