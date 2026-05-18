# LLM Protocol

## Purpose

The LLM protocol defines how this project talks to model providers without letting model output become trusted world state. All model calls pass through `LLMProvider`, and structured outputs are validated with Pydantic schemas.

The LLM is a parser, narrator, summarizer, and optional authoring draft assistant. It is not the world judge. In v1.0 this boundary is frozen as a stable local studio contract: model output can affect language-facing fields only after schema validation and cannot directly modify `GameState`.

## Provider Boundary

Runtime provider construction must go through:

- `backend/app/llm/provider_factory.py`
- `create_llm_provider(settings)`

The factory reads `LLM_PROVIDER` from settings/environment.

Supported values:

- `mock`: default for local development and tests.
- `local_stub`: deterministic local-provider placeholder for tests and offline
  development. It does not call a model service.
- `local_http`: configurable local HTTP provider for local model services that
  expose an OpenAI-compatible `/chat/completions` style endpoint. It validates
  `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`, timeout, and JSON-mode configuration
  without binding the engine to one specific local model product.
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
- `LOCAL_LLM_JSON_MODE`

These settings must not expand LLM authority. Local models remain parser,
narrator, summarizer, or draft assistant providers behind `LLMProvider`; they
do not judge world outcomes or directly mutate `GameState`.

## Current LLM Uses

### Prompt Profiles

`PromptProfile` is a local configuration layer for provider/model-specific prompt
preferences. Profiles can select safe prompt variants, narrator style text,
temperature overrides, and optional output-token preferences. Profiles are
loaded through `PromptProfileStore` and can be selected with
`PROMPT_PROFILE_ID` or the local Settings / Privacy UI.

Prompt profiles are explicitly not authority grants:

- they cannot add hidden facts, NPC secrets, raw `GameState`, or raw
  `state_deltas` to prompts
- they cannot let model output modify `GameState`
- they cannot bypass `LLMProvider`, schema validation, visibility filtering,
  `MemoryContextBuilder`, StateDelta, or EventLog
- invalid profiles that attempt to weaken these boundaries are rejected by
  schema validation

The current runtime passes the selected profile into `IntentParser`,
`Narrator`, and `MemorySummarizer`. This may change style, variants, or
temperature, but it does not change which facts those components receive.

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

## v1.0 Rule, Studio, And Quality Modules Do Not Call LLM

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

The following v0.7 local studio modules are also deterministic code paths and
do not call `LLMProvider`:

- Studio Home Dashboard and `GET /studio/status`
- Save Migration UI and migration API use
- Mod Manager UI and mod validation display
- Narrative Quality Dashboard report storage and display
- Performance Dashboard display of sanitized local samples
- Desktop launcher scripts and packaging documentation
- Scenario Template System list/preview/render/validation
- Visual Quest Graph Editor parse/preview/YAML conversion
- Automated Playtesting Dashboard and playtest report display
- Import/export service and archive validation
- Settings / Local Privacy summary endpoint and UI

These modules may display safe provider configuration status, but they do not
ask a model to decide validation, migration, mod compatibility, graph
visibility, import safety, playtest results, performance status, quest graph
correctness, or scenario template output validity.

The following v0.8 visual authoring modules are deterministic code paths and
do not call `LLMProvider`:

- visual map data model and map editor
- visual quest graph editor
- NPC goal editor
- faction/relationship visual editor
- item/economy editor
- rumor/crime consequence editor
- visual validation graph
- timeline replay visualizer
- world branch/diff
- scenario regression UI
- local template browser
- prompt profile manager
- advanced import/export packages
- desktop shell launcher scripts

The following v0.9 quality modules are deterministic code paths and do not call
`LLMProvider`:

- `WorldQualityReport`, `QualityIssue`, `QualityMetric`, and quality report
  aggregation
- expanded automated playtesting scenarios and batch runner
- scenario regression authoring and execution
- hidden information leak regression suite
- quest completion analysis
- dead-end and unreachable objective detection
- NPC behavior coverage and schedule conflict detection
- economy, combat, and social consequence balance/coverage checks
- save/load/migration stress tests
- performance benchmark suite
- narrative consistency evals
- world health score and content coverage dashboards
- branch diff regression testing
- mod compatibility stress testing
- quality gate CLI/API

These modules may use previously recorded events, playtest output, safe
visible-state snapshots, validation reports, and temporary sessions. They must
not use a model to decide whether a rule outcome is correct, whether content is
valid, or whether a quality gate passes.

### v1.0 Quality And Eval Boundary

v1.0 evals and playtests use deterministic fixtures, mock providers,
`local_stub`, or test harnesses. They do not call real OpenAI APIs, local HTTP
model services, or external LLM judges in automated tests.

The quality gate is not an LLM decision. It combines deterministic validation,
analysis reports, thresholds, and severities into pass/fail output. It must not
write results into active saves, mutate `GameState`, or promote report text
into canonical facts.

Narrative consistency evals inspect mock/fake narrator outputs for
contradictions with `ActionResult`, visible state, timeline, NPC knowledge,
quest state, item/location existence, hidden witness boundaries, and the rule
that memory is not authoritative fact. Failure summaries must be safe and must
not print hidden fact text.

