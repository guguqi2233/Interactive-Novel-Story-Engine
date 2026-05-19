from typing import Any

from pydantic import BaseModel, Field

from app.core.state_delta import StateDelta
from app.engine.content.world_branching import WorldBranch, WorldBranchCreateRequest, WorldDiff, WorldDiffDraftRequest
from app.engine.content.world_loader import MapVisualGraph
from app.roleplay.rp_scenario_templates import RPScenarioDraft, RPScenarioTemplate


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


class DialogueSessionResponse(BaseModel):
    session_id: str
    save_id: str | None = None
    game_session_id: str | None = None
    participant_ids: list[str] = Field(default_factory=list)
    focus_npc_id: str
    started_turn: int
    last_turn: int
    dialogue_mode: str
    active_topics: list[str] = Field(default_factory=list)
    scene_mood_preset_id: str | None = None
    safe_context_summary: str = ""
    status: str


class DialogueContextResponse(BaseModel):
    npc_known_facts: list[str] = Field(default_factory=list)
    emotional_summary: str = ""
    relationship_tone_summary: str = ""
    scene_mood_summary: str = ""
    example_dialogue_summaries: list[str] = Field(default_factory=list)
    rp_memory_summaries: list[str] = Field(default_factory=list)
    rp_prompt_style_summary: str = ""
    safe_context_summary: str = ""


class DialogueStartRequest(BaseModel):
    game_session_id: str
    focus_npc_id: str
    dialogue_mode: str = "focused"
    active_topics: list[str] = Field(default_factory=list)
    scene_mood_preset_id: str | None = None


class DialogueContinueRequest(BaseModel):
    dialogue_session_id: str
    player_input: str = Field(min_length=1)


class DialogueEndRequest(BaseModel):
    dialogue_session_id: str


class DialogueModeResponse(BaseModel):
    dialogue_session: DialogueSessionResponse
    dialogue_context: DialogueContextResponse
    narrative_text: str = ""
    visible_state: VisibleStateResponse
    turn: int
    output_ok: bool = True
    output_issues: list[str] = Field(default_factory=list)


class GroupDialogueSceneResponse(BaseModel):
    scene_id: str
    game_session_id: str | None = None
    participant_ids: list[str] = Field(default_factory=list)
    location_id: str
    active_speaker_id: str
    turn_order: list[str] = Field(default_factory=list)
    scene_topic: str = ""
    scene_mood: str = "neutral"
    scene_mood_preset_id: str | None = None
    visibility_scope: str = "player_visible"
    status: str


class GroupParticipantContextResponse(BaseModel):
    npc_id: str
    emotional_summary: str = ""
    relationship_tone_summary: str = ""
    scene_mood_summary: str = ""
    example_dialogue_summaries: list[str] = Field(default_factory=list)
    rp_prompt_style_summary: str = ""
    safe_context_summary: str = ""


class GroupDialogueStartRequest(BaseModel):
    game_session_id: str
    participant_ids: list[str] = Field(min_length=2)
    scene_topic: str = ""
    scene_mood: str = "neutral"
    scene_mood_preset_id: str | None = None
    active_speaker_id: str | None = None


class GroupDialogueNextSpeakerRequest(BaseModel):
    scene_id: str
    manual_focus_id: str | None = None


class GroupDialogueEndRequest(BaseModel):
    scene_id: str


class GroupDialogueSceneModeResponse(BaseModel):
    scene: GroupDialogueSceneResponse
    participant_contexts: list[GroupParticipantContextResponse] = Field(default_factory=list)
    narrative_text: str = ""
    visible_state: VisibleStateResponse
    turn: int


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
    selected_prompt_profile_id: str = "default_safe"
    prompt_profiles: list["PromptProfileResponse"] = Field(default_factory=list)
    privacy_notes: list[str] = Field(default_factory=list)


class PromptProfileTemperatureOverridesResponse(BaseModel):
    narrator: float | None = None
    intent_parser: float | None = None
    memory: float | None = None


class RPPromptProfileResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    dialogue_depth: str
    emotional_intensity: str
    prose_density: str
    response_length_policy: str
    perspective: str
    inner_thought_policy: str
    sensuality_policy: str
    hidden_fact_policy: str = "deny"
    state_modification_policy: str = "deny"


class PromptProfileResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    provider_filter: list[str] = Field(default_factory=list)
    model_filter: list[str] = Field(default_factory=list)
    narrator_style: str
    intent_parser_prompt_variant: str
    narrator_prompt_variant: str
    memory_prompt_variant: str
    temperature_overrides: PromptProfileTemperatureOverridesResponse
    max_output_tokens: int | None = None
    scene_mood_preset_id: str | None = None
    rp_profile: RPPromptProfileResponse
    enabled: bool
    matches_current_provider: bool = False


class PromptProfileListResponse(BaseModel):
    local_only: bool = True
    selected_profile_id: str
    profiles: list[PromptProfileResponse] = Field(default_factory=list)


class PromptProfileSelectRequest(BaseModel):
    profile_id: str


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


class DebugNPCSimulationSummaryResponse(BaseModel):
    npc_id: str
    location_id: str
    alive: bool
    condition: str
    intent_count: int = 0
    plan_count: int = 0
    active_goal_id: str | None = None
    known_fact_ids: list[str] = Field(default_factory=list)
    hidden_fact_ids: list[str] = Field(default_factory=list)
    debug_reason_count: int = 0


class DebugNPCSimulationDetailResponse(DebugNPCSimulationSummaryResponse):
    intent_queue: list[dict[str, Any]] = Field(default_factory=list)
    plans: list[dict[str, Any]] = Field(default_factory=list)
    goals: list[dict[str, Any]] = Field(default_factory=list)
    emotional_state: dict[str, Any] = Field(default_factory=dict)
    social_disposition: dict[str, Any] = Field(default_factory=dict)
    faction_duties: list[dict[str, Any]] = Field(default_factory=list)
    relationship_behavior_summary: dict[str, Any] = Field(default_factory=dict)
    known_rumor_ids: list[str] = Field(default_factory=list)
    known_crime_ids: list[str] = Field(default_factory=list)
    debug_decision_reasons: list[dict[str, str]] = Field(default_factory=list)


class DebugNPCSimulationListResponse(BaseModel):
    local_only: bool = True
    npcs: list[DebugNPCSimulationSummaryResponse] = Field(default_factory=list)


class DebugNPCSimulationTickListResponse(BaseModel):
    local_only: bool = True
    ticks: list[DebugEventResponse] = Field(default_factory=list)


class DebugNPCSimulationDryRunResponse(BaseModel):
    local_only: bool = True
    dry_run: bool = True
    result: dict[str, Any]
    state_unchanged: bool = True


class NPCBehaviorTimelineEntryResponse(BaseModel):
    turn: int
    event_id: str
    behavior_type: str
    intent_id: str | None = None
    plan_id: str | None = None
    location_id: str | None = None
    safe_summary: str = ""
    debug_reason_redacted: str | None = None


class NPCBehaviorTimelineResponse(BaseModel):
    local_only: bool = True
    source_type: str
    source_id: str
    npc_id: str
    entries: list[NPCBehaviorTimelineEntryResponse] = Field(default_factory=list)


class TimelineStateDiffResponse(BaseModel):
    path: str
    operation: str
    reason: str | None = None
    visible_to_player: bool = False


class TimelineEventViewResponse(BaseModel):
    turn: int
    event_id: str
    actor_id: str
    action_type: str
    result: str
    target_id: str | None = None
    visible_to_player: bool
    event_kind: str
    state_deltas: list[StateDelta] = Field(default_factory=list)
    visible_changes: list[TimelineStateDiffResponse] = Field(default_factory=list)
    delta_count: int = 0
    created_at: str


class TimelineTurnGroupResponse(BaseModel):
    turn: int
    events: list[TimelineEventViewResponse] = Field(default_factory=list)
    event_count: int = 0
    delta_count: int = 0


class ReplayCheckpointResponse(BaseModel):
    turn: int
    event_id: str
    checksum: str
    delta_count: int


class ReplaySummaryResponse(BaseModel):
    event_count: int
    final_state_checksum: str
    invariant_violations: list[str] = Field(default_factory=list)
    failed_event_id: str | None = None
    checkpoints: list[ReplayCheckpointResponse] = Field(default_factory=list)


