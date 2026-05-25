# v3.7 Full Integration Review

Verification date: 2026-05-25

## Verdict

**Mostly Integrated with v3.7 Product Check Blockers**

The v0.1-v3.6 foundation remains integrated in current HEAD. Backend tests pass,
the frontend production build passes, stable quality-gate fixtures pass, the v2
release checklist passes, the compatibility matrix reports compatible
contracts, and contract docs check passes through the documented
`PYTHONPATH=backend` tool invocation.

v3.7 product completion is not yet ready to declare final Local Complete
Product acceptance because the "all frontend check:* scripts" requirement is
currently failing. The failures are static/product-readiness checks, not a
pytest or production build failure, but they are release-blocking for the v3.7
acceptance bar because v3.7 requires all frontend checks to pass.

## Version Coverage Matrix

| Version | Docs Present | Code / API / UI Present | Tests Present | Integrated in Current HEAD | Covered by Successor | Gaps / Blocking Status |
| --- | --- | --- | --- | --- | --- | --- |
| v0.1 | Yes | Health, game start/input/state, GameState, StateDelta, EventLog, fake provider, SQLite, starter frontend | Current pytest covers legacy paths | Yes | Later World Studio / QA | No blocker found |
| v0.2 | Yes | World loading, saves, visible_state, provider factory, frontend world/save controls | Current pytest covers persistence and visibility | Yes | Later project/save UI | No blocker found |
| v0.3 | Yes | NPC schedule, search, inventory, lockpick, sneak, quests, tick, debug timeline | Current pytest includes v0.3 regression | Yes | Later World Studio / Replay | No blocker found |
| v0.4 | Yes | Faction, reputation, rumor, crime, combat, social tick, memory safety | Current pytest covers social/combat systems | Yes | Later World and QA panels | No blocker found |
| v0.5 | Yes | Authoring API, validation, memory backend, NPC planning, mod packaging | Current pytest covers authoring and memory | Yes | v3.4 Authoring / Mod UI | No blocker found |
| v0.6 | Yes | Save migration, authoring diff/dry-run, graph APIs, playtesting, perf instrumentation | Current pytest covers migration, playtest, perf | Yes | v3.5/v3.6 QA and perf UI | No blocker found |
| v0.7 | Yes | Studio home, migration UI, mod manager, quality/performance dashboards, settings/privacy | Current pytest and frontend checks cover successors | Yes | v2.9-v3.6 UI | No blocker found |
| v0.8 | Yes | Visual authoring, relationship/quest/map tooling, replay, branch/diff, import/export | Current pytest covers authoring, graph, import/export | Yes | v3.4 Authoring / v3.5 Replay | No blocker found |
| v0.9 | Yes | WorldQualityReport, playtesting, hidden leak, coverage, quality gate | Current pytest covers quality gate and hidden leak | Yes | v3.5 Quality Dashboard | No blocker found |
| v1.0 | Yes | Stable local studio edition and local API hardening | Current pytest covers stable APIs | Yes | v2.x/v3.x local studio | No blocker found |
| v1.1 | Yes | RP immersion, boundaries, character cards, RP memory, Tavern compatibility | Current pytest covers RP and Tavern boundaries | Yes | v3.2 Tavern UI | No blocker found |
| v1.2 | Yes | Visual Authoring Pro and content authoring workflows | Current pytest covers authoring workflows | Yes | v3.4 Authoring UI | No blocker found |
| v1.3 | Yes | Advanced NPC simulation, plans, reactions, simulation tick/debugger | Current pytest covers NPC simulation | Yes | World/QA successors | No blocker found |
| v1.4 | Yes | Content production pipeline, batch validators, templates, local library | Current pytest covers production pipeline | Yes | Authoring/Mod successors | No blocker found |
| v1.5 | Yes | Provider capability registry, prompt lab, benchmark, routing, usage | Current pytest covers provider/prompt lab | Yes | v2.5/v3.5 Provider | No blocker found |
| v1.6 | Yes | Advanced gameplay modules, ActionRegistry extension, action DSL, module quality | Current pytest covers modules and action mods | Yes | v2.7/v3.3/v3.4 | No blocker found |
| v1.7 | Yes | Desktop studio, launcher, project selector, logs, backup/restore, offline help | Current pytest and frontend checks cover successors | Yes | v3.0 Desktop Studio | No blocker found |
| v1.8 | Yes | Stable contracts, compatibility matrix, contract docs generator | Current compatibility matrix and contract docs check pass | Yes | v2.0 platform contracts | No blocker found |
| v1.9 | Yes | Release candidate hardening, release checklist, audits | Current v2 release checklist passes | Yes | v2.0/v3.x release flow | Historical test count not recorded in doc; not blocking current integration |
| v2.0 | Yes | Modular platform, package/module/provider contracts, local browsers, release checklist | Current pytest and v2 release checklist pass | Yes | v2.1-v3.7 platform | Historical test count not recorded in doc; not blocking current integration |
| v2.1 | Yes | NarrativeProject, workspace, repository, project APIs/frontend shell | Current pytest covers project workspace | Yes | v2.9/v3.x shell | No blocker found |
| v2.2 | Yes | Novel Studio MVP and shared libraries | Current pytest and frontend checks cover Novel successors | Yes | v3.1 Novel UI | No blocker found |
| v2.3 | Yes | Tavern Studio MVP | Current pytest and frontend checks cover Tavern successors | Yes | v3.2 Tavern UI | No blocker found |
| v2.4 | Yes | Cross-Mode bridge, proposals, validation, audit | Current pytest covers Cross-Mode | Yes | v3.5/v3.7 review surfaces | No blocker found |
| v2.5 | Yes | Provider Gateway Pro, ProviderProfile, ModelProfile, routing, usage | Current pytest covers Provider Gateway and v3.5 provider APIs | Yes | v3.5 Provider Connectivity | No blocker found |
| v2.6 | Yes | Script / Mod Platform Pro, PackageManifestV2, ActionMod, RuleModule, quality | Current pytest covers mod platform | Yes | v3.4 Authoring/Mod | No blocker found |
| v2.7 | Yes | Advanced world simulation modules and module quality/migration | Current pytest covers modules | Yes | v3.3 World module UI | No blocker found |
| v2.8 | Yes | Roleplay immersion and mature module safety | Current pytest covers RP/mature boundaries | Yes | v3.2 Tavern UI | No blocker found |
| v2.9 | Yes | Local UI/UX foundation and frontend safety checks | `check:v29-ui` passes | Yes | v3.x UI | No blocker found |
| v3.0 | Yes | Desktop Studio polish, backup/restore, diagnostics, launcher docs | Backend/build pass, but `check:v30-ux` currently fails | Partially | v3.7 product status/navigation | **Blocking check gap:** missing "Desktop Packaging" token in current frontend check target |
| v3.1 | Yes | Novel Studio UI Pro | `check:v31-novel-ui` passes | Yes | v3.7 Novel checklist | No blocker found |
| v3.2 | Yes | Tavern Studio UI Pro | `check:v32-tavern-ui` passes | Yes | v3.7 Tavern checklist | No blocker found |
| v3.3 | Yes | World Studio UI Pro | `check:v33-world-ui` passes | Yes | v3.7 World checklist | No blocker found |
| v3.4 | Yes | Authoring / Mod UI Pro | `check:v34-authoring-ui` passes | Yes | v3.7 Authoring/Mod checklist | No blocker found |
| v3.5 | Yes | QA / Debug / Replay and Provider Connectivity UI Pro | `check:v35-qa-debug-provider-ui` passes; provider pytest passes | Yes | v3.7 product readiness | No blocker found |
| v3.6 | Yes | Performance / accessibility polish, chunk splitting, long-list optimization, safe caches | v3.6 individual checks pass; `check:v36-integration-regression` fails only because it depends on failing v3.0 check | Integrated with inherited check failure | v3.7 product polish | Inherited frontend check blocker |
| v3.7 | Roadmap and contract docs present; acceptance report not expected yet | Product readiness, tour, workflow, provider setup, lifecycle, studio workflows, privacy, navigation, settings, status, states, and acceptance UI are partially present | Backend v3.7 tests pass; several v3.7 frontend checks fail | Partially | N/A | **Release blocker before v3.7 acceptance:** frontend check failures listed below |

