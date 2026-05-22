# v2.8 Acceptance Report: Roleplay Immersion & Mature Module

## Verdict

Accepted with known limitations.

v2.8 is accepted as a local-first Roleplay Immersion & Mature Module release
candidate. The implementation adds RP immersion contracts, default-off mature
policy infrastructure, mature memory/export isolation, provider safety routing,
Multi-NPC Tavern support, RP safety/quality checks, cross-mode hardening, and
v2.8 integration regression coverage without changing the core authority model.

No high-risk v2.8 acceptance blocker remains in the current verification pass.

## Verification Date

2026-05-23

## Verification Commands

```powershell
python -m pytest
```

Result:

```text
1679 passed in 105.71s (0:01:45)
```

```powershell
cd frontend
npm.cmd run build
```

Result:

```text
tsc -b && vite build
vite v7.3.3 building client environment for production...
30 modules transformed.
built in 1.05s
```

Note: Vite reported the existing chunk-size warning for the main bundle
(`assets/index-*.js` over 500 kB after minification). This is not a v2.8
acceptance blocker.

## Scope Accepted

The following v2.8 scope is accepted for the current implementation:

- Roleplay Immersion Contract Review exists in
  `docs/V2_8_ROLEPLAY_CONTRACT_REVIEW.md`.
- Advanced RP memory is represented by `AdvancedRPMemoryRecord` and related
  filtering rules; RP memory remains non-authoritative.
- Emotion Arc System is represented by `EmotionState` and `EmotionArc`, with
  bounded intensity and prompt-safe context rules.
- Relationship Tone Pro is represented by `RelationshipToneProfile` and
  `RelationshipToneProService`, with bounded tone dimensions and proposal-only
  world impact.
- Multi-NPC Scene Pro backend is available through Tavern scene services and
  `/projects/{project_id}/tavern/multi-scenes` endpoints.
- Multi-NPC Scene Pro frontend is available in the Studio UI and builds
  successfully.
- Scene Mood Preset Pro supports expression-only mood context and does not
  enable hidden fact access.
- Character Voice Lab supports text voice profile and sample management without
  changing world facts.
- Roleplay Boundary Profiles default to safe behavior, including
  `mature_allowed=false`.
- Mature Content Rating Framework exists through `ContentRating` and
  `MatureContentPolicy`, with mature content disabled by default.
- Consent / Boundary System exists through `ConsentState`,
  `BoundaryCheckResult`, and `BoundaryCheckService`.
- Fade-to-Black Mode exists through `FadeToBlackPolicy` and
  `FadeToBlackRenderer`, using deterministic safe text.
- Mature Memory Partition isolates `mature_only` memory from normal Tavern,
  Novel, World, export, and quality contexts by default.
- Provider Safety Routing checks mature policy, provider content rating
  allowance, explicit-adult defaults, and local-only constraints.
- Mature Export Controls default to excluding mature memory/content, boundary
  private notes, debug memory, and secrets.
- Mature Module Settings UI exposes local policy metadata while keeping mature
  content disabled by default and without rendering mature memory bodies,
  secrets, raw env, or API keys.
- RP Safety Evals, RP Style Quality Checks, and RP-World Consistency checks are
  present and covered by tests.
- Cross-Mode RP Bridge hardening keeps Tavern-to-World proposal-only and filters
  mature memory from normal cross-mode views.
- Mature Module import/export/mod policy warns on mature packages, keeps them
  disabled by default, and rejects unsafe hidden-access/provider-secret patterns.
- Mature / RP Quality Gate is integrated with project quality checks and scans
  deterministic local artifacts for mature/RP blockers.
- v2.8 integration regression tests are present in
  `backend/tests/test_v28_roleplay_mature_module.py` and
  `backend/tests/test_v28_integration_regression.py`.

## Boundary Review

The v2.8 boundary remains aligned with the project architecture:

- LLM remains the language layer, not the world judge.
- World Engine remains the authoritative source of facts.
- Tavern/RP memories, emotion arcs, relationship tone, voice profiles, and mood
  presets are presentation and proposal metadata; they do not directly mutate
  `GameState`.
- Multi-NPC scene generation writes Tavern messages only. It does not write
  `EventLog` and does not mutate active `GameState`.
- Per-speaker Multi-NPC prompt context is constrained to safe known facts,
  safe RP/voice/mood context, relevant safe memory, and relationship tone safe
  summaries.
- Hidden facts, NPC secrets, debug memory, raw `state_deltas`, mature-only
  memory, API keys, provider secrets, and raw env are excluded from normal RP
  prompts and reports.
- Mature Module is optional and disabled by default.
- Unknown-age, minor-age, unwilling, coerced, intoxication/unconscious, or
  otherwise boundary-failing mature scenarios are blocked or routed to
  fade-to-black by deterministic local checks.
- LLM is not used to judge age, consent, relationship boundaries, mature policy,
  provider safety pass/fail, or quality gate pass/fail.
- Provider Gateway remains the only model entry point. Mature routing must pass
  both project policy and `ProviderSafetyPolicy`.
- Normal export excludes mature content/memory, boundary private notes, debug
  material, API keys, provider secrets, database files, logs, caches, and build
  artifacts.
- Tavern-to-World changes remain proposal/validation/explicit-apply only; RP
  content is not treated as world fact.

## Known Limitations

- v2.8 does not implement an online adult-content platform, account system,
  mature cloud sync, age verification service, NSFW image generation, or
  arbitrary-code mature plugins.
- Mature Module enablement is local policy metadata; it is not an external age
  verification or legal compliance service.
- Fade-to-black uses deterministic safe templates. It is intentionally not an
  explicit-content generator.
- Multi-NPC Scene Pro is an MVP for safe local Tavern orchestration, not a full
  autonomous multi-agent society simulation.
- Character Voice Lab is text-only. It does not implement TTS or voice audio.
- Provider safety routing depends on local provider profile declarations and
  project policy; it cannot prove an external provider's real-world moderation
  behavior.
- The frontend build still emits a Vite chunk-size warning. This is a packaging
  optimization target, not a correctness blocker.
- Current working tree includes expected v2.7/v2.8 source, test, frontend, and
  documentation changes that are not yet committed.

## Acceptance Risks

- Future richer provider-backed Multi-NPC replies must keep per-NPC knowledge
  filtering and prompt redaction tests in place.
- Any new export path must explicitly reuse mature export filtering rather than
  hand-rolling a separate serializer.
- Any future mature package type must keep default-disabled import behavior and
  reject hidden fact access, provider secrets, executable payloads, and policy
  bypasses.
- Any UI that exposes authoring/debug views must continue to separate normal
  safe views from mature/private/debug content.
- Quality gate artifact scanning is deterministic and local; new project file
  layouts should add tests so blocker detection does not become path-fragile.

## Recommended v2.9 Priorities

- Quality Studio Pro: consolidate v2.1-v2.8 release confidence into a stronger
  dashboard for acceptance, audits, quality gates, visibility checks, provider
  policy diagnostics, and export/report redaction.
- Add richer local diagnostics for RP/Mature prompt redaction and per-NPC prompt
  context previews without exposing sensitive text in normal UI.
- Add export/report visual diff tools that prove mature/private/debug material
  is removed from normal outputs.
- Consider Online-Ready Architecture only after local privacy, mature policy,
  provider routing, and export boundaries are fully audited for that mode.

## Final Status

v2.8 is accepted for the current local-first release scope.

Final status: PASS. The full backend suite and frontend production build pass,
the required v2.8 audits and contract review exist, and no high-risk RP/Mature
boundary blocker remains in the current acceptance pass.