Performance benchmarks and instrumentation may record stage names, durations,
counts, thresholds, and safe environment summaries. They must not record prompt
text, API keys, hidden fact text, raw `GameState`, or raw `state_deltas`.

Quality reports may contain debug-only diagnostic fields, but normal report
views must use safe summaries only. Hidden/debug memory remains filtered by
`MemoryContextBuilder`; quality tooling does not widen narrator or player
visibility.

The following v0.8 visual authoring and studio modules are also deterministic
code paths and do not call `LLMProvider`:

- Visual Map Data Model and Visual Map Editor.
- Visual Quest Graph Editor full authoring flow.
- NPC Goal Editor.
- Faction / Relationship Visual Editor.
- Item / Economy Editor.
- Rumor / Crime Consequence Editor.
- Visual Validation Graph.
- Timeline Replay Visualizer and replay dry-run.
- World Branch / Diff System.
- Scenario Regression Suite.
- Local Template Browser.
- Prompt Profile Manager validation and selection.
- Advanced Import / Export Packages.
- Desktop App Shell Polish.
- Authoring UX Integration Pass.

Visual editors may convert graph DTOs to YAML, validate drafts, and save
content after explicit user action. They do not ask an LLM to generate maps,
rewrite quests, create NPC goals, decide relationships, set prices, judge
crime/rumor consequences, explain validation errors, summarize hidden replay
events, or interpret diffs. Authoring outputs are content-pack edits, not
runtime `GameState` mutations, and must pass validation.

Prompt profiles are a style/configuration layer only. They can change prompt
variants, narrator style, temperature, and optional token preferences, but
they cannot add hidden facts, hidden/debug memory, NPC secrets, raw
`GameState`, raw `state_deltas`, or direct state-write instructions to any
prompt. Invalid profiles that attempt to widen authority are rejected.

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

## v0.8 Local Provider Integration

v0.7 introduced the configurable local HTTP provider, and v0.8 keeps it as the
current local model integration boundary:
integration while keeping the same authority boundary:

- `local_stub`
- `local_http`

`local_stub` is safe for tests and offline development. It returns
schema-validated deterministic `PlayerIntent` and `NarrativeResult` payloads.

`local_http` posts chat requests to
`{LOCAL_LLM_BASE_URL}/chat/completions` with `model`, `messages`, and
`temperature`. When `LOCAL_LLM_JSON_MODE=true`, JSON calls include
`response_format: {"type": "json_object"}`. Responses are accepted from common
OpenAI-compatible shapes such as `choices[0].message.content`, or from simple
`content`/`text`/`response` fields for lightweight local test harnesses.

Missing `LOCAL_LLM_BASE_URL` fails clearly. HTTP failures, non-JSON HTTP
responses, unparseable JSON model content, and Pydantic schema failures are
reported as `LLMProviderError`.

`generate_text` returns provider text only to language-layer callers.
`generate_json` parses model text as JSON and validates it against the caller's
Pydantic schema before returning it. A local model service is therefore not a
trusted state writer; it has the same bounded authority as any other provider.

Business code must continue to depend only on `LLMProvider`. No rule module may
directly instantiate local provider classes or treat local model output as
canonical world state.

The local provider slice does not grant a local model any additional authority.
`local_stub` and `local_http` responses are still schema-validated and
may only feed parser, narrator, summarizer, or author-facing draft workflows.
World outcomes, combat results, migration output, graph visibility, authoring
validation, mod compatibility, and playtesting reports remain rule-engine
decisions.

## Narrative Quality And Consistency Evals

v0.6+ uses deterministic narrative quality evals, and v0.9 adds narrative
consistency evals. They do not use an external LLM judge and do not call real
model APIs in automated tests. The evals inspect mock/fake narrative outputs
for:

- contradiction with `ActionResult`
- invented key items, NPCs, or locations
- hidden fact or hidden witness leakage
- unsafe suggested actions
- missing visible consequences where relevant
- excessive verbosity in simple cases
- contradiction with visible state or timeline
- dead NPCs speaking
- NPCs knowing unknown facts
- memory being treated as authoritative fact

Eval reports are testing artifacts only. They do not modify `GameState` and do
not become canonical story facts.

The v0.7 dashboard is only a report viewer/runner for these deterministic
checks. It must not send hidden fixtures to an external judge, and failed eval
case summaries shown in the UI must be safe/redacted.

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

## v1.0 Known Limitations

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
- Keep benchmark reports and quality gate results free of prompt text, hidden
  fact text, raw save JSON, and raw event deltas in normal views.
- Keep save export UX explicit that save archives can contain hidden runtime
  state and event history.
- Consider a dedicated `require_eval_api()` so eval routes can be enabled
  separately from broad debug access.
- Consider a dedicated `ENABLE_QUALITY_API` / `require_quality_api()` gate for
  all v0.9 analyzer endpoints. Current implementation gates the main
  playtest/eval/benchmark/quality-gate flows through existing local flags, but
  some analyzer endpoints are local-only without an independent quality flag.
- Keep v0.8 authoring graph response types out of player/narrator API routes.
- Add regression prompt snapshots for any future runtime memory-to-narrator
  integration.
- Keep package import/export reports summarized and avoid rendering raw save
  JSON, raw EventLog, or raw `state_deltas` outside debug/local-only panels.
