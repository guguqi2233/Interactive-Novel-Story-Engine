# LLM Protocol

## v2.5 Provider Gateway Pro Boundary

v2.5 upgrades Provider Gateway into the single safe model-entry boundary for
Novel, Tavern, World, Cross-Mode, Quality, and authoring workflows. Provider
selection may change wording, latency, cost estimate, formatting, or structured
output reliability. It cannot change world authority, reveal hidden facts, or
modify `GameState`.

Provider Gateway Pro components:

- `LLMProvider`: runtime provider contract. Providers must implement
  `generate_text` and schema-validated `generate_json`; optional streaming
  remains provider capability metadata, not a new authority path.
- `ProviderProfileV2`: project-local provider profile schema for provider type,
  model profiles, allowed modes, timeout, retry, fallback ids, cost hints, and
  safety policy. It rejects raw `api_key`, `llm_api_key`, and
  `openai_api_key` fields.
- `ModelProfile`: per-model capability and cost-hint metadata. Cost hints are
  local estimates, not billing records.
- `ProviderSecretResolver`: backend-only secret resolver for `api_key_env` and
  `secret_ref`. It may read environment variables or test fake secrets; it must
  never return secret values to frontend, exports, logs, usage reports, or
  quality reports.
- `ProviderRouter`: mode/use-case routing layer for `novel_draft`,
  `novel_rewrite`, `tavern_reply`, `world_intent_parse`, `world_narration`,
  `memory_summary`, `cross_mode_draft`, `quality_eval`, `structured_json`, and
  `cheap_summary`.
- `ProviderGateway`: executes safe provider calls through the resolved provider
  path, applies fallback behavior, records safe call traces, and preserves
  schema validation.

Mode-based routing rules:

- Novel draft/rewrite flows use Novel use cases.
- Tavern response generation uses `tavern_reply`.
- World intent parsing uses a JSON-capable route such as
  `world_intent_parse`.
- World narration uses `world_narration`.
- Memory summarization uses `memory_summary` and must not send raw
  `state_deltas`.
- Cross-mode draft/proposal helpers use `cross_mode_draft` or
  `structured_json`; apply, validation, quality gate pass/fail, import/export,
  and conflict detection remain deterministic and LLM-free.

Fallback rules:

- Fallback providers must satisfy the same required capabilities and safety
  policy as the primary provider.
- Fallback cannot bypass prompt safety filtering or Pydantic schema
  validation.
- Fallback traces use safe metadata only: provider/profile id, model id, use
  case, reason, timing, success, and error category. They must not contain
  prompt text, output text, API keys, provider secrets, raw env, hidden facts,
  or raw `state_deltas`.

Provider safety policy:

- `ProviderSafetyPolicy` controls allowed/disallowed modes, sensitive/debug
  prompt allowance, mature-content allowance, local-only requirements, prompt
  logging, output logging, and secret redaction.
- `log_prompts=false`, `log_outputs=false`, and `redact_secrets=true` are the
  safe defaults.
- Project-local-only policy must reject cloud/remote providers unless an
  explicit local trusted override is implemented for that call path.
- Provider profiles and routing rules cannot grant hidden fact access,
  `GameState` mutation, action-result override, visibility bypass, or proposal
  apply authority.

Structured output rules:

- Every `generate_json` result must be validated against a Pydantic schema
  before use.
- Schema failure must fail closed with a clear provider error or use a
  schema-valid fallback path.
- Model output may become text, draft, summary, or proposal metadata only after
  validation. It must not directly enter `GameState`, `EventLog`, content
  packs, facts, relationships, or save files.

Usage and privacy rules:

- Provider usage records store safe metadata only: provider/profile id, model
  id, mode, use case, estimated tokens, estimated cost, duration, success, and
  error category.
- Usage/cost tracking is local observability only. It is approximate, not
  billing-grade, and must not upload telemetry.
- Usage records, benchmark reports, structured-output reliability reports,
  routing explanations, call traces, fallback traces, frontend dashboards, and
  exports must not contain full prompts, full outputs, API keys, raw env,
  hidden facts, debug memory, or raw `state_deltas`.

Provider API and UI rules:

- Project provider APIs are local authoring/studio endpoints gated by local
  configuration.
- Frontend provider screens may edit provider type, env-var references,
  `secret_ref`, model profiles, allowed modes, routing preferences, and safe
  status. They must not include a plaintext API key field.
- OpenAI-compatible and relay profiles are generic compatible API profiles.
  The project does not provide API resale, online billing, cloud accounts, or
  vendor-specific relay integrations.

## v2.4 Cross-Mode Bridge LLM Boundary

v2.4 Cross-Mode Bridge does not grant the LLM any new world authority. Cross
mode pipelines may use LLM-assisted text generation only as a draft/proposal
assistant, and the current bridge implementation defaults to structured,
deterministic conversion and fake/mock/local providers in tests.

