# v2.8 Roadmap: Roleplay Immersion & Mature Module

## Version Theme

Roleplay Immersion & Mature Module.

v2.8 builds on Novel Studio, Tavern Studio, World Studio, Cross-Mode Bridge,
Provider Gateway Pro, Script / Mod Platform Pro, and Advanced World Simulation
Modules. The release should deepen Tavern-style roleplay while adding a
default-off, local-only Mature Content Framework with strict consent, adult
eligibility, boundary profiles, provider safety routing, export controls,
memory isolation, and quality gates.

## Current Baseline

- v2.7 Advanced World Simulation Modules are present in the working tree, but
  the current HEAD observed during v2.8 readiness checks was still tagged
  `v2.6`. v2.7 should be committed and tagged before v2.8 implementation
  begins.
- Tavern Studio MVP already supports Tavern characters, sessions, messages,
  RP/Voice Profiles, Tavern memory, safe lorebook/world-info context, scene
  mood presets, relationship tone, Tavern response generation, Tavern-to-World
  proposals, World NPC to Tavern drafts, and Tavern boundary evals.
- Provider Gateway already includes `ProviderSafetyPolicy`, including mature
  content allowance, sensitive prompt controls, safe logging defaults, and
  redaction.
- `ProjectSafetyPolicy` includes local-only defaults, mature content disabled
  by default, external providers disabled by default, and `export_secrets=false`.
- Mature runtime systems are not complete. v2.8 plans them as optional local
  safety infrastructure, not as a public adult-content platform.

## Goal

v2.8 should improve Tavern/RP immersion through richer memory, emotional arcs,
relationship tone, multi-NPC scenes, scene mood, character voice experimentation,
and reusable boundary profiles.

v2.8 should also introduce a Mature Content Framework that is:

- disabled by default;
- local-only;
- limited to adult characters with explicit consent and declared boundaries;
- separated from ordinary memory and ordinary prompts;
- provider-routed only through explicit safety policy;
- export-filtered by default;
- covered by deterministic evals and quality gates;
- unable to bypass World Engine authority.

## Explicit Non-Goals

v2.8 does not implement:

- mature content enabled by default;
- an online adult-content platform;
- an age verification service;
- cloud sync for mature content;
- NSFW image generation;
- arbitrary-code plugins;
- RP or mature content bypassing the World Engine;
- RP messages directly modifying `GameState`;
- LLM judgment of consent, age, relationship boundaries, or safety pass/fail;
- mature memory entering ordinary narrator or Tavern prompts;
- bypasses around provider safety policy;
- mature scenes involving minor or unknown-age characters;
- non-consensual, coerced, incapacitated, or unconscious mature content;
- adultization of real people without consent;
- a public-release claim for Mature Module capability.

## Hard Constraints

- Tavern/RP may improve expression, pacing, emotional texture, and dialogue
  style, but cannot change world facts.
- The World Engine remains the authoritative fact source.
- Mature Module must be disabled by default.
- Mature content requires adult characters, explicit consent, explicit
  boundaries, and content rating.
- Mature memory must be partitioned from ordinary RP/Narrator memory.
- Mature content export is disabled by default.
- Provider routing must check `ProviderSafetyPolicy`.
- Important RP-to-World effects must go through proposal, validation, and
  explicit apply.
- Hidden facts, NPC secrets, debug memory, and raw `state_deltas` must not enter
  ordinary RP prompts.
- Tests must use mock/local providers and must not call real APIs.
- LLMs cannot act as world judges or safety judges.

## Recommended Development Order

1. Boundary Foundation
   - Roleplay Immersion Contract Review
   - Roleplay Boundary Profiles
   - Mature Content Rating Framework
   - Consent / Boundary System
   - Fade-to-Black Mode

2. RP Immersion
   - Advanced RP Memory
   - Emotion Arc System
   - Relationship Tone Pro
   - Scene Mood Preset Pro
   - Character Voice Lab

