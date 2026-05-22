# v2.9 Local App Shell Review

## Current Routes

The frontend currently uses a local React state router instead of a URL router. The top-level modes are:

- `project`: Narrative project shell, Novel/Tavern/Cross-Mode sections, and project validation.
- `studio`: local studio dashboard, workspace tools, quality, playtest, performance, privacy, and diagnostics surfaces.
- `play`: World Studio play view, visible state, saves, dialogue, social graphs, status, and debug side panel.
- `authoring`: world authoring and Script / Mod platform tools selected by `requestedAuthoringTool`.
- `prompt_lab`: Provider Gateway, Prompt Lab, routing, usage, and provider profile tools.

Several v2.9 destinations already exist as panels rather than independent routes. Novel, Tavern, and Cross-Mode are inside the project shell. Script/Mods are inside authoring. Providers are inside Prompt Lab. Debug/Replay is a side panel gated by backend debug capability.

## Current Navigation

The previous shell exposed only Project, Studio, Play, Authoring, and Prompt Lab. That made the product model harder to scan because important local workflows were nested behind broad labels. Debug state was visible as a side panel but not clearly represented as a gated local tool. Mature/RP settings existed in privacy/Tavern areas and should stay out of primary navigation.

v2.9 should present a unified local navigation surface for Project Home, Novel, Tavern, World, Cross-Mode, Script / Mods, Providers, Quality, Debug / Replay, and Settings while still mapping to the existing state router.

## Current Layout Structure

The app is intentionally local and monolithic. `frontend/src/App.tsx` contains most page sections, panels, cards, status badges, debug views, authoring tools, provider tools, module browser, and project shell logic. `frontend/src/styles.css` contains global layout and component styling. This is workable for v2.9 if the shared surface is improved without splitting the whole app.

Recommended v2.9 structure:

- Keep the current mode state router.
- Add reusable, safe UI primitives for summaries, mode cards, risk badges, local-only notices, and privacy notices.
- Add a local status bar and landing sections that reuse safe summaries from existing state.
- Keep debug and diagnostics views explicit and gated.

## Duplicated Components

Repeated patterns exist for:

- Cards and status summaries across Studio Home, Project Shell, Provider, Module Browser, and Quality panels.
- Risk and validation badges across authoring, module, quality, import/export, and provider surfaces.
- Loading, empty, error, and disabled copy.
- Privacy reminders around provider setup, export, debug, and package import.

v2.9 should centralize the most common patterns in lightweight local components inside the current frontend without adding a UI framework.

## Loading/Empty/Error Gaps

Most sections have partial empty/error handling, but the shape is inconsistent. Gaps include:

- Missing setup hints when a mode has no project data yet.
- Raw backend error text could vary by endpoint and needs consistent redaction before display.
- Disabled API states should explain the relevant local configuration flag, especially debug/replay.
- Provider and quality missing states should read as "not configured" or "not run" instead of broken.

## Privacy/Secret Risks

The frontend already prefers `api_key_env` and `secret_ref` instead of plaintext keys. v2.9 should make this more visible and enforce it in UI copy and static checks.

Risk areas to keep guarded:

- Provider status/debug JSON must be rendered through safe redaction.
- Error panels must not show API keys, Authorization headers, raw env values, stack traces, or sensitive local paths.
- Export and diagnostics UI must default to safe summaries only.
- No account, cloud sync, online marketplace, or remote package download entry should appear as a near-term feature.

## Hidden/Debug Display Risks

Normal UI must not show hidden facts, NPC secrets, debug memory, raw prompts, or raw `state_deltas`. Existing debug/replay surfaces may show diagnostic material only when gated by `ENABLE_DEBUG_API`. v2.9 navigation, status, diagnostics, and landing pages should show safe counts and summaries, not raw debug payloads.

## Recommended v2.9 Shell Shape

The v2.9 shell should be:

- Local-first: project data stays local, cloud sync is not implemented, and no online marketplace is offered.
- Mode-clear: primary navigation should expose Project, Novel, Tavern, World, Cross-Mode, Script/Mods, Providers, Quality, Debug/Replay, and Settings.
- Secret-safe: provider configuration uses env/secret refs only; displayed errors and diagnostics are redacted.
- Boundary-preserving: UI never directly modifies `GameState`; world changes continue through backend validation, `StateDelta`, and `EventLog`.
- Debug-gated: debug/replay/diagnostics debug export remains clearly marked and controlled by `ENABLE_DEBUG_API`.
