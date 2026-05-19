from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.script_package_builder import (
    ScriptPackageBuildRequest,
    ScriptPackageFile,
    ScriptPackageManifest,
    build_script_package,
)
from app.main import app
from app.quality.batch_quality_gate import BatchQualityGateRequest, BatchQualityGateThresholds, run_batch_quality_gate
from app.session_store import InMemorySessionStore


def _roots(tmp_path: Path) -> tuple[Path, Path]:
    worlds_root = tmp_path / "worlds"
    packages_root = tmp_path / "packages"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    packages_root.mkdir()
    return worlds_root, packages_root


def _make_script_package(packages_root: Path, package_id: str = "safe_script") -> None:
    build_script_package(
        ScriptPackageBuildRequest(
            manifest=ScriptPackageManifest(package_id=package_id, name="Safe Script", included_worlds=["mist_valley"]),
            files=[ScriptPackageFile(path="beats/opening.yaml", content="beats: []")],
            available_dependency_ids=["mist_valley"],
            packages_root=str(packages_root),
            confirm_apply=True,
        )
    )


def _client(tmp_path: Path, *, authoring: bool = True) -> TestClient:
    worlds_root, packages_root = _roots(tmp_path)
    app.state.settings = Settings(enable_authoring_api=authoring, llm_provider="mock")
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "batch_quality.db")
    app.state.session_store = InMemorySessionStore(worlds_root=worlds_root)
    app.state.worlds_root = worlds_root
    app.state.mods_root = tmp_path / "mods"
    app.state.mods_root.mkdir()
    return TestClient(app)


def test_valid_batch_pass(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    _make_script_package(packages_root)

    report = run_batch_quality_gate(
        BatchQualityGateRequest(
            world_ids=["mist_valley"],
            package_ids=["script_packages/safe_script"],
            worlds_root=str(worlds_root),
            packages_root=str(packages_root),
            thresholds=BatchQualityGateThresholds(min_health_score=0),
        )
    )

    assert report.passed
    assert report.aggregate_summary["total"] == 2


def test_blocker_package_fails(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    bad = packages_root / "bad_script"
    bad.mkdir()
    (bad / "run.py").write_text("print('no')", encoding="utf-8")

    report = run_batch_quality_gate(
        BatchQualityGateRequest(
            package_ids=["bad_script"],
            worlds_root=str(worlds_root),
            packages_root=str(packages_root),
        )
    )

    assert not report.passed
    assert report.blockers


def test_warning_threshold_blocks(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    _make_script_package(packages_root)

    report = run_batch_quality_gate(
        BatchQualityGateRequest(
            package_ids=["script_packages/safe_script"],
            worlds_root=str(worlds_root),
            packages_root=str(packages_root),
            thresholds=BatchQualityGateThresholds(max_warnings=0),
            include_migration_check=False,
        )
    )

    assert not report.passed
    assert any("Warning threshold exceeded" in blocker for blocker in report.blockers)


def test_hidden_details_redacted(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    bad = packages_root / "bad_hidden"
    bad.mkdir()
    (bad / "run.py").write_text("hidden secret sk-real-looking-key", encoding="utf-8")

    report = run_batch_quality_gate(
        BatchQualityGateRequest(
            package_ids=["bad_hidden"],
            worlds_root=str(worlds_root),
            packages_root=str(packages_root),
        )
    )

    payload = report.model_dump_json().lower()
    assert "sk-" not in payload
    redacted_payload = payload.replace("hidden_details_redacted", "").replace("include_hidden_leak_suite", "")
    assert "hidden" not in redacted_payload
    assert "secret" not in payload


def test_api_batch_quality_gate(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post(
        "/production/batch-quality-gate",
        json={"world_ids": ["mist_valley"], "thresholds": {"min_health_score": 0}},
    )

    assert response.status_code == 200
    assert response.json()["aggregate_summary"]["total"] == 1


def test_cli_batch_quality_gate(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    _make_script_package(packages_root)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.tools.production",
            "--json",
            "--worlds-root",
            str(worlds_root),
            "--packages-root",
            str(packages_root),
            "batch-quality-gate",
            "--package",
            "script_packages/safe_script",
        ],
        cwd=Path.cwd() / "backend",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["passed"] is True
