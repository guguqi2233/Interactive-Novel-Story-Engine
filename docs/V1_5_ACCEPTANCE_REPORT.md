# v1.5 Acceptance Report: Local Model & Prompt Lab

## Verdict

Accepted.

v1.5 is accepted as the Local Model & Prompt Lab release. The implementation
adds a local diagnostic studio for provider/model capability inspection,
provider benchmarks, prompt profile experiments, style labs, structured-output
reliability checks, context inspection, prompt diffing, compatibility summaries,
provider routing rules, token budget management, usage summaries, prompt
experiment packages, frontend Prompt Lab panels, Prompt Lab CLI commands, and
v1.5 integration regression tests.

No high-risk v1.5 acceptance blocker was found.

## Verification Date

2026-05-20

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Verification results:

- `python -m pytest`: passed, `1341 passed in 95.58s`.
- `cd frontend && npm.cmd run build`: passed, `vite build` completed.
- Frontend build note: Vite reported a non-blocking chunk-size warning for the
  main JavaScript bundle. This does not block v1.5 acceptance.

## Scope Accepted

Accepted v1.5 scope:

1. Model & Prompt Lab Boundary Contract.
2. Provider Capability Registry.
3. Provider Benchmark Harness.
4. Prompt Profile A/B Test.
5. Narrator Style Lab.
6. NPC Voice Style Lab.
7. Structured Output Reliability Test.
8. Cost / Latency Tracker.
9. Context Builder Inspector.
10. Prompt Diff Tool.
11. Model Compatibility Matrix.
12. Provider Routing Rule Editor.
13. Prompt Regression Suite.
14. Local Model Diagnostics.
15. Token Budget Manager Pro.
16. Model Usage Dashboard.
17. Prompt Experiment Package.
18. Prompt Lab Frontend.
19. Prompt Lab CLI.
20. v1.5 integration regression tests.

Documents reviewed:

- `AGENTS.md`
- `docs/SPEC.md`
- `docs/WORLD_ENGINE.md`
- `docs/LLM_PROTOCOL.md`
- `docs/MODEL_PROMPT_LAB_BOUNDARY.md`
- `docs/V1_0_ACCEPTANCE_REPORT.md`
- `docs/V1_1_ACCEPTANCE_REPORT.md`
- `docs/V1_2_ACCEPTANCE_REPORT.md`
- `docs/V1_3_ACCEPTANCE_REPORT.md`
- `docs/V1_4_ACCEPTANCE_REPORT.md`
- `docs/V1_5_ROADMAP.md`
- Current backend and frontend code.

## Boundary Review

The v1.5 Model & Prompt Lab boundary is accepted.

- Prompt Lab is a local diagnostic and evaluation surface. It produces reports,
  matrices, summaries, benchmarks, diffs, diagnostics, redacted context
  snapshots, and experiment packages; it does not modify active `GameState`,
  active saves, active sessions, or active content packs.
- LLM output remains language-layer output. It cannot directly modify
  `GameState`, bypass schema validation, widen visibility, or become the world
  judge.
- The world engine remains the source of truth. Runtime state changes continue
  to be governed by engine rules, `StateDelta`, and event logging.
- Prompt Profiles and RP Prompt Profiles remain style/configuration surfaces.
  They cannot enable hidden facts, NPC secrets, raw `GameState`, raw
  `state_deltas`, debug memory, or state modification.
- Provider calls in v1.5 lab modules go through `LLMProvider`,
  `create_llm_provider`, fake providers, or the approved `ProviderRouter`
  abstraction. Concrete provider construction remains centralized in provider
  implementation/factory code.
- Provider Capability Registry is metadata-only and does not call real
  providers during normal capability listing.
- Provider Benchmark defaults to fake/mock/local behavior. Real external
  provider benchmark requires explicit `allow_real_provider=true`.
- Local Model Diagnostics defaults to fake/non-real checks. Real local HTTP
  diagnostics require explicit `allow_real_local_check=true`.
- Prompt A/B validates profile boundaries and cannot change hidden-fact or
  state-modification policy.
- Narrator Style Lab evaluates style output without changing `ActionResult` or
  active state.
- NPC Voice Style Lab evaluates voice consistency without adding NPC knowledge.
- Structured Output Reliability validates schema behavior and records failures
  as reports; it does not write `GameState`.
- Context Builder Inspector is read-only. Hidden facts and debug content are
  redacted from normal snapshots; raw prompt inspection is disabled by default
  and redacted when explicitly enabled.
- Prompt Diff flags hidden-fact policy or state-modification policy relaxation
  as blockers and does not render hidden text.
