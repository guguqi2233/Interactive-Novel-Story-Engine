import base64
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.gameplay_module_packages import (
    GameplayModulePackageImportRequest,
    export_gameplay_module_package,
    import_gameplay_module_package_apply,
    import_gameplay_module_package_dry_run,
)
from app.main import app
from app.session_store import InMemorySessionStore
from app.tools import module_package as module_package_cli


def _write_module(
    root: Path,
    module_id: str = "package_pray",
    *,
    execute_code: bool = False,
    delta_path: str = "flags.package_prayed",
    hidden_leak: bool = False,
) -> Path:
    module_path = root / "gameplay_modules" / module_id
    module_path.joinpath("action_mods").mkdir(parents=True)
    module_path.joinpath("docs").mkdir()
    module_path.joinpath("gameplay_module.yaml").write_text(
        f"""
id: {module_id}
name: Package Pray
version: 0.1.0
module_type: action_pack
engine_version_min: 0.1.0
schema_version: "0.6"
provided_actions:
  - id: {module_id}.pray
    action_type: {module_id}.pray
state_schema_extensions:
  - path_prefix: module_state.{module_id}.enabled
    default_value: false
event_types:
  - id: {module_id}.pray.resolved
    visible_to_player_by_default: true
permissions:
  execute_code: {str(execute_code).lower()}
  access_network: false
  access_filesystem: false
  call_llm: false
  modify_game_state_directly: false
quality_tests: [action_mod_validation, hidden_leak_suite, module_regression]
""",
        encoding="utf-8",
    )
    hidden = (
        """
        visible_facts: [secret_oath]
        hidden_facts: [secret_oath]
        hidden_outcome: true
    visibility_policy:
      hidden_outcome_player_visible: true
"""
        if hidden_leak
        else ""
    )
    module_path.joinpath("action_mods", "actions.yaml").write_text(
        f"""
actions:
  - id: {module_id}.pray
    label: Pray
    aliases: [pray]
    category: general
    outcomes:
      success:
        success_level: success
        reason: Safe package action.
        state_delta_templates:
          - operation: set
            path: {delta_path}
            value: true
{hidden}
    event_type: {module_id}.pray.resolved
""",
        encoding="utf-8",
    )
    module_path.joinpath("docs", "README.md").write_text("# Package Pray\n", encoding="utf-8")
    return module_path


def _client(tmp_path: Path, *, authoring: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "module_package_api.db")
    app.state.gameplay_modules_root = str(tmp_path / "gameplay_modules")
    app.state.settings = Settings(enable_authoring_api=authoring, llm_provider="mock")
    return TestClient(app)


def _zip_entries(archive_base64: str) -> dict[str, bytes]:
    with ZipFile(BytesIO(base64.b64decode(archive_base64.encode("ascii"))), "r") as archive:
        return {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}


def _archive_with_entries(entries: dict[str, bytes]) -> str:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def test_valid_gameplay_module_export_succeeds(tmp_path: Path) -> None:
    _write_module(tmp_path)

    exported = export_gameplay_module_package("package_pray", modules_root=tmp_path / "gameplay_modules")

    assert exported.exported is True
    assert exported.manifest.module_manifest.id == "package_pray"
    entries = _zip_entries(exported.archive_base64)
    assert "gameplay_module_package_manifest.json" in entries
    assert b"api_key" not in b"".join(entries.values()).lower()


def test_gameplay_module_package_includes_checksums(tmp_path: Path) -> None:
    _write_module(tmp_path)

    exported = export_gameplay_module_package("package_pray", modules_root=tmp_path / "gameplay_modules")
    manifest = json.loads(_zip_entries(exported.archive_base64)["gameplay_module_package_manifest.json"])

    assert manifest["checksums"]["gameplay_modules/package_pray/gameplay_module.yaml"]
    assert manifest["checksums"]["gameplay_modules/package_pray/action_mods/actions.yaml"]


def test_import_dry_run_does_not_write_disk(tmp_path: Path) -> None:
    _write_module(tmp_path)
    exported = export_gameplay_module_package("package_pray", modules_root=tmp_path / "gameplay_modules")
    target_root = tmp_path / "target_modules"

    report = import_gameplay_module_package_dry_run(
        GameplayModulePackageImportRequest(archive_base64=exported.archive_base64)
    )

    assert report.ok is True
    assert report.imported is False
    assert report.writes_to_disk is False
    assert not target_root.exists()