Cross-mode LLM rules:

- Novel -> World may produce draft/proposal candidates only. It cannot create
  authoritative World facts, write content packs, or modify `GameState`.
- World -> Novel may use safe EventLog/timeline summaries to create Novel
  draft text only. It cannot modify EventLog or `GameState`.
- Tavern -> World may create proposal/apply-plan text or structured proposal
  metadata only. The LLM cannot decide whether a proposal is applied.
- Tavern -> Novel may create Novel scene draft material only and must not
  import hidden/debug memory, private persona, raw `state_deltas`, or NPC
  secrets.
- Novel -> Tavern may create Tavern character/RP/voice drafts only and must
  exclude private notes in safe mode.
- `CrossModeLink` cannot bypass validation or visibility filtering.
- `CrossModeApplyPlan` must require explicit confirmation. LLM output cannot
  disable confirmation.
- Any World-changing apply path must use `StateDelta` and `EventLog`; LLM
  output is never applied directly.

Prompt/context exclusions for all cross-mode pipelines:

- hidden facts
- NPC secrets and NPC unknown facts
- private authoring notes / private persona
- raw debug memory
- raw `GameState`
- raw `state_deltas`
- API keys
- provider secrets
- raw env

Provider access remains unchanged: business code must use `LLMProvider` /
Provider Gateway or an injected fake provider in tests. Cross-mode validation,
conflict detection, import/export, audit, and quality-gate checks are
deterministic local checks and do not use an external LLM judge.

## v2.3 Tavern Studio LLM Boundary

v2.3 allows optional RP reply generation through
`TavernResponseGenerationService`. This does not expand LLM authority.

- Tavern generation accepts an injected `LLMProvider`; application code must not
  construct concrete provider SDK clients directly.
- Tavern chat routes obtain providers through app state or provider factory
  paths and tests use `FakeLLMProvider` / mock/local-stub providers.
- Prompt input must be built from `TavernPromptContext`.
- `TavernPromptContext` may contain only current speaker safe profile, safe
  `TavernRPProfile` summary, safe `TavernVoiceProfile` summary, safe scene mood
  fields, safe relationship tone summary, recent safe messages, tavern-safe
  memory, safe lorebook entries, and style instructions.
- `TavernPromptContext` must not contain hidden facts, NPC secrets, NPC unknown
  facts, private persona authoring-only text, raw debug memory, raw
  `state_deltas`, API keys, provider secrets, or raw env.
- Tavern-scoped `ProjectPromptProfile` values may affect style only. They cannot
  enable `can_access_hidden_facts`, `can_modify_state`,
  `can_override_action_result`, or `can_bypass_visibility`.
- `TavernRPProfile`, `TavernVoiceProfile`, `SceneMoodPreset`, and
  `RelationshipTone` affect expression, tone, pacing, and relationship flavor
  only. They do not change world facts or NPC knowledge.
- Generated output is schema-validated as `GeneratedTavernReply`.
- Generated RP text is a Tavern reply/draft only. It is not a World fact, does
  not write `GameState`, does not emit `StateDelta`, and does not append
  `EventLog`.
- Tavern-to-World outcomes must be represented as `TavernWorldProposal` and
  validated separately. v2.3 does not implement apply-to-World.
- Tavern safety evals are deterministic local checks and do not use an external
  LLM judge.

Testing rule: v2.3 Tavern tests must use fake/mock/local-stub providers and
must not call real OpenAI, OpenAI-compatible, or local HTTP services by default.

## v2.2 Novel Studio LLM Boundary

v2.2 allows optional LLM-assisted Novel drafting through
`NovelDraftGenerationService`, but this does not expand LLM authority.

- The service accepts an injected `LLMProvider`; it must not instantiate
  concrete providers directly.
- Prompt input must be built from `NovelPromptContext`, which contains only
  chapter/scene summaries, safe character summaries, safe World Bible context,
  safe timeline summaries, and style instructions.
- Novel-scoped `ProjectPromptProfile` values may affect style instructions and
  generation preferences only.
- Prompt profiles still cannot access hidden facts, modify state, override
  action results, or bypass visibility.
- Generated output is schema-validated as `GeneratedNovelDraft`.
- Generated text is a Novel draft/proposal only. It is not a World fact, does
  not modify `GameState`, and does not append `EventLog`.
- Tests use fake/mock/local providers and do not call real APIs.

Novel prompt context safety:

- `NovelPromptContext` must not include hidden facts, NPC secrets, raw debug
  memory, raw `state_deltas`, raw `GameState`, API keys, provider secrets, raw
  env, or unredacted authoring-private notes.
