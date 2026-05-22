const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type VisibleTime = {
  day: number;
  minutes_of_day: number;
  time_of_day: string;
  formatted: string;
};

export type VisibleLocation = {
  id: string;
  name: string;
  exits: Record<string, string>;
};

export type VisibleObject = {
  id: string;
};

export type VisibleNPC = {
  id: string;
  mood: string;
  relationship_to_player: number;
  condition?: string;
};

export type KnownFact = {
  id: string;
  text?: string | null;
  tags: string[];
};

export type VisibleQuest = {
  id: string;
  title?: string;
  name: string;
  description?: string;
  status: string;
  current_stage?: string;
  stage_title?: string;
  stage_description?: string;
  objectives?: VisibleQuestObjective[];
};

export type VisibleQuestObjective = {
  id: string;
  completed: boolean;
};

export type VisibleFaction = {
  id: string;
  name: string;
  description?: string;
  reputation?: number;
  band: string;
  tags: string[];
};

export type VisibleRumor = {
  id: string;
  text_for_player: string;
  truth_status: string;
  spread_level: number;
  tags: string[];
};

export type VisibleCrime = {
  id: string;
  crime_type: string;
  location_id: string;
  severity: number;
  status: string;
  created_turn: number;
};

export type VisibleRelationship = {
  id: string;
  source_id: string;
  target_id: string;
  relation_type: string;
  trust: number;
  fear: number;
  affinity: number;
  obligation: number;
  tags: string[];
};

export type VisibleFactionConflict = {
  faction_id: string;
  alert_level: number;
  conflict_level: number;
  relationships_to_other_factions: Record<string, number>;
  conflict_tags: string[];
};

export type VisibleActorCondition = {
  actor_id: string;
  condition: string;
};

export type ActiveCombatSummary = {
  combat_id: string;
  location_id: string;
  status: string;
  player_stance: string;
  player_condition: string;
  player_status_effects: string[];
  visible_combatants: string[];
};

export type StateDelta = {
  operation: string;
  path: string;
  value?: unknown;
  caused_by_event_id?: string | null;
  reason?: string | null;
  metadata: Record<string, string>;
};

export type DebugEvent = {
  turn: number;
  event_id: string;
  actor_id: string;
  action_type: string;
  result: string;
  state_deltas: StateDelta[];
  visible_to_player: boolean;
  created_at: string;
};

export type DebugEventListResponse = {
  local_only: boolean;
  events: DebugEvent[];
};

export type DebugNPCSimulationSummary = {
  npc_id: string;
  location_id: string;
  alive: boolean;
  condition: string;
  intent_count: number;
  plan_count: number;
  active_goal_id?: string | null;
  known_fact_ids: string[];
  hidden_fact_ids: string[];
  debug_reason_count: number;
};

export type DebugNPCSimulationDetail = DebugNPCSimulationSummary & {
  intent_queue: Record<string, unknown>[];
  plans: Record<string, unknown>[];
  goals: Record<string, unknown>[];
  emotional_state: Record<string, unknown>;
  social_disposition: Record<string, unknown>;
  faction_duties: Record<string, unknown>[];
  relationship_behavior_summary: Record<string, unknown>;
  known_rumor_ids: string[];
  known_crime_ids: string[];
  debug_decision_reasons: { intent_id: string; debug_only_reason: string }[];
};

export type DebugNPCSimulationListResponse = {
  local_only: boolean;
  npcs: DebugNPCSimulationSummary[];
};

export type DebugNPCSimulationTickListResponse = {
  local_only: boolean;
  ticks: DebugEvent[];
};

export type DebugNPCSimulationDryRunResponse = {
  local_only: boolean;
  dry_run: boolean;
  result: Record<string, unknown>;
  state_unchanged: boolean;
};

export type ModuleDebugActionSummary = {
  id: string;
  label: string;
  category: string;
  aliases: string[];
  event_type: string;
  target_types: string[];
  precondition_count: number;
  check_count: number;
  effect_count: number;
  state_delta_templates: string[];
};

export type ModuleDebugSummary = {
  local_only: boolean;
  module_id: string;
  name: string;
  version: string;
  module_type: string;
  permissions: Record<string, boolean>;
  state_schema_extensions: Record<string, unknown>[];
  event_types: Record<string, unknown>[];
  actions: ModuleDebugActionSummary[];
  hidden_details_redacted: boolean;
  contains_api_key: boolean;
  calls_llm: boolean;
};

export type ModuleDebugListResponse = {
  local_only: boolean;
  modules: ModuleDebugSummary[];
};

export type ModuleActionDryRunResponse = {
  local_only: boolean;
  dry_run: boolean;
  state_unchanged: boolean;
  module_id: string;
  action_id: string;
  preconditions_result: Record<string, unknown>[];
  checks_result: Record<string, unknown>[];
  selected_outcome: string;
  state_delta_preview: StateDelta[];
  event_preview: Record<string, unknown>;
  visibility_summary: Record<string, unknown>;
  hidden_facts_redacted: boolean;
  contains_api_key: boolean;
  calls_llm: boolean;
};

export type NPCBehaviorTimelineEntry = {
  turn: number;
  event_id: string;
  behavior_type: string;
  intent_id?: string | null;
  plan_id?: string | null;
  location_id?: string | null;
  safe_summary: string;
  debug_reason_redacted?: string | null;
};

export type NPCBehaviorTimelineResponse = {
  local_only: boolean;
  source_type: string;
  source_id: string;
  npc_id: string;
  entries: NPCBehaviorTimelineEntry[];
};

export type TimelineStateDiff = {
  path: string;
  operation: string;
  reason?: string | null;
  visible_to_player: boolean;
};

export type TimelineEventView = {
  turn: number;
  event_id: string;
  actor_id: string;
  action_type: string;
  result: string;
  target_id?: string | null;
  visible_to_player: boolean;
  event_kind: string;
  state_deltas: StateDelta[];
  visible_changes: TimelineStateDiff[];
  delta_count: number;
  created_at: string;
};

export type TimelineTurnGroup = {
  turn: number;
  events: TimelineEventView[];
  event_count: number;
  delta_count: number;
};

export type ReplayCheckpoint = {
  turn: number;
  event_id: string;
  checksum: string;
  delta_count: number;
};

export type ReplaySummary = {
  event_count: number;
  final_state_checksum: string;
  invariant_violations: string[];
  failed_event_id?: string | null;
  checkpoints: ReplayCheckpoint[];
};

export type TimelineReplayResponse = {
  local_only: boolean;
  source_type: string;
  source_id: string;
  turns: TimelineTurnGroup[];
  event_count: number;
  delta_count: number;
  replay_summary?: ReplaySummary | null;
};

export type GraphVisibility = "player_visible" | "debug_only";

export type GraphNode = {
  id: string;
  label: string;
  type: "npc" | "faction" | "player" | "location" | "quest";
  visibility: GraphVisibility;
  tags: string[];
};

export type GraphEdge = {
  source: string;
  target: string;
  type: string;
  weight?: number | null;
  label?: string | null;
  visibility: GraphVisibility;
  metadata_safe?: Record<string, string | number | boolean>;
};

