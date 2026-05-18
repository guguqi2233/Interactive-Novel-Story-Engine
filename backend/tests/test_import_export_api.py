import base64
import json
from io import BytesIO
from pathlib import Path
from shutil import copytree
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def make_client(tmp_path: Path, *, authoring_enabled: bool = True) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    mods_root = tmp_path / "mods"
    _write_mod(mods_root)
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "import_export.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = mods_root
    app.state.settings = Settings(
        enable_authoring_api=authoring_enabled,
        llm_provider="mock",
        llm_api_key="test-api-key-placeholder",
    )
    return TestClient(app)


def test_export_and_import_world_pack(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    export_response = client.get("/authoring/export/worlds/mist_valley")
    assert export_response.status_code == 200
    exported = export_response.json()
    assert exported["export_type"] == "world"
    assert exported["file_name"].endswith(".world.zip")
    assert "test-api-key-placeholder" not in export_response.text

    app.state.worlds_root = tmp_path / "imported_worlds"
    import_response = client.post(
        "/authoring/import/worlds",
        json={"archive_base64": exported["archive_base64"]},
    )

    assert import_response.status_code == 200
    payload = import_response.json()
    assert payload["imported"] is True
    assert payload["validation_ok"] is True
    assert (tmp_path / "imported_worlds" / "mist_valley" / "manifest.yaml").exists()


def test_export_world_package_has_manifest_and_checksum(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    export_response = client.get("/authoring/export/worlds/mist_valley")

    assert export_response.status_code == 200
    archive = _zip_entries(export_response.json()["archive_base64"])
    package_manifest = json.loads(archive["local_package_manifest.json"])
    assert package_manifest["package_type"] == "world"
    assert "worlds/mist_valley/manifest.yaml" in package_manifest["included_files"]
    assert package_manifest["checksums"]["worlds/mist_valley/manifest.yaml"]


def test_import_package_dry_run_valid_world_succeeds(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    export_response = client.get("/authoring/export/worlds/mist_valley")
    app.state.worlds_root = tmp_path / "imported_worlds"

    dry_run_response = client.post(
        "/authoring/import/packages/dry-run",
        json={"archive_base64": export_response.json()["archive_base64"]},
    )

    assert dry_run_response.status_code == 200
    assert dry_run_response.json()["ok"] is True
    assert dry_run_response.json()["manifest"]["package_type"] == "world"
    assert not (tmp_path / "imported_worlds" / "mist_valley").exists()


def test_import_package_apply_requires_confirmation(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    export_response = client.get("/authoring/export/worlds/mist_valley")
    app.state.worlds_root = tmp_path / "imported_worlds"

    rejected = client.post(
        "/authoring/import/packages/apply",
        json={"archive_base64": export_response.json()["archive_base64"]},
    )
    accepted = client.post(
        "/authoring/import/packages/apply",
        json={"archive_base64": export_response.json()["archive_base64"], "confirm_apply": True},
    )

    assert rejected.status_code == 400
    assert "explicit confirmation" in rejected.json()["detail"]
    assert accepted.status_code == 200
    assert accepted.json()["imported"] is True
    assert (tmp_path / "imported_worlds" / "mist_valley" / "manifest.yaml").exists()


def test_import_package_rejects_checksum_mismatch(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    export_response = client.get("/authoring/export/worlds/mist_valley")
    tampered = _tamper_archive_file(
        export_response.json()["archive_base64"],
        "worlds/mist_valley/manifest.yaml",
        "world_id: mist_valley\nname: Tampered\n",
    )

    response = client.post("/authoring/import/packages/dry-run", json={"archive_base64": tampered})

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "Checksum mismatch" in response.json()["errors"][0]


def test_export_and_import_mod_package(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    export_response = client.get("/authoring/export/mods/mist_mod")
    assert export_response.status_code == 200
    exported = export_response.json()

    app.state.mods_root = tmp_path / "imported_mods"
    import_response = client.post(
        "/authoring/import/mods",
        json={"archive_base64": exported["archive_base64"]},
    )

    assert import_response.status_code == 200
    payload = import_response.json()
    assert payload["imported"] is True
    assert payload["validation_ok"] is True
    assert (tmp_path / "imported_mods" / "mist_mod" / "mod.yaml").exists()


def test_import_world_rejects_path_traversal(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "bad_world"},
            "../evil.txt": "nope",
        }
    )

    response = client.post("/authoring/import/worlds", json={"archive_base64": archive})

    assert response.status_code == 400
    assert "Unsafe archive path" in response.json()["detail"]


def test_import_package_dry_run_rejects_zip_slip(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "bad_world"},
            "local_package_manifest.json": {
                "package_id": "bad_world",
                "package_type": "world",
                "version": "0.8.16",
                "engine_version_min": "0.8.0",
                "schema_version": "0.8",
                "included_files": ["../evil.txt"],
                "checksums": {"../evil.txt": "x"},
                "dependencies": [],
                "conflicts": [],
                "created_at": "2026-05-18T00:00:00Z",
                "notes": "",
            },
            "../evil.txt": "nope",
        }
    )

    response = client.post("/authoring/import/packages/dry-run", json={"archive_base64": archive})

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "Unsafe archive path" in response.json()["errors"][0]


def test_import_archive_containing_executable_is_rejected(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "bad_world"},
            "worlds/bad_world/manifest.yaml": "world_id: bad_world\nname: Bad\n",
            "worlds/bad_world/evil.py": "print('no')\n",
        }
    )

    response = client.post("/authoring/import/worlds", json={"archive_base64": archive})

    assert response.status_code == 400
    assert "executable code" in response.json()["detail"]


