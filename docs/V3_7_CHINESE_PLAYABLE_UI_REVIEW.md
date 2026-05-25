# v3.7 Chinese Playable UI Review

## Current UI Judgment

Verdict: **Not ready for v3.7 tag as Local Playable Complete Product CN**.

The current v3.7 UI is functionally broad and safety-focused, but it still reads
as a developer/release-readiness dashboard rather than a Chinese local playable
product for players and creators. It proves many capabilities exist, but the
default first screen does not yet prioritize everyday play, writing, RP, and
model setup.

Evidence from the current frontend:

- `frontend/src/App.tsx` defaults to `mode = "studio"`.
- `debugOpen` defaults to `true`.
- `DesktopStudioHome` renders `ProductReadinessDashboard` before the product
  home panel.
- Navigation exposes Project, Novel, Tavern, World, Cross-Mode,
  Authoring / Mods, Provider, QA / Quality, Settings, Backup, Diagnostics, and
  Debug / Replay at the same level.
- A static text scan found only a handful of Chinese characters in `App.tsx`,
  while core UI terms such as Home, Project, Provider, Debug, Quality,
  Readiness, Novel, Tavern, World, Backup, Diagnostics, Settings, Create, Open,
  and Disabled appear heavily in English.

## Review Checklist

| Check | Result | Notes |
| --- | --- | --- |
| First screen defaults to Chinese | Fail | Core UI copy is still overwhelmingly English. |
| First screen targets players / creators | Fail | The default screen is still readiness/status/dashboard-heavy. |
| First screen highlights Novel / Tavern / World | Partial | Entries exist, but they are not the primary first-screen product path. |
| Debug / Replay hidden by default | Fail | `debugOpen` defaults to `true`, and the debug drawer renders by default. |
| First screen avoids many disabled controls | Fail | The studio/default surfaces still include many readiness, debug, and unavailable states. |
| No project state only highlights Open/Create Project, Provider Setup, Tour | Fail | Navigation and dashboard surfaces still expose many broader tools. |
| Project-selected state highlights Continue World, Write Novel, Start RP, Provider Status | Partial | These flows exist, but are not the dominant layout. |
| Left navigation is concise | Fail | Too many top-level entries are shown together. |
| Advanced tools are folded | Fail | QA / Quality and Debug / Replay are top-level/default-visible rather than folded. |
| Provider setup is understandable to normal users | Partial | Safe fields exist, but the copy is English and still technical. |
| Error / empty / disabled states are Chinese-friendly | Fail | Most states are English and developer-oriented. |
| Large blocks of English core copy remain | Fail | Yes. |
| API key / hidden / debug leak | Pass | Existing safety checks pass; raw debug remains gated or redacted in reviewed areas. |
| Real LLM experience entry exists | Partial | Provider profile setup exists, but real provider manual testing needs a clearer product path and backend switch strategy. |
| UI still feels like developer console | Yes | Product readiness, QA, Debug, and Diagnostics are too prominent for default use. |

## Problems Blocking Chinese Product Experience

1. **Default language is not Chinese.**
   The UI cannot be tagged as a Chinese local playable product while core
   headings, buttons, cards, empty states, and navigation remain mostly English.

2. **Default home is not a playable creator home.**
   The app opens in the broad studio dashboard, where readiness, health,
   launcher, quality, and diagnostic panels appear before a simple player /
   creator path.

3. **Debug is visible by default.**
   The current `debugOpen = true` behavior makes Timeline Replay, EventLog,
   Hidden Leak, DebugGate, and StateDelta-adjacent surfaces too prominent for
   normal users.

4. **Navigation is not tiered by user intent.**
   Product, authoring, QA, debug, provider, backup, settings, and diagnostics
   compete in one flat navigation group. This is useful for audits, but not for
   daily writing/RP/play.

5. **No-project state is noisy.**
   Instead of focusing only on Open Project, Create Project, Configure Model,
   and Tour, the UI still exposes many workflows that require setup.

