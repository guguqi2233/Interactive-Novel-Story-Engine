# v3.7 Local Complete Product Privacy Audit

Verification date: 2026-05-25

## Audit Basis

This is a read-only privacy audit for the v3.7 Local Complete Product phase. It
reviewed the current v3.7 integration report, the v3.7 security audit,
local-first product documentation, workspace/recent-project handling,
backup/restore, diagnostics, logs, Provider cache, project export, Novel export,
Tavern export, mature/private filtering, and frontend product privacy copy.

This audit did not modify business code or tests. The current integration
baseline from `docs/V3_7_FULL_INTEGRATION_REVIEW.md` is:

- `python -m pytest`: passed, `1795 passed in 136.29s`.
- `cd frontend && npm.cmd run build`: passed.
- v2 release checklist: passed, no real API key pattern found.
- all frontend `check:*` scripts are not yet passing; v3.7 privacy/product copy
  checks still include release-blocking failures.

## Passed Items

1. **Local-first posture is preserved.**
   - README, `.env.example`, v3.7 roadmap, Product Tour, Product Readiness,
     Settings, Status/Health, Backup/Diagnostics, Export, and Product
     Acceptance copy all describe local-first behavior.
   - Product surfaces repeatedly state that data is not uploaded by default and
     that Provider use is user-configured, local metadata-driven, or mock /
     local_stub for tests.

2. **No account system is presented as implemented.**
   - Product copy states no account requirement.
   - Settings copy explicitly avoids account settings.
   - `.env.example` does not introduce account configuration.

3. **No cloud sync is presented as implemented.**
   - Product copy and README repeatedly state no cloud sync.
   - Backup/restore and diagnostics flows are local-only and do not describe
     cloud backup or remote sync.

4. **No online marketplace is presented as implemented.**
   - Authoring/Mod and product navigation copy explicitly state no online
     marketplace, no remote package download, and no package execution.
   - Content pack docs and roadmap keep marketplace/remote registry behavior
     outside v3.7 scope.

5. **No telemetry upload is present in the reviewed product path.**
   - README and `.env.example` state no telemetry upload.
   - performance, usage, writing session, diagnostics, QA, and acceptance UI
     copy describes local metadata only.

6. **Project export filters secrets and sensitive content.**
   - `export_project()` requires debug export to be explicitly requested.
   - project package export skips files containing secret-like text.
   - mature/private content is excluded unless the mature export policy allows
     it.
   - Cross-Mode raw debug material such as raw state deltas or debug memory is
     skipped in normal export.
   - import apply requires `confirm_apply` and validates paths/checksums before
     writing.

7. **Novel export filters hidden/mature/private/debug/secret content.**
   - Novel export only selects normal-visibility chapters/scenes.
   - consistency checks block export when blocker findings exist.
   - `MatureExportFilter` is applied before writing.
   - export rejects secret-like text and state-delta markers.

8. **Tavern export filters hidden/mature/private/debug/secret content.**
   - Tavern export policy lists API key, hidden facts, NPC secrets,
     mature/private by default, and debug data exclusions.
   - preview uses safe message summaries.
   - create requires `explicit_confirm`.
   - create rejects secret-like text, key-like text, and state-delta markers.
   - mature/private and debug inclusion are controlled through explicit request
     flags and `MatureExportPolicy`.

9. **World and normal QA/export surfaces keep hidden/debug data out by default.**
   - frontend World, QA, Product Acceptance, and Export copy states that normal
     UI/export excludes hidden facts, NPC secrets, debug memory, raw prompts,
     raw outputs, and raw `state_deltas`.
   - backend playtesting invariants check for raw `state_deltas` in player
     visible payloads.

10. **Backup filters secrets by default.**
    - backup plans are dry-run by default.
    - backup create requires `explicit_confirm`.
    - default exclusions include `.env`, API key, provider secrets, logs,
      cache, `node_modules`, `frontend/dist`, desktop build outputs, databases,
      debug-only data, and mature/private content.
    - backup target paths must stay inside the local workspace and reject
      disallowed path components.

11. **Diagnostics filter secrets by default.**
    - diagnostics preview writes no file.
    - diagnostics excluded sections include `.env`, API key, provider secrets,
      raw env, raw prompt/output, hidden facts, NPC secrets, debug memory, raw
      `state_deltas`, mature/private content, database files, and full save
      files.
    - diagnostics bundle validation rejects sensitive text after desktop and
      provider redaction.
    - debug diagnostics require `include_debug`, explicit debug confirmation,
      and enabled debug API.

12. **Logs are redacted and path-limited.**
    - `LocalLogService` reads only `.log` files directly under the local
      `logs` directory.
    - log lines are passed through desktop secret redaction and Provider
      redaction before they are returned.
    - debug logs require enabled debug API.

13. **Provider cache does not save secrets.**
    - `ProviderConnectionStatusCache` stores only provider id, status,
      tested time, latency, safe error type, model count, and redaction flag.
    - cache documentation explicitly excludes raw provider responses, raw error
      bodies, env values, Authorization headers, API keys, transient keys,
      ProviderProfile secret values, and safe message text.