- Token Budget Manager protects safety, boundary, and policy sections; it does
  not trim safety boundaries to make content fit.
- Cost / Latency Tracker records safe metadata and estimates only. It does not
  persist raw prompts, API keys, hidden facts, raw `GameState`, or raw outputs.
- Model Compatibility Matrix is advisory and does not automatically switch
  production provider/model configuration.
- Provider Routing Rule Editor validates provider/model ids and routing
  constraints without storing API keys or expanding model authority.
- Prompt Regression Suite uses deterministic checks; pass/fail is not delegated
  to the LLM.
- Prompt Experiment Package export/import rejects API keys, raw env, hidden
  facts, raw `GameState`, raw state deltas, sensitive prompt snapshots,
  executables, and path traversal. Import does not auto-enable profiles.
- Prompt Lab frontend presents safe summaries, counts, booleans, warnings, and
  redacted context. It does not render API key values or hidden fact text in
  normal UI.
- Prompt Lab CLI defaults to fake/local behavior and redacted output. Real
  provider usage requires explicit flags.

Security/privacy checks accepted:

- API key values do not enter frontend payloads or exported prompt experiment
  packages.
- Raw prompts do not enter normal reports.
- Hidden facts and NPC secrets do not enter ordinary Prompt Lab reports.
- Tests use fake/mock/local_stub providers and do not call real external APIs
  by default.
- Structured output failures are reported clearly through errors, blockers, or
  validation failure records rather than silently producing authoritative data.

## Known Limitations

- v1.5 is not an online model marketplace, hosted benchmark platform, cloud
  sync feature, shared evaluation service, or automatic model-selection system.
- Prompt Lab cannot modify active `GameState`; it is intentionally limited to
  local diagnostics and evaluation.
- Model Compatibility Matrix is not an absolute model ranking and does not
  automatically switch production models.
- Benchmark, Prompt A/B, style lab, compatibility, and regression results are
  local diagnostic signals, not universal quality judgments.
- Cost / Latency Tracker uses estimates and local metadata. It is not a billing
  system and should not be treated as exact provider accounting.
- Token estimates are approximate.
- Context Inspector defaults to redacted output. Explicit debug raw inspection
  remains local/debug-only and still returns redacted text.
- Real provider benchmark and real local diagnostics are intentionally
  available only through explicit opt-in. Users must avoid putting sensitive
  world content into custom real-provider cases.
- Some tests intentionally include fake `sk-...` and hidden-text sentinel
  strings to verify redaction. These are not real credentials.
- Frontend build emits a non-blocking Vite chunk-size warning. Future UI work
  can consider code splitting.

## Acceptance Risks

No high-risk v1.5 acceptance blocker remains.

Non-blocking risks to preserve in future work:

1. Real provider opt-in paths can send prompts off-machine if explicitly
   enabled. Keep UI/CLI warning friction and redaction tests.
2. Context Inspector debug raw mode is sensitive even when redacted. Keep it
   disabled by default and clearly separated from normal UI.
3. Usage tracking is safe in the current metadata form. If persistent storage
   is added later, tests must prove raw prompts, raw outputs, hidden facts, and
   secrets are never stored.
4. Broader debug/timeline surfaces outside Prompt Lab may expose raw state
   delta details for local debugging. They must remain isolated from player UI,
   narrator prompts, Prompt Lab normal reports, and exports.
5. Synthetic hidden leak fixtures must not be replaced with real hidden world
   facts in reusable benchmark/regression cases.

## Recommended v1.6 Priorities

1. Campaign Director and deterministic pacing tools.
2. Player-facing journal, clue board, rumor board, and faction dossier.
3. Advanced mystery runtime support with evidence chains and suspect behavior.
4. Stronger semantic redaction for prompt/context/debug reports.
5. Save/content migration assistant for generated worlds and prompt profiles.
6. Local bundle/release wizard for worlds, packages, prompt profiles, and lab
   reports.
7. Optional draft-only LLM authoring assistants with provenance and Prompt Lab
   regression gates.
8. Content analytics for dead content, hidden exposure, prompt regressions, NPC
   simulation coverage, and quest completion health.

## Final Status

v1.5 is accepted.

The Local Model & Prompt Lab is ready for release freeze, final pre-tag review,
commit, and tag creation. The release preserves the central project boundary:
LLMs are language-layer tools, the world engine remains the sole fact source,
Prompt Lab cannot modify active `GameState`, Provider calls remain within the
factory/router abstraction, and normal reports/packages must not expose API
keys, raw prompts, hidden facts, or debug-only context.