def test_import_rejects_executable_file(tmp_path: Path) -> None:
    _write_module(tmp_path)
    exported = export_gameplay_module_package("package_pray", modules_root=tmp_path / "gameplay_modules")
    entries = _zip_entries(exported.archive_base64)
    entries["gameplay_modules/package_pray/evil.py"] = b"print('no')"
    archive = _archive_with_entries(entries)

    report = import_gameplay_module_package_dry_run(GameplayModulePackageImportRequest(archive_base64=archive))

    assert report.ok is False
    assert "executable code" in report.errors[0]


def test_import_rejects_zip_slip(tmp_path: Path) -> None:
    archive = _archive_with_entries({"../evil.txt": b"no"})

    report = import_gameplay_module_package_dry_run(GameplayModulePackageImportRequest(archive_base64=archive))

    assert report.ok is False
    assert "zip slip" in report.errors[0]


def test_import_rejects_execute_code_permission(tmp_path: Path) -> None:
    _write_module(tmp_path, execute_code=True)
    # Build an archive directly so export validation does not mask the import dry-run check.
    module_path = tmp_path / "gameplay_modules" / "package_pray"
    files = {
        "gameplay_modules/package_pray/gameplay_module.yaml": module_path.joinpath("gameplay_module.yaml").read_bytes(),
        "gameplay_modules/package_pray/action_mods/actions.yaml": module_path.joinpath("action_mods", "actions.yaml").read_bytes(),
    }
    from app.engine.gameplay_module_packages import GameplayModulePackageManifest
    from app.engine.gameplay_module_loader import GameplayModuleLoader
    import hashlib

    manifest = GameplayModulePackageManifest(
        package_id="package_pray",
        module_manifest=GameplayModuleLoader(tmp_path / "gameplay_modules").load_manifest_only("package_pray"),
        checksums={name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
    )
    files["gameplay_module_package_manifest.json"] = manifest.model_dump_json().encode("utf-8")
    archive = _archive_with_entries(files)

    report = import_gameplay_module_package_dry_run(GameplayModulePackageImportRequest(archive_base64=archive))

    assert report.ok is False
    assert any("execute_code" in error for error in report.errors)


def test_quality_gate_fail_blocks_apply(tmp_path: Path) -> None:
    _write_module(tmp_path, delta_path="player.hp")
    module_path = tmp_path / "gameplay_modules" / "package_pray"
    files = {
        "gameplay_modules/package_pray/gameplay_module.yaml": module_path.joinpath("gameplay_module.yaml").read_bytes(),
        "gameplay_modules/package_pray/action_mods/actions.yaml": module_path.joinpath("action_mods", "actions.yaml").read_bytes(),
    }
    from app.engine.gameplay_module_packages import GameplayModulePackageManifest
    from app.engine.gameplay_module_loader import GameplayModuleLoader
    import hashlib

    manifest = GameplayModulePackageManifest(
        package_id="package_pray",
        module_manifest=GameplayModuleLoader(tmp_path / "gameplay_modules").load_manifest_only("package_pray"),
        checksums={name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
    )
    files["gameplay_module_package_manifest.json"] = manifest.model_dump_json().encode("utf-8")
    archive = _archive_with_entries(files)
    target_root = tmp_path / "imported_modules"

    report = import_gameplay_module_package_apply(
        GameplayModulePackageImportRequest(archive_base64=archive, confirm_apply=True),
        modules_root=target_root,
    )

    assert report.ok is False
    assert report.imported is False
    assert not (target_root / "package_pray").exists()


def test_gameplay_module_package_api_and_cli(tmp_path: Path) -> None:
    _write_module(tmp_path)
    client = _client(tmp_path)

    export_response = client.post("/modules/export", params={"module_id": "package_pray"})
    assert export_response.status_code == 200
    archive = export_response.json()["archive_base64"]
    dry_run_response = client.post("/modules/import-dry-run", json={"archive_base64": archive})
    assert dry_run_response.status_code == 200
    assert dry_run_response.json()["ok"] is True
    archive_file = tmp_path / "module.b64"
    archive_file.write_text(archive, encoding="utf-8")

    exit_code = module_package_cli.main(
        ["--modules-root", str(tmp_path / "gameplay_modules"), "--json", "import-dry-run", "--archive", str(archive_file)]
    )

    assert exit_code == 0
