# v0.7 Acceptance Report

## Verdict

**Accepted for local v0.7 release with non-blocking cautions.**

v0.7 meets the planned "Polished Local Studio" scope: studio home, save migration UI, mod manager, narrative/performance dashboards, local model provider integration, desktop launcher hardening, scenario templates, quest graph authoring, playtesting dashboard, import/export, settings/privacy, and v0.7 regression coverage are present and verified.

The core authority model remains intact: the world engine is still the fact source, LLMs remain language-layer providers, and local studio tools do not become player-facing authority.

## Verification Date

2026-05-18

## Verification Commands

```powershell
python -m pytest
npm.cmd run build
python -m pytest backend/tests/test_v04_integration_regression.py::test_v04_memory_retrieval_is_safe_and_non_authoritative -vv
python -m pytest
```

Notes:

- First full `python -m pytest` run collected 502 tests and had 1 failure in `test_v04_memory_retrieval_is_safe_and_non_authoritative`.
- The failed test passed when rerun directly.
- A second full `python -m pytest` run passed: **502 passed in 17.31s**.
- Frontend build passed: `tsc -b && vite build`.
- PowerShell emitted a local profile execution-policy warning during commands. It did not affect test/build results.

## Scope Accepted

### 1. Studio Home Dashboard

Accepted.

- Studio status/config endpoints provide safe local summaries for backend status, worlds, recent saves, API feature flags, performance logging, provider status, validation summaries, and recent playtest status.
- Tests verify status/config summaries do not expose API keys or raw state.
- Frontend includes a studio-oriented navigation surface and safe empty/disabled states.

### 2. Save Migration UI

Accepted.

- Migration status, dry-run, apply, migration list, and history APIs are available from the save workflow.
- Dry-run does not write the database.
- Apply records migration history and uses the migration service/registry path.
- UI flow includes apply confirmation and avoids raw `GameState` display.

### 3. Mod Manager UI

Accepted.

- Mod listing, details, validation, dependency/conflict checks, engine/content schema compatibility, and load order are exposed through authoring-gated APIs.
- Mod packages remain content-only.
- Validation rejects executable paths and path traversal.
- Frontend shows mod status without executing code or exposing sensitive paths.

### 4. Narrative Quality Dashboard

Accepted.

- Narrative quality reports include run id, totals, categories, case results, and failure reasons.
- Evals are deterministic and do not call a real LLM or external judge.
- The v0.7 blocker found during review was fixed: hidden fixture text is no longer returned in failure reasons. Failure reasons use redacted markers, and API responses sanitize legacy reports.

### 5. Performance Dashboard

Accepted.

- Performance instrumentation supports local timing samples and summary views.
- Debug performance APIs are gated by `ENABLE_DEBUG_API`.
- Tests verify samples do not record API keys, prompt text, hidden fact text, raw `GameState`, or raw `state_deltas`.
- Frontend provides a performance view with safe empty/disabled behavior.

### 6. Local Model Provider Full Integration

Accepted.

- `local_stub` and `local_http` are selected through the provider factory.
- `LocalHTTPProvider` supports text and JSON generation behind `LLMProvider`.
- JSON output is schema-validated.
- Missing `LOCAL_LLM_BASE_URL` fails clearly.
- Tests use fake transports and do not call real local services.
- Local model output still cannot directly modify `GameState`.

### 7. Desktop Packaging Enhancement

Accepted as a prototype.

- `docs/DESKTOP_PACKAGING.md` and launcher scripts document/start the local studio workflow.
- Scripts avoid embedding API keys into the frontend.
- `.env`, database files, logs, `frontend/dist`, desktop build outputs, and release outputs are covered by ignore rules.
- This remains a local launcher/prototype, not a formal installer or public release package.

### 8. Scenario Template System

Accepted.

- Scenario template schema, listing, preview, render, and validation flow are present.
- Templates are data/YAML renderers, not script execution.
- Preview does not write disk or modify active `GameState`.
- Rendered content is validated before use.

### 9. Visual Quest Graph Editor

Accepted.

- `quests.yaml` can be parsed into graph data.
- Graph data can be previewed back into YAML.
- Invalid edges are caught by validation.
- Preview does not write disk or active saves.
- Save remains routed through authoring validation.

### 10. Save Migration UI / Mod Manager Integration Tests

Accepted.

- v0.7 integration tests cover migration status, dry-run/apply, migration history, mod listing, mod validation, dependencies/conflicts, and load order.
- Tests use temporary SQLite databases and do not call real LLM APIs.

### 11. Studio UX Polish Pass

Accepted.

- Frontend includes unified local-studio navigation areas and shared UX patterns for status, empty/error handling, local-only notices, and dangerous action confirmations.
- Debug/authoring/player surfaces remain visually and structurally separated.

### 12. Automated Playtesting Dashboard

Accepted.

- Playtest APIs are gated by `ENABLE_PLAYTEST_API` or debug mode.
- Playtests use deterministic mock/local providers and act through the game loop/test harness.
- Reports include turns, actions, errors, invariant violations, visibility leak summaries, save/load failures, and final state summaries.
- Reports are sanitized and do not expose hidden fact text in player UI.

### 13. Import / Export Workflow

Accepted.

