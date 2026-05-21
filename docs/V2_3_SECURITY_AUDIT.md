# v2.3 Security / Session Export Audit

## Verdict

PASS.

v2.3 Tavern Studio MVP adds local authoring/studio Tavern APIs, repository
storage, character card import, chat generation, proposals, and adapter flows.
The review found no high-risk security issue and no release-blocking secret,
artifact, script execution, real-provider test call, or Tavern session export
leak.

## Verification Date

2026-05-22

## Scope Reviewed

- `backend/app/main.py`
- `backend/app/platform/tavern_studio.py`
- `backend/app/platform/security.py`
- `backend/app/config.py`
- `backend/app/evals/tavern_boundary.py`
- `backend/tests/test_v23_tavern_studio_mvp.py`
- `backend/tests/test_v23_integration_regression.py`
- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- git tracked-file scan
- secret-pattern scan

## Checks Performed

- Tavern route gating search for `require_authoring_api`.
- Tavern repository path and secret-handling review.
- Character card import parsing and safety review.
- Tavern response generation provider/test review.
- Tavern frontend API and rendering review.
- Tracked artifact scan for `.env`, databases, logs, caches, `node_modules`,
  `frontend/dist`, desktop outputs, backups, and crash reports.
- Secret scan for real-looking `sk-...` keys and private key markers.

## Passed Items

1. Tavern API is gated by local authoring/studio configuration.
   - Tavern routes under `/projects/{project_id}/tavern/...` call
     `require_authoring_api()`.
   - `require_authoring_api()` returns HTTP 403 when authoring API is disabled.

2. `TavernRepository` rejects path traversal.
   - Section paths are validated with `validate_project_relative_path`.
   - Item ids are constrained by `_safe_id`.
   - `_dir()` resolves paths and rejects escapes outside `project_root`.

3. Character card import does not execute scripts.
   - `CharacterCardImportService` parses JSON or YAML with `yaml.safe_load`.
   - Imported prompt-like text is treated as data only.
   - No card content is executed, imported as code, or evaluated.

4. Character card import rejects API keys/secrets.
   - `ImportedCharacterCard` validates with `contains_secret_text`.
   - `TavernRepository._write_yaml()` refuses to persist Tavern data containing
     secret-like text.

5. Tavern session export surface.
   - v2.3 does not add a Tavern session export endpoint.
   - Existing legacy Tavern compatibility export is under authoring routes and
     remains gated by `require_authoring_api()`.
   - No new Tavern export path was found that could include `.env`, API keys,
     provider secrets, debug memory, raw `state_deltas`, private persona, or
     authoring notes.

6. Tavern data storage rejects secret-like payloads.
   - Repository writes check the serialized model payload with
     `contains_secret_text`.
   - Repository reads are limited to expected `*.yaml` files inside Tavern
     section directories and skip `.env`-prefixed files in `_read_all`.

7. Provider profiles and prompt profiles do not introduce real keys in v2.3.
   - Tavern code uses provider/profile refs and safe summaries.
   - Prompt profile integration rejects unsafe permissions and does not store
     secrets.

8. Response generation tests do not call real APIs.
   - v2.3 tests use `FakeLLMProvider`.
   - Tavern chat API supports an app-state test provider and replaces the local
     `MockLLMProvider` default with deterministic fake output for local stub
     behavior.

9. Frontend does not store API keys.
   - v2.3 Tavern frontend only calls backend Tavern APIs and renders safe
     summaries.
   - No new frontend code stores or requests provider secrets.

10. Settings/config summaries do not return raw env.
    - Existing local config and desktop summaries report configured/not
      configured status and redact raw env/secrets.
    - Tavern frontend displays "no API keys, hidden facts, or raw env" guidance
      and does not render raw config.

11. Player API raw `state_deltas` are not exposed by Tavern changes.
    - Tavern APIs are authoring/studio routes, not player APIs.
    - Tavern prompt/context code rejects raw `state_delta` material.

12. Debug API and authoring API controls remain in place.
    - Debug APIs remain under `ENABLE_DEBUG_API`.
    - Tavern APIs are authoring-gated under `ENABLE_AUTHORING_API` / local
      authoring configuration.

13. Tracked artifact scan passed.
    - The scan found `.env.example` and `frontend/.env.example`, which are
      allowed placeholder/example files.
    - No tracked `.env`, database, log, cache, `node_modules`, `frontend/dist`,
      desktop output, backup, or crash report artifact was identified.

14. Secret scan found no confirmed real API key.
    - Hits are fake/test placeholders and documented redaction fixtures, such
      as `sk-test-*`, `sk-real-looking-*`, and `sk-live-secret1234567890` in
      tests or prior security audit docs.
    - These are intentionally used to verify redaction and should not be treated
      as real credentials.

15. Tavern Safety Evals are local and deterministic.
    - `backend/app/evals/tavern_boundary.py` does not use an external LLM judge.
    - It checks known leak classes and redacts normal report details.

## High-Risk Issues

None found.

## Medium-Risk Issues

None blocking.

Watch item: v2.3 currently has no dedicated Tavern session export endpoint. If
one is added later, it must use the project/package export safety filters and
must explicitly exclude `.env`, API keys, provider secrets, debug memory, raw
`state_deltas`, private persona, authoring notes, logs, caches, databases, and
build artifacts.

## Low-Risk Issues

1. Secret scan output includes intentionally fake secret-like strings in tests
   and historical audit docs. This is acceptable, but release checklists should
   continue distinguishing fake fixtures from real credentials.
2. `yaml.safe_load` is safe for script execution, but imported card content can
   still contain prompt-like injection text. v2.3 warns on forbidden permission
   markers and keeps prompt-like text out of prompt-safe fields.
3. Tavern repository stores YAML files locally under project roots. Future
   export/import features should add checksum/manifest coverage if Tavern
   sessions become packageable.

## Recommendations

1. Keep Tavern APIs authoring-gated and local-only.
2. Do not add Tavern session export without an explicit safe export policy and
   tests for `.env`, API key, provider secret, debug memory, raw `state_deltas`,
   private persona, and authoring note exclusion.
3. Keep tests on fake/mock/local providers only.
4. Continue running tracked artifact and secret scans before v2.3 release.
5. Keep distinguishing allowed `.env.example` placeholders and fake test keys
   from real secrets.

## Release Impact

This audit does not block v2.3 release.

Final status: PASS.
