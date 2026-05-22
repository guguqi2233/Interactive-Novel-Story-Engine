# v2.8 Provider / Export / Privacy Audit

## Verification Date

2026-05-23

## Scope

This audit reviews v2.8 provider routing, mature export controls, and privacy boundaries for:

- `ProviderSafetyPolicy`
- mature-aware provider routing
- provider usage records and traces
- Project / Novel / Tavern / Module export filtering
- mature memory and boundary private notes
- frontend secret display
- git-tracked sensitive files
- documentation and test key fixtures
- cloud sync / online mature-content behavior

This is a read-only audit. No code was modified.

## Passed Items

1. **ProviderSafetyPolicy contains content rating constraints.**
   - `ProviderSafetyPolicy` includes `allowed_content_ratings`, `allow_mature_content`, `allow_explicit_adult`, and `require_local_only_for_mature`.
   - `allow_explicit_adult` defaults to false and is validated.

2. **Mature routing does not leak sensitive prompt text.**
   - `ProviderRoutingContext` carries structured `content_rating` and `mature_policy`; it does not need prompt text for mature routing decisions.
   - `ProviderRouter.reject_or_downgrade_by_policy()` returns policy error codes, not prompt excerpts.

3. **Provider usage logs do not record mature text.**
   - `ModelUsageRecord` stores metadata only: provider/model IDs, mode, use case, timing, estimated tokens/cost, success, error type, and request ID.
   - Usage tracking estimates token counts from messages/outputs but does not persist message text or output text.

4. **Provider traces do not record hidden/mature sensitive content in normal usage records.**
   - Usage APIs return `record.safe_dict()` without raw prompts or outputs.
   - Prompt Lab benchmark/reliability tools use redacted prompt previews where previews exist.

5. **Project export excludes mature content by default.**
   - `export_project()` accepts a `MatureExportPolicy`, defaulting to normal mode.
   - Normal export skips mature-only and mature scene material.

6. **Novel export excludes mature notes by default.**
   - `NovelExportRequest.include_mature_content` defaults false.
   - `NovelExportService.export()` applies `MatureExportFilter` before returning export text.

7. **Tavern export / project Tavern section excludes mature memory/messages by default.**
   - Tavern memory is exported through project/package export paths.
   - `mature_only` memory records are filtered by default.
   - Tests confirm mature Tavern memory files are absent from normal project export.

8. **Module export excludes mature content by default.**
   - `ModImportExportService.export_package()` defaults to `MatureExportPolicy()`.
   - Mature-only package files and mature package content are skipped unless explicit mature export policy allows them.

9. **Boundary private notes do not enter normal export.**
   - `MatureExportPolicy.include_boundary_private_notes=false` by default.
   - The policy validator only permits boundary private notes in explicit authoring/debug export modes.
   - `MatureExportFilter` removes private notes / private persona fields.

10. **API keys do not enter export by default.**
    - `MatureExportFilter` removes `api_key`, `llm_api_key`, `openai_api_key`, `authorization`, `x-api-key`, raw env, raw prompts, and debug memory keys.
    - Provider Profile Pack still permits `api_key_env` / `secret_ref` placeholders, not real keys.

11. **`.env` is not tracked by git.**
    - `git ls-files .env "*.env" "*.db" "*.sqlite" "*.sqlite3" "*.log" "logs/*" "frontend/dist/*" "node_modules/*"` returned no tracked sensitive/runtime artifacts.

12. **Docs/tests do not appear to contain real keys.**
    - `sk-...` search hits are confined to tests and historical audit docs as explicit fake/redaction fixtures, such as `sk-test-*`, `sk-real-looking-*`, and `sk-real-not-allowed-*`.
    - These are used to verify redaction and rejection behavior.

13. **Frontend does not display secrets by design.**
    - Frontend provider and privacy UI uses `api_key_configured` booleans, `api_key_env`, and `secret_ref` placeholders.
    - Mature settings UI states it does not display mature memory bodies, API keys, raw env, hidden facts, or provider secrets.

14. **Debug export requires explicit mode/flag.**
    - `MatureExportPolicy` validates that `export_mode="debug"` requires `include_debug=True`.
    - Boundary private notes require authoring/debug mode, not normal mode.

15. **No cloud sync of mature content is implemented.**
    - v2.8 remains local-first.
    - Mature Module is default-off and not an online content platform.
    - No cloud sync API or remote mature package marketplace path was found in v2.8 scope.

## High-Risk Issues

No high-risk provider/export/privacy blocker was found.

No inspected path currently:

- persists raw mature prompt text in provider usage records;
- exports mature memory by default;
- exports boundary private notes in normal mode;
- exposes API keys in frontend normal UI;
- tracks `.env` or database/log/build artifacts in git;
- enables mature cloud sync or online mature content platform behavior.

## Medium-Risk Issues

1. **Provider traces outside `ModelUsageRecord` require continued discipline.**
   - Usage tracking itself is safe, but other future debug/trace features must keep using redacted previews and avoid raw prompt persistence.

2. **Tavern export is covered via project export, not a standalone Tavern export service.**
   - This is acceptable for the current implementation.
   - If a dedicated Tavern export endpoint is later added, it must reuse `MatureExportPolicy` and `MatureExportFilter`.

3. **Mature export can be enabled explicitly.**
   - Explicit export is intended, but final release docs/UI should keep warning that explicit mature export still filters secrets and should remain local.

4. **Provider policy is locally declared.**
   - The router enforces local `ProviderSafetyPolicy`; it does not verify an external provider's real-world content policy.
   - This must remain documented as local configuration, not a guarantee from any third-party provider.

## Low-Risk Issues

1. **Vite build artifact exists after frontend build but is not tracked.**
   - `frontend/dist` is generated during build and should remain untracked.

2. **Historical docs mention fake keys.**
   - Existing security/audit docs include fake key examples for redaction verification.
   - They are not production credentials.

3. **Usage token counts are estimates.**
   - Cost/token tracking remains estimate-only and not billing-grade.

## Fix Recommendations

Before v2.8 final release:

1. Add or keep release-readiness checks that confirm no tracked `.env`, database, log, cache, `frontend/dist`, or `node_modules` files.
2. If a dedicated Tavern export API is added, route it through `MatureExportPolicy`.
3. Keep provider usage/tracing APIs metadata-only in normal mode.
4. Keep mature provider routing explanations as structured codes, not prompt excerpts.
5. Keep docs explicit that ProviderSafetyPolicy is local configuration and mature export is explicit/local-only.

## v2.8 Release Blocker Assessment

**Does this block v2.8 release?**

No. The provider/export/privacy implementation is acceptable for v2.8 release readiness.

The medium-risk items are future hardening / documentation priorities, not current blockers, provided final release checks continue to verify:

- `python -m pytest` passes;
- frontend build passes;
- `.env`, databases, logs, caches, `frontend/dist`, and `node_modules` are not tracked;
- no real API key is present;
- normal exports exclude mature content, mature memory, boundary private notes, debug memory, raw prompts, raw env, and provider secrets.
