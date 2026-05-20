from pydantic import BaseModel, Field
import json

from app.db.migrations import (
    CURRENT_SAVE_SCHEMA_VERSION,
    MigrationRecoveryPlan,
    MigrationRegistry,
    MigrationReport,
    SaveMigration,
    create_default_registry,
)
from app.db.models import SaveGame
from app.db.repository import SQLiteSaveRepository


class MigrationInfo(BaseModel):
    migration_id: str
    source_version: str
    target_version: str
    description: str


class MigrationStatus(BaseModel):
    save_id: str
    engine_version: str
    schema_version: str
    world_id: str
    world_version: str
    content_pack_version: str
    needs_migration: bool
    target_schema_version: str
    migration_path: list[MigrationInfo] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MigrationService:
    def __init__(
        self,
        repository: SQLiteSaveRepository,
        registry: MigrationRegistry | None = None,
    ) -> None:
        self._repository = repository
        self._registry = registry or create_default_registry()

    def list_available_migrations(self) -> list[MigrationInfo]:
        return [_migration_info(migration) for migration in self._registry.list_available_migrations()]

    def status(
        self,
        save_id: str,
        available_mod_versions: dict[str, str] | None = None,
    ) -> MigrationStatus:
        save = self._repository.get_save(save_id)
        warnings: list[str] = []
        try:
            path = self._registry.find_path(save.schema_version, CURRENT_SAVE_SCHEMA_VERSION)
        except Exception as exc:
            path = []
            if save.schema_version != CURRENT_SAVE_SCHEMA_VERSION:
                warnings.append(str(exc))
        warnings.extend(_mod_version_warnings(save, available_mod_versions or {}))
        return _status_from_save(save, [_migration_info(migration) for migration in path], warnings)

    def dry_run(self, save_id: str) -> MigrationReport:
        return self._repository.migrate_save(save_id, dry_run=True)

    def apply(self, save_id: str) -> MigrationReport:
        return self._repository.migrate_save(save_id, dry_run=False)

    def recovery_plan(self, save_id: str) -> MigrationRecoveryPlan:
        return self._repository.migration_recovery_plan(save_id)

    def restore_pre_migration_backup(self, save_id: str, *, confirm_restore: bool = False) -> MigrationRecoveryPlan:
        self._repository.restore_pre_migration_backup(save_id, confirm_restore=confirm_restore)
        return self.recovery_plan(save_id)


def _migration_info(migration: SaveMigration) -> MigrationInfo:
    return MigrationInfo(
        migration_id=migration.migration_id,
        source_version=migration.source_version,
        target_version=migration.target_version,
        description=migration.description,
    )


def _status_from_save(
    save: SaveGame,
    migration_path: list[MigrationInfo],
    warnings: list[str],
) -> MigrationStatus:
    return MigrationStatus(
        save_id=save.save_id,
        engine_version=save.engine_version,
        schema_version=save.schema_version,
        world_id=save.world_id,
        world_version=save.world_version,
        content_pack_version=save.content_pack_version,
        needs_migration=save.schema_version != CURRENT_SAVE_SCHEMA_VERSION,
        target_schema_version=CURRENT_SAVE_SCHEMA_VERSION,
        migration_path=migration_path,
        warnings=warnings,
    )


def _mod_version_warnings(save: SaveGame, available_mod_versions: dict[str, str]) -> list[str]:
    try:
        saved_mods = json.loads(save.enabled_mods)
    except json.JSONDecodeError:
        return ["Saved enabled_mods metadata is invalid JSON."]
    if not isinstance(saved_mods, list):
        return ["Saved enabled_mods metadata is not a list."]
    warnings: list[str] = []
    for item in saved_mods:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            continue
        mod_id = item["id"]
        saved_version = str(item.get("version", "unknown"))
        current_version = available_mod_versions.get(mod_id)
        if current_version is None:
            warnings.append(f"Enabled mod {mod_id} is not currently available.")
        elif current_version != saved_version:
            warnings.append(
                f"Enabled mod {mod_id} version mismatch: save={saved_version}, current={current_version}."
            )
    return warnings
