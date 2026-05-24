from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROJECT_FIXTURE = ROOT / "backend" / "tests" / "fixtures" / "projects" / "minimal_valid_project"
MOD_FIXTURE = ROOT / "backend" / "tests" / "fixtures" / "mods" / "minimal_valid_action_mod"


def test_project_quality_gate_fixture_path_is_stable() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.app.tools.project_quality_gate",
            str(PROJECT_FIXTURE),
            "--json",
            "--skip-world-quality-gate",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert '"passed": true' in result.stdout


def test_mod_quality_gate_fixture_path_is_stable() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "backend.app.tools.mod_quality_gate",
            str(MOD_FIXTURE),
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert '"ok": true' in result.stdout