3. Multi-NPC Tavern
   - Multi-NPC Scene Pro Backend
   - Multi-NPC Scene Pro Frontend
   - RP Consistency with World State

4. Mature Safety Infrastructure
   - Mature Memory Partition
   - Provider Safety Routing for Mature Content
   - Mature Export Controls
   - Mature Module Settings UI
   - Mature Module Import / Export / Mod Policy

5. Quality and Release Hardening
   - RP Safety Evals
   - Tavern / Narrative Style Quality Checks
   - Cross-Mode RP Bridge Hardening
   - Mature / RP Quality Gate
   - v2.8 Integration Regression Tests

## Module Plans

### 1. Roleplay Immersion Contract Review

- Goal: audit existing Tavern/RP/mature boundaries and define the v2.8 roleplay
  contract before feature work.
- Data structures: `RoleplayImmersionContractReport`,
  `RoleplayBoundaryFinding`, current capability/gap summary.
- API changes: none required; document existing Tavern, Cross-Mode, Provider,
  and quality APIs.
- Frontend changes: none.
- Tests: static checks for no direct Tavern `GameState` mutation, no hidden
  prompt material, and no mature default-on config.
- Acceptance: a contract review document exists and identifies blockers before
  implementation begins.

### 2. Advanced RP Memory

- Goal: improve Tavern memory retrieval and summarization while keeping RP
  memory non-authoritative and separate from mature/debug memory.
- Data structures: `AdvancedRPMemoryRecord`, `RPMemoryScope`,
  `RPMemoryRetrievalPolicy`, safe memory summary.
- API changes: safe memory query and summary endpoints for Tavern sessions.
- Frontend changes: Tavern memory panel with safe snippets, source session refs,
  and visibility labels.
- Tests: ordinary memory does not include mature memory, hidden facts, NPC
  secrets, debug memory, or raw `state_deltas`.
- Acceptance: RP memory improves continuity without becoming a fact source.

### 3. Emotion Arc System

- Goal: track character emotional arcs for RP presentation and continuity.
- Data structures: `EmotionArc`, `EmotionBeat`, `EmotionArcSummary`,
  emotional baseline refs.
- API changes: local authoring endpoints for previewing and updating RP
  emotional arc metadata.
- Frontend changes: compact emotion arc timeline in Tavern character/session
  views.
- Tests: emotion arc data cannot modify canonical NPC state without proposal
  and validation.
- Acceptance: emotional continuity is visible and testable as presentation
  metadata.

### 4. Relationship Tone Pro

- Goal: expand relationship-tone derivation and presentation controls without
  changing relationship values directly.
- Data structures: `RelationshipToneProfile`, `ToneAxis`, `ToneOverrideDraft`,
  safe tone summary.
- API changes: relationship tone preview and validation endpoints.
- Frontend changes: relationship tone controls with diff/preview and boundary
  warnings.
- Tests: tone changes do not mutate relationship score, faction reputation, or
  World facts.
- Acceptance: users can tune RP tone while World relationship state remains
  authoritative.

### 5. Multi-NPC Scene Pro Backend

- Goal: support safe multi-character Tavern scenes with per-NPC knowledge and
  visibility filtering.
- Data structures: `MultiNPCScene`, `SceneParticipant`, `SceneTurnPlan`,
  per-participant safe context.
- API changes: create/list scenes, add participant, generate next reply, and
  summarize scene endpoints.
- Frontend changes: none in this slice beyond API readiness.
- Tests: each NPC sees only its allowed facts; hidden participants, NPC secrets,
  mature memory, and debug memory do not enter ordinary context.
- Acceptance: multi-NPC RP works through Tavern data and cannot directly affect
  `GameState`.

### 6. Multi-NPC Scene Pro Frontend

- Goal: add Tavern UI for multi-NPC scenes, turn management, safe participant
  summaries, and scene boundary warnings.
