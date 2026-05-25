# v3.8 Chinese Product UX Review

Verification date: 2026-05-25

Scope: read-only review of the current v3.7 Chinese playable product baseline as the starting point for v3.8 Chinese Product UX Polish. This review focuses on whether the app already feels like a Chinese local product instead of a stacked developer console.

Verification commands run for this review:

```powershell
cd frontend
npm.cmd run check:v37-product-cn
npm.cmd run check:v37-e2e-product-experience
npm.cmd run check:v37-product-states
```

Results:

- `check:v37-product-cn`: passed.
- `check:v37-e2e-product-experience`: passed.
- `check:v37-product-states`: passed.

Recent broader baseline from the v3.8 preparation check:

- `python -m pytest`: 1822 passed.
- `cd frontend && npm.cmd run build`: passed.
- all frontend `check:*` scripts: passed.

## 当前 UI 判断

Current verdict: **Mostly productized, ready for v3.8 UX polish.**

The current UI has moved away from the old “developer dashboard first” shape. Static checks confirm that the default Home contains Chinese product copy, three primary entry paths, reduced navigation, no default Debug / Replay drawer, and an Advanced Tools foldout for developer-facing capabilities.

Current strengths:

- Home is intended as a Chinese player / creator entry point.
- Home highlights writing novels, Tavern RP, and open-world play.
- No-project state focuses on opening / creating a project, configuring model service, and trying the demo project.
- Debug / Replay, Product Readiness, StateDelta Viewer, EventLog Viewer, Quality Gate, Diagnostics, and Authoring / Mods remain available but are not intended to occupy the default first screen.
- Existing checks guard against API key display, raw state_deltas on Home, and Debug / Replay appearing outside advanced access.

Current product feel is good enough to enter v3.8, but not polished enough for a stable everyday Chinese product. The remaining work is mostly clarity, wording, recovery flow, visual hierarchy, and reducing engineering-language residue.

## 产品化阻塞项

No release-blocking productization issue was found for entering v3.8 development.

However, these issues should be treated as v3.8 priority items before a future v3.8 release:

1. Backend unavailable recovery is still too generic.
   The UI has Chinese error copy, but the recovery path does not yet clearly separate “backend not running”, “frontend cannot reach backend”, “Authoring API disabled”, and “Provider missing secret”. A normal user may still read an API failure as a model-service problem.

2. Provider setup still has high conceptual load.
   The product supports `api_key_env`, `secret_ref`, `local_secret_ref`, transient keys, Base URL, provider types, model discovery, and assignment. This is secure, but still reads like a technical setup flow in places.

3. Some advanced areas still carry English developer labels.
   This is acceptable inside Advanced Tools, but v3.8 should make sure English tokens do not leak into the default Home, empty states, recovery flows, or main mode entry paths except for intentional terms such as Provider, Debug, StateDelta, EventLog, and Quality Gate.

## 可用性问题

Medium-risk usability issues:

- First-run tour is better than a full checklist, but it can still feel like an implementation walkthrough rather than a short product guide if too many steps are visible.
- Product status and next-step cards can still compete with the three main mode entries. They should remain supportive, not become a dashboard.
- Provider setup has many safe states: unconfigured, configured not tested, connected, missing secret, auth failed, timeout, model list failed, unsupported model list. These need plain Chinese explanations and one obvious next action.
- Demo project entry exists, but the demo path and fake/local_stub wording are still technical. The CTA should lead with “先体验” and put implementation details in secondary text.
- Backup / Restore / Diagnostics are safe and local, but the product copy should emphasize “先预览、再确认、不会上传” more than internal report vocabulary.

Low-risk usability issues:

- Some pagination and utility buttons inside advanced or long-list areas still use English such as First / Previous / Next / Last.
- Some safe-summary text mixes English nouns and Chinese grammar. This is acceptable for technical pages but should be smoothed in product-facing areas.

## 中文化问题

Current status: **core Chinese UX is present, but consistency pass is still needed.**

Passed:

- Home product name and primary CTAs are checked by `check:v37-product-cn`.
- Home includes Chinese entries for writing novels, character RP, open-world play, opening / creating projects, configuring model service, demo project, and local safety.
- Provider, Settings, Backup / Diagnostics, Novel, Tavern, and World have Chinese workflow checks.

Issues to polish:

- Keep intentional mixed terms only where they clarify a boundary: Provider / 模型服务, Tavern RP, Debug / 调试, StateDelta, EventLog, Quality Gate.
- Replace unnecessary English labels in main flows with Chinese.
- Avoid showing “Backend API unavailable” as the primary visible message. The visible message should be “本地后端暂时无法连接” with recovery actions.
- Keep security terms concise. “API Key 不进入项目 / 前端 / 日志 / 备份 / 诊断 / 导出” is useful, but should not dominate the Home hero.

## 导航 / 首页问题

Passed:

- Main entries are reduced to Home / Novel / Tavern / World when a project exists.
- No-project navigation is reduced to project and provider setup paths.
- Advanced Tools contains Debug / Replay.
- Home checks forbid Product Readiness Dashboard, StateDelta Viewer, TimelineReplayPanel, EventLogViewerPanel, raw_state_delta, and raw state_deltas in the default Home slice.

