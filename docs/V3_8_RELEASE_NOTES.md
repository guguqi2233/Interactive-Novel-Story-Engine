# v3.8 Release Notes - Chinese Product UX Polish

## 1. Version Name

v3.8 Chinese Product UX Polish

中文名称：v3.8 中文产品体验打磨版

## 2. Version Goal

v3.8 focuses on polishing the Chinese local product experience introduced by v3.7. It does not add a large new system. The goal is to make the application feel less like a developer dashboard and more like a local Chinese product that helps users quickly start writing novels, running Tavern RP, playing in the open world, configuring model services, recovering from backend connection issues, and finding advanced tools when needed.

v3.8 keeps the existing local-first architecture:

- No account system.
- No cloud sync.
- No online marketplace.
- No remote package auto-download.
- No online writing, RP, or play platform.
- No arbitrary-code plugin support.
- No World Engine rule changes.
- No Provider Gateway semantic changes.
- No StateDelta / EventLog / Visibility boundary changes.

## 3. Product Home UX Improvements

The Home page is now product-oriented and Chinese-first.

Highlights:

- Home emphasizes `写小说`, `角色 RP`, and `大世界游玩`.
- Home shows project status, recent projects, open/create project entry points, Provider status, local safety summary, next-step suggestions, and Demo project access.
- Home no longer defaults to a developer-style dashboard full of Debug, Replay, StateDelta, Product Readiness, or disabled panels.
- No-project state emphasizes opening/creating a project, configuring model service, or trying the Demo project.

## 4. Backend Unavailable Recovery UX

v3.8 adds a clearer Chinese recovery state when the local backend is unavailable.

The recovery card includes:

- `本地后端未连接`.
- Current API address as a safe summary.
- Common causes such as backend not started, port mismatch, or local service issue.
- Actions for reconnecting, viewing startup guidance, opening diagnostics, and opening settings.

The recovery state does not show raw env, API keys, Authorization headers, raw provider errors, hidden facts, raw state deltas, or sensitive local paths.

## 5. First-Run Tour Simplification

The first-run tour is simplified into a product guide rather than a full checklist wall.

The tour now focuses on:

- Local-first introduction.
- Opening or creating a project.
- Configuring model service.
- Testing connection and reading models.
- Assigning models by mode.
- Choosing a start path: novel writing, Tavern RP, or open-world play.
- Backup and privacy basics.

Full steps remain discoverable, but the default view focuses on the current step.

## 6. Three Main Modes Entry Polish

The three core modes are more visible on Home:

- `写小说`: manuscript, chapter, outline, scene, and Novel Studio entry.
- `角色 RP`: character selection, Tavern sessions, RP memory, and Tavern Studio entry.
- `大世界游玩`: start/continue world, visible world panels, and World Studio entry.

Each main card gives a current status, next step, recent content summary, Provider/model readiness, and a primary action.

## 7. Provider Setup UX Polish

Provider setup is presented as a Chinese step-by-step model service wizard.

Covered setup flow:

1. Select Provider/model service type.
2. Fill Base URL.
3. Choose API key source.
4. Manually test connection.
5. Fetch or manually add models.
6. Assign models by use case.
7. Save safe configuration.

Provider setup explains:

- What a model service is.
- What Base URL means.
- What an API Key is.
- How `api_key_env`, `secret_ref`, and `local_secret_ref` work.
- Why model lists are useful.
- Why Novel, Tavern, World, Cross-Mode, and Quality can use different models.
- Why JSON/structured-output capability matters for world input parsing.
- Relay-style configuration means user-supplied compatible API settings, not API resale.

Real provider connections remain user-triggered only. Tests and CI still use fake/local_stub providers.

## 8. Chinese Copy Consistency

v3.8 improves Chinese copy consistency across core product areas:

- Home.
- Sidebar navigation.
- First-run tour.
- Provider setup.
- Novel/Tavern/World entry points.
- Settings.
- Backup and Diagnostics.
- QA / Debug advanced tools.
- Empty, error, and disabled states.
- Inline help and Product Guide references.

Some technical terms remain bilingual where useful, such as Provider, Base URL, ModelProfile, Debug, Quality Gate, StateDelta, and EventLog.

## 9. Advanced Tools Collapse

Advanced tools are retained but no longer dominate the default product surface.

Advanced tools include:

- Cross-Mode.
- Authoring / Mods.
- Quality Gate.
- Debug / Replay.
- Diagnostics.
- Export.
- Product Readiness.
- StateDelta Viewer.
- EventLog Viewer.
- Hidden Leak Report.

