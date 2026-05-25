# v3.7 Local Complete Product Contract Review

Verification date: 2026-05-25

Verdict: The current project has a mostly complete local product foundation for
v3.7 closure. The core Novel, Tavern, World, Authoring/Mod, Provider,
QA/Debug/Replay, Backup/Restore, Diagnostics, and local privacy boundaries are
present and integrated in current HEAD. No high-risk product completeness
blocker was found in this contract review.

This review is a contract and readiness pass. It does not claim that v3.7 final
product polish is complete; it identifies the remaining product-shape work that
should be closed during v3.7 without adding large new systems.

## Current Product Entry Points

Present entry points:

- Product Home / Project Home: present in the local Studio app shell with
  project status, workspace navigation, and local-first messaging.
- First-run onboarding: present as a local onboarding surface and ready to be
  expanded into the v3.7 complete product tour.
- Project Picker / Recent Projects: present through the Desktop / Local Studio
  surfaces, with safe summary expectations documented from v3.0 onward.
- Novel Studio: present through the Novel workspace and related editor,
  outline, scene, quality, export, and recovery surfaces.
- Tavern Studio: present through character library, RP/session, multi-NPC,
  memory, boundary, safety, export, and recovery surfaces.
- World Studio: present through play, map/location, NPC, quest, inventory,
  module, timeline/EventLog, save/load, quality, provider, and debug surfaces.
- Authoring / Mod Studio: present through package editors, validation,
  diff/dry-run, safe apply, module browser, permissions, compatibility,
  certification, import/export, and quality gate surfaces.
- QA / Debug / Replay: present through Timeline Replay, EventLog Viewer,
  StateDelta Viewer, Visible vs Debug Compare, Hidden Leak Report, Playtest,
  Quality Gate, Performance, CrossMode Conflict, Module Playtest, Save
  Migration, Diagnostics, Local Test Run, and Safe Debug Export surfaces.
- Provider Connectivity: present through setup, connection status, connection
  test, model discovery/sync, model assignment, usage/cost, capability matrix,
  and slow-provider warning surfaces.
- Settings / Privacy: present through local settings, privacy/secrets guidance,
  reduced motion and visual comfort settings, and local-first status messaging.
- Backup / Restore / Diagnostics / Export: present through local backup,
  restore dry-run/apply, diagnostics preview/create, export controls, and safe
  debug export surfaces.
- Offline help/manual entry: present in the local/offline help direction, but
  v3.7 should consolidate it into a complete product guide.

Product entry gap: there is not yet a single Product Readiness Dashboard that
summarizes all of these entry points and their readiness state in one place.

## Current End-to-End Workflows

The current codebase supports the pieces of the complete local workflow:

1. Create or open a local project through the project picker and project home.
2. Configure a provider profile using local provider setup.
3. Test provider connectivity with safe connection-test APIs.
4. Fetch and sync provider model metadata as `ModelProfile` records.
5. Assign models by Novel, Tavern, World, Cross-Mode, Quality, and summary use
   cases through provider routing/model assignment.
6. Write in Novel Studio using outline, chapter, scene, search, quality, export,
   and World-to-Novel import surfaces.
7. Roleplay in Tavern Studio using character cards, sessions, multi-NPC scenes,
   RP memory, voice/tone, boundaries, safety, and export/recovery controls.
8. Play in World Studio using backend action APIs, visible state, modules,
   EventLog/timeline, save/load, quality, and debug-gated inspection surfaces.
9. Move content across modes through Cross-Mode drafts, proposals, validation,
   review, apply plans, and audit records.
10. Author content packs and mods through safe editors, validation,
    diff/dry-run, import/export hardening, and safe apply/publish-to-local.
11. Run Quality Gate, Playtest, Hidden Leak, CrossMode Conflict, Module Stress,
    Performance, and Diagnostics reviews locally.
12. Backup, restore, export, and generate diagnostics with explicit safe
    filtering and confirmation for risky flows.

Workflow closure gap: the pieces are present, but v3.7 should add a guided
End-to-End Local Workflow Checker so users can see whether a local project has
completed the full product path.

## Current Provider Setup Flow

Provider setup is ready for v3.7 product closure:

- `ProviderProfile` / `ProviderProfileV2` concepts exist, with `api_key_env`
  and `secret_ref` boundaries.
- Provider list, create/update/delete, validate, status, and usage APIs exist.
- Provider connection testing exists and returns safe status data.
- Provider model fetch/sync exists for OpenAI-compatible/custom-style model
  lists using fake-provider tests by default.
- Model list APIs and patch/update paths exist for `ModelProfile` metadata.
- Model assignment by mode/use case exists, including validation and capability
  warnings.
- Provider connection status cache exists and stores only safe status fields:
  provider id, status, tested time, latency, safe error type, model count, and
  redaction flag.
- Frontend Provider UI includes connectivity dashboard, setup, model list,
  assignment, usage/cost, capability matrix, and slow-provider warnings.

Provider setup constraints still hold:

- Real API keys must not be saved to project files or frontend state.
- `transient_api_key` is one-time only and must not be persisted.
- Provider tests must use fake clients/providers and must not call real
  providers in CI.
