# Demo Local Narrative Project

This is a minimal local demo project for v3.7 Local Complete Product checks.
It is intentionally small, deterministic, and safe for local validation.

## What Is Included

- Project metadata for a local-first narrative project.
- A small harbor world with three locations, three NPCs, one short quest, a map,
  public facts, factions, relationships, and rumors.
- A short Novel manuscript outline, chapter draft, scene card, character arc,
  plot thread, and foreshadowing item.
- A Tavern character, voice/RP profile, session, safe messages, scene preset,
  and memory summary.
- Cross-Mode draft/proposal/review/apply-plan/audit markers that link Novel
  material to a World quest without applying changes.
- A fake local Provider profile using `local_stub` and model assignment metadata.
- Quality summary files for local demo and checklist review.
- A safe diagnostics preview marker for readiness checks; no backup archive or
  diagnostics bundle is included.

## Safety Notes

- No real provider credentials are included.
- No `.env`, database, log, cache, build output, backup archive, diagnostics
  bundle, or crash report files are included.
- The demo does not call a real provider.
- The demo does not upload data.
- The demo is not enabled by default; use it only as a local sample or test
  fixture.
- Cross-Mode content remains a draft/proposal-style artifact and does not apply
  world changes.

## Local Verification

From the repository root:

```powershell
python -m backend.app.tools.project_quality_gate examples/demo_local_narrative_project --profile fast --include-cross-mode --json
```

Optional focused test:

```powershell
python -m pytest backend/tests/test_v37_demo_local_project.py
```
