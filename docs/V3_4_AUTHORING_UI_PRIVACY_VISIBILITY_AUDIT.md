# v3.4 Authoring UI Privacy / Visibility Audit

Verification date: 2026-05-24

Scope reviewed:
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/scripts/check-v34-authoring-ui.mjs`
- `backend/tests/test_v34_integration_regression.py`
- v3.4 roadmap and contract review docs

This audit is read-only for business code. It reviews whether Authoring / Mod UI
normal views, previews, reports, import/export surfaces, and debug-adjacent
panels can expose hidden facts, NPC secrets, raw state deltas, provider secrets,
API keys, sensitive paths, or online/remote package entry points.

## Passed Items

1. API keys are not shown as plaintext frontend fields.
   - `check-v34-authoring-ui.mjs` fails on `<input name="api_key">` and
     literal `api_key` assignments.
   - Provider UI copy consistently points users to `api_key_env` or
     `secret_ref`.

2. Import / Export UI states the correct filtering policy.
   - The v3.4 Import / Export Wizard excludes `.env`, API keys, provider
     secrets, database files, logs/cache, `node_modules/dist`, debug reports,
     and mature/private content by default.
   - Provider Profile Pack export copy allows only `api_key_env` or
     `secret_ref`.

3. Debug details are gated.
   - Raw `event.state_deltas` rendering in the main app is inside `DebugGate`.
   - Debug copy explicitly mentions `ENABLE_DEBUG_API`.

4. Error messages are redacted before display.
   - `extractErrorInfo` and `redactSensitiveText` redact `sk-*`, auth headers,
     key/secret/token/password patterns, Windows paths, sensitive Unix-style
     paths, hidden-fact labels, raw prompt labels, state-delta labels, and stack
     traces.

5. Module UI is local-only and non-executing.
   - Module Browser, Permission Dashboard, Compatibility Matrix,
     Certification, Rule Module Contract UI, and Mod Quality Gate repeatedly
     state local-only, no package execution, no online marketplace, and no
     remote download.

6. Audit UI uses safe summaries.
   - Authoring Audit Trail renders `safe_summary`, actor, action type, entity,
     result, and risk level.
   - It does not render raw EventLog or raw `state_deltas`.

7. Recent v3.4 integration regression covers privacy boundaries.
   - Character Pack import dry-run no longer returns `private_notes` text in the
     tested response.
   - Provider Profile Pack rejects raw `api_key`.
   - Import dry-run blocks secret-containing archives without echoing the fake
     key.
   - Active `GameState` is unchanged by authoring dry-runs.

8. No positive online marketplace / remote download entry was found.
   - The reviewed UI uses these phrases only as explicit negative/local-first
     boundary copy.

## High-Risk UI Leaks

1. Authoring preview panels can display raw YAML / preview content in normal
   authoring UI.
   - `PreviewResultPanel` renders `previewContent` inside `<pre>`.
   - Multiple authoring panels pass backend `yaml_content` or `yaml_contents`
     into preview displays, including map/location, quest graph, NPC goals,
     item/economy, rumor/crime, faction/relationship, and some template flows.
   - This is an authoring surface rather than player preview, but the current
     checklist asks whether Authoring normal UI shows hidden facts in full. Raw
     YAML previews can include hidden objectives, hidden truth, witness data,
     hidden item properties, or authoring-only NPC fields when the draft
     contains them.
   - Impact: hidden/authoring-only text may be visible without a distinct
     gated "authoring-only raw preview" boundary.

2. Validation issue rows may render backend issue strings directly.
   - Several UI paths map `validation.errors`, `validation.warnings`, module
     errors, quality blockers, and compatibility errors directly into visible
     rows.
   - Backend validators often use safe summaries, and recent tests cover
     specific leaks, but the UI does not add a second redaction layer for all
     validation/report strings.
   - Impact: if a validator includes a hidden text excerpt in an issue message,
     normal Authoring UI can show it.

## Medium-Risk UI Leaks

1. Player preview and authoring preview are not visually separated everywhere.
   - The roadmap distinguishes player-visible preview from authoring-only
     hidden sections, but several current panels present generic "Preview" or
     YAML preview language.
   - Risk: users may confuse raw authoring preview with player-safe preview.

2. Action Mod Editor includes a "Hidden facts" field.
   - The editor is declarative authoring, not player preview.
   - However, the field label can invite entering hidden fact ids/text without a
     nearby warning that full hidden text should not be used.

3. Module quality/certification blockers are rendered directly.
   - Current module browser services redact manifest data, secret-looking text,
     and unsafe paths in many paths.
   - The UI still trusts returned blocker/warning strings.

4. `safe_path_hint` is displayed as a safe path summary.
   - Current service uses package directory names, which is acceptable.
   - Future backend changes should preserve this invariant and never return full
     sensitive paths through `safe_path_hint`.

## Minor Issues

1. Negative online-marketplace copy appears frequently.
   - This is good for policy clarity, but broad string scans may flag it unless
     they distinguish negative copy from feature entry points.

2. Some panel copy says raw YAML is "not shown here" while adjacent editor flows
   can still show YAML previews.
   - This is a clarity mismatch more than a confirmed leak.

3. v3.4 has a regression check script but no dedicated privacy audit check yet.
   - `check-v34-authoring-ui` catches major token-level issues, not all preview
     content pathways.

## Fix Recommendations

1. Add a shared `AuthoringSafePreviewPanel`.
   - Default view should show changed entity counts, section names, ids, and
     safe summaries only.
   - Raw YAML/full draft content should be behind an explicit
     `AuthoringOnlyDetails` disclosure with warning text.

2. Add frontend redaction before rendering validation/report strings.
   - Reuse or export `redactSensitiveText` for validation issues, quality
     blockers, compatibility errors, module scan errors, and audit summaries.
   - Redact hidden-fact labels plus adjacent values, `npc secrets`, raw
     `state_deltas`, local paths, and key/secret/token patterns.

3. Separate "player-visible preview" from "authoring-only draft preview".
   - Player preview must never include hidden facts, NPC secrets, hidden
     objectives/truth, hidden witness data, or hidden item properties.
   - Authoring-only preview should be collapsed by default and clearly labeled.

4. Harden backend issue messages.
   - Validators should report ids, file names, paths, issue codes, and safe
     summaries, not full hidden/private text.
   - Add tests for quest, rumor/crime, item/economy, NPC/social, and module
     validators to ensure issue messages do not echo hidden text.

5. Extend `check-v34-authoring-ui`.
   - Check that raw YAML preview components are paired with authoring-only
     warning/disclosure copy.
   - Check that validation/report rendering paths call a redaction helper.

## Release Blocking Assessment

Blocking for v3.4 release: Yes.

Reason:
- The current UI generally respects local-first, no-secret, no-online, and
  debug-gated boundaries.
- However, raw YAML / preview content and direct validation/report issue
  rendering can expose hidden or authoring-only text in normal Authoring UI.
  This conflicts with the requested v3.4 privacy/visibility checklist.

Recommended release condition:
- Do not tag v3.4 until raw authoring previews are separated from player-safe
  previews, raw/full draft content is collapsed behind an explicit
  authoring-only disclosure, and validation/report strings are redacted before
  rendering.
