import base64
import json
import os
import sqlite3
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from app.compatibility.contracts import (
    PACKAGE_CONTRACT_VERSION,
    STATEDELTA_CONTRACT_VERSION,
    deprecated_field_warnings,
    validate_contract_version,
)
from app.compatibility.matrix import CompatibilityCheckRequest, build_compatibility_matrix, check_compatibility
from app.compatibility.shims import apply_compatibility_shims
from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaError, StateDeltaOperation, validate_stable_delta_contract
from app.core.world_state import FactState, FactVisibility, GameState
from app.db.migrations import CURRENT_ENGINE_VERSION, CURRENT_SAVE_SCHEMA_VERSION, MigrationError, MigrationRegistry, SaveMigration
from app.db.repository import SQLiteSaveRepository
from app.engine.content.import_export import ImportExportService
from app.llm.prompt_profiles import PromptProfile
from app.llm.provider_capabilities import ProviderCapabilityRegistry
from app.tools.v2_compatibility_checklist import run_checklist


def test_core_contract_versions_and_delta_validation() -> None:
    state = GameState(world_id="contract_world")
    delta = StateDelta(operation=StateDeltaOperation.SET, path="flags.ready", value=True)
    event = Event(
        event_id="event-contract",
        turn=0,
        actor_id="player",
        action_type="test",
        result="ok",
        visible_to_player=True,
        state_deltas=[delta],
    )

    assert state.contract_version == "1.8"
    assert delta.contract_version == STATEDELTA_CONTRACT_VERSION
    assert event.contract_version == "1.8"

    with pytest.raises(StateDeltaError):
        validate_stable_delta_contract(
            StateDelta(operation=StateDeltaOperation.SET, path="secrets.api_key", value="x")
        )


def test_legacy_shim_warns_without_changing_visibility() -> None:
    payload = {
        "content_schema_version": "0.6",
        "facts": {"hidden_oath": {"visibility": "hidden"}},
    }

    result = apply_compatibility_shims(payload, scope="content_pack")

    assert result.payload["schema_version"] == "0.6"
    assert result.payload["facts"]["hidden_oath"]["visibility"] == "hidden"
    assert result.warnings
    assert deprecated_field_warnings({"content_pack": {"manifest": {"content_schema_version": "0.6"}}})


def test_package_missing_contract_version_is_rejected(tmp_path: Path) -> None:
    archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "bad_world"},
            "local_package_manifest.json": {
                "package_id": "bad_world",
                "package_type": "world",
                "version": "0.8.16",
                "engine_version_min": "0.8.0",
                "schema_version": CURRENT_SAVE_SCHEMA_VERSION,
                "included_files": ["worlds/bad_world/manifest.yaml"],
                "checksums": {"worlds/bad_world/manifest.yaml": _sha256_text("world_id: bad_world\nname: Bad\n")},
                "created_at": "2026-05-21T00:00:00Z",
            },
            "worlds/bad_world/manifest.yaml": "world_id: bad_world\nname: Bad\n",
        }
    )
    service = ImportExportService(
        worlds_root=tmp_path / "worlds",
        mods_root=tmp_path / "mods",
        templates_root=tmp_path / "templates",
        repository=SQLiteSaveRepository(tmp_path / "packages.db"),
    )

    report = service.dry_run_import_package(archive)

    assert report.ok is False
    assert any("missing contract_version" in error for error in report.errors)


def test_package_with_contract_version_still_rejects_checksum_mismatch(tmp_path: Path) -> None:
    archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "bad_world"},
            "local_package_manifest.json": {
                "package_id": "bad_world",
                "package_type": "world",
                "contract_version": PACKAGE_CONTRACT_VERSION,
                "version": "0.8.16",
                "engine_version_min": "0.8.0",
                "schema_version": CURRENT_SAVE_SCHEMA_VERSION,
                "included_files": ["worlds/bad_world/manifest.yaml"],
                "checksums": {"worlds/bad_world/manifest.yaml": "not-a-real-checksum"},
                "created_at": "2026-05-21T00:00:00Z",
            },
            "worlds/bad_world/manifest.yaml": "world_id: bad_world\nname: Bad\n",
        }
    )
    service = ImportExportService(
        worlds_root=tmp_path / "worlds",
        mods_root=tmp_path / "mods",
        templates_root=tmp_path / "templates",
        repository=SQLiteSaveRepository(tmp_path / "packages.db"),
    )

    report = service.dry_run_import_package(archive)

    assert report.ok is False
    assert any("Checksum mismatch" in error for error in report.errors)