export type GraphResponse = {
  local_only: boolean;
  scope: GraphVisibility;
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type AuthoringValidationIssue = {
  severity: string;
  file: string;
  path: string;
  code: string;
  message: string;
  ref_id?: string | null;
  suggestion?: string | null;
};

export type AuthoringValidation = {
  world_id: string;
  ok: boolean;
  errors: AuthoringValidationIssue[];
  warnings: AuthoringValidationIssue[];
  suggestions: AuthoringValidationIssue[];
};

export type AuthoringWorldSummary = {
  world_id: string;
  name?: string | null;
  description: string;
  version?: string | null;
  file_count: number;
};

export type AuthoringWorldListResponse = {
  local_only: boolean;
  worlds: AuthoringWorldSummary[];
};

export type AuthoringModSummary = {
  id: string;
  name: string;
  version: string;
  engine_version_min: string;
  engine_version_max?: string | null;
  content_schema_version: string;
  dependencies: string[];
  optional_dependencies: string[];
  conflicts: string[];
  load_order_hint: number;
  compatible_worlds: string[];
  migration_notes: string;
  entry_worlds: string[];
  content_paths: string[];
  author?: string | null;
  description: string;
};

export type AuthoringModListResponse = {
  local_only: boolean;
  mods: AuthoringModSummary[];
};

export type AuthoringModValidation = {
  local_only: boolean;
  mod_id: string;
  ok: boolean;
  errors: AuthoringValidationIssue[];
  warnings: AuthoringValidationIssue[];
  suggestions: AuthoringValidationIssue[];
  world_report_ids: string[];
};

export type AuthoringModDetailResponse = {
  local_only: boolean;
  mod: AuthoringModSummary;
  validation?: AuthoringModValidation | null;
};

export type AuthoringModLoadOrderResponse = {
  local_only: boolean;
  ok: boolean;
  load_order: string[];
  errors: string[];
};

export type ArchiveExportResponse = {
  local_only: boolean;
  export_type: string;
  id: string;
  file_name: string;
  archive_base64: string;
};

export type ArchiveImportResponse = {
  local_only: boolean;
  imported: boolean;
  import_type: string;
  id: string;
  validation_ok: boolean;
  errors: string[];
  warnings: string[];
  migration_needed: boolean;
  migration_warnings: string[];
};

export type ExportProfile = {
  profile_id: string;
  name: string;
  kind: "safe" | "authoring" | "strict";
  include_world: boolean;
  include_characters: boolean;
  include_templates: boolean;
  include_scenarios: boolean;
  include_prompt_profiles: boolean;
  include_hidden_authoring_data: boolean;
  redact_hidden_text: boolean;
  include_quality_reports: boolean;
  include_test_fixtures: boolean;
  forbids_api_keys: boolean;
};

export type ImportProfile = {
  profile_id: string;
  name: string;
  kind: "safe" | "authoring" | "strict";
  allow_overwrite: boolean;
  allow_hidden_authoring_data: boolean;
  require_validation: boolean;
  require_quality_gate: boolean;
  require_migration_check: boolean;
  reject_executables: boolean;
  reject_unknown_schema: boolean;
  forbids_api_keys: boolean;
};

export type ImportExportProfileCatalog = {
  export_profiles: ExportProfile[];
  import_profiles: ImportProfile[];
};

export type NarrativeEvalCaseResult = {
  case_id: string;
  category: string;
  passed: boolean;
  skipped: boolean;
  failure_reasons: string[];
};

export type NarrativeEvalReport = {
  run_id: string;
  created_at: string;
  total_cases: number;
  passed: number;
  failed: number;
  skipped: number;
  failure_reasons: Record<string, string[]>;
  categories: Record<string, Record<string, number>>;
  case_results: NarrativeEvalCaseResult[];
};

export type NarrativeEvalRecentResponse = {
  local_only: boolean;
  reports: NarrativeEvalReport[];
};

export type DebugPerformanceSample = {
  sample_id: string;
  name: string;
  duration_ms: number;
  started_at: string;
  stage_durations_ms: Record<string, number>;
  tags: Record<string, string>;
};

export type DebugPerformanceRecentResponse = {
  local_only: boolean;
  enabled: boolean;
  samples: DebugPerformanceSample[];
};

export type DebugPerformanceSummaryEntry = {
  name: string;
  count: number;
  total_duration_ms: number;
  average_duration_ms: number;
  max_duration_ms: number;
};

export type DebugPerformanceSummaryResponse = {
  local_only: boolean;
  enabled: boolean;
  sample_count: number;
  entries: DebugPerformanceSummaryEntry[];
};

export type WorldHealthCategoryScore = {
  dimension: string;
  score: number;
  status: string;
  explanation: string;
  blocker_count: number;
  error_count: number;
  warning_count: number;
};

export type WorldHealthScore = {
  health_id: string;
  world_id: string;
  created_at: string;
  overall_score: number;
  category_scores: WorldHealthCategoryScore[];
  blockers: string[];
  warnings: string[];
  recommended_actions: string[];
  source_report_ids: string[];
  summary: Record<string, unknown>;
};

export type ContentCoverageSummary = {
  total: number;
  covered: number;
  uncovered: number;
  coverage_percent: number;
  covered_ids: string[];
  uncovered_ids: string[];
  safe_summary: string;
};

export type ContentCoverageReport = {
  world_id: string;
  locations: ContentCoverageSummary;
  npcs: ContentCoverageSummary;
  items: ContentCoverageSummary;
  quests: ContentCoverageSummary;
  facts: ContentCoverageSummary;
  factions: ContentCoverageSummary;
  rumors: ContentCoverageSummary;
  crimes: ContentCoverageSummary;
  combat_encounters: ContentCoverageSummary;
  shops_trade: ContentCoverageSummary;
  hidden_entities_redacted: Record<string, number>;
  quality_report: Record<string, unknown>;
};

export type ContentCoverageSuggestion = {
  category: string;
  summary: string;
  recommended_tool: string;
  priority: string;
  safe_refs: string[];
};

export type ContentCoveragePlan = {
  world_id: string;
  genre: string;
  desired_playtime: string;
  desired_complexity: string;
  missing_location_types: ContentCoverageSuggestion[];
  missing_npc_archetypes: ContentCoverageSuggestion[];
  missing_quest_types: ContentCoverageSuggestion[];
  missing_clue_paths: ContentCoverageSuggestion[];
  missing_faction_hooks: ContentCoverageSuggestion[];
  missing_rp_scenes: ContentCoverageSuggestion[];
  missing_scenario_regressions: ContentCoverageSuggestion[];
  missing_playtest_paths: ContentCoverageSuggestion[];
  normal_report: boolean;
};

export type ContentCoveragePlanRequest = {
  target_world: string;
  genre?: string;
  desired_playtime?: string;
  desired_complexity?: string;
  current_content_coverage_report?: ContentCoverageReport | null;
};

export type PlaytestActionRecord = {
  step: number;
  turn_before: number;
  turn_after: number;
  input_text: string;
  action_type: string;
  result: string;
  event_id?: string | null;
};

export type PlaytestFinalStateSummary = {
  world_id: string;
  turn: number;
  location_id: string;
  event_count: number;
};

export type PlaytestReport = {
  local_only: boolean;
  run_id: string;
  created_at: string;
  agent_type: string;
  world_id: string;
  seed: number;
  steps_requested: number;
  turns_run: number;
  actions_taken: PlaytestActionRecord[];
  errors: string[];
  invariant_violations: string[];
  visibility_leaks: string[];
  save_load_failures: string[];
  final_state_summary: PlaytestFinalStateSummary;
};

export type PlaytestRecentResponse = {
  local_only: boolean;
  reports: PlaytestReport[];
};

export type PlaytestRunRequest = {
  world_id: string;
  agent_type: string;
  steps: number;
  seed: number;
  save_load_check: boolean;
};

export type PlaytestBatchRunRequest = {
  world_id: string;
  scenario_ids: string[];
  agent_types: string[];
  seeds: number[];
  steps: number;
  max_parallelism: number;
  stop_on_blocker: boolean;
  save_load_check: boolean;
};

export type PlaytestBatchRunItem = {
  run_index: number;
  scenario_id?: string | null;
  agent_type: string;
  seed: number;
  passed: boolean;
  blocker: boolean;
  duration_ms: number;
  turns_run: number;
  issue_count: number;
  safe_failure_reasons: string[];
  report: PlaytestReport;
};

export type PlaytestBatchRun = {
  local_only: boolean;
  run_id: string;
  created_at: string;
  world_id: string;
  total_runs: number;
  passed: number;
  failed: number;
  blockers: number;
  aggregate_issues: string[];
  coverage_summary: {
    action_types: Record<string, number>;
    final_locations: Record<string, number>;
    scenarios_run: string[];
    agents_run: string[];
    seeds_run: number[];
  };
  performance_summary: {
    total_duration_ms: number;
    average_duration_ms: number;
    max_duration_ms: number;
  };
  run_items: PlaytestBatchRunItem[];
  quality_report: Record<string, unknown>;
};

export type ScenarioRegressionCase = {
  id: string;
  world_id: string;
  name: string;
  description: string;
  initial_save?: string | null;
  input_sequence: string[];
  expected_visible_facts: string[];
  forbidden_visible_facts: string[];
  expected_quest_states: Record<string, string>;
  expected_inventory: string[];
  max_turns: number;
  tags: string[];
};

export type ScenarioRegressionCaseResult = {
  case_id: string;
  world_id: string;
  name: string;
  passed: boolean;
  failed_step?: number | null;
  failure_reasons: string[];
  expected_summary: Record<string, unknown>;
  actual_summary: Record<string, unknown>;
  hidden_leak_summary: string[];
  save_load_failure?: string | null;
};

export type ScenarioRegressionRun = {
  run_id: string;
  created_at: string;
  world_id?: string | null;
  total_cases: number;
  passed: number;
  failed: number;
  case_results: ScenarioRegressionCaseResult[];
};

export type ScenarioRegressionListResponse = {
  local_only: boolean;
  cases: ScenarioRegressionCase[];
};

export type ScenarioRegressionRunRequest = {
  world_id?: string | null;
  scenario_ids: string[];
};

export type ScenarioAuthoringListResponse = {
  local_only: boolean;
  scenarios: ScenarioRegressionCase[];
};

export type ScenarioAuthoringPreviewResponse = {
  local_only: boolean;
  scenario: ScenarioRegressionCase;
  validation: AuthoringValidation;
  writes_to_disk: boolean;
};

export type AuthoringWorldDetailResponse = {
  local_only: boolean;
  world: AuthoringWorldSummary;
  files: string[];
  validation: AuthoringValidation;
};

export type AuthoringFileListResponse = {
  local_only: boolean;
  world_id: string;
  files: string[];
};

export type AuthoringFileResponse = {
  local_only: boolean;
  world_id: string;
  file_name: string;
  content: string;
};

export type AuthoringFileWriteResponse = {
  local_only: boolean;
  world_id: string;
  file_name: string;
  validation: AuthoringValidation;
};

export type AuthoringDiffSummary = {
  added_ids: string[];
  removed_ids: string[];
  changed_ids: string[];
  line_count_before: number;
  line_count_after: number;
};

export type AuthoringImpactAnalysis = {
  removed_ids: string[];
  renamed_ids: string[];
  changed_location_exits: string[];
  removed_locations: string[];
  removed_npcs: string[];
  removed_items: string[];
  removed_facts: string[];
  removed_quests: string[];
  removed_factions: string[];
  may_break_saves: boolean;
  notes: string[];
};

export type AuthoringFilePreviewResponse = {
  local_only: boolean;
  world_id: string;
  file_name: string;
  parsed_ok: boolean;
  validation_report: AuthoringValidation;
  normalized_yaml?: string | null;
  diff_summary: AuthoringDiffSummary;
  affected_refs: string[];
  potential_save_migration_required: boolean;
  impact: AuthoringImpactAnalysis;
};

export type WorldBranch = {
  branch_id: string;
  world_id: string;
  base_world_id: string;
  name: string;
  created_at: string;
  description: string;
  content_path: string;
  parent_branch_id?: string | null;
};

export type WorldBranchListResponse = {
  world_id: string;
  branches: WorldBranch[];
};

export type MergeConflict = {
  conflict_id: string;
  conflict_type: string;
  file_name: string;
  entity_id: string;
  message: string;
  base?: Record<string, unknown> | null;
  ours?: Record<string, unknown> | null;
  theirs?: Record<string, unknown> | null;
};

export type MergeResolution = {
  conflict_id: string;
  choice: "base" | "ours" | "theirs" | "custom";
  custom?: Record<string, unknown> | null;
};

export type WorldMergeDraft = {
  world_id: string;
  ours: string;
  theirs: string;
  conflicts: MergeConflict[];
  resolutions: MergeResolution[];
  proposed_files: Record<string, string>;
  validation: AuthoringValidation;
  writes_to_disk: boolean;
  saved: boolean;
};

export type ContentDiffKind =
  | "file_diff"
  | "entity_diff"
  | "graph_diff"
  | "package_diff"
  | "schema_diff"
  | "visibility_diff"
  | "rp_profile_diff";

export type ContentDiffRef = {
  world_id?: string | null;
  branch_id?: string | null;
  files?: Record<string, string>;
};

export type ContentDiffEntity = {
  file_name: string;
  entity_id: string;
  entity_type: string;
  diff_type: ContentDiffKind;
  summary: string;
};

export type ContentDiffReview = {
  local_only: boolean;
  normal_view: boolean;
  diff_types: ContentDiffKind[];
  added: ContentDiffEntity[];
  removed: ContentDiffEntity[];
  changed: ContentDiffEntity[];
  renamed_candidates: string[];
  visibility_risk: string[];
  migration_impact: string[];
  validation_issues: string[];
};

export type AuthoringWorkflowStep = {
  id: string;
  label: string;
  tool_ref: string;
  action: string;
  requires_validation: boolean;
  writes_content: boolean;
};

export type AuthoringWorkflowPreset = {
  id: string;
  preset_type: string;
  name: string;
  description: string;
  steps: AuthoringWorkflowStep[];
  required_tools: string[];
  validation_gates: string[];
  suggested_templates: string[];
  quality_checks: string[];
};

export type AuthoringWorkflowPresetList = {
  local_only: boolean;
  presets: AuthoringWorkflowPreset[];
};

export type LocalContentType =
  | "world"
  | "character_pack"
  | "quest_pack"
  | "NPC_pack"
  | "template_pack"
  | "scenario_suite"
  | "prompt_profile"
  | "RP_profile"
  | "mod"
  | "script_package"
  | "campaign_starter";

export type LocalContentLibraryItem = {
  id: string;
  content_type: LocalContentType;
  name: string;
  version?: string | null;
  description: string;
  path_label: string;
  metadata: Record<string, unknown>;
  tags: string[];
  dependencies: string[];
  quality_summary: Record<string, unknown>;
  capabilities: string[];
};

export type LocalContentLibrary = {
  local_only: boolean;
  items: LocalContentLibraryItem[];
};

export type ModuleBrowserSummary = {
  package_id: string;
  name: string;
  version: string;
  package_type: string;
  permissions: Record<string, unknown>;
  validation_status: string;
  compatibility_status: string;
  permission_risk_level: string;
  local_only: boolean;
  safe_path_hint: string;
  warnings: string[];
  errors: string[];
};

export type ModuleBrowserDetail = {
  summary: ModuleBrowserSummary;
  manifest: Record<string, unknown>;
  dependencies: string[];
  conflicts: string[];
  target_worlds: string[];
  target_project_modes: string[];
};

export type ModulePermissionSummary = {
  package_id: string;
  package_type: string;
  permission_summary: Record<string, unknown>;
  dangerous_permissions: string[];
  risk_level: string;
};

export type ModCompatibilityEntry = {
  package_id: string;
  compatible: boolean;
  status: string;
  errors: string[];
  warnings: string[];
  load_order_index?: number | null;
};

export type ModCompatibilityMatrix = {
  ok: boolean;
  entries: ModCompatibilityEntry[];
  conflicts_summary: string[];
  load_order: string[];
};

export type ExtensionCertificationReport = {
  package_id: string;
  level: string;
  ok: boolean;
  reasons: string[];
  safe_summary: Record<string, string>;
};

export type ModQualityGateResult = {
  ok: boolean;
  package_id: string;
  blockers: string[];
  warnings: string[];
  certification_level: string;
  compatibility_status: string;
};

export type ModAuditRecord = {
  audit_id: string;
  project_id: string;
  package_id: string;
  action_type: string;
  actor: string;
  timestamp: string;
  result: string;
  safe_summary: string;
  risk_level: string;
  related_report_ids: string[];
};

export type AdvancedModuleDashboardItem = {
  module_id: string;
  enabled: boolean;
  state_extension_status: string;
  actions_provided: string[];
  migration_required: boolean;
  validation_status: string;
  quality_gate_status: string;
};

export type AdvancedModuleDashboardResponse = {
  local_only: boolean;
  world_id: string;
  modules: AdvancedModuleDashboardItem[];
};

export type AdvancedModuleDraftValidation = {
  local_only: boolean;
  world_id: string;
  ok: boolean;
  errors: string[];
  warnings: string[];
};

export type AdvancedModuleQualityGateResult = {
  passed: boolean;
  blockers: string[];
  warnings: string[];
  module_ids: string[];
};

export type AuthoringProjectStatus = {
  status: string;
  errors: number;
  warnings: number;
  last_run_at?: string | null;
  summary: string;
};

export type AuthoringRecentEdit = {
  label: string;
  content_type: string;
  updated_at: string;
};

export type AuthoringPackageStatus = {
  total: number;
  by_type: Record<string, number>;
};

export type AuthoringProjectSummary = {
  local_only: boolean;
  active_world?: string | null;
  active_world_name?: string | null;
  active_branch?: string | null;
  active_branch_name?: string | null;
  recent_edits: AuthoringRecentEdit[];
  validation_status: AuthoringProjectStatus;
  quality_gate_status: AuthoringProjectStatus;
  content_counts: Record<string, number>;
  open_warnings: string[];
  migration_impact: string[];
  package_status: AuthoringPackageStatus;
  hidden_details_redacted: boolean;
  sensitive_details_redacted: boolean;
};

export type ReferenceKind =
  | "location"
  | "NPC"
  | "item"
  | "fact"
  | "quest"
  | "quest_stage"
  | "faction"
  | "relationship"
  | "rumor"
  | "crime type"
  | "RP profile"
  | "scene mood"
  | "prompt profile";

export type ReferenceIndexItem = {
  id: string;
  kind: ReferenceKind;
  label: string;
  hidden: boolean;
  player_visible: boolean;
  authoring_safe_metadata: Record<string, unknown>;
};

export type ReferenceIndex = {
  local_only: boolean;
  world_id: string;
  items: ReferenceIndexItem[];
};

export type ValidationGraphNode = {
  id: string;
  label: string;
  type: "file" | "entity" | "reference" | "issue" | "schema" | string;
  severity?: string | null;
  file?: string | null;
  path?: string | null;
  code?: string | null;
};

export type ValidationGraphEdge = {
  source: string;
  target: string;
  type: "contains" | "references" | "missing_reference" | "invalid_value" | "visibility_risk" | "cycle" | string;
  label?: string | null;
};

export type ValidationGraphIssue = {
  id: string;
  severity: string;
  file: string;
  path: string;
  code: string;
  message: string;
  ref_id?: string | null;
  suggestion?: string | null;
};

export type ValidationGraph = {
  local_only: boolean;
  world_id: string;
  nodes: ValidationGraphNode[];
  edges: ValidationGraphEdge[];
  issues: ValidationGraphIssue[];
};

export type MapVisibility = "public" | "hidden" | "discoverable";
export type MapVisualEdgeType = "exit" | "one_way" | "locked" | "hidden" | "conditional";

export type MapVisualNode = {
  id: string;
  name: string;
  location_id: string;
  x: number;
  y: number;
  region_id?: string | null;
  layer_id?: string | null;
  tags: string[];
  visibility: MapVisibility;
  icon?: string | null;
  color_tag?: string | null;
  display_group?: string | null;
};

export type MapVisualEdge = {
  source_location_id: string;
  target_location_id: string;
  edge_type: MapVisualEdgeType;
  label: string;
  visibility: MapVisibility;
  travel_cost: number;
  discovery_rules: string[];
  unlock_condition?: string | null;
};

export type MapVisualRegion = {
  id: string;
  name: string;
  layer_id?: string | null;
  color_tag?: string | null;
};

export type MapVisualLayer = {
  id: string;
  name: string;
  order: number;
};

export type MapVisualGraph = {
  nodes: MapVisualNode[];
  edges: MapVisualEdge[];
  regions: MapVisualRegion[];
  layers: MapVisualLayer[];
  conditional_edges: MapVisualEdge[];
  locked_edges: MapVisualEdge[];
  hidden_edges: MapVisualEdge[];
};

export type AuthoringMapGraphResponse = {
  local_only: boolean;
  world_id: string;
  graph: MapVisualGraph;
};

export type AuthoringMapPreviewResponse = {
  local_only: boolean;
  world_id: string;
  graph: MapVisualGraph;
  yaml_content: string;
  validation: AuthoringValidation;
  confirmation_required: boolean;
  diff_summary?: AuthoringDiffSummary | null;
  impact?: AuthoringImpactAnalysis | null;
};

export type AuthoringMapWriteResponse = {
  local_only: boolean;
  world_id: string;
  graph: MapVisualGraph;
  validation: AuthoringValidation;
  confirmation_required: boolean;
  saved: boolean;
};

export type ScenarioTemplateOutputFile = {
  file_name: string;
  content: string;
};

export type ScenarioTemplate = {
  id: string;
  name: string;
  description: string;
  template_type: string;
  required_variables: string[];
  optional_variables: Record<string, string>;
  output_files: ScenarioTemplateOutputFile[];
  validation_rules: string[];
  tags: string[];
};

export type ScenarioTemplateListResponse = {
  local_only: boolean;
  templates: ScenarioTemplate[];
};

export type RenderedScenarioTemplate = {
  template_id: string;
  template_type: string;
  files: ScenarioTemplateOutputFile[];
};

export type ScenarioTemplatePreviewResponse = {
  local_only: boolean;
  template: ScenarioTemplate;
  rendered: RenderedScenarioTemplate;
  validation_report?: AuthoringValidation | null;
  writes_to_disk: boolean;
  target_world_id?: string | null;
};

export type ScenarioTemplateApplyResponse = ScenarioTemplatePreviewResponse & {
  applied: boolean;
};

export type TemplateWizardType =
  | "world"
  | "location_cluster"
  | "questline"
  | "npc_set"
  | "character_pack"
  | "dialogue_scene"
  | "group_rp_scene"
  | "faction_conflict"
  | "mystery_case";

export type TemplateWizardDraft = {
  id: string;
  name: string;
  template_type: TemplateWizardType;
  current_step: string;
  variables: Record<string, string>;
  target_world_id?: string | null;
  save_as_template: boolean;
};

export type TemplateWizardPreviewResponse = {
  draft: TemplateWizardDraft;
  generated_files: ScenarioTemplateOutputFile[];
  validation?: AuthoringValidation | null;
  writes_to_disk: boolean;
  applied: boolean;
  saved_template: boolean;
};

export type WorldPackWizardDraft = {
  world_id: string;
  name: string;
  genre: string;
  tone: string;
  description: string;
  starting_location: string;
  location_seed_count: number;
  npc_seed_count: number;
  quest_seed_count: number;
  enabled_systems: string[];
  default_prompt_profile: string;
  default_quality_profile: string;
  llm_assisted?: boolean;
  current_step?: string;
};

export type WorldPackWizardPreviewResponse = {
  local_only: boolean;
  draft: WorldPackWizardDraft;
  generated_files: ScenarioTemplateOutputFile[];
  validation?: AuthoringValidation | null;
  writes_to_disk: boolean;
  applied: boolean;
  gate_allowed_to_save: boolean;
  confirmation_required: boolean;
};

export type NPCPackGeneratorDraft = {
  target_world_id: string;
  pack_id: string;
  theme: string;
  faction_ids: string[];
  location_ids: string[];
  npc_count: number;
  archetypes: string[];
  rp_style: string;
  simulation_preset_ids: string[];
  relationship_density: number;
  hidden_secret_ratio: number;
  llm_assisted?: boolean;
};

export type NPCPackCandidate = {
  id: string;
  name: string;
  location_id: string;
  faction_id?: string | null;
  archetype: string;
  personality: string;
  rp_profile: Record<string, unknown>;
  voice_profile: Record<string, unknown>;
  hidden_secrets: { id: string; text: string; visibility: string; hidden: boolean }[];
};

export type NPCPackGeneratorPreviewResponse = {
  draft: NPCPackGeneratorDraft;
  generated: {
    npc_candidates: NPCPackCandidate[];
    rp_profiles: Record<string, Record<string, unknown>>;
    voice_profiles: Record<string, Record<string, unknown>>;
    relationship_candidates: Record<string, unknown>[];
    goal_candidates: Record<string, Record<string, unknown>[]>;
    schedule_candidates: Record<string, Record<string, unknown>[]>;
  };
  yaml_contents: Record<string, string>;
  validation: AuthoringValidation;
  writes_to_disk: boolean;
  applied: boolean;
  exported_pack?: Record<string, unknown> | null;
  confirmation_required: boolean;
};

export type QuestPackGeneratorDraft = {
  target_world_id: string;
  pack_id: string;
  theme: string;
  quest_count: number;
  involved_npcs: string[];
  involved_locations: string[];
  involved_factions: string[];
  required_facts: string[];
  mystery_mode: boolean;
  failure_paths_enabled: boolean;
  reward_policy: string;
  llm_assisted?: boolean;
};

export type QuestPackGeneratorPreviewResponse = {
  draft: QuestPackGeneratorDraft;
  generated: {
    quest_candidates: Record<string, unknown>[];
    fact_candidates: Record<string, unknown>[];
    rumor_candidates: Record<string, unknown>[];
    consequence_candidates: Record<string, unknown>[];
    scenario_regression_candidates: Record<string, unknown>[];
    quest_graph?: QuestGraphResponse | null;
    quality_checks: AuthoringValidation;
  };
  yaml_contents: Record<string, string>;
  validation: AuthoringValidation;
  writes_to_disk: boolean;
  applied: boolean;
  confirmation_required: boolean;
};

export type LocationClusterTemplate = {
  id: string;
  name: string;
  cluster_type: string;
  required_variables: string[];
  location_nodes: MapVisualNode[];
  exit_edges: MapVisualEdge[];
  optional_hidden_edges: MapVisualEdge[];
  default_visual_layout: string;
  tags: string[];
};

export type LocationClusterTemplateList = {
  local_only: boolean;
  templates: LocationClusterTemplate[];
};

export type LocationClusterPreviewResponse = {
  template: LocationClusterTemplate;
  target_world_id: string;
  graph: MapVisualGraph;
  validation: AuthoringValidation;
  yaml_content: string;
  writes_to_disk: boolean;
  applied: boolean;
  active_game_state_changed: boolean;
  confirmation_required: boolean;
};

export type RPScenarioTemplate = {
  id: string;
  name: string;
  description: string;
  scene_type: string;
  required_participants: string[];
  optional_participants: string[];
  suggested_mood: string;
  suggested_mood_preset_id?: string | null;
  suggested_dialogue_mode: string;
  opening_context: string;
  allowed_topics: string[];
  forbidden_topics: string[];
  required_visible_facts: string[];
  safety_notes: string[];
  tags: string[];
};

export type RPScenarioDraft = {
  draft_id: string;
  template_id: string;
  scene_type: string;
  participant_ids: string[];
  focus_npc_id?: string | null;
  dialogue_mode: string;
  scene_mood: string;
  scene_mood_preset_id?: string | null;
  active_topics: string[];
  opening_context_summary: string;
  dialogue_session_draft?: DialogueSession | null;
  group_scene_draft?: GroupDialogueScene | null;
};

export type RPScenarioTemplateListResponse = {
  local_only: boolean;
  templates: RPScenarioTemplate[];
};

export type RPScenarioTemplatePreviewResponse = {
  local_only: boolean;
  template: RPScenarioTemplate;
  draft: RPScenarioDraft;
  warnings: string[];
  errors: string[];
  writes_to_disk: boolean;
  modifies_game_state: boolean;
  requires_confirmation: boolean;
  applied: boolean;
};

export type QuestObjectiveNode = {
  id: string;
  text: string;
  visibility: string;
  hidden_authoring_note?: string | null;
  x: number;
  y: number;
};

export type QuestStageNode = {
  id: string;
  title: string;
  description: string;
  objectives: QuestObjectiveNode[];
  next_stages: string[];
  failure_stages: string[];
  alternate_stages: string[];
  x: number;
  y: number;
};

export type QuestTriggerNode = {
  type: string;
  id: string;
  action: string;
  objective_id?: string | null;
  next_stage?: string | null;
  x: number;
  y: number;
};

export type QuestRewardNode = {
  id: string;
  text: string;
  reward_type: string;
  x: number;
  y: number;
};

export type QuestConsequenceNode = {
  id: string;
  text: string;
  consequence_type: string;
  x: number;
  y: number;
};

export type QuestGraphNode = {
  id: string;
  title: string;
  description: string;
  initial_stage: string;
  visibility: string;
  stages: QuestStageNode[];
  triggers: QuestTriggerNode[];
  rewards: QuestRewardNode[];
  consequences: QuestConsequenceNode[];
  x: number;
  y: number;
};

export type QuestGraphEdge = {
  source: string;
  target: string;
  type: string;
  quest_id: string;
  label?: string | null;
  source_stage_id?: string | null;
  target_stage_id?: string | null;
  condition?: Record<string, string> | null;
};

export type QuestGraphResponse = {
  local_only: boolean;
  world_id: string;
  quests: QuestGraphNode[];
  edges: QuestGraphEdge[];
  quest_nodes: QuestGraphNode[];
  stage_nodes: QuestStageNode[];
  objective_nodes: QuestObjectiveNode[];
  trigger_nodes: QuestTriggerNode[];
  reward_nodes: QuestRewardNode[];
  consequence_nodes: QuestConsequenceNode[];
  failure_path_edges: QuestGraphEdge[];
  optional_path_edges: QuestGraphEdge[];
};

export type QuestGraphPreviewResponse = {
  local_only: boolean;
  world_id: string;
  graph: QuestGraphResponse;
  yaml_content: string;
  validation: AuthoringValidation;
  confirmation_required: boolean;
};

export type QuestGraphSaveResponse = {
  local_only: boolean;
  world_id: string;
  graph: QuestGraphResponse;
  yaml_content: string;
  validation: AuthoringValidation;
  saved: boolean;
  confirmation_required: boolean;
};

export type QuestGraphScenarioDraftResponse = {
  local_only: boolean;
  world_id: string;
  scenario: ScenarioRegressionCase;
  validation: AuthoringValidation;
};

export type NPCGoalNode = {
  id: string;
  description: string;
  priority: number;
  status: string;
  conditions: string[];
  desired_state: Record<string, unknown>;
  allowed_actions: string[];
  forbidden_actions: string[];
};

export type NPCGoalAuthoringNode = {
  npc_id: string;
  name: string;
  hidden: boolean;
  goals: NPCGoalNode[];
  priorities: Record<string, number>;
  constraints: string[];
  current_goal_id?: string | null;
  plan_state: Record<string, unknown>;
};

export type NPCGoalAuthoringGraph = {
  local_only: boolean;
  world_id: string;
  npcs: NPCGoalAuthoringNode[];
};

export type NPCGoalAuthoringPreviewResponse = {
  local_only: boolean;
  world_id: string;
  graph: NPCGoalAuthoringGraph;
  yaml_content: string;
  validation: AuthoringValidation;
  confirmation_required: boolean;
};

export type NPCGoalAuthoringSaveResponse = NPCGoalAuthoringPreviewResponse & {
  saved: boolean;
};

export type NPCSimulationPreset = {
  id: string;
  name: string;
  description: string;
  goals: NPCGoalNode[];
  intent_priorities: Record<string, number>;
  faction_duties: Record<string, unknown>[];
  relationship_behavior_rules: Record<string, unknown>[];
  rumor_decision_tendencies: Record<string, unknown>;
  social_disposition_defaults: Record<string, unknown>;
  conflict_avoidance_defaults: Record<string, unknown>;
};

export type NPCSimulationPresetListResponse = {
  local_only: boolean;
  presets: NPCSimulationPreset[];
};

export type NPCSimulationPresetPreviewResponse = {
  local_only: boolean;
  world_id: string;
  npc_id: string;
  preset: NPCSimulationPreset;
  graph: NPCGoalAuthoringGraph;
  yaml_content: string;
  validation: AuthoringValidation;
  gate_allowed_to_save: boolean;
  confirmation_required: boolean;
  applied_fields: string[];
};

export type FactionAuthoringNode = {
  id: string;
  name: string;
  description: string;
  known_by_player: boolean;
  default_reputation: number;
  default_alert_level: number;
  default_conflict_level: number;
  tags: string[];
  conflict_tags: string[];
  visibility: string;
  x: number;
  y: number;
};

export type FactionAuthoringEdge = {
  source_faction_id: string;
  target_faction_id: string;
  relation_type: string;
  relation: number;
  conflict_level: number;
  visibility: string;
  conflict_tags: string[];
};

export type FactionAuthoringGraph = {
  world_id: string;
  faction_nodes: FactionAuthoringNode[];
  factions: FactionAuthoringNode[];
  relation_edges: FactionAuthoringEdge[];
  conflict_edges: FactionAuthoringEdge[];
  alliance_edges: FactionAuthoringEdge[];
  hostility_edges: FactionAuthoringEdge[];
  visibility_fields: string[];
  conflict_tag_index: string[];
};

export type RelationshipAuthoringNode = {
  id: string;
  label: string;
  node_type: string;
  hidden: boolean;
  x: number;
  y: number;
};

export type RelationshipTonePreview = {
  preset_id: string;
  summary: string;
  address_style: string;
  formality: string;
  warmth: number;
  tension: number;
  intimacy: number;
  respect: number;
  resentment: number;
  fear: number;
  avoidance: number;
  trust_expression: string;
};

export type RelationshipTonePreset = {
  id: string;
  label: string;
  description: string;
};

export type RelationshipAuthoringEdge = {
  id: string;
  source_id: string;
  target_id: string;
  relation_type: string;
  trust: number;
  fear: number;
  affinity: number;
  obligation: number;
  tags: string[];
  known_by_player: boolean;
  hidden_relationship: boolean;
  hidden_authoring_note?: string | null;
  tone_preset?: string | null;
  rp_tone_preview: RelationshipTonePreview;
};

export type SocialAuthoringGraph = {
  local_only: boolean;
  world_id: string;
  faction_graph: FactionAuthoringGraph;
  relationship_graph: RelationshipAuthoringGraph;
};

export type RelationshipAuthoringGraph = {
  world_id: string;
  npc_nodes: RelationshipAuthoringNode[];
  nodes: RelationshipAuthoringNode[];
  relationship_edges: RelationshipAuthoringEdge[];
  relationships: RelationshipAuthoringEdge[];
  hidden_relationship_fields: string[];
  relationship_tone_presets: RelationshipTonePreset[];
  rp_tone_preview_fields: string[];
};

export type SocialAuthoringPreviewResponse = {
  local_only: boolean;
  world_id: string;
  graph: SocialAuthoringGraph;
  yaml_contents: Record<string, string>;
  validation: AuthoringValidation;
  confirmation_required: boolean;
};

export type SocialAuthoringSaveResponse = SocialAuthoringPreviewResponse & {
  saved: boolean;
};

export type ItemEconomyItem = {
  id: string;
  name: string;
  description: string;
  location_id?: string | null;
  owner_id?: string | null;
  container_id?: string | null;
  portable: boolean;
  visible: boolean;
  hidden: boolean;
  discoverable: boolean;
  discovered_by: string[];
  tags: string[];
  base_price: number;
  tradeable: boolean;
  rarity: string;
  locked: boolean;
  lock_difficulty: number;
  lock_state: string;
  stolen_item_policy: string;
};

export type MerchantEconomyNode = {
  npc_id: string;
  name: string;
  hidden: boolean;
  merchant: boolean;
  shop_inventory: string[];
  buy_price_modifier: number;
  sell_price_modifier: number;
};

export type ShopInventoryEdge = {
  id: string;
  merchant_id: string;
  item_id: string;
  buy_price: number;
  sell_price: number;
  player_visible: boolean;
};

export type QuestRewardLink = {
  id: string;
  quest_id: string;
  item_id: string;
  reward_index: number;
};

export type EconomyBalanceWarning = {
  code: string;
  path: string;
  message: string;
  ref_id?: string | null;
};

export type ItemEconomyAuthoring = {
  local_only: boolean;
  world_id: string;
  items: ItemEconomyItem[];
  merchants: MerchantEconomyNode[];
  item_nodes: ItemEconomyItem[];
  merchant_nodes: MerchantEconomyNode[];
  shop_inventory_edges: ShopInventoryEdge[];
  price_modifier_fields: Record<string, Record<string, number>>;
  stolen_item_policy: Record<string, string>;
  quest_reward_links: QuestRewardLink[];
  balance_warnings: EconomyBalanceWarning[];
};

export type ItemEconomyAuthoringPreviewResponse = {
  local_only: boolean;
  world_id: string;
  graph: ItemEconomyAuthoring;
  yaml_contents: Record<string, string>;
  validation: AuthoringValidation;
  confirmation_required: boolean;
};

export type ItemEconomyAuthoringSaveResponse = ItemEconomyAuthoringPreviewResponse & {
  saved: boolean;
};

export type FactReferenceNode = {
  id: string;
  visibility: string;
  tags: string[];
};

export type FactionReferenceNode = {
  id: string;
  name: string;
  known_by_player: boolean;
};

export type NPCReferenceNode = {
  id: string;
  name: string;
  hidden: boolean;
};

export type QuestReferenceNode = {
  id: string;
  title: string;
};

export type ConsequenceTriggerNode = {
  id: string;
  trigger_type: string;
  ref_id?: string | null;
  label: string;
};

export type WitnessConsequenceNode = {
  id: string;
  npc_id: string;
  crime_id?: string | null;
  report_intent: string;
};

export type RumorAuthoringNode = {
  id: string;
  fact_id?: string | null;
  source_event_id?: string | null;
  text_for_player?: string | null;
  truth_status: string;
  known_by_npcs: string[];
  known_by_factions: string[];
  known_by_player: boolean;
  spread_level: number;
  created_turn: number;
  tags: string[];
  delay_turns: number;
  cooldown_turns: number;
  dedupe_key?: string | null;
};

export type CrimeConsequenceNode = {
  id: string;
  crime_type: string;
  trigger_condition: string;
  severity: number;
  visibility: string;
  tags: string[];
};

export type ReputationEffectNode = {
  id: string;
  faction_id: string;
  amount: number;
  reason: string;
  delay_turns: number;
  cooldown_turns: number;
  dedupe_key?: string | null;
};

export type NPCReactionConsequenceNode = {
  id: string;
  npc_id: string;
  reaction: string;
  delay_turns: number;
  cooldown_turns: number;
  dedupe_key?: string | null;
};

export type QuestTriggerConsequenceNode = {
  id: string;
  quest_id: string;
  trigger_id: string;
  action: string;
  delay_turns: number;
  cooldown_turns: number;
  dedupe_key?: string | null;
};

export type ConsequenceGraphEdge = {
  source: string;
  target: string;
  type: string;
  label?: string | null;
};

export type RumorCrimeConsequenceAuthoring = {
  local_only: boolean;
  world_id: string;
  facts: FactReferenceNode[];
  factions: FactionReferenceNode[];
  npcs: NPCReferenceNode[];
  quests: QuestReferenceNode[];
  trigger_nodes: ConsequenceTriggerNode[];
  witness_nodes: WitnessConsequenceNode[];
  crime_nodes: CrimeConsequenceNode[];
  rumor_nodes: RumorAuthoringNode[];
  reputation_effect_nodes: ReputationEffectNode[];
  npc_reaction_nodes: NPCReactionConsequenceNode[];
  quest_effect_nodes: QuestTriggerConsequenceNode[];
  rumors: RumorAuthoringNode[];
  crimes: CrimeConsequenceNode[];
  reputation_effects: ReputationEffectNode[];
  npc_reactions: NPCReactionConsequenceNode[];
  quest_triggers: QuestTriggerConsequenceNode[];
  edges: ConsequenceGraphEdge[];
  impact_summary: Record<string, number>;
};

export type RumorCrimeConsequencePreviewResponse = {
  local_only: boolean;
  world_id: string;
  graph: RumorCrimeConsequenceAuthoring;
  yaml_contents: Record<string, string>;
  validation: AuthoringValidation;
  confirmation_required: boolean;
};

export type RumorCrimeConsequenceSaveResponse = RumorCrimeConsequencePreviewResponse & {
  saved: boolean;
};

export type VisibleState = {
  world_id: string;
  turn: number;
  time: VisibleTime;
  location: VisibleLocation;
  inventory: VisibleObject[];
  visible_objects: VisibleObject[];
  visible_npcs: VisibleNPC[];
  known_facts: KnownFact[];
  quests: VisibleQuest[];
  factions?: VisibleFaction[];
  known_rumors?: VisibleRumor[];
  known_crimes?: VisibleCrime[];
  relationships?: VisibleRelationship[];
  faction_conflicts?: VisibleFactionConflict[];
  player_condition?: VisibleActorCondition;
  active_combat?: ActiveCombatSummary | null;
};

export type StartGameResponse = {
  session_id: string;
  world_id: string;
  visible_state: VisibleState;
  turn: number;
};

export type GameInputResponse = {
  narrative_text: string;
  suggested_actions: string[];
  visible_state: VisibleState;
  turn: number;
};

export type DialogueSession = {
  session_id: string;
  save_id?: string | null;
  game_session_id?: string | null;
  participant_ids: string[];
  focus_npc_id: string;
  started_turn: number;
  last_turn: number;
  dialogue_mode: string;
  active_topics: string[];
  scene_mood_preset_id?: string | null;
  safe_context_summary: string;
  status: string;
};

export type DialogueContext = {
  npc_known_facts: string[];
  emotional_summary: string;
  relationship_tone_summary: string;
  scene_mood_summary: string;
  example_dialogue_summaries: string[];
  rp_memory_summaries: string[];
  rp_prompt_style_summary: string;
  safe_context_summary: string;
};

export type DialogueModeResponse = {
  dialogue_session: DialogueSession;
  dialogue_context: DialogueContext;
  narrative_text: string;
  visible_state: VisibleState;
  turn: number;
  output_ok: boolean;
  output_issues: string[];
};

export type GroupDialogueScene = {
  scene_id: string;
  game_session_id?: string | null;
  participant_ids: string[];
  location_id: string;
  active_speaker_id: string;
  turn_order: string[];
  scene_topic: string;
  scene_mood: string;
  scene_mood_preset_id?: string | null;
  visibility_scope: string;
  status: string;
};

export type GroupParticipantContext = {
  npc_id: string;
  emotional_summary: string;
  relationship_tone_summary: string;
  scene_mood_summary: string;
  example_dialogue_summaries: string[];
  rp_prompt_style_summary: string;
  safe_context_summary: string;
};

export type GroupDialogueSceneResponse = {
  scene: GroupDialogueScene;
  participant_contexts: GroupParticipantContext[];
  narrative_text: string;
  visible_state: VisibleState;
  turn: number;
};

export type GameStateResponse = {
  session_id: string;
  visible_state: VisibleState;
  turn: number;
};

export type SaveSummary = {
  save_id: string;
  world_id: string;
  world_name: string;
  turn: number;
  current_location_name: string;
  formatted_time: string;
  created_at: string;
  updated_at: string;
  player_summary?: string | null;
  enabled_mods?: Record<string, string>;
};

export type SaveListResponse = {
  saves: SaveSummary[];
};

export type StudioValidationSummary = {
  world_id: string;
  ok: boolean;
  error_count: number;
  warning_count: number;
};

export type StudioPlaytestSummary = {
  available: boolean;
  recent_runs: number;
  latest_status?: string | null;
};

export type StudioStatus = {
  local_only: boolean;
  engine_version: string;
  schema_version: string;
  backend_status: string;
  worlds_count: number;
  recent_saves: SaveSummary[];
  authoring_api_enabled: boolean;
  debug_api_enabled: boolean;
  performance_logging_enabled: boolean;
  llm_provider: string;
  local_model_provider_status?: string | null;
  validation_summaries: StudioValidationSummary[];
  playtest_summary: StudioPlaytestSummary;
};

export type ProjectWorkspace = {
  workspace_id: string;
  name: string;
  path_redacted: string;
  world_count: number;
  last_opened_at?: string | null;
  engine_version: string;
  schema_version: string;
  safe_status: "ok" | "missing" | "invalid" | "unsafe_path";
};

export type WorkspaceListResponse = {
  local_only: boolean;
  workspaces: ProjectWorkspace[];
};

export type WorkspaceTemplateType =
  | "blank_studio"
  | "novel_project"
  | "world_project"
  | "RP_project"
  | "script_package_project"
  | "module_development_project"
  | "campaign_project";

export type WorkspaceTemplate = {
  template_id: WorkspaceTemplateType;
  name: string;
  description: string;
  directories: string[];
  default_config_template: string;
  starter_world: boolean;
  docs_links: string[];
  recommended_workflow_presets: string[];
};

export type WorkspaceTemplateListResponse = {
  local_only: boolean;
  templates: WorkspaceTemplate[];
};

export type RecentProjectEntry = {
  workspace_id: string;
  display_name: string;
  path_redacted: string;
  last_opened_at: string;
  last_world_id?: string | null;
  safe_status: "ok" | "missing" | "invalid" | "unsafe_path";
};

export type RecentProjectsResponse = {
  local_only: boolean;
  projects: RecentProjectEntry[];
};

export type StudioConfigSummary = {
  local_only: boolean;
  llm_provider: string;
  provider_status: string;
  provider_sends_prompts_off_machine: boolean;
  authoring_api_enabled: boolean;
  debug_api_enabled: boolean;
  performance_logging_enabled: boolean;
  playtest_api_enabled: boolean;
  eval_api_enabled: boolean;
  database_configured: boolean;
  database_path_hint: string;
  api_key_configured: boolean;
  selected_prompt_profile_id: string;
  prompt_profiles: PromptProfile[];
  privacy_notes: string[];
};

export type LocalConfigIssue = {
  code: string;
  severity: "info" | "warning" | "error";
  message: string;
  safe_field: string;
};

export type LocalConfigSummary = {
  local_only: boolean;
  provider_type: string;
  model_id: string;
  debug_api_enabled: boolean;
  authoring_api_enabled: boolean;
  eval_api_enabled: boolean;
  playtest_api_enabled: boolean;
  usage_tracking_enabled: boolean;
  database_configured: boolean;
  database_path_hint: string;
  api_key_configured: boolean;
  local_paths_redacted: Record<string, string>;
  issues: LocalConfigIssue[];
};

export type LocalEnvTemplateResponse = {
  local_only: boolean;
  file_name: string;
  template: string;
  contains_real_secret: boolean;
  writes_to_disk: boolean;
};

export type LocalReleaseNoteSummary = {
  version: string;
  title: string;
  path: string;
  summary: string;
  upgrade_notes: string[];
  known_limitations: string[];
};

export type LocalUpdateNotesIndex = {
  local_only: boolean;
  current_version: string;
  release_notes: LocalReleaseNoteSummary[];
  warnings: string[];
};

export type DesktopHealthStatus = "pass" | "warning" | "error";

export type DesktopHealthCheckItem = {
  check_id: string;
  label: string;
  status: DesktopHealthStatus;
  message: string;
  safe_detail?: string | null;
};

export type DesktopHealthCheckReport = {
  local_only: boolean;
  overall_status: DesktopHealthStatus;
  checks: DesktopHealthCheckItem[];
  provider_config: LocalConfigSummary;
  current_workspace?: ProjectWorkspace | null;
  recent_errors: string[];
};

export type CrashReport = {
  id: string;
  timestamp: string;
  component: string;
  error_type: string;
  safe_message: string;
  stack_redacted: string;
  context_safe_summary: Record<string, string>;
};

export type CrashReportListResponse = {
  local_only: boolean;
  reports: CrashReport[];
};

export type PromptProfileTemperatureOverrides = {
  narrator?: number | null;
  intent_parser?: number | null;
  memory?: number | null;
};

export type RPPromptProfile = {
  id: string;
  name: string;
  description: string;
  dialogue_depth: string;
  emotional_intensity: string;
  prose_density: string;
  response_length_policy: string;
  perspective: string;
  inner_thought_policy: string;
  sensuality_policy: string;
  hidden_fact_policy: string;
  state_modification_policy: string;
};

export type PromptProfile = {
  id: string;
  name: string;
  description: string;
  provider_filter: string[];
  model_filter: string[];
  narrator_style: string;
  intent_parser_prompt_variant: string;
  narrator_prompt_variant: string;
  memory_prompt_variant: string;
  temperature_overrides: PromptProfileTemperatureOverrides;
  max_output_tokens?: number | null;
  scene_mood_preset_id?: string | null;
  rp_profile: RPPromptProfile;
  enabled: boolean;
  matches_current_provider: boolean;
};

export type PromptProfileListResponse = {
  local_only: boolean;
  selected_profile_id: string;
  profiles: PromptProfile[];
};

export type PromptABUseCase = "narrator" | "RP_dialogue" | "intent_parser" | "memory_summary";

export type PromptABTestCase = {
  id: string;
  input_text: string;
  visible_facts: string[];
  hidden_terms: string[];
  expected_schema?: string | null;
  tags: string[];
  max_prompt_preview_chars: number;
};

export type PromptABVariantResult = {
  profile_id: string;
  ok: boolean;
  latency_ms: number;
  schema_valid?: boolean | null;
  hidden_leak: boolean;
  consistency_flags: string[];
  style_metrics: Record<string, number>;
  output_summary_safe: string;
  error_class?: string | null;
  error_message_safe?: string | null;
};

export type PromptABCaseResult = {
  case_id: string;
  input_preview_redacted: string;
  variant_a: PromptABVariantResult;
  variant_b: PromptABVariantResult;
};

export type PromptABTestReport = {
  run_id: string;
  created_at: string;
  profile_a_id: string;
  profile_b_id: string;
  provider_id: string;
  model_id?: string | null;
  use_case: PromptABUseCase;
  pass_fail: string;
  cases: PromptABCaseResult[];
  schema_reliability: Record<string, number>;
  hidden_leak_flags: string[];
  consistency_flags: string[];
  style_metrics: Record<string, Record<string, number>>;
  latency_cost_summary: Record<string, number>;
  blockers: string[];
  warnings: string[];
};

export type PromptABTestRun = {
  run_id?: string;
  profile_a_id: string;
  profile_b_id: string;
  test_cases?: Partial<PromptABTestCase>[];
  provider_id?: string;
  model_id?: string | null;
  use_case?: PromptABUseCase;
  allow_real_provider?: boolean;
};

export type NarratorStyleExperiment = {
  run_id?: string;
  prompt_profile_id?: string;
  scene_mood_id?: string | null;
  perspective?: string;
  prose_density?: string;
  response_length?: string;
  sensory_focus?: string;
  genre_tone?: string;
  provider_id?: string;
  model_id?: string | null;
  allow_real_provider?: boolean;
  player_input?: string;
  visible_facts?: string[];
  hidden_terms?: string[];
  action_reason?: string;
  expected_action?: string;
};

export type NarratorStyleFinding = {
  check: string;
  passed: boolean;
  severity: string;
  safe_detail: string;
};

export type NarratorStyleReport = {
  run_id: string;
  created_at: string;
  prompt_profile_id: string;
  scene_mood_id?: string | null;
  provider_id: string;
  model_id?: string | null;
  pass_fail: string;
  output_summary_safe: string;
  style_score: number;
  latency_ms: number;
  suggested_actions: string[];
  findings: NarratorStyleFinding[];
  blockers: string[];
  warnings: string[];
};

export type VoiceProfileVariant = {
  tone?: string;
  sentence_length?: string;
  vocabulary_style?: string;
  catchphrases?: string[];
  speech_habits?: string[];
  silence_style?: string;
  emotional_tells?: string[];
};

export type NPCVoiceDialogueTestCase = {
  id?: string;
  player_line?: string;
  expected_emotional_tone?: string;
  npc_known_facts?: string[];
  unknown_fact_terms?: string[];
  hidden_terms?: string[];
};

export type NPCVoiceStyleExperiment = {
  run_id?: string;
  npc_id: string;
  voice_profile_variant?: VoiceProfileVariant;
  rp_prompt_profile_id?: string;
  example_dialogue_set?: string[];
  dialogue_test_cases?: NPCVoiceDialogueTestCase[];
  provider_id?: string;
  model_id?: string | null;
  allow_real_provider?: boolean;
};

export type NPCVoiceStyleFinding = {
  case_id: string;
  check: string;
  passed: boolean;
  severity: string;
  safe_detail: string;
};

export type NPCVoiceStyleReport = {
  run_id: string;
  created_at: string;
  npc_id: string;
  rp_prompt_profile_id: string;
  provider_id: string;
  model_id?: string | null;
  pass_fail: string;
  voice_consistency_score: number;
  latency_ms: number;
  output_summaries_safe: string[];
  findings: NPCVoiceStyleFinding[];
  blockers: string[];
  warnings: string[];
};

export type ContextInspectType =
  | "narrator"
  | "dialogue"
  | "group_rp"
  | "intent_parser"
  | "memory_summary"
  | "character_import";

export type ContextSection = {
  section_type: string;
  token_estimate: number;
  visibility_level: "normal" | "narrator_safe" | "npc_known" | "debug_only" | "hidden_redacted";
  safe_summary: string;
  content_redacted: string;
  excluded_reasons: string[];
};

export type ContextSnapshot = {
  local_only?: boolean;
  snapshot_id: string;
  context_type: ContextInspectType;
  total_token_estimate: number;
  sections: ContextSection[];
  raw_prompt_redacted?: string | null;
  raw_prompt_included: boolean;
};

export type ContextInspectRequest = {
  context_type?: ContextInspectType;
  actor_id?: string;
  location_id?: string;
  npc_id?: string | null;
  player_input?: string;
  include_debug_raw?: boolean;
  max_raw_chars?: number;
};

export type ModelCompatibilityUseCase =
  | "intent_parser"
  | "narrator"
  | "RP_dialogue"
  | "memory_summary"
  | "character_import"
  | "lorebook_classification"
  | "quest_draft"
  | "structured_json"
  | "embedding";

export type ModelUseCaseCompatibility = {
  provider_id: string;
  model_id: string;
  use_case: ModelCompatibilityUseCase;
  supported: boolean;
  recommended: boolean;
  caution: boolean;
  unsupported: boolean;
  reason: string;
  last_tested_at?: string | null;
};

export type ModelCompatibilityMatrix = {
  local_only?: boolean;
  matrix_id: string;
  generated_at: string;
  use_cases: ModelCompatibilityUseCase[];
  rows: ModelUseCaseCompatibility[];
  blockers: string[];
  warnings: string[];
  source_summary: Record<string, unknown>;
};

export type ProviderRoutingUseCase =
  | "intent_parser"
  | "narrator"
  | "RP_dialogue"
  | "memory_summary"
  | "character_import"
  | "lorebook_classification"
  | "quest_draft"
  | "structured_json"
  | "novel_draft"
  | "novel_rewrite"
  | "tavern_reply"
  | "world_intent_parse"
  | "world_narration"
  | "cross_mode_draft"
  | "quality_eval"
  | "cheap_summary";

export type ProviderRoutingRule = {
  use_case: ProviderRoutingUseCase;
  primary_provider_id: string;
  primary_model_id: string;
  fallback_provider_id?: string | null;
  fallback_model_id?: string | null;
  max_latency_ms?: number | null;
  max_cost_per_call?: number | null;
  require_json_support: boolean;
  require_local_only?: boolean | null;
  enabled: boolean;
};

export type ProviderRoutingConfig = {
  rules: ProviderRoutingRule[];
};

export type ProviderRoutingValidationReport = {
  ok: boolean;
  rule: ProviderRoutingRule;
  errors: string[];
  warnings: string[];
};

export type ProviderRoutingDecision = {
  use_case: ProviderRoutingUseCase;
  provider_id: string;
  model_id: string;
  used_fallback: boolean;
  reason: string;
  warnings: string[];
};

export type ProviderRoutingSummary = {
  local_only: boolean;
  rules: ProviderRoutingRule[];
  validation_reports: ProviderRoutingValidationReport[];
  warnings: string[];
};

export type ProviderRoutingPreview = {
  local_only: boolean;
  validation: ProviderRoutingValidationReport;
  decision?: ProviderRoutingDecision | null;
};

export type ProviderCapabilitySummary = {
  provider_id: string;
  provider_type: string;
  supports_text: boolean;
  supports_json: boolean;
  supports_streaming: boolean;
  supports_tools: boolean;
  supports_embeddings: boolean;
  context_window?: number | null;
  max_output_tokens?: number | null;
  recommended_use_cases: string[];
  json_reliability_rating?: string | null;
  requires_api_key: boolean;
  local_only: boolean;
  notes: string;
};

export type ModelCapabilitySummary = ProviderCapabilitySummary & {
  model_id: string;
};

export type ProviderCapabilityCatalog = {
  local_only: boolean;
  current_provider?: string | null;
  current_model?: string | null;
  api_key_configured: boolean;
  local_http_configured: boolean;
  providers: ProviderCapabilitySummary[];
  models: ModelCapabilitySummary[];
};

export type ProviderProfileSummary = {
  provider_profile_id: string;
  display_name: string;
  provider_type: string;
  base_url_configured?: boolean;
  base_url_source?: string | null;
  api_key_env?: string | null;
  secret_ref?: string | null;
  model_profiles: Array<{
    model_id: string;
    display_name?: string;
    context_window?: number | null;
    supports_text?: boolean;
    supports_json?: boolean;
    supports_tools?: boolean;
    supports_streaming?: boolean;
    recommended_use_cases?: string[];
  }>;
  capabilities?: string[];
  allowed_modes?: string[];
  enabled: boolean;
  cost_tracking?: boolean;
  safety_policy?: Record<string, unknown>;
  provider_notes?: string;
};

export type ProviderProfileDraft = {
  provider_profile_id: string;
  display_name: string;
  provider_type: string;
  base_url?: string | null;
  base_url_env?: string | null;
  api_key_env?: string | null;
  secret_ref?: string | null;
  model_profiles: Array<{
    model_id: string;
    display_name?: string;
    supports_json?: boolean;
    supports_streaming?: boolean;
    recommended_use_cases?: string[];
  }>;
  allowed_modes?: string[];
  default_timeout_seconds?: number;
  fallback_profile_ids?: string[];
  cost_tracking?: boolean;
  enabled?: boolean;
  requires_api_key?: boolean | null;
};

export type ModelCapabilityMatrixRow = {
  provider_profile_id: string;
  model_id: string;
  capabilities: Record<string, unknown>;
  allowed_modes: string[];
  recommended_use_cases: string[];
  warnings: string[];
  disabled_reasons: string[];
};

export type ProviderModelCapabilityMatrix = {
  matrix_id: string;
  project_id: string;
  generated_at: string;
  rows: ModelCapabilityMatrixRow[];
  warnings: string[];
};

export type ModelUsageRecord = {
  usage_id: string;
  project_id?: string;
  provider_id: string;
  provider_profile_id?: string | null;
  model_id: string;
  mode?: string;
  use_case: string;
  started_at: string;
  created_at?: string | null;
  duration_ms: number;
  input_tokens_estimated: number;
  output_tokens_estimated: number;
  total_tokens_estimated?: number;
  cost_estimated: number;
  currency?: string;
  success: boolean;
  error_type?: string | null;
  request_id?: string | null;
};

export type CostLatencyGroupSummary = {
  key: string;
  count: number;
  failures: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  total_tokens_estimated: number;
  total_cost_estimated: number;
};

export type CostLatencyUseCaseSummary = {
  use_case: string;
  count: number;
  failures: number;
  average_latency_ms: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  total_input_tokens_estimated: number;
  total_output_tokens_estimated: number;
  total_cost_estimated: number;
};

export type ModelUsageSummary = {
  local_only?: boolean;
  enabled: boolean;
  total_calls: number;
  successes: number;
  failures: number;
  error_rate: number;
  average_latency_ms: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  total_input_tokens_estimated: number;
  total_output_tokens_estimated: number;
  total_cost_estimated: number;
  by_use_case: CostLatencyUseCaseSummary[];
  by_provider: CostLatencyGroupSummary[];
  by_model: CostLatencyGroupSummary[];
  recent_failures: ModelUsageRecord[];
};

export type ProviderBenchmarkReport = {
  run_id: string;
  provider_id: string;
  model_id?: string | null;
  allow_real_provider: boolean;
  real_provider_blocked: boolean;
  total_cases: number;
  ok_cases: number;
  error_rate: number;
  schema_reliability?: number | null;
  average_latency_ms: number;
  hidden_leak_risk_count: number;
  blockers: string[];
  warnings: string[];
};

export type StructuredOutputReliabilityReport = {
  run_id: string;
  provider_id: string;
  model_id?: string | null;
  allow_real_provider: boolean;
  real_provider_blocked: boolean;
  total_cases: number;
  valid_json_rate: number;
  schema_valid_rate: number;
  retry_success_rate: number;
  hidden_policy_violation_rate: number;
  blockers: string[];
  warnings: string[];
};

export type PromptRegressionReport = {
  run_id: string;
  pass_fail: string;
  regressions: string[];
  improvements: string[];
  safety_blockers: string[];
  blockers: string[];
  warnings: string[];
};

export type LocalModelDiagnosticReport = {
  run_id: string;
  provider_id: string;
  model_id?: string | null;
  base_url_configured: boolean;
  allow_real_local_check: boolean;
  pass_fail: string;
  blockers: string[];
  warnings: string[];
};

export type PromptDiffReport = {
  local_only?: boolean;
  report_id: string;
  diff_type: string;
  added_sections: string[];
  removed_sections: string[];
  changed_sections: string[];
  safety_policy_changes: string[];
  token_delta: number;
  hidden_access_policy_changes: string[];
  state_modification_policy_changes: string[];
  blockers: string[];
  warnings: string[];
};

export type TokenBudgetUseCase =
  | "narrator"
  | "dialogue"
  | "group_rp"
  | "intent_parser"
  | "memory_summary"
  | "character_import";

export type TokenBudgetProfile = {
  id: string;
  use_case: TokenBudgetUseCase;
  max_total_tokens: number;
  reserved_output_tokens: number;
  max_memory_tokens: number;
  max_lore_tokens: number;
  max_recent_events_tokens: number;
  max_dialogue_examples_tokens: number;
  priority_order: string[];
  overflow_policy: "trim_low_priority" | "drop_low_priority" | "report_only";
};

export type TokenBudgetSectionReport = {
  section_type: string;
  original_tokens: number;
  allocated_tokens: number;
  final_tokens: number;
  trimmed_tokens: number;
  dropped: boolean;
  protected: boolean;
  safe_summary: string;
};

export type BudgetReport = {
  local_only?: boolean;
  report_id: string;
  profile: TokenBudgetProfile;
  input_token_estimate: number;
  available_context_tokens: number;
  reserved_output_tokens: number;
  final_context_tokens: number;
  overflow_tokens: number;
  sections: TokenBudgetSectionReport[];
  trimmed_sections: string[];
  dropped_sections: string[];
  warnings: string[];
  blockers: string[];
  trimmed_context: ContextSection[];
};

export type SaveGameResponse = {
  save_id: string;
  session_id: string;
  world_id: string;
  turn: number;
};

export type DeleteSaveResponse = {
  save_id: string;
  deleted: boolean;
};

export type LoadGameResponse = {
  save_id: string;
  session_id: string;
  visible_state: VisibleState;
  turn: number;
};

export type MigrationHistoryEntry = {
  migration_id: string;
  source_version: string;
  target_version: string;
  description: string;
  applied_at: string;
};

export type SaveMigrationStatus = {
  save_id: string;
  engine_version: string;
  schema_version: string;
  world_id: string;
  world_version: string;
  content_pack_version: string;
  needs_migration: boolean;
  target_schema_version: string;
  migration_path: string[];
  warnings: string[];
};

export type SaveMigrationResponse = {
  save_id: string;
  source_version: string;
  target_version: string;
  dry_run: boolean;
  backup_save_id?: string | null;
  success: boolean;
  warnings: string[];
  applied_migrations: MigrationHistoryEntry[];
};

export async function startGame(worldId?: string): Promise<StartGameResponse> {
  return requestJson<StartGameResponse>("/game/start", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      world_id: worldId
    })
  });
}

