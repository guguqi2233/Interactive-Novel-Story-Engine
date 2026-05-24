# Quality Gate Fixtures

This repository includes two small, deterministic fixtures for release-readiness
checks:

- `backend/tests/fixtures/projects/minimal_valid_project`
- `backend/tests/fixtures/mods/minimal_valid_action_mod`
- `fixtures/projects/v36_readiness_project`
- `mods/safe_content`
- `mods/sample_basic_action_mod`

They are local-only and safe by construction. They contain no API keys, provider
secrets, raw prompts, hidden facts, raw `state_deltas`, executable payloads,
remote download metadata, or online marketplace behavior.

## Recommended Commands

Run these commands from the repository root:

```powershell
python -m backend.app.tools.project_quality_gate backend/tests/fixtures/projects/minimal_valid_project --json --skip-world-quality-gate
python -m backend.app.tools.mod_quality_gate backend/tests/fixtures/mods/minimal_valid_action_mod --json
python -m backend.app.tools.mod_quality_gate mods/sample_basic_action_mod --json
python -m backend.app.tools.v2_release_checklist --json
python -m backend.app.tools.v2_release_candidate_checklist --json
```

Or use the local tool wrapper, which sets `PYTHONPATH=backend` and only runs
allowlisted backend tools:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tool.ps1 project_quality_gate backend/tests/fixtures/projects/minimal_valid_project --json --skip-world-quality-gate
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tool.ps1 mod_quality_gate mods/sample_basic_action_mod --json
```

```bash
scripts/run_tool.sh project_quality_gate backend/tests/fixtures/projects/minimal_valid_project --json --skip-world-quality-gate
scripts/run_tool.sh mod_quality_gate mods/sample_basic_action_mod --json
```

Some lower-level tools under `app.tools` require `PYTHONPATH=backend` when run
directly:

```powershell
$env:PYTHONPATH='backend'
python -m app.tools.compatibility_matrix --json
python -m app.tools.generate_contract_docs --check
```

The fixtures are not production content packs. They exist only to keep local
release checklist commands stable before v3.6 performance and accessibility
optimization work.
