# v2.8 Release Notes: Roleplay Immersion & Mature Module

## 1. Version Name

v2.8 is **Roleplay Immersion & Mature Module**.

This release deepens Tavern-style roleplay while adding a default-off local
Mature Content Framework for policy, boundary, provider routing, export
filtering, and quality checks. It does not turn the project into an online adult
content platform and does not add explicit content examples.

## 2. Version Goal

v2.8 improves local RP continuity and safety by adding:

- richer RP memory, emotion, relationship tone, scene mood, and voice metadata;
- Multi-NPC Tavern scene orchestration with per-speaker safe context;
- default-off mature content policy infrastructure;
- deterministic consent, boundary, age-category, fade-to-black, provider
  routing, export, import/mod policy, and quality gate checks.

The core authority model is unchanged:

- Tavern/RP does not directly modify `GameState`;
- World Engine remains the fact source;
- LLMs remain language tools, not world judges or safety judges;
- Provider Gateway remains the only model entry point.

## 3. New Features

- Added v2.8 Roleplay contract documentation and audits.
- Added Advanced RP Memory records with safe visibility filtering.
- Added Emotion State and Emotion Arc schemas for Tavern presentation
  continuity.
- Added Relationship Tone Pro profiles and derivation helpers.
- Added Multi-NPC Scene backend services and frontend panel.
- Added Scene Mood Preset Pro and Character Voice Lab metadata.
- Added Roleplay Boundary Profiles.
- Added `ContentRating`, `MatureContentPolicy`, `ConsentState`, and
  `BoundaryCheckResult`.
- Added Fade-to-Black policy and deterministic safe renderer.
- Added Mature Memory Partition.
- Added Provider Safety Routing checks for content ratings and mature policy.
- Added Mature Export Controls for project, Novel, Tavern, and module export
  paths.
- Added Mature Module Settings UI.
- Added RP Safety Evals, RP Style Quality Checks, RP-World Consistency checks,
  Cross-Mode RP hardening, and Mature/RP Quality Gate integration.

## 4. Behavior Changes

- Mature Module is disabled by default.
- `explicit_adult` capability is disabled by default.
- Mature export is disabled by default.
- Mature-only memory is excluded from normal Tavern, Novel, World, export, and
  quality contexts by default.
- Unknown-age or minor-age characters are blocked from mature-rated flows.
- Unknown, unwilling, coerced, intoxicated, or unconscious consent states block
  mature-rated flows.
- Fade-to-black is the default safe fallback for boundary-sensitive transitions.
- Tavern-to-World output remains proposal-only and carries RP safety metadata.
- Multi-NPC replies write Tavern messages only and do not mutate `GameState` or
  write `EventLog`.

## 5. API Changes

New or updated local APIs include:

```text
GET   /projects/{project_id}/mature/settings
PATCH /projects/{project_id}/mature/settings
POST  /projects/{project_id}/tavern/multi-scenes
GET   /projects/{project_id}/tavern/multi-scenes
POST  /projects/{project_id}/tavern/multi-scenes/{scene_id}/next-reply
POST  /projects/{project_id}/quality-gate/run
```

Provider routing now checks content rating metadata when mature policy is
involved. Project quality gate output can include RP/Mature checks when enabled
by local project configuration.

## 6. Frontend Changes

- Added Mature Module Settings UI with default-disabled policy display.
- Added controls and warnings for max content rating, fade-to-black, adult
  character requirement, consent requirement, export controls, and provider
  routing requirements.
- Added Multi-NPC Scene Pro UI for local Tavern scenes.
- Frontend avoids rendering mature memory bodies, hidden facts, NPC secrets, API
  keys, raw env, provider secrets, raw prompts, and raw `state_deltas`.
- Frontend build passes for v2.8.

## 7. RP Memory / Emotion / Tone Changes

- Added `AdvancedRPMemoryRecord` for non-authoritative RP continuity memory.
- Added memory visibility categories including safe Tavern/Novel views,
  authoring-only, mature-only, hidden, and debug-only.
- Added `EmotionState` and `EmotionArc` for bounded emotional continuity.
- Added `RelationshipToneProfile` and `RelationshipToneProService`.
- Relationship tone can derive from safe Tavern memory, safe emotion arc data,
  and safe world relationship summaries.
- RP memory, emotion, and tone metadata do not become World facts and do not
  directly modify `GameState`.

## 8. Multi-NPC Scene Changes

- Added Multi-NPC scene service support for scene creation, participants,
  turn order, speaker context, reply generation, and turn advancement.
- Each NPC speaker context is limited to safe known facts and safe RP/voice/
  mood/memory/tone context.
- NPC unknown facts, hidden facts, NPC secrets, mature-only memory, debug
  memory, and raw `state_deltas` are excluded from ordinary prompt context.
- Generated replies write Tavern messages only.
- Tests use fake/mock provider behavior and do not call real APIs.

## 9. Scene Mood / Voice Lab Changes

- Added Scene Mood Preset Pro fields for expression controls such as mood tags,
  sensory focus, pacing, intensity, genre flavor, density, and emotional
  temperature.
- Scene mood presets cannot access hidden facts, modify state, override action
  results, or force mature content.
- Added Character Voice Lab profile/sample support for text-only voice
  experiments.