6. **Provider setup is safe but still too technical.**
   The UI uses safe metadata fields such as `api_key_env` and `secret_ref`, but
   ordinary users still need a clearer Chinese flow for real API setup, manual
   connection testing, model fetching, and model assignment.

7. **Real provider path is not yet product-clear.**
   The backend and frontend preserve safe ProviderProfile boundaries, but the
   product needs an explicit manual-only real-provider path that cannot be
   confused with CI fake provider behavior.

## Productization Blockers

These should block the corrected v3.7 tag:

1. **Chinese UI default is missing.**
2. **Debug / Replay default visibility is wrong for a playable product.**
3. **Default Home still behaves like a readiness dashboard.**
4. **Advanced tools are not folded by default.**
5. **No-project experience shows too many non-actionable surfaces.**
6. **Provider real-LLM setup lacks a clear Chinese product wizard.**
7. **No v3.7 CN product check exists to prevent regression back to dashboard UI.**

## Non-Blocking Usability Issues

These matter, but can follow after the blockers:

- Product Tour can be simplified into a single current-step card with `1/13`
  progress and a folded full-step list.
- Local privacy copy should be shorter on the first screen.
- Provider capability warnings should be translated and grouped by task.
- Backup / Restore / Diagnostics can stay advanced, but need clearer Chinese
  labels and safer next-action wording.
- Product Readiness Dashboard can remain available for audits, but should move
  under Advanced Tools or Acceptance.
- The current release/audit documents still describe the old dashboard-style
  complete-product goal and should be updated after UI changes.

## Recommended Fix Order

1. **Create Chinese playable home shell.**
   Default first screen should show current project, continue/open/create
   project, Novel, Tavern, World, Provider status, next step, and local privacy
   summary.

2. **Turn off Debug by default.**
   Change Debug / Replay to an Advanced Tools entry. Keep DebugGate and
   `ENABLE_DEBUG_API` boundaries intact.

3. **Simplify navigation.**
   Top-level: Home, Novel, Tavern, World. Secondary: Provider, Settings,
   Backup. Fold Advanced Tools: Authoring / Mods, QA / Quality, Debug / Replay,
   Diagnostics.

4. **Rewrite core UI copy in Chinese.**
   Cover first screen, navigation, tour, Provider setup, no-project state,
   errors, empty states, disabled states, and primary CTAs.

5. **Clarify Provider real-LLM flow.**
   Add a Chinese manual-only setup path for API key via one-time transient key,
   `api_key_env`, `secret_ref`, or future `local_secret_ref`. Keep ProviderProfile
   secret-free.

6. **Add v3.7 CN frontend checks.**
   Checks should assert: Chinese home exists, Novel/Tavern/World are first-screen
   entries, no raw Debug / Replay panel appears by default, no API key appears,
   and no account/cloud/marketplace entry exists.

7. **Update docs and release notes after UI changes.**
   The docs should describe v3.7 as a Chinese playable local product, not a
   dashboard completion milestone.

## Security And Visibility Review

No new leak was identified during this review.

Current safety posture remains acceptable:

- `ProviderProfile` stores `api_key_env` / `secret_ref` metadata, not raw keys.
- `transient_api_key` is treated as one-time request/session data.
- Provider status cache excludes API key, transient key, Authorization header,
  raw env, raw provider response, and raw error body.
- Normal UI safety checks continue to require no hidden facts, NPC secrets,
  debug memory, raw prompts, raw outputs, or raw `state_deltas`.
- Debug UI remains gated where raw details are rendered.

The issue is product experience, not a known security regression.

## Release Decision

**Blocks v3.7 tag.**

The existing v3.7 implementation should not be tagged as
`Local Playable Complete Product CN` yet. It is suitable as a strong
developer-facing completeness checkpoint, but the corrected v3.7 needs a
Chinese, playable, creator-first default experience before release.