- World, mod, and save archive export/import APIs are present behind authoring API gating.
- Zip slip/path traversal is rejected.
- Executable files, `.env`, secrets files, DB files, logs, and disallowed file types are rejected.
- Imported content is validated.
- Save bundle import checks migration status.

### 14. App Settings / Local Privacy Panel

Accepted.

- Config summary endpoint returns safe provider/API status and privacy notes.
- API keys, raw env, and full sensitive paths are not returned.
- Frontend settings/privacy view explains local saves, provider prompt boundary, authoring/debug local use, and content-only mod rules.
- Frontend cannot edit `.env` or sensitive backend config.

### 15. v0.7 Integration Tests

Accepted.

- Full backend suite passed on final run: **502 passed**.
- Frontend build passed.
- v0.7 integration regression tests are present for studio status, eval/performance safety, templates/quest graph, import/export, migration/mod UI integration, local provider, and privacy boundaries.

## Boundary Review

### LLM Boundary

Passed.

- v0.7 studio modules do not use LLM output for validation, migration, mod safety, graph visibility, import/export safety, playtesting decisions, performance status, scenario templates, or quest graph correctness.
- `local_http` remains behind `LLMProvider` and provider factory.
- Intent parsing, narration, memory summaries, and optional draft generation remain schema-validated language-layer uses.
- No LLM output is applied directly to `GameState`.

### StateDelta / Event Boundary

Passed with existing architecture caveat.

- Runtime world changes continue to flow through `StateDelta` and `apply_delta`.
- Player actions, system ticks, NPC planning ticks, and playtest agent inputs are represented through event-producing game-loop paths.
- Authoring/template/quest graph/import-export operations edit content files or archives, not active runtime `GameState`.
- Existing crime/social consequences may be recorded as separate system events rather than folded into the initiating player event; this is accepted as the current event model.

### Visibility / Privacy Boundary

Passed.

- Player API uses `visible_state`.
- Hidden facts, NPC secrets, hidden witnesses, hidden relationships, hidden/debug memory, debug graphs, raw debug events, and raw `state_deltas` are excluded from player/narrator surfaces.
- Debug, authoring, eval, playtest, and performance APIs remain local/gated tooling surfaces.
- Narrative eval hidden fixture text redaction was fixed before acceptance.

### Security / Packaging Boundary

Passed for local self-use release.

- Authoring/import/export APIs are gated.
- Import/export rejects zip slip and executable content.
- Mod system remains content-only and does not execute arbitrary code.
- Desktop packaging remains a prototype and does not embed `.env` or API keys.
- Frontend does not store API keys.

## Known Limitations

- Desktop packaging is still a prototype launcher workflow, not a signed installer or full desktop distribution.
- Save bundle export necessarily contains full save internals, including hidden state and events. It must remain a local authoring/archive workflow and should not be shown in player UI.
- Debug APIs intentionally expose internal events and `state_deltas` when enabled. They must remain local-only.
- Authoring UI intentionally exposes hidden content to the local creator; it must remain separated from player mode.
- Narrative evals are deterministic heuristic checks, not a human or LLM quality judge.
- Performance instrumentation records local timings only and is not an optimization system.
- Local HTTP provider support is configurable but not product-specific; compatibility with every local model server is not guaranteed.
- A first full pytest run showed one transient ordering/serialization-style failure in a v0.4 memory save/load comparison; the exact test passed when rerun directly and the subsequent full suite passed.
- PowerShell profile execution-policy warnings add noise to command output on this machine.

## Acceptance Risks

1. **Save export sensitivity**
   - Save archives can contain full hidden/internal state by design.
   - Risk is acceptable for local authoring/export, but UI and docs should keep it clearly labeled as sensitive local data.

2. **Debug defaults in local mode**
   - Debug features are useful for local development but would be risky if the backend were exposed beyond loopback.
   - Current launch docs/scripts should continue binding locally and warning users.

3. **Narrative quality eval brittleness**
   - Evals are rule-based and useful for regression, but cannot guarantee literary quality.
   - They should remain a guardrail, not a release-quality oracle.

4. **Possible nondeterministic serialization comparison**
   - The initial pytest failure suggests at least one test path may still compare unordered set-derived JSON too strictly.
   - This did not reproduce in the direct rerun or second full run, so it is not blocking v0.7, but it should be hardened.

5. **Frontend remains a local prototype**
   - The UI is broad and functional, but not a hardened production product.
   - v0.8 should continue polish, workflow affordances, and local safety clarity.

## Recommended v0.8 Priorities

1. Harden save/export UX with explicit sensitive archive warnings and safer download/upload flows.
2. Add deterministic serialization helpers for set/list fields used in save/load equality tests.
3. Add a dedicated `ENABLE_EVAL_API` gate separate from full debug mode.
4. Improve desktop packaging beyond launcher prototype, still without bundling secrets.
5. Expand frontend component-level tests for disabled API states and debug/player separation.
6. Clean corrupted/mojibake prompt/sample text in eval/provider fixtures.
7. Add stronger authoring diff previews for hidden-content risk and save migration impact.
8. Continue local model provider compatibility tests with fake transports only.

## Final Status

**v0.7 accepted for local self-use release.**

Final verification:

- Backend tests: **passed on final full run, 502 passed**.
- Frontend build: **passed**.
- Release blockers from the v0.7 code review were addressed before this acceptance report.
- Remaining risks are local-only operational cautions or v0.8 hardening candidates, not v0.7 release blockers.
