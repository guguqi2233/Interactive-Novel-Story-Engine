# v1.6 Acceptance Report

## Verdict

Accepted with non-blocking limitations.

v1.6 Advanced Gameplay Modules meets the release acceptance bar for a local
interactive novel world engine. Gameplay modules are declarative or trusted
rule-code extensions, not arbitrary code plugins. Runtime outcomes remain
rule-adjudicated, state changes remain `StateDelta` based, and gameplay action
execution remains evented and visibility-filtered.

The release-blocking hidden fact leak identified during final review was
fixed before this acceptance pass:

- Action DSL `ADD_FACT_DISCOVERY` no longer discovers hidden or unknown facts
  into `player_visible_facts`.
- Declarative action `visible_facts` are filtered at runtime so hidden facts in
  `GameState` do not enter player-visible action results.

## Verification Date

2026-05-20

## Verification Commands

```powershell
python -m pytest
cd frontend
npm.cmd run build
```

Observed results:

- `python -m pytest`: 1503 passed.
- `cd frontend && npm.cmd run build`: passed.
- Frontend build emitted the existing Vite chunk-size warning for a chunk above
  500 kB; this is not a functional failure.

## Scope Accepted

The following v1.6 scope is accepted:

1. Gameplay Module Boundary Contract.
2. Gameplay Module Manifest.
3. Declarative Action Mod System.
4. Action Registry Extension.
5. Action DSL Preconditions / Checks / Effects.
6. Action Mod Validation.
7. Action Mod Authoring UI.
8. Magic System.
9. Hacking System.
10. Crafting System.
11. Investigation / Deduction System.
12. Travel / Survival System.
13. Stealth Expansion.
14. Combat Expansion.
15. Social Manipulation System.
16. Faction Mission System.
17. Domain / Base Management.
18. Gameplay Module Quality Gate.
19. Gameplay Module Regression Playtests.
20. Gameplay Module Debugger.
21. Gameplay Module Import / Export.
22. v1.6 integration regression tests.

## Boundary Review

### Gameplay Module Boundary

Accepted.

- Arbitrary code execution is rejected by manifest permissions, loader checks,
  package import checks, executable-file rejection, and Action Mod authoring
  constraints.
- Modules do not directly mutate active `GameState`; module actions and rule
  systems return `StateDelta` values.
- Module actions record `Event` values for replay, debugging, and audit.
- LLMs do not adjudicate spell effects, hacking outcomes, crafting output,
  deduction truth, survival risks, stealth detection, combat results, social
  manipulation, faction mission completion, or domain income.

### Manifest / Action Mod

Accepted.

- `GameplayModuleManifest` validates permissions, dependencies, conflicts,
  state schema extensions, event types, save compatibility, and quality-test
  metadata.
- Declarative Action Mods can be registered through `ActionRegistry` and are
  resolved through `DeclarativeActionHandler`.
- Action DSL is constrained to schema-defined preconditions, checks, and
  effects. It does not evaluate arbitrary code, import modules, perform IO, or
  call the network.
- StateDelta path validation is active for module-defined templates.
- Action Mod validation is available from backend services and authoring
  flows.

### Gameplay Systems

Accepted.

- Magic supports deterministic spell definitions, resource consumption,
  effects, failure effects, visibility policy, and crime/witness integration.
- Hacking supports terminal/security/camera/log/trace actions with deterministic
  success/failure, alarms, traces, and visibility filtering.
- Crafting supports recipes, materials, tools, stations, time cost, success,
  failure policy, and inventory-safe deltas.
- Investigation / Deduction supports evidence, testimony, hypotheses,
  accusations, timeline reconstruction, hidden-truth safety, and quest/social
  consequences.
- Travel / Survival supports route travel, fatigue, hunger, thirst, rest,
  camp, forage, food/water consumption, weather, and seeded risk.
- Stealth Expansion supports hiding, following, distraction, noise, decoys,
  shadowing, detection checks, suspicion, witness/combat consequences, and
  hidden observer redaction.
- Combat Expansion supports weapon tags, stances, status effects, non-lethal
  attacks, flee risk, crime/witness/faction consequences, and hidden witness
  redaction.
