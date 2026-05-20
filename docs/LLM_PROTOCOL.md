# LLM Protocol

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
directly modify `GameState` or decide gameplay outcomes.

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