- World Bible and Lore/Fact context builders include flavor lore and safe
  structured summaries only in normal mode. Hidden and authoring-only entries
  are excluded unless an explicit authoring/debug view requests redacted notes.
- Character context uses safe summaries and excludes
  `private_notes_authoring_only`.
- Timeline context uses safe summaries only. Hidden and authoring-only timeline
  events are excluded.

Novel draft generation rules:

- `generate_scene_draft`, `rewrite_scene_style`, `summarize_chapter`, and
  `expand_outline_node` may call only an injected `LLMProvider` / Provider
  Gateway path.
- Generated text is saved only when the caller provides explicit confirmation;
  existing draft text must not be overwritten implicitly.
- Schema failures must return clear errors or fail closed. Model output is not
  trusted as world state.
- Tests must use fake/mock/local providers and must not call OpenAI or other
  real external APIs by default.

## v2.1 NarrativeProject LLM Boundary

v2.1 adds a project layer for Novel, Tavern, World, Script/Mods, Providers,
Quality, and Settings. This layer does not expand LLM authority. The LLM
remains a language-layer provider behind `LLMProvider` / Provider Gateway.

Mode-specific rules:

- Novel Mode stub may store outlines and chapter drafts. Drafts are not world
  facts and cannot directly write `GameState`.
- Tavern Mode stub may store RP sessions, messages, and proposals. Proposals
  do not create `StateDelta` values or world facts by themselves.
- World Mode remains the existing World Engine path. Facts are decided by
  deterministic rules, `StateDelta`, `EventLog`, and visibility.
- `CrossModeLink` stores references only. It cannot convert hidden facts,
  draft lore, RP memories, or Novel scenes into visible world state.

Project prompt/provider profile rules:

- `ProjectPromptProfile` may select style, prompt variants, temperature
  overrides, and output-token hints by mode.
- It cannot set `can_access_hidden_facts`, `can_modify_state`,
  `can_override_action_result`, or `can_bypass_visibility`.
- `ProjectProviderProfile` stores provider type, display metadata,
  capabilities, allowed modes, fallback id, and `api_key_env` references only.
  It must not contain raw API keys.
- Provider construction still goes through Provider Gateway / `LLMProvider`;
  project profiles are not concrete provider instances.

Shared libraries also preserve the boundary:

- World Bible hidden entries are not narrator-safe.
- Lore/fact hidden entries are filtered from Novel/Tavern normal context.
- Project memory is non-authoritative and hidden/debug memory is filtered.
- Character private notes are authoring-only and excluded from safe summaries.

## v2.0 Provider and Platform Boundary

v2.0 keeps Provider Gateway as the stable model access boundary. Plugins,
modules, authoring extensions, package import/export, campaign tools, timeline
branching, and character transfer cannot grant the LLM authority to modify
GameState or decide rules. Prompt/profile compatibility cannot enable hidden
facts or state modification. Tests and release checklists use mock/local
providers by default.

## Purpose

The LLM protocol defines how this project talks to model providers without letting model output become trusted world state. All model calls pass through `LLMProvider`, and structured outputs are validated with Pydantic schemas.

The LLM is a parser, narrator, summarizer, roleplay expression layer, optional
authoring/production draft assistant, and v1.5 local model/prompt experiment
target. It is not the world judge. In v1.0 this boundary is frozen as a stable
local studio contract, v1.1 extends it to RP dialogue, v1.2 extends local
visual authoring, v1.3 adds deterministic NPC simulation, v1.4 adds local
content production, and v1.5 adds Model & Prompt Lab diagnostics without
expanding LLM authority. v1.6 adds Advanced Gameplay Modules without changing
the LLM boundary: model output can affect language-facing draft fields or lab
reports only after schema validation and consistency checks, and cannot
directly modify `GameState` or decide gameplay outcomes. v1.7 adds local
Desktop Studio convenience, diagnostics, packaging safety, workspace
selection, and local configuration views without adding new LLM authority.

## Provider Boundary

Runtime provider construction must go through the provider boundary:

- `backend/app/llm/provider_factory.py`
- `create_llm_provider(settings)`
- `ProviderGateway` / `ProviderRouter` for v2.5 mode/use-case routing where
  the caller has project provider metadata

The legacy factory path reads `LLM_PROVIDER` from settings/environment.
Project-scoped v2.5 paths may also resolve `ProviderProfileV2` metadata and
then delegate construction through the same provider boundary.

Supported values:

- `mock`: default for local development and tests.
- `local_stub`: deterministic local-provider placeholder for tests and offline
  development. It does not call a model service.
- `local_http`: configurable local HTTP provider for local model services that
  expose an OpenAI-compatible `/chat/completions` style endpoint. It validates
  `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`, timeout, and JSON-mode configuration
  without binding the engine to one specific local model product.
