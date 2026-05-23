# v3.2 Tavern Studio UI Contract Review

## Current Tavern Routes

The current local backend exposes project-scoped Tavern APIs for characters,
character-card import, sessions, messages, chat generation, scene presets,
multi-NPC scenes, Tavern-to-World proposals, World NPC adaptation, mature
settings, and Cross-Mode bridge review. These APIs are authoring-gated and are
local-only surfaces.

## Current Tavern Components

Before v3.2, the main Tavern UI was concentrated in `frontend/src/App.tsx`.
v3.2 introduces `frontend/src/tavernUi.tsx` for reusable safe RP components:
workspace shell, character/session cards, message bubbles, speaker/safety/mood
badges, safe summary panels, toolbar, chat save status, and Tavern Pro panels.

## Current Tavern Data Flow

Tavern UI calls local backend APIs. Tavern characters, sessions, messages,
scene presets, recovery drafts, preferences, export previews, and safety reports
remain project-local. Tavern data is not authoritative World state and does not
directly modify `GameState`.

## Current Chat UX

Single-character chat stores Tavern messages only. Multi-NPC scene generation
stores Tavern scene messages only. Provider calls remain behind the Provider
Gateway and tests must use mock/local-stub providers by default.

## Current Character / Profile UX

Character Card Library and Tavern Character Editor are local authoring surfaces.
Character-card import treats embedded content as untrusted authoring material,
does not execute scripts, does not download remote cards, and does not create or
overwrite World NPCs.

## Current Memory / Emotion / Relationship UX

RP memory, emotion arc, relationship tone, scene mood, and voice panels display
safe summaries. RP memory is not a World fact source. Relationship changes that
could affect World state must become proposals and pass validation.

## Current Cross-Mode UX

Tavern-to-World remains proposal/validation/dry-run/explicit-apply. Tavern-to-
Novel creates Novel draft material only. World NPC-to-Tavern creates Tavern
drafts/references only and does not overwrite World NPCs.

## Current Boundary / Mature UX

Mature Module remains disabled by default. Mature/private memory is hidden from
normal Tavern views and excluded from normal export/backup/diagnostics by
default. Consent and adult-character policy remain explicit boundaries.

## Privacy / Visibility Risks

Normal Tavern UI must not display API keys, raw env, provider secrets, hidden
facts, NPC secrets, private persona, mature memory, debug memory, raw prompts,
or raw `state_deltas`. The v3.2 UI surfaces use safe summaries, redacted text,
and explicit filtering copy.

## Recommended v3.2 Tavern UI Shape

Tavern Studio should remain a local RP workspace with:

- a left character/session navigator;
- a central chat or scene workspace;
- a right safe context/safety sidebar;
- a bottom local/provider/mature-disabled status bar;
- explicit review flows for Tavern-to-World, Tavern-to-Novel, and World NPC-to-
  Tavern interactions.

v3.2 must not add online RP, account systems, cloud sync, online marketplaces,
remote character download, direct GameState mutation, or mature content default
enablement.
