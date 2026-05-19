from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.script_package_builder import (
    ScriptPackageBuildRequest,
    ScriptPackageFile,
    ScriptPackageManifest,
    build_script_package,
    build_script_package_dry_run,
    export_script_package,
    validate_script_package,
)
from app.main import app
from app.session_store import InMemorySessionStore


def _request(tmp_path: Path, **overrides: object) -> ScriptPackageBuildRequest:
    manifest = ScriptPackageManifest(
        package_id="mist_intro_script",
        name="Mist Intro Script",
        included_worlds=["mist_valley"],
        included_quests=["find_the_old_road"],
        included_characters=["elder_mara"],
        included_templates=["opening_scene"],
        included_scenarios=["intro_regression"],
        included_quality_profile="default_safe",
        dependencies=["mist_valley"],
    )
    values: dict[str, object] = {
        "manifest": manifest,
        "files": [
            ScriptPackageFile(path="beats/opening.yaml", content="beats:\n  - id: opening\n    summary: Safe opening beat.\n"),
            ScriptPackageFile(path="notes/hidden_truth.yaml", content="truth: culprit redacted\n", hidden=True),
        ],
        "available_dependency_ids": ["mist_valley"],
        "packages_root": str(tmp_path / "packages"),
    }
    values.update(overrides)
    return ScriptPackageBuildRequest(**values)


def _client(tmp_path: Path) -> TestClient:
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "script_package.db")
    app.state.session_store = InMemorySessionStore(worlds_root=tmp_path / "worlds")
    app.state.worlds_root = tmp_path / "worlds"
    return TestClient(app)


def test_valid_script_package_build_dry_run_succeeds(tmp_path: Path) -> None:
    report = build_script_package_dry_run(_request(tmp_path))

    assert report.validation.ok
    assert report.dry_run is True
    assert report.applied is False
    assert report.manifest.package_id == "mist_intro_script"
    assert "script_package_payload.json" in report.files


def test_missing_dependency_is_caught(tmp_path: Path) -> None:
    report = validate_script_package(_request(tmp_path, available_dependency_ids=[]))

    assert report.validation.ok

    manifest = _request(tmp_path).manifest.model_copy(update={"dependencies": ["missing_pack"]})
    report = validate_script_package(_request(tmp_path, manifest=manifest, available_dependency_ids=["other_pack"]))

    assert not report.validation.ok
    assert any(issue.code == "script_package_missing_dependency" for issue in report.validation.errors)


def test_conflict_is_caught(tmp_path: Path) -> None:
    manifest = _request(tmp_path).manifest.model_copy(update={"conflicts": ["mist_valley"]})

    report = validate_script_package(_request(tmp_path, manifest=manifest))

    assert not report.validation.ok
    assert any(issue.code == "script_package_conflict_detected" for issue in report.validation.errors)


def test_package_rejects_api_key_and_env(tmp_path: Path) -> None:
    request = _request(
        tmp_path,
        files=[
            ScriptPackageFile(path=".env", content="LLM_API_KEY=sk-real-looking-secret"),
            ScriptPackageFile(path="notes/readme.yaml", content="api_key: sk-real-looking-secret"),
        ],
    )

    report = validate_script_package(request)

    assert not report.validation.ok
    codes = {issue.code for issue in report.validation.errors}
    assert "script_package_sensitive_file_rejected" in codes
    assert "script_package_secret_rejected" in codes


def test_checksum_generated(tmp_path: Path) -> None:
    report = build_script_package_dry_run(_request(tmp_path))

    assert report.manifest.checksums
    assert report.manifest.checksums["beats/opening.yaml"]
    assert report.manifest.checksums["script_package_payload.json"]


def test_executable_file_rejected(tmp_path: Path) -> None:
    report = validate_script_package(_request(tmp_path, files=[ScriptPackageFile(path="run.py", content="print('no')")]))

    assert not report.validation.ok
    assert any(issue.code == "script_package_executable_rejected" for issue in report.validation.errors)


def test_build_apply_writes_package_only_after_confirmation(tmp_path: Path) -> None:
    request = _request(tmp_path)
    blocked = build_script_package(request)

    assert not blocked.applied
    assert not (tmp_path / "packages").exists()

    confirmed = build_script_package(request.model_copy(update={"confirm_apply": True}))

    assert confirmed.applied
    assert (tmp_path / "packages" / "script_packages" / "mist_intro_script" / "script_package_manifest.json").exists()
    assert not (tmp_path / "worlds").exists()


def test_build_apply_rejects_existing_package_without_overwrite(tmp_path: Path) -> None:
    request = _request(tmp_path).model_copy(update={"confirm_apply": True})
    first = build_script_package(request)
    second = build_script_package(request)

    assert first.applied is True
    assert second.applied is False
    assert any(issue.code == "script_package_overwrite_rejected" for issue in second.validation.errors)


def test_export_zip_contains_manifest_and_checksums(tmp_path: Path) -> None:
    report = export_script_package(_request(tmp_path))

    assert report.archive_base64
    archive_bytes = base64.b64decode(report.archive_base64)
    with ZipFile(BytesIO(archive_bytes), "r") as archive:
        manifest = json.loads(archive.read("script_package_manifest.json"))
        assert manifest["package_id"] == "mist_intro_script"
        assert manifest["checksums"]["beats/opening.yaml"]
        assert "beats/opening.yaml" in archive.namelist()


def test_api_build_dry_run(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post(
        "/production/script-packages/build-dry-run",
        json=_request(tmp_path).model_dump(mode="json"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["validation"]["ok"] is True
    assert payload["applied"] is False
