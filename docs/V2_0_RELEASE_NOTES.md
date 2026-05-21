# v2.0 Release Notes

## Version Name

v2.0 Modular Narrative RPG Platform

## Version Goal

v2.0 turns the local AI Narrative Studio into a modular narrative RPG platform
with stable local package, plugin, module, campaign, workspace, and compatibility
contracts.

## New Features

- Stable Plugin API.
- Stable Module API.
- Content Pack Schema v2.
- Save Migration Contract v2.
- Authoring Extension API.
- Provider Gateway v2.
- Package Contract v2.
- Local Module and Script Package Browser services.
- Workspace project, multi-campaign, timeline branch, character transfer, and
  long campaign management services.
- v2 release checklist automation.

## Breaking / Compatibility Notes

v2.0 does not promise unlimited v1.x compatibility. Legacy content enters
explicit shim, warning, migration, or safe-fail paths.

## Migration Notes

Save migration v2 requires dry-run first, backup before apply, EventLog
preservation, and hidden visibility preservation.

## Package / Plugin / Module Notes

Plugins and modules remain declarative. Package v2 rejects executable files,
zip slip paths, secrets, and hidden/debug payloads in safe exports.

## Frontend Changes

Frontend build remains compatible with the local studio. Additional v2.0 UI
polish is deferred to v2.1.

## Known Limitations

- No online marketplace.
- No cloud sync, accounts, or multi-user collaboration.
- LLM is still not the world judge.
- Arbitrary-code plugins are not enabled by default.
- Sample world content is local demo content, not commercial-complete content.

## Upgrade from v1.9

Run compatibility and release checklists before treating a workspace as v2.0
ready:

```bash
python -m backend.app.tools.v2_compatibility_checklist --json
python -m backend.app.tools.v2_release_candidate_checklist --json
python -m backend.app.tools.v2_release_checklist --json
```

## Recommended v2.1 Direction

Polish platform UI, expand compatibility fixtures, improve browser ergonomics,
and deepen long-campaign tools while preserving local-first boundaries.

