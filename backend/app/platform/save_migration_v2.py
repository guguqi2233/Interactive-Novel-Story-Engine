from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.core.world_state import CURRENT_GAME_STATE_SCHEMA_VERSION
from app.db.migrations import CURRENT_ENGINE_VERSION


SAVE_V2_VERSION = "2"


class SaveV2Metadata(BaseModel):
    save_version: str = SAVE_V2_VERSION
    game_state_schema_version: str = CURRENT_GAME_STATE_SCHEMA_VERSION
    engine_version: str = CURRENT_ENGINE_VERSION
    content_pack_version: str | None = None
    module_versions: dict[str, str] = Field(default_factory=dict)
    migration_history: list[dict[str, str]] = Field(default_factory=list)
    checksum: str | None = None


class MigrationPathV2(BaseModel):
    source_version: str
    target_version: str = SAVE_V2_VERSION
    can_migrate: bool = True
    warnings: list[str] = Field(default_factory=list)


class SaveMigrationV2Report(BaseModel):
    ok: bool
    dry_run: bool = True
    source_version: str
    target_version: str = SAVE_V2_VERSION
    backup_created: bool = False
    event_log_preserved: bool = True
    hidden_visibility_preserved: bool = True
    module_state_warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


def plan_save_migration_v2(source_version: str | None) -> MigrationPathV2:
    version = source_version or "legacy"
    if version in {"2", "2.0"}:
        return MigrationPathV2(source_version=version)
    if version.startswith("v") or version in {"legacy", "1", "1.8", "1.9"}:
        return MigrationPathV2(source_version=version, warnings=["Legacy save requires v2 compatibility migration."])
    return MigrationPathV2(source_version=version, can_migrate=False, warnings=["Unsupported save version."])
