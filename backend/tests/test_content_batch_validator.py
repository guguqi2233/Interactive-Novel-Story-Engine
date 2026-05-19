from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from shutil import copytree

import yaml

from app.engine.content.character_pack_builder import CharacterPack, CharacterPackManifest
from app.engine.content.content_batch_validator import (
    BatchPackageType,
    ContentBatchValidationRequest,
    ContentBatchValidationTarget,
    validate_content_batch,
)


def _roots(tmp_path: Path) -> tuple[Path, Path]:
    worlds_root = tmp_path / "worlds"
    packages_root = tmp_path / "packages"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    packages_root.mkdir()
    return worlds_root, packages_root


def test_batch_validator_valid_packages_pass(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    pack = CharacterPack(
        manifest=CharacterPackManifest(
            pack_id="safe_pack",
            name="Safe Pack",
            exported_at="2026-01-01T00:00:00Z",
        )
    )
    (packages_root / "safe_pack.json").write_text(pack.model_dump_json(), encoding="utf-8")

    report = validate_content_batch(
        ContentBatchValidationRequest(
            worlds_root=str(worlds_root),
            packages_root=str(packages_root),
            targets=[
                ContentBatchValidationTarget(package_type=BatchPackageType.WORLD, id="mist_valley"),
                ContentBatchValidationTarget(package_type=BatchPackageType.CHARACTER_PACK, id="safe_pack", path="safe_pack.json"),
            ],
        )
    )

    assert report.total == 2
    assert report.passed == 2
    assert report.failed == 0


def test_batch_validator_invalid_package_fails(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    (packages_root / "bad_quest.yaml").write_text("not_quests: []\n", encoding="utf-8")

    report = validate_content_batch(
        ContentBatchValidationRequest(
            worlds_root=str(worlds_root),
            packages_root=str(packages_root),
            targets=[ContentBatchValidationTarget(package_type=BatchPackageType.QUEST_PACK, id="bad_quest", path="bad_quest.yaml")],
        )
    )

    assert report.failed == 1
    assert report.per_package_report[0].status == "failed"


def test_batch_validator_mixed_batch_aggregates(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    (packages_root / "bad_quest.yaml").write_text("not_quests: []\n", encoding="utf-8")

    report = validate_content_batch(
        ContentBatchValidationRequest(
            worlds_root=str(worlds_root),
            packages_root=str(packages_root),
            targets=[
                ContentBatchValidationTarget(package_type=BatchPackageType.WORLD, id="mist_valley"),
                ContentBatchValidationTarget(package_type=BatchPackageType.QUEST_PACK, id="bad_quest", path="bad_quest.yaml"),
            ],
        )
    )

    assert report.total == 2
    assert report.passed == 1
    assert report.failed == 1
    assert report.aggregate_issues


def test_batch_validator_rejects_path_traversal(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)

    report = validate_content_batch(
        ContentBatchValidationRequest(
            worlds_root=str(worlds_root),
            packages_root=str(packages_root),
            targets=[ContentBatchValidationTarget(package_type=BatchPackageType.QUEST_PACK, id="bad", path="../outside.yaml")],
        )
    )

    assert report.failed == 1
    assert "escapes package root" in report.per_package_report[0].errors[0].message


def test_batch_validator_normal_report_redacts_hidden_details(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    (packages_root / "bad.yaml").write_text("hidden_secret: sk-real-looking-secret\n", encoding="utf-8")

    report = validate_content_batch(
        ContentBatchValidationRequest(
            worlds_root=str(worlds_root),
            packages_root=str(packages_root),
            targets=[ContentBatchValidationTarget(package_type=BatchPackageType.QUEST_PACK, id="bad", path="bad.yaml")],
        )
    )

    payload = report.model_dump_json()
    assert "hidden_secret" not in payload
    assert "sk-real-looking-secret" not in payload


def test_batch_validator_script_package_rejects_executable(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    script_dir = packages_root / "script_package"
    script_dir.mkdir()
    (script_dir / "run.py").write_text("print('nope')\n", encoding="utf-8")

    report = validate_content_batch(
        ContentBatchValidationRequest(
            worlds_root=str(worlds_root),
            packages_root=str(packages_root),
            targets=[ContentBatchValidationTarget(package_type=BatchPackageType.SCRIPT_PACKAGE, id="script_package")],
        )
    )

    assert report.failed == 1
    assert any(issue.code == "batch_script_executable_rejected" for issue in report.aggregate_issues)


def test_batch_validator_script_package_rejects_sensitive_files_and_secrets(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    script_dir = packages_root / "script_package"
    script_dir.mkdir()
    (script_dir / ".env").write_text("LLM_API_KEY=sk-real-looking-secret\n", encoding="utf-8")
    (script_dir / "debug.db").write_text("sqlite", encoding="utf-8")
    (script_dir / "notes.yaml").write_text("api_key: sk-real-looking-secret\n", encoding="utf-8")

    report = validate_content_batch(
        ContentBatchValidationRequest(
            worlds_root=str(worlds_root),
            packages_root=str(packages_root),
            targets=[ContentBatchValidationTarget(package_type=BatchPackageType.SCRIPT_PACKAGE, id="script_package")],
        )
    )

    codes = {issue.code for issue in report.aggregate_issues}
    payload = report.model_dump_json()
    assert report.failed == 1
    assert "batch_script_sensitive_file_rejected" in codes
    assert "batch_script_secret_rejected" in codes
    assert "sk-real-looking-secret" not in payload


def test_batch_validator_cli_runs(tmp_path: Path) -> None:
    worlds_root, packages_root = _roots(tmp_path)
    command = [
        sys.executable,
        "-m",
        "app.tools.batch_validate_content",
        "--worlds-root",
        str(worlds_root),
        "--packages-root",
        str(packages_root),
        "--target",
        "world:mist_valley",
        "--json",
    ]

    result = subprocess.run(command, cwd=Path.cwd() / "backend", text=True, capture_output=True, check=False)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["passed"] == 1
