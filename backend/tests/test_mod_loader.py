from pathlib import Path
from shutil import copytree

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.mod_loader import ModLoader, ModLoaderError, compare_versions, parse_version
from app.main import app
from app.session_store import InMemorySessionStore


def write_mod(
    tmp_path: Path,
    mod_id: str = "mist_mod",
    *,
    dependencies: list[str] | None = None,
    conflicts: list[str] | None = None,
    content_paths: list[str] | None = None,
    copy_world: bool = True,
    engine_version_min: str = "0.5.0",
    content_schema_version: str = "0.6",
    load_order_hint: int = 0,
) -> Path:
    mod_path = tmp_path / "mods" / mod_id
    mod_path.mkdir(parents=True)
    if copy_world:
        content_root = mod_path / "content"
        content_root.mkdir()
        copytree(Path("worlds") / "mist_valley", content_root / "mist_valley")
    paths = content_paths if content_paths is not None else ["content"]
    mod_path.joinpath("mod.yaml").write_text(
        f"""
id: {mod_id}
name: Mist Mod
version: 0.1.0
engine_version_min: {engine_version_min}
content_schema_version: "{content_schema_version}"
dependencies: {dependencies or []}
optional_dependencies: []
conflicts: {conflicts or []}
load_order_hint: {load_order_hint}
compatible_worlds:
  - mist_valley
migration_notes: ""
entry_worlds:
  - mist_valley
content_paths:
{chr(10).join(f"  - {path}" for path in paths)}
author: Local Tester
description: Local content-only mod.
""",
        encoding="utf-8",
    )
    return mod_path


def make_client(tmp_path: Path, authoring_enabled: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "mod_api.db")
    app.state.mods_root = tmp_path / "mods"
    app.state.settings = Settings(enable_authoring_api=authoring_enabled)
    return TestClient(app)


def test_discover_mods_finds_valid_mod(tmp_path: Path) -> None:
    write_mod(tmp_path)

    mods = ModLoader(tmp_path / "mods").discover_mods()

    assert [mod.manifest.id for mod in mods] == ["mist_mod"]
    assert mods[0].manifest.entry_worlds == ["mist_valley"]


def test_invalid_manifest_raises_clear_error(tmp_path: Path) -> None:
    mod_path = tmp_path / "mods" / "bad_mod"
    mod_path.mkdir(parents=True)
    mod_path.joinpath("mod.yaml").write_text("id: bad_mod\nname: Bad\n", encoding="utf-8")

    with pytest.raises(ModLoaderError, match="Invalid mod manifest"):
        ModLoader(tmp_path / "mods").discover_mods()


def test_dependency_missing_is_reported(tmp_path: Path) -> None:
    write_mod(tmp_path, dependencies=["missing_mod"])

    report = ModLoader(tmp_path / "mods").resolve_dependencies()

    assert not report.ok
    assert report.missing_dependencies == {"mist_mod": ["missing_mod"]}


def test_conflict_detection_reports_enabled_pair(tmp_path: Path) -> None:
    write_mod(tmp_path, "first_mod", conflicts=["second_mod"])
    write_mod(tmp_path, "second_mod")

    report = ModLoader(tmp_path / "mods").detect_conflicts(["first_mod", "second_mod"])

    assert not report.ok
    assert report.conflicts == [("first_mod", "second_mod")]


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    write_mod(tmp_path, content_paths=["../outside"], copy_world=False)

    report = ModLoader(tmp_path / "mods").validate_mod("mist_mod")

    assert not report.ok
    assert any(issue.code == "unsafe_content_path" for issue in report.errors)


def test_mod_cannot_contain_executable_code(tmp_path: Path) -> None:
    mod_path = write_mod(tmp_path)
    mod_path.joinpath("evil.py").write_text("print('nope')\n", encoding="utf-8")

    report = ModLoader(tmp_path / "mods").validate_mod("mist_mod")

    assert not report.ok
    assert any(issue.code == "mod_executable_code_forbidden" for issue in report.errors)


def test_mod_cannot_contain_platform_executable_content(tmp_path: Path) -> None:
    mod_path = write_mod(tmp_path)
    mod_path.joinpath("helpers.psm1").write_text("Write-Host nope\n", encoding="utf-8")
    mod_path.joinpath("payload.jar").write_text("not really a jar\n", encoding="utf-8")

    report = ModLoader(tmp_path / "mods").validate_mod("mist_mod")

    assert not report.ok
    forbidden_paths = {issue.path for issue in report.errors if issue.code == "mod_executable_code_forbidden"}
    assert "helpers.psm1" in forbidden_paths
    assert "payload.jar" in forbidden_paths