def test_import_package_dry_run_rejects_executable(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "bad_world"},
            "local_package_manifest.json": {
                "package_id": "bad_world",
                "package_type": "world",
                "version": "0.8.16",
                "engine_version_min": "0.8.0",
                "schema_version": "0.8",
                "included_files": ["worlds/bad_world/evil.py"],
                "checksums": {"worlds/bad_world/evil.py": "x"},
                "dependencies": [],
                "conflicts": [],
                "created_at": "2026-05-18T00:00:00Z",
                "notes": "",
            },
            "worlds/bad_world/evil.py": "print('no')\n",
        }
    )

    response = client.post("/authoring/import/packages/dry-run", json={"archive_base64": archive})

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "executable code" in response.json()["errors"][0]


def test_import_package_dry_run_rejects_platform_executable_suffixes(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "bad_world"},
            "local_package_manifest.json": {
                "package_id": "bad_world",
                "package_type": "world",
                "version": "1.0.0",
                "engine_version_min": "1.0.0",
                "schema_version": "1.0",
                "included_files": ["worlds/bad_world/helpers.psm1"],
                "checksums": {"worlds/bad_world/helpers.psm1": "x"},
                "dependencies": [],
                "conflicts": [],
                "created_at": "2026-05-19T00:00:00Z",
                "notes": "",
            },
            "worlds/bad_world/helpers.psm1": "Write-Host nope\n",
        }
    )

    response = client.post("/authoring/import/packages/dry-run", json={"archive_base64": archive})

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "executable code" in response.json()["errors"][0]


