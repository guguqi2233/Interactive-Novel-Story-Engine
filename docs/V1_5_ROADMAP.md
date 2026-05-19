# v1.5 Roadmap: Local Model & Prompt Lab

## Version Goal

v1.5 builds a local Model & Prompt Lab for comparing, debugging, and
regression-testing providers, models, prompt profiles, context builders,
structured output reliability, token budgets, latency, cost, and compatibility.

The lab is a local diagnostic and evaluation surface. It may create benchmark
results, prompt diffs, redacted context reports, compatibility summaries, and
experiment packages. It must not become a runtime authority.

The core rule is unchanged:

LLM output can support language-facing parsing, narration, summarization, RP
expression, and draft-only authoring experiments. It cannot directly modify
`GameState`, bypass schema validation, widen Prompt Profile permissions, or
act as world judge.

## Not In v1.5

- LLM world adjudication.
- LLM direct `GameState` mutation.
- Prompt Profile expansion of LLM permissions.
- Provider calls that bypass `LLMProvider` or the approved `ProviderRouter`.
- Default tests that call real external APIs.
- Logging full sensitive prompts.
- Returning API keys to frontend, debug APIs, reports, logs, or packages.
- Writing API keys into Prompt Profiles, experiment packages, or exports.
- Model compatibility reports that expose hidden facts.
- Context Inspector showing hidden/debug context in normal UI.
- Automatic replacement of production provider configuration.
- Online model downloads, marketplaces, cloud sync, hosted comparisons, or
  remote sharing.
- Treating benchmark scores as absolute model quality judgments.

## Frozen Constraints

- LLM output cannot directly modify `GameState`.
- LLM JSON output must pass schema validation before any caller uses it.
- All provider calls go through `LLMProvider` or an approved `ProviderRouter`
  wrapper that delegates to `LLMProvider`.
- Prompt Lab outputs evaluation results only; it does not mutate active
  `GameState`, active saves, active sessions, or content packs.
- Prompt Profiles may change expression style, variants, temperature, token
  hints, and routing preferences only. They cannot change fact permissions.
- Context Inspector must classify every payload as `normal`, `debug`, or
  `hidden`, and normal views must be redacted.
- Benchmark defaults use `mock`, `fake`, or `local_stub`.
- Real provider benchmarks require explicit opt-in and clear local warning.
- API keys cannot enter frontend payloads, logs, prompt experiment packages,
  exported packages, prompt profiles, benchmark reports, or snapshots.
- Cost and latency tracking stores metadata and safe summaries, not sensitive
  prompt text.
- Hidden facts, NPC secrets, hidden/debug memory, raw `GameState`, and raw
  `state_deltas` do not enter normal reports.
- Provider routing cannot grant world-judge authority or bypass schema,
  visibility, memory, RP, authoring, or content-production boundaries.

## Recommended Development Order

1. Model & Prompt Lab Boundary Contract.
2. Provider Capability Registry.
3. Cost / Latency Tracker.
4. Local Model Diagnostics.
5. Provider Benchmark Harness.
6. Structured Output Reliability Test.
7. Token Budget Manager Pro.
8. Context Builder Inspector.
9. Prompt Diff Tool.
10. Prompt Profile A/B Test.
11. Narrator Style Lab.
12. NPC Voice Style Lab.
13. Model Compatibility Matrix.
14. Provider Routing Rule Editor.
15. Prompt Regression Suite.
16. Prompt Experiment Package.
17. Model Usage Dashboard.
18. Prompt Lab Frontend.
19. Prompt Lab CLI.

The first phase should land the shared boundary, provider capability metadata,
and safe metrics collection before any benchmark UI. This keeps later lab
features from accidentally logging sensitive prompts or treating model output
as authoritative state.

## Module Roadmap

### 1. Model & Prompt Lab Boundary Contract

Goal: Define the v1.5 boundary for provider tests, prompt experiments, context
inspection, benchmark reports, routing rules, and active runtime state.

Data structures:

- `PromptLabPolicy`
- `PromptLabOperation`
- `PromptLabRun`
- `PromptLabReport`
- `PromptLabPrivacyClass`
- `PromptLabRedactionPolicy`
- `PromptLabDecision`

API changes:

- `GET /prompt-lab/boundary`
- `POST /prompt-lab/boundary/check`

Frontend changes:

- Add a local Prompt Lab boundary/status panel.
- Show whether a run uses fake/local/real providers, redacted context, and
  debug-only fields.

Tests:

- Lab runs do not modify active `GameState`.
- Real-provider operation is blocked without explicit opt-in.
- API keys and hidden facts are redacted from normal reports.
- Prompt profiles cannot widen hidden-fact or state-write policies.

Acceptance:

- Every v1.5 module references the boundary contract.
- Prompt Lab has no runtime authority.

Provider boundary impact: introduces an approved lab policy around provider
experiments without bypassing `LLMProvider`.

Prompt Profile safety impact: freezes style-only permissions.

Leak risk: high if prompt snapshots include hidden facts or API keys. Normal
reports must store redacted summaries only.

### 2. Provider Capability Registry

Goal: Track local capability metadata for supported providers and models.

Data structures:

- `ProviderCapability`
- `ModelCapability`
- `ProviderCapabilityRegistry`
- `ProviderFeatureFlag`
- `ProviderSchemaSupport`

API changes:

- `GET /prompt-lab/providers/capabilities`
- `POST /prompt-lab/providers/capabilities/refresh`

Frontend changes:

- Provider/model capability table with local-only status labels.

Tests:

- Registry loads `mock`, `local_stub`, `local_http`, and `openai` metadata.
- Unknown providers are rejected.
- API key presence is represented as boolean only.
- Registry does not instantiate real providers during normal load.

Acceptance:

- Lab can show provider capability metadata without making model calls.

Provider boundary impact: metadata only; provider construction remains through
factory/router.

Prompt Profile safety impact: profiles can reference capabilities but cannot
override permissions.

Leak risk: provider config summaries must not expose API keys or raw URLs in
normal views.

### 3. Provider Benchmark Harness

Goal: Run deterministic benchmark scenarios against fake/local providers by
default and real providers only with explicit opt-in.

Data structures:

- `ProviderBenchmarkRequest`
- `ProviderBenchmarkCase`
- `ProviderBenchmarkResult`
- `ProviderBenchmarkRun`
- `ProviderBenchmarkSafety`

API changes:

- `POST /prompt-lab/benchmarks/run`
- `GET /prompt-lab/benchmarks/{run_id}`

Frontend changes:

- Benchmark runner with provider selector, explicit real-provider toggle, and
  safe result summaries.

Tests:

- Default benchmark uses fake/local provider.
- Real provider is blocked without explicit opt-in.
- Benchmark output is schema-validated.
- Prompt text and API keys are not stored in normal results.

Acceptance:

- Users can compare provider behavior locally without leaking prompt data.

Provider boundary impact: benchmark calls go through `LLMProvider` or
`ProviderRouter`.

Prompt Profile safety impact: benchmarks can test profiles but not modify them.

Leak risk: prompt payloads and responses can contain hidden text; store hashes,
safe summaries, and redacted samples only.

### 4. Prompt Profile A/B Test

Goal: Compare two or more Prompt Profiles against the same safe scenario set.

Data structures:

- `PromptProfileABTestRequest`
- `PromptProfileVariant`
- `PromptProfileABResult`
- `PromptProfileComparisonMetric`

API changes:

- `POST /prompt-lab/prompt-profiles/ab-test`
- `GET /prompt-lab/prompt-profiles/ab-test/{run_id}`

Frontend changes:

- A/B comparison panel for profile variants, output summaries, schema pass
  rates, latency, and consistency findings.

Tests:

- Profiles cannot change hidden-fact or state-modification policy.
- A/B runs do not write active profile config unless explicitly exported as an
  experiment package.
- Hidden facts are not included in normal test cases.

Acceptance:

- A creator can compare style outcomes safely without altering runtime config.

Provider boundary impact: runs through lab harness/provider abstraction.

Prompt Profile safety impact: validates permission fields before every run.

Leak risk: variants may contain unsafe free text; reject or redact prompt
instructions that request hidden facts or state writes.

### 5. Narrator Style Lab

Goal: Compare narrator style settings against player-visible scenario outputs.

Data structures:

- `NarratorStyleLabRequest`
- `NarratorStyleCase`
- `NarratorStyleResult`
- `NarratorStyleMetric`

API changes:

- `POST /prompt-lab/narrator/style/run`
- `GET /prompt-lab/narrator/style/{run_id}`