export async function fetchStudioStatus(): Promise<StudioStatus> {
  return requestJson<StudioStatus>("/studio/status");
}

export async function fetchStudioConfigSummary(): Promise<StudioConfigSummary> {
  return requestJson<StudioConfigSummary>("/studio/config-summary");
}

export async function fetchLocalConfigSummary(): Promise<LocalConfigSummary> {
  return requestJson<LocalConfigSummary>("/studio/config/summary");
}

export async function fetchLocalConfigIssues(): Promise<LocalConfigIssue[]> {
  return requestJson<LocalConfigIssue[]>("/studio/config/issues");
}

export async function generateLocalEnvTemplate(): Promise<LocalEnvTemplateResponse> {
  return requestJson<LocalEnvTemplateResponse>("/studio/config/generate-template", {
    method: "POST"
  });
}

export async function fetchLocalUpdateNotes(): Promise<LocalUpdateNotesIndex> {
  return requestJson<LocalUpdateNotesIndex>("/studio/update-notes");
}

export async function fetchDesktopHealth(): Promise<DesktopHealthCheckReport> {
  return requestJson<DesktopHealthCheckReport>("/studio/health");
}

export async function runDesktopHealthCheck(): Promise<DesktopHealthCheckReport> {
  return requestJson<DesktopHealthCheckReport>("/studio/health/check", {
    method: "POST"
  });
}

