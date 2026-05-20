from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.core.world_state import CURRENT_GAME_STATE_SCHEMA_VERSION, load_game_state_payload

CURRENT_ENGINE_VERSION = "0.6.0"
CURRENT_SAVE_SCHEMA_VERSION = CURRENT_GAME_STATE_SCHEMA_VERSION
LEGACY_SCHEMA_VERSION = "legacy"


class MigrationError(RuntimeError):
    """Raised when a save migration cannot be completed safely."""


class MigrationHistoryEntry(BaseModel):
    migration_id: str
    source_version: str
    target_version: str
    description: str
    applied_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class MigrationReport(BaseModel):
    save_id: str
    source_version: str
    target_version: str
    applied_migrations: list[MigrationHistoryEntry] = Field(default_factory=list)
    dry_run: bool = False
    backup_save_id: str | None = None
    pre_migration_checksum: str | None = None
    success: bool = True
    warnings: list[str] = Field(default_factory=list)


class MigrationFailureReport(BaseModel):
    save_id: str
    source_version: str = "unknown"
    target_version: str = CURRENT_SAVE_SCHEMA_VERSION
    pre_migration_checksum: str | None = None
    backup_save_id: str | None = None
    success: bool = False
    error: str
    hidden_details_redacted: bool = True


class MigrationRecoveryPlan(BaseModel):
    save_id: str
    can_restore_backup: bool
    backup_save_id: str | None = None
    recommended_steps: list[str] = Field(default_factory=list)
    failure_report: MigrationFailureReport | None = None