- `openai`: OpenAI API provider.
- `openai_compatible`: OpenAI-compatible API profile for local/private/relay
  compatible endpoints without binding to a specific service.
- `relay`: relay-style compatible API profile that reuses the
  OpenAI-compatible protocol. It is not an API resale service.

Business modules depend on `LLMProvider`, `ProviderGateway`, or
`ProviderRouter` metadata, not `OpenAIProvider` or a vendor SDK. Tests may use
`FakeLLMProvider`, mock, or local-stub providers as controlled test doubles.

## Credentials

API keys are read only from environment variables.

- `LLM_API_KEY` is required when `LLM_PROVIDER=openai`.
- Project-scoped v2.5 provider profiles should use `api_key_env` names such as
  `OPENAI_API_KEY` or `RELAY_API_KEY`, or a `secret_ref` resolved only by the
  backend.
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

v1.5 adds `ProviderRouter` as a local routing configuration layer. Routing
rules select provider/model ids for use cases and may define fallback
constraints, but they do not contain credentials and do not create providers
directly. Runtime provider construction still delegates to `LLMProvider` /
`create_llm_provider`, and routing cannot grant world-judge or state-write
authority.

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

v1.1 adds `RPPromptProfile` inside `PromptProfile` for Dialogue Mode and Group
RP. It can tune roleplay style fields such as dialogue depth, emotional
intensity, prose density, response length, perspective, inner-thought handling,
and scene sensuality intensity. Its boundary fields are fixed:

- `hidden_fact_policy=deny`
- `state_modification_policy=deny`

Validation rejects profiles that try to override those values. RP prompt
profiles can alter expression style only; they cannot change NPC knowledge,
visible facts, `ActionResult`, `StateDelta`, quest state, consistency checks, or
world rules.

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

## v1.2 Visual Authoring Pro LLM Boundary

v1.2 Visual Authoring Pro modules are deterministic authoring tools. They do
not call `LLMProvider`, do not instantiate concrete providers, and do not use
model output to create authoritative content. They may show provider status in
studio surfaces, but provider selection remains limited to
`create_llm_provider`.

The following v1.2 modules do not call the LLM:

- Authoring Pro Boundary policy and checks.
- Authoring Validation Gate.
- Visual Map Editor Pro.
- Quest Graph Editor Pro and deterministic scenario regression draft
  generation.
- NPC Relationship Graph Editing.
- Faction Conflict Editor.
- Rumor / Crime Consequence Graph Pro.
- Item / Economy Editor Pro and balance warnings.
- RP Character Authoring UI Pro, import preview, validation, and safe export.
- Dialogue Scene Editor.
- Group RP Scene Authoring.
- Character Pack Builder import/export.
- Template Wizard.
- World Branch Merge Assistant.
- Content Diff Review.
- Authoring Workflow Presets.
- Local Content Library.
- Reference Picker / ReferenceIndex.
- Authoring Draft History.

Visual editors can convert graph DTOs to YAML, preview generated YAML, validate
drafts, show diff/impact reports, and save after explicit confirmation. They do
not ask an LLM to generate maps, quests, relationships, faction conflict,
rumors, crime consequences, prices, dialogue scene facts, group scene hidden
facts, templates, merge resolutions, or diff explanations.

Authoring drafts are not active runtime state. A v1.2 editor save writes
content-pack files only after validation and the Authoring Validation Gate. It
does not write active sessions, active saves, or live `GameState`.

RP authoring can edit public style/profile fields and private authoring fields,
but it cannot enlarge prompt permissions. Imported `system_prompt`,
`creator_notes`, unsafe example dialogue, hidden facts, and
`private_self_summary` stay out of ordinary player-facing and RP prompt
contexts unless deterministic code creates a separate safe field. Safe export
excludes hidden/private/debug fields.

Template Wizard, character-pack import, local library import, and package import
are data flows. They do not execute scripts, fetch remote URLs, read local
secrets, or automatically apply external content to active worlds. Imported or
generated content must remain draft/content-pack data and must pass validation.

Merge Assistant and Content Diff Review are structural tools. They do not call
an LLM to resolve conflicts or explain diffs. Conflict resolution requires an
explicit user choice.

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

## v1.1 Roleplay Prompt Boundary

v1.1 adds RP-oriented language surfaces: Dialogue Mode, Group RP, RP profiles,
voice profiles, scene mood presets, example dialogue, lorebook import,
Tavern-like compatibility import/export, RP memory context, RP prompt profiles,
and RP output consistency checks. These features are language/context layers.
They do not grant the LLM new world authority.

The RP boundary is defined in `docs/ROLEPLAY_BOUNDARY.md`. The short rule is:
expression may be flexible, facts are controlled. The model may vary voice,
word choice, mood, pacing, emotional expression, and dialogue density. It may
not create key facts, reveal hidden facts, decide quest progress, decide combat
or social outcomes, modify relationship values, update emotional state, or
write `GameState`.