export async function fetchCrashReports(): Promise<CrashReportListResponse> {
  return requestJson<CrashReportListResponse>("/debug/crash-reports");
}

export async function fetchCrashReport(reportId: string): Promise<CrashReport> {
  return requestJson<CrashReport>(`/debug/crash-reports/${encodeURIComponent(reportId)}`);
}

export async function deleteCrashReport(reportId: string): Promise<{ local_only: boolean; deleted: boolean }> {
  return requestJson<{ local_only: boolean; deleted: boolean }>(`/debug/crash-reports/${encodeURIComponent(reportId)}`, {
    method: "DELETE"
  });
}

export async function fetchStudioWorkspaces(): Promise<WorkspaceListResponse> {
  return requestJson<WorkspaceListResponse>("/studio/workspaces");
}

export async function fetchWorkspaceTemplates(): Promise<WorkspaceTemplateListResponse> {
  return requestJson<WorkspaceTemplateListResponse>("/studio/workspace-templates");
}

export async function addStudioWorkspace(path: string, name?: string): Promise<ProjectWorkspace> {
  return requestJson<ProjectWorkspace>("/studio/workspaces", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ path, name })
  });
}

export async function createWorkspaceFromTemplate(
  templateId: WorkspaceTemplateType,
  path: string,
  name?: string
): Promise<ProjectWorkspace> {
  return requestJson<ProjectWorkspace>("/studio/workspaces/create-from-template", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ template_id: templateId, path, name })
  });
}

export async function selectStudioWorkspace(workspaceId: string, lastWorldId?: string): Promise<ProjectWorkspace> {
  return requestJson<ProjectWorkspace>("/studio/workspaces/select", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ workspace_id: workspaceId, last_world_id: lastWorldId })
  });
}

export async function fetchCurrentStudioWorkspace(): Promise<ProjectWorkspace> {
  return requestJson<ProjectWorkspace>("/studio/workspaces/current");
}

export async function fetchRecentProjects(): Promise<RecentProjectsResponse> {
  return requestJson<RecentProjectsResponse>("/studio/recent-projects");
}

export async function removeRecentProject(workspaceId: string): Promise<{ local_only: boolean; removed: boolean }> {
  return requestJson<{ local_only: boolean; removed: boolean }>(`/studio/recent-projects/${encodeURIComponent(workspaceId)}`, {
    method: "DELETE"
  });
}

export async function clearRecentProjects(): Promise<{ local_only: boolean; cleared: boolean }> {
  return requestJson<{ local_only: boolean; cleared: boolean }>("/studio/recent-projects/clear", {
    method: "POST"
  });
}

export async function fetchPromptProfiles(): Promise<PromptProfileListResponse> {
  return requestJson<PromptProfileListResponse>("/studio/prompt-profiles");
}

export async function selectPromptProfile(profileId: string): Promise<PromptProfileListResponse> {
  return requestJson<PromptProfileListResponse>("/studio/prompt-profiles/select", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ profile_id: profileId })
  });
}

export async function runPromptABTest(request: PromptABTestRun): Promise<PromptABTestReport> {
  return requestJson<PromptABTestReport>("/prompt-lab/prompt-profiles/ab-test", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
}

export async function runNarratorStyleExperiment(request: NarratorStyleExperiment): Promise<NarratorStyleReport> {
  return requestJson<NarratorStyleReport>("/prompt-lab/narrator-style/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
}

export async function runNPCVoiceStyleExperiment(request: NPCVoiceStyleExperiment): Promise<NPCVoiceStyleReport> {
  return requestJson<NPCVoiceStyleReport>("/prompt-lab/npc-voice-style/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
}

export async function inspectPromptLabContext(request: ContextInspectRequest): Promise<ContextSnapshot> {
  return requestJson<ContextSnapshot>("/prompt-lab/context/inspect", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
}

export async function fetchModelCompatibilityMatrix(): Promise<ModelCompatibilityMatrix> {
  return requestJson<ModelCompatibilityMatrix>("/prompt-lab/model-compatibility");
}

export async function recomputeModelCompatibilityMatrix(): Promise<ModelCompatibilityMatrix> {
  return requestJson<ModelCompatibilityMatrix>("/prompt-lab/model-compatibility/recompute", {
    method: "POST"
  });
}

export async function fetchProviderRoutingSummary(): Promise<ProviderRoutingSummary> {
  return requestJson<ProviderRoutingSummary>("/prompt-lab/provider-routing");
}

export async function fetchProviderCapabilities(): Promise<ProviderCapabilityCatalog> {
  return requestJson<ProviderCapabilityCatalog>("/prompt-lab/provider-capabilities");
}

export async function runProviderBenchmark(allowRealProvider = false): Promise<ProviderBenchmarkReport> {
  return requestJson<ProviderBenchmarkReport>("/prompt-lab/providers/benchmark", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider_id: "fake", allow_real_provider: allowRealProvider })
  });
}

export async function runStructuredOutputReliability(allowRealProvider = false): Promise<StructuredOutputReliabilityReport> {
  return requestJson<StructuredOutputReliabilityReport>("/prompt-lab/structured-output/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider_id: "fake", allow_real_provider: allowRealProvider })
  });
}

export async function runPromptRegressionSuite(): Promise<PromptRegressionReport> {
  return requestJson<PromptRegressionReport>("/prompt-lab/regression/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({})
  });
}

export async function runLocalModelDiagnostics(): Promise<LocalModelDiagnosticReport> {
  return requestJson<LocalModelDiagnosticReport>("/prompt-lab/local-model/diagnose", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider_id: "local_stub", fake_mode: "ok" })
  });
}

export async function reviewPromptDiff(left: Record<string, unknown>, right: Record<string, unknown>): Promise<PromptDiffReport> {
  return requestJson<PromptDiffReport>("/prompt-lab/prompt-diff/review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ diff_type: "prompt_profile_diff", left, right })
  });
}

export async function fetchModelUsageSummary(): Promise<ModelUsageSummary> {
  return requestJson<ModelUsageSummary>("/prompt-lab/usage/summary");
}

export async function fetchRecentModelUsage(limit = 20): Promise<{ local_only: boolean; enabled: boolean; records: ModelUsageRecord[] }> {
  return requestJson<{ local_only: boolean; enabled: boolean; records: ModelUsageRecord[] }>(`/prompt-lab/usage/recent?limit=${limit}`);
}

export async function fetchProjectProviders(projectId: string): Promise<{ local_only: boolean; providers: ProviderProfileSummary[] }> {
  return requestJson<{ local_only: boolean; providers: ProviderProfileSummary[] }>(`/projects/${encodeURIComponent(projectId)}/providers`);
}

