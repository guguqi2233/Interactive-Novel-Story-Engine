# LLM Protocol

## Purpose

The LLM protocol defines how this project talks to model providers without letting model output become trusted world state. All model calls pass through `LLMProvider`, and structured outputs are validated with Pydantic schemas.

The LLM is a parser, narrator, summarizer, and optional authoring draft assistant. It is not the world judge.

## Provider Boundary

Runtime provider construction must go through:

- `backend/app/llm/provider_factory.py`
- `create_llm_provider(settings)`

The factory reads `LLM_PROVIDER` from settings/environment.

Supported values:

- `mock`: default for local development and tests.
- `local_stub`: deterministic local-provider placeholder for tests and offline
  development. It does not call a model service.
- `local_http`: v0.6 interface stub for a future local HTTP model service. It
  validates `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`, and timeout configuration,
  but does not bind to a specific local model product yet.
- `openai`: OpenAI API provider.

Business modules depend on `LLMProvider`, not `OpenAIProvider` or a vendor SDK. Tests may use `FakeLLMProvider` as a controlled test double.

## Credentials

API keys are read only from environment variables.

- `LLM_API_KEY` is required when `LLM_PROVIDER=openai`.
- `LOCAL_LLM_BASE_URL` is required when `LLM_PROVIDER=local_http`.
- Real API keys must not be committed, logged, written into fixtures, returned from APIs, or stored in saves.
- Missing OpenAI credentials fail with a clear `LLMProviderError`.
- Unknown providers fail with a clear `LLMProviderError`.

Local provider settings:

- `LOCAL_LLM_BASE_URL`
- `LOCAL_LLM_MODEL`
- `LOCAL_LLM_TIMEOUT_SECONDS`

These settings must not expand LLM authority. Local models remain parser,
narrator, summarizer, or draft assistant providers behind `LLMProvider`; they
do not judge world outcomes or directly mutate `GameState`.

## Current LLM Uses

### IntentParser

`IntentParser` receives player text and asks the provider for a schema-validated `PlayerIntent`.

The parsed intent is input to the world engine. It does not modify `GameState`.

If provider/schema failure occurs, the parser returns a controlled clarification/unknown intent rather than applying world changes.

### Narrator

`Narrator` renders player-facing prose after the world engine has already resolved the action.

Inputs include:

- player input
- safe action result payload
- `visible_facts`
- current location id
- tone

`Narrator` does not receive:

- `ActionResult.hidden_facts`
- raw `GameState`
- raw system tick deltas
- raw debug event timeline
- witness records
- NPC secrets
- hidden/debug memories
- raw `state_deltas`

Current caution: `Narrator` receives `ActionResult.reason`. Rule authors must keep this reason player-safe. A future hardening pass should split `player_reason` and `debug_reason`.

### MemorySummarizer

`MemorySummarizer` summarizes recent events into `MemorySummary`.

It does not:

- mutate `GameState`
- apply `StateDelta`
- write `EventLog`
- promote summary text into canonical facts
- replace structured state

Because event payloads can contain raw `state_deltas`, summaries derived from hidden/debug events should be stored as `debug_only` or `hidden` unless explicitly sanitized.

### Memory Retrieval And Context

Memory retrieval is local deterministic code and does not call the LLM.

`MemoryRecord.visibility` values:

- `player_visible`
- `narrator_safe`
- `debug_only`
- `hidden`

`MemoryContextBuilder` builds separate lists:

- `narrator_safe_memories`
- `player_visible_memories`
- `npc_known_memories`
- debug-only exclusion reasons

Narrator-safe memory filtering allows only:

- `player_visible`
- `narrator_safe`

Forbidden for narrator:

- `debug_only`
- `hidden`
- memory linked to hidden/discoverable facts the player has not discovered
- memory tagged as `source_event_hidden`

NPC memory context also checks `npc_knows`; NPCs cannot receive memory tied to unknown facts.

Current runtime note: memory context is implemented and tested, but the main `GameLoop` currently calls `Narrator` with action-visible facts only. When memory is connected to runtime narration, it must pass through `MemoryContextBuilder`.

### Procedural Side Quest Drafts

`side_quest_generator.py` supports:

- deterministic `rule_based_generate_side_quest`
- optional `llm_assisted_generate_side_quest`

The LLM-assisted path:

- accepts an injected `LLMProvider`
- calls `generate_json` into the `QuestDraft` schema
- validates references against the loaded `WorldPack`
- rejects hidden fact text in player-facing draft fields
- returns `QuestDraft` only

It does not:

- modify active `GameState`
- apply `StateDelta`
- write `quests.yaml`
- activate or complete quests
- bypass world validation

Any future API/UI exposure for LLM-assisted drafts must remain authoring-only and require explicit user review/export.

## v0.5/v0.6 Rule Modules Do Not Call LLM

The following v0.5 modules are deterministic rule/code paths and do not call `LLMProvider`:

