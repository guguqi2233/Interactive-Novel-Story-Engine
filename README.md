# Local LLM Interactive Novel World Engine

A local-only interactive fiction engine where an LLM handles language-facing work and a deterministic Python world engine owns canonical state, rules, events, visibility, social consequences, combat outcomes, and saves.

v0.4 includes a playable local backend, a minimal React/Vite frontend, content packs, SQLite save/load, NPC schedules, search, inventory rules, lockpick, sneak, quests, factions, rumors, crime/witnesses, social tick, combat, life state rules, NPC reactions, advanced memory retrieval, content validation, and a local debug timeline.

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

API keys must come from environment variables. Do not put keys in code, tests, logs, docs, saves, or database fixtures.

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

Build frontend:

```powershell
cd frontend
npm run build
```

## Choose A World

World content packs live under:

```text
worlds/{world_id}/
```

The included world is:

```text
mist_valley
```

Start a session with the default world:

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

`visible_state` is filtered. It should not include hidden facts, hidden NPCs, hidden witnesses, undiscovered hidden objects, NPC secrets, hidden inactive quests, hidden factions, or debug-only details.

## Save And Load

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

Do not expose debug endpoints on an untrusted network.

## Validate A World Pack

Run local content validation:

```powershell
python scripts\validate_world.py mist_valley
```

The validator reports:

- errors
- warnings
- suggestions

Exit codes:

- non-zero when errors exist
- zero when only warnings/suggestions exist

Validation checks schema, ids, exits, NPC locations, NPC faction references, item placement, quest triggers, fact `known_by`, rumor references, hidden fact leak warnings, schedule locations, and basic combat/life fields.

## v0.4 Features

### Social State

- `factions.yaml` loads faction state.
- Reputation changes are rule-generated `StateDelta` values.
- `known_rumors` and `known_crimes` appear only when player-visible.
- Crime/witness records can drive reputation and rumor consequences.

### Social Tick

World tick can process:

- NPC schedule
- quest triggers
- crime reports
- rumor propagation
- reputation consequences
- NPC reactions
- delayed consequences

### Combat And Life State

Implemented player actions:

- `attack`
- `defend`
- `flee`

Combat and injury outcomes are deterministic rules. The LLM only renders resolved outcomes. Dead/incapacitated NPCs cannot talk, move by schedule, or spread rumors.

### Memory Retrieval

Memory records can be searched by:

- tags
- entity ids
- fact ids
- substring
- turn range

Memory is not authoritative state. Hidden/debug memory is filtered from narrator/player contexts.

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
  factions.yaml
  rumors.yaml
```

See `docs/CONTENT_PACKS.md` for v0.4 content-pack fields and authoring notes.

## Run Tests

```powershell
python -m pytest
```

## Known v0.4 Limits

- No tactical grid combat or multi-round NPC combat AI.
- No guard pursuit, arrest, trial, or full legal system.
- No economy, shop, crafting, equipment progression, or weight systems.
- No complex NPC planning or LLM-driven agents.
- No pathfinding.
- No world editor UI.
- No vector database memory.
- Debug API has no production auth; keep it local-only.
- Raw faction reputation is still present in player API, though the frontend displays only the band.