14. **Recent Projects stores safe summaries only.**
    - recent project entries store workspace id, display name, redacted path,
      last opened time, last world id, and safe status.
    - raw paths, env values, API keys, and GameState are explicitly excluded.
    - `_ensure_safe_recent_entry()` rejects entries containing key/env markers.

15. **Local paths are summarized rather than exposed wholesale in local studio
    APIs.**
    - workspace paths use `path_redacted`.
    - backup and diagnostics outputs return safe path summaries such as
      shortened `.../dir/file` forms.
    - workspace path validation rejects `.env`, `node_modules`, path traversal,
      unsafe generated workspace locations, and environment-file targets.

16. **Mature/private is default-off and default-excluded.**
    - `MatureExportPolicy` defaults `include_mature_content`,
      `include_mature_memory`, `include_boundary_private_notes`, and
      `include_debug` to false.
    - mature memory requires mature content to be explicitly included.
    - boundary private notes require authoring or debug export mode.
    - backup, diagnostics, Novel export, Tavern export, and project export keep
      mature/private excluded by default.

17. **Debug data is default-excluded.**
    - debug export mode requires explicit debug inclusion.
    - diagnostics include debug only when debug is requested, explicitly
      confirmed, and debug API is enabled.
    - backup excludes debug-only data by default.
    - Safe Debug Export UI is gated by `ENABLE_DEBUG_API` and explicit confirm.

## High-risk Privacy Issues

None found in the reviewed privacy boundaries.

No evidence was found of account/cloud/marketplace enablement, telemetry upload,
raw API key export, raw Provider secret cache storage, unredacted diagnostics,
unredacted logs, Recent Projects secret storage, mature/private default export,
or debug data default export.

## Medium-risk Issues

1. **v3.7 privacy/safety frontend check currently fails.**
   - `check:v37-privacy-safety-review` reports missing hidden fact display
     exclusion copy: `no hidden fact text`.
   - The underlying privacy boundary is documented and older visibility/backend
     checks pass, but v3.7's product-level privacy UI must make this exclusion
     explicit before release.

2. **Several v3.7 workflow checks fail on secret-boundary wording.**
   - Novel, Tavern, World, Cross-Mode, QA/Debug, and Backup/Diagnostics
     workflow checks flag API-key or transient-key terminology outside the
     scripts' expected safe exclusion wording.
   - This does not prove a privacy leak, but it is a product privacy release
     blocker because v3.7 requires all frontend checks to pass.

3. **v3.0 Desktop Packaging token regression remains relevant to privacy
   release hygiene.**
   - `check:v30-ux` currently fails due missing "Desktop Packaging" token.
   - Desktop packaging docs and policy still contain strict exclusions, but the
     product UI/static check should again expose that boundary clearly.

4. **Privacy guarantees rely on continued safe-summary discipline in frontend
   product copy and check scripts.**
   - The current frontend contains many explicit privacy exclusions. Future text
     changes can still accidentally trip check scripts or create ambiguous
     wording if not reviewed.

## Non-blocking Follow-ups

- Add a targeted v3.7 privacy fixture that snapshots Product Privacy/Safety
  Review output and asserts no hidden text, raw prompt/output, raw env, API key,
  Provider secret, mature/private body, or raw `state_deltas` appear.
- Add a small test for Recent Projects serialization to ensure redacted path
  summaries remain free of `.env`, `sk-`, `api_key`, raw env, and full
  GameState markers.
- Add a Provider cache file-content test that fails on `safe_message`,
  Authorization, raw provider response, raw error body, API key, and
  transient-key markers.
- Add docs/check-script guidance for allowed privacy exclusion wording so v3.7
  workflow copy remains explicit without resembling a plaintext secret input.
- Continue browser-level smoke testing for diagnostics preview, backup preview,
  export preview, privacy review, and Safe Debug Export disabled/enabled states.

## Release Decision

Privacy-specific verdict: **No high-risk privacy issue found.**

v3.7 release verdict: **Not ready for final v3.7 release acceptance yet.**

Reason: current v3.7 frontend product checks still fail on privacy/safety copy
and secret-boundary wording. These findings are not confirmed raw data leaks,
but they are release-blocking for Local Complete Product because the product UI
must clearly communicate hidden-data exclusion and secret handling before final
acceptance.

Recommended next step:

1. Add the missing `no hidden fact text` privacy exclusion wording in the
   v3.7 privacy/safety review UI.
2. Rewrite v3.7 workflow checklist secret-boundary copy so it remains explicit
   about exclusion/redaction without resembling key-entry or transient-key
   persistence.
3. Restore the v3.0 Desktop Packaging completion token or equivalent safe
   product boundary wording.
4. Re-run all frontend `check:*` scripts, frontend build, and `python -m pytest`
   before v3.7 acceptance.
