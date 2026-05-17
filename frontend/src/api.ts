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
  id: string;
  status: string;
  combatants?: string[];
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
};

export type SaveListResponse = {
  saves: SaveSummary[];
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

export async function fetchSessionDebugEvents(sessionId: string): Promise<DebugEventListResponse> {
  return requestJson<DebugEventListResponse>(
    `/debug/sessions/${encodeURIComponent(sessionId)}/events`
  );
}

export async function fetchSaveDebugEvents(saveId: string): Promise<DebugEventListResponse> {
  return requestJson<DebugEventListResponse>(`/debug/saves/${encodeURIComponent(saveId)}/events`);
}

export async function fetchAuthoringWorlds(): Promise<AuthoringWorldListResponse> {
  return requestJson<AuthoringWorldListResponse>("/authoring/worlds");
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
