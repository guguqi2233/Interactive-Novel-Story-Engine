# v0.7 Roadmap

## Theme

Polished Local Studio

## Goal

v0.7 turns the v0.6 local studio from a capable toolset into a smoother long-term daily workspace. The release should make common studio work easier to start, inspect, migrate, evaluate, package, and recover from without changing the authority model.

The world engine remains the fact source. The LLM remains a bounded language layer for parsing, narration, summarization, local-provider-backed language output, and optional author-facing drafts. No v0.7 feature may let model output become trusted world state.

Core invariants:

- LLM does not directly modify `GameState`.
- All runtime state changes go through `StateDelta`.
- Player actions, system ticks, NPC planning ticks, and playtesting-agent game inputs are recorded as `Event`.
- Hidden facts do not enter `visible_state`.
- NPCs cannot know or act on unknown facts.
- Memory is not an authoritative fact source.
- Authoring/debug/perf APIs are local-only and gated.
- Mods are content-only and never execute arbitrary code.
- Save migration must remain dry-run capable and testable.
- Desktop packaging must never include API keys or a real `.env`.
- Local model providers must go through `LLMProvider`.
- Authoring UI must go through backend validation and must not edit active `GameState`.

## Explicitly Not In v0.7

v0.7 will not include:

- LLM world-judge behavior.
- LLM-generated canonical `StateDelta` application.
- Cloud sync, accounts, hosted auth, marketplace publishing, or multi-user collaboration.
- Arbitrary mod/plugin code execution.
- Full tactical/grid combat.
- Large-scale war simulation.
- Large-scale dynamic economy simulation.
- Online mod marketplace.
- Frontend direct filesystem access.
- Authoring UI edits to active session `GameState`.
- Local model output written directly into `GameState`.
- Performance shortcuts that bypass `StateDelta`, `EventLog`, schema validation, visibility filters, save migration checks, or content validation.

## Recommended Development Order

1. Studio Home Dashboard.
2. App Settings / Local Privacy Panel.
3. Save Migration UI.
4. Mod Manager UI.
5. Import / Export Workflow.
6. Narrative Quality Dashboard.
7. Performance Dashboard.
8. Automated Playtesting Dashboard.
9. Scenario Template System.
10. Visual Quest Graph Editor initial slice.
11. Local Model Provider full integration.
12. Desktop Packaging enhancement.
13. Studio UX polish pass.
14. v0.7 integration regression tests, audits, acceptance report, and release notes.

## Module 1: Studio Home Dashboard

### Goal

Provide a first screen for the local studio that summarizes worlds, recent saves, validation health, recent playtest runs, performance warnings, and common actions.

### Data Structures

- `StudioSummary`
  - `worlds: list[WorldSummary]`
  - `recent_saves: list[SaveSummary]`
  - `validation_status: list[WorldValidationSummary]`
  - `recent_playtests: list[PlaytestSummary]`
  - `performance_status: PerformanceHealthSummary | None`
  - `migration_warnings: list[MigrationWarning]`
- `WorldSummary`
  - `world_id: str`
  - `name: str`
  - `version: str | None`
  - `content_pack_version: str | None`
  - `last_validated_at: str | None`
  - `error_count: int`
  - `warning_count: int`

### API Changes

- Add local-only studio endpoint:
  - `GET /studio/summary`
- The endpoint must aggregate existing safe summaries rather than returning raw `GameState`, raw YAML content, debug events, API keys, or hidden data.

### Frontend Changes

- Add a Studio Home view.
- Include quick links to:
  - start or continue a game
  - open authoring
  - run validation
  - inspect saves
  - run migration dry-run
  - open playtesting dashboard
  - inspect performance
- Show safe warnings only; never show hidden facts or debug-only content in player-facing areas.

### Tests

- Studio summary returns expected sections.
- Missing optional subsystems degrade gracefully.
- Summary does not expose hidden facts, raw `state_deltas`, API keys, or raw `GameState`.
- Frontend build passes with empty and populated summary data.

### Acceptance

- A local user can understand project health from the first screen.
- The dashboard is a launcher and summary surface, not a new source of truth.

### Save Migration Impact

- Reads migration status summaries only.
- Does not apply migrations.

### Content Pack / Mod Version Impact

- Displays version and validation health.
- Does not change content or load order.

### LLM Boundary

- No LLM calls.

### Visibility Risk