- Data structures: TypeScript models matching backend multi-NPC scene records.
- API changes: consume Multi-NPC Scene Pro Backend APIs.
- Frontend changes: multi-NPC scene panel with participants, recent messages,
  active speaker, safety status, and proposal controls.
- Tests: frontend build, empty/error states, hidden participant exclusion, no
  secret display.
- Acceptance: users can run local multi-NPC scenes without exposing hidden data.

### 7. Scene Mood Preset Pro

- Goal: expand scene mood presets into richer expression controls.
- Data structures: `SceneMoodPresetPro`, mood intensity, pacing, sensory focus,
  dialogue energy, mature eligibility marker.
- API changes: scene mood preview and validation endpoints.
- Frontend changes: preset editor with safe preview and compatibility warnings.
- Tests: mood presets cannot grant hidden fact access, state mutation, or mature
  access by themselves.
- Acceptance: mood changes affect style only.

### 8. Character Voice Lab

- Goal: provide local voice/style experimentation for characters.
- Data structures: `CharacterVoiceExperiment`, `VoiceVariant`,
  `VoiceConsistencyReport`.
- API changes: create experiment, compare variants, save safe voice preset.
- Frontend changes: voice lab panel with variant comparison and consistency
  warnings.
- Tests: experiments do not call real providers by default and do not alter
  canonical NPC facts.
- Acceptance: users can test voice variants safely with mock/local providers.

### 9. Roleplay Boundary Profiles

- Goal: define reusable RP boundary profiles for prompt permissions and scene
  behavior.
- Data structures: `RoleplayBoundaryProfile`, prompt permission flags, mature
  eligibility policy, memory scopes, export policy.
- API changes: CRUD and validation for project-local boundary profiles.
- Frontend changes: boundary profile editor and assignment controls.
- Tests: profiles cannot enable hidden fact access, direct state mutation,
  provider bypass, or mature access unless project policy allows it.
- Acceptance: RP boundary behavior is explicit, reusable, and validated.

### 10. Mature Content Rating Framework

- Goal: add default-off content rating and mature scene classification.
- Data structures: `MatureContentRating`, `MatureSceneClassification`,
  `CharacterAgeEligibility`, rating audit summary.
- API changes: classify/validate mature scene metadata without using an LLM as
  judge.
- Frontend changes: rating display and disabled-by-default warnings.
- Tests: unknown-age or minor characters are rejected from mature scenes.
- Acceptance: mature scene eligibility is deterministic and auditable.

### 11. Consent / Boundary System

- Goal: enforce explicit consent and boundary rules for mature scenes.
- Data structures: `ConsentProfile`, `BoundaryLimit`, `SceneConsentState`,
  consent audit result.
- API changes: validate consent and boundaries before mature scene generation.
- Frontend changes: consent/boundary checklist and clear blocked-state UI.
- Tests: non-consensual, coerced, incapacitated, unconscious, unknown-age, or
  minor scenarios are blocked.
- Acceptance: consent and boundaries are rule-checked and never LLM-judged.

### 12. Fade-to-Black Mode

- Goal: provide deterministic fade-to-black behavior when mature content is
  disabled, ambiguous, or outside boundaries.
- Data structures: `FadeToBlackPolicy`, `FadeToBlackSummary`, blocked reason.
- API changes: mature scene request returns fade summary instead of explicit
  content when policy requires it.
- Frontend changes: safe fade summary UI and reason display.
- Tests: blocked mature content produces safe non-explicit summaries and does
  not store mature prompt text in ordinary memory.
- Acceptance: fade mode is predictable, safe, and default fallback behavior.

### 13. Mature Memory Partition

- Goal: isolate mature-scoped memory from ordinary RP, Novel, Narrator, and
  World prompts.
- Data structures: `MatureMemoryRecord`, `MatureMemoryPartitionPolicy`,
  partition-safe summary.
- API changes: mature memory create/query/delete endpoints gated by project
  policy and local settings.
