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
  turn: number;
  created_at: string;
  updated_at: string;
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

export async function listSaves(): Promise<SaveListResponse> {
  return requestJson<SaveListResponse>("/game/saves");
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

export async function fetchSessionDebugEvents(sessionId: string): Promise<DebugEventListResponse> {
  return requestJson<DebugEventListResponse>(
    `/debug/sessions/${encodeURIComponent(sessionId)}/events`
  );
}

export async function fetchSaveDebugEvents(saveId: string): Promise<DebugEventListResponse> {
  return requestJson<DebugEventListResponse>(`/debug/saves/${encodeURIComponent(saveId)}/events`);
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
