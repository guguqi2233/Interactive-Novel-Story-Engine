from pathlib import Path

import pytest

from app.engine.gameplay_module_loader import (
    GameplayModuleLoader,
    GameplayModuleLoaderError,
)


def write_gameplay_module(
    tmp_path: Path,
    module_id: str = "magic_basics",
    *,
    dependencies: list[str] | None = None,
    conflicts: list[str] | None = None,
    execute_code: bool = False,
    state_path: str = "flags.magic_enabled",
    safe_to_add_mid_save: bool = True,
    migration_required: bool = False,
    requires_new_game: bool = False,
    migration_defaults: str = "{}",
) -> Path:
    module_path = tmp_path / "gameplay_modules" / module_id
    module_path.mkdir(parents=True)
    module_path.joinpath("gameplay_module.yaml").write_text(
        f"""
id: {module_id}
name: Magic Basics
version: 0.1.0
module_type: action_pack
engine_version_min: 0.1.0
schema_version: "0.6"
dependencies: {dependencies or []}
conflicts: {conflicts or []}
required_systems:
  - action_registry
provided_actions:
  - id: {module_id}.cast_spark
    action_type: cast_spark
provided_rules:
  - id: {module_id}.spell_check
    rule_type: deterministic_check
state_schema_extensions:
  - path_prefix: {state_path}
    default_value: false
    migration_required: {str(migration_required).lower()}
    player_visible: false
event_types:
  - id: {module_id}.spell_cast
    visible_to_player_by_default: true
    debug_only: false
permissions:
  execute_code: {str(execute_code).lower()}
  access_network: false
  access_filesystem: false
  call_llm: false
  modify_game_state_directly: false
save_compatibility:
  safe_to_add_mid_save: {str(safe_to_add_mid_save).lower()}
  migration_required: {str(migration_required).lower()}
  requires_new_game: {str(requires_new_game).lower()}
  migration_defaults: {migration_defaults}
quality_tests:
  - hidden_leak
""",
        encoding="utf-8",
    )
    return module_path


def test_valid_gameplay_module_manifest_loads(tmp_path: Path) -> None:
    write_gameplay_module(tmp_path)

    loader = GameplayModuleLoader(tmp_path / "gameplay_modules")
    modules = loader.discover_modules()
    manifest = loader.load_manifest_only("magic_basics")

    assert [module.manifest.id for module in modules] == ["magic_basics"]
    assert manifest.name == "Magic Basics"
    assert manifest.permissions.execute_code is False
    assert manifest.save_compatibility.safe_to_add_mid_save is True


def test_execute_code_true_is_rejected_by_validation(tmp_path: Path) -> None:
    write_gameplay_module(tmp_path, execute_code=True)

    report = GameplayModuleLoader(tmp_path / "gameplay_modules").validate_module("magic_basics")

    assert not report.ok
    assert any(issue.code == "gameplay_module_forbidden_permission" for issue in report.errors)


def test_missing_dependency_is_reported(tmp_path: Path) -> None:
    write_gameplay_module(tmp_path, dependencies=["missing_module"])

    report = GameplayModuleLoader(tmp_path / "gameplay_modules").resolve_dependencies()

    assert not report.ok
    assert report.missing_dependencies == {"magic_basics": ["missing_module"]}


def test_conflict_is_reported(tmp_path: Path) -> None:
    write_gameplay_module(tmp_path, "magic_basics", conflicts=["blood_magic"])
    write_gameplay_module(tmp_path, "blood_magic")

    report = GameplayModuleLoader(tmp_path / "gameplay_modules").detect_conflicts(["magic_basics", "blood_magic"])

    assert not report.ok
    assert report.conflicts == [("blood_magic", "magic_basics")]


def test_state_schema_extension_is_validated(tmp_path: Path) -> None:
    write_gameplay_module(tmp_path, state_path="player.hp")

    report = GameplayModuleLoader(tmp_path / "gameplay_modules").validate_module("magic_basics")

    assert not report.ok
    assert any(issue.code == "gameplay_module_unsafe_state_extension" for issue in report.errors)


def test_save_compatibility_is_validated(tmp_path: Path) -> None:
    write_gameplay_module(
        tmp_path,
        safe_to_add_mid_save=True,
        requires_new_game=True,
        migration_required=True,
        migration_defaults="{}",
    )

    report = GameplayModuleLoader(tmp_path / "gameplay_modules").validate_module("magic_basics")

    assert not report.ok
    codes = {issue.code for issue in report.errors}
    assert "gameplay_module_invalid_save_compatibility" in codes
    assert "gameplay_module_missing_migration_defaults" in codes


def test_path_traversal_module_id_is_rejected(tmp_path: Path) -> None:
    write_gameplay_module(tmp_path)

    loader = GameplayModuleLoader(tmp_path / "gameplay_modules")
    with pytest.raises(GameplayModuleLoaderError, match="Invalid gameplay module id"):
        loader.load_manifest_only("../magic_basics")


def test_manifest_loader_rejects_executable_files(tmp_path: Path) -> None:
    module_path = write_gameplay_module(tmp_path)
    module_path.joinpath("evil.py").write_text("print('no')\n", encoding="utf-8")

    report = GameplayModuleLoader(tmp_path / "gameplay_modules").validate_module("magic_basics")

    assert not report.ok
    assert any(issue.code == "gameplay_module_executable_code_forbidden" for issue in report.errors)