- content authoring service
- structured content validator
- local memory store retrieval backends
- `MemoryContextBuilder`
- NPC goals
- NPC planning tick
- relationship graph
- faction conflict layer
- economy/trade
- mod loader and mod validation
- multi-world save browser

The following v0.6 modules are also deterministic code paths and do not call
`LLMProvider`:

- save migration registry, service, API, and CLI
- migration compatibility fixtures
- authoring diff, preview, draft validation, and impact analysis
- player/debug relationship and faction graph generation
- deterministic playtesting agents and invariant checks
- narrative quality eval checks and report generation
- performance instrumentation and debug performance summaries
- advanced mod versioning, dependency checks, conflict checks, load order, and
  content schema compatibility checks
- desktop launcher prototype and packaging documentation
- advanced combat slice: stance, status effects, non-lethal attack, flee risk,
  and combat visible summary

Existing deterministic v0.3/v0.4 rule paths also do not call the LLM:

- search
- inventory rules
- lockpick
- sneak
- quest state machine
- NPC schedule resolver
- world tick
- faction reputation
- rumor propagation
- crime/witness rules
- social consequence tick
- combat core
- injury/death/incapacitation rules
- NPC reaction rules
- debug timeline API

They may receive a schema-validated `PlayerIntent`, but action results and state changes are decided by Python rules and emitted as `StateDelta`.

## v0.6 Local Provider Slice

v0.6 adds provider-factory entries for local model research:

- `local_stub`
- `local_http`

`local_stub` is safe for tests and offline development. It returns
schema-validated deterministic `PlayerIntent` and `NarrativeResult` payloads.

`local_http` is only a configuration-checked placeholder. Missing
`LOCAL_LLM_BASE_URL` fails clearly. Runtime generation currently raises a clear
provider error instead of calling an unspecified local service.

Business code must continue to depend only on `LLMProvider`. No rule module may
directly instantiate local provider classes or treat local model output as
canonical world state.

The local provider slice does not grant a local model any additional authority.
`local_stub` and future `local_http` responses are still schema-validated and
may only feed parser, narrator, summarizer, or author-facing draft workflows.
World outcomes, combat results, migration output, graph visibility, authoring
validation, mod compatibility, and playtesting reports remain rule-engine
decisions.

## Narrative Quality Evals

v0.6 adds deterministic narrative quality evals. They do not use an external
LLM judge and do not call real model APIs in automated tests. The evals inspect
mock/fake narrative outputs for:

- contradiction with `ActionResult`
- invented key items, NPCs, or locations
- hidden fact or hidden witness leakage
- unsafe suggested actions
- missing visible consequences where relevant
- excessive verbosity in simple cases

Eval reports are testing artifacts only. They do not modify `GameState` and do
not become canonical story facts.

## Output Validation

All LLM JSON outputs must validate against Pydantic schemas:

- `PlayerIntent`
- `NarrativeResult`
- `MemorySummary`
- `QuestDraft`

Schema validation failure must not silently modify state.

Observed behavior:

- `IntentParser` falls back to a clarification/unknown intent.
- `Narrator` errors propagate; `GameLoop` tests ensure state/event commit does not happen after narrator failure.
- `MemorySummarizer` invalid schema raises provider error.
- LLM-assisted side quest generation raises on invalid schema or invalid draft references.

## Error Handling

If an LLM call fails:

- do not mutate `GameState`
- do not apply deltas based on failed output
- return a clear application/provider error or controlled fallback
- do not print secrets or environment values

If narrator generation fails after rule resolution, `GameLoop` must not commit state or append events for the failed step.

## Visibility Rules For Prompts

Prompt inputs must obey world visibility:

- player-visible facts only
- narrator-safe memories only, if memory is introduced to narrator context
- no hidden facts unless discovered and promoted to `player_visible_facts`
- no NPC secrets unless deterministic rules explicitly make them player-visible
- no debug timeline data in narrative prompts
- no raw `state_deltas` in narrative prompts
- no raw `hidden_facts` field in narrator payloads
- no hidden witness identities unless discovered

The LLM can render prose or draft authoring candidates, but it cannot create canonical items, NPCs, locations, quest progress, crimes, rumors, combat outcomes, faction changes, memories, relationships, trade results, or facts.

## Known v0.6 Hardening Items

- Split `ActionResult.reason` into `player_reason` and `debug_reason`.
- Classify memory summaries from raw non-player-visible events as `debug_only` or `hidden` by default.
- Ensure any runtime memory-to-narrator integration uses only `MemoryContextBuilder.narrator_safe_memories`.
- Sanitize mod manifest errors before returning them through authoring APIs.
- Rewrite any mojibake prompt text into clean UTF-8 wording.
- Align `visible_state.relationships` with player graph filtering so hidden
  relationship endpoints cannot leak through the player API.
- Keep performance instrumentation tags free of prompt text, content text,
  hidden fact text, raw `GameState`, raw `state_deltas`, API keys, or local
  absolute paths.