## Feature Coverage Matrix

| Feature Area | Status | Evidence | Gaps / Risks |
| --- | --- | --- | --- |
| World Engine | Present / Integrated | Pytest covers GameState, StateDelta, EventLog, actions, saves, visibility, modules | No current blocker |
| LLM Boundary | Present / Integrated | Provider tests and docs maintain LLM as language layer | No real provider tests found in executed checks |
| Visibility | Present / Integrated | Visibility tests pass; v3.6/v3.5 docs and checks preserve normal/debug split | v3.7 privacy check needs explicit "no hidden fact text" exclusion copy |
| Persistence / Migration | Present / Integrated | Save repository, migration, backup/restore tests pass | No current blocker |
| Content Packs / Templates | Present / Integrated | Content validation and production pipeline tests pass; demo project exists under examples | No current blocker |
| Social / Combat / Economy | Present / Integrated | Pytest covers factions, combat, economy, rumors, social tick | No current blocker |
| Novel Studio | Present / Integrated, product check not clean | v3.1 check passes; current pytest passes | v3.7 Novel workflow check fails on API-key/transient-key wording rule |
| Tavern Studio | Present / Integrated, product check not clean | v3.2 check passes; current pytest passes | v3.7 Tavern workflow check fails on API-key/transient-key wording rule |
| World Studio | Present / Integrated, product check not clean | v3.3 check passes; current pytest passes | v3.7 World workflow check fails on API-key/transient-key wording rule |
| Cross-Mode Bridge | Present / Integrated, product check not clean | Cross-Mode backend tests pass | v3.7 Cross-Mode workflow check fails on API-key/transient-key wording rule |
| Authoring / Mod Studio | Present / Integrated | v3.4 and v3.7 Authoring/Mod checks pass; mod gate fixture passes | No current blocker |
| Provider Gateway | Present / Integrated | Provider pytest passes; v3.5/v3.6 provider checks pass | No current blocker in backend; product checklist wording must stay secret-safe |
| Provider Connectivity / Model Discovery | Present / Integrated | Connection, model discovery/sync, assignment, status cache tests pass | No real-provider test found |
| QA / Debug / Replay | Present / Integrated, product check not clean | v3.5 checks pass; StateDelta/EventLog/debug tests pass | v3.7 QA/Debug workflow check fails on API-key/transient-key wording rule |
| Quality Gate / Playtest | Present / Integrated | Project quality gate fixture passes; pytest quality tests pass | No current blocker |
| Backup / Restore / Diagnostics | Present / Integrated, product check not clean | Backup/diagnostics v3.6 checks pass | v3.7 Backup/Diagnostics workflow check fails on key terminology rule |
| Export | Present / Integrated | v3.7 Export workflow check passes | No current blocker |
| Local UI/UX / Accessibility | Present / Mostly Integrated | v2.9, v3.1-v3.6 individual checks pass; build passes | v3.0 UX check fails; inherited v3.6 integration check fails |
| Desktop Studio | Present / Integrated with check gap | Desktop docs/features exist in v3.0 acceptance and current code | Frontend v3.0 check missing "Desktop Packaging" token |
| Privacy / Secrets | Present / Mostly Integrated | v2 release checklist secret scan passes; pytest provider redaction tests pass | v3.7 privacy UI check missing explicit hidden fact exclusion copy |
| Local-first / No Onlineization | Present / Integrated | Docs and frontend checks preserve no account/cloud/marketplace direction | No onlineization blocker found |