Frontend changes:

- Narrator style preview panel with visible-state-only context and redacted
  output comparison.

Tests:

- Narrator receives only visible facts and narrator-safe memory.
- Hidden facts and raw `state_deltas` are absent from prompt context.
- Model output does not mutate `GameState`.

Acceptance:

- Style comparison works without weakening narrator visibility.

Provider boundary impact: uses existing narrator provider abstraction.

Prompt Profile safety impact: narrator profile changes remain expression-only.

Leak risk: high if cases use debug event data. Inputs must be built from
player-visible scenario fixtures.

### 6. NPC Voice Style Lab

Goal: Compare NPC voice and RP profile expression while preserving NPC
knowledge boundaries.

Data structures:

- `NPCVoiceStyleLabRequest`
- `NPCVoiceCase`
- `NPCVoiceStyleResult`
- `NPCVoiceSafetyFinding`

API changes:

- `POST /prompt-lab/npc-voice/run`
- `GET /prompt-lab/npc-voice/{run_id}`

Frontend changes:

- NPC voice lab with participant selection, profile variant comparison, and
  hidden/unknown-fact consistency flags.

Tests:

- NPC context contains only `npc_known_facts`.
- `private_self_summary` is excluded from normal prompt context.
- Hidden/debug memory does not enter normal output.

Acceptance:

- NPC voice can be tested without granting omniscience or state authority.

Provider boundary impact: routes through RP/dialogue provider interfaces.

Prompt Profile safety impact: RP prompt profile boundary fields stay fixed.

Leak risk: NPC secrets and private RP fields must be hidden/redacted in normal
reports.

### 7. Structured Output Reliability Test

Goal: Measure how reliably providers return schema-valid outputs for known
schemas.

Data structures:

- `StructuredOutputTestRequest`
- `StructuredOutputSchemaCase`
- `StructuredOutputResult`
- `StructuredOutputFailure`

API changes:

- `POST /prompt-lab/structured-output/run`
- `GET /prompt-lab/structured-output/{run_id}`

Frontend changes:

- Schema reliability panel with pass/fail, parse errors, validation errors,
  retry counts, and safe snippets.

Tests:

- Invalid model JSON is rejected.
- Schema validation failures do not mutate state.
- Results store error classes, not full sensitive prompt text.

Acceptance:

- Lab can report schema reliability per provider/profile.

Provider boundary impact: all calls use `generate_json` through abstraction.

Prompt Profile safety impact: profiles cannot override schema requirements.

Leak risk: failed responses may echo hidden prompts; store redacted excerpts.

### 8. Cost / Latency Tracker

Goal: Track local timing, token estimates, and optional provider cost metadata
without recording sensitive prompts.

Data structures:

- `ModelUsageSample`
- `CostLatencyReport`
- `TokenUsageEstimate`
- `ProviderCostProfile`

API changes:

- `GET /prompt-lab/usage`
- `POST /prompt-lab/usage/record`
- `POST /prompt-lab/usage/report`

Frontend changes:

- Usage charts for latency, token estimates, error rate, schema pass rate, and
  provider/profile grouping.

Tests:

- Samples omit API keys and prompt text.
- Token/cost estimates are deterministic for mock cases.
- Reports aggregate metadata only.

Acceptance:

- Users can compare cost/latency without storing prompts.

Provider boundary impact: tracker observes provider calls through wrapper
metadata only.

Prompt Profile safety impact: profile ids may be recorded; profile secret text
must not.

Leak risk: timing labels and tags can leak context names; sanitize labels and
forbid hidden ids in normal views.

### 9. Context Builder Inspector

Goal: Inspect how narrator, NPC, RP, memory, authoring, and production contexts
are assembled with explicit privacy classes.

Data structures:

- `ContextInspectionRequest`
- `ContextInspectionReport`
- `ContextSegment`
- `ContextPrivacyClass`
- `ContextRedactionFinding`

API changes:

- `POST /prompt-lab/context/inspect`
- `GET /prompt-lab/context/inspect/{run_id}`

Frontend changes:

- Context inspector with normal/debug/hidden tabs, redacted normal view, and
  exclusion reasons.

Tests:

- Normal view excludes hidden facts, NPC secrets, debug memory, raw state, and
  raw deltas.