- Main risk is accidentally mixing debug summaries into the home view.
- Mitigation: use explicit safe summary schemas and tests for hidden/debug absence.

## Module 2: Save Migration UI

### Goal

Expose v0.6 migration status, dry-run, apply, backup metadata, and failure reports in the local frontend.

### Data Structures

- `MigrationStatusView`
  - `save_id: str`
  - `current_schema_version: str`
  - `target_schema_version: str`
  - `needs_migration: bool`
  - `migration_path: list[str]`
  - `warnings: list[str]`
  - `errors: list[str]`
- `MigrationApplyResultView`
  - `save_id: str`
  - `backup_id: str | None`
  - `migration_history: list[dict[str, str]]`
  - `success: bool`

### API Changes

Reuse existing v0.6 endpoints:

- `GET /saves/{save_id}/migration-status`
- `POST /saves/{save_id}/migrate-dry-run`
- `POST /saves/{save_id}/migrate`
- `GET /migrations`

Add only small response-shaping helpers if the frontend needs stable summary fields.

### Frontend Changes

- Add migration status inside Save Browser.
- Add dry-run button.
- Add apply button with confirmation.
- Show backup metadata and migration history.
- Keep raw hidden state out of the UI.

### Tests

- UI handles no migration needed.
- UI handles dry-run warnings/errors.
- Apply requires confirmation.
- API failures are visible and do not corrupt local UI state.
- Backend migration tests continue to prove dry-run does not write.

### Acceptance

- A user can safely check and apply migrations without CLI.
- Migration UI never displays raw hidden save payloads.

### Save Migration Impact

- Primary module for v0.7 migration usability.
- Must not bypass `MigrationRegistry`.

### Content Pack / Mod Version Impact

- Can display content/mod version mismatch warnings.
- Does not auto-resolve mod versions.

### LLM Boundary

- No LLM calls.

### Visibility Risk

- Migration reports must not include raw hidden facts, raw memory, debug-only memory, or raw `GameState`.

## Module 3: Mod Manager UI

### Goal

Provide a local UI for discovering, validating, enabling/disabling, and inspecting content-only mods.

### Data Structures

- `ModManagerSummary`
  - `mods: list[ModSummary]`
  - `load_order: list[str]`
  - `errors: list[ValidationIssue]`
  - `warnings: list[ValidationIssue]`
- `EnabledModSet`
  - `world_id: str`
  - `mod_ids: list[str]`
  - `resolved_versions: dict[str, str]`

### API Changes

Potential endpoints:

- `GET /authoring/mods`
- `POST /authoring/mods/{mod_id}/validate`
- `POST /authoring/mods/resolve-load-order`
- `GET /authoring/worlds/{world_id}/enabled-mods`
- `PUT /authoring/worlds/{world_id}/enabled-mods`

All endpoints remain gated by `ENABLE_AUTHORING_API`.

### Frontend Changes

- Add Mod Manager view.
- Show mod manifest details, dependency/conflict errors, content schema compatibility, and load order.
- Enable/disable mods only through backend validation.

### Tests

- Authoring disabled blocks mod manager API.
- Dependency, conflict, engine version, and schema version errors display correctly.
- Path traversal remains rejected.
- No executable mod entry is accepted.

### Acceptance

- A local author can safely inspect and configure content-only mods.
- Mod manager does not execute code or read outside approved roots.

### Save Migration Impact

- Enabled mods should be reflected in save summaries and migration warnings.
- Changing mods does not mutate active session `GameState`.

### Content Pack / Mod Version Impact

- Primary UI for v0.6 advanced mod versioning.
- May require a stable enabled-mods config file, such as `worlds/{world_id}/enabled_mods.yaml`, validated before use.

### LLM Boundary

- No LLM calls.

### Visibility Risk

- Authoring UI may show full content to the local author.
- It must stay separated from player UI and narrator inputs.

## Module 4: Narrative Quality Dashboard

### Goal

Expose automated narrative boundary and quality eval results in the local studio UI.

### Data Structures

- `NarrativeEvalRun`
  - `run_id: str`
  - `created_at: str`
  - `total_cases: int`
  - `passed: int`
  - `failed: int`
  - `failure_reasons: list[str]`
- `NarrativeEvalCaseResult`
  - `case_id: str`
  - `dimension: str`
  - `passed: bool`
  - `reason: str | None`
  - `safe_snapshot_path: str | None`

### API Changes

