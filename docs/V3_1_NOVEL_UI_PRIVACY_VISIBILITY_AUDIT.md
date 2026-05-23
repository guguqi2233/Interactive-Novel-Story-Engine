# v3.1 Novel UI Privacy / Visibility Audit

Verification date: 2026-05-23

## 已通过项目

- Novel UI does not provide a plaintext API key input. Static checks in `frontend/scripts/check-v31-novel-ui.mjs` reject `<input name="api_key">`, API-key literals, and secret-looking `sk-*` tokens.
- Novel UI copy and components consistently state that API keys, raw env, provider secrets, hidden facts, private notes, raw prompts, and raw `state_deltas` are not shown in normal Novel UI.
- Novel Prompt / Provider panel shows only prompt profile id, provider safe summary, model/use-case hints, and the text `API key not shown`; it does not render provider secret values.
- Novel normal UI uses safe summary components in `frontend/src/novelUi.tsx`; World Bible Sidebar copy is restricted to flavor lore and novel-safe structured facts and explicitly excludes NPC secrets.
- Timeline Link Panel is represented as safe summaries only. Backend `NovelTimelineService` uses `TimelineEvent.safe_summary()` and excludes hidden events from normal timeline summaries.
- Chapter/Scene editor does not render raw `state_deltas`; the v3.1 UI text explicitly says raw `state_deltas` are excluded.
- Novel Export Wizard states that authoring notes, hidden refs, mature/private content, debug data, and API keys are excluded by default. Backend `NovelExportService` renders draft text and normal scene text only, checks `contains_secret_text`, rejects `state_delta`, and uses `MatureExportFilter`.
- Draft snapshots validate against secrets, `hidden fact`, `state_delta`, and `raw_prompt` before saving. The API list/create responses replace `draft_text` with `[stored locally]`.
- Novel Search defaults `include_authoring=False`; it does not search plot/arc authoring notes unless explicitly requested by backend code, and no normal UI path enables that flag.
- Quality Dashboard normal UI is a safe issue summary panel. Backend consistency issues use safe codes/messages and use `[hidden-ref]` for hidden fact risk details.
- Error display uses existing frontend safe error formatting; v2.9 API/client checks cover stack trace, Authorization, raw env, hidden facts, raw prompts, raw `state_deltas`, and local path redaction.
- Novel UI does not bypass Diagnostics/Backup flows. It calls project-scoped Novel APIs only and does not directly read/write arbitrary files.
- No account, cloud sync, online publishing, or online marketplace primary Novel UI entry was introduced. Local-first copy remains present.

## 高风险 UI 泄露

None found.

## 中风险 UI 泄露

None found in the implemented v3.1 Novel UI path.

## 小问题

- `docs/V3_1_ROADMAP.md` is currently missing. This is a release documentation gap, not a privacy/visibility blocker.
- `frontend/src/api.ts` still contains broad platform types with fields such as `state_deltas`, `state_delta_templates`, and `api_key_configured` for non-Novel/debug/authoring surfaces. The Novel UI path does not render those as raw data, but future cleanup should keep v3.1 checks focused on Novel normal UI.
- `NovelExportService` writes export files locally and returns a local path. Existing desktop/path-safety policy treats local paths carefully elsewhere; a future Novel Export UI pass should prefer safe path summaries if the path is surfaced prominently.

## 修复建议

- Add `docs/V3_1_ROADMAP.md` before v3.1 release freeze.
- Keep `npm.cmd run check:v31-novel-ui` in the release checklist and extend it if new Novel panels are split into additional files.
- If a future authoring/debug Novel view displays authoring notes or prompt context, require explicit gating and clear labels, and continue excluding hidden facts, API keys, raw prompts, and raw `state_deltas`.
- Prefer safe path summaries for any future export result display.

## 是否阻塞 v3.1 release

Not blocked on privacy / visibility grounds.

The only noted item is the missing v3.1 roadmap document, which should be handled as a documentation checklist item before final release/tagging rather than a UI privacy blocker.