- Relay/custom provider configuration is treated as a local compatible base URL
  setup, not an API resale service.

v3.7 product gap: the Provider Complete Setup Checklist should make the local
provider path explicit: configure, test, discover models, sync, assign by mode,
validate routing, and review secret boundaries.

## Current Novel/Tavern/World Readiness

Novel Studio readiness:

- Novel workspace, outline/tree, chapter/editor surfaces, scene board,
  manuscript/dashboard, character arcs, plot/foreshadowing, timeline links,
  world bible, version compare, writing session, search/filter, provider UX,
  export, World-to-Novel import, quality, preferences, and recovery surfaces are
  represented in the current v3.1+ product line.
- Novel mode remains a drafting layer. It does not directly mutate active
  `GameState`; World-bound changes remain draft/proposal/validation/apply.

Tavern Studio readiness:

- Tavern workspace, character card library, RP/voice editor, single character
  chat, multi-NPC scene UI, memory, emotion, relationship tone, scene mood,
  voice lab, boundaries/mature settings, provider UX, tags/search, World and
  Novel bridge surfaces, safety, export/backup, preferences, and recovery are
  represented in the current v3.2+ product line.
- Tavern RP does not directly mutate active `GameState`; World-bound effects
  remain proposal/validation/apply.

World Studio readiness:

- World workspace, play view, map/location, NPC/relationship, quest/journal,
  inventory/trade, tactical/economy/faction/deduction/survival/magic/hacking/
  crafting/cultivation module UI, timeline/EventLog, visible state inspector,
  save/load, quality/playtest, provider UX, action input, debug boundary, and
  safe debug UI are represented in the current v3.3+ product line.
- World Studio normal views rely on `visible_state` and safe summaries.
  World-changing actions go through backend APIs, `StateDelta`, and `EventLog`.

Product gap: v3.7 should add workflow completion checks for each studio so a
user can tell whether Novel, Tavern, and World flows are locally usable from
first launch through export/backup/diagnostics.

## Current Authoring/Mod Readiness

Authoring / Mod readiness is strong for v3.7 closure:

- Authoring workspace and editors exist for world, script, character, quest,
  location/map, NPC/faction/relationship, item/economy/trade, rumor/crime/
  consequence, and advanced module authoring panels.
- Action Mod Editor and Action Mod Test Harness are present as declarative,
  non-arbitrary-code flows.
- Rule Module UI remains contract-only.
- Module Browser, Permission Dashboard, Compatibility Matrix, Certification,
  Import/Export Wizard, Mod Quality Gate, Validation Dashboard, Diff/Preview/
  Dry-Run, Audit Trail, Backup/Restore, and Safe Apply workflows are present.
- Import/export hardening, zip slip/executable/secrets filtering, and
  ProviderProfilePack secret boundaries are covered by v3.4/v3.5/v3.6 work.

v3.7 product gap: the existing surfaces should be connected into a single
Authoring / Mod Complete Workflow Check that verifies validate, dry-run,
preview, confirm, safe apply, audit, export, and backup in order.

## Current QA/Debug/Replay Readiness

QA / Debug / Replay readiness is strong:

- Timeline Replay UI Pro exists with safe summaries and debug-gated details.
- EventLog Viewer Pro exists with normal safe summaries and linked delta counts.
- StateDelta Viewer Pro exists and remains debug-sensitive.
- Visible vs Debug State Compare exists and is debug-gated with redaction.
- Hidden Leak Report, Playtest, Unified Quality Gate, Performance Dashboard,
  CrossMode Conflict Review, Module Playtest/Stress, Save Migration Visualizer,
  Diagnostics Bundle Review, Local Test Run Dashboard, and Safe Debug Export
  surfaces exist.
- v3.6 optimization added route-level splitting, long-list rendering,
  large-report filtering, safe cache strategy, keyboard/focus/accessibility
  polish, reduced motion, error boundaries, and loading/progressive rendering.

Boundary readiness:

- Debug/Replay views are observation tools. They must not modify `GameState`.
- Raw `state_deltas` remain debug-gated.
- Normal QA views must not show hidden facts, NPC secrets, debug memory, raw
  prompt/output, provider secrets, or raw deltas.

v3.7 product gap: a Product Acceptance Checklist UI should bring QA, debug,
replay, provider, backup, diagnostics, and export status into one acceptance
surface.

## Current Backup/Restore/Diagnostics Readiness

Backup / Restore / Diagnostics readiness is adequate for v3.7 closure:

- Local backup dry-run/create/list flows are present.
- Restore dry-run/apply flows are present, with explicit-confirm expectations.
- Diagnostics preview/create/validate flows are present.
- Progress UI exists for long backup/restore/diagnostics flows.
- Safe Debug Export exists and requires debug gating plus explicit confirmation
  for risky raw debug material.
- Diagnostics and backup defaults are documented to exclude `.env`, API keys,
  provider secrets, raw env, raw prompt/output, hidden facts, NPC secrets, raw
  `state_deltas`, mature/private data, databases, logs, caches, build outputs,
  backups, and crash reports unless a future explicit safe policy allows them.

