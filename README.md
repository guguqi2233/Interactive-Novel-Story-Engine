# Local LLM Interactive Novel World Engine

A local-only interactive fiction engine where an LLM handles language-facing work and a deterministic Python world engine owns canonical state, rules, events, visibility, and saves.

v0.3 includes a playable local backend, a minimal React/Vite frontend, content packs, SQLite save/load, NPC schedules, search, inventory rules, lockpick, sneak, quest state, world tick, and a local debug timeline.

## Requirements

- Python 3.11+
- Node.js and npm
- SQLite

## Install Backend Dependencies

```powershell
python -m pip install -e ".[dev]"
```

## Configure Environment

Copy `.env.example` to your local environment file or set variables in your shell. Do not commit a real `.env`.

Useful defaults:

```powershell
$env:PYTHONPATH="backend"
$env:DATABASE_URL="sqlite:///./world_engine.db"
$env:LLM_PROVIDER="mock"
$env:ENABLE_DEBUG_API="true"
```

For OpenAI:

```powershell
$env:LLM_PROVIDER="openai"
$env:LLM_API_KEY="your-local-key"
```

API keys must come from environment variables. Do not put keys in code, tests, logs, or docs.

## Start Backend

From the repository root:

```powershell
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Start Frontend

From `frontend/`:

```powershell
npm install
npm run dev
```

The frontend reads the backend URL from:

```text
VITE_API_BASE_URL
```

If unset, it defaults to:

```text
http://127.0.0.1:8000
```

Example:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

## Choose a World

World content packs live under:

```text
worlds/{world_id}/
```

The included world is:

```text
mist_valley
```

Start a session with default world:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/game/start
```

Start a specific world:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/game/start `
  -ContentType "application/json" `
  -Body '{"world_id":"mist_valley"}'
```

The frontend provides a world selector with `mist_valley`.

## Play Through API

Submit player input:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/game/input `
  -ContentType "application/json" `
  -Body '{"session_id":"SESSION_ID","player_input":"observe"}'
```

Get current visible state:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/game/state/SESSION_ID
```

`visible_state` is filtered. It should not include hidden facts, hidden NPCs, undiscovered hidden objects, NPC secrets, or hidden inactive quests.

## Save and Load

List saves:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/game/saves
```

Save active session:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/game/SESSION_ID/save
```

Load save:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/game/load/SAVE_ID
```

Loading returns a new active `session_id` that can continue receiving input.

## Debug Timeline

Debug timeline is local-development only and controlled by:

```text
ENABLE_DEBUG_API
```

When enabled:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/debug/sessions/SESSION_ID/events
Invoke-RestMethod http://127.0.0.1:8000/debug/saves/SAVE_ID/events
```

The debug timeline may include raw `state_deltas`, including hidden/system-only information. It is intentionally separate from player-facing APIs and appears only in the frontend debug panel.

## Run Tests

```powershell
python -m pytest
```

Build frontend:

```powershell
cd frontend
npm run build
```

## Content Pack Structure

Example:

```text
worlds/mist_valley/
  manifest.yaml
  locations.yaml
  npcs.yaml
  items.yaml
  facts.yaml
  quests.yaml
```

The engine validates references such as exits, NPC locations, fact `known_by`, quest triggers, and item placement.

## Known v0.3 Limits

- No combat.
- No economy, shop, crafting, equipment, or weight systems.
- No complex NPC planning or LLM-driven agents.
- No pathfinding.
- No world editor.
- No vector database memory.
- Debug API has no production auth; keep it local-only.