export async function createProjectProvider(projectId: string, profile: ProviderProfileDraft): Promise<{ local_only: boolean; provider: ProviderProfileSummary }> {
  return requestJson<{ local_only: boolean; provider: ProviderProfileSummary }>(`/projects/${encodeURIComponent(projectId)}/providers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile)
  });
}

export async function validateProjectProvider(projectId: string, providerProfileId: string): Promise<{ local_only: boolean; ok: boolean; warnings: string[] }> {
  return requestJson<{ local_only: boolean; ok: boolean; warnings: string[] }>(`/projects/${encodeURIComponent(projectId)}/providers/${encodeURIComponent(providerProfileId)}/validate`, {
    method: "POST"
  });
}

export async function fetchProjectProviderStatus(projectId: string, providerProfileId: string): Promise<{ local_only: boolean; status: Record<string, unknown> }> {
  return requestJson<{ local_only: boolean; status: Record<string, unknown> }>(`/projects/${encodeURIComponent(projectId)}/providers/${encodeURIComponent(providerProfileId)}/status`);
}

export async function fetchProjectProviderCapabilityMatrix(projectId: string): Promise<{ local_only: boolean; matrix: ProviderModelCapabilityMatrix }> {
  return requestJson<{ local_only: boolean; matrix: ProviderModelCapabilityMatrix }>(`/projects/${encodeURIComponent(projectId)}/providers/capability-matrix`);
}

export async function fetchProjectProviderUsageSummary(projectId: string, sinceMinutes?: number): Promise<ModelUsageSummary> {
  const query = sinceMinutes ? `?since_minutes=${sinceMinutes}` : "";
  return requestJson<ModelUsageSummary>(`/projects/${encodeURIComponent(projectId)}/providers/usage/summary${query}`);
}

export async function fetchProjectProviderUsageRecent(projectId: string, limit = 20, sinceMinutes?: number): Promise<{ local_only: boolean; enabled: boolean; records: ModelUsageRecord[] }> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (sinceMinutes) params.set("since_minutes", String(sinceMinutes));
  return requestJson<{ local_only: boolean; enabled: boolean; records: ModelUsageRecord[] }>(`/projects/${encodeURIComponent(projectId)}/providers/usage/recent?${params.toString()}`);
}

export async function fetchProjectProviderUsageByMode(projectId: string, sinceMinutes?: number): Promise<{ local_only: boolean; enabled: boolean; by_mode: CostLatencyGroupSummary[] }> {
  const query = sinceMinutes ? `?since_minutes=${sinceMinutes}` : "";
  return requestJson<{ local_only: boolean; enabled: boolean; by_mode: CostLatencyGroupSummary[] }>(`/projects/${encodeURIComponent(projectId)}/providers/usage/by-mode${query}`);
}

export async function fetchProjectProviderUsageByProvider(projectId: string, sinceMinutes?: number): Promise<{ local_only: boolean; enabled: boolean; by_provider: CostLatencyGroupSummary[] }> {
  const query = sinceMinutes ? `?since_minutes=${sinceMinutes}` : "";
  return requestJson<{ local_only: boolean; enabled: boolean; by_provider: CostLatencyGroupSummary[] }>(`/projects/${encodeURIComponent(projectId)}/providers/usage/by-provider${query}`);
}

export async function previewProviderRoutingRule(rule: ProviderRoutingRule): Promise<ProviderRoutingPreview> {
  return requestJson<ProviderRoutingPreview>("/prompt-lab/provider-routing/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rule)
  });
}

export async function saveProviderRoutingConfig(config: ProviderRoutingConfig): Promise<ProviderRoutingSummary> {
  return requestJson<ProviderRoutingSummary>("/prompt-lab/provider-routing/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config)
  });
}

export async function fetchTokenBudgetProfiles(): Promise<{ local_only: boolean; profiles: TokenBudgetProfile[] }> {
  return requestJson<{ local_only: boolean; profiles: TokenBudgetProfile[] }>("/prompt-lab/token-budget/profiles");
}

export async function estimateTokenBudget(profile: TokenBudgetProfile, sections: ContextSection[]): Promise<BudgetReport> {
  return requestJson<BudgetReport>("/prompt-lab/token-budget/estimate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile, sections })
  });
}

export async function submitPlayerInput(
  sessionId: string,
  playerInput: string
): Promise<GameInputResponse> {
  return requestJson<GameInputResponse>("/game/input", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      session_id: sessionId,
      player_input: playerInput
    })
  });
}

export async function startDialogue(
  gameSessionId: string,
  focusNpcId: string,
  dialogueMode = "focused",
  sceneMoodPresetId?: string
): Promise<DialogueModeResponse> {
  return requestJson<DialogueModeResponse>("/game/dialogue/start", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      game_session_id: gameSessionId,
      focus_npc_id: focusNpcId,
      dialogue_mode: dialogueMode,
      scene_mood_preset_id: sceneMoodPresetId || null
    })
  });
}

export async function continueDialogue(
  dialogueSessionId: string,
  playerInput: string
): Promise<DialogueModeResponse> {
  return requestJson<DialogueModeResponse>("/game/dialogue/continue", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      dialogue_session_id: dialogueSessionId,
      player_input: playerInput
    })
  });
}

export async function endDialogue(dialogueSessionId: string): Promise<DialogueModeResponse> {
  return requestJson<DialogueModeResponse>("/game/dialogue/end", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      dialogue_session_id: dialogueSessionId
    })
  });
}

export async function startGroupDialogue(
  gameSessionId: string,
  participantIds: string[],
  sceneTopic = "",
  sceneMood = "neutral",
  sceneMoodPresetId?: string
): Promise<GroupDialogueSceneResponse> {
  return requestJson<GroupDialogueSceneResponse>("/game/group-dialogue/start", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      game_session_id: gameSessionId,
      participant_ids: participantIds,
      scene_topic: sceneTopic,
      scene_mood: sceneMood,
      scene_mood_preset_id: sceneMoodPresetId || null
    })
  });
}

export async function selectGroupDialogueNextSpeaker(sceneId: string): Promise<GroupDialogueSceneResponse> {
  return requestJson<GroupDialogueSceneResponse>("/game/group-dialogue/next-speaker", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ scene_id: sceneId })
  });
}

export async function endGroupDialogue(sceneId: string): Promise<GroupDialogueSceneResponse> {
  return requestJson<GroupDialogueSceneResponse>("/game/group-dialogue/end", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ scene_id: sceneId })
  });
}

export async function fetchGameState(sessionId: string): Promise<GameStateResponse> {
  return requestJson<GameStateResponse>(`/game/state/${encodeURIComponent(sessionId)}`);
}

export async function listSaves(worldId?: string): Promise<SaveListResponse> {
  const query = worldId ? `?world_id=${encodeURIComponent(worldId)}` : "";
  return requestJson<SaveListResponse>(`/game/saves${query}`);
}

export async function saveGame(sessionId: string): Promise<SaveGameResponse> {
  return requestJson<SaveGameResponse>(`/game/${encodeURIComponent(sessionId)}/save`, {
    method: "POST"
  });
}

export async function loadGame(saveId: string): Promise<LoadGameResponse> {
  return requestJson<LoadGameResponse>(`/game/load/${encodeURIComponent(saveId)}`, {
    method: "POST"
  });
}

export async function deleteSave(saveId: string): Promise<DeleteSaveResponse> {
  return requestJson<DeleteSaveResponse>(`/game/saves/${encodeURIComponent(saveId)}`, {
    method: "DELETE"
  });
}

export async function fetchSaveMigrationStatus(saveId: string): Promise<SaveMigrationStatus> {
  return requestJson<SaveMigrationStatus>(`/saves/${encodeURIComponent(saveId)}/migration-status`);
}

export async function dryRunSaveMigration(saveId: string): Promise<SaveMigrationResponse> {
  return requestJson<SaveMigrationResponse>(`/saves/${encodeURIComponent(saveId)}/migrate-dry-run`, {
    method: "POST"
  });
}

export async function applySaveMigration(saveId: string): Promise<SaveMigrationResponse> {
  return requestJson<SaveMigrationResponse>(`/saves/${encodeURIComponent(saveId)}/migrate`, {
    method: "POST"
  });
}

export async function fetchSessionDebugEvents(sessionId: string): Promise<DebugEventListResponse> {
  return requestJson<DebugEventListResponse>(
    `/debug/sessions/${encodeURIComponent(sessionId)}/events`
  );
}

export async function fetchSaveDebugEvents(saveId: string): Promise<DebugEventListResponse> {
  return requestJson<DebugEventListResponse>(`/debug/saves/${encodeURIComponent(saveId)}/events`);
}

function timelineQuery(params?: {
  turnFrom?: number | null;
  turnTo?: number | null;
  eventFilter?: string;
}): string {
  const query = new URLSearchParams();
  if (params?.turnFrom !== undefined && params.turnFrom !== null) {
    query.set("turn_from", String(params.turnFrom));
  }
  if (params?.turnTo !== undefined && params.turnTo !== null) {
    query.set("turn_to", String(params.turnTo));
  }
  if (params?.eventFilter && params.eventFilter !== "all") {
    query.set("event_filter", params.eventFilter);
  }
  const encoded = query.toString();
  return encoded ? `?${encoded}` : "";
}

export async function fetchSessionTimelineReplay(
  sessionId: string,
  params?: { turnFrom?: number | null; turnTo?: number | null; eventFilter?: string }
): Promise<TimelineReplayResponse> {
  return requestJson<TimelineReplayResponse>(
    `/debug/sessions/${encodeURIComponent(sessionId)}/timeline${timelineQuery(params)}`
  );
}

export async function fetchSaveTimelineReplay(
  saveId: string,
  params?: { turnFrom?: number | null; turnTo?: number | null; eventFilter?: string }
): Promise<TimelineReplayResponse> {
  return requestJson<TimelineReplayResponse>(
    `/debug/saves/${encodeURIComponent(saveId)}/timeline${timelineQuery(params)}`
  );
}

export async function dryRunSaveTimelineReplay(saveId: string): Promise<TimelineReplayResponse> {
  return requestJson<TimelineReplayResponse>(
    `/debug/saves/${encodeURIComponent(saveId)}/replay-dry-run`,
    { method: "POST" }
  );
}

export async function fetchPlayerRelationshipGraph(sessionId: string): Promise<GraphResponse> {
  return requestJson<GraphResponse>(
    `/game/${encodeURIComponent(sessionId)}/graphs/relationships`
  );
}

export async function fetchPlayerFactionGraph(sessionId: string): Promise<GraphResponse> {
  return requestJson<GraphResponse>(`/game/${encodeURIComponent(sessionId)}/graphs/factions`);
}

export async function fetchDebugRelationshipGraph(sessionId: string): Promise<GraphResponse> {
  return requestJson<GraphResponse>(
    `/debug/sessions/${encodeURIComponent(sessionId)}/graphs/relationships`
  );
}

export async function fetchDebugFactionGraph(sessionId: string): Promise<GraphResponse> {
  return requestJson<GraphResponse>(
    `/debug/sessions/${encodeURIComponent(sessionId)}/graphs/factions`
  );
}

export async function fetchNPCSimulationDebug(sessionId: string): Promise<DebugNPCSimulationListResponse> {
  return requestJson<DebugNPCSimulationListResponse>(
    `/debug/sessions/${encodeURIComponent(sessionId)}/npc-simulation`
  );
}

export async function fetchNPCSimulationDebugDetail(
  sessionId: string,
  npcId: string
): Promise<DebugNPCSimulationDetail> {
  return requestJson<DebugNPCSimulationDetail>(
    `/debug/sessions/${encodeURIComponent(sessionId)}/npcs/${encodeURIComponent(npcId)}/simulation`
  );
}

export async function fetchNPCSimulationDebugTicks(sessionId: string): Promise<DebugNPCSimulationTickListResponse> {
  return requestJson<DebugNPCSimulationTickListResponse>(
    `/debug/sessions/${encodeURIComponent(sessionId)}/npc-simulation/ticks`
  );
}

export async function dryRunNPCSimulationTick(sessionId: string): Promise<DebugNPCSimulationDryRunResponse> {
  return requestJson<DebugNPCSimulationDryRunResponse>(
    `/debug/sessions/${encodeURIComponent(sessionId)}/npc-simulation/dry-run-tick`,
    { method: "POST" }
  );
}

export async function fetchGameplayModuleDebug(): Promise<ModuleDebugListResponse> {
  return requestJson<ModuleDebugListResponse>("/debug/modules");
}

export async function fetchGameplayModuleDebugDetail(moduleId: string): Promise<ModuleDebugSummary> {
  return requestJson<ModuleDebugSummary>(`/debug/modules/${encodeURIComponent(moduleId)}`);
}

export async function dryRunGameplayModuleAction(
  moduleId: string,
  actionId: string,
  inputText = ""
): Promise<ModuleActionDryRunResponse> {
  return requestJson<ModuleActionDryRunResponse>(
    `/debug/modules/${encodeURIComponent(moduleId)}/actions/${encodeURIComponent(actionId)}/dry-run`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input_text: inputText })
    }
  );
}

function behaviorTimelineQuery(turnFrom?: number | null, turnTo?: number | null): string {
  const query = new URLSearchParams();
  if (turnFrom !== undefined && turnFrom !== null) {
    query.set("turn_from", String(turnFrom));
  }
  if (turnTo !== undefined && turnTo !== null) {
    query.set("turn_to", String(turnTo));
  }
  const encoded = query.toString();
  return encoded ? `?${encoded}` : "";
}

export async function fetchNPCBehaviorTimeline(
  sessionId: string,
  npcId: string,
  turnFrom?: number | null,
  turnTo?: number | null
): Promise<NPCBehaviorTimelineResponse> {
  return requestJson<NPCBehaviorTimelineResponse>(
    `/debug/sessions/${encodeURIComponent(sessionId)}/npcs/${encodeURIComponent(npcId)}/behavior-timeline${behaviorTimelineQuery(turnFrom, turnTo)}`
  );
}

export async function fetchAuthoringWorlds(): Promise<AuthoringWorldListResponse> {
  return requestJson<AuthoringWorldListResponse>("/authoring/worlds");
}

export async function fetchAuthoringMods(): Promise<AuthoringModListResponse> {
  return requestJson<AuthoringModListResponse>("/authoring/mods");
}

export async function fetchAuthoringMod(modId: string): Promise<AuthoringModDetailResponse> {
  return requestJson<AuthoringModDetailResponse>(`/authoring/mods/${encodeURIComponent(modId)}`);
}

export async function validateAuthoringMod(modId: string): Promise<AuthoringModValidation> {
  return requestJson<AuthoringModValidation>(`/authoring/mods/${encodeURIComponent(modId)}/validate`, {
    method: "POST"
  });
}

export async function fetchAuthoringModLoadOrder(): Promise<AuthoringModLoadOrderResponse> {
  return requestJson<AuthoringModLoadOrderResponse>("/authoring/mods/load-order");
}

export async function exportWorldArchive(worldId: string): Promise<ArchiveExportResponse> {
  return requestJson<ArchiveExportResponse>(`/authoring/export/worlds/${encodeURIComponent(worldId)}`);
}

export async function fetchImportExportProfiles(): Promise<ImportExportProfileCatalog> {
  return requestJson<ImportExportProfileCatalog>("/authoring/import-export-profiles");
}

export async function exportCharacterPack(
  worldId: string,
  characterIds: string[],
  exportProfileId = "safe"
): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>("/authoring/character-packs/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      world_id: worldId,
      character_ids: characterIds,
      export_profile_id: exportProfileId
    })
  });
}

export async function importWorldArchive(archiveBase64: string, overwrite = false, importProfileId = "safe"): Promise<ArchiveImportResponse> {
  return requestJson<ArchiveImportResponse>("/authoring/import/worlds", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ archive_base64: archiveBase64, overwrite, import_profile_id: importProfileId })
  });
}

export async function exportModArchive(modId: string): Promise<ArchiveExportResponse> {
  return requestJson<ArchiveExportResponse>(`/authoring/export/mods/${encodeURIComponent(modId)}`);
}

export async function importModArchive(archiveBase64: string, overwrite = false, importProfileId = "safe"): Promise<ArchiveImportResponse> {
  return requestJson<ArchiveImportResponse>("/authoring/import/mods", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ archive_base64: archiveBase64, overwrite, import_profile_id: importProfileId })
  });
}

export async function exportSaveArchive(saveId: string): Promise<ArchiveExportResponse> {
  return requestJson<ArchiveExportResponse>(`/authoring/export/saves/${encodeURIComponent(saveId)}`);
}

export async function importSaveArchive(archiveBase64: string, overwrite = false, importProfileId = "safe"): Promise<ArchiveImportResponse> {
  return requestJson<ArchiveImportResponse>("/authoring/import/saves", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ archive_base64: archiveBase64, overwrite, import_profile_id: importProfileId })
  });
}

export async function fetchNarrativeEvalRecent(): Promise<NarrativeEvalRecentResponse> {
  return requestJson<NarrativeEvalRecentResponse>("/evals/narrative/recent");
}

export async function runNarrativeEval(): Promise<NarrativeEvalReport> {
  return requestJson<NarrativeEvalReport>("/evals/narrative/run", {
    method: "POST"
  });
}

export async function fetchNarrativeEval(runId: string): Promise<NarrativeEvalReport> {
  return requestJson<NarrativeEvalReport>(`/evals/narrative/${encodeURIComponent(runId)}`);
}

export async function fetchDebugPerformanceRecent(): Promise<DebugPerformanceRecentResponse> {
  return requestJson<DebugPerformanceRecentResponse>("/debug/performance/recent");
}

export async function fetchDebugPerformanceSummary(): Promise<DebugPerformanceSummaryResponse> {
  return requestJson<DebugPerformanceSummaryResponse>("/debug/performance/summary");
}

export async function fetchWorldHealth(worldId: string): Promise<WorldHealthScore> {
  return requestJson<WorldHealthScore>(`/quality/worlds/${encodeURIComponent(worldId)}/health`);
}

export async function runWorldHealth(worldId: string): Promise<WorldHealthScore> {
  return requestJson<WorldHealthScore>(`/quality/worlds/${encodeURIComponent(worldId)}/health/run`, {
    method: "POST"
  });
}

export async function fetchContentCoverage(worldId: string): Promise<ContentCoverageReport> {
  return requestJson<ContentCoverageReport>(`/quality/worlds/${encodeURIComponent(worldId)}/coverage`);
}

export async function runContentCoverage(worldId: string): Promise<ContentCoverageReport> {
  return requestJson<ContentCoverageReport>(`/quality/worlds/${encodeURIComponent(worldId)}/coverage/run`, {
    method: "POST"
  });
}

export async function planContentCoverage(request: ContentCoveragePlanRequest): Promise<ContentCoveragePlan> {
  return requestJson<ContentCoveragePlan>("/production/content-coverage-plan", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
}

export async function fetchPlaytestRecent(): Promise<PlaytestRecentResponse> {
  return requestJson<PlaytestRecentResponse>("/playtests/recent");
}

export async function runPlaytest(request: PlaytestRunRequest): Promise<PlaytestReport> {
  return requestJson<PlaytestReport>("/playtests/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
}

export async function fetchPlaytest(runId: string): Promise<PlaytestReport> {
  return requestJson<PlaytestReport>(`/playtests/${encodeURIComponent(runId)}`);
}

export async function runPlaytestBatch(request: PlaytestBatchRunRequest): Promise<PlaytestBatchRun> {
  return requestJson<PlaytestBatchRun>("/playtests/batch/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
}

export async function fetchPlaytestBatch(runId: string): Promise<PlaytestBatchRun> {
  return requestJson<PlaytestBatchRun>(`/playtests/batch/${encodeURIComponent(runId)}`);
}

export async function fetchScenarioRegressionCases(): Promise<ScenarioRegressionListResponse> {
  return requestJson<ScenarioRegressionListResponse>("/scenarios/regression");
}

export async function runScenarioRegression(
  request: ScenarioRegressionRunRequest
): Promise<ScenarioRegressionRun> {
  return requestJson<ScenarioRegressionRun>("/scenarios/regression/run", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(request)
  });
}

export async function fetchScenarioRegression(runId: string): Promise<ScenarioRegressionRun> {
  return requestJson<ScenarioRegressionRun>(`/scenarios/regression/${encodeURIComponent(runId)}`);
}

export async function fetchAuthoringScenarios(): Promise<ScenarioAuthoringListResponse> {
  return requestJson<ScenarioAuthoringListResponse>("/authoring/scenarios");
}

export async function fetchAuthoringScenario(scenarioId: string): Promise<ScenarioAuthoringPreviewResponse> {
  return requestJson<ScenarioAuthoringPreviewResponse>(
    `/authoring/scenarios/${encodeURIComponent(scenarioId)}`
  );
}

export async function previewAuthoringScenario(
  scenario: ScenarioRegressionCase
): Promise<ScenarioAuthoringPreviewResponse> {
  return requestJson<ScenarioAuthoringPreviewResponse>("/authoring/scenarios/preview", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ scenario })
  });
}

export async function validateAuthoringScenario(
  scenario: ScenarioRegressionCase
): Promise<ScenarioAuthoringPreviewResponse> {
  return requestJson<ScenarioAuthoringPreviewResponse>(
    `/authoring/scenarios/${encodeURIComponent(scenario.id)}/validate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ scenario })
    }
  );
}

export async function saveAuthoringScenario(
  scenario: ScenarioRegressionCase
): Promise<ScenarioAuthoringPreviewResponse> {
  return requestJson<ScenarioAuthoringPreviewResponse>(
    `/authoring/scenarios/${encodeURIComponent(scenario.id)}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ scenario })
    }
  );
}

export async function fetchAuthoringWorld(worldId: string): Promise<AuthoringWorldDetailResponse> {
  return requestJson<AuthoringWorldDetailResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}`
  );
}

export async function fetchAuthoringFiles(worldId: string): Promise<AuthoringFileListResponse> {
  return requestJson<AuthoringFileListResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/files`
  );
}

export async function fetchAuthoringFile(
  worldId: string,
  fileName: string
): Promise<AuthoringFileResponse> {
  return requestJson<AuthoringFileResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/files/${encodeURIComponent(fileName)}`
  );
}

export async function saveAuthoringFile(
  worldId: string,
  fileName: string,
  content: string
): Promise<AuthoringFileWriteResponse> {
  return requestJson<AuthoringFileWriteResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/files/${encodeURIComponent(fileName)}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ content })
    }
  );
}

export async function validateAuthoringWorld(worldId: string): Promise<AuthoringValidation> {
  return requestJson<AuthoringValidation>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/validate`,
    {
      method: "POST"
    }
  );
}

export async function fetchValidationGraph(worldId: string): Promise<ValidationGraph> {
  return requestJson<ValidationGraph>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/validation-graph`
  );
}