Remaining issues:

- Advanced Tools are present and folded, but the foldout summary still contains enough developer terms that it can feel like a checklist area.
- Product readiness and health status are useful, but should remain short. v3.8 should avoid expanding readiness blocks on Home by default.
- Sidebar should keep “模型服务 / 设置 / 备份” separate from “高级工具” and avoid visually competing with the three main modes.

## 后端不可用恢复问题

Current status: **safe but not product-polished.**

Passed:

- Error states are redacted.
- Product state checks pass.
- Existing Chinese error copy includes “请求失败” and safe retry guidance.
- Recent backend CORS / local frontend origin tests exist in the working tree and reduce local startup friction.

Problems:

- The current recovery copy is still generic: retry local operation, check backend health, or open diagnostics.
- The UI should explicitly offer:
  - 重新连接。
  - 查看启动指南。
  - 打开诊断。
- The UI should classify likely causes when possible:
  - 本地后端未启动。
  - 前端无法连接后端。
  - 本地 API 被配置禁用。
  - 模型服务未配置或缺少密钥。
- Provider-related advice should not appear as the first suggestion when the backend itself is unreachable.

v3.8 recommendation: implement a dedicated Backend Unavailable Recovery panel with safe cause labels and clear CTAs.

## Provider 设置理解成本

Current status: **secure and functional, but still technical.**

Passed:

- Provider setup supports real runtime providers while tests use fake/local_stub.
- API key values are not shown.
- ProviderProfile uses safe references such as `api_key_env`, `secret_ref`, and `local_secret_ref`.
- transient keys are one-time only.
- Model list and model assignment checks pass.

Understanding risks:

- `api_key_env`, `secret_ref`, and `local_secret_ref` are secure but unfamiliar to ordinary users.
- “Relay / 中转站” must stay clearly described as a compatible API base URL, not as API resale.
- Model capabilities such as JSON / structured output, streaming, tools, and fallback need short Chinese explanations tied to actual use cases.
- Users need a clear path from Provider setup to model fetch to model assignment to “start writing / RP / world play”.

v3.8 recommendation: add plain-language helper copy and a single “模型服务是否可用” checklist that avoids raw technical payload.

## API key / hidden / debug 泄露检查

Current status: **no high-risk leak found in reviewed product surfaces.**

Passed evidence:

- v37 product checks forbid API key-like rendering, Authorization bearer values, localStorage/sessionStorage persistence of API keys, raw state_deltas on Home, and Debug / Replay default panels.
- v2 release checklist reports no real API key pattern found.
- Backend tests include provider redaction, transient key non-persistence, normal visible_state boundary, and raw StateDelta exclusion coverage.

Remaining attention:

- Keep aria-labels, error text, cache summaries, and recovery panels free of secrets and hidden/debug content.
- Avoid adding raw provider error messages to the new recovery UX.
- Do not make Product Help or inline guides display real key examples.

## 在线化近期入口检查

Current status: **no onlineization entry found.**

The project continues to state:

- No account system.
- No cloud sync.
- No online marketplace.
- No remote package auto-download.
- No online writing / RP / play platform.
- No API resale service.

These appear as negative / boundary copy, not as enabled product entries.

## 推荐修复顺序

1. Backend Unavailable Recovery UX.
   Add a product-grade Chinese recovery panel with reconnect, startup guide, diagnostics, and cause-specific hints.

2. Product Home UX Polish.
   Keep the three main entries visually dominant and reduce health/readiness competition.

3. Provider Setup UX Final Polish.
   Translate secure technical concepts into ordinary-user guidance without weakening secret boundaries.

4. Provider / Model Explanation UX.
   Explain model fetch, model assignment, JSON capability, and fallback by use case.

5. First-Run Tour Simplification.
   Make the tour a small guided product card, not a full implementation checklist.

6. Empty / Error / Disabled State Polish.
   Ensure every missing project / missing provider / no save / debug disabled state has one clear next action.

7. Advanced Tools Collapse UX.
   Keep developer tools discoverable but visually quiet.

8. Chinese Copy Consistency Pass.
   Remove unnecessary English in main flows while preserving intentional boundary terms.

9. Responsive / Window Size and Accessibility Polish.
   Make sure the product remains usable in ordinary desktop window sizes and keyboard/focus flows.

10. v3.8 Product UX Regression Tests.
   Add checks for backend unavailable recovery, Home hierarchy, Provider explanation, and no raw/debug/secret leaks.

## 是否阻塞 v3.8 release

Current decision: **Not blocking v3.8 development; likely blocking v3.8 release until polished.**

There is no blocker preventing the project from entering v3.8 implementation. For a v3.8 release, the main release-quality requirements should be:

- Backend unavailable recovery is clear and actionable in Chinese.
- Home remains player / creator-first.
- Provider setup is understandable without reading developer docs.
- First-run tour does not look like a checklist.
- Advanced Tools stay folded by default.
- No API key, hidden fact, NPC secret, debug memory, raw prompt/output, raw provider response, or raw state_delta appears in normal UI.

