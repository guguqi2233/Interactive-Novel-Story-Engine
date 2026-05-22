# v2.8 Roleplay Immersion Contract Review

## Existing RP Contracts

Tavern Studio stores project-local characters, sessions, messages, memory,
scene mood presets, relationship tone, lore context, and Tavern-to-World
proposals. Existing contracts already treat Tavern output as RP material rather
than authoritative world state.

World NPC to Tavern adapters use safe summaries and exclude NPC secrets from
player-safe drafts. Tavern-to-World outcomes are proposals and must be validated
before any apply flow.

## Existing Tavern Prompt Context

`TavernPromptContext` contains safe character, RP, voice, scene mood,
relationship tone, recent messages, Tavern-safe memory, and safe lorebook
entries. It rejects API keys, raw `state_delta`, hidden fact markers, and
private persona markers.

v2.8 adds stricter mature-aware boundaries: `mature_only`, `hidden`, and
`debug_only` material must not enter ordinary Tavern/Novel/World prompt context.

## Existing Memory Boundaries

Tavern and project memory are non-authoritative. They can influence expression,
tone, and continuity, but they do not create World facts. Debug/hidden memory is
excluded from normal prompt context.

v2.8 introduces explicit mature memory partitioning. Mature memory is exported
and prompted only when mature policy is enabled and explicit include flags are
set.

## Existing Cross-Mode Boundaries

Novel/Tavern to World flows are draft/proposal based. World application must
remain explicit and must go through `StateDelta` and `EventLog`. Cross-mode
normal summaries already redact debug and hidden material.

v2.8 requires Tavern-to-World proposals to carry RP safety metadata. Mature
content cannot become World facts.

## Existing Provider Safety Support

Provider profiles already have `ProviderSafetyPolicy`, safe summaries, and
secret-free profile storage. v2.8 extends provider safety with content ratings,
mature routing flags, explicit-adult defaults, and local-only mature routing
requirements.

## Mature Content Current Status

Mature runtime behavior is default-off. v2.8 implements policy, boundary,
fade-to-black, memory isolation, export filtering, mature-aware provider
routing, mature mod policy, and quality gates. It does not implement online
adult content services, age verification, cloud sync, public mature content
distribution, NSFW images, or arbitrary-code plugins.

## Risks Before v2.8

- RP context can grow large enough to accidentally include hidden, private, or
  mature-only material if filtering is inconsistent.
- Cross-mode RP proposals need explicit metadata so mature/RP content cannot be
  confused with World facts.
- Export paths must share mature filtering instead of relying on one-off string
  checks.
- Provider fallback must obey the same mature safety policy as primary routing.

## Recommended v2.8 Contract Shape

- RP memory, emotion arcs, relationship tone, voice lab, and scene mood are
  expression metadata only.
- Mature Module is disabled by default.
- Adult/known-age, consent, boundary, provider policy, and export policy checks
  are deterministic local code.
- Ordinary prompts, exports, reports, and UI exclude hidden facts, NPC secrets,
  private persona, debug memory, raw `state_deltas`, mature memory, API keys,
  and provider secrets.
- Tavern-to-World changes remain proposals until validated and explicitly
  applied through World Engine authority.
