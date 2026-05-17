# v0.7 LLM Boundary Audit

## Audit Date

2026-05-18

## Scope

This audit reviews v0.7 additions and the existing LLM boundary they depend on:

- Studio Home Dashboard
- Save Migration UI / API
- Mod Manager UI / API
- Narrative Quality Dashboard
- Performance Dashboard
- Local Model Provider full integration
- Desktop packaging enhancement
- Scenario Template System
- Visual Quest Graph Editor
- Automated Playtesting Dashboard
- Import / Export Workflow
- App Settings / Local Privacy Panel
- Existing `IntentParser`, `Narrator`, `MemorySummarizer`, `MemoryContextBuilder`, provider factory, and tests

The core standard remains unchanged: the world engine is the fact source, and LLMs are language-layer tools only.

## Review Method

Read-only review using repository searches and targeted source inspection:

- Provider selection and direct provider construction
- v0.7 API routes in `backend/app/main.py`
- v0.7 response schemas in `backend/app/api.py`
- frontend studio panels in `frontend/src/App.tsx`
- provider implementations in `backend/app/llm`
- playtesting provider and runner
- memory context filtering
- performance instrumentation sanitization
- v0.7 integration and provider tests

No code changes were made for this audit.

## 已通过项目

1. **v0.7 新增模块整体不使用 LLM 进行规则判定**
   - Studio Home, migration UI, mod manager, performance dashboard, scenario templates, quest graph editor, playtesting dashboard, import/export, and settings/privacy are deterministic local tools.
   - None of these modules decide world outcomes through LLM output.

2. **Studio Home 不暴露敏感 provider 配置**
   - `/studio/status` returns safe status fields such as `llm_provider`, enabled flags, validation summaries, and recent save summaries.
   - It does not return API key values, raw environment variables, raw `GameState`, or raw hidden state.

3. **Settings / Local Privacy Panel 不暴露 API key**
   - `/studio/config-summary` returns `api_key_configured: bool`, provider status, and a redacted database path hint.
   - It does not return `LLM_API_KEY`, raw env, or full local database path.

4. **Save Migration UI 不调用 LLM**
   - Migration status, dry-run, and apply routes call the migration service and repository only.
   - Migration UI consumes safe summaries and does not request model output.

5. **Mod Manager UI 不调用 LLM 判断 mod 安全**
   - Mod validation uses `ModLoader` and content validation rules.
   - The mod system remains content-only and does not execute arbitrary code or invoke model judgment.

6. **Narrative Quality Dashboard 不使用外部 LLM judge**
   - Narrative evals use deterministic local rule checks.
   - The dashboard displays sanitized report summaries and does not call a real provider.

7. **Performance Dashboard 不记录 prompt 全文或敏感内容**
   - `PerformanceRecorder` sanitizes tags containing `api_key`, `llm_api_key`, `secret`, `sk-`, `prompt`, `game_state`, or `state_delta`.
   - Debug performance APIs expose samples and summaries, not prompts, API keys, or raw state.

8. **Local Model Provider full integration 仍通过 `LLMProvider` 抽象**
   - `local_http` and `local_stub` are selected through `create_llm_provider`.
   - Business modules continue to depend on `LLMProvider`, not provider-specific classes.

9. **local model 输出不能直接进入 `GameState`**
   - `IntentParser`, `Narrator`, and `MemorySummarizer` validate outputs through Pydantic schemas.
   - The game loop still applies world changes only from rule-produced `StateDelta`, not provider output.

10. **Desktop packaging 不打包 API key**
    - Desktop packaging remains a local prototype/script workflow.
    - Documentation and scripts do not embed `.env` or API keys into the frontend bundle.

11. **Scenario Template System 不调用 LLM**
    - Template preview/render is variable substitution plus validation.
    - Template output does not modify active `GameState` and does not bypass validation.

12. **Quest Graph Editor 不调用 LLM 自动改任务图**
    - Graph parsing and preview are local transforms over `quests.yaml`.
    - Save is still gated by validation; preview does not write disk or runtime state.

13. **Playtesting Dashboard 不调用真实 LLM**
    - Playtests use `PlaytestLLMProvider`, a deterministic local provider.
    - Agents act through `GameLoop`/test harness and record Events.

14. **Import / Export 不调用 LLM**
    - Archive import/export performs zip safety checks, manifest validation, content/mod validation, and migration-status checks.
    - No model is involved.

15. **没有发现 LLM 输出直接进入 `GameState`**
    - Runtime state updates still flow through `ActionResult.state_deltas`, `apply_delta`, and system tick deltas.
    - Provider output is used for intent/narration/summary schemas, not authoritative state mutation.