## Missing or Unconfirmed Items

### Release Blockers Before v3.7 Local Complete Product

1. **All frontend check scripts do not pass.** Current result: 53 scripts found;
   44 passed and 9 failed.
2. **`check:v30-ux` fails** because the v3.0 Local Studio UX safety check cannot
   find the required "Desktop Packaging" completion token.
3. **`check:v36-integration-regression` fails** because it runs and depends on
   the failing v3.0 UX safety check.
4. **Several v3.7 workflow checks fail** because the checklist copy contains
   API-key or transient-key terminology outside the scripts' allowed safe
   exclusion wording:
   - `check:v37-novel-workflow`
   - `check:v37-tavern-workflow`
   - `check:v37-world-workflow`
   - `check:v37-cross-mode-workflow`
   - `check:v37-qa-debug-workflow`
   - `check:v37-backup-diagnostics-workflow`
5. **`check:v37-privacy-safety-review` fails** because the privacy review UI
   does not include the expected hidden fact display exclusion wording:
   "no hidden fact text".

### Must Fix Before v3.7 Acceptance

- Restore the v3.0 Desktop Packaging token or update the check target/copy in a
  way that keeps the local desktop packaging boundary visible.
- Rewrite v3.7 workflow checklist secret-boundary copy so it is explicit about
  exclusion/redaction without looking like an API-key input path.