- Optional local-only endpoints:
  - `POST /evals/narrative-quality/run`
  - `GET /evals/narrative-quality/recent`
  - `GET /evals/narrative-quality/{run_id}`
- Endpoints must use deterministic mock/fake outputs by default and must not call external LLM judges.

### Frontend Changes

- Add quality dashboard showing pass/fail dimensions:
  - invented item
  - invented NPC
  - invented location
  - contradiction with `ActionResult`
  - hidden fact leakage
  - hidden witness leakage
  - illegal suggested action

### Tests

- Dashboard shows successful and failed eval cases.
- Eval runner does not call real LLM.
- Hidden/debug prompt snapshots remain sanitized.

### Acceptance

- A user can run or inspect narrative evals from the studio.
- Failing cases are actionable without exposing hidden content to player UI.

### Save Migration Impact

- None.

### Content Pack / Mod Version Impact

- Eval cases may reference content pack ids.
- Invalid references should be reported, not silently skipped.

### LLM Boundary

- No external LLM judge.
- If future real-model eval mode is added, it must be explicit and excluded from default tests.

### Visibility Risk

- Eval snapshots must be sanitized and never reused as narrator context.

## Module 5: Performance Dashboard

### Goal

Make v0.6 performance samples visible and useful in the local studio.

### Data Structures

- `PerformanceDashboardSummary`
  - `recent_samples: list[PerformanceSample]`
  - `slowest_stages: list[StageTimingSummary]`
  - `threshold_warnings: list[str]`
- `StageTimingSummary`
  - `stage: str`
  - `count: int`
  - `avg_ms: float`
  - `p95_ms: float | None`
  - `max_ms: float`

### API Changes

Reuse:

- `GET /debug/performance/recent`
- `GET /debug/performance/summary`

Potentially add query params:

- `limit`
- `stage`
- `since_turn`

Still gated by `ENABLE_DEBUG_API`.

### Frontend Changes

- Add Performance Dashboard in debug/studio area.
- Show slow game loop stages, validation timings, memory search timings, and save/load timings.
- Avoid raw prompts, hidden facts, raw `GameState`, and API keys.

### Tests

- Disabled debug API blocks dashboard data.
- Enabled debug API returns sanitized performance data.
- Frontend handles empty data.

### Acceptance

- A local developer can identify slow stages without receiving sensitive payloads.

### Save Migration Impact

- Can display migration duration samples.
- Does not modify migrations.

### Content Pack / Mod Version Impact

- Can display validation timing per world/mod.

### LLM Boundary

- No LLM calls.
- Model names or token estimates may be displayed only if sanitized.

### Visibility Risk

- Must not show prompt text, hidden fact text, raw memory content, or debug-only memory in performance metadata.

## Module 6: Local Model Provider Full Integration

### Goal

Turn the v0.6 local provider slice into a usable local HTTP provider integration while keeping the provider abstraction and schema validation.

### Data Structures

- `LocalModelSettings`
  - `base_url: str`
  - `model: str`
  - `timeout_seconds: float`
  - `json_mode: bool`
  - `health_endpoint: str | None`
- `ProviderHealth`
  - `provider: str`
  - `configured: bool`
  - `reachable: bool | None`
  - `model: str | None`
  - `error: str | None`

### API Changes

- `GET /llm/provider/status`
- Optional local-only provider test endpoint:
  - `POST /llm/provider/test-json`

The test endpoint must not send hidden game state. It should use a static harmless schema.

### Frontend Changes

- Add provider settings/status to App Settings.
- Show `mock`, `local_stub`, `local_http`, and `openai` configuration guidance.
- Do not expose or persist API keys in frontend local storage.

### Tests

- `local_http` validates missing `LOCAL_LLM_BASE_URL` clearly.
- Provider status endpoint redacts credentials.
- JSON schema validation failure returns clear error.
- Business modules still depend on `LLMProvider`.

### Acceptance

- A local user can configure and health-check a local model service.
- Local model output still cannot modify `GameState`.

### Save Migration Impact

- None.

### Content Pack / Mod Version Impact

- None.

### LLM Boundary

- Provider authority does not change.
- All outputs used by intent/narrator/memory/draft flows remain schema-validated.

### Visibility Risk

- Health/test endpoints must use synthetic safe prompts, not active hidden state.

## Module 7: Desktop Packaging Enhancement

### Goal

Improve the v0.6 desktop packaging prototype into a smoother local launch workflow without committing to a production installer.