def test_import_package_reports_conflict(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    export_response = client.get("/authoring/export/worlds/mist_valley")

    response = client.post(
        "/authoring/import/packages/dry-run",
        json={"archive_base64": export_response.json()["archive_base64"]},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert "World already exists" in response.json()["conflicts"][0]


def test_import_invalid_manifest_is_rejected(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    archive = _raw_archive_b64({"export_manifest.json": "{not-json"})

    response = client.post("/authoring/import/worlds", json={"archive_base64": archive})

    assert response.status_code == 400
    assert "Invalid export manifest" in response.json()["detail"]


def test_import_archive_does_not_accept_env_or_api_key_files(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "leaky_world"},
            "worlds/leaky_world/manifest.yaml": "world_id: leaky_world\nname: Leaky\n",
            "worlds/leaky_world/.env": "OPENAI_API_KEY=test-secret-placeholder\n",
        }
    )

    response = client.post("/authoring/import/worlds", json={"archive_base64": archive})

    assert response.status_code == 400
    assert "sensitive file" in response.json()["detail"]
    assert "test-secret-placeholder" not in response.text


def test_save_bundle_import_reports_migration_status(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    start_response = client.post("/game/start", json={"world_id": "mist_valley"})
    session_id = start_response.json()["session_id"]
    save_response = client.post(f"/game/{session_id}/save")
    save_id = save_response.json()["save_id"]

    export_response = client.get(f"/authoring/export/saves/{save_id}")
    assert export_response.status_code == 200
    exported = export_response.json()

    app.state.save_repository = SQLiteSaveRepository(tmp_path / "imported_saves.db")
    import_response = client.post(
        "/authoring/import/saves",
        json={"archive_base64": exported["archive_base64"]},
    )
    status_response = client.get(f"/saves/{save_id}/migration-status")

    assert import_response.status_code == 200
    assert import_response.json()["imported"] is True
    assert import_response.json()["migration_needed"] is False
    assert status_response.status_code == 200
    assert status_response.json()["needs_migration"] is False
    assert "test-api-key-placeholder" not in import_response.text
    assert "state_deltas" not in import_response.text


def test_save_package_dry_run_reports_migration_status_and_no_secret(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    start_response = client.post("/game/start", json={"world_id": "mist_valley"})
    session_id = start_response.json()["session_id"]
    save_response = client.post(f"/game/{session_id}/save")
    save_id = save_response.json()["save_id"]
    export_response = client.get(f"/authoring/export/saves/{save_id}")
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "imported_saves.db")

    response = client.post(
        "/authoring/import/packages/dry-run",
        json={"archive_base64": export_response.json()["archive_base64"]},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["package_type"] == "save_bundle"
    assert response.json()["migration_needed"] is False
    assert "test-api-key-placeholder" not in response.text


def test_authoring_import_export_api_obeys_toggle(tmp_path: Path) -> None:
    client = make_client(tmp_path, authoring_enabled=False)

    response = client.get("/authoring/export/worlds/mist_valley")

    assert response.status_code == 403
    assert response.json()["detail"] == "Authoring API is disabled"


def _write_mod(mods_root: Path) -> None:
    mod_path = mods_root / "mist_mod"
    content_root = mod_path / "content"
    content_root.mkdir(parents=True)
    copytree(Path("worlds") / "mist_valley", content_root / "mist_valley")
    mod_path.joinpath("mod.yaml").write_text(
        """
id: mist_mod
name: Mist Mod
version: 0.1.0
engine_version_min: 0.5.0
content_schema_version: "0.6"
dependencies: []
optional_dependencies: []
conflicts: []
load_order_hint: 0
compatible_worlds:
  - mist_valley
migration_notes: ""
entry_worlds:
  - mist_valley
content_paths:
  - content
author: Local Tester
description: Local content-only mod.
""",
        encoding="utf-8",
    )


def _archive_b64(files: dict[str, str | dict[str, object]]) -> str:
    serialized: dict[str, str] = {}
    for name, value in files.items():
        serialized[name] = json.dumps(value) if isinstance(value, dict) else value
    return _raw_archive_b64(serialized)


def _raw_archive_b64(files: dict[str, str]) -> str:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _zip_entries(archive_base64: str) -> dict[str, str]:
    archive_bytes = base64.b64decode(archive_base64.encode("ascii"))
    with ZipFile(BytesIO(archive_bytes), "r") as archive:
        return {name: archive.read(name).decode("utf-8") for name in archive.namelist()}


def _tamper_archive_file(archive_base64: str, file_name: str, content: str) -> str:
    entries = _zip_entries(archive_base64)
    entries[file_name] = content
    return _raw_archive_b64(entries)