def test_validate_mod_reuses_world_validation(tmp_path: Path) -> None:
    mod_path = write_mod(tmp_path)
    locations_path = mod_path / "content" / "mist_valley" / "locations.yaml"
    locations_path.write_text(
        locations_path.read_text(encoding="utf-8").replace("east: blacksmith", "east: nowhere"),
        encoding="utf-8",
    )

    report = ModLoader(tmp_path / "mods").validate_mod("mist_mod")

    assert not report.ok
    assert report.world_reports
    assert any(issue.code for issue in report.errors)


def test_list_enabled_mods_filters_requested_ids(tmp_path: Path) -> None:
    write_mod(tmp_path, "first_mod")
    write_mod(tmp_path, "second_mod")

    mods = ModLoader(tmp_path / "mods").list_enabled_mods(["second_mod"])

    assert [mod.manifest.id for mod in mods] == ["second_mod"]


def test_authoring_mod_api_lists_and_validates(tmp_path: Path) -> None:
    write_mod(tmp_path)
    client = make_client(tmp_path)

    list_response = client.get("/authoring/mods")
    detail_response = client.get("/authoring/mods/mist_mod")
    validate_response = client.post("/authoring/mods/mist_mod/validate")
    load_order_response = client.get("/authoring/mods/load-order")

    assert list_response.status_code == 200
    assert list_response.json()["mods"][0]["id"] == "mist_mod"
    assert detail_response.status_code == 200
    assert detail_response.json()["mod"]["id"] == "mist_mod"
    assert detail_response.json()["validation"]["ok"] is True
    assert validate_response.status_code == 200
    assert validate_response.json()["ok"] is True
    assert validate_response.json()["world_report_ids"]
    assert load_order_response.status_code == 200
    assert load_order_response.json()["load_order"] == ["mist_mod"]


def test_authoring_mod_api_obeys_authoring_toggle(tmp_path: Path) -> None:
    write_mod(tmp_path)
    client = make_client(tmp_path, authoring_enabled=False)

    response = client.get("/authoring/mods")
    detail_response = client.get("/authoring/mods/mist_mod")
    load_order_response = client.get("/authoring/mods/load-order")

    assert response.status_code == 403
    assert detail_response.status_code == 403
    assert load_order_response.status_code == 403


def test_version_parser_and_comparator() -> None:
    assert parse_version("1.2.3") == (1, 2, 3)
    assert compare_versions("1.2.0", "1.2") == 0
    assert compare_versions("1.3.0", "1.2.9") == 1
    assert compare_versions("1.0.0", "1.0.1") == -1


def test_valid_mod_version_passes(tmp_path: Path) -> None:
    write_mod(tmp_path)

    report = ModLoader(tmp_path / "mods").validate_mod_version("mist_mod")

    assert report.ok
    assert report.errors == {}


def test_engine_version_min_not_satisfied_is_error(tmp_path: Path) -> None:
    write_mod(tmp_path, engine_version_min="9.0.0")

    report = ModLoader(tmp_path / "mods").validate_mod("mist_mod")

    assert not report.ok
    assert any(issue.code == "mod_version_incompatible" for issue in report.errors)


def test_content_schema_mismatch_is_reported_as_warning(tmp_path: Path) -> None:
    write_mod(tmp_path, content_schema_version="9.9")

    report = ModLoader(tmp_path / "mods").validate_mod("mist_mod")

    assert any(issue.code == "mod_version_warning" for issue in report.warnings)
    assert any("Content schema 9.9 differs" in issue.message for issue in report.warnings)


def test_load_order_is_deterministic_and_dependency_aware(tmp_path: Path) -> None:
    write_mod(tmp_path, "base_mod", load_order_hint=10)
    write_mod(tmp_path, "addon_mod", dependencies=["base_mod"], load_order_hint=0)

    report = ModLoader(tmp_path / "mods").resolve_load_order(["addon_mod", "base_mod"])

    assert report.ok
    assert report.load_order == ["base_mod", "addon_mod"]


def test_mod_cannot_declare_executable_entry(tmp_path: Path) -> None:
    mod_path = write_mod(tmp_path)
    manifest = mod_path / "mod.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + "\npython_entrypoint: evil.py\n",
        encoding="utf-8",
    )

    with pytest.raises(ModLoaderError, match="Invalid mod manifest"):
        ModLoader(tmp_path / "mods").discover_mods()
