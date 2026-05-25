# v3.7 Chinese Usability Audit

Verification Date: 2026-05-25

Scope: v3.7 Local Playable Complete Product CN usability review. This audit checks whether the current UI behaves like a Chinese player/creator product instead of a developer dashboard. It is based on source inspection of the v3.7 home, navigation, first-run tour, Provider wizard, Novel/Tavern/World entry points, error/empty/disabled states, and v3.7 frontend check scripts. No business code was changed, no real provider was called, and no data was uploaded.

Verification checks run:

- `cd frontend && npm.cmd run check:v37-product-cn` - passed.
- `cd frontend && npm.cmd run check:v37-provider-real-llm-wizard` - passed.
- `cd frontend && npm.cmd run check:v37-product-states` - passed.
- `cd frontend && npm.cmd run check:v37-e2e-product-experience` - passed.

## Passed Items

1. First screen now reads like a Chinese product.
   - The default home uses `本地 AI 叙事工作室`, `中文本地可游玩完整产品`, Chinese CTAs, and local-first safety pills.
   - The old developer-dashboard emphasis is moved below the playable home or into folded advanced tools.

2. Novel / Tavern RP / World are prominent.
   - Home exposes `写小说`, `角色 RP`, and `大世界游玩` as main entries.
   - Project-loaded and no-project states both point users toward these flows instead of release checklist panels.

3. Disabled noise is reduced on the default Home.
   - No-project Home emphasizes `打开项目`, `创建项目`, `配置模型服务`, `查看引导`, and `体验 Demo 项目`.
   - v3.7 checks verify the playable Home does not render a screen full of disabled controls.

4. Debug / QA are hidden from the default first impression.
   - `debugOpen` defaults to false.
   - Debug / Replay and Product Readiness are available through Advanced Tools rather than expanded on the playable Home.

5. First-run tour is understandable.
   - The tour uses a current-step card, progress indicator, `上一步`, `下一步`, `跳过`, `完成`, and folded `查看全部步骤`.
   - It explains local-first setup, project creation/opening, Provider setup, model fetching, model assignment, and starting Novel/Tavern/World.

6. Provider configuration is mostly clear in Chinese.
   - Provider setup includes Chinese sections for service type, API key source, manual connection test, model list fetching/manual model id, model assignment, and save.
   - It explains `api_key_env`, `secret_ref`, `local_secret_ref`, transient key, local_http, relay/custom compatible API, and mock/local_stub paths.

7. Real LLM risks are documented and partially surfaced in UI.
   - Product guide and manual smoke-test docs explain possible cost, prompt sending, manual-only connection, no CI real-provider calls, and how to return to mock/local_stub.
   - Home and Provider UI state that real connections are manual and do not run at startup.

8. Model assignment is understandable.
   - Model assignment UI lists Novel, Tavern, World, Cross-Mode, memory summary, quality, and low-cost summary use cases.
   - World intent parsing shows a JSON / structured-output capability warning.

9. World play entry is clear.
   - Home shows `继续大世界`, `开始大世界`, and `大世界游玩`.
   - World UI has Chinese empty states such as `还没有开始大世界` and explains that normal play uses backend `visible_state`.

10. Tavern RP entry is clear.
    - Tavern UI exposes `Tavern / 角色 RP 工作室`, `开始单角色 RP`, `单角色 RP`, and `多 NPC 场景`.
    - Provider-missing states point to `配置模型服务`.

11. Novel writing entry is clear.
    - Novel UI exposes `写小说 / Novel Studio`, `创建稿件`, `写章节`, export, quality, and model-service status.
    - Provider-missing states point to `配置模型服务`.

12. Error / Empty / Disabled states are friendlier.
    - Shared localization maps missing project, missing Provider, missing model assignment, no manuscript, no character/session, no save, debug disabled, diagnostics, backup/restore, and authoring/mod cases to Chinese next actions.
    - v3.7 product-state check passed.

13. Advanced tools remain discoverable without dominating.
    - Navigation folds Cross-Mode, Authoring / Mods, QA / Quality, Diagnostics, Export, and Debug / Replay under Advanced Tools.
    - Product Readiness, Quality Gate, Debug / Replay, Authoring / Mods, Backup, and Diagnostics remain available in folded advanced sections.

14. No obvious first-screen API key or raw debug exposure was found.
    - Chinese Home and v3.7 checks forbid API key display, raw `state_deltas`, StateDelta Viewer, TimelineReplayPanel, EventLogViewerPanel, and Product Readiness Dashboard on the default playable Home.

15. No account/cloud/marketplace remains clear.
    - The Home, navigation, docs, and checks preserve `无需账号`, `不使用云同步`, and `无在线市场` messaging without making those the main product experience.

## High-risk Usability Issues

None found.

No current high-risk usability blocker prevents v3.7 from being presented as the Chinese Local Playable Complete Product.

## Medium-risk Issues

1. Some advanced and secondary surfaces still contain English developer labels.
   - Examples include Project Home health cards such as `Backend health`, `Project loaded`, `Provider status`, and `Model assignment status`, plus Prompt Lab / Settings headings such as `Prompt Profiles / Experiments`.
   - These are not on the main playable Home, so they do not block release, but they weaken the full Chinese product feel.

2. The default Home is product-oriented but still dense.
   - It includes project entry, LLM runtime status, recent projects, demo entry, mode entries, quality summary, and safety summary.
   - This is much better than the earlier dashboard stack, but v4.0 polish should consider a shorter first viewport with secondary summaries below the fold.

3. Real LLM cost/prompt risk is clearer in docs than in the Provider wizard itself.
   - The wizard clearly states manual-only connection and secret safety.
   - It should also surface a short Chinese warning near `Test Connection` / generation actions: real provider calls may send prompts and may incur cost.

4. Some terms remain mixed English/Chinese by design, but the balance is uneven.
   - Acceptable mixed terms: Provider, Tavern RP, Debug, Quality Gate, Cross-Mode, ModelProfile.
   - Less ideal mixed labels remain in badges, status cards, and advanced checklists. These are non-blocking but should be normalized later.

5. Advanced tools are findable, but their internal information density is high.
   - QA, Debug, Product Readiness, Authoring, Diagnostics, and Quality panels still contain many audit/checklist-style cards.
   - This is acceptable because they are now advanced tools, but future polish should add task-focused presets.

## Non-blocking Follow-ups

- Translate remaining secondary Project Home, Prompt Lab, status bar, quality, and authoring headings to Chinese-first labels.
- Add a short inline Provider risk banner: `真实调用可能产生费用，并会向用户配置的 Provider 发送经过可见性过滤的 prompt。`
- Shorten the first viewport by moving detailed LLM/runtime and quality summaries into expandable sections.
- Replace remaining `Open ...`, `No ...`, `Missing ...`, and `Status ...` strings in secondary empty states with Chinese-first text.
- Keep English technical names only where they are established product terms or API concepts.
- Add a visual/manual QA pass after the next CSS/layout polish to ensure the Chinese copy does not wrap awkwardly on smaller screens.

## Release Decision

Pass.

v3.7 meets the Chinese usability baseline for a Local Playable Complete Product. The main Home is Chinese and creator/player-oriented, Novel/Tavern/World entries are prominent, disabled and debug noise is reduced, Provider setup is understandable, and key v3.7 frontend usability checks pass. Remaining issues are medium-risk polish items and do not block the v3.7 tag.