- Add the missing hidden-fact exclusion wording to the v3.7 privacy/safety
  review surface.
- Re-run all frontend `check:*` scripts with strict exit-code handling.

### Can Be Optimized After v3.7 Acceptance

- Browser-level smoke tests for route-level lazy pages.
- Larger demo fixtures for very large manuscripts, sessions, EventLogs, model
  lists, and packages.
- More screen-reader and keyboard walkthrough QA beyond static source checks.
- Further App shell extraction if the main chunk grows again.

### Historical Doc Gaps Only

- v1.9 and v2.0 acceptance reports exist but do not record historical test
  counts in the current documents. Current pytest, release checklist, and
  compatibility checks cover the current integration state, so this is not a
  current blocker.
- v3.7 acceptance report and release notes are not expected yet at this review
  stage.

### Unconfirmed

- No browser-driven route smoke test was run during this review.
- No real Provider connectivity was tested; this is intentional. Tests and
  checklists must continue to use fake/mock/local_stub providers only.

## Regression Risks

- **Frontend product check regression:** v3.0/v3.7 static checks fail. This is
  the primary current release risk.
- **Desktop packaging visibility:** the missing v3.0 token may indicate that a
  user-facing desktop packaging/status label was removed or renamed during
  product navigation/status polish.
- **Secret-boundary copy risk:** v3.7 workflow checklist text is close enough to
  API-key/transient-key wording that safety scripts flag it. Even if the UI does
  not expose a key field, the copy should be tightened before release.
- **Privacy/safety wording risk:** the privacy review needs an explicit safe
  hidden-fact display exclusion statement.
- **Tool invocation UX:** direct `python -m backend.app.tools.compatibility_matrix`
  and `python -m backend.app.tools.generate_contract_docs` imports fail because
  those tools expect the documented `PYTHONPATH=backend` plus `app.tools...`
  invocation. The documented invocation passes; wrappers/docs should remain the
  recommended route.
- **Worktree state:** the current worktree contains expected v3.7 development
  changes and is not clean. This review is not a commit-readiness audit.

## Boundary Review

### World Engine Authority

Passed at current evidence level. Backend tests covering GameState,
StateDelta, EventLog, actions, save/load, migration, modules, and visibility all
pass. No evidence was found that v3.7 product polish changed the World Engine
fact boundary.

### StateDelta / EventLog

Passed at current evidence level. StateDelta and EventLog contracts remain in
the compatibility matrix as compatible. Debug and replay remain documented as
observation-only. Frontend v3.6 StateDelta/EventLog checks pass.

### Visibility

Mostly passed, with a v3.7 UI wording blocker. Backend visibility tests pass and
normal UI safety checks through v3.6 pass. The v3.7 privacy/safety frontend
check requires clearer hidden-fact exclusion copy before acceptance.

### Provider Gateway / Provider Secrets

Passed at current evidence level. Provider Gateway, provider connection,
model discovery/sync, model assignment, redaction, and status cache tests pass
through pytest. v2 release checklist reports no real API key pattern found.
Provider tests use fake/local paths in the current suite.

### transient Provider Key

Passed at current evidence level in backend tests and v3.6 cache checks.
However, v3.7 workflow checklist copy around transient-key terminology must be
rewritten to satisfy frontend safety checks.

### Mod Permissions / Arbitrary Code

Passed at current evidence level. Mod quality gate fixture passes; standalone
safe declarative mod sample tests pass in pytest. No arbitrary-code plugin
enablement was found by the executed checks.

