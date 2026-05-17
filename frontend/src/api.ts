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
};

export type QuestTriggerNode = {
  type: string;
  id: string;
  action: string;
  objective_id?: string | null;
  next_stage?: string | null;
};

export type QuestGraphNode = {
  id: string;
  title: string;
  description: string;
  initial_stage: string;
  visibility: string;
  stages: QuestStageNode[];
  triggers: QuestTriggerNode[];
};

export type QuestGraphEdge = {
  source: string;
  target: string;
  type: string;
  quest_id: string;
  label?: string | null;
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
  privacy_notes: string[];
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

export async function fetchScenarioTemplates(): Promise<ScenarioTemplateListResponse> {
  return requestJson<ScenarioTemplateListResponse>("/authoring/templates");
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