### Data Structures

- `DesktopLaunchProfile`
  - `name: str`
  - `backend_host: str`
  - `backend_port: int`
  - `frontend_port: int`
  - `database_url: str`
  - `enable_debug_api: bool`
  - `enable_authoring_api: bool`
  - `enable_perf_logging: bool`
- `DesktopPreflightResult`
  - `checks: list[DesktopPreflightCheck]`
  - `can_start: bool`

### API Changes

- No required runtime API changes.
- Optional preflight CLI/script output can be JSON for UI consumption.

### Frontend Changes

- Add docs/UX for local launch profiles if implemented.
- Keep API base URL configured through `VITE_API_BASE_URL`.

### Tests

- Launcher script contains no real secrets.
- Build outputs remain ignored.
- README and packaging docs remain accurate.

### Acceptance

- A local user has a repeatable way to launch backend/frontend together.
- No `.env` or API key is bundled into frontend assets.

### Save Migration Impact

- Launcher can warn about saves needing migration, but should not auto-apply migration.

### Content Pack / Mod Version Impact

- Launcher can run validation preflight.

### LLM Boundary

- No new model authority.

### Visibility Risk

- Packaging must not expose local paths or secrets in player UI.

## Module 8: Scenario Template System

### Goal

Provide reusable local templates for new worlds, starter locations, NPC sets, quests, and small scenario packs.

### Data Structures

- `ScenarioTemplate`
  - `id: str`
  - `name: str`
  - `description: str`
  - `template_version: str`
  - `content_files: list[str]`
  - `variables: list[TemplateVariable]`
  - `validation_rules: list[str]`
- `TemplateInstantiationPlan`
  - `template_id: str`
  - `target_world_id: str`
  - `variables: dict[str, str]`
  - `created_files: list[str]`
  - `warnings: list[str]`

### API Changes

- `GET /authoring/templates`
- `GET /authoring/templates/{template_id}`
- `POST /authoring/templates/{template_id}/preview`
- `POST /authoring/templates/{template_id}/instantiate`

All endpoints gated by `ENABLE_AUTHORING_API`. Instantiation writes only content-pack files after validation.

### Frontend Changes

- Add Create World / Add Scenario wizard.
- Show template variables, preview, validation report, and impact report.

### Tests

- Template preview does not write files.
- Template instantiation validates output.
- Path traversal and duplicate ids are rejected.
- Hidden text is not automatically made player-visible.

### Acceptance

- A local author can create a new world scaffold without hand-copying YAML.

### Save Migration Impact

- New templates do not migrate saves.
- Adding templates to existing worlds should produce impact warnings if ids collide.

### Content Pack / Mod Version Impact

- Template files must declare compatible schema/content versions.

### LLM Boundary

- No LLM required.
- Future LLM-assisted template filling must produce drafts only and go through validation.

### Visibility Risk

- Templates must not mark hidden facts as player-visible by default.

## Module 9: Visual Quest Graph Editor Initial Slice

### Goal

Provide a visual read/edit surface for quest stages, objectives, and triggers while preserving YAML validation.

### Data Structures

- `QuestGraphNode`
  - `quest_id: str`
  - `stage_id: str`
  - `label: str`
  - `visibility: str`
  - `objectives: list[str]`
- `QuestGraphEdge`
  - `source_stage_id: str`
  - `target_stage_id: str`
  - `trigger_type: str`
  - `trigger_ref: str`
- `QuestGraphDraft`
  - `quest_id: str`
  - `nodes: list[QuestGraphNode]`
  - `edges: list[QuestGraphEdge]`
  - `validation_report: ValidationReport`

### API Changes

- `GET /authoring/worlds/{world_id}/quests/graph`
- `POST /authoring/worlds/{world_id}/quests/graph/preview`
- `PUT /authoring/worlds/{world_id}/quests/graph`

All writes must update YAML through backend validation, not active `GameState`.

### Frontend Changes

- Add graph/list hybrid editor for quests.
- Initial implementation may use simple nodes and edges rather than full drag-and-drop.
- Support raw YAML fallback.

### Tests

- Quest graph load matches `quests.yaml`.
- Preview catches invalid trigger refs.
- Save requires validation.
- Hidden quests remain hidden in player visible state.

### Acceptance

- Authors can inspect and make small quest graph edits without losing YAML fidelity.

### Save Migration Impact

- Removing/renaming quest ids must trigger impact-analysis warnings.