- Voice Lab affects expression only. It does not change NPC knowledge, World
  facts, or `GameState`.
- v2.8 does not implement TTS or audio voice generation.

## 10. Mature Content Framework Changes

- Added `ContentRating` and `MatureContentPolicy`.
- Mature Module defaults:
  - `enabled=false`;
  - `require_adult_characters=true`;
  - `require_consent=true`;
  - `default_fade_to_black=true`;
  - `export_mature_content=false`;
  - `allow_explicit_adult=false`.
- The framework is local policy and filtering infrastructure. It is not an
  online adult-content platform, age verification service, cloud mature-content
  sync service, or NSFW image generation system.
- v2.8 intentionally includes no explicit content examples.

## 11. Consent / Boundary / Fade-to-Black Changes

- Added `RoleplayBoundaryProfile`.
- Added `ConsentState` and `BoundaryCheckService`.
- Mature-rated flows are blocked for unknown/minor age categories, unknown or
  unwilling consent, coercion risk, intoxication/unconscious risk, and boundary
  violations.
- Added deterministic Fade-to-Black renderer for safe transition text.
- LLMs do not judge age, consent, relationship boundaries, or safety pass/fail.

## 12. Provider Safety Routing Changes

- Extended `ProviderSafetyPolicy` with content rating constraints.
- Mature routing checks project `MatureContentPolicy` and provider
  `ProviderSafetyPolicy`.
- Providers that disallow mature-rated content are rejected or downgraded to
  fade-to-black behavior.
- Local-only mature routing rejects cloud providers when required.
- Routing explanations avoid sensitive prompt text.
- Provider Gateway remains the only model entry point.

## 13. Export / Privacy Changes

- Added `MatureExportPolicy`.
- Normal exports exclude mature-only memory, mature scene details, boundary
  private notes, debug memory, API keys, provider secrets, raw env, database
  files, logs, caches, and build artifacts.
- Explicit mature export flags are required before mature content can be
  included, and secrets remain filtered even then.
- Project, Novel, Tavern, and Module export paths are covered by v2.8 filtering
  tests.
- Mature memory does not enter World facts or ordinary narrator/Tavern prompt
  context.

## 14. Safety / Quality Gate Changes

- Added RP Safety Eval cases for hidden fact leaks, NPC secret leaks, private
  persona leaks, mature memory leaks, provider policy mismatches, and export
  filtering.
- Added RP Style Quality checks for forbidden phrases, missing speaker IDs,
  private note leaks, hidden fact leaks, scene mood mismatch, mature rating
  mismatch, and style boundary violations.
- Added RP-World Consistency checks for dead/incapacitated NPC speaking,
  unknown facts, nonexistent items/locations, quest contradictions,
  relationship contradictions, and absent world events.
- Added Mature/RP Quality Gate aggregation and blocker categories.
- Quality gates are deterministic local checks, not LLM judgments.
- Full verification for acceptance passed:

```text
python -m pytest
1679 passed

cd frontend && npm.cmd run build
passed
```

## 15. Known Limitations

- v2.8 does not support an online adult-content platform.
- v2.8 does not support age verification service.
- v2.8 does not support NSFW image generation.
- v2.8 does not support mature cloud sync.
- v2.8 does not support arbitrary-code mature plugins.
- Mature Module enablement is local policy metadata, not external compliance or
  identity verification.
- Multi-NPC Scene Pro is an MVP for safe local Tavern orchestration, not a full
  autonomous multi-agent society simulation.
- Character Voice Lab is text-only and does not implement TTS.
- Provider safety routing relies on local provider policy metadata and cannot
  prove an external provider's real-world moderation behavior.
- Frontend production build still emits a non-blocking Vite chunk-size warning.

## 16. Upgrade Notes From v2.7

- Review project safety settings after upgrade. Mature Module remains disabled
  unless explicitly configured.
- Review provider profiles and `ProviderSafetyPolicy` if using content rating
  metadata or local-only mature routing.
- Keep mature export disabled unless there is an explicit local authoring need.
- Ensure Tavern/RP workflows treat RP memory, emotion, tone, voice, and mood as
  expression/proposal metadata, not World facts.
- Route RP-to-World changes through proposal, validation, explicit apply,
  `StateDelta`, and `EventLog`.
- Do not add real API keys to provider profiles, exports, docs, tests, mods, or
  frontend code.
- Existing v2.7 Advanced World Simulation Modules remain compatible with the
  v2.8 RP/Mature boundaries.

## 17. Recommended v2.9 Direction

Recommended v2.9 direction: **Local UI / UX Foundation**.

The post-v2.8 roadmap is local-first, UI-first, and experience-first:

- v2.9: Local UI / UX Foundation
- v3.0: Local Desktop Studio Polish
- v3.1: Novel Studio UI Pro
- v3.2: Tavern Studio UI Pro
- v3.3: World Studio UI Pro
- v3.4: Authoring / Mod UI Pro
- v3.5: Local QA / Debug / Replay UI Pro
- v3.6: Local Performance & Accessibility Polish

Online-Ready Architecture and Sandbox Plugin Runtime are demoted to long-term
optional directions. Account systems, cloud sync, online marketplaces, remote
package registries, online narrative platforms, and online mature-content
platforms are not near-term goals.
