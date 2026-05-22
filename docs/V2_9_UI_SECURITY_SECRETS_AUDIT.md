# v2.9 UI Security / Secrets Audit

## Verdict

Pass with no release-blocking UI security or secrets issue found.

This audit reviewed the v2.9 frontend shell, Provider setup UI, API client error handling, diagnostics export UI, static UI safety check, and v2.9 UI regression tests. The reviewed UI remains local-first, does not add account/cloud/marketplace flows, does not accept plaintext API keys, and does not export secrets by default.

## Scope Reviewed

- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/scripts/check-v29-ui-safety.mjs`
- `backend/tests/test_v29_ui_regression.py`
- `docs/V2_9_UI_PRIVACY_VISIBILITY_AUDIT.md`

## Passed Items

1. **Provider setup plaintext key input**
   - Provider setup exposes `api_key_env` and `secret_ref` only.
   - No `<input name="api_key">` or literal plaintext `api_key` field was found.
   - UI copy explicitly says there is no plaintext API key field.

2. **Frontend secret caching**
   - No `localStorage` or `sessionStorage` usage was found in `frontend/src`.
   - Provider form state stores only `api_key_env` and `secret_ref` references, not secret values.
   - No frontend cache or persistence layer for secrets was found.

3. **`api.ts` secret logging**
   - `api.ts` contains no `console.log`, `console.error`, or equivalent logging of request/response payloads.
   - API wrappers preserve route contracts and return parsed data; they do not log secrets.

4. **Console logging**
   - The only console usage found in the v2.9 frontend check script prints static check failures/success.
   - No frontend runtime console logging of provider profiles, API errors, Authorization headers, diagnostics payloads, or secrets was found.

5. **Authorization header redaction**
   - `api.ts` redacts `Authorization` / bearer-like fragments in `getErrorMessageSafe`.
   - `App.tsx` `sanitizeDisplayError` also redacts authorization-like fragments before rendering errors.

6. **Diagnostics export and `.env`**
   - Diagnostics export default filter list explicitly includes `.env`.
   - The generated diagnostics preview uses safe summaries and an `api_key_status: "[redacted]"` field.
   - It does not include raw environment values.

7. **Diagnostics export and provider secrets**
   - Diagnostics export includes provider status/type summaries only.
   - Provider secrets are represented as redacted status and listed in the filter summary.
   - Provider profile bodies with secrets are not exported by the v2.9 diagnostics panel.

8. **Project/export UI default secret filtering**
   - Settings / Privacy and Project Home state that exports filter secrets.
   - Existing export copy states `.env`, API keys, logs, cache, `node_modules`, and `dist` are excluded.
   - No upload behavior was introduced.

9. **Local path exposure**
   - Error formatters redact Windows local paths and common sensitive path fragments.
   - UI copy favors safe summaries.
   - Residual path-like fields such as `safe_path_hint` remain a backend contract responsibility and are not considered a confirmed leak.

10. **Remote package download entry**
    - Module Browser copy says no remote auto-download.
    - No remote package download workflow or button was found.

11. **Online marketplace entry**
    - UI copy says "No online marketplace."
    - `check:v29-ui` blocks account/cloud/marketplace primary entries.

12. **Cloud sync entry**
    - Project Home, Help, and navigation copy say no cloud sync.
    - No cloud sync button or settings entry was found.

13. **Account entry**
    - Help/navigation copy says no account.
    - No account/login/signup entry was found.

14. **Mature content export default**
    - Mature settings show mature export as default off.
    - Diagnostics and privacy notices list mature/private content as filtered by default.

15. **Debug export confirmation**
    - Diagnostics debug export requires both `includeDebug` and explicit confirmation.
    - Debug export is disabled unless `ENABLE_DEBUG_API` is enabled.

## High-Risk Issues

None found.

No evidence was found that the v2.9 frontend accepts plaintext API keys, stores secrets, logs secrets, exports `.env`, exposes provider secrets, or adds online/account/cloud/marketplace flows.

## Medium-Risk Issues

None blocking.

Residual non-blocking concerns:

- `api_key_env` and `secret_ref` are kept in React form state while editing provider profiles. These are references rather than secret values, but future copy should keep this distinction clear.
- `safe_path_hint` and other backend-provided safe path summaries should continue to be treated as display-only hints, never raw full paths.
- Diagnostics export is frontend-only safe JSON today. If a backend diagnostics export API is added later, it must repeat the same filtering rules server-side.

## Low-Risk Issues

- Debug panels remain present in the shell and may be visually prominent, although gated by backend capability. Future UI polish can collapse them by default.
- The static UI check is intentionally lightweight. It catches common regressions but is not a replacement for manual release audits.
- Generic `SafeJSON` remains useful for redacted previews, but normal UI should prefer purpose-built safe summaries.

## Recommendations

1. Keep `npm.cmd run check:v29-ui` and `backend/tests/test_v29_ui_regression.py` in the v2.9 release checklist.
2. Do not add any plaintext API key field in future Provider setup flows.
3. Keep diagnostics export local-only and safe-summary-only unless a future backend export path implements equivalent filtering.
4. Continue blocking account/cloud/marketplace/remote-download UI entries for v2.9-v3.6 unless a later roadmap explicitly changes scope.
5. Add a future regression check for full-path rendering if more local path fields are introduced.

## Release Blocking Assessment

Not blocking v2.9 release.

The reviewed implementation preserves local-first secret handling, avoids plaintext API key capture, redacts sensitive error text, keeps diagnostics/export safe by default, and does not introduce onlineization entry points.
