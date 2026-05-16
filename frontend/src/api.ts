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
};

export type KnownFact = {
  id: string;
  text?: string | null;
  tags: string[];
};

export type VisibleQuest = {
  id: string;
  name: string;
  status: string;
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
