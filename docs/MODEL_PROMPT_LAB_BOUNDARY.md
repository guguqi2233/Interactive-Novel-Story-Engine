# Model & Prompt Lab Boundary Contract

## Purpose

v1.5 introduces a local Model & Prompt Lab for comparing providers, models,
Prompt Profiles, structured-output behavior, context builder output, token
budgets, latency, and prompt experiments.

The lab is diagnostic and evaluative. It is not a world judge, not a runtime
state writer, and not a shortcut around provider, prompt, visibility, RP,
authoring, or content-production boundaries.

Core rule:

LLM output may support language-facing parsing, narration, summarization,
roleplay expression, and draft-only experiments after schema validation. It
must not directly modify `GameState`, widen fact visibility, bypass
`LLMProvider`, or become authoritative world state.

## Boundary Concepts

### provider_profile

Safe metadata describing a provider/model candidate for lab use. It may include
provider id, provider type, model id, JSON-mode support, streaming support,
local/real-provider classification, and whether a key is configured as a
boolean.

It must not include API key values, raw environment values, sensitive local
paths, or full unredacted endpoint secrets in normal/front-end summaries.

### model_capability

Local capability metadata for a model, such as schema support, JSON-mode
support, context-window hints, streaming support, and compatibility notes.
Capability data is descriptive only; it does not grant the model new authority.

### prompt_profile

Existing `PromptProfile` / `RPPromptProfile` data used to tune expression,
prompt variants, temperature, token hints, and RP style.

Prompt Profiles are style/configuration only. They cannot enable hidden facts,
NPC secrets, raw `GameState`, raw `state_deltas`, debug memory, or state-write
permissions.

### prompt_experiment

A local experiment comparing prompt profiles, providers, context snapshots, or
structured-output cases. Experiments may produce metrics and redacted reports.
They do not mutate active `GameState`, active saves, active sessions, or
content packs.

### benchmark_run

A local benchmark execution over safe eval cases. Benchmarks default to
`mock`, `fake`, or `local_stub` providers. Real external provider benchmarks
must require explicit opt-in and must still route through `LLMProvider` or an
approved provider router.

### context_snapshot

A captured view of context builder output. Every segment must be classified as
`normal`, `debug`, or `hidden`. Normal views must redact hidden/debug content
and show only safe summaries or ids.

### redacted_prompt

A prompt or prompt fragment after credentials, hidden/debug content, raw
state, raw deltas, and other sensitive material have been removed or replaced
with safe markers. Redacted prompts can be used in reports; full sensitive
prompts should not be logged or exported by default.

### debug_only_prompt_data

Prompt/context details that may help local debugging but are not safe for
normal UI, player UI, narrator prompts, exports, packages, or logs. Debug-only
data must remain behind local/debug gates and must be clearly labeled.

### safe_eval_case

A deterministic test case suitable for lab runs. It may include player-visible
facts, safe action result summaries, schema targets, and prompt profile ids. It
must not include API keys, hidden fact text, NPC secrets, debug memory, raw
`GameState`, or raw `state_deltas` in normal payloads.

## Allowed

Model & Prompt Lab may:

- Compare model outputs for safe eval cases.
- Measure structured-output reliability and schema validation failures.
- Track latency, token estimates, and optional cost metadata.
- Compare Prompt Profiles as expression/style variants.
- Inspect context builder output with normal/debug/hidden separation.
- Generate provider/model compatibility matrix reports.
- Produce prompt diffs, benchmark reports, diagnostics, and experiment package
  summaries using redacted payloads.

## Forbidden

Model & Prompt Lab must not:

- Let LLM output directly modify `GameState`.
- Treat benchmark output as authoritative world facts.
- Let Prompt Profiles enable hidden facts or state modification.
- Call real external provider APIs by default.
- Record API keys, raw env, or provider credentials.
- Record full sensitive prompt text in normal reports, logs, or packages.
- Send debug context to ordinary UI, player UI, narrator prompts, or normal
  reports.
- Instantiate concrete providers directly from business/lab modules instead of
  using `LLMProvider` / `create_llm_provider` or an approved provider router.
- Bypass Pydantic schema validation for structured output.
- Auto-replace production provider settings based on benchmark results.

## Safe Flow

1. Build or load safe eval cases.
2. Validate Prompt Profiles and provider profiles.
3. Build context snapshots with explicit privacy classes.
4. Redact prompt/context data before normal reporting.
5. Run benchmarks only through `LLMProvider` / provider router.
6. Require explicit opt-in for real external providers.
7. Validate structured outputs with schemas.
8. Store metrics, safe summaries, hashes, and redacted snippets only.
9. Keep lab results separate from active runtime state.

## Prompt Profile Rules

Prompt Profiles may alter:

- narrator style
- parser/narrator/RP prompt variants
- temperature overrides
- response-length and tone preferences
- RP expression style

Prompt Profiles may not alter:

- visible facts
- NPC knowledge
- hidden fact policy
- `StateDelta` authority
- EventLog authority
- schema validation requirements
- provider factory path

`RPPromptProfile.hidden_fact_policy` and
`RPPromptProfile.state_modification_policy` remain fixed to `deny`.

## Context Inspection Rules

Context inspection is read-only and does not call providers by itself.

Normal view may show:

- segment labels
- privacy class labels
- safe summaries
- redacted prompt fragments
- counts and ids when safe

Normal view must not show:

- hidden fact text
- NPC secrets
- hidden/debug memory text
- raw `GameState`
- raw `state_deltas`
- API keys or raw env
- full sensitive prompt text

Debug view may contain more detail only in local/debug-only surfaces and must
not be reused as player, narrator, package, or normal report content.

## Provider Rules

Provider construction remains centralized:

- `backend/app/llm/provider_factory.py`
- `create_llm_provider(settings)`

Future provider routing must delegate to `LLMProvider`; it cannot grant model
outputs world-judge authority.

Default lab benchmarks must use fake/mock/local providers. Real external
provider benchmarks require explicit opt-in and must not store credentials or
full sensitive prompts.

## Implementation Hook

The initial policy module is:

- `backend/app/llm/model_prompt_lab_policy.py`

It defines:

- `ProviderProfile`
- `ModelCapability`
- `PromptExperiment`
- `BenchmarkRun`
- `ContextSnapshot`
- `ContextSegment`
- `RedactedPrompt`
- `DebugOnlyPromptData`
- `SafeEvalCase`
- `ModelPromptLabPolicy`

The module is read-only and does not call an LLM.

## Test Requirements

v1.5.1 boundary tests must verify:

- Prompt Profiles cannot enable hidden facts.
- Context snapshots default to redacted normal views.
- Benchmark defaults do not call real external APIs.
- Provider config summaries do not expose API keys or raw provider config to
  frontend/normal views.