Product gap: v3.7 should close Export Complete Workflow and Diagnostics Complete
Workflow as user-facing checklists rather than leaving the user to infer the
safe order across multiple panels.

## Current Privacy/Security Boundaries

Current boundaries required for v3.7 are present in docs and code direction:

- Local-first remains the product line. There is no near-term account system,
  cloud sync, online marketplace, online RP/writing/play platform, remote
  package auto-download, or API resale service.
- World Engine remains the fact authority.
- LLMs are language/rendering helpers, not rules judges.
- Provider Gateway remains the model entry boundary.
- `GameState` must not be directly modified by UI, LLM output, Novel/Tavern
  bridges, Authoring drafts, mods, or debug tools.
- World changes must go through `StateDelta` and be recorded in `EventLog`.
- `visible_state` remains the safe normal UI source.
- Hidden facts, NPC secrets, hidden witnesses, debug memory, raw prompts, raw
  outputs, raw `state_deltas`, mature/private content, provider secrets, and
  API keys must not enter normal UI, normal reports, exports, diagnostics,
  backups, logs, packages, prompt profiles, or tests.
- Debug UI is gated by `ENABLE_DEBUG_API` / `DebugGate`.
- Mature/private content remains opt-in and disabled/filtered by default.
- Mods remain declarative by default; arbitrary code plugins remain forbidden.
- Action Mods must go through `ActionRegistry`, `StateDelta`, and `EventLog`.
- Rule Modules remain contract-only.
- Provider profiles may save only `api_key_env` or `secret_ref`.
- `transient_api_key` is one-time and must not persist to frontend state,
  logs, diagnostics, backup, export, project files, prompt profiles, caches, or
  package manifests.

No high-risk privacy/security contract regression was found during this
review.

## Missing Product Gaps

Product completeness blockers:

- None found for starting v3.7 product closure.

Must close during v3.7 to call the product complete:

- Product Readiness Dashboard: a single overview of local product readiness,
  provider readiness, project lifecycle readiness, privacy status, and quality
  status.
- End-to-End Local Workflow Checker: guided confirmation that a user can create
  or open a project, configure provider, discover/sync/assign models, use Novel,
  Tavern, World, Cross-Mode, Authoring/Mod, QA/Debug, Backup/Restore, Export,
  and Diagnostics locally.
- Provider Complete Setup Checklist: explicit provider configuration through
  connection test, model discovery/sync, model assignment, capability warnings,
  and safe secret review.
- Studio workflow closure checks: separate Novel, Tavern, World, Authoring/Mod,
  QA/Debug/Replay, Backup/Restore/Diagnostics, and Export completion checks.
- Demo Local Narrative Project: sample assets exist (`worlds/mist_valley`,
  templates, RP templates, and sample safe action mod), but v3.7 should package
  them into a single guided local demo project/workthrough.
- Product Guide / Offline Manual Pro: existing help/docs should be consolidated
  into a user-facing offline guide for complete local use.
- Product Acceptance Checklist UI: user-visible final checklist for local
  readiness, privacy, provider, quality, backup, diagnostics, and export.

Non-blocking polish items:

- Reduce remaining app-shell complexity where old detailed components still
  coexist with newer lazy-loaded summary components.
- Add browser-level smoke coverage for the complete local workflow.
- Improve provider model-name normalization and long model display behavior.
- Expand large-project demo fixtures for very large manuscripts, sessions,
  EventLogs, provider model lists, and package sets.
- Continue keyboard and screen-reader QA beyond static build/check scripts.
- Tighten final navigation labels and empty-state copy for first-time users.

## Recommended v3.7 Product Shape

v3.7 should be a closure and product-readiness release, not a feature expansion
release.

Recommended implementation shape:

1. Start with a Product Readiness Dashboard that reads existing safe summaries
   and shows local readiness without introducing new authority or online flows.
2. Add a First-Run Complete Product Tour that points to existing entry points:
   project, provider, Novel, Tavern, World, Authoring/Mod, QA/Debug,
   Backup/Restore, Export, and Diagnostics.
3. Add checklist-style workflow closures for provider setup, local project
   lifecycle, Novel, Tavern, World, Cross-Mode, Authoring/Mod, QA/Debug/Replay,
   Backup/Restore/Diagnostics, and Export.
4. Package a local demo narrative project from existing safe samples and make it
   clear that it is local-only, not enabled by default, and contains no secrets
   or executable plugin code.
5. Consolidate offline guide/manual content around the complete local workflow.
6. Polish navigation, settings, status/health, error/empty/disabled states, and
   acceptance checklists.
7. Keep privacy/security boundaries visible in UI copy: local-first, no cloud,
   no marketplace, no remote package download, no arbitrary code plugins, no
   real keys in project files, no debug/hidden data in normal UI.
8. Finish with a v0.1-v3.7 full integration review and v3.7 integration
   regression tests using fake providers and local fixtures only.

Release decision for v3.7.1: Ready to proceed to the next v3.7 product closure
module. No code-level release blocker was identified by this contract review.