16. **Narrator 仍只接收可见输入**
    - `Narrator.render` passes a reduced payload containing `success_level`, `reason`, and `visible_facts`.
    - `hidden_facts`, raw `state_deltas`, raw `GameState`, and debug events are not included.

17. **MemoryContextBuilder 过滤 hidden/debug memory**
    - Narrator context uses `filter_narrator_safe_memories`.
    - Hidden, debug-only, and player-unknown hidden/discoverable fact-linked memories are excluded.

18. **provider factory 仍是 provider 选择入口**
    - `create_llm_provider` supports `mock`, `local_stub`, `local_http`, and `openai`.
    - Tests check for direct business-code instantiation of `LocalHTTPProvider`.

19. **测试不调用真实 API**
    - Provider tests use fake transports for `local_http`.
    - Playtesting uses deterministic providers.
    - Narrative evals are local rule checks.

20. **schema 校验失败路径清晰**
    - `OpenAIProvider`, `LocalHTTPProvider`, `LocalStubProvider`, and `FakeLLMProvider` raise clear errors on parse/schema failures.
    - Missing `LLM_API_KEY` and missing `LOCAL_LLM_BASE_URL` fail clearly.

## 风险项目

1. **MemorySummarizer 仍会把 Event payload 交给 LLMProvider**
   - Existing summarizer payload includes event fields and `state_deltas`.
   - This is not a v0.7 regression and does not feed the narrator directly, but if a real external provider is used, hidden or debug-adjacent event details could be sent for summarization unless the caller limits the event set.
   - Recommendation: add a future safe event summarization payload builder that redacts hidden/debug deltas before real-provider use.

2. **Narrator system prompt text appears encoding-corrupted**
   - The prompt file contains mojibake-like text in `NARRATOR_SYSTEM_PROMPT`.
   - Runtime protection is mostly enforced by the code-level safe payload and schema validation, so this is not currently a direct permission escalation.
   - Recommendation: replace with clean Chinese/English boundary text in a future doc/prompt cleanup task.

3. **Authoring UI can display hidden content to the author**
   - This is intended for local content editing, but it must remain isolated from player UI and narrator paths.
   - Current routing keeps authoring surfaces separate.

4. **`local_http` can send prompts off-process**
   - The settings panel correctly flags `provider_sends_prompts_off_machine` for `local_http` and `openai`.
   - Users should understand local HTTP endpoints are still provider calls and may log prompts outside this app.

## 高风险问题

None found.

No v0.7 feature was found that lets LLM output directly mutate `GameState`, produce authoritative `StateDelta`, decide rule outcomes, or bypass the provider factory.

## 中风险问题

1. **Memory summarization payload may include raw `state_deltas`**
   - Impact: privacy exposure to the configured provider if summarization is run with a non-mock provider.
   - Current containment: not used as world authority; not sent to narrator; memory remains non-authoritative.
   - Recommended fix: introduce `build_safe_memory_summarizer_events()` that excludes hidden/debug deltas or uses player/narrator-safe event summaries.

2. **Narrator prompt boundary relies more on code than prompt text**
   - Impact: the system prompt is not human-readable due to encoding corruption.
   - Current containment: code sends only safe action result and visible facts; output schema is validated.
   - Recommended fix: clean prompt text and add a snapshot test for narrator message construction.

## 小问题

1. `/studio/status` and `/studio/config-summary` expose boolean provider/API states by design.
   - This is acceptable for a local-only studio, but should remain non-sensitive and not become a raw config dump.

2. Import/export archives can contain hidden authoring content by design.
   - This is acceptable as local archive data, but archives must not be fed into player UI or narrator prompts.

3. Frontend debug panels display raw `state_deltas` in debug areas.
   - This is expected for local debug surfaces and remains separate from player/narrator output.

## 修复建议

Recommended before or during v0.8, not required to unblock v0.7:

1. Add a safe event payload builder for `MemorySummarizer`.
2. Replace the corrupted `NARRATOR_SYSTEM_PROMPT` with readable boundary text.
3. Add a prompt/message snapshot test ensuring narrator input excludes:
   - raw `state_deltas`
   - `hidden_facts`
   - debug events
   - hidden/debug memory
4. Consider a provider privacy warning in README for `local_http`, explaining that “local” means configured endpoint, not necessarily in-process.

## 是否阻塞 v0.7 acceptance

No.

Final LLM boundary verdict: **v0.7 LLM boundary audit passed with non-blocking medium-risk recommendations**.

