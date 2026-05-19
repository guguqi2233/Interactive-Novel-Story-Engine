# v1.5 Release Notes: Local Model & Prompt Lab

## 1. Version Name

v1.5: Local Model & Prompt Lab

## 2. Version Goal

v1.5 adds a local Model & Prompt Lab for comparing and debugging providers,
models, Prompt Profiles, context builders, structured output reliability,
latency, cost estimates, token budgets, compatibility, and prompt regression
behavior.

This remains a local self-use engine and studio. The world engine is still the
source of truth. LLMs are still language-layer tools, not world judges. Prompt
Lab can produce diagnostics, benchmarks, redacted reports, diffs, compatibility
summaries, and experiment packages, but it cannot modify active `GameState`,
active saves, active sessions, or active content packs.

## 3. New Features

- Model & Prompt Lab Boundary Contract.
- Provider Capability Registry.
- Provider Benchmark Harness.
- Prompt Profile A/B Test.
- Narrator Style Lab.
- NPC Voice Style Lab.
- Structured Output Reliability Test.
- Cost / Latency Tracker.
- Context Builder Inspector.
- Prompt Diff Tool.
- Model Compatibility Matrix.
- Provider Routing Rule Editor.
- Prompt Regression Suite.
- Local Model Diagnostics.
- Token Budget Manager Pro.
- Model Usage Dashboard.
- Prompt Experiment Package export/import.
- Prompt Lab Frontend.
- Prompt Lab CLI.
- v1.5 integration regression tests.

## 4. Behavior Changes

- Prompt Lab outputs are read-only with respect to runtime state.
- Prompt Profiles and RP Prompt Profiles remain expression/style configuration;
  they cannot enable hidden facts, NPC secrets, raw `GameState`, raw
  `state_deltas`, debug memory, or state modification.
- Real external provider benchmarks are disabled by default and require
  explicit opt-in.
- Local model diagnostics default to fake/non-real checks unless explicitly
  allowed.
- Prompt/context/report output defaults to redacted safe summaries.
- Usage tracking records safe metadata and estimates only.
- Token budget trimming protects safety, boundary, and policy sections.

## 5. API Changes

New Prompt Lab API surfaces include:

- `GET /prompt-lab/provider-capabilities`
- `POST /prompt-lab/providers/benchmark`
- `GET /prompt-lab/providers/benchmark/{run_id}`
- `POST /prompt-lab/prompt-profiles/ab-test`
- `GET /prompt-lab/prompt-profiles/ab-test/{run_id}`
- `POST /prompt-lab/narrator-style/run`
- `GET /prompt-lab/narrator-style/{run_id}`
- `POST /prompt-lab/npc-voice-style/run`
- `GET /prompt-lab/npc-voice-style/{run_id}`
- `POST /prompt-lab/structured-output/run`
- `POST /prompt-lab/context/inspect`
- `POST /prompt-lab/prompt-diff/review`
- `GET /prompt-lab/model-compatibility`
- `POST /prompt-lab/model-compatibility/recompute`
- `GET /prompt-lab/provider-routing`
- `POST /prompt-lab/provider-routing/validate`
- `POST /prompt-lab/provider-routing/preview`
- `POST /prompt-lab/provider-routing/save`
- `POST /prompt-lab/regression/run`
- `POST /prompt-lab/local-model/diagnose`
- `GET /prompt-lab/token-budget/profiles`
- `POST /prompt-lab/token-budget/estimate`
- `GET /prompt-lab/usage/recent`
- `GET /prompt-lab/usage/summary`
- `GET /prompt-lab/usage/by-use-case`
- `POST /prompt-lab/experiment-packages/export`
- `POST /prompt-lab/experiment-packages/import-dry-run`
- `POST /prompt-lab/experiment-packages/import-apply`

API responses for normal Prompt Lab reports are designed around safe summaries,
flags, counts, metrics, redacted snippets, and validation findings. They must
not return API key values, raw env, raw prompts, hidden facts, raw `GameState`,
or raw `state_deltas`.

## 6. Frontend Changes

- Added a Prompt Lab page to the Studio UI.
- Added panels for provider capabilities, provider benchmark, Prompt A/B,
  narrator style, NPC voice style, structured-output reliability, context
  inspection, prompt diff, model compatibility, provider routing, prompt
  regression, local diagnostics, token budgets, and model usage.
- Added visible local warnings and explicit controls around real-provider
  behavior.
- Added redacted context display for Context Inspector.
- Added usage dashboard summaries for provider/use-case distribution, estimated
  tokens, estimated cost, latency, error rate, and recent failures.

Frontend build passes. The current build emits a non-blocking Vite chunk-size
warning for the main JavaScript bundle.

The frontend does not display API key values and should not be used as a
provider secret editor.

## 7. Provider / Model Changes

- Provider Capability Registry records declared provider/model metadata such as
  JSON support, streaming support, context-window hints, local-only status,
  recommended use cases, and cost hints.
- Provider construction remains centralized through `LLMProvider`,
  `create_llm_provider`, and the approved `ProviderRouter`.
- Provider Routing Rule Editor supports local use-case routing preferences and
  fallbacks without storing API keys or expanding model authority.
- Model Compatibility Matrix summarizes declared capabilities and local test
  signals. It is advisory, not an absolute model ranking, and it does not
  automatically choose or switch production models.

## 8. Prompt Lab Changes

