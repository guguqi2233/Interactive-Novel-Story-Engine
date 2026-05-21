from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.db.migrations import CURRENT_ENGINE_VERSION
from app.platform.security import safe_identifier


CONTENT_PACK_SCHEMA_V2 = "2"


class ContentPackV2Manifest(BaseModel):
    world_id: str
    name: str
    version: str = "2.0.0"
    schema_version: str = CONTENT_PACK_SCHEMA_V2
    engine_version_min: str = CURRENT_ENGINE_VERSION
    contract_version: str = "2"
    modules_required: list[str] = Field(default_factory=list)
    content_files: dict[str, str] = Field(default_factory=dict)
    migration_policy: Literal["compatible", "migration_required", "unsupported"] = "compatible"
    visibility_policy: Literal["default_hidden_safe", "strict"] = "default_hidden_safe"
    package_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("world_id")
    @classmethod
    def validate_world_id(cls, value: str) -> str:
        if not safe_identifier(value):
            raise ValueError("Unsafe world_id")
        return value


class ContentPackV2ValidationReport(BaseModel):
    world_id: str
    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    legacy_v1_compatible: bool = False


def validate_content_pack_v2_manifest(payload: dict) -> ContentPackV2ValidationReport:
    if "schema_version" not in payload:
        world_id = str(payload.get("world_id") or payload.get("id") or "legacy_world")
        return ContentPackV2ValidationReport(world_id=world_id, ok=True, warnings=["Legacy content pack missing schema_version; v1 compatibility shim required."], legacy_v1_compatible=True)
    try:
        manifest = ContentPackV2Manifest.model_validate(payload)
    except Exception as exc:
        return ContentPackV2ValidationReport(world_id=str(payload.get("world_id", "unknown")), ok=False, errors=[str(exc)])
    return ContentPackV2ValidationReport(world_id=manifest.world_id, ok=True)

