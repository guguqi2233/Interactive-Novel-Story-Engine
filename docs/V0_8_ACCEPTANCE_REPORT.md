# v0.8 Acceptance Report

## Verdict

**Accepted for local v0.8 release with non-blocking cautions.**

v0.8 meets the planned "Visual World Authoring" scope. The project now provides visual authoring surfaces for maps, quests, NPC goals, factions/relationships, item economy data, rumor/crime consequence chains, validation graphs, timeline replay, world branch/diff workflows, scenario regression, local templates, prompt profiles, advanced packages, and authoring UX integration.

The core authority model remains intact: the world engine is still the fact source, LLMs remain language-layer providers, authoring tools edit content packs through preview/validation/explicit save, and authoring/debug data is not promoted into player or narrator surfaces.

## Verification Date

2026-05-18

## Verification Commands

```powershell
python -m pytest
npm.cmd run build
npm.cmd run build
```

Results:

- `python -m pytest`: **596 passed in 17.24s**.
- First parallel frontend build attempt failed with a transient Vite/Rollup emitted asset path error: `received "d:/KF/world/frontend/index.html"`.
- Immediate standalone rerun of `npm.cmd run build`: **passed** with `tsc -b && vite build`.

## Scope Accepted

### 1. Visual Map

Accepted.

- `locations.yaml` remains backward-compatible when visual fields are absent.
- Map graph generation derives nodes from locations and edges from exits.
- Authoring map APIs support read, preview, validate, and explicit save.
- Player-visible map graph filters hidden nodes and hidden edges.
- Map save routes through content validation and does not modify active `GameState`.

### 2. Quest Graph

Accepted.

- `quests.yaml` can be converted into structured quest graph data and back to YAML.
- Invalid `next_stage` references are caught.
- Unreachable stage and missing terminal-stage cases produce validation warnings.
- Hidden quest content remains authoring-only and does not enter player visible state.
- Quest graph save goes through validation and does not bypass the quest state machine.

### 3. NPC Goal Editor

Accepted.

- NPC goals are read from `npcs.yaml` and exposed through authoring schema.
- Goal ids, priorities, statuses, condition references, desired-state references, and planning action names are validated.
- Hidden NPC goals remain authoring-only.
- Goal editing does not mutate active runtime `GameState`; runtime NPC planning still uses rule modules and NPC knowledge boundaries.

### 4. Faction / Relationship Editor

Accepted.

- Faction and relationship authoring graphs can be read, previewed, validated, and saved.
- Invalid NPC and faction ids are caught.
- Trust, fear, affinity, obligation, conflict, and visibility fields remain structured.
- Hidden relationships do not enter player graph responses.
- Save goes through world validation.

### 5. Item / Economy Editor

Accepted.

- Item and merchant inventory data are exposed through structured authoring schema.
- Item ids, non-negative prices, ownership conflicts, merchant references, and shop inventory references are validated.
- Hidden shop items are filtered from player shop/economy UI.
- The frontend may preview/display price fields, but authoritative trade results remain in backend economy rules.

### 6. Rumor / Crime Consequence Editor

Accepted.

- Rumor/crime consequence graph data can be generated from content.
- Invalid rumor fact ids, hidden fact text leakage, duplicate consequence ids, and loop-like consequence risks are detected by validation.
- The editor configures content and consequence definitions only; it does not modify active crime records or runtime social state.
- No LLM is used for rumor truth or crime consequence decisions.

### 7. Visual Validation Graph

Accepted.

- Validation reports can be converted into `ValidationGraph` data with file/entity/reference/issue nodes and structured edges.
- Missing references and visibility risks are represented as graph issues.
- Output uses content-relative file/path/id data and does not expose API keys, raw env, or sensitive local absolute paths in reviewed paths.

### 8. Timeline Replay

Accepted.

- Debug timeline APIs return stable turn-grouped event views.
- Replay dry-run applies event deltas in memory and does not write the database.
- Raw `state_deltas` are available only through debug timeline/replay APIs.
- Player APIs do not return debug timeline data or raw deltas.

### 9. World Branch / Diff

Accepted.

- Local world branches can be created from whitelisted content files.
- Diff detects added, removed, changed, renamed-candidate, broken-reference, migration-impact, and visibility-risk data.
- Branch creation does not copy `.env`, database, logs, caches, arbitrary files, or build outputs.
- Branch/diff operations do not modify active `GameState`.

### 10. Scenario Regression

Accepted.

- Scenario regression cases and runs are available through gated local APIs.
- Runs use mock/local deterministic providers and act through game-loop style input.
- Forbidden visible facts cause failures.
- Runs use temporary sessions/saves and do not modify real user saves.
- Hidden fact text is redacted in ordinary report output.

### 11. Template Browser

Accepted.

- Local templates can be listed, viewed, previewed, rendered, and applied through authoring-gated APIs.
- Preview does not write disk.
- Apply requires explicit validation/save flow.
- Templates are data/YAML renderers and are not script executors.
- Executable template files and unsafe paths are rejected.

### 12. Prompt Profile Manager

Accepted.

- Prompt profiles can be listed, selected, and validated.
- Profiles can adjust local style and prompt variants, but cannot grant LLMs hidden facts, raw state deltas, or GameState authority.
- API keys are not part of prompt profile data.
- Provider selection still goes through the provider factory and `LLMProvider` abstraction.

### 13. Advanced Import / Export

Accepted.