### Dialogue Mode Prompt Rules

Dialogue Mode builds a safe `DialogueContext` for the current focus NPC. The
context may include:

- player-visible facts
- facts known by the speaking NPC
- safe public RP/voice profile fields
- safe emotional-state summary
- safe relationship-tone summary
- prompt-safe example dialogue summaries
- selected scene mood style fields
- selected RP prompt profile style fields
- RP memory already filtered by `RPMemoryContextBuilder`

It must not include:

- hidden facts unknown to the player
- facts unknown to the speaking NPC
- NPC secrets not revealed by rules
- `private_self_summary` unless explicitly made safe/known
- hidden/debug memory
- raw `GameState`
- raw `state_deltas`
- debug timeline data
- imported system prompts or creator notes marked unsafe

Dialogue output is text. Any resulting state change must come from
deterministic rules through `StateDelta` and `EventLog`, not from model text.

### Group RP Prompt Rules

Group RP builds participant-specific contexts. NPC A and NPC B do not share a
global all-knowing context. Each participant receives only that NPC's known
facts, safe memory, emotional summary, relationship tone, and relevant visible
scene context. Hidden facts known by one NPC cannot appear in another NPC's
prompt unless normal NPC knowledge rules allow it.

The next speaker is selected by deterministic code using scene state,
relationship tension, emotional intensity, topic relevance, quest relevance, or
manual focus. The model may produce a single participant's expression, but it
does not decide world facts or simultaneously mutate multiple NPCs.

### RP Profile, Scene Mood, And Prompt Profile Permissions

`RPProfile`, `VoiceProfile`, `SceneMoodPreset`, and `RPPromptProfile` are style
inputs only. They can change:

- tone
- sentence length
- vocabulary and catchphrases
- emotional expression intensity
- scene mood and pacing
- response length and perspective

They cannot change:

- NPC knowledge
- visible facts
- `ActionResult`
- `StateDelta`
- quest state
- relationship values
- combat/crime/trade outcomes
- memory authority

`RPPromptProfile.hidden_fact_policy` and
`RPPromptProfile.state_modification_policy` are fixed to `deny`; validation
rejects profiles that attempt to widen them.

### Import And Lorebook Prompt Safety

Character card, lorebook, and Tavern-like import are authoring-only flows.
External `system_prompt`, `creator_notes`, prompt injection instructions,
script-like payloads, and remote URL references are not trusted. Import reports
classify entries as safe style/flavor, structured fact candidates, hidden fact
candidates, or unsafe entries. Structured facts must become content-pack facts
through authoring validation before they are authoritative. Hidden fact
candidates remain under visibility rules. Unsafe entries do not enter prompts.

Example dialogue can guide style only. It is not a memory record, not NPC
knowledge, and not a canonical fact. Only `prompt_safe` examples with safe fact
policy can enter dialogue prompts.

### RP Memory Filtering

`RPMemoryContextBuilder` extends the existing memory boundary for dialogue. It
filters out:

- `hidden` memory
- `debug_only` memory
- memory tied to hidden facts not currently visible
- memory tied to facts the speaking NPC does not know
- raw event/debug summaries

Memory remains context support, not truth. If memory conflicts with
`GameState`, `GameState` wins.

### RP Consistency Checking

`RPOutputConsistencyChecker` checks generated RP text for hidden fact leakage,
NPC unknown-fact mentions, invented key items/NPCs/locations, dead NPCs
speaking, contradiction with `ActionResult`, unauthorized relationship change,
unauthorized quest completion, and raw debug/state-delta leakage. It is a
deterministic checker, not an external LLM judge.

RP boundary evals and RP regression playtests use fake/mock outputs and
mock/local providers. They do not call real model APIs.

## v1.2 Prompt Safety Notes

Narrator and dialogue prompt safety remains unchanged in v1.2:

- `Narrator` receives only safe action result payload, current location, tone,
  and visible facts.
- Dialogue context receives player-visible facts, NPC-known facts, safe
  RP/voice fields, prompt-safe examples, scene mood style, relationship tone,
  and filtered RP memory.
- Group RP builds a separate context per participant.
- Hidden facts, NPC secrets, hidden/debug memory, raw `GameState`, raw
  `state_deltas`, authoring draft YAML, import reports, diff payloads, merge
  conflicts, and draft history snapshots do not enter ordinary prompts.

Prompt profiles and RP prompt profiles can alter style, variants, temperature,
and RP expression settings only. They cannot add hidden facts, change NPC
knowledge, bypass visibility, grant state-write authority, or change the
provider construction path.

## v1.3 NPC Simulation LLM Boundary