class TimelineReplayResponse(BaseModel):
    local_only: bool = True
    source_type: str
    source_id: str
    turns: list[TimelineTurnGroupResponse] = Field(default_factory=list)
    event_count: int = 0
    delta_count: int = 0
    replay_summary: ReplaySummaryResponse | None = None


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
    confirm_warnings: bool = False


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
    confirmation_required: bool = False
    saved: bool = True


class WorldBranchListResponse(BaseModel):
    local_only: bool = True
    world_id: str
    branches: list[WorldBranch] = Field(default_factory=list)


class WorldBranchCreateResponse(BaseModel):
    local_only: bool = True
    branch: WorldBranch
    active_session_note: str = "Branch operations do not modify active sessions. Restart or reload to use branch content."


class WorldDiffResponse(BaseModel):
    local_only: bool = True
    diff: WorldDiff
    active_session_note: str = "Diff operations do not modify active GameState."


class AuthoringMapGraphResponse(BaseModel):
    local_only: bool = True
    world_id: str
    graph: MapVisualGraph


class AuthoringMapGraphRequest(BaseModel):
    graph: MapVisualGraph
    confirm_warnings: bool = False


class AuthoringMapPreviewResponse(BaseModel):
    local_only: bool = True
    world_id: str
    graph: MapVisualGraph
    yaml_content: str
    validation: AuthoringValidationResponse
    confirmation_required: bool = False
    diff_summary: AuthoringDiffSummaryResponse | None = None
    impact: AuthoringImpactAnalysisResponse | None = None


class AuthoringMapWriteResponse(BaseModel):
    local_only: bool = True
    world_id: str
    graph: MapVisualGraph
    validation: AuthoringValidationResponse
    confirmation_required: bool = False
    saved: bool = True


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
    confirm_apply: bool = False


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
    target_world_id: str | None = None


class ScenarioTemplateApplyResponse(ScenarioTemplatePreviewResponse):
    applied: bool = True


class RPScenarioTemplateListResponse(BaseModel):
    local_only: bool = True
    templates: list[RPScenarioTemplate] = Field(default_factory=list)


class RPScenarioTemplateRenderRequest(BaseModel):
    game_session_id: str | None = None
    participant_ids: list[str] = Field(default_factory=list)
    confirm_apply: bool = False


class RPScenarioTemplatePreviewResponse(BaseModel):
    local_only: bool = True
    template: RPScenarioTemplate
    draft: RPScenarioDraft
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    writes_to_disk: bool = False
    modifies_game_state: bool = False
    requires_confirmation: bool = True
    applied: bool = False


class QuestObjectiveNodeResponse(BaseModel):
    id: str
    text: str
    visibility: str = "public"
    hidden_authoring_note: str | None = None
    x: float = 0.0
    y: float = 0.0


class QuestStageNodeResponse(BaseModel):
    id: str
    title: str
    description: str = ""
    objectives: list[QuestObjectiveNodeResponse] = Field(default_factory=list)
    next_stages: list[str] = Field(default_factory=list)
    failure_stages: list[str] = Field(default_factory=list)
    alternate_stages: list[str] = Field(default_factory=list)
    x: float = 0.0
    y: float = 0.0


class QuestTriggerNodeResponse(BaseModel):
    type: str
    id: str
    action: str
    objective_id: str | None = None
    next_stage: str | None = None
    x: float = 0.0
    y: float = 0.0


class QuestRewardNodeResponse(BaseModel):
    id: str
    text: str
    reward_type: str = "generic"
    x: float = 0.0
    y: float = 0.0


class QuestConsequenceNodeResponse(BaseModel):
    id: str
    text: str
    consequence_type: str = "generic"
    x: float = 0.0
    y: float = 0.0


class QuestGraphNodeResponse(BaseModel):
    id: str
    title: str
    description: str = ""
    initial_stage: str
    visibility: str
    stages: list[QuestStageNodeResponse] = Field(default_factory=list)
    triggers: list[QuestTriggerNodeResponse] = Field(default_factory=list)
    rewards: list[QuestRewardNodeResponse] = Field(default_factory=list)
    consequences: list[QuestConsequenceNodeResponse] = Field(default_factory=list)
    x: float = 0.0
    y: float = 0.0


class QuestGraphEdgeResponse(BaseModel):
    source: str
    target: str
    type: str
    quest_id: str
    label: str | None = None
    source_stage_id: str | None = None
    target_stage_id: str | None = None
    condition: dict[str, str] | None = None