- Debug view requires debug/local gate.
- Inspector never sends inspected context to a provider by itself.

Acceptance:

- Users can debug context construction without leaking hidden data to normal
  surfaces.

Provider boundary impact: inspector is read-only and does not call providers.

Prompt Profile safety impact: shows profile effects on style fields only.

Leak risk: very high. Normal/debug/hidden separation is mandatory.

### 10. Prompt Diff Tool

Goal: Compare two prompt/context builds or prompt profiles safely.

Data structures:

- `PromptDiffRequest`
- `PromptDiffReport`
- `PromptDiffHunk`
- `PromptDiffRisk`

API changes:

- `POST /prompt-lab/prompts/diff`

Frontend changes:

- Redacted prompt diff viewer with privacy risk badges.

Tests:

- Diff normal view redacts hidden text.
- API keys and raw env are not rendered.
- Diff does not call providers or mutate state.

Acceptance:

- Users can compare prompt changes without exposing secrets.

Provider boundary impact: none; no provider calls.

Prompt Profile safety impact: highlights profile permission changes and blocks
unsafe widening.

Leak risk: full prompt diffs are sensitive; normal view must use redacted hunks.

### 11. Model Compatibility Matrix

Goal: Summarize provider/model compatibility with JSON mode, schema reliability,
streaming support, tool-like restrictions, token capacity, and latency classes.

Data structures:

- `ModelCompatibilityMatrix`
- `ModelCompatibilityCell`
- `CompatibilityFinding`
- `CompatibilityProfile`

API changes:

- `GET /prompt-lab/models/compatibility`
- `POST /prompt-lab/models/compatibility/run`

Frontend changes:

- Matrix table with filters by provider, schema, profile, and local/real mode.

Tests:

- Matrix uses fake/local data by default.
- Hidden facts are absent from compatibility cases.
- Real provider mode requires explicit opt-in.

Acceptance:

- Users can compare model fit without leaking content.

Provider boundary impact: capability/benchmark data only, via provider
abstraction.

Prompt Profile safety impact: matrix can show profile compatibility but cannot
auto-switch runtime profile.

Leak risk: compatibility failure examples must be redacted.

### 12. Provider Routing Rule Editor

Goal: Let local users define safe provider routing preferences without
granting new model authority.

Data structures:

- `ProviderRoutingRule`
- `ProviderRoutingProfile`
- `ProviderRoutingDecision`
- `ProviderRoutingValidationReport`

API changes:

- `GET /prompt-lab/provider-routing`
- `POST /prompt-lab/provider-routing/preview`
- `POST /prompt-lab/provider-routing/validate`
- `POST /prompt-lab/provider-routing/save`

Frontend changes:

- Routing rule editor with dry-run preview and validation report.

Tests:

- Routing never bypasses `LLMProvider` / `ProviderRouter`.
- Rules cannot route hidden/debug prompts to normal/report surfaces.
- Save does not auto-replace production provider config unless explicit and
  validated.

Acceptance:

- Users can preview routing rules safely before applying config.

Provider boundary impact: introduces router policy while preserving provider
abstraction.

Prompt Profile safety impact: routing cannot alter prompt permissions.

Leak risk: routing rules may expose provider ids and local endpoints; redact
sensitive endpoint details in normal view.

### 13. Prompt Regression Suite

Goal: Regression-test prompts and providers against known safe fixtures.

Data structures:

- `PromptRegressionSuite`
- `PromptRegressionCase`
- `PromptRegressionResult`
- `PromptRegressionFailure`

API changes:

- `POST /prompt-lab/regression/run`
- `GET /prompt-lab/regression/{run_id}`

Frontend changes:

- Regression runner with pass/fail trends and privacy findings.

Tests:

- Tests use mock/fake/local_stub by default.
- Hidden fixtures are excluded or redacted.
- Failures do not write active state or active profiles.

Acceptance:

- Prompt changes can be regression-tested before use.

Provider boundary impact: provider calls go through harness/router.

Prompt Profile safety impact: catches profile permission regressions.

Leak risk: failing outputs may reveal hidden text; store safe failure summaries.

### 14. Local Model Diagnostics

Goal: Diagnose local provider configuration, endpoint availability, JSON mode,
timeouts, parse failures, and schema failures.

Data structures:

- `LocalModelDiagnosticRequest`
- `LocalModelDiagnosticReport`
- `ProviderConnectivityCheck`
- `ProviderDiagnosticFinding`