v1.3 Advanced NPC Simulation does not add LLM authority. NPC behavior is
selected by deterministic rule modules, not by model output. The LLM may later
express an already selected behavior in narration or dialogue, but it cannot
choose the behavior, generate authoritative plans, grant knowledge, create
facts, or write `GameState`.

The following v1.3 modules are rule-only paths and must not call
`LLMProvider`, concrete provider classes, `generate_text`, or `generate_json`:

- NPC Simulation Boundary / `NPCSimulationPolicy`
- NPC Intent Queue
- NPC Short-Term Plans
- NPC Memory-Based Reactions
- NPC Relationship-Driven Behavior
- NPC Faction Duties
- NPC Rumor Decisions
- NPC Fear / Trust / Loyalty Models
- NPC Conflict Avoidance
- NPC Daily Goal Replanning
- NPC Simulation Tick Orchestrator
- NPC Simulation Debugger and Behavior Timeline
- NPC Simulation Authoring Presets
- NPC Simulation Quality Evals
- NPC Simulation Regression Playtests

NPC simulation may produce candidate intents, finite plans, `StateDelta`
entries, and `Event` records. It must not:

- ask an LLM to decide NPC actions
- ask an LLM to generate free-form plans
- use LLM output to decide rumor propagation, faction duties, fear/trust values,
  conflict avoidance, or daily replanning
- pass debug simulation traces to narrator prompts
- let hidden facts enter NPC prompts or RP prompts unless normal visibility and
  NPC knowledge rules allow them
- apply model output directly to `GameState`

NPC dialogue context remains scoped to `npc_known_facts`, player-visible facts,
safe RP/voice fields, relationship tone, emotional summaries, scene mood, and
filtered memory. Group RP builds a separate context for each participant. One
NPC's hidden knowledge cannot be copied into another NPC's prompt.

Prompt profiles, RP profiles, scene moods, social disposition, relationship
tone, and simulation presets are expression/configuration inputs only. They
cannot expand LLM permissions or make model text authoritative.

## v1.4 Content Production LLM Boundary

v1.4 Content Production Pipeline modules are deterministic local draft and
package tools by default. They do not call a real LLM to create worlds, NPCs,
quests, mysteries, factions, script packages, campaign starters, imports,
batch reports, coverage plans, or quality gate decisions.

The following v1.4 modules are rule/service paths and must not call
`LLMProvider`, concrete provider classes, `generate_text`, or `generate_json`
in normal operation:

- Content Production Boundary policy
- World Pack Wizard
- NPC Pack Generator
- Quest Pack Generator
- Location Cluster Templates
- Mystery Template System
- Faction Template System
- Content Batch Validator
- Content Coverage Planner
- Export / Import Profiles
- Local Content Library Pro
- Batch Character Card Import
- Batch Lorebook Classification
- Script Package Builder
- Campaign Starter Kit Builder
- Production Pipeline Dashboard
- Content Production CLI
- Batch Quality Gate

Some draft schemas expose `llm_assisted` as reserved metadata for a future
draft helper. In the current implementation it does not call a real provider.
If a future LLM-assisted generation path is added, it must:

- use `create_llm_provider(settings)` / `LLMProvider`
- default to `mock`, `local_stub`, or fake providers in tests
- produce `production_draft`, `generated_content_candidate`, or package draft
  objects only
- validate output through Pydantic schemas
- classify hidden/public fields before preview
- run Authoring Validation Gate before save/apply/import/export/build
- run Quality Gate or Batch Quality Gate for release/package operations
- never write active `GameState`
- never apply `StateDelta`
- never record runtime `Event` as a consequence of generation
- never bypass visibility, NPC knowledge, RP private-field, or hidden-content
  redaction rules

Content generation output is not authoritative content until the user reviews
it, validation passes, and explicit save/apply/build writes content-pack or
package files. Even after content is saved, it affects runtime only when a
world pack is loaded and normal rules expose it.

Batch character card import and batch lorebook classification treat external
prompt text as untrusted data. Imported prompt instructions cannot override
system prompts, visibility, `StateDelta`, `EventLog`, validation gates, or
package safety. Unsafe entries are flagged for review, and hidden facts remain
hidden fact candidates rather than player-facing prompt content.

Narrator and dialogue prompt boundaries are unchanged in v1.4:

- Narrator receives visible facts and narrator-safe memory only.
- NPC dialogue receives NPC-known facts and NPC-safe memory only.
- RP prompt profiles can tune expression but cannot expand authority.
- Production debug data, package manifests, batch reports, hidden truth facts,
  unsafe import text, and dry-run reports are not narrator inputs.

## v1.5 Model & Prompt Lab LLM Boundary

v1.5 Local Model & Prompt Lab is a local diagnostic surface for providers,
models, prompt profiles, prompt diffs, context snapshots, structured output,
token budgets, usage summaries, compatibility, and prompt experiment packages.

