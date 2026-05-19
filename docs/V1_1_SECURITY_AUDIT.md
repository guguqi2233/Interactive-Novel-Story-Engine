# v1.1 Security / Import Audit

Verification Date: 2026-05-19

Scope: v1.1 Roleplay Immersion Layer import/export surfaces, player/API privacy boundaries, provider configuration failure behavior, tracked-file hygiene, and secret scanning.

Verification commands used:

- `Get-Content backend/app/main.py | Select-Object -Skip 1938 -First 105`
- `rg -n "Remote URLs|remote URL|script|confirm_save|unsafe|source_name|_reject_unsafe|private_self_summary|hidden|sk-|state_delta|require_authoring_enabled" backend/app/roleplay backend/app/main.py backend/app/session_store.py backend/app/llm/provider_factory.py backend/tests`
- `git status --short`
- `git ls-files | rg -i '(^|/)(\.env($|\.)|node_modules/|frontend/dist/|dist/|build/|\.vite/|\.pytest_cache/|__pycache__/|.*\.(db|sqlite|sqlite3|log)$|data/.*\.(db|sqlite|sqlite3|log)$)'`
- `rg -n --hidden -g '!frontend/dist/**' -g '!node_modules/**' -g '!data/**' -g '!*.db' -g '!*.sqlite*' -g '!*.log' 'sk-'`
- `rg -n "localStorage|sessionStorage|api.?key|OPENAI_API_KEY|LLM_API_KEY|sk-" frontend/src .env.example README.md backend/app/llm/provider_factory.py backend/tests/test_llm_provider.py`
- `Get-Content backend/app/roleplay/character_cards.py | Select-Object -First 180`
- `Get-Content backend/app/roleplay/lorebooks.py | Select-Object -First 140`
- `Get-Content backend/app/roleplay/tavern_compat.py | Select-Object -First 400`
- `Get-Content backend/app/llm/provider_factory.py`
- `Get-Content backend/app/llm/openai_provider.py | Select-Object -First 90`
- `Get-Content backend/app/llm/local_provider.py | Select-Object -First 140`

## 已通过项目

1. Character Card Import does not provide arbitrary filesystem reads. The importer accepts raw content, not a user-provided file path, and apply writes through the fixed authoring service path after explicit confirmation and validation.
2. Tavern compatibility import rejects path traversal in `source_name` by disallowing `..`, `/`, and `\`.
3. Character Card Import rejects remote URL references in raw content and does not fetch external URLs.
4. Character Card Import rejects executable/script-like payload markers such as script tags, shell shebangs, PowerShell, and cmd payloads.
5. Character card `system_prompt` and `creator_notes` are classified as unsafe/control entries and are not trusted as prompt authority.
6. Lorebook Import rejects remote URL references and executable/script-like payloads.
7. Lorebook Import classifies prompt/control instructions as `unsafe_entry`; unsafe entries block apply.
8. Tavern Compatibility Import runs untrusted resources through deterministic preview/classification and rejects unsafe raw payloads before apply.
9. Tavern Compatibility Import does not trust external system prompts. Prompt presets must validate through the local `PromptProfile` schema and cannot expand hidden fact or state modification permissions.
10. All checked v1.1 import/export API routes call `require_authoring_api()` before processing.
11. Character card, lorebook, and tavern apply paths require explicit confirmation and content validation before writing content pack files.
12. Tavern export safe mode excludes API keys, raw GameState, save data, and hidden facts by design. Safe lorebook export only exports public facts, and character card export omits private self summaries in safe mode.
13. Frontend search did not show API key persistence via `localStorage` or `sessionStorage`. The Settings UI displays only `api_key_configured` status, not the key value.
14. Settings/config summary exposes safe booleans and provider status rather than raw environment values.
15. Player API response schemas use `visible_state` and do not expose raw `state_deltas`.
16. Existing player visibility tests cover absence of `hidden_facts`, NPC secrets, hidden witness/debug memory markers, and raw `state_deltas` from player-facing payloads.
17. Git tracked-file scan found only `.env.example` and `frontend/.env.example` in env-like files. These are expected examples, not real `.env` secrets.
18. No tracked database, log, cache, `node_modules`, `frontend/dist`, or desktop build output files were identified by the tracked-file scan.
19. Secret scan for `sk-` outside ignored build/data areas found no real-looking OpenAI key. Search results were limited to example env labels, README instructions, redaction code, and fake test keys.
20. Tests use fake/local providers and fake transports for local HTTP provider coverage.
21. Provider factory remains the provider selection entry point. `openai` without `LLM_API_KEY` and `local_http` without `LOCAL_LLM_BASE_URL` fail clearly through `LLMProviderError`.

## 高风险问题

None found.

No evidence was found that v1.1 import paths execute scripts, fetch remote URLs, trust external system prompts, expose API keys, return raw player-hidden state, or bypass authoring API gates.

## 中风险问题

None found that blocks v1.1 release.

## 小问题

1. `CharacterCardImport.source_name` and `LorebookImport.source_name` are currently metadata-only and are not used for filesystem access, but they do not have the same explicit path-separator validator as `TavernCompatibilityImportRequest.source_name`.
2. Secret scanning is pattern-based. It correctly avoids flagging current fake test keys, but future fake keys should keep obvious fake prefixes such as `sk-test-` or avoid `sk-` entirely.
3. Import unsafe detection is rule-based. It blocks the common local risks currently in scope, but it is not a general-purpose malicious prompt detector.
4. Safe export checks for common sensitive markers and excludes known hidden fields. It cannot prove that arbitrary creator-authored public text does not contain a manually pasted secret unless secret scanning is also run before release.

## 修复建议

1. For defense in depth, add the same `source_name` validator used by Tavern import to `CharacterCardImport` and `LorebookImport`, even though these fields are metadata-only today.
2. Keep release-time secret scanning in the release checklist, including a distinction between fake fixtures and real `sk-...` keys.
3. Add future fixtures for more prompt injection variants in character card and lorebook imports.
4. Continue keeping import/export APIs under `ENABLE_AUTHORING_API`; do not expose them as player-facing routes.
5. Maintain safe export as the default and require explicit warning/confirmation for any future authoring/debug export mode that may include hidden authoring metadata.

## 是否阻塞 v1.1 release

Not blocking.

The security/import audit found no high-risk or release-blocking issue. v1.1 can proceed to acceptance if the LLM boundary, visibility/RP memory, full test suite, frontend build, and final release checks also remain green.