### Content Pack / Mod Version Impact

- Quest graph writes may require content pack version bump guidance.

### LLM Boundary

- No LLM judgment.
- Optional draft suggestions remain drafts only.

### Visibility Risk

- Authoring UI can show hidden quest content to the author, but it must not enter player UI or narrator.

## Module 10: Automated Playtesting Dashboard

### Goal

Expose v0.6 playtesting agents, invariant results, and reports in the local studio UI.

### Data Structures

- `PlaytestRunRequest`
  - `world_id: str`
  - `agent: str`
  - `steps: int`
  - `seed: int`
  - `save_load_check: bool`
- `PlaytestRunSummary`
  - `run_id: str`
  - `turns_run: int`
  - `actions_taken: list[str]`
  - `errors: list[str]`
  - `invariant_violations: list[str]`
  - `visibility_leaks: list[str]`
  - `save_load_failures: list[str]`

### API Changes

- `POST /playtests/run`
- `GET /playtests/recent`
- `GET /playtests/{run_id}`

These are local studio endpoints and should default to mock/local_stub providers.

### Frontend Changes

- Add Playtesting Dashboard.
- Let user choose agent, steps, seed, and world.
- Show invariant failures and action trace.

### Tests

- Fixed seed is deterministic.
- Dashboard handles failed invariants.
- Playtest actions go through `GameLoop`.
- No real LLM calls.

### Acceptance

- A local author can run deterministic smoke playtests from the UI.

### Save Migration Impact

- Playtest can include save/load check.
- Does not modify existing user saves unless explicitly configured to use a temp save.

### Content Pack / Mod Version Impact

- Can run against selected enabled mod set.

### LLM Boundary

- Uses mock/local_stub by default.
- Agents must not call real LLM or directly inspect hidden state for decisions.

### Visibility Risk

- Playtest reports are debug/studio data and must not enter player narrative.

## Module 11: Import / Export Workflow

### Goal

Support safe local export/import of worlds, mods, saves, eval reports, and validation reports.

### Data Structures

- `ExportManifest`
  - `id: str`
  - `created_at: str`
  - `export_type: world | mod | save | report_bundle`
  - `engine_version: str`
  - `schema_version: str`
  - `included_files: list[str]`
  - `redactions: list[str]`
- `ImportPreview`
  - `parsed_ok: bool`
  - `manifest: ExportManifest | None`
  - `conflicts: list[str]`
  - `validation_report: ValidationReport`
  - `requires_migration: bool`

### API Changes

- `POST /authoring/export`
- `POST /authoring/import/preview`
- `POST /authoring/import/apply`

Authoring-gated. Apply must validate content and refuse path traversal.

### Frontend Changes

- Add import/export panel.
- Show manifest, validation, conflicts, and dry-run impact before apply.

### Tests

- Export excludes `.env`, database internals not explicitly requested, logs, cache, and build output.
- Import preview does not write files.
- Apply validates paths and schema.
- Save import runs migration dry-run.

### Acceptance

- A user can move local content safely without hand-copying many files.

### Save Migration Impact

- Imported saves may require migration.
- Import preview must surface migration status before apply.

### Content Pack / Mod Version Impact

- Export/import manifests must include content/mod version info.

### LLM Boundary

- No LLM calls.

### Visibility Risk

- Export can include hidden authoring content by design, but must label the bundle as authoring data and never feed it into player UI.

## Module 12: App Settings / Local Privacy Panel

### Goal

Make local configuration, provider settings, debug/authoring/perf toggles, data paths, and privacy boundaries visible in one place.

### Data Structures

- `AppSettingsSummary`
  - `database_configured: bool`
  - `llm_provider: str`
  - `local_provider_configured: bool`
  - `debug_api_enabled: bool`
  - `authoring_api_enabled: bool`
  - `perf_logging_enabled: bool`
  - `memory_backend: str`
  - `redacted_paths: dict[str, str]`
- `PrivacyBoundarySummary`
  - `stores_api_keys: bool`
  - `uploads_telemetry: bool`
  - `debug_data_local_only: bool`
  - `authoring_data_local_only: bool`

### API Changes

- `GET /settings/summary`
- `GET /settings/privacy`

Responses must redact secrets and avoid raw `.env`.

### Frontend Changes

- Add Settings / Privacy panel.
- Show provider status, local-only notices, and safe config summaries.
- Do not edit `.env` directly in v0.7 unless a later task explicitly designs a safe config writer.

