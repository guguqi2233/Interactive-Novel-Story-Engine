# v3.7 Chinese UI Privacy / Visibility Audit

Verification Date: 2026-05-25

Scope: v3.7 Local Playable Complete Product CN frontend surfaces, demo project,
and Chinese product guidance related to Home, Provider, Novel, Tavern, World,
Debug / Replay, Backup, Diagnostics, and accessibility labels.

This is a read-only privacy and visibility audit. No business code, tests, or
runtime data were changed for this report.

## Passed Items

1. Home does not render API key values.
   - The Chinese Home surfaces only safe status and guidance that API keys are
     not stored in the project and are not displayed in the UI.
   - No secret-looking key values were found in the Home source slice.

2. Home does not render hidden facts.
   - Home copy explicitly states that normal UI excludes hidden facts, NPC
     secrets, debug memory, and raw state change details.
   - Product readiness summaries are safe summaries only.

3. Home does not render raw state_deltas.
   - Raw StateDelta rendering exists only in debug-oriented components.
   - Home surfaces only safe summaries and high-level readiness/status text.

4. Chinese aria-labels do not contain secrets.
   - aria-label usage was reviewed for known secret terms and secret-like
     values. Labels contain feature names, safe summaries, or static guidance,
     not actual key values.
   - The transient API key field is a password input with `autoComplete="off"`
     and a static label; it does not embed the typed value in aria text.

5. Provider UI does not display saved API key values.
   - Provider setup uses `api_key_env`, `secret_ref`, `local_secret_ref`, or a
     one-time `transient_api_key` flow.
   - Provider profile forms and dashboards show configured/not shown style
     status, not actual key values.
   - Saved secret values and Authorization headers are not rendered.

6. ErrorState Chinese copy is redacted.
   - Error and disabled state copy says stack traces, raw env, sensitive paths,
     API keys, hidden facts, NPC secrets, debug memory, and raw state_deltas
     are not shown.
   - Error formatting includes stack trace redaction and key-like text
     sanitization.

7. Demo project does not contain secrets.
   - `examples/demo_local_narrative_project` uses `local_stub` provider
     metadata and explicit safe flags: `export_secrets: false`,
     `allow_debug_exports: false`, `allow_mature_content: false`, and
     `contains_secrets: false`.
   - No real API key pattern was found in the demo project scan.

8. Novel / Tavern / World normal UI still filters hidden/debug data.
   - Novel normal UI excludes API keys, hidden facts, private notes, raw
     prompts, and raw state_deltas.
   - Tavern normal UI excludes API keys, hidden facts, NPC secrets,
     mature/private memory, private persona, raw prompts, and raw state_deltas.
   - World normal UI uses visible_state safe summaries and excludes hidden
     facts, NPC secrets, raw state_deltas, raw env, and provider secrets.

9. Debug is hidden by default.
   - Debug / Replay is placed under Advanced Tools and `debugOpen` defaults to
     false.
   - Home does not default-render the Debug / Replay drawer.

10. Debug remains gated.
    - Debug panels use `DebugGate` and `ENABLE_DEBUG_API` messaging.
    - StateDelta Viewer, raw EventLog details, Timeline debug details, Visible
      vs Debug Compare, and Safe Debug Export remain debug-gated.

11. Mature/private data remains hidden by default.
    - Mature module UI and docs state default-off behavior.
    - Tavern RP memory, export, backup, and diagnostics copy continues to
      exclude mature/private content by default.

12. Backup / Diagnostics Chinese copy accurately describes filtering.
    - Backup/Diagnostics UI states that `.env`, API keys, provider secrets,
      raw env, debug raw data, mature/private content, databases, logs, caches,
      and build outputs are excluded by default.
    - Diagnostics copy says preview/create is local-only and not uploaded.

## High-risk Issues

None found.

No release-blocking privacy or visibility regression was identified in the
Chinese v3.7 product UI. The reviewed surfaces do not expose real API keys,
hidden facts, NPC secrets, raw state_deltas, raw env, stack traces, or
mature/private content in normal UI.

## Medium-risk Issues

None currently blocking release.

Notes:

1. Provider setup intentionally supports a transient key entry for a manual
   user-triggered connection test. This is acceptable because it is a password
   field, uses `autoComplete="off"`, is not saved to ProviderProfile, and is not
   written to local/session storage. Keep this path covered by regression tests.

2. Raw StateDelta / EventLog debug rendering still exists in source code, as
   expected, but is wrapped by debug-gated UI. Future refactors should keep
   static checks focused on preventing these components from moving into Home or
   normal mode routes.

## Non-blocking Follow-ups

1. Continue expanding automated checks for Chinese aria-label safety, especially
   around future icon-only buttons and Provider status badges.

2. Keep demo project secret scanning in release checklists so `local_stub`
   remains safe and no future example accidentally introduces key-like data.

3. Some advanced Provider wizard strings appeared encoded inconsistently in the
   source review output. This is not a privacy leak, but it should be polished
   before final UX sign-off if it appears in the rendered UI.

4. Maintain a dedicated Home check that verifies Debug / Replay panels, raw
   state_deltas, raw EventLog JSON, and Product Readiness full checklist do not
   appear in the default player/creator Home.

## Release Decision

Pass for v3.7 Chinese UI privacy / visibility.

The v3.7 Chinese Local Playable Complete Product UI remains aligned with the
local-first privacy model:

- API keys are not rendered as values.
- Provider secrets are represented only as safe metadata or local references.
- Hidden facts, NPC secrets, raw state_deltas, debug memory, raw prompts, raw
  outputs, and mature/private content stay out of normal UI.
- Debug / Replay remains hidden by default and gated by `ENABLE_DEBUG_API`.
- Backup and Diagnostics Chinese copy correctly describes local-only,
  preview-first, redacted behavior.

No high-risk release blocker was found.