It may call a provider only for explicit lab runs such as benchmark, structured
output reliability, Prompt A/B, narrator style, NPC voice style, prompt
regression, or local diagnostics. These runs default to fake/mock/local_stub
providers. Real external provider benchmark/regression runs require explicit
`allow_real_provider=true`; real local HTTP diagnostics require
`allow_real_local_check=true`.

Prompt Lab must not:

- mutate active `GameState`, active saves, active sessions, or active content
  packs
- treat benchmark/model output as canonical facts
- let Prompt Profiles grant hidden facts, NPC secrets, raw `GameState`, raw
  `state_deltas`, or state-write authority
- record API keys, raw env, raw sensitive prompts, hidden fact text, or raw
  provider secrets in normal reports
- expose debug context through ordinary UI, player UI, narrator prompts, or
  exported packages
- bypass Pydantic schema validation for structured output
- switch production provider configuration automatically based on benchmark or
  compatibility results

### Provider Factory / Router Usage

Allowed v1.5 provider entry points:

- `create_llm_provider(settings)`
- `LLMProvider`
- local fake provider/test doubles for deterministic tests
- `ProviderRouter` for selecting provider/model ids before delegating to the
  factory/provider abstraction

Disallowed:

- business/lab modules directly constructing `OpenAIProvider`,
  `LocalHTTPProvider`, or other concrete runtime providers
- storing API keys in routing rules, Prompt Profiles, experiment packages, or
  frontend state
- treating compatibility matrix recommendations as automatic routing changes

### Prompt Profile Safety Boundary

`PromptProfile` can configure provider/model filters, prompt variants,
narrator style, temperature overrides, max output hints, scene mood id, and RP
style fields.

`RPPromptProfile` can configure expression fields such as dialogue depth,
emotional intensity, prose density, response length, perspective, inner-thought
policy, and sensuality policy.

Both remain style/configuration only:

- `hidden_fact_policy` must be `deny`
- `state_modification_policy` must be `deny`
- profiles cannot add hidden facts or NPC knowledge
- profiles cannot modify `ActionResult`, `StateDelta`, EventLog, quest state,
  relationship values, inventory, combat, economy, or facts

Prompt Diff must mark any relaxed hidden-fact or state-modification policy as
a blocker.

### Context Redaction

`Context Inspector` builds read-only `ContextSnapshot` reports. Sections are
classified as:

- `normal`
- `narrator_safe`
- `npc_known`
- `debug_only`
- `hidden_redacted`

Normal reports may show labels, token estimates, safe summaries, redacted ids,
and exclusion reasons. They must not show hidden fact text, NPC secrets,
hidden/debug memory text, raw `GameState`, raw `state_deltas`, API keys, raw
env, or full sensitive prompts.

`include_debug_raw` is off by default. If enabled for local debug, the raw
prompt field is still redacted and must not be copied into player UI,
narration, exports, packages, or normal dashboards.

### Real Provider Benchmark Principle

Provider benchmarks, Prompt A/B, style labs, structured output reliability,
and prompt regression default to fake/mock/local providers. Real provider
calls require explicit request flags and should show local UI/CLI warnings.

Reports must store safe summaries and metrics only:

- pass/fail or blocker flags
- schema reliability
- hidden leak flags
- latency and estimated cost
- redacted prompt previews
- safe error classes

They must not store full sensitive prompt text, hidden fact text, API keys, or
raw provider credentials.

### Structured Output Reliability

Structured output tests exercise schemas such as:

- `PlayerIntent`
- `NarrativeResult`
- `MemorySummary`
- `QuestDraft`
- `CharacterCardImportResult`
- `LorebookClassificationResult`
- `RPConsistencyReport`

Invalid JSON, schema validation errors, retry failures, refusals, and hidden
policy violations are reported as diagnostics. They do not produce canonical
state, `StateDelta`, or content-pack writes.

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
- Keep v1.2 Merge Assistant and ReferenceIndex normal views redacted when
  showing hidden/private content. Full merge conflict payloads and hidden
  reference labels are local authoring/debug data, not player or prompt input.
- Add static regression tests that fail if v1.2 visual authoring modules import
  concrete LLM providers or call `generate_text` / `generate_json`.

## v1.6 Gameplay Modules LLM Boundary

v1.6 Advanced Gameplay Modules are deterministic rule modules and declarative
Action Mods. They do not call the LLM to judge results, and they do not give
Prompt Profiles or provider routing any new world authority.

The runtime boundary is:

`ActionRegistry -> ActionHandler/rule module -> ActionResult -> StateDelta -> EventLog -> Visibility / NPC Knowledge -> Narrator`

### What The LLM May Do

- Parse player language into a candidate `PlayerIntent`.
- Render prose after the gameplay module has already returned a structured
  `ActionResult`.