export async function previewAuthoringFileChange(
  worldId: string,
  fileName: string,
  proposedContent: string
): Promise<AuthoringFilePreviewResponse> {
  return requestJson<AuthoringFilePreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/preview-file-change`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        file_name: fileName,
        proposed_content: proposedContent
      })
    }
  );
}

export async function fetchAuthoringMap(worldId: string): Promise<AuthoringMapGraphResponse> {
  return requestJson<AuthoringMapGraphResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/map`
  );
}

export async function previewAuthoringMap(
  worldId: string,
  graph: MapVisualGraph
): Promise<AuthoringMapPreviewResponse> {
  return requestJson<AuthoringMapPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/map/preview`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function validateAuthoringMap(
  worldId: string,
  graph: MapVisualGraph
): Promise<AuthoringValidation> {
  return requestJson<AuthoringValidation>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/map/validate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function saveAuthoringMap(
  worldId: string,
  graph: MapVisualGraph,
  confirmWarnings = false
): Promise<AuthoringMapWriteResponse> {
  return requestJson<AuthoringMapWriteResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/map`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph, confirm_warnings: confirmWarnings })
    }
  );
}

export async function fetchWorldBranches(worldId: string): Promise<WorldBranchListResponse> {
  return requestJson<WorldBranchListResponse>(`/authoring/worlds/${encodeURIComponent(worldId)}/branches`);
}

export async function previewWorldMerge(
  worldId: string,
  ours: string,
  theirs: string,
  resolutions: MergeResolution[] = []
): Promise<WorldMergeDraft> {
  return requestJson<WorldMergeDraft>(`/authoring/worlds/${encodeURIComponent(worldId)}/merge/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ours, theirs, resolutions })
  });
}

export async function saveWorldMerge(
  worldId: string,
  ours: string,
  theirs: string,
  resolutions: MergeResolution[] = [],
  confirmWarnings = false
): Promise<WorldMergeDraft> {
  return requestJson<WorldMergeDraft>(`/authoring/worlds/${encodeURIComponent(worldId)}/merge/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ours, theirs, resolutions, confirm_save: true, confirm_warnings: confirmWarnings })
  });
}

export async function reviewContentDiff(
  base: ContentDiffRef,
  proposed: ContentDiffRef,
  diffTypes: ContentDiffKind[] = ["file_diff", "entity_diff", "graph_diff"],
  normalView = true
): Promise<ContentDiffReview> {
  return requestJson<ContentDiffReview>("/authoring/diff/review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      base,
      proposed,
      diff_types: diffTypes,
      normal_view: normalView
    })
  });
}

export async function fetchAuthoringWorkflowPresets(): Promise<AuthoringWorkflowPresetList> {
  return requestJson<AuthoringWorkflowPresetList>("/authoring/workflow-presets");
}

export async function fetchAuthoringProjectSummary(worldId?: string, branchId?: string): Promise<AuthoringProjectSummary> {
  const params = new URLSearchParams();
  if (worldId) {
    params.set("world_id", worldId);
  }
  if (branchId) {
    params.set("branch_id", branchId);
  }
  const query = params.toString();
  return requestJson<AuthoringProjectSummary>(`/authoring/project-summary${query ? `?${query}` : ""}`);
}

export async function fetchReferenceIndex(worldId: string): Promise<ReferenceIndex> {
  return requestJson<ReferenceIndex>(`/authoring/worlds/${encodeURIComponent(worldId)}/references`);
}

export async function fetchLocalContentLibrary(contentType?: string): Promise<LocalContentLibrary> {
  const query = contentType && contentType !== "all" ? `?content_type=${encodeURIComponent(contentType)}` : "";
  return requestJson<LocalContentLibrary>(`/library/items${query}`);
}

export async function searchLocalContentLibrary(
  query: string,
  contentTypes: LocalContentType[] = [],
  tags: string[] = []
): Promise<LocalContentLibrary> {
  return requestJson<LocalContentLibrary>("/library/items/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, content_types: contentTypes, tags })
  });
}

export async function fetchLocalContentLibraryItem(itemId: string): Promise<LocalContentLibraryItem> {
  return requestJson<LocalContentLibraryItem>(`/library/items/${encodeURIComponent(itemId)}`);
}

export async function validateLocalContentLibraryItem(itemId: string): Promise<AuthoringValidation> {
  return requestJson<AuthoringValidation>(`/library/items/${encodeURIComponent(itemId)}/validate`, { method: "POST" });
}

export async function batchValidateLocalContentLibrary(itemIds: string[], contentTypes: LocalContentType[] = []): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>("/library/items/batch-validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_ids: itemIds, content_types: contentTypes, normal_report: true })
  });
}

export async function exportLocalContentLibraryItem(contentType: LocalContentType, itemId: string, exportProfileId = "safe"): Promise<ArchiveExportResponse> {
  return requestJson<ArchiveExportResponse>("/library/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content_type: contentType, item_id: itemId, export_profile_id: exportProfileId })
  });
}

export async function importLocalContentLibraryArchive(
  archiveBase64: string,
  overwrite = false,
  confirmApply = false,
  importProfileId = "safe"
): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>("/library/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ archive_base64: archiveBase64, overwrite, confirm_apply: confirmApply, import_profile_id: importProfileId })
  });
}

export async function fetchScenarioTemplates(): Promise<ScenarioTemplateListResponse> {
  return requestJson<ScenarioTemplateListResponse>("/authoring/templates");
}

export async function fetchScenarioTemplate(templateId: string): Promise<ScenarioTemplate> {
  return requestJson<ScenarioTemplate>(`/authoring/templates/${encodeURIComponent(templateId)}`);
}

export async function previewScenarioTemplate(
  templateId: string,
  variables: Record<string, string>,
  targetWorldId?: string
): Promise<ScenarioTemplatePreviewResponse> {
  return requestJson<ScenarioTemplatePreviewResponse>(
    `/authoring/templates/${encodeURIComponent(templateId)}/preview`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        variables,
        target_world_id: targetWorldId || null
      })
    }
  );
}

export async function applyScenarioTemplate(
  templateId: string,
  variables: Record<string, string>,
  targetWorldId?: string
): Promise<ScenarioTemplateApplyResponse> {
  return requestJson<ScenarioTemplateApplyResponse>(
    `/authoring/templates/${encodeURIComponent(templateId)}/apply`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        variables,
        target_world_id: targetWorldId || null,
        confirm_apply: true
      })
    }
  );
}

export async function previewTemplateWizard(
  draft: TemplateWizardDraft
): Promise<TemplateWizardPreviewResponse> {
  return requestJson<TemplateWizardPreviewResponse>("/authoring/template-wizard/preview", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(draft)
  });
}

export async function validateTemplateWizard(
  draft: TemplateWizardDraft
): Promise<TemplateWizardPreviewResponse> {
  return requestJson<TemplateWizardPreviewResponse>("/authoring/template-wizard/validate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(draft)
  });
}

export async function applyTemplateWizard(
  draft: TemplateWizardDraft,
  confirmApply = true,
  confirmWarnings = false
): Promise<TemplateWizardPreviewResponse> {
  return requestJson<TemplateWizardPreviewResponse>("/authoring/template-wizard/apply", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      draft,
      confirm_apply: confirmApply,
      confirm_warnings: confirmWarnings
    })
  });
}

export async function createWorldPackWizardDraft(
  draft: WorldPackWizardDraft
): Promise<WorldPackWizardDraft> {
  return requestJson<WorldPackWizardDraft>("/authoring/production/world-pack/create-draft", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(draft)
  });
}

export async function previewWorldPackWizard(
  draft: WorldPackWizardDraft
): Promise<WorldPackWizardPreviewResponse> {
  return requestJson<WorldPackWizardPreviewResponse>("/authoring/production/world-pack/preview", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(draft)
  });
}

export async function validateWorldPackWizard(
  draft: WorldPackWizardDraft
): Promise<WorldPackWizardPreviewResponse> {
  return requestJson<WorldPackWizardPreviewResponse>("/authoring/production/world-pack/validate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(draft)
  });
}

export async function applyWorldPackWizard(
  draft: WorldPackWizardDraft,
  confirmApply = true,
  confirmWarnings = false
): Promise<WorldPackWizardPreviewResponse> {
  return requestJson<WorldPackWizardPreviewResponse>("/authoring/production/world-pack/apply", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      draft,
      confirm_apply: confirmApply,
      confirm_warnings: confirmWarnings
    })
  });
}

export async function previewNPCPackGenerator(
  draft: NPCPackGeneratorDraft
): Promise<NPCPackGeneratorPreviewResponse> {
  return requestJson<NPCPackGeneratorPreviewResponse>("/production/npc-pack/preview", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(draft)
  });
}

export async function validateNPCPackGenerator(
  draft: NPCPackGeneratorDraft
): Promise<NPCPackGeneratorPreviewResponse> {
  return requestJson<NPCPackGeneratorPreviewResponse>("/production/npc-pack/validate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(draft)
  });
}

export async function applyNPCPackGenerator(
  draft: NPCPackGeneratorDraft,
  confirmApply = true,
  confirmWarnings = false
): Promise<NPCPackGeneratorPreviewResponse> {
  return requestJson<NPCPackGeneratorPreviewResponse>("/production/npc-pack/apply", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      draft,
      confirm_apply: confirmApply,
      confirm_warnings: confirmWarnings
    })
  });
}

export async function exportNPCPackGenerator(
  draft: NPCPackGeneratorDraft,
  safeExport = true
): Promise<NPCPackGeneratorPreviewResponse> {
  return requestJson<NPCPackGeneratorPreviewResponse>("/production/npc-pack/export", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      draft,
      safe_export: safeExport
    })
  });
}

export async function previewQuestPackGenerator(
  draft: QuestPackGeneratorDraft
): Promise<QuestPackGeneratorPreviewResponse> {
  return requestJson<QuestPackGeneratorPreviewResponse>("/production/quest-pack/preview", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(draft)
  });
}

export async function validateQuestPackGenerator(
  draft: QuestPackGeneratorDraft
): Promise<QuestPackGeneratorPreviewResponse> {
  return requestJson<QuestPackGeneratorPreviewResponse>("/production/quest-pack/validate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(draft)
  });
}

export async function applyQuestPackGenerator(
  draft: QuestPackGeneratorDraft,
  confirmApply = true,
  confirmWarnings = false
): Promise<QuestPackGeneratorPreviewResponse> {
  return requestJson<QuestPackGeneratorPreviewResponse>("/production/quest-pack/apply", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      draft,
      confirm_apply: confirmApply,
      confirm_warnings: confirmWarnings
    })
  });
}

export async function fetchLocationClusterTemplates(): Promise<LocationClusterTemplateList> {
  return requestJson<LocationClusterTemplateList>("/production/location-clusters");
}

export async function previewLocationClusterTemplate(
  templateId: string,
  targetWorldId: string,
  variables: Record<string, string>
): Promise<LocationClusterPreviewResponse> {
  return requestJson<LocationClusterPreviewResponse>(`/production/location-clusters/${encodeURIComponent(templateId)}/preview`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      target_world_id: targetWorldId,
      variables
    })
  });
}

export async function applyLocationClusterTemplate(
  templateId: string,
  targetWorldId: string,
  variables: Record<string, string>,
  confirmApply = true,
  confirmWarnings = false
): Promise<LocationClusterPreviewResponse> {
  return requestJson<LocationClusterPreviewResponse>(`/production/location-clusters/${encodeURIComponent(templateId)}/apply-draft`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      target_world_id: targetWorldId,
      variables,
      confirm_apply: confirmApply,
      confirm_warnings: confirmWarnings
    })
  });
}

export async function fetchRPScenarioTemplates(): Promise<RPScenarioTemplateListResponse> {
  return requestJson<RPScenarioTemplateListResponse>("/authoring/rp-scenario-templates");
}

export async function previewRPScenarioTemplate(
  templateId: string,
  gameSessionId?: string,
  participantIds: string[] = []
): Promise<RPScenarioTemplatePreviewResponse> {
  return requestJson<RPScenarioTemplatePreviewResponse>(
    `/authoring/rp-scenario-templates/${encodeURIComponent(templateId)}/preview`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        game_session_id: gameSessionId || null,
        participant_ids: participantIds
      })
    }
  );
}

export async function applyRPScenarioTemplate(
  templateId: string,
  gameSessionId?: string,
  participantIds: string[] = []
): Promise<RPScenarioTemplatePreviewResponse> {
  return requestJson<RPScenarioTemplatePreviewResponse>(
    `/authoring/rp-scenario-templates/${encodeURIComponent(templateId)}/apply`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        game_session_id: gameSessionId || null,
        participant_ids: participantIds,
        confirm_apply: true
      })
    }
  );
}

export async function fetchQuestGraph(worldId: string): Promise<QuestGraphResponse> {
  return requestJson<QuestGraphResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/quests/graph`
  );
}

export async function previewQuestGraph(
  worldId: string,
  graph: QuestGraphResponse
): Promise<QuestGraphPreviewResponse> {
  return requestJson<QuestGraphPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/quests/graph/preview`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function validateQuestGraph(
  worldId: string,
  graph: QuestGraphResponse
): Promise<QuestGraphPreviewResponse> {
  return requestJson<QuestGraphPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/quests/graph/validate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function saveQuestGraph(
  worldId: string,
  graph: QuestGraphResponse,
  confirmWarnings = false
): Promise<QuestGraphSaveResponse> {
  return requestJson<QuestGraphSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/quests/graph`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph, confirm_warnings: confirmWarnings })
    }
  );
}

export async function generateQuestGraphScenarioDraft(
  worldId: string,
  graph: QuestGraphResponse
): Promise<QuestGraphScenarioDraftResponse> {
  return requestJson<QuestGraphScenarioDraftResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/quests/graph/scenario-draft`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function fetchNPCGoalGraph(worldId: string): Promise<NPCGoalAuthoringGraph> {
  return requestJson<NPCGoalAuthoringGraph>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/npcs/goals`
  );
}

export async function fetchNPCSimulationPresets(): Promise<NPCSimulationPresetListResponse> {
  return requestJson<NPCSimulationPresetListResponse>("/authoring/npc-simulation-presets");
}

export async function previewNPCSimulationPreset(
  worldId: string,
  npcId: string,
  presetId: string,
  confirmWarnings = false
): Promise<NPCSimulationPresetPreviewResponse> {
  return requestJson<NPCSimulationPresetPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/npcs/${encodeURIComponent(npcId)}/simulation-preset/preview`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ preset_id: presetId, confirm_warnings: confirmWarnings })
    }
  );
}

export async function applyNPCSimulationPresetDraft(
  worldId: string,
  npcId: string,
  presetId: string,
  confirmWarnings = false
): Promise<NPCSimulationPresetPreviewResponse> {
  return requestJson<NPCSimulationPresetPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/npcs/${encodeURIComponent(npcId)}/simulation-preset/apply-draft`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ preset_id: presetId, confirm_warnings: confirmWarnings })
    }
  );
}

export async function previewNPCGoalGraph(
  worldId: string,
  graph: NPCGoalAuthoringGraph
): Promise<NPCGoalAuthoringPreviewResponse> {
  return requestJson<NPCGoalAuthoringPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/npcs/goals/preview`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function validateNPCGoalGraph(
  worldId: string,
  graph: NPCGoalAuthoringGraph
): Promise<NPCGoalAuthoringPreviewResponse> {
  return requestJson<NPCGoalAuthoringPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/npcs/goals/validate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function saveNPCGoalGraph(
  worldId: string,
  graph: NPCGoalAuthoringGraph
): Promise<NPCGoalAuthoringSaveResponse> {
  return requestJson<NPCGoalAuthoringSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/npcs/goals`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function fetchSocialAuthoringGraph(worldId: string): Promise<SocialAuthoringGraph> {
  return requestJson<SocialAuthoringGraph>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/social/graph`
  );
}

export async function previewSocialAuthoringGraph(
  worldId: string,
  graph: SocialAuthoringGraph
): Promise<SocialAuthoringPreviewResponse> {
  return requestJson<SocialAuthoringPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/social/graph/preview`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function validateSocialAuthoringGraph(
  worldId: string,
  graph: SocialAuthoringGraph
): Promise<SocialAuthoringPreviewResponse> {
  return requestJson<SocialAuthoringPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/social/graph/validate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function saveSocialAuthoringGraph(
  worldId: string,
  graph: SocialAuthoringGraph,
  confirmWarnings = false
): Promise<SocialAuthoringSaveResponse> {
  return requestJson<SocialAuthoringSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/social/graph`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph, confirm_warnings: confirmWarnings })
    }
  );
}

export async function fetchItemEconomyAuthoring(worldId: string): Promise<ItemEconomyAuthoring> {
  return requestJson<ItemEconomyAuthoring>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/economy`
  );
}

export async function previewItemEconomyAuthoring(
  worldId: string,
  graph: ItemEconomyAuthoring
): Promise<ItemEconomyAuthoringPreviewResponse> {
  return requestJson<ItemEconomyAuthoringPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/economy/preview`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function validateItemEconomyAuthoring(
  worldId: string,
  graph: ItemEconomyAuthoring
): Promise<ItemEconomyAuthoringPreviewResponse> {
  return requestJson<ItemEconomyAuthoringPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/economy/validate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function balanceCheckItemEconomyAuthoring(
  worldId: string,
  graph: ItemEconomyAuthoring
): Promise<ItemEconomyAuthoringPreviewResponse> {
  return requestJson<ItemEconomyAuthoringPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/economy/balance-check`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function saveItemEconomyAuthoring(
  worldId: string,
  graph: ItemEconomyAuthoring,
  confirmWarnings = false
): Promise<ItemEconomyAuthoringSaveResponse> {
  return requestJson<ItemEconomyAuthoringSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/economy`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph, confirm_warnings: confirmWarnings })
    }
  );
}

