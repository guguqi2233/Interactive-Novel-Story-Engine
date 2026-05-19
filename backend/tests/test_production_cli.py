from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from shutil import copytree


def _run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "app.tools.production", *args],
        cwd=cwd or Path.cwd() / "backend",
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_world_wizard_preview_json(tmp_path: Path) -> None:
    result = _run(
        [
            "--json",
            "--worlds-root",
            str(tmp_path / "worlds"),
            "world-wizard",
            "--world-id",
            "cli_world",
            "--name",
            "CLI World",
            "--preview",
        ]
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["writes_to_disk"] is False
    assert payload["validation"]["ok"] is True


def test_cli_apply_requires_explicit_parameter(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    result = _run(
        [
            "--json",
            "--worlds-root",
            str(worlds_root),
            "--packages-root",
            str(tmp_path / "packages"),
            "build-script-package",
            "--package-id",
            "cli_script",
            "--name",
            "CLI Script",
            "--file",
            "beats/opening.yaml=beats: []",
        ]
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert payload["applied"] is False
    assert not (tmp_path / "packages").exists()


def test_cli_batch_validate_runs(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")

    result = _run(
        [
            "--json",
            "--worlds-root",
            str(worlds_root),
            "batch-validate",
            "--target",
            "world:mist_valley",
        ]
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["passed"] == 1


def test_cli_script_package_build_with_apply(tmp_path: Path) -> None:
    result = _run(
        [
            "--json",
            "--packages-root",
            str(tmp_path / "packages"),
            "build-script-package",
            "--package-id",
            "cli_script_apply",
            "--name",
            "CLI Script Apply",
            "--worlds",
            "mist_valley",
            "--dependencies",
            "mist_valley",
            "--file",
            "beats/opening.yaml=beats: []",
            "--apply",
        ]
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["applied"] is True
    assert (tmp_path / "packages" / "script_packages" / "cli_script_apply" / "script_package_manifest.json").exists()


def test_cli_redacts_hidden_details(tmp_path: Path) -> None:
    result = _run(
        [
            "--json",
            "--packages-root",
            str(tmp_path / "packages"),
            "build-script-package",
            "--package-id",
            "cli_redact",
            "--name",
            "CLI Redact",
            "--file",
            "notes/readme.yaml=hidden secret sk-real-looking-key",
        ]
    )

    assert result.returncode == 1
    assert "sk-" not in result.stdout
    assert "hidden" not in result.stdout.lower()
    assert "secret" not in result.stdout.lower()


def test_cli_invalid_input_returns_nonzero(tmp_path: Path) -> None:
    result = _run(
        [
            "--json",
            "--worlds-root",
            str(tmp_path / "worlds"),
            "world-wizard",
            "--world-id",
            "../bad",
            "--name",
            "Bad",
        ]
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