def test_migration_failure_preserves_original_and_backup(tmp_path: Path) -> None:
    registry = MigrationRegistry()
    registry.register(_FailingV05Migration())
    repository = SQLiteSaveRepository(tmp_path / "migration.db", migration_registry=registry)
    original_state = GameState(
        world_id="legacy_world",
        facts={"hidden_oath": FactState(id="hidden_oath", text="secret", visibility=FactVisibility.HIDDEN)},
    )
    repository.create_save("legacy-save", original_state)
    _force_save_schema(repository.database_path, "legacy-save", "0.5")
    before = repository.get_save("legacy-save").state_json

    with pytest.raises(Exception):
        repository.migrate_save("legacy-save")

    after = repository.get_save("legacy-save").state_json
    plan = repository.migration_recovery_plan("legacy-save")

    assert after == before
    assert plan.can_restore_backup is True
    assert plan.backup_save_id is not None
    assert repository.load_save("legacy-save").facts["hidden_oath"].visibility == FactVisibility.HIDDEN


def test_prompt_provider_matrix_and_checklist_no_secrets(tmp_path: Path) -> None:
    profile = PromptProfile(id="safe", name="Safe")
    registry_summary = ProviderCapabilityRegistry().safe_summary_for_frontend()
    matrix = build_compatibility_matrix()
    check = check_compatibility(CompatibilityCheckRequest(contract="GameState", version="1.8"))
    missing = validate_contract_version(None, expected="1.8", path="package")
    checklist = run_checklist(tmp_path)

    serialized = json.dumps(
        {
            "profile": profile.model_dump(mode="json"),
            "registry": registry_summary,
            "matrix": matrix.model_dump(mode="json"),
            "check": check.model_dump(mode="json"),
            "missing": missing.model_dump(mode="json"),
            "checklist": checklist.model_dump(mode="json"),
        },
        sort_keys=True,
    )

    assert check.status == "compatible"
    assert missing.ok is False
    assert checklist.passed is False
    assert "sk-" not in serialized.lower()
    assert "sk-" not in serialized.lower()


def test_contract_docs_generator_deterministic() -> None:
    env = {**os.environ, "PYTHONPATH": "backend"}
    first = subprocess.run(
        [sys.executable, "-m", "app.tools.generate_contract_docs", "--check"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    second = subprocess.run(
        [sys.executable, "-m", "app.tools.generate_contract_docs", "--check"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert first.stdout == second.stdout
    assert "Contract Index" in first.stdout
    assert "sk-" not in first.stdout.lower()


class _FailingV05Migration(SaveMigration):
    source_version = "0.5"
    target_version = CURRENT_SAVE_SCHEMA_VERSION
    description = "Intentional failure for recovery tests."

    def can_migrate(self, save_data: dict) -> bool:
        return True

    def migrate(self, save_data: dict) -> dict:
        raise MigrationError("boom hidden fact text should be redacted")


def _force_save_schema(database_path: str, save_id: str, schema_version: str) -> None:
    connection = sqlite3.connect(database_path)
    try:
        row = connection.execute("SELECT state_json FROM save_games WHERE save_id = ?", (save_id,)).fetchone()
        payload = json.loads(row[0])
        payload["schema_version"] = schema_version
        connection.execute(
            "UPDATE save_games SET state_json = ?, schema_version = ?, engine_version = ? WHERE save_id = ?",
            (json.dumps(payload), schema_version, CURRENT_ENGINE_VERSION, save_id),
        )
        connection.commit()
    finally:
        connection.close()


def _archive_b64(files: dict[str, object]) -> str:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, content in files.items():
            if isinstance(content, dict):
                content = json.dumps(content, sort_keys=True)
            archive.writestr(name, str(content))
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()