### Mature / Private Data

Passed at current evidence level. RP/mature tests pass and mature/private
content remains default-off and excluded by default in docs and tests.

### Debug Gating

Passed at current evidence level. Debug tests pass; v3.5/v3.6 debug frontend
checks pass. v3.7 QA/Debug product checklist currently fails for copy rules, not
for a detected debug-gating bypass.

### Local-first / No Onlineization

Passed at current evidence level. No account, cloud sync, online marketplace,
remote package download, online writing/RP/play, or API resale entry was
detected by the executed release/frontend checks.

## Verification Commands and Results

| Command | Result |
| --- | --- |
| `python -m pytest` | Passed: `1795 passed in 136.29s` |
| `cd frontend && npm.cmd run build` | Passed. Main App chunk: `App-DDVN4kM_.js` 453.31 kB, gzip 109.26 kB. No Vite >500 kB warning emitted. |
| All frontend `check:*` scripts from `frontend/package.json` | Failed: 53 scripts run; 44 passed; 9 failed. |
| `python -m backend.app.tools.project_quality_gate backend/tests/fixtures/projects/minimal_valid_project --json --skip-world-quality-gate` | Passed: `passed: true`, 4 checks, no blockers/errors/warnings. |
| `python -m backend.app.tools.mod_quality_gate backend/tests/fixtures/mods/minimal_valid_action_mod --json` | Passed: `ok: true`, certification `verified_action`, compatibility `compatible`; 2 non-blocking warnings about running local harness action tests before release. |
| `python -m backend.app.tools.v2_release_checklist --json` | Passed: no blockers; warning notes that the checklist invocation itself did not run pytest/build, which were run separately in this review. |
| `$env:PYTHONPATH='backend'; python -m app.tools.compatibility_matrix --json` | Passed: GameState, StateDelta, EventLog, ContentPack, SaveMigration, ModuleManifest, ActionMod, PromptProfile, ProviderGateway, Package, DebugAPI, and QualityGate all compatible. |
| `$env:PYTHONPATH='backend'; python -m app.tools.generate_contract_docs --check` | Passed with exit code 0. |

Failed frontend check scripts:

| Script | Failure |
| --- | --- |
| `check:v30-ux` | Missing v3.0 completion token: Desktop Packaging |
| `check:v36-integration-regression` | Fails because `check-v30-local-studio-ux.mjs` fails |
| `check:v37-novel-workflow` | API-key/transient-key terminology outside safe exclusion copy |
| `check:v37-tavern-workflow` | API-key/transient-key terminology outside safe exclusion copy |
| `check:v37-world-workflow` | API-key/transient-key terminology outside safe exclusion copy |
| `check:v37-cross-mode-workflow` | API-key/transient-key terminology outside safe exclusion copy |
| `check:v37-qa-debug-workflow` | API-key/transient-key terminology outside safe exclusion copy |
| `check:v37-backup-diagnostics-workflow` | API-key/transient-key terminology present |
| `check:v37-privacy-safety-review` | Missing hidden fact display exclusion copy: `no hidden fact text` |

## Final Recommendation

Do **not** declare v3.7 Local Complete Product complete yet.

The project is broadly integrated from v0.1 through v3.6, and the v3.7 product
surfaces are partially implemented, but the v3.7 acceptance path requires all
frontend checks to pass. The current blockers are concentrated in product
readiness copy/static checks, not in backend pytest or production build.

Recommended next steps:

1. Fix the v3.0 Desktop Packaging token regression.
2. Fix v3.7 workflow checklist secret-boundary wording so it remains explicit
   about exclusions without resembling API-key input or transient-key handling
   surfaces.
3. Add the missing hidden-fact exclusion copy to the privacy/safety review UI.
4. Re-run `python -m pytest`, frontend build, and all frontend `check:*`
   scripts.
5. After checks pass, proceed to v3.7 integration regression tests, acceptance
   report, release notes, final freeze, and tag readiness review.

Commit/tag recommendation: do not tag v3.7 yet. The current state should be
treated as **v3.7 integration in progress with release-blocking frontend check
failures**.