class QuestGraphResponse(BaseModel):
    local_only: bool = True
    world_id: str
    quests: list[QuestGraphNodeResponse] = Field(default_factory=list)
    edges: list[QuestGraphEdgeResponse] = Field(default_factory=list)
    quest_nodes: list[QuestGraphNodeResponse] = Field(default_factory=list)
    stage_nodes: list[QuestStageNodeResponse] = Field(default_factory=list)
    objective_nodes: list[QuestObjectiveNodeResponse] = Field(default_factory=list)
    trigger_nodes: list[QuestTriggerNodeResponse] = Field(default_factory=list)
    reward_nodes: list[QuestRewardNodeResponse] = Field(default_factory=list)
    consequence_nodes: list[QuestConsequenceNodeResponse] = Field(default_factory=list)
    failure_path_edges: list[QuestGraphEdgeResponse] = Field(default_factory=list)
    optional_path_edges: list[QuestGraphEdgeResponse] = Field(default_factory=list)


class QuestGraphPreviewRequest(BaseModel):
    graph: QuestGraphResponse
    confirm_warnings: bool = False


class QuestGraphScenarioDraftResponse(BaseModel):
    local_only: bool = True
    world_id: str
    scenario: dict[str, Any]
    validation: AuthoringValidationResponse


class QuestGraphPreviewResponse(BaseModel):
    local_only: bool = True
    world_id: str
    graph: QuestGraphResponse
    yaml_content: str
    validation: AuthoringValidationResponse
    confirmation_required: bool = False


class QuestGraphSaveResponse(BaseModel):
    local_only: bool = True
    world_id: str
    graph: QuestGraphResponse
    yaml_content: str
    validation: AuthoringValidationResponse
    saved: bool
    confirmation_required: bool = False


class NPCGoalNodeResponse(BaseModel):
    id: str
    description: str = ""
    priority: int = 0
    status: str = "inactive"
    conditions: list[str] = Field(default_factory=list)
    desired_state: dict[str, object] = Field(default_factory=dict)
    allowed_actions: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)


class NPCGoalAuthoringNodeResponse(BaseModel):
    npc_id: str
    name: str
    hidden: bool = False
    goals: list[NPCGoalNodeResponse] = Field(default_factory=list)
    priorities: dict[str, int] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    current_goal_id: str | None = None
    plan_state: dict[str, object] = Field(default_factory=dict)


class NPCGoalAuthoringGraphResponse(BaseModel):
    local_only: bool = True
    world_id: str
    npcs: list[NPCGoalAuthoringNodeResponse] = Field(default_factory=list)


class NPCGoalAuthoringGraphRequest(BaseModel):
    graph: NPCGoalAuthoringGraphResponse


class NPCGoalAuthoringPreviewResponse(BaseModel):
    local_only: bool = True
    world_id: str
    graph: NPCGoalAuthoringGraphResponse
    yaml_content: str
    validation: AuthoringValidationResponse
    confirmation_required: bool = False


class NPCGoalAuthoringSaveResponse(NPCGoalAuthoringPreviewResponse):
    saved: bool = False


class NPCSimulationPresetResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    goals: list[NPCGoalNodeResponse] = Field(default_factory=list)
    intent_priorities: dict[str, int] = Field(default_factory=dict)
    faction_duties: list[dict[str, object]] = Field(default_factory=list)
    relationship_behavior_rules: list[dict[str, object]] = Field(default_factory=list)
    rumor_decision_tendencies: dict[str, object] = Field(default_factory=dict)
    social_disposition_defaults: dict[str, object] = Field(default_factory=dict)
    conflict_avoidance_defaults: dict[str, object] = Field(default_factory=dict)


class NPCSimulationPresetListResponse(BaseModel):
    local_only: bool = True
    presets: list[NPCSimulationPresetResponse] = Field(default_factory=list)


class NPCSimulationPresetApplyRequest(BaseModel):
    preset_id: str | None = None
    preset: NPCSimulationPresetResponse | None = None
    confirm_warnings: bool = False


class NPCSimulationPresetPreviewResponse(BaseModel):
    local_only: bool = True
    world_id: str
    npc_id: str
    preset: NPCSimulationPresetResponse
    graph: NPCGoalAuthoringGraphResponse
    yaml_content: str
    validation: AuthoringValidationResponse
    gate_allowed_to_save: bool = False
    confirmation_required: bool = False
    applied_fields: list[str] = Field(default_factory=list)


class FactionAuthoringNodeResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    known_by_player: bool = False
    default_reputation: int = 0
    default_alert_level: int = 0
    default_conflict_level: int = 0
    tags: list[str] = Field(default_factory=list)
    conflict_tags: list[str] = Field(default_factory=list)
    visibility: str = "hidden"
    x: float = 0.0
    y: float = 0.0


class FactionAuthoringEdgeResponse(BaseModel):
    source_faction_id: str
    target_faction_id: str
    relation_type: str = "neutral"
    relation: int = 0
    conflict_level: int = 0
    visibility: str = "hidden"
    conflict_tags: list[str] = Field(default_factory=list)


class FactionAuthoringGraphResponse(BaseModel):
    world_id: str
    faction_nodes: list[FactionAuthoringNodeResponse] = Field(default_factory=list)
    factions: list[FactionAuthoringNodeResponse] = Field(default_factory=list)
    relation_edges: list[FactionAuthoringEdgeResponse] = Field(default_factory=list)
    conflict_edges: list[FactionAuthoringEdgeResponse] = Field(default_factory=list)
    alliance_edges: list[FactionAuthoringEdgeResponse] = Field(default_factory=list)
    hostility_edges: list[FactionAuthoringEdgeResponse] = Field(default_factory=list)
    visibility_fields: list[str] = Field(default_factory=list)
    conflict_tag_index: list[str] = Field(default_factory=list)


class RelationshipAuthoringNodeResponse(BaseModel):
    id: str
    label: str
    node_type: str
    hidden: bool = False
    x: float = 0.0
    y: float = 0.0


class RelationshipTonePreviewResponse(BaseModel):
    preset_id: str = "derived"
    summary: str = ""
    address_style: str = "neutral"
    formality: str = "medium"
    warmth: int = 0
    tension: int = 0
    intimacy: int = 0
    respect: int = 50
    resentment: int = 0
    fear: int = 0
    avoidance: int = 0
    trust_expression: str = "reserved"


class RelationshipTonePresetResponse(BaseModel):
    id: str
    label: str
    description: str = ""


class RelationshipAuthoringEdgeResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    trust: int = 0
    fear: int = 0
    affinity: int = 0
    obligation: int = 0
    tags: list[str] = Field(default_factory=list)
    known_by_player: bool = False
    hidden_relationship: bool = False
    hidden_authoring_note: str | None = None
    tone_preset: str | None = None
    rp_tone_preview: RelationshipTonePreviewResponse = Field(default_factory=RelationshipTonePreviewResponse)


class RelationshipAuthoringGraphResponse(BaseModel):
    world_id: str
    npc_nodes: list[RelationshipAuthoringNodeResponse] = Field(default_factory=list)
    nodes: list[RelationshipAuthoringNodeResponse] = Field(default_factory=list)
    relationship_edges: list[RelationshipAuthoringEdgeResponse] = Field(default_factory=list)
    relationships: list[RelationshipAuthoringEdgeResponse] = Field(default_factory=list)
    hidden_relationship_fields: list[str] = Field(default_factory=list)
    relationship_tone_presets: list[RelationshipTonePresetResponse] = Field(default_factory=list)
    rp_tone_preview_fields: list[str] = Field(default_factory=list)


class SocialAuthoringGraphResponse(BaseModel):
    local_only: bool = True
    world_id: str
    faction_graph: FactionAuthoringGraphResponse
    relationship_graph: RelationshipAuthoringGraphResponse


class SocialAuthoringGraphRequest(BaseModel):
    graph: SocialAuthoringGraphResponse
    confirm_warnings: bool = False


class SocialAuthoringPreviewResponse(BaseModel):
    local_only: bool = True
    world_id: str
    graph: SocialAuthoringGraphResponse
    yaml_contents: dict[str, str]
    validation: AuthoringValidationResponse
    confirmation_required: bool = False


class SocialAuthoringSaveResponse(SocialAuthoringPreviewResponse):
    saved: bool = False


class ItemEconomyItemResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    location_id: str | None = None
    owner_id: str | None = None
    container_id: str | None = None
    portable: bool = False
    visible: bool = True
    hidden: bool = False
    discoverable: bool = False
    discovered_by: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    base_price: int = 0
    tradeable: bool = True
    rarity: str = "common"
    locked: bool = False
    lock_difficulty: int = 0
    lock_state: str = "intact"
    stolen_item_policy: str = "refuse_stolen"


class MerchantEconomyNodeResponse(BaseModel):
    npc_id: str
    name: str
    hidden: bool = False
    merchant: bool = False
    shop_inventory: list[str] = Field(default_factory=list)
    buy_price_modifier: float = 1.0
    sell_price_modifier: float = 0.5


class ShopInventoryEdgeResponse(BaseModel):
    id: str
    merchant_id: str
    item_id: str
    buy_price: int = 0
    sell_price: int = 0
    player_visible: bool = True


class QuestRewardLinkResponse(BaseModel):
    id: str
    quest_id: str
    item_id: str
    reward_index: int = 0


class EconomyBalanceWarningResponse(BaseModel):
    code: str
    path: str
    message: str
    ref_id: str | None = None


class ItemEconomyAuthoringResponse(BaseModel):
    local_only: bool = True
    world_id: str
    items: list[ItemEconomyItemResponse] = Field(default_factory=list)
    merchants: list[MerchantEconomyNodeResponse] = Field(default_factory=list)
    item_nodes: list[ItemEconomyItemResponse] = Field(default_factory=list)
    merchant_nodes: list[MerchantEconomyNodeResponse] = Field(default_factory=list)
    shop_inventory_edges: list[ShopInventoryEdgeResponse] = Field(default_factory=list)
    price_modifier_fields: dict[str, dict[str, float]] = Field(default_factory=dict)
    stolen_item_policy: dict[str, str] = Field(default_factory=dict)
    quest_reward_links: list[QuestRewardLinkResponse] = Field(default_factory=list)
    balance_warnings: list[EconomyBalanceWarningResponse] = Field(default_factory=list)


class ItemEconomyAuthoringRequest(BaseModel):
    graph: ItemEconomyAuthoringResponse
    confirm_warnings: bool = False


class ItemEconomyAuthoringPreviewResponse(BaseModel):
    local_only: bool = True
    world_id: str
    graph: ItemEconomyAuthoringResponse
    yaml_contents: dict[str, str]
    validation: AuthoringValidationResponse
    confirmation_required: bool = False


class ItemEconomyAuthoringSaveResponse(ItemEconomyAuthoringPreviewResponse):
    saved: bool = False


class FactReferenceNodeResponse(BaseModel):
    id: str
    visibility: str
    tags: list[str] = Field(default_factory=list)


class FactionReferenceNodeResponse(BaseModel):
    id: str
    name: str
    known_by_player: bool = False


class NPCReferenceNodeResponse(BaseModel):
    id: str
    name: str
    hidden: bool = False


class QuestReferenceNodeResponse(BaseModel):
    id: str
    title: str = ""


class ConsequenceTriggerNodeResponse(BaseModel):
    id: str
    trigger_type: str = "event"
    ref_id: str | None = None
    label: str = ""


class WitnessConsequenceNodeResponse(BaseModel):
    id: str
    npc_id: str
    crime_id: str | None = None
    report_intent: str = "none"


class RumorAuthoringNodeResponse(BaseModel):
    id: str
    fact_id: str | None = None
    source_event_id: str | None = None
    text_for_player: str | None = None
    truth_status: str = "unknown"
    known_by_npcs: list[str] = Field(default_factory=list)
    known_by_factions: list[str] = Field(default_factory=list)
    known_by_player: bool = False
    spread_level: int = 0
    created_turn: int = 0
    tags: list[str] = Field(default_factory=list)
    delay_turns: int = 0
    cooldown_turns: int = 0
    dedupe_key: str | None = None


class CrimeConsequenceNodeResponse(BaseModel):
    id: str
    crime_type: str = "theft"
    trigger_condition: str = ""
    severity: int = 1
    visibility: str = "hidden"
    tags: list[str] = Field(default_factory=list)


class ReputationEffectNodeResponse(BaseModel):
    id: str
    faction_id: str
    amount: int = 0
    reason: str = ""
    delay_turns: int = 0
    cooldown_turns: int = 0
    dedupe_key: str | None = None