- Social Manipulation supports persuade, threaten, bribe, deceive, provoke,
  comfort, blackmail, and extract-information using NPC knowledge,
  relationships, emotions, leverage, and reputation.
- Faction Mission System supports availability, accept, complete, fail,
  rewards, consequences, quest integration, reputation gates, and hidden
  mission filtering.
- Domain / Base Management supports claim, build, assign staff, upgrade, store,
  withdraw, collect income, upkeep, and bounded domain tick behavior.

### Quality / Debug / Import

Accepted.

- Gameplay Module Quality Gate runs manifest/action/safety/save compatibility
  checks and rejects unsafe modules.
- Gameplay Module Regression Playtests are deterministic and use temporary
  state.
- Gameplay Module Debugger is gated by `ENABLE_DEBUG_API`; dry-run does not
  modify active `GameState`.
- Module import/export rejects zip slip, executable files, dangerous
  permissions, checksum mismatch, sensitive local files, API keys, and package
  content that resembles secrets.
- Import apply requires explicit confirmation and does not automatically enable
  untrusted modules.

### Frontend

Accepted.

- Action Mod Authoring UI is available and supports declarative fields,
  validation, preview, and export without arbitrary code editing.
- Gameplay Module Debugger UI is available under debug surfaces.
- Disabled API states degrade safely.
- Frontend build passes.

### Core Boundary

Accepted.

- World engine remains the only fact source.
- LLM remains parser/narrator/style layer only.
- Module state changes use `StateDelta`.
- Module actions record `Event`.
- Hidden facts, NPC secrets, hidden targets, hidden witnesses, and debug data
  are filtered from player APIs and narrator-facing paths.
- Provider factory remains the only runtime provider entry point.
- Tests use mock/fake/local_stub-style providers and do not call real external
  APIs by default.

## Known Limitations

- Gameplay Module Quality Gate currently treats some regression coverage as
  declared metadata rather than executing every referenced regression artifact
  inside the gate itself. Dedicated regression tests exist and pass, but the
  gate can be made stricter in a future release.
- Action alias conflicts are detected and surfaced, but registry registration
  does not globally hard-fail every conflict at insertion time. Validation and
  authoring flows should continue treating conflicts as release-blocking for
  packages.
- Module Debugger dry-run returns StateDelta previews in debug API responses.
  The debug route is gated and hidden fact IDs are summarized/redacted, but a
  future hardening pass should recursively redact StateDelta preview values and
  metadata that resemble hidden text or secrets.
- Action Mod Authoring UI intentionally allows free-form declarative path input
  for local authors; backend validation remains the authority that rejects
  forbidden paths.
- Frontend bundle size remains above Vite's 500 kB warning threshold. This is
  a performance/maintainability warning, not a release blocker.

## Acceptance Risks

- Future module integrations must not bypass `ActionRegistry`,
  `ActionModValidation`, or package validation. The accepted boundary assumes
  module install/enable flows keep those gates in place.
- Any future use of `state_delta_preview` outside debug-only UI would risk
  exposing internal state. It must remain debug-only and redacted.
- Any future extension of fact-discovery effects must preserve the v1.6 fix:
  hidden facts cannot be promoted to `player_visible_facts` by generic Action
  Mod effects.
- LLM-assisted module draft generation, if added later, must remain
  authoring-only, fake/mock by default in tests, and validation-gated before
  export or enablement.

## Recommended v1.7 Priorities

1. Harden Module Debugger redaction for StateDelta preview values and metadata.
2. Make module quality gate execute referenced regression scenarios or require
   verifiable regression artifacts.
3. Upgrade alias conflict handling from warning-capable to mandatory
   blocking in package enablement.
4. Add a module dependency graph and save migration assistant for enabled
   gameplay modules.
5. Split player-facing action reasons from debug reasons where gameplay modules
   need richer diagnostics.
6. Add code-splitting for the frontend Studio panels to reduce build chunk
   size.
7. Expand deterministic module regression scenarios for combined module
   interactions, such as stealth + combat, hacking + faction missions, and
   investigation + social manipulation.

## Final Status

v1.6 is accepted for freeze.

Final status: PASS.

Release blocker status: no known high-risk blockers remain after the hidden
fact discovery fix.