- Prompt A/B compares profile variants against safe cases.
- Narrator Style Lab evaluates style parameters without changing
  `ActionResult` or active game state.
- NPC Voice Style Lab evaluates voice consistency without adding NPC knowledge.
- Prompt Diff highlights section changes, token deltas, hidden access policy
  changes, and state modification policy changes.
- Prompt Regression Suite checks prompt/provider/profile changes against
  deterministic safety and schema cases.
- Prompt Experiment Package can export/import local experiment metadata without
  API keys, hidden facts, raw env, raw `GameState`, raw state deltas, sensitive
  prompt snapshots, executables, or path traversal.

Prompt Profile remains style-only. It cannot grant hidden fact access, state
modification authority, or world-judge powers.

## 9. Usage / Cost / Benchmark Changes

- Cost / Latency Tracker records safe local metadata: provider, model, use
  case, start time, duration, estimated token counts, estimated cost,
  success/failure, and error type.
- Cost estimates are approximations for local diagnostics. They are not bills
  and should not be treated as exact provider accounting.
- Provider Benchmark Harness defaults to fake/mock/local_stub behavior.
- Real provider benchmark requires explicit `allow_real_provider=true`.
- Local Model Diagnostics defaults to fake/non-real checks unless explicitly
  configured for real local HTTP diagnostics.
- Structured Output Reliability Test measures JSON/schema behavior without
  writing active state.

## 10. Testing / Regression Changes

Acceptance verification:

- `python -m pytest`: passed, `1341 passed in 95.58s`.
- `cd frontend && npm.cmd run build`: passed.

v1.5 test coverage includes:

- Model & Prompt Lab boundary checks.
- Provider capability safe summaries.
- Provider benchmark fake/default behavior and real-provider blocking.
- Prompt Profile hidden-fact and state-modification denial.
- Prompt A/B, Narrator Style Lab, NPC Voice Style Lab, and Prompt Regression.
- Structured output reliability and schema failure reporting.
- Context Inspector redaction.
- Prompt Diff safety policy blockers.
- Token Budget Manager safety-section protection.
- Usage tracking without raw prompt or API key persistence.
- Provider Routing validation and secret rejection.
- Local Model Diagnostics fake-mode behavior.
- Prompt Experiment Package secret rejection, dry-run behavior, and no
  auto-enable behavior.
- Prompt Lab CLI default non-real provider behavior.
- v1.5 integration regression across Prompt Lab boundaries.

## 11. Known Limitations

- v1.5 is not an online model marketplace, hosted benchmark platform, cloud
  sync feature, or shared evaluation service.
- Prompt Lab cannot modify active `GameState`.
- Model Compatibility Matrix is not an absolute model ranking and does not
  automatically select the best model.
- Benchmark, Prompt A/B, style lab, compatibility, and regression results are
  local diagnostic signals, not universal quality judgments.
- Cost / Latency Tracker uses estimates and local metadata. It is not a billing
  system.
- Token estimates are approximate.
- Context Inspector defaults to redacted output. Explicit debug raw inspection
  remains local/debug-only and still returns redacted text.
- Real provider benchmark and real local diagnostics require explicit opt-in.
  Users remain responsible for avoiding sensitive custom real-provider cases.
- Token Budget Manager does not remove safety/boundary instructions as a way to
  fit content.
- Frontend build emits a non-blocking Vite chunk-size warning.

## 12. Upgrade Notes from v1.4

- v1.4 Content Production Pipeline behavior remains unchanged: generators
  produce drafts/candidates/packages, not active runtime state.
- v1.5 adds Prompt Lab APIs, frontend panels, CLI commands, and provider/model
  diagnostics as local studio tools.
- Review `.env.example` for provider, local model, usage tracking, debug/eval,
  and API base URL settings.
- Keep provider credentials in backend environment/secret configuration. Do not
  put API keys in `VITE_*` frontend variables.
- Existing Prompt Profiles can be compared in Prompt Lab, but hidden-fact or
  state-modification policy relaxation is rejected.
- Prompt Experiment Packages are safe metadata packages. They do not contain
  provider credentials and do not automatically enable imported profiles.

## 13. Recommended v1.6 Directions

- Campaign Director and deterministic pacing tools.
- Player-facing journal, clue board, rumor board, and faction dossier.
- Advanced mystery runtime support with evidence chains and suspect behavior.
- Stronger semantic redaction for prompt/context/debug reports.
- Save/content migration assistant for generated worlds and prompt profiles.
- Local bundle/release wizard for worlds, packages, prompt profiles, and lab
  reports.
- Optional draft-only LLM authoring assistants with provenance and Prompt Lab
  regression gates.
- Content analytics for dead content, hidden exposure, prompt regressions, NPC
  simulation coverage, and quest completion health.

## Release Boundary Summary

v1.5 is accepted as a local diagnostic studio release.

The core boundaries remain:

- This is a local self-use engine and studio.
- LLM is not the world judge.
- Prompt Lab cannot modify active `GameState`.
- Prompt Profile cannot expand LLM permissions.
- Real Provider benchmark must be explicitly enabled.
- Cost / Latency Tracker is an estimate, not a bill.
- Context Inspector defaults to redacted output.
- Prompt Experiment Package does not include API keys.
- Model Compatibility Matrix is advisory, not an automatic production switch.
- Token Budget Manager does not trim safety boundaries.