class SaveMigration(ABC):
    source_version: str
    target_version: str
    description: str

    @property
    def migration_id(self) -> str:
        return f"{self.source_version}->{self.target_version}"

    @abstractmethod
    def can_migrate(self, save_data: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def migrate(self, save_data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def validate_before(self, save_data: dict[str, Any]) -> None:
        _require_state_json(save_data)

    def validate_after(self, save_data: dict[str, Any]) -> None:
        state_payload = _state_payload(save_data)
        state = load_game_state_payload(state_payload)
        if state.schema_version != self.target_version:
            raise MigrationError(
                f"Migration {self.migration_id} produced schema_version "
                f"{state.schema_version}, expected {self.target_version}"
            )


class DefaultFillToV06Migration(SaveMigration):
    target_version = CURRENT_SAVE_SCHEMA_VERSION
    description = "Fill v0.6 save metadata and GameState schema defaults."

    def can_migrate(self, save_data: dict[str, Any]) -> bool:
        return detect_schema_version(save_data) == self.source_version

    def migrate(self, save_data: dict[str, Any]) -> dict[str, Any]:
        self.validate_before(save_data)
        migrated = deepcopy(save_data)
        state_payload = _state_payload(migrated)
        state_payload["schema_version"] = self.target_version
        migrated["state_json"] = _dump_state_payload(state_payload)
        migrated["engine_version"] = migrated.get("engine_version") or CURRENT_ENGINE_VERSION
        migrated["schema_version"] = self.target_version
        migrated["world_id"] = migrated.get("world_id") or state_payload.get("world_id", "unknown")
        migrated["world_version"] = migrated.get("world_version") or "unknown"
        migrated["content_pack_version"] = migrated.get("content_pack_version") or migrated["world_version"]
        migrated["migration_history"] = _append_history(
            migrated.get("migration_history"),
            MigrationHistoryEntry(
                migration_id=self.migration_id,
                source_version=self.source_version,
                target_version=self.target_version,
                description=self.description,
            ),
        )
        self.validate_after(migrated)
        return migrated


class LegacyToV06Migration(DefaultFillToV06Migration):
    source_version = LEGACY_SCHEMA_VERSION


class V03ToV06Migration(DefaultFillToV06Migration):
    source_version = "0.3"


class V04ToV06Migration(DefaultFillToV06Migration):
    source_version = "0.4"


class V05ToV06Migration(DefaultFillToV06Migration):
    source_version = "0.5"


class MigrationRegistry:
    def __init__(self) -> None:
        self._migrations: list[SaveMigration] = []

    def register(self, migration: SaveMigration) -> None:
        if any(
            item.source_version == migration.source_version
            and item.target_version == migration.target_version
            for item in self._migrations
        ):
            raise MigrationError(f"Migration already registered: {migration.migration_id}")
        self._migrations.append(migration)

    def list_available_migrations(self) -> list[SaveMigration]:
        return list(self._migrations)

    def find_path(self, source_version: str, target_version: str) -> list[SaveMigration]:
        if source_version == target_version:
            return []
        visited: set[str] = set()
        queue: list[tuple[str, list[SaveMigration]]] = [(source_version, [])]
        while queue:
            version, path = queue.pop(0)
            if version in visited:
                continue
            visited.add(version)
            for migration in self._migrations:
                if migration.source_version != version:
                    continue
                next_path = [*path, migration]
                if migration.target_version == target_version:
                    return next_path
                queue.append((migration.target_version, next_path))
        raise MigrationError(
            f"No migration path from {source_version} to {target_version}"
        )

    def migrate_to_latest(
        self,
        save_id: str,
        save_data: dict[str, Any],
        *,
        target_version: str = CURRENT_SAVE_SCHEMA_VERSION,
        dry_run: bool = False,
        backup_save_id: str | None = None,
    ) -> tuple[dict[str, Any], MigrationReport]:
        source_version = detect_schema_version(save_data)
        migrated = deepcopy(save_data)
        report = MigrationReport(
            save_id=save_id,
            source_version=source_version,
            target_version=target_version,
            dry_run=dry_run,
            backup_save_id=backup_save_id,
        )
        for migration in self.find_path(source_version, target_version):
            if not migration.can_migrate(migrated):
                raise MigrationError(
                    f"Migration {migration.migration_id} cannot migrate this save"
                )
            migration.validate_before(migrated)
            migrated = migration.migrate(migrated)
            migration.validate_after(migrated)
            report.applied_migrations.append(
                MigrationHistoryEntry(
                    migration_id=migration.migration_id,
                    source_version=migration.source_version,
                    target_version=migration.target_version,
                    description=migration.description,
                )
            )
        if not report.applied_migrations and source_version == target_version:
            report.warnings.append("Save already at target schema version.")
        return migrated, report


def create_default_registry() -> MigrationRegistry:
    registry = MigrationRegistry()
    registry.register(LegacyToV06Migration())
    registry.register(V03ToV06Migration())
    registry.register(V04ToV06Migration())
    registry.register(V05ToV06Migration())
    return registry


def detect_schema_version(save_data: dict[str, Any]) -> str:
    version = save_data.get("schema_version")
    if isinstance(version, str) and version:
        return version
    state_payload = _state_payload(save_data)
    state_version = state_payload.get("schema_version")
    if isinstance(state_version, str) and state_version:
        return state_version
    return LEGACY_SCHEMA_VERSION


def _require_state_json(save_data: dict[str, Any]) -> None:
    if "state_json" not in save_data:
        raise MigrationError("Save data is missing state_json")
    _state_payload(save_data)


def _state_payload(save_data: dict[str, Any]) -> dict[str, Any]:
    import json

    raw_state = save_data.get("state_json")
    if isinstance(raw_state, str):
        try:
            payload = json.loads(raw_state)
        except json.JSONDecodeError as exc:
            raise MigrationError("Save state_json is not valid JSON") from exc
    elif isinstance(raw_state, dict):
        payload = dict(raw_state)
    else:
        raise MigrationError("Save state_json must be a JSON object string")
    if not isinstance(payload, dict):
        raise MigrationError("Save state_json must decode to an object")
    return payload


def _dump_state_payload(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _append_history(raw_history: Any, entry: MigrationHistoryEntry) -> str:
    import json

    if isinstance(raw_history, str) and raw_history:
        try:
            history = json.loads(raw_history)
        except json.JSONDecodeError:
            history = []
    elif isinstance(raw_history, list):
        history = list(raw_history)
    else:
        history = []
    history.append(entry.model_dump(mode="json"))
    return json.dumps(history, ensure_ascii=False, sort_keys=True)
