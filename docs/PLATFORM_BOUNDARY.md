# Platform Boundary

v2.0 defines a local modular platform around the world engine. The platform
coordinates projects, packages, plugins, modules, campaigns, timeline branches,
authoring extensions, and provider routing. It does not replace the world
engine as the source of truth.

## Responsibilities

- Platform layer: package/plugin/module discovery, compatibility checks, local
  project metadata, and release gates.
- World engine layer: GameState, StateDelta, EventLog, rules, visibility, and
  saves.
- RP layer: expressive dialogue and style only.
- Authoring layer: preview, validation, and explicit save for draft content.
- Module layer: manifest-only gameplay extensions routed through ActionRegistry.
- Provider layer: LLMProvider / ProviderRouter only.
- Desktop layer: local UI and startup helpers; it cannot bypass backend APIs.

## Hard Boundaries

- Plugins and modules cannot directly modify GameState.
- All gameplay state changes still go through StateDelta and EventLog.
- Visibility remains authoritative; compatibility shims cannot reveal hidden
  data.
- LLMs are language tools, not world judges.
- Platformization does not mean arbitrary code plugins.
- Secrets, hidden facts, debug data, raw prompts, and raw state deltas do not
  enter player APIs, safe packages, logs, or normal reports.