### Tests

- Settings endpoint redacts secrets.
- No API key values returned.
- Frontend displays disabled states safely.

### Acceptance

- A user can see what is enabled and why local privacy boundaries matter.

### Save Migration Impact

- Can link to migration settings/status.

### Content Pack / Mod Version Impact

- Can show authoring root and enabled mod status.

### LLM Boundary

- Provider status only; no model calls unless explicit safe health check.

### Visibility Risk

- Must not expose secrets, raw environment variables, or local absolute paths beyond redacted display.

## Module 13: Studio UX Polish Pass

### Goal

Improve navigation, empty states, error states, loading states, copy consistency, accessibility, and frontend resilience without changing world rules.

### Data Structures

No new canonical backend structures expected.

Frontend-only helper types may include:

- `PanelState`
- `ToastMessage`
- `AsyncRequestState`
- `StudioNavigationItem`

### API Changes

None expected.

### Frontend Changes

- Normalize panel layout and navigation.
- Improve empty/error/loading states.
- Ensure debug-only panels are visually separated.
- Ensure player-facing panels never render debug-only records.
- Add clear local-only labels for authoring/debug/perf tools.

### Tests

- Frontend build passes.
- Key views tolerate missing optional data.
- Debug disabled states render safely.
- No player main area renders `debug_only` graph nodes, raw `state_deltas`, or debug memories.

### Acceptance

- Studio feels coherent and less fragile while preserving all safety boundaries.

### Save Migration Impact

- None beyond UI links/status.

### Content Pack / Mod Version Impact

- None beyond UI labels/status.

### LLM Boundary

- No new LLM authority.

### Visibility Risk

- Main risk is accidental cross-panel rendering of debug data.
- Mitigate with type-level separation and frontend checks.

## v0.7 Integration Testing Requirements

The v0.7 regression suite should cover:

1. Studio home loads from a clean v0.6-style project.
2. Save migration UI can status, dry-run, and apply through existing migration service.
3. Mod Manager UI can show valid, invalid, dependency-conflicted, and disabled mods.
4. Narrative Quality Dashboard displays deterministic eval failures without real LLM calls.
5. Performance Dashboard reads sanitized debug performance summaries.
6. Local provider settings/status never expose keys and never bypass `LLMProvider`.
7. Desktop launcher/preflight never includes real `.env` or API keys.
8. Scenario template preview does not write files; instantiation validates output.
9. Quest graph preview catches invalid references and does not mutate active `GameState`.
10. Playtesting Dashboard runs a deterministic agent through `GameLoop`.
11. Import/export preview does not write files and rejects path traversal.
12. Settings/Privacy panel redacts secrets and keeps authoring/debug/perf local-only.
13. Frontend player UI never renders debug-only graph nodes, raw `state_deltas`, hidden memory, hidden relationships, or hidden mod metadata.
14. `python -m pytest` passes.
15. `cd frontend && npm.cmd run build` passes.

## v0.7 Final Acceptance Standards

v0.7 can be accepted when:

- All v0.7 features preserve the v0.6 authority and visibility boundaries.
- Studio workflows are accessible from the frontend without needing CLI for common daily tasks.
- CLI remains available for migration, validation, playtesting, and eval workflows.
- Save migration remains dry-run capable and fixture-tested.
- Authoring UI continues to use backend validation and never edits active `GameState`.
- Mod manager never executes code and never reads outside approved roots.
- Local model provider integration remains behind `LLMProvider` and schema validation.
- Desktop packaging remains prototype/local-only and excludes `.env` and API keys.
- Narrative and playtesting evals are deterministic and do not call real external APIs by default.
- Debug/perf data never reaches narrator or player-facing main UI.
- Full backend tests and frontend build pass.
- v0.7 audits, acceptance report, release notes, and freeze checks are complete.

## v0.8 Candidate Directions

Potential v0.8 directions:

- Stable desktop packaging with signed local installer research.
- Richer visual editors for quests, NPC schedules, relationships, and economy.
- Local-only backup/restore manager.
- More capable local model adapters with provider-specific capability detection.
- Scenario library and reusable content snippets.
- Advanced playtest scenario scripting.
- Narrative regression corpus with author-curated golden cases.
- Accessibility and keyboard-driven studio workflows.
- Save diff/replay visualizer.
- Optional local-only semantic memory backend with stronger redaction controls.