API changes:

- `POST /prompt-lab/local-model/diagnose`
- `GET /prompt-lab/local-model/diagnostics/{run_id}`

Frontend changes:

- Diagnostics panel with safe config status, connectivity result, and failure
  hints.

Tests:

- Missing local URL fails clearly.
- API keys are not returned.
- Diagnostics can run in offline fake mode.

Acceptance:

- Users can debug local provider setup without exposing secrets.

Provider boundary impact: diagnostic calls use provider abstraction or safe
connectivity adapters.

Prompt Profile safety impact: diagnostics do not modify profiles.

Leak risk: local endpoint URLs can be sensitive; normal view should show
redacted host hints where possible.

### 15. Token Budget Manager Pro

Goal: Estimate, compare, and enforce safe token budgets for narrator, RP,
memory, authoring, and production contexts.

Data structures:

- `TokenBudgetProfile`
- `TokenBudgetEstimate`
- `TokenBudgetPolicy`
- `TokenBudgetWarning`

API changes:

- `POST /prompt-lab/token-budget/estimate`
- `POST /prompt-lab/token-budget/validate`
- `GET /prompt-lab/token-budget/profiles`

Frontend changes:

- Token budget panel showing segment counts, risks, and suggested trimming
  policies.

Tests:

- Estimates do not include hidden text in normal output.
- Budget validation blocks raw `GameState` and raw deltas.
- Trimming suggestions do not remove required safety instructions.

Acceptance:

- Users can manage token budget without exposing prompt content.

Provider boundary impact: no provider calls required for estimates.

Prompt Profile safety impact: budget profiles cannot remove boundary fields.

Leak risk: segment names and excerpts may leak hidden context; normal view uses
counts and redacted labels.

### 16. Model Usage Dashboard

Goal: Visualize safe provider/model/profile usage over local lab and runtime
calls.

Data structures:

- `ModelUsageDashboardSummary`
- `ModelUsageTrend`
- `ProviderUsageBreakdown`
- `PromptProfileUsageBreakdown`

API changes:

- `GET /prompt-lab/usage/summary`
- `GET /prompt-lab/usage/trends`

Frontend changes:

- Dashboard for latency, estimated tokens, schema pass rate, error rate, and
  provider/profile distribution.

Tests:

- Dashboard hides prompts, API keys, raw env, hidden ids, and local sensitive
  paths.
- Disabled lab state is safe.

Acceptance:

- Users can inspect usage safely in the local studio.

Provider boundary impact: read-only metrics surface.

Prompt Profile safety impact: displays profile ids and safe names only.

Leak risk: trend labels and error messages must be sanitized.

### 17. Prompt Experiment Package

Goal: Export/import local prompt experiment packages without API keys or hidden
content.

Data structures:

- `PromptExperimentPackageManifest`
- `PromptExperimentCase`
- `PromptExperimentResultSummary`
- `PromptExperimentImportReport`

API changes:

- `POST /prompt-lab/experiments/export`
- `POST /prompt-lab/experiments/import-dry-run`
- `POST /prompt-lab/experiments/import-apply`

Frontend changes:

- Experiment package export/import panel with safe/debug profile options.

Tests:

- Safe export excludes API keys, hidden facts, raw prompts, and raw outputs.
- Import rejects path traversal and executables.
- Import dry-run writes nothing.

Acceptance:

- Users can share local-safe experiment metadata without secrets.

Provider boundary impact: packages contain metadata/results, not provider
credentials.

Prompt Profile safety impact: package profiles remain style-only and validated.

Leak risk: raw prompts and outputs are sensitive; safe packages include hashes,
ids, metrics, and redacted summaries only.

### 18. Prompt Lab Frontend

Goal: Provide a coherent local UI for all lab tools.

Data structures:

- Frontend DTOs mirroring lab schemas.
- `PromptLabViewState`
- `PromptLabSafetyBadge`

API changes:

- No new backend schema beyond consumed APIs.

Frontend changes:

- Add Prompt Lab navigation.
- Provider capabilities, benchmark runner, A/B test, style labs, context
  inspector, prompt diff, compatibility matrix, routing editor, diagnostics,
  token budget, usage dashboard, regression runner, and experiment packages.

Tests:

- Frontend build passes.
- Disabled lab/API state does not crash.
- API keys and hidden context are not displayed in normal UI.

Acceptance:

- Prompt Lab is usable as a local studio surface without mixing into player UI.

Provider boundary impact: frontend never calls provider APIs directly.

Prompt Profile safety impact: unsafe profile changes must show validation
errors.

Leak risk: normal UI must not render debug/hidden payload fields.

### 19. Prompt Lab CLI

Goal: Provide local command-line access for benchmark, diagnostics, regression,
diff, token budget, and experiment package workflows.

Data structures:

- `PromptLabCLIReport`
- `PromptLabCLIExitCode`
- `PromptLabCLIProfile`

API changes:

- No HTTP API required; CLI calls service layer.

Frontend changes:

- Optional README/dashboard command snippets.

Tests:

- CLI defaults to fake/local providers.
- Real provider requires explicit flag.
- JSON output redacts API keys and hidden text.
- Invalid input returns non-zero exit code.

Acceptance:

- Local users can run Prompt Lab checks from scripts safely.

Provider boundary impact: CLI uses service layer and provider abstraction.

Prompt Profile safety impact: CLI validates profile permission fields.

Leak risk: stdout can leak prompts; default output must be redacted.

## v1.5 Integration Test Requirements

1. Boundary:
   - Prompt Lab runs do not modify active `GameState`.
   - LLM output cannot bypass schema validation.
   - Prompt Profiles cannot widen hidden-fact or state-write permissions.

2. Provider:
   - All calls route through `LLMProvider` or `ProviderRouter`.
   - No business module directly instantiates concrete providers.
   - Real provider benchmarks require explicit opt-in.
   - Default tests use mock/fake/local_stub and do not call real APIs.

3. Privacy:
   - API keys do not enter frontend, logs, reports, exports, packages, or
     prompt profiles.
   - Hidden facts, NPC secrets, debug memory, raw `GameState`, and raw
     `state_deltas` do not enter normal lab reports.
   - Context Inspector separates normal/debug/hidden views.

4. Prompt/Profile:
   - Prompt Profile A/B tests are read-only unless exported as experiment data.
   - Narrator style lab uses visible facts only.
   - NPC voice lab uses NPC-known facts only.
   - Prompt diff normal view redacts hidden context.

5. Metrics:
   - Cost/latency/token tracking stores safe metadata only.
   - Usage dashboard hides prompt content and sensitive paths.
   - Compatibility matrix uses safe cases by default.

6. Packages/CLI:
   - Prompt experiment package safe export excludes API keys and hidden text.
   - Import dry-run writes nothing.
   - CLI defaults to redacted output and fake/local providers.

7. Frontend:
   - `cd frontend && npm.cmd run build` passes.
   - Disabled lab/API state is safe.
   - Player UI never shows Prompt Lab debug context.

## v1.5 Final Acceptance Standards

- `python -m pytest` passes.
- `cd frontend && npm.cmd run build` passes.
- `docs/PROMPT_LAB_BOUNDARY.md` exists.
- `docs/V1_5_ACCEPTANCE_REPORT.md` exists.
- `docs/V1_5_RELEASE_NOTES.md` exists.
- LLM boundary audit confirms lab/provider tooling cannot write `GameState`,
  bypass schema validation, or call real providers by default.
- Privacy audit confirms prompts, context, hidden facts, NPC secrets, debug
  memory, API keys, raw env, raw state, and raw deltas are redacted from normal
  reports and packages.
- Security audit confirms no API keys in frontend/logs/exports/packages and no
  provider bypass.
- Prompt Profile safety tests confirm profiles cannot expand permissions.
- No high-risk release blocker remains.

## v1.6 Candidate Directions

- Campaign Director and pacing tools for deterministic chapter/milestone
  planning.
- Player-facing journal, clue board, rumor board, and faction dossier.
- Advanced mystery runtime support with evidence chains and suspect behavior.
- Stronger semantic redaction for prompts, hidden text, and debug reports.
- Save/content migration assistant for generated worlds and prompt profiles.
- Local bundle/release wizard for worlds, packages, prompt profiles, and lab
  reports.
- Optional draft-only LLM authoring assistants with provenance and lab
  regression gates.
- Content analytics for dead content, hidden exposure, prompt regressions, NPC
  simulation coverage, and quest completion health.