export async function fetchRumorCrimeAuthoring(worldId: string): Promise<RumorCrimeConsequenceAuthoring> {
  return requestJson<RumorCrimeConsequenceAuthoring>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/rumor-crime`
  );
}

export async function previewRumorCrimeAuthoring(
  worldId: string,
  graph: RumorCrimeConsequenceAuthoring
): Promise<RumorCrimeConsequencePreviewResponse> {
  return requestJson<RumorCrimeConsequencePreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/rumor-crime/preview`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function validateRumorCrimeAuthoring(
  worldId: string,
  graph: RumorCrimeConsequenceAuthoring
): Promise<RumorCrimeConsequencePreviewResponse> {
  return requestJson<RumorCrimeConsequencePreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/rumor-crime/validate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
}

export async function saveRumorCrimeAuthoring(
  worldId: string,
  graph: RumorCrimeConsequenceAuthoring,
  confirmWarnings = false
): Promise<RumorCrimeConsequenceSaveResponse> {
  return requestJson<RumorCrimeConsequenceSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/rumor-crime`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph, confirm_warnings: confirmWarnings })
    }
  );
}

export type ExampleDialogueVisibility = "prompt_safe" | "authoring_only" | "debug_only" | "unsafe";
export type ExampleDialogueFactPolicy = "flavor_only" | "may_reference_known_facts" | "unsafe";

export type ExampleDialogueMessage = {
  speaker: string;
  text: string;
};

export type ExampleDialogue = {
  id: string;
  character_id: string;
  source: string;
  messages: ExampleDialogueMessage[];
  tags: string[];
  style_notes: string[];
  visibility: ExampleDialogueVisibility;
  fact_policy: ExampleDialogueFactPolicy;
};

export type ExampleDialogueListResponse = {
  world_id: string;
  entries: ExampleDialogue[];
};

export type ExampleDialoguePreviewResponse = {
  world_id: string;
  entries: ExampleDialogue[];
  yaml_content: string;
  validation: AuthoringValidation;
};

export type ExampleDialogueSaveResponse = ExampleDialoguePreviewResponse & {
  saved: boolean;
};

export type RPProfile = {
  public_persona: string;
  private_self_summary?: string | null;
  attachment_style: string;
  trust_expression_style: string;
  conflict_expression_style: string;
  intimacy_expression_style: string;
  deception_style: string;
  boundaries: string[];
};

export type VoiceProfile = {
  tone: string;
  sentence_length: string;
  vocabulary_style: string;
  catchphrases: string[];
  speech_habits: string[];
  silence_style: string;
  emotional_tells: string[];
};

export type EmotionalState = {
  primary_emotion: string;
  intensity: number;
  stress: number;
  stability: number;
  last_emotional_event_id?: string | null;
};

export type RPCharacterAuthoringProfile = {
  npc_id: string;
  name: string;
  location_id: string;
  personality: string;
  visible: boolean;
  hidden: boolean;
  knowledge: string[];
  rp_profile: RPProfile;
  voice_profile: VoiceProfile;
  default_emotional_state: EmotionalState;
  relationship_expression: Record<string, string>;
  example_dialogue_refs: string[];
  example_dialogues: ExampleDialogue[];
  lorebook_links: string[];
  scene_mood_preferences: string[];
  private_field_visibility: Record<string, string>;
  import_report?: CharacterCardImportReport | null;
  safety_flags: string[];
};

export type RPCharacterAuthoring = {
  world_id: string;
  characters: RPCharacterAuthoringProfile[];
};

export type RPCharacterAuthoringPreviewResponse = {
  world_id: string;
  graph: RPCharacterAuthoring;
  yaml_contents: Record<string, string>;
  validation: AuthoringValidation;
  confirmation_required: boolean;
};

export type RPCharacterAuthoringSaveResponse = RPCharacterAuthoringPreviewResponse & {
  saved: boolean;
};

export type CharacterCardImportReport = {
  ok: boolean;
  source_format: string;
  normalized_card: Record<string, unknown>;
  rp_profile_candidate: Record<string, unknown>;
  voice_profile_candidate: Record<string, unknown>;
  example_dialogue_candidate: { lines: string[] };
  flavor_lore_candidate: unknown[];
  structured_fact_candidate: unknown[];
  hidden_fact_candidate: unknown[];
  unsafe_or_unsupported_entries: unknown[];
  warnings: string[];
};

export type BatchCharacterCardImportReport = {
  target_world_id: string;
  parsed_count: number;
  failed_count: number;
  unsafe_count: number;
  duplicate_names: string[];
  candidate_characters: Record<string, unknown>[];
  rp_profiles: Record<string, Record<string, unknown>>;
  voice_profiles: Record<string, Record<string, unknown>>;
  example_dialogues: Record<string, unknown>[];
  unsafe_entries: Record<string, unknown>[];
  character_pack_draft: Record<string, unknown>;
  writes_to_disk: boolean;
  active_game_state_modified: boolean;
};

export type BatchLorebookClassificationReport = {
  target_world_id: string;
  total_entries: number;
  flavor_lore: Record<string, unknown>[];
  structured_fact_candidates: Record<string, unknown>[];
  hidden_fact_candidates: Record<string, unknown>[];
  unsafe_entries: Record<string, unknown>[];
  duplicate_keys: string[];
  prompt_injection_warnings: string[];
  validation?: AuthoringValidation | null;
  yaml_draft: string;
  writes_to_disk: boolean;
  normal_report: boolean;
};

export type ScriptPackageManifest = {
  package_id: string;
  name: string;
  version: string;
  target_engine_version: string;
  target_schema_version: string;
  included_worlds: string[];
  included_quests: string[];
  included_characters: string[];
  included_templates: string[];
  included_scenarios: string[];
  included_quality_profile?: string | null;
  dependencies: string[];
  conflicts: string[];
  checksums: Record<string, string>;
  created_at?: string;
  normal_manifest: boolean;
};

export type ScriptPackageFile = {
  path: string;
  content: string;
  hidden: boolean;
};

export type ScriptPackageBuildRequest = {
  manifest: ScriptPackageManifest;
  files: ScriptPackageFile[];
  available_dependency_ids: string[];
  packages_root: string;
  confirm_apply: boolean;
  normal_report: boolean;
};

export type ScriptPackageBuildReport = {
  manifest: ScriptPackageManifest;
  validation: AuthoringValidation;
  dry_run: boolean;
  applied: boolean;
  package_dir?: string | null;
  archive_file_name?: string | null;
  archive_base64?: string | null;
  files: string[];
  dependencies: string[];
  conflicts: string[];
  normal_manifest: Record<string, unknown>;
};

export type CampaignStarterKitDraft = {
  campaign_id: string;
  name: string;
  genre: string;
  tone: string;
  starting_region: string;
  core_conflict: string;
  npc_count: number;
  questline_count: number;
  faction_count: number;
  mystery_enabled: boolean;
  RP_focus_level: string;
  target_playtime_hours: number;
  llm_assisted?: boolean;
};

export type CampaignStarterKitPreview = {
  draft: CampaignStarterKitDraft;
  world_pack_draft: WorldPackWizardDraft;
  world_pack_preview: WorldPackWizardPreviewResponse;
  npc_pack_draft: NPCPackGeneratorDraft;
  quest_pack_draft: QuestPackGeneratorDraft;
  faction_draft?: Record<string, unknown> | null;
  mystery_draft?: Record<string, unknown> | null;
  scenario_regression_suite: Record<string, unknown>[];
  quality_gate_config: Record<string, unknown>;
  quality_gate_dry_run: {
    passed: boolean;
    validation_ok: boolean;
    quality_gate_dry_run: boolean;
    blockers: string[];
    warnings: string[];
    summary: Record<string, unknown>;
  };
  script_package_draft: ScriptPackageBuildReport;
  validation: AuthoringValidation;
  writes_to_disk: boolean;
  active_game_state_modified: boolean;
  built: boolean;
};

export type ProductionPipelineStatus = {
  status: string;
  count: number;
  warnings: string[];
  blockers: string[];
  summary: string;
};

export type ProductionPipelineTask = {
  tool_id: string;
  label: string;
  status: string;
  summary: string;
  warnings: string[];
  blockers: string[];
};

export type ProductionPipelineSummary = {
  local_only: boolean;
  generated_at: string;
  active_world?: string | null;
  active_production_drafts: ProductionPipelineTask[];
  recent_generated_packages: ProductionPipelineTask[];
  batch_validation_status: ProductionPipelineStatus;
  content_coverage_plan?: ContentCoveragePlan | null;
  quality_gate_summary: ProductionPipelineStatus;
  import_export_profile_status: ProductionPipelineStatus;
  script_package_build_status: ProductionPipelineStatus;
  campaign_starter_status: ProductionPipelineStatus;
  quick_entries: ProductionPipelineTask[];
  warnings: string[];
  blockers: string[];
  hidden_details_redacted: boolean;
  sensitive_details_redacted: boolean;
};

export type RPCharacterSafeExportResponse = {
  world_id: string;
  npc_id: string;
  card: Record<string, unknown>;
  excluded_fields: string[];
};

export type DialogueSceneOutcomeTemplate = {
  id: string;
  description: string;
  state_delta_operation?: string | null;
  state_delta_path?: string | null;
  allowed: boolean;
};

export type DialogueSceneTemplate = {
  id: string;
  name: string;
  participant_ids: string[];
  focus_npc_id: string;
  location_id: string;
  dialogue_mode: string;
  scene_mood?: string | null;
  rp_prompt_profile_id?: string | null;
  opening_context: string;
  allowed_topics: string[];
  forbidden_topics: string[];
  required_visible_facts: string[];
  possible_outcomes: DialogueSceneOutcomeTemplate[];
};

export type DialogueSceneAuthoring = {
  world_id: string;
  templates: DialogueSceneTemplate[];
};

export type DialogueScenePreviewResponse = {
  world_id: string;
  graph: DialogueSceneAuthoring;
  yaml_content: string;
  validation: AuthoringValidation;
  prompt_preview: Record<string, string>;
  confirmation_required: boolean;
};

export type DialogueSceneSaveResponse = DialogueScenePreviewResponse & {
  saved: boolean;
};

export type GroupRPParticipantRole = {
  role_id: string;
  npc_id: string;
  label: string;
  required: boolean;
};

export type GroupRPSceneTemplate = {
  id: string;
  name: string;
  scene_type: string;
  participant_ids: string[];
  required_roles: GroupRPParticipantRole[];
  location_id: string;
  turn_order_policy: string;
  speaker_selection_policy: string;
  scene_mood?: string | null;
  starting_tension: number;
  opening_public_context: string;
  allowed_topics: string[];
  forbidden_topics: string[];
  exit_conditions: string[];
  allow_dead_participants: boolean;
};

export type GroupRPSceneAuthoring = {
  world_id: string;
  templates: GroupRPSceneTemplate[];
};

export type GroupRPScenePreviewResponse = {
  world_id: string;
  graph: GroupRPSceneAuthoring;
  yaml_content: string;
  validation: AuthoringValidation;
  safe_prompt_preview: Record<string, string>;
  confirmation_required: boolean;
};

export type GroupRPSceneSaveResponse = GroupRPScenePreviewResponse & {
  saved: boolean;
};

export type DeclarativeActionTargetSpec = {
  kind: "self" | "current_location" | "location" | "object" | "npc";
  required: boolean;
  allowed_ids: string[];
};

export type DeclarativeStateDeltaTemplate = {
  operation: "set" | "inc" | "add" | "remove";
  path: string;
  value?: unknown;
  reason?: string | null;
  metadata?: Record<string, string>;
};

export type DeclarativeOutcome = {
  success_level: "success" | "partial_success" | "failure" | "invalid";
  reason: string;
  state_delta_templates: DeclarativeStateDeltaTemplate[];
  visible_facts: string[];
  hidden_facts: string[];
  hidden_outcome: boolean;
};

export type DeclarativeActionDefinition = {
  id: string;
  label: string;
  aliases: string[];
  category: string;
  target_specs: DeclarativeActionTargetSpec[];
  affordance_requirements: {
    required_visible_facts: string[];
    required_flags: Record<string, string | number | boolean>;
  };
  time_cost: number;
  preconditions: Record<string, unknown>[];
  checks: Record<string, unknown>[];
  outcomes: Record<string, DeclarativeOutcome>;
  state_delta_templates: DeclarativeStateDeltaTemplate[];
  event_type: string;
  visibility_policy: {
    hidden_outcome_player_visible: boolean;
    include_target_in_visible_facts: boolean;
    include_current_location_in_visible_facts: boolean;
  };
  narrator_hints: {
    style: string;
    safe_summary: string;
    hidden_summary: string;
  };
};

export type ActionModDraft = {
  module_id: string;
  name: string;
  version: string;
  actions: DeclarativeActionDefinition[];
};

export type ActionModValidationReport = {
  module_id: string;
  ok: boolean;
  errors: AuthoringValidationIssue[];
  warnings: AuthoringValidationIssue[];
};

export type ActionModPreviewResponse = {
  local_only: boolean;
  draft: ActionModDraft;
  validation: ActionModValidationReport;
  writes_to_disk: boolean;
  executes_code: boolean;
  active_game_state_modified: boolean;
  normalized_yaml: string;
};

export type ActionModExportResponse = {
  local_only: boolean;
  exported: boolean;
  file_name: string;
  archive_base64: string;
  validation: ActionModValidationReport;
  contains_api_key: boolean;
  writes_to_disk: boolean;
  executes_code: boolean;
};

export async function previewActionModDraft(draft: ActionModDraft): Promise<ActionModPreviewResponse> {
  return requestJson<ActionModPreviewResponse>("/authoring/action-mods/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(draft)
  });
}

export async function validateActionModDraft(draft: ActionModDraft): Promise<ActionModPreviewResponse> {
  return requestJson<ActionModPreviewResponse>("/authoring/action-mods/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(draft)
  });
}

export async function exportActionModDraft(draft: ActionModDraft): Promise<ActionModExportResponse> {
  return requestJson<ActionModExportResponse>("/authoring/action-mods/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(draft)
  });
}

export async function fetchExampleDialogues(worldId: string): Promise<ExampleDialogueListResponse> {
  return requestJson<ExampleDialogueListResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/example-dialogue`
  );
}

export async function previewExampleDialogues(
  worldId: string,
  entries: ExampleDialogue[]
): Promise<ExampleDialoguePreviewResponse> {
  return requestJson<ExampleDialoguePreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/example-dialogue/preview`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ entries })
    }
  );
}

export async function validateExampleDialogues(
  worldId: string,
  entries: ExampleDialogue[]
): Promise<ExampleDialoguePreviewResponse> {
  return requestJson<ExampleDialoguePreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/example-dialogue/validate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ entries })
    }
  );
}

export async function saveExampleDialogues(
  worldId: string,
  entries: ExampleDialogue[]
): Promise<ExampleDialogueSaveResponse> {
  return requestJson<ExampleDialogueSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/example-dialogue`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ entries })
    }
  );
}

export async function fetchRPCharacterAuthoring(worldId: string): Promise<RPCharacterAuthoring> {
  return requestJson<RPCharacterAuthoring>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/rp/characters/pro`
  );
}

export async function previewRPCharacterImport(
  worldId: string,
  rawContent: string,
  inputFormat = "auto"
): Promise<CharacterCardImportReport> {
  return requestJson<CharacterCardImportReport>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/rp/characters/pro/import-preview`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_content: rawContent, input_format: inputFormat })
    }
  );
}

function batchCharacterCardPayload(worldId: string, rawContents: string[], selectedNames: string[] = []) {
  return {
    target_world_id: worldId,
    pasted_texts: rawContents,
    selected_names: selectedNames
  };
}

export async function previewBatchCharacterCardImport(
  worldId: string,
  rawContents: string[]
): Promise<BatchCharacterCardImportReport> {
  return requestJson<BatchCharacterCardImportReport>("/production/characters/batch-import/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(batchCharacterCardPayload(worldId, rawContents))
  });
}

export async function applyBatchCharacterCardImportDraft(
  worldId: string,
  rawContents: string[],
  selectedNames: string[]
): Promise<BatchCharacterCardImportReport> {
  return requestJson<BatchCharacterCardImportReport>("/production/characters/batch-import/apply-draft", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(batchCharacterCardPayload(worldId, rawContents, selectedNames))
  });
}

export async function exportBatchCharacterCardPack(
  worldId: string,
  rawContents: string[],
  selectedNames: string[]
): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>("/production/characters/batch-import/export-pack", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(batchCharacterCardPayload(worldId, rawContents, selectedNames))
  });
}

function batchLorebookPayload(worldId: string, rawContents: string[], selectedKeys: string[] = []) {
  return {
    target_world_id: worldId,
    sources: rawContents.map((rawContent, index) => ({
      source_name: `pasted_lorebook_${index + 1}`,
      raw_content: rawContent,
      input_format: "auto"
    })),
    selected_keys: selectedKeys
  };
}

export async function previewBatchLorebookClassification(
  worldId: string,
  rawContents: string[]
): Promise<BatchLorebookClassificationReport> {
  return requestJson<BatchLorebookClassificationReport>("/production/lorebooks/batch-classify/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(batchLorebookPayload(worldId, rawContents))
  });
}

export async function applyBatchLorebookClassificationDraft(
  worldId: string,
  rawContents: string[],
  selectedKeys: string[]
): Promise<BatchLorebookClassificationReport> {
  return requestJson<BatchLorebookClassificationReport>("/production/lorebooks/batch-classify/apply-draft", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(batchLorebookPayload(worldId, rawContents, selectedKeys))
  });
}

export async function dryRunScriptPackageBuild(
  request: ScriptPackageBuildRequest
): Promise<ScriptPackageBuildReport> {
  return requestJson<ScriptPackageBuildReport>("/production/script-packages/build-dry-run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request)
  });
}

export async function buildScriptPackage(request: ScriptPackageBuildRequest): Promise<ScriptPackageBuildReport> {
  return requestJson<ScriptPackageBuildReport>("/production/script-packages/build", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request)
  });
}

export async function validateScriptPackage(request: ScriptPackageBuildRequest): Promise<ScriptPackageBuildReport> {
  return requestJson<ScriptPackageBuildReport>("/production/script-packages/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request)
  });
}

export async function exportScriptPackage(request: ScriptPackageBuildRequest): Promise<ScriptPackageBuildReport> {
  return requestJson<ScriptPackageBuildReport>("/production/script-packages/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request)
  });
}

export async function previewCampaignStarterKit(draft: CampaignStarterKitDraft): Promise<CampaignStarterKitPreview> {
  return requestJson<CampaignStarterKitPreview>("/production/campaign-starter/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(draft)
  });
}

export async function buildCampaignStarterKit(
  draft: CampaignStarterKitDraft,
  confirmBuild: boolean
): Promise<CampaignStarterKitPreview> {
  return requestJson<CampaignStarterKitPreview>("/production/campaign-starter/build", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft, confirm_build: confirmBuild })
  });
}

export async function exportCampaignStarterScriptPackage(
  draft: CampaignStarterKitDraft
): Promise<ScriptPackageBuildReport> {
  return requestJson<ScriptPackageBuildReport>("/production/campaign-starter/export-script", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(draft)
  });
}

export async function fetchProductionPipelineSummary(worldId?: string): Promise<ProductionPipelineSummary> {
  const query = worldId ? `?world_id=${encodeURIComponent(worldId)}` : "";
  return requestJson<ProductionPipelineSummary>(`/production/pipeline-summary${query}`);
}

export async function previewRPCharacterAuthoring(
  worldId: string,
  graph: RPCharacterAuthoring
): Promise<RPCharacterAuthoringPreviewResponse> {
  return requestJson<RPCharacterAuthoringPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/rp/characters/pro/preview`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(graph)
    }
  );
}

export async function validateRPCharacterAuthoring(
  worldId: string,
  graph: RPCharacterAuthoring
): Promise<RPCharacterAuthoringPreviewResponse> {
  return requestJson<RPCharacterAuthoringPreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/rp/characters/pro/validate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(graph)
    }
  );
}

export async function saveRPCharacterAuthoring(
  worldId: string,
  graph: RPCharacterAuthoring,
  confirmWarnings = false
): Promise<RPCharacterAuthoringSaveResponse> {
  return requestJson<RPCharacterAuthoringSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/rp/characters/pro?confirm_warnings=${confirmWarnings ? "true" : "false"}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(graph)
    }
  );
}

export async function exportSafeRPCharacterCard(
  worldId: string,
  npcId: string
): Promise<RPCharacterSafeExportResponse> {
  return requestJson<RPCharacterSafeExportResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/rp/characters/pro/safe-export`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ npc_id: npcId })
    }
  );
}

export async function fetchDialogueSceneAuthoring(worldId: string): Promise<DialogueSceneAuthoring> {
  return requestJson<DialogueSceneAuthoring>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/dialogue-scenes`
  );
}

export async function previewDialogueSceneAuthoring(
  worldId: string,
  graph: DialogueSceneAuthoring
): Promise<DialogueScenePreviewResponse> {
  return requestJson<DialogueScenePreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/dialogue-scenes/preview`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(graph)
    }
  );
}

export async function validateDialogueSceneAuthoring(
  worldId: string,
  graph: DialogueSceneAuthoring
): Promise<DialogueScenePreviewResponse> {
  return requestJson<DialogueScenePreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/dialogue-scenes/validate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(graph)
    }
  );
}

export async function saveDialogueSceneAuthoring(
  worldId: string,
  graph: DialogueSceneAuthoring,
  confirmWarnings = false
): Promise<DialogueSceneSaveResponse> {
  return requestJson<DialogueSceneSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/dialogue-scenes?confirm_warnings=${confirmWarnings ? "true" : "false"}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(graph)
    }
  );
}

export async function fetchGroupRPSceneAuthoring(worldId: string): Promise<GroupRPSceneAuthoring> {
  return requestJson<GroupRPSceneAuthoring>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/group-rp-scenes`
  );
}

export async function previewGroupRPSceneAuthoring(
  worldId: string,
  graph: GroupRPSceneAuthoring
): Promise<GroupRPScenePreviewResponse> {
  return requestJson<GroupRPScenePreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/group-rp-scenes/preview`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(graph)
    }
  );
}

export async function validateGroupRPSceneAuthoring(
  worldId: string,
  graph: GroupRPSceneAuthoring
): Promise<GroupRPScenePreviewResponse> {
  return requestJson<GroupRPScenePreviewResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/group-rp-scenes/validate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(graph)
    }
  );
}

export async function saveGroupRPSceneAuthoring(
  worldId: string,
  graph: GroupRPSceneAuthoring,
  confirmWarnings = false
): Promise<GroupRPSceneSaveResponse> {
  return requestJson<GroupRPSceneSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/group-rp-scenes?confirm_warnings=${confirmWarnings ? "true" : "false"}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(graph)
    }
  );
}

export type NarrativeProjectSummary = {
  project_id: string;
  name: string;
  path_redacted?: string;
  schema_version?: string;
  safe_status?: string;
};

export type NarrativeProject = {
  project_id: string;
  name: string;
  description?: string;
  version?: string;
  schema_version?: string;
  engine_version?: string;
  default_world_id?: string | null;
  active_campaign_id?: string | null;
  modes?: Record<string, boolean>;
  libraries?: Record<string, string | null>;
  safety_policy?: Record<string, boolean>;
};