- Frontend changes: mature memory management in Mature Module settings only.
- Tests: mature memory never enters ordinary Tavern/Narrator prompts or normal
  exports.
- Acceptance: mature memory is isolated and export-filtered by default.

### 14. Provider Safety Routing for Mature Content

- Goal: route mature-labeled prompts only through providers that explicitly
  allow mature content.
- Data structures: `MatureProviderRoutingContext`, mature use cases, provider
  safety decision report.
- API changes: ProviderRouter context gains mature scene flags and rejection
  reasons.
- Frontend changes: provider status shows whether mature routing is configured,
  without exposing secrets.
- Tests: provider with `allow_mature_content=false` is rejected; fallback cannot
  bypass the same policy.
- Acceptance: provider safety policy is enforced end-to-end.

### 15. Mature Export Controls

- Goal: keep mature content export disabled by default and provide explicit
  filtered/redacted export modes.
- Data structures: `MatureExportPolicy`, `MatureExportReport`, redaction
  summary.
- API changes: export dry-run and apply controls with explicit confirmation.
- Frontend changes: export warnings and opt-in controls in Mature Settings.
- Tests: ordinary project export excludes mature memory/content by default and
  never includes secrets.
- Acceptance: mature export is explicit, redacted, and auditable.

### 16. Mature Module Settings UI

- Goal: add local settings UI for Mature Module enablement and policy review.
- Data structures: TypeScript models for mature policy, consent defaults,
  export policy, provider readiness, and partition status.
- API changes: consume mature settings/status APIs.
- Frontend changes: settings panel with disabled default state, warnings,
  consent/boundary controls, provider status, and export controls.
- Tests: frontend build, default-off state, blocked states, no secret display.
- Acceptance: users can see and configure mature policies without exposing
  sensitive data.

### 17. RP Safety Evals

- Goal: add deterministic RP and mature safety evals.
- Data structures: `RPSafetyEvalCase`, `RPSafetyEvalReport`, blocker categories.
- API changes: optional local eval run endpoint and quality-gate integration.
- Frontend changes: display eval status in quality panels if present.
- Tests: hidden facts, NPC secrets, debug memory, raw `state_deltas`, mature
  partition leaks, minor/unknown-age attempts, and consent failures are caught.
- Acceptance: high-risk RP/mature boundary regressions block release readiness.

### 18. Tavern / Narrative Style Quality Checks

- Goal: evaluate Tavern reply quality and style consistency without using an
  LLM as judge.
- Data structures: `TavernStyleQualityReport`, voice drift metrics, repetition
  checks, tone mismatch checks.
- API changes: local quality run and summary endpoints.
- Frontend changes: quality panel for style warnings and consistency trends.
- Tests: deterministic checks catch voice drift, unsafe style overrides, and
  repeated phrasing.
- Acceptance: quality checks improve RP style while staying local and
  deterministic.

### 19. RP Consistency with World State

- Goal: validate RP output against visible World state and prevent authoritative
  fact invention.
- Data structures: `RPWorldConsistencyReport`, contradiction refs, proposal
  suggestions.
- API changes: validate RP transcript/output against safe visible world summary.
- Frontend changes: consistency warnings in Tavern session view.
- Tests: RP text that claims quest completion, item creation, relationship
  changes, or fact discovery without proposal/validation is flagged.
- Acceptance: RP can suggest but cannot establish World facts.

### 20. Cross-Mode RP Bridge Hardening

- Goal: harden Tavern/RP to Novel/World bridge flows for mature and multi-NPC
  scenes.
- Data structures: bridge policy flags, mature exclusion metadata, safe draft
  summaries.
- API changes: Cross-Mode preview/validation paths enforce mature export and
  memory partition policies.
- Frontend changes: warnings on draft/proposal review surfaces.
- Tests: Tavern/RP to World remains proposal-only; Tavern/RP to Novel excludes
  mature content unless explicitly allowed.