- Local package manifests and checksums are supported.
- Import dry-run validates manifest, checksum, compatibility, path traversal, disallowed file types, and overwrite/conflict risks.
- Zip slip and executable files are rejected.
- Save bundle import reports migration status.
- `.env`, API keys, database connection config, logs, and executable code are not imported.

### 14. Desktop Shell

Accepted as local prototype polish.

- Desktop packaging documentation and startup scripts have been updated for local studio use.
- Scripts do not hardcode or inject API keys into frontend builds.
- `.env` is not committed or bundled by design.
- Build outputs remain local artifacts and are not part of the release surface.
- This remains a local launcher/shell prototype, not a signed public desktop installer.

### 15. Authoring UX

Accepted.

- Authoring navigation is unified across map, quests, NPC goals, factions/relationships, items/economy, rumors/crime, templates, and validation.
- Editors share preview/validate/save concepts, validation report display, dirty-state handling, hidden-content warnings, and disabled API fallbacks.
- Authoring-only data remains visually and structurally separate from player UI.

### 16. v0.8 Integration Tests

Accepted.

- v0.8 integration coverage exists for map authoring, quest graph authoring, NPC goal authoring, social graph authoring, item/economy authoring, rumor/crime authoring, validation graph, timeline replay, world branching, scenario regression, scenario templates, prompt profiles, import/export, and full v0.8 regression paths.
- Full backend suite passed: **596 tests**.
- Frontend build passed on standalone verification.

## Boundary Review

### LLM Boundary

Passed.

- v0.8 visual editors do not call LLMs to generate or validate canonical content.
- LLM output does not directly modify `GameState`.
- Local model and prompt profile support remain behind `LLMProvider` and provider factory.
- Narrator still receives only visible facts and narrator-safe context.
- Scenario regression, playtesting, validation graph, branch/diff, import/export, and timeline replay do not call real LLM APIs.

### StateDelta / Event Boundary

Passed.

- Runtime state changes continue to flow through `StateDelta` and `apply_delta`.
- Player actions, system ticks, NPC planning ticks, and playtesting-agent game inputs are recorded through event-producing paths.
- Authoring and visual editor operations modify content files only through local authoring services and explicit save; they do not mutate active runtime `GameState`.
- Timeline replay dry-run applies deltas in memory and does not write saves.

### Visibility / Authoring / Debug Boundary

Passed.

- Player APIs expose only player-visible state.
- Hidden facts, hidden objects, NPC secrets, hidden witnesses, hidden relationships, hidden faction conflicts, hidden shop inventory, hidden/debug memory, and authoring-only graph data do not enter player/narrator surfaces.
- Authoring APIs may expose full local content to the creator, but they are gated and separate from player UI.
- Debug timeline and raw `state_deltas` remain debug-only.

### Security / Import-Export Boundary

Passed for local self-use release.

- Authoring/debug/perf/eval/playtest APIs are local/gated tooling surfaces.
- Import/export rejects zip slip, executable files, `.env`, secret files, database files, logs, and unsafe paths.
- Template and mod systems do not execute arbitrary code.
- Desktop shell work does not package API keys or a real `.env`.
- Frontend does not store API keys.

## Known Limitations

- Frontend build had one transient failure during a parallel verification run, then passed immediately when rerun standalone. This should be watched during final freeze.
- Authoring single-file saves validate and roll back on validation failure, but a process crash between write and rollback could leave invalid YAML. This is a non-blocking hardening item.
- Mod validation may include local path-like data in some error reports. This is authoring-only but should be sanitized further in a future hardening pass.
- Narrative eval endpoints are debug-gated rather than independently gated by `ENABLE_EVAL_API`.
- Debug timeline intentionally exposes raw `state_deltas` when debug API is enabled. It must remain local-only.
- Authoring tools intentionally expose hidden content to the local creator. They must remain separated from player/narrator surfaces.
- Save/package exports can contain full local state. They must remain local artifacts and should not be rendered as player summaries.
- Desktop shell remains a local prototype, not a formal packaged desktop release.

## Acceptance Risks

1. **Authoring data durability**
   - Validation rollback protects ordinary errors, but atomic write hardening would reduce crash-window risk.

2. **Local-only API exposure**
   - Debug, authoring, eval, playtest, and performance endpoints are appropriate for local use. Binding the backend beyond localhost would raise risk.

3. **Frontend authoring/player separation**
   - v0.8 adds many authoring panels. Future UI changes must avoid reusing authoring/debug payloads in player narrative panels.

4. **Package/save sensitivity**
   - Advanced import/export can handle full saves and content packages. Summaries should remain safe, and raw archives should stay local.

5. **Build reproducibility**
   - One transient Vite build failure appeared under parallel execution. Standalone build passed; final freeze should rerun build once more.

## Recommended v0.9 Priorities

1. Harden authoring saves with draft validation plus atomic replace.
2. Sanitize all authoring/mod/validation path output to relative, non-sensitive paths.
3. Add independent `ENABLE_EVAL_API` gating for narrative eval endpoints.
4. Add lightweight frontend/component tests for authoring-player separation, disabled API states, and validation UX.
5. Expand replay/checkpoint verification and deterministic timeline snapshots.
6. Improve visual editor ergonomics: better graph layout, reference pickers, bulk validation, and safer conflict resolution.
7. Continue desktop shell work only as local packaging unless a formal secure distribution plan is designed.

## Final Status

**v0.8 is accepted for local release.**

No release-blocking high-risk issue was found after audits, strict code review, blocker triage, backend test verification, and frontend build verification. The remaining issues are non-blocking hardening items appropriate for v0.9 or a v0.8.x patch.