class NPCReactionConsequenceNodeResponse(BaseModel):
    id: str
    npc_id: str
    reaction: str = "notice"
    delay_turns: int = 0
    cooldown_turns: int = 0
    dedupe_key: str | None = None


class QuestTriggerConsequenceNodeResponse(BaseModel):
    id: str
    quest_id: str
    trigger_id: str
    action: str = "activate"
    delay_turns: int = 0
    cooldown_turns: int = 0
    dedupe_key: str | None = None


class ConsequenceGraphEdgeResponse(BaseModel):
    source: str
    target: str
    type: str
    label: str | None = None


class RumorCrimeConsequenceAuthoringResponse(BaseModel):
    local_only: bool = True
    world_id: str
    facts: list[FactReferenceNodeResponse] = Field(default_factory=list)
    factions: list[FactionReferenceNodeResponse] = Field(default_factory=list)
    npcs: list[NPCReferenceNodeResponse] = Field(default_factory=list)
    quests: list[QuestReferenceNodeResponse] = Field(default_factory=list)
    trigger_nodes: list[ConsequenceTriggerNodeResponse] = Field(default_factory=list)
    witness_nodes: list[WitnessConsequenceNodeResponse] = Field(default_factory=list)
    crime_nodes: list[CrimeConsequenceNodeResponse] = Field(default_factory=list)
    rumor_nodes: list[RumorAuthoringNodeResponse] = Field(default_factory=list)
    reputation_effect_nodes: list[ReputationEffectNodeResponse] = Field(default_factory=list)
    npc_reaction_nodes: list[NPCReactionConsequenceNodeResponse] = Field(default_factory=list)
    quest_effect_nodes: list[QuestTriggerConsequenceNodeResponse] = Field(default_factory=list)
    rumors: list[RumorAuthoringNodeResponse] = Field(default_factory=list)
    crimes: list[CrimeConsequenceNodeResponse] = Field(default_factory=list)
    reputation_effects: list[ReputationEffectNodeResponse] = Field(default_factory=list)
    npc_reactions: list[NPCReactionConsequenceNodeResponse] = Field(default_factory=list)
    quest_triggers: list[QuestTriggerConsequenceNodeResponse] = Field(default_factory=list)
    edges: list[ConsequenceGraphEdgeResponse] = Field(default_factory=list)
    impact_summary: dict[str, int] = Field(default_factory=dict)


class RumorCrimeConsequenceAuthoringRequest(BaseModel):
    graph: RumorCrimeConsequenceAuthoringResponse
    confirm_warnings: bool = False


class RumorCrimeConsequencePreviewResponse(BaseModel):
    local_only: bool = True
    world_id: str
    graph: RumorCrimeConsequenceAuthoringResponse
    yaml_contents: dict[str, str]
    validation: AuthoringValidationResponse
    confirmation_required: bool = False


class RumorCrimeConsequenceSaveResponse(RumorCrimeConsequencePreviewResponse):
    saved: bool = False


class ValidationGraphNodeResponse(BaseModel):
    id: str
    label: str
    type: str
    severity: str | None = None
    file: str | None = None
    path: str | None = None
    code: str | None = None


class ValidationGraphEdgeResponse(BaseModel):
    source: str
    target: str
    type: str
    label: str | None = None


class ValidationGraphIssueResponse(BaseModel):
    id: str
    severity: str
    file: str
    path: str
    code: str
    message: str
    ref_id: str | None = None
    suggestion: str | None = None


class ValidationGraphResponse(BaseModel):
    local_only: bool = True
    world_id: str
    nodes: list[ValidationGraphNodeResponse] = Field(default_factory=list)
    edges: list[ValidationGraphEdgeResponse] = Field(default_factory=list)
    issues: list[ValidationGraphIssueResponse] = Field(default_factory=list)


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
    confirm_apply: bool = False
    import_profile_id: str | None = None


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


class LocalPackageManifestResponse(BaseModel):
    package_id: str
    package_type: str
    version: str
    engine_version_min: str
    schema_version: str
    content_pack_version: str | None = None
    included_files: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    created_at: str
    notes: str = ""


class PackageDryRunResponse(BaseModel):
    local_only: bool = True
    ok: bool
    package_id: str
    package_type: str
    manifest: LocalPackageManifestResponse | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    compatibility_warnings: list[str] = Field(default_factory=list)
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
