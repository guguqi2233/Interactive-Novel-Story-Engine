# v3.2 Roadmap: Tavern Studio UI Pro

## Version Goal

v3.2 makes Tavern Studio a more usable local RP workspace. The release focuses
on local-first RP authoring, session review, safety visibility, and Cross-Mode
review. It does not add online RP, accounts, cloud sync, online marketplaces,
remote character downloads, or default Mature Module enablement.

## Scope

- Tavern Studio UI Contract Review.
- Tavern Workspace Layout Polish.
- Character Card Library UI.
- Tavern Character / RP / Voice Profile Editor.
- Single Character Chat Pro.
- Multi-NPC Scene UI Pro.
- RP Memory Panel.
- Emotion Arc Panel.
- Relationship Tone Panel.
- Scene Mood Preset UI.
- Character Voice Lab UI.
- Boundary / Mature Settings UI Polish.
- Tavern Prompt / Provider UX Polish.
- Tavern Session Search / Tags / Filters.
- Tavern -> World Proposal Review UX Pro.
- Tavern -> Novel Scene Draft UX Pro.
- World NPC -> Tavern Character UX Pro.
- RP Safety Dashboard.
- Tavern Session Export / Backup UX.
- Tavern Local Preferences.
- Tavern Recovery / Unsaved Session UX.
- Tavern UI Component Cleanup.
- Tavern UI regression / build checks.

## Non-Goals

- Account system.
- Cloud sync.
- Online RP platform.
- Online marketplace.
- Remote character-card download.
- Remote package auto-download.
- Multi-user collaboration.
- Mature content default enablement.
- Direct Tavern-to-GameState mutation.
- LLM authority changes.

## Architecture Boundaries

- Tavern Mode is an RP draft/session mode.
- Tavern UI does not directly modify `GameState`.
- Tavern -> World remains proposal, validation, dry-run, and explicit apply.
- Tavern -> Novel creates Novel draft material only.
- World NPC -> Tavern creates Tavern drafts/references only.
- World Engine remains the authority for facts.
- Provider Gateway remains the model access boundary.
- API keys only come from env/local secret resolver and never enter frontend,
  exports, backups, diagnostics, logs, or Tavern packages.
- Hidden facts, NPC secrets, private persona, mature memory, debug memory, raw
  prompts, and raw `state_deltas` do not enter normal Tavern UI.

## Security / Privacy Requirements

- Mature Module is disabled by default.
- Mature/private content is hidden and excluded from normal exports by default.
- Tavern export defaults exclude API keys, hidden facts, NPC secrets,
  mature/private memory, debug data, raw prompts, and raw `state_deltas`.
- Tavern recovery drafts must not store prompt context, API keys, hidden facts,
  NPC secrets, mature/private content, or debug memory.
- Tavern preferences store only safe IDs and booleans.
- World NPC adapter `player_safe` mode excludes NPC secrets and player-unknown
  facts.

## Testing / Verification

Required checks:

```powershell
python -m pytest
cd frontend
npm.cmd run build
npm.cmd run check:v32-tavern-ui
```

Tests must not call real providers, upload data, or require online services.

## Known Limitations

v3.2 is a local UI polish release, not a complete online RP product. Some
advanced panels may initially show safe summaries or disabled states when deeper
backend data is unavailable. Mature/private workflows remain opt-in policy
surfaces and are not enabled by default.

## Recommended v3.3 Priorities

- World Studio UI Pro.
- World workspace layout.
- Map / Quest / Inventory / Combat panels.
- Economy and faction-war dashboards.
- Timeline replay and debug-gated world inspection.
- World quality and validation UX polish.