- Acceptance: cross-mode flows preserve proposal, validation, and explicit apply
  boundaries.

### 21. Mature Module Import / Export / Mod Policy

- Goal: extend Script/Mod Platform policy for mature-aware packages.
- Data structures: mature package flags, mature mod policy, import/export
  validation report.
- API changes: package validation rejects default-enabled mature content,
  unsafe mature fields, executable payloads, secrets, and hidden fact leaks.
- Frontend changes: Module Browser warnings for mature package policy.
- Tests: mature packages cannot auto-enable mature module or include disallowed
  content/secrets.
- Acceptance: mature-aware packages are local, explicit, safe, and
  quality-gated.

### 22. Mature / RP Quality Gate

- Goal: aggregate RP immersion and mature safety checks into release readiness.
- Data structures: `MatureRPQualityGateConfig`, `MatureRPQualityGateResult`,
  blocker/warning categories.
- API changes: Quality Gate includes RP/mature checks and safe summaries.
- Frontend changes: quality dashboard status for RP/mature blockers.
- Tests: blockers include mature default-on, memory partition leak, provider
  safety bypass, hidden fact leak, consent failure, minor/unknown-age scene, and
  unsafe export.
- Acceptance: high-risk mature/RP issues block v2.8 acceptance.

### 23. v2.8 Integration Regression Tests

- Goal: verify the complete v2.8 RP/mature boundary.
- Data structures: test fixtures for ordinary RP, mature-disabled, mature
  allowed, blocked, fade-to-black, cross-mode, provider routing, and export.
- API changes: none beyond tested surfaces.
- Frontend changes: build verification and UI empty/error/disabled states.
- Tests: full backend suite, focused v2.8 tests, frontend build, no real API
  calls.
- Acceptance: v2.8 can ship only when deterministic tests cover RP immersion,
  Mature Module safety, provider routing, export controls, and cross-mode
  boundaries.

## Impact on Tavern Studio

Tavern Studio becomes the main beneficiary of v2.8. It gains deeper RP memory,
emotion arcs, relationship tone controls, multi-NPC scene orchestration, scene
mood presets, voice experimentation, and optional Mature Module settings.

Tavern data remains local RP data. Tavern messages, memories, style controls,
and mature scene records cannot directly modify `GameState`.

## Impact on Novel Studio

Novel Studio may consume safe Tavern scene summaries and RP-derived drafts, but
must not receive mature memory or hidden details unless an explicit export
policy allows a redacted authoring-only path.

Novel drafts remain drafts. They do not establish World facts.

## Impact on World Mode / GameState

World Mode remains the authoritative fact layer. RP and Mature Module outputs
can create proposals, validation reports, and explicit apply requests, but they
cannot directly mutate `GameState`.

Any confirmed world change still requires structured validation, `StateDelta`,
and `EventLog`.

## Impact on Cross-Mode Bridge

Cross-Mode Bridge must keep Tavern/RP material as draft/proposal data unless a
validated explicit apply path is used. Mature memory/content is excluded from
ordinary bridge outputs by default.

Mature-aware bridge paths require explicit policy checks and safe summaries.

## Impact on Provider Gateway

Provider Gateway remains the only model entry. v2.8 adds mature-aware routing
context and requires `ProviderSafetyPolicy.allow_mature_content=true` before a
provider may handle mature-labeled prompts.

Fallback providers must satisfy the same mature and safety policies.

## Impact on Mod Platform

Script/Mod Platform must reject mature packages that auto-enable mature content,
contain secrets, include executable payloads, bypass consent/boundary rules, or
leak hidden facts.

Mature-aware mods remain declarative and local. They are not arbitrary-code
plugins.

## Impact on LLM Permission Boundary

LLMs remain language tools only. They may render dialogue, voice, mood, and
fade-to-black summaries from safe context, but cannot decide:

- consent;
- character age eligibility;
- relationship boundaries;
- mature safety pass/fail;
- World facts;
- StateDelta application;
- provider safety policy.