- Help draft module/action content in local authoring contexts, with schema
  validation, preview, and explicit save/export.

### What The LLM Must Not Do

- Decide whether a gameplay action succeeds or fails.
- Decide spell effects, hacking outcomes, crafting outputs, deduction truth,
  stealth detection, combat hit/damage/death, social manipulation results,
  faction mission completion, travel risk, survival consequences, or domain
  income.
- Produce `StateDelta` values that bypass rule validation.
- Modify `GameState`, saves, databases, content packs, or module packages
  directly.
- See hidden facts, NPC secrets, hidden witnesses, debug module traces, raw
  module StateDelta previews, or raw `GameState` in ordinary prompts.
- Enable module permissions such as `call_llm`, `execute_code`,
  `access_network`, or direct state mutation.

### Module-Specific Boundary

- Declarative Action Mods are data. They do not import provider code and do
  not call `generate_text` or `generate_json`.
- Magic, hacking, crafting, investigation, survival, stealth, combat, social
  manipulation, faction missions, and domain/base management resolve through
  local handlers, DSL checks, seeded RNG where applicable, and structured
  deltas/events.
- Narrator receives only player-safe action results and visible facts. It may
  describe "the spell fizzles" or "the terminal raises an alarm", but those
  outcomes are already decided before narration.
- Module debug APIs and dry-run traces are gated by `ENABLE_DEBUG_API` and are
  not prompt inputs.
- Module quality and regression tools use deterministic checks and
  mock/fake/local_stub defaults; they do not use an LLM judge.

### Prompt/Profile Interaction

Prompt Profiles and RP Prompt Profiles remain expression controls only. They
cannot:

- make hidden module state visible
- grant NPCs unknown facts
- change Action DSL policy
- alter module permission validation
- turn LLM output into canonical action effects

Provider routing and Model Compatibility Matrix entries may choose a model for
language-facing use cases, but they cannot route around `LLMProvider`, module
rules, schema validation, StateDelta, EventLog, Visibility, or NPC Knowledge.

## v1.7 Desktop Studio LLM Boundary

v1.7 desktop tools are local operational and packaging surfaces. They do not
call the LLM to diagnose, repair, validate, package, restore, or modify the
world. They do not make the desktop shell a world judge or a state editor.

The following v1.7 modules and scripts are deterministic local code paths and
must not call `LLMProvider`, concrete provider classes, `generate_text`, or
`generate_json`:

- Desktop Studio Boundary policy.
- Desktop Launcher Pro scripts.
- Project Selector.
- Recent Projects.
- Local Config Manager.
- Local Update Notes.
- Desktop Health Check.
- Workspace Templates.
- Crash Report Local Viewer.
- Startup Diagnostics CLI.
- Desktop packaging safety checks.

The roadmap also defines Log Viewer, Error Recovery Wizard, Backup / Restore,
One-click Quality Gate, One-click Export World Pack, Offline Help Docs, and
Desktop Settings surfaces. Where implemented or extended, these must remain
local deterministic tools. They must not use an LLM to analyze logs, repair
errors, select recovery actions, approve backups, judge quality gates, or
decide export safety.

### Desktop Tools Cannot Modify State Through LLM Output

Desktop tools may start local processes, show safe status, summarize local
workspace metadata, generate `.env.example`-style templates, list local update
notes, run local diagnostics, and display redacted crash reports. They must
not:

- modify active `GameState`, saves, worlds, modules, prompt profiles, or
  content packs outside existing backend services;
- apply model text as a state patch;
- run real provider calls as part of startup, health checks, crash viewing,
  workspace selection, config summary, update notes, or packaging checks;
- bypass validation gates, migration dry-runs, package validation, or quality
  gates.

If a future desktop feature offers model-assisted troubleshooting, it must be
authoring/debug-only, opt-in, routed through `LLMProvider`, redacted by
default, and prohibited from directly changing state.

### Provider Secrets And Frontend Boundary

Provider secrets remain backend-only:

- `LLM_API_KEY` and provider credentials are read from local backend
  environment / ignored `.env` only.
- The frontend receives only safe variables such as `VITE_API_BASE_URL`.
- Launcher scripts must not inject API keys into `VITE_*` variables.
- Safe config summaries may expose `api_key_configured=true/false`, but never
  the key value.
- Crash reports, logs, update notes, health checks, usage summaries, prompt
  reports, backups, exports, and desktop packages must not contain API key
  values, raw env, raw prompts, hidden facts, or raw provider credentials.

`LOCAL_LLM_BASE_URL` is configuration for backend provider construction only.
It should not contain embedded credentials. Provider construction remains
behind `create_llm_provider(settings)` / `LLMProvider`; desktop tools do not
instantiate concrete providers.