export type NarrativeProjectListResponse = {
  projects: NarrativeProjectSummary[];
};

export type NarrativeProjectModeStatus = {
  mode: string;
  enabled: boolean;
  configured: boolean;
  missing_requirements: string[];
  safe_summary: Record<string, unknown>;
};

export type NarrativeProjectModesResponse = {
  project_id: string;
  modes: NarrativeProjectModeStatus[];
};

export type NarrativeProjectValidationReport = {
  project_id?: string | null;
  ok: boolean;
  errors: unknown[];
  warnings: unknown[];
  suggestions: unknown[];
  summary: Record<string, number>;
};

export type NovelManuscript = {
  manuscript_id: string;
  project_id: string;
  title: string;
  description?: string;
  genre_tags?: string[];
  target_style?: string;
  chapter_refs?: string[];
  default_prompt_profile_id?: string | null;
};

export type NovelChapter = {
  chapter_id: string;
  project_id: string;
  manuscript_id?: string | null;
  title: string;
  order_index: number;
  summary?: string;
  draft_text?: string;
  scene_refs?: string[];
  status?: string;
};

export type NovelScene = {
  scene_id: string;
  project_id: string;
  chapter_id: string;
  title: string;
  summary?: string;
  draft_text?: string;
  status?: string;
};

export type TavernCharacter = {
  tavern_character_id: string;
  project_id: string;
  display_name: string;
  description?: string;
  linked_character_profile_id?: string | null;
  linked_world_npc_id?: string | null;
  rp_profile_id?: string | null;
  voice_profile_id?: string | null;
  default_prompt_profile_id?: string | null;
  lorebook_refs?: string[];
  safety_flags?: string[];
};

export type TavernSession = {
  session_id: string;
  project_id: string;
  title: string;
  character_ids: string[];
  message_count?: number;
  status: string;
  scene_context?: Record<string, unknown>;
};

export type TavernMessage = {
  message_id: string;
  session_id: string;
  speaker_type: string;
  speaker_id?: string | null;
  content: string;
  created_at: string;
  safety_notes?: string[];
};

export type TavernScenePreset = {
  preset_id: string;
  name: string;
  description?: string;
  mood_tags?: string[];
  narration_style?: string;
  pacing?: string;
  sensory_focus?: string[];
  emotional_tone?: string;
  max_intensity?: number;
  safety_flags?: string[];
};

export type MatureContentPolicy = {
  enabled: boolean;
  max_rating: string;
  require_adult_characters: boolean;
  require_consent: boolean;
  default_fade_to_black: boolean;
  export_mature_content: boolean;
  allow_explicit_adult: boolean;
};

export type MatureSettingsResponse = {
  project_id: string;
  policy: MatureContentPolicy;
  warnings: string[];
};

export type MultiNPCSceneSummary = {
  scene_id: string;
  project_id: string;
  title: string;
  participant_ids: string[];
  turn_order: string[];
  current_turn_index: number;
  message_ids: string[];
  status: string;
  safety_notes: string[];
};

export type TavernChatResponse = {
  message_id: string;
  character_id: string;
  content: string;
  safety_notes: string[];
  proposed_world_effects: string[];
  created_at: string;
};

export type CrossModeDraftSummary = {
  artifact_id: string;
  project_id: string;
  direction: string;
  source_refs: string[];
  target_refs: string[];
  artifact_type: string;
  status: string;
  validation_status?: string;
  warnings?: string[];
  proposed_content?: Record<string, unknown>;
};

export type CrossModeValidationReport = {
  project_id?: string | null;
  ok: boolean;
  blockers: unknown[];
  errors: unknown[];
  warnings: unknown[];
  suggestions: unknown[];
  summary: Record<string, unknown>;
};

export type CrossModeTimelineEntry = {
  entry_id: string;
  source_mode: string;
  source_ref: string;
  title: string;
  safe_summary: string;
  visibility: string;
  proposal_status?: string | null;
};

export type CrossModeLinkReviewReport = {
  project_id: string;
  ok: boolean;
  broken_links: string[];
  hidden_target_risks: string[];
  duplicate_links: string[];
  stale_links: string[];
  links: Record<string, unknown>[];
};

export type CrossModeConflictReport = {
  project_id: string;
  ok: boolean;
  conflicts: Array<{ conflict_id: string; conflict_type: string; severity: string; safe_summary: string; status: string }>;
};

export type CrossModeAuditRecord = {
  audit_id: string;
  action_type: string;
  actor: string;
  source_artifact_id?: string | null;
  safe_summary: string;
  result: string;
  timestamp: string;
};

export async function fetchNarrativeProjects(): Promise<NarrativeProjectListResponse> {
  return requestJson<NarrativeProjectListResponse>("/projects");
}

export async function createNarrativeProject(input: {
  project_id: string;
  name: string;
  description?: string;
  project_root: string;
  default_world_id?: string;
  dry_run?: boolean;
}): Promise<{ dry_run: boolean; project: NarrativeProject }> {
  return requestJson<{ dry_run: boolean; project: NarrativeProject }>("/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function fetchNarrativeProject(projectId: string): Promise<NarrativeProject> {
  return requestJson<NarrativeProject>(`/projects/${encodeURIComponent(projectId)}`);
}

export async function validateNarrativeProject(projectId: string): Promise<NarrativeProjectValidationReport> {
  return requestJson<NarrativeProjectValidationReport>(`/projects/${encodeURIComponent(projectId)}/validate`, {
    method: "POST"
  });
}

export async function fetchNarrativeProjectModes(projectId: string): Promise<NarrativeProjectModesResponse> {
  return requestJson<NarrativeProjectModesResponse>(`/projects/${encodeURIComponent(projectId)}/modes`);
}

export async function fetchNovelManuscripts(projectId: string): Promise<{ project_id: string; manuscripts: NovelManuscript[] }> {
  return requestJson<{ project_id: string; manuscripts: NovelManuscript[] }>(`/projects/${encodeURIComponent(projectId)}/novel/manuscripts`);
}

export async function createNovelManuscript(projectId: string, input: { manuscript_id: string; title: string; description?: string }): Promise<NovelManuscript> {
  return requestJson<NovelManuscript>(`/projects/${encodeURIComponent(projectId)}/novel/manuscripts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function fetchNovelChapters(projectId: string): Promise<{ project_id: string; chapters: NovelChapter[] }> {
  return requestJson<{ project_id: string; chapters: NovelChapter[] }>(`/projects/${encodeURIComponent(projectId)}/novel/chapters`);
}

export async function createNovelChapter(projectId: string, input: { chapter_id: string; manuscript_id?: string; title: string; order_index?: number; draft_text?: string }): Promise<NovelChapter> {
  return requestJson<NovelChapter>(`/projects/${encodeURIComponent(projectId)}/novel/chapters`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function updateNovelChapter(projectId: string, chapterId: string, input: Partial<NovelChapter>): Promise<NovelChapter> {
  return requestJson<NovelChapter>(`/projects/${encodeURIComponent(projectId)}/novel/chapters/${encodeURIComponent(chapterId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function fetchNovelScenes(projectId: string): Promise<{ project_id: string; scenes: NovelScene[] }> {
  return requestJson<{ project_id: string; scenes: NovelScene[] }>(`/projects/${encodeURIComponent(projectId)}/novel/scenes`);
}

export async function createNovelScene(projectId: string, input: { scene_id: string; chapter_id: string; title: string; draft_text?: string }): Promise<NovelScene> {
  return requestJson<NovelScene>(`/projects/${encodeURIComponent(projectId)}/novel/scenes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function exportNovelManuscript(projectId: string, input: { manuscript_id: string; format: "markdown" | "txt"; chapter_ids?: string[] }): Promise<{ export_id: string; format: string; path: string; chapters_exported: string[] }> {
  return requestJson<{ export_id: string; format: string; path: string; chapters_exported: string[] }>(`/projects/${encodeURIComponent(projectId)}/novel/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function fetchTavernCharacters(projectId: string): Promise<{ project_id: string; characters: TavernCharacter[] }> {
  return requestJson<{ project_id: string; characters: TavernCharacter[] }>(`/projects/${encodeURIComponent(projectId)}/tavern/characters`);
}

export async function createTavernCharacter(projectId: string, input: { tavern_character_id: string; display_name: string; description?: string }): Promise<TavernCharacter> {
  return requestJson<TavernCharacter>(`/projects/${encodeURIComponent(projectId)}/tavern/characters`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function importTavernCharacterCard(projectId: string, rawContent: string): Promise<{ tavern_character: TavernCharacter; warnings: string[] }> {
  return requestJson<{ tavern_character: TavernCharacter; warnings: string[] }>(`/projects/${encodeURIComponent(projectId)}/tavern/import-character-card`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_content: rawContent, apply: true })
  });
}

export async function fetchTavernSessions(projectId: string): Promise<{ project_id: string; sessions: TavernSession[] }> {
  return requestJson<{ project_id: string; sessions: TavernSession[] }>(`/projects/${encodeURIComponent(projectId)}/tavern/sessions`);
}

export async function createTavernSession(projectId: string, input: { session_id: string; title: string; character_ids?: string[] }): Promise<TavernSession> {
  return requestJson<TavernSession>(`/projects/${encodeURIComponent(projectId)}/tavern/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function fetchTavernMessages(projectId: string, sessionId: string): Promise<{ project_id: string; session_id: string; messages: TavernMessage[] }> {
  return requestJson<{ project_id: string; session_id: string; messages: TavernMessage[] }>(`/projects/${encodeURIComponent(projectId)}/tavern/sessions/${encodeURIComponent(sessionId)}/messages`);
}

export async function sendTavernChatMessage(projectId: string, sessionId: string, input: { character_id: string; user_message: string }): Promise<TavernChatResponse> {
  return requestJson<TavernChatResponse>(`/projects/${encodeURIComponent(projectId)}/tavern/sessions/${encodeURIComponent(sessionId)}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function fetchTavernScenePresets(projectId: string): Promise<{ project_id: string; scene_presets: TavernScenePreset[] }> {
  return requestJson<{ project_id: string; scene_presets: TavernScenePreset[] }>(`/projects/${encodeURIComponent(projectId)}/tavern/scene-presets`);
}

export async function createTavernScenePreset(projectId: string, input: { preset_id: string; name: string; description?: string; mood_tags?: string[] }): Promise<TavernScenePreset> {
  return requestJson<TavernScenePreset>(`/projects/${encodeURIComponent(projectId)}/tavern/scene-presets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function fetchMatureSettings(projectId: string): Promise<MatureSettingsResponse> {
  return requestJson<MatureSettingsResponse>(`/projects/${encodeURIComponent(projectId)}/mature/settings`);
}

export async function updateMatureSettings(projectId: string, policy: Partial<MatureContentPolicy>): Promise<MatureSettingsResponse> {
  return requestJson<MatureSettingsResponse>(`/projects/${encodeURIComponent(projectId)}/mature/settings`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(policy)
  });
}

export async function fetchTavernMultiNPCScenes(projectId: string): Promise<{ project_id: string; scenes: MultiNPCSceneSummary[] }> {
  return requestJson<{ project_id: string; scenes: MultiNPCSceneSummary[] }>(`/projects/${encodeURIComponent(projectId)}/tavern/multi-scenes`);
}

export async function createTavernMultiNPCScene(projectId: string, input: { scene_id: string; title: string; participant_ids: string[]; turn_order?: string[] }): Promise<MultiNPCSceneSummary> {
  return requestJson<MultiNPCSceneSummary>(`/projects/${encodeURIComponent(projectId)}/tavern/multi-scenes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function generateTavernMultiNPCReply(projectId: string, sceneId: string): Promise<{ scene: MultiNPCSceneSummary; message: TavernMessage }> {
  return requestJson<{ scene: MultiNPCSceneSummary; message: TavernMessage }>(`/projects/${encodeURIComponent(projectId)}/tavern/multi-scenes/${encodeURIComponent(sceneId)}/next-reply`, {
    method: "POST"
  });
}

export async function createNovelToWorldDraft(projectId: string, input: { source_ref: string; draft_type: string; proposed_content?: Record<string, unknown> }): Promise<CrossModeDraftSummary> {
  return requestJson<CrossModeDraftSummary>(`/projects/${encodeURIComponent(projectId)}/cross-mode/novel-to-world/draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function validateNovelToWorldDraft(projectId: string, draftId: string): Promise<CrossModeDraftSummary> {
  return requestJson<CrossModeDraftSummary>(`/projects/${encodeURIComponent(projectId)}/cross-mode/novel-to-world/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft_id: draftId })
  });
}

export async function fetchNovelToWorldDrafts(projectId: string): Promise<{ project_id: string; drafts: CrossModeDraftSummary[] }> {
  return requestJson<{ project_id: string; drafts: CrossModeDraftSummary[] }>(`/projects/${encodeURIComponent(projectId)}/cross-mode/novel-to-world/drafts`);
}

export async function previewWorldToNovel(projectId: string, input: { safe_event_summaries: string[]; source_event_ids?: string[]; target_chapter_id?: string }): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>(`/projects/${encodeURIComponent(projectId)}/cross-mode/world-to-novel/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
}

export async function fetchCrossModeTimeline(projectId: string): Promise<{ project_id: string; entries: CrossModeTimelineEntry[] }> {
  return requestJson<{ project_id: string; entries: CrossModeTimelineEntry[] }>(`/projects/${encodeURIComponent(projectId)}/cross-mode/timeline`);
}

export async function fetchCrossModeLinks(projectId: string): Promise<CrossModeLinkReviewReport> {
  return requestJson<CrossModeLinkReviewReport>(`/projects/${encodeURIComponent(projectId)}/cross-mode/links`);
}

export async function detectCrossModeConflicts(projectId: string): Promise<CrossModeConflictReport> {
  return requestJson<CrossModeConflictReport>(`/projects/${encodeURIComponent(projectId)}/cross-mode/conflicts/detect`, { method: "POST" });
}

export async function validateCrossMode(projectId: string): Promise<CrossModeValidationReport> {
  return requestJson<CrossModeValidationReport>(`/projects/${encodeURIComponent(projectId)}/cross-mode/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile: "normal" })
  });
}

export async function fetchCrossModeAudit(projectId: string): Promise<{ project_id: string; audit: CrossModeAuditRecord[] }> {
  return requestJson<{ project_id: string; audit: CrossModeAuditRecord[] }>(`/projects/${encodeURIComponent(projectId)}/cross-mode/audit`);
}

export async function buildTavernApplyPlan(projectId: string, proposalId: string): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>(`/projects/${encodeURIComponent(projectId)}/cross-mode/tavern-to-world/proposals/${encodeURIComponent(proposalId)}/apply-plan`, { method: "POST" });
}

export async function fetchProjectModules(projectId: string): Promise<{ local_only: boolean; modules: ModuleBrowserSummary[] }> {
  return requestJson<{ local_only: boolean; modules: ModuleBrowserSummary[] }>(`/projects/${encodeURIComponent(projectId)}/modules`);
}

export async function scanProjectModules(projectId: string): Promise<{ local_only: boolean; modules: ModuleBrowserSummary[]; errors: string[] }> {
  return requestJson<{ local_only: boolean; modules: ModuleBrowserSummary[]; errors: string[] }>(`/projects/${encodeURIComponent(projectId)}/modules/scan`, { method: "POST" });
}

export async function fetchProjectModule(projectId: string, packageId: string): Promise<{ local_only: boolean; module: ModuleBrowserDetail }> {
  return requestJson<{ local_only: boolean; module: ModuleBrowserDetail }>(`/projects/${encodeURIComponent(projectId)}/modules/${encodeURIComponent(packageId)}`);
}

export async function validateProjectModule(projectId: string, packageId: string): Promise<{ local_only: boolean; validation: { ok: boolean; errors: string[]; warnings: string[] } }> {
  return requestJson<{ local_only: boolean; validation: { ok: boolean; errors: string[]; warnings: string[] } }>(`/projects/${encodeURIComponent(projectId)}/modules/${encodeURIComponent(packageId)}/validate`, { method: "POST" });
}

export async function fetchProjectModulePermissions(projectId: string, packageId: string): Promise<{ local_only: boolean; permissions: ModulePermissionSummary }> {
  return requestJson<{ local_only: boolean; permissions: ModulePermissionSummary }>(`/projects/${encodeURIComponent(projectId)}/modules/${encodeURIComponent(packageId)}/permissions`);
}

export async function fetchProjectModuleCompatibility(projectId: string, packageId: string): Promise<{ local_only: boolean; compatibility: Record<string, unknown> }> {
  return requestJson<{ local_only: boolean; compatibility: Record<string, unknown> }>(`/projects/${encodeURIComponent(projectId)}/modules/${encodeURIComponent(packageId)}/compatibility`);
}

export async function fetchProjectModulePermissionsSummary(projectId: string): Promise<{ local_only: boolean; permissions: ModulePermissionSummary[] }> {
  return requestJson<{ local_only: boolean; permissions: ModulePermissionSummary[] }>(`/projects/${encodeURIComponent(projectId)}/modules/permissions-summary`);
}

export async function buildProjectModuleCompatibilityMatrix(projectId: string, packageIds?: string[]): Promise<{ local_only: boolean; matrix: ModCompatibilityMatrix }> {
  return requestJson<{ local_only: boolean; matrix: ModCompatibilityMatrix }>(`/projects/${encodeURIComponent(projectId)}/modules/compatibility-matrix`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ package_ids: packageIds })
  });
}

export async function certifyProjectModule(projectId: string, packageId: string): Promise<{ local_only: boolean; certification: ExtensionCertificationReport }> {
  return requestJson<{ local_only: boolean; certification: ExtensionCertificationReport }>(`/projects/${encodeURIComponent(projectId)}/modules/${encodeURIComponent(packageId)}/certify`, { method: "POST" });
}

export async function runProjectModuleQualityGate(projectId: string, packageId: string): Promise<{ local_only: boolean; quality_gate: ModQualityGateResult }> {
  return requestJson<{ local_only: boolean; quality_gate: ModQualityGateResult }>(`/projects/${encodeURIComponent(projectId)}/modules/${encodeURIComponent(packageId)}/quality-gate`, { method: "POST" });
}

export async function runProjectAdvancedModuleQualityGate(projectId: string): Promise<{ local_only: boolean; quality_gate: AdvancedModuleQualityGateResult }> {
  return requestJson<{ local_only: boolean; quality_gate: AdvancedModuleQualityGateResult }>(`/projects/${encodeURIComponent(projectId)}/modules/quality-gate`, { method: "POST" });
}

export async function fetchAuthoringModuleDashboard(worldId: string): Promise<AdvancedModuleDashboardResponse> {
  return requestJson<AdvancedModuleDashboardResponse>(`/authoring/worlds/${encodeURIComponent(worldId)}/modules/dashboard`);
}

export async function fetchTacticalCombatConfig(worldId: string): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>(`/authoring/worlds/${encodeURIComponent(worldId)}/modules/tactical-combat/config`);
}

export async function validateTacticalCombatDraft(worldId: string, draft: Record<string, unknown>): Promise<AdvancedModuleDraftValidation> {
  return requestJson<AdvancedModuleDraftValidation>(`/authoring/worlds/${encodeURIComponent(worldId)}/modules/tactical-combat/validate-draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft })
  });
}

export async function fetchEconomySimConfig(worldId: string): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>(`/authoring/worlds/${encodeURIComponent(worldId)}/modules/economy-sim/config`);
}

export async function validateEconomySimDraft(worldId: string, draft: Record<string, unknown>): Promise<AdvancedModuleDraftValidation> {
  return requestJson<AdvancedModuleDraftValidation>(`/authoring/worlds/${encodeURIComponent(worldId)}/modules/economy-sim/validate-draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft })
  });
}

export async function fetchFactionWarConfig(worldId: string): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>(`/authoring/worlds/${encodeURIComponent(worldId)}/modules/faction-war/config`);
}

export async function validateFactionWarDraft(worldId: string, draft: Record<string, unknown>): Promise<AdvancedModuleDraftValidation> {
  return requestJson<AdvancedModuleDraftValidation>(`/authoring/worlds/${encodeURIComponent(worldId)}/modules/faction-war/validate-draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ draft })
  });
}

export async function fetchProjectModuleAudit(projectId: string): Promise<{ local_only: boolean; records: ModAuditRecord[] }> {
  return requestJson<{ local_only: boolean; records: ModAuditRecord[] }>(`/projects/${encodeURIComponent(projectId)}/modules/audit`);
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    const errorBody = await safeReadError(response);
    throw new Error(errorBody || `Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

async function safeReadError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? "";
  } catch {
    return "";
  }
}