## Hidden Facts / NPC Secrets / Mature Memory / Privacy Risks

v2.8 increases the amount of RP context, so privacy boundaries become release
critical:

- hidden facts must not enter ordinary Tavern prompts;
- NPC secrets and private persona remain authoring-only unless revealed by
  rules;
- debug memory and raw `state_deltas` must not enter prompts, exports, or normal
  reports;
- mature memory must be partitioned from ordinary memory;
- mature export is disabled by default;
- mature provider routing cannot bypass `ProviderSafetyPolicy`;
- mature settings and reports must not expose API keys, provider secrets, or
  local sensitive paths.

## v2.8 Integration Test Requirements

v2.8 requires focused and integration tests for:

- Mature Module default-off behavior.
- Adult/known-age eligibility enforcement.
- Consent and boundary rejection for non-consensual, coerced, incapacitated,
  unconscious, minor, unknown-age, and real-person adultization scenarios.
- Fade-to-black fallback.
- Mature memory partition isolation.
- ProviderSafetyPolicy mature routing and fallback enforcement.
- Tavern hidden fact, NPC secret, debug memory, and raw `state_deltas` prompt
  exclusion.
- RP messages not mutating `GameState`.
- RP-to-World proposal, validation, and explicit apply flow.
- Mature export disabled by default and secret-safe when enabled.
- Mature-aware mod/package import/export rejection of unsafe packages.
- Multi-NPC per-participant visibility and knowledge filtering.
- Tavern / narrative style quality checks.
- Mature / RP Quality Gate blockers.
- Frontend Mature Settings and Multi-NPC UI disabled/empty/error states.
- No real provider/API calls.

Final validation:

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

## v2.8 Final Acceptance Criteria

- v2.7 has been committed and tagged before v2.8 implementation begins.
- Roleplay Immersion Contract Review exists and matches implementation.
- Mature Module is disabled by default.
- Mature content requires adult/known-age characters, explicit consent, explicit
  boundaries, and content rating.
- Mature memory is partitioned from ordinary memory.
- Mature content export is disabled by default.
- Provider safety routing blocks providers that do not explicitly allow mature
  content.
- Tavern/RP cannot directly mutate `GameState`.
- RP-to-World changes require proposal, validation, and explicit apply.
- Hidden facts, NPC secrets, debug memory, and raw `state_deltas` do not enter
  ordinary RP prompts.
- Mature-aware import/export rejects secrets, executable payloads, hidden fact
  leaks, and default-enabled mature content.
- RP/mature quality gates block high-risk boundary violations.
- Full backend tests and frontend build pass.

## v2.9 Candidate Directions

Recommended v2.9 direction: **Local UI / UX Foundation**.

Rationale: v2.1-v2.8 would cover project structure, Novel/Tavern/World modes,
Cross-Mode Bridge, Provider Gateway, Script/Mod Platform, advanced modules, and
RP/mature safety. The next priority should be making these local capabilities
easier, clearer, safer, and more pleasant to use before adding online
architecture. v2.9 should establish shared UI patterns, navigation,
information-density rules, local settings surfaces, safe preview panels, and
consistent empty/error/loading states.

Planned local-first follow-up roadmap:

- v3.0: Local Desktop Studio Polish
- v3.1: Novel Studio UI Pro
- v3.2: Tavern Studio UI Pro
- v3.3: World Studio UI Pro
- v3.4: Authoring / Mod UI Pro
- v3.5: Local QA / Debug / Replay UI Pro
- v3.6: Local Performance & Accessibility Polish

Online-Ready Architecture, account systems, cloud sync, online marketplaces,
remote package registries, online narrative platforms, and online mature-content
platforms are demoted to long-term optional directions. They should not be
treated as v2.9 or near-term v3.x goals, and they must not be introduced before
the local privacy, provider, export, package, mature/RP, and UI boundaries are
stable.
