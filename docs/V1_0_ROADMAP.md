# v1.0 Roadmap: Stable Local Studio Edition

## Goal

v1.0 turns the project into a stable local studio edition. The focus is
freezing contracts, hardening tests, finishing documentation, preserving save
compatibility, and keeping the local workflow understandable over time.

The project remains local personal software. The world engine is the fact
source. The LLM is a language layer, not the world judge.

## In Scope

1. Core API freeze.
2. Content pack schema freeze.
3. Save migration guarantee.
4. Mod packaging stable contract.
5. Quality gate hardening.
6. Flaky test and regression stability pass.
7. Performance budget finalization.
8. Security and privacy hardening.
9. `mist_valley` sample world polish.
10. Starter templates finalization.
11. Authoring UI final polish.
12. Desktop startup reliability.
13. Documentation finalization.
14. End-to-end local workflow guide.
15. Upgrade guide from v0.x to v1.0.
16. Release checklist automation through documented criteria and quality gate.

## Out Of Scope

- LLM world judging.
- Cloud sync, accounts, multiplayer, or online collaboration.
- Arbitrary mod code execution.
- Online marketplace.
- Formal signed desktop installer, code signing, or auto-update.
- Large new gameplay systems.
- Large frontend architecture rewrites.
- Automatic rewriting of user worlds.
- Performance optimizations that bypass `StateDelta`, `EventLog`, validation,
  or visibility boundaries.
- Breaking v0.9 save compatibility without a tested migration path.

## Frozen Contracts

- `GameState`, `StateDelta`, `Event`, and EventLog semantics.
- Content pack YAML schema.
- Save migration dry-run/apply behavior and failure safety.
- Mod manifest and content-only mod validation.
- `LLMProvider` interface and provider factory selection.
- Player, authoring, debug, migration, mod, studio, and quality API contracts.

## Required Boundaries

- All state changes go through `StateDelta`.
- Player actions, system ticks, NPC planning ticks, and playtest actions record
  `Event` entries.
- Hidden facts, NPC secrets, hidden witnesses, hidden relationships, hidden map
  edges, hidden items, hidden memory, debug memory, and raw `state_deltas` do
  not enter player-visible output.
- Authoring/debug/perf/eval/playtest/quality APIs are trusted-local tooling.
- API keys never enter frontend code, frontend builds, content packs, saves,
  reports, or logs.
- Quality scores are heuristics, not absolute design judgments.

## Validation

v1.0 release candidates must satisfy `docs/V1_0_RELEASE_CRITERIA.md`, including:

- `python -m pytest`
- `cd frontend && npm.cmd run build`
- quality gate
- hidden leak suite
- save/load/migration stress
- scenario regression suite
- performance benchmark smoke checks

## v1.1 Candidates

- Optional process stop/status helper for desktop launcher.
- More sample worlds and templates.
- More ergonomic visual editor interactions.
- More explicit quality report history and comparison views.
- Further local provider compatibility adapters, still behind `LLMProvider`.
