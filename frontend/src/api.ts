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
};

export type MapVisualGraph = {
  nodes: MapVisualNode[];
  edges: MapVisualEdge[];
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
};

export type AuthoringMapWriteResponse = {
  local_only: boolean;
  world_id: string;
  graph: MapVisualGraph;
  validation: AuthoringValidation;
  confirmation_required: boolean;
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

export type QuestObjectiveNode = {
  id: string;
  text: string;
};

export type QuestStageNode = {
  id: string;
  title: string;
  description: string;
  objectives: QuestObjectiveNode[];
  next_stages: string[];
  failure_stages: string[];
  alternate_stages: string[];
};

export type QuestTriggerNode = {
  type: string;
  id: string;
  action: string;
  objective_id?: string | null;
  next_stage?: string | null;
};

export type QuestRewardNode = {
  id: string;
  text: string;
  reward_type: string;
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
};

export type FactionAuthoringEdge = {
  source_faction_id: string;
  target_faction_id: string;
  relation: number;
  conflict_level: number;
  visibility: string;
};

export type FactionAuthoringGraph = {
  world_id: string;
  factions: FactionAuthoringNode[];
  conflict_edges: FactionAuthoringEdge[];
};

export type RelationshipAuthoringNode = {
  id: string;
  label: string;
  node_type: string;
  hidden: boolean;
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
};

export type SocialAuthoringGraph = {
  local_only: boolean;
  world_id: string;
  faction_graph: FactionAuthoringGraph;
  relationship_graph: RelationshipAuthoringGraph;
};

export type RelationshipAuthoringGraph = {
  world_id: string;
  nodes: RelationshipAuthoringNode[];
  relationships: RelationshipAuthoringEdge[];
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

export type ItemEconomyAuthoring = {
  local_only: boolean;
  world_id: string;
  items: ItemEconomyItem[];
  merchants: MerchantEconomyNode[];
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
};

export type QuestTriggerConsequenceNode = {
  id: string;
  quest_id: string;
  trigger_id: string;
  action: string;
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
  rumors: RumorAuthoringNode[];
  crimes: CrimeConsequenceNode[];
  reputation_effects: ReputationEffectNode[];
  quest_triggers: QuestTriggerConsequenceNode[];
  edges: ConsequenceGraphEdge[];
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

export type PromptProfileTemperatureOverrides = {
  narrator?: number | null;
  intent_parser?: number | null;
  memory?: number | null;
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
  enabled: boolean;
  matches_current_provider: boolean;
};

export type PromptProfileListResponse = {
  local_only: boolean;
  selected_profile_id: string;
  profiles: PromptProfile[];
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

export async function importWorldArchive(archiveBase64: string, overwrite = false): Promise<ArchiveImportResponse> {
  return requestJson<ArchiveImportResponse>("/authoring/import/worlds", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ archive_base64: archiveBase64, overwrite })
  });
}

export async function exportModArchive(modId: string): Promise<ArchiveExportResponse> {
  return requestJson<ArchiveExportResponse>(`/authoring/export/mods/${encodeURIComponent(modId)}`);
}

export async function importModArchive(archiveBase64: string, overwrite = false): Promise<ArchiveImportResponse> {
  return requestJson<ArchiveImportResponse>("/authoring/import/mods", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ archive_base64: archiveBase64, overwrite })
  });
}

export async function exportSaveArchive(saveId: string): Promise<ArchiveExportResponse> {
  return requestJson<ArchiveExportResponse>(`/authoring/export/saves/${encodeURIComponent(saveId)}`);
}

export async function importSaveArchive(archiveBase64: string, overwrite = false): Promise<ArchiveImportResponse> {
  return requestJson<ArchiveImportResponse>("/authoring/import/saves", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ archive_base64: archiveBase64, overwrite })
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
  graph: MapVisualGraph
): Promise<AuthoringMapWriteResponse> {
  return requestJson<AuthoringMapWriteResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/map`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
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
  graph: QuestGraphResponse
): Promise<QuestGraphSaveResponse> {
  return requestJson<QuestGraphSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/quests/graph`,
    {
      method: "PUT",
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
  graph: SocialAuthoringGraph
): Promise<SocialAuthoringSaveResponse> {
  return requestJson<SocialAuthoringSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/social/graph`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
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

export async function saveItemEconomyAuthoring(
  worldId: string,
  graph: ItemEconomyAuthoring
): Promise<ItemEconomyAuthoringSaveResponse> {
  return requestJson<ItemEconomyAuthoringSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/economy`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
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
  graph: RumorCrimeConsequenceAuthoring
): Promise<RumorCrimeConsequenceSaveResponse> {
  return requestJson<RumorCrimeConsequenceSaveResponse>(
    `/authoring/worlds/${encodeURIComponent(worldId)}/rumor-crime`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ graph })
    }
  );
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