Debug and Replay remain gated and advanced. Raw debug details remain behind DebugGate.

## 10. Empty / Error / Disabled State Improvements

v3.8 improves empty, error, and disabled states with Chinese explanations and next steps.

Examples:

- Missing project -> open/create project or try Demo.
- Missing Provider -> configure model service.
- Missing model assignment -> assign models by use case.
- Backend unavailable -> reconnect, startup guide, diagnostics, settings.
- Debug disabled -> enable `ENABLE_DEBUG_API` to view debug tools.
- No manuscript/character/save -> create manuscript, create/import character, or start world.

Error text is redacted and avoids stack traces, raw env, secrets, sensitive paths, and raw provider responses.

## 11. Demo Project Entry Experience

Home includes a clearer Demo project entry.

The Demo project:

- Uses `examples/demo_local_narrative_project`.
- Uses fake/local_stub provider configuration.
- Requires no real API key.
- Provides a safe path to try novel writing, Tavern RP, and open-world play.
- Does not upload data.
- Does not include mature/private content.
- Does not call a real provider by default.

## 12. Settings / Backup / Diagnostics Improvements

Settings and local operations are clearer for Chinese users.

Settings includes local product configuration areas such as:

- General.
- Model service.
- Model assignment.
- Local privacy.
- Export.
- Debug.
- Backup / Restore.
- Diagnostics.
- Mature Module.
- UI preferences.

Backup / Restore / Diagnostics now better explain:

- Dry-run first.
- Explicit confirmation before writes.
- No cloud backup.
- No diagnostics upload.
- Default exclusion of API keys, `.env`, Provider secrets, debug raw data, mature/private content, databases, logs, caches, and build outputs.

## 13. Privacy / Security Boundaries

v3.8 preserves existing privacy and security boundaries.

API keys must not enter:

- Project files.
- Frontend storage.
- Logs.
- Backups.
- Diagnostics.
- Exports.
- Mods.
- Prompt profiles.
- Tests.
- Documentation examples.

Normal UI must not show:

- Hidden facts.
- NPC secrets.
- Debug memory.
- Raw prompts.
- Raw outputs.
- Raw `state_deltas`.
- Provider secrets.
- Authorization headers.

World and LLM boundaries remain unchanged:

- World Engine remains the authority for facts and rules.
- LLMs are language/rendering providers, not world judges.
- World changes still go through backend APIs, StateDelta, and EventLog.
- Provider Gateway remains the only model routing boundary.
- Debug UI remains gated by `ENABLE_DEBUG_API` / DebugGate.

## 14. Known Limitations

- v3.8 is a UX polish release, not a new architecture release.
- Some deep advanced-tool panels still retain technical or English labels.
- v3.8 does not introduce a full i18n framework.
- Real LLM use depends on the user configuring a valid provider, Base URL, and safe key source.
- Backend unavailable UX guides recovery but does not execute arbitrary shell commands or automatically start services.
- Debug, QA, Authoring, and Diagnostics remain advanced local tools and may still feel technical.

## 15. Upgrade Notes from v3.7

Users upgrading from v3.7 should expect:

- A clearer Chinese Home page.
- Three main mode cards for novel writing, Tavern RP, and open-world play.
- Advanced tools folded away from the default Home screen.
- Better backend unavailable recovery messaging.
- More understandable Provider/model setup copy.
- Better empty/error/disabled states.
- A clearer Demo project entry.

No migration of World Engine state, save format, Provider Gateway semantics, StateDelta, EventLog, or visibility contracts is required for v3.8.

Tests and CI continue to use fake/local providers. Real providers are only used when a user manually configures and triggers them.

## 16. Recommended v3.9 Direction

Recommended v3.9 direction: Local Stable Candidate.

Suggested v3.9 priorities:

- Final Chinese copy pass for advanced Debug, QA, Authoring, and legacy panels.
- More direct routing from Home cards into Novel, Tavern, and World active workspaces.
- Further polish for real Provider setup and manual smoke-test guidance.
- Additional visual QA for small windows and desktop packaging.
- Release-candidate hardening for local project lifecycle, backup/restore, diagnostics, and export.
- Continued security, privacy, and boundary audits before v4.0.

v3.9 should continue toward a stable local candidate without adding account systems, cloud sync, online marketplaces, remote package downloads, online platforms, or arbitrary-code plugins.
