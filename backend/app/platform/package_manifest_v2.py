from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.platform.module_permissions import ModulePermissionSet, validate_module_permissions
from app.platform.rp_mature import MatureModPolicy
from app.platform.security import contains_secret_text, validate_relative_package_path


class PackageTypeV2(StrEnum):
    SCRIPT_PACK = "script_pack"
    WORLD_EXTENSION_PACK = "world_extension_pack"
    CHARACTER_PACK = "character_pack"
    PROMPT_PROFILE_PACK = "prompt_profile_pack"
    PROVIDER_PROFILE_PACK = "provider_profile_pack"
    NARRATIVE_STYLE_MOD = "narrative_style_mod"
    RP_PROFILE_MOD = "rp_profile_mod"
    ACTION_MOD = "action_mod"
    RULE_MODULE = "rule_module"
    TEMPLATE_PACK = "template_pack"


EXECUTABLE_SUFFIXES = {".py", ".js", ".sh", ".ps1", ".bat", ".cmd", ".exe", ".dll", ".com"}


class PackageDependency(BaseModel):
    package_id: str
    version_min: str | None = None
    version_max: str | None = None


class PackageFileEntry(BaseModel):
    path: str
    media_type: str = "application/octet-stream"
    required: bool = True

    @field_validator("path")
    @classmethod
    def _safe_path(cls, value: str) -> str:
        return validate_relative_package_path(value)


class PackageEntryPoint(BaseModel):
    entry_id: str
    path: str
    kind: str = "declarative"

    @field_validator("path")
    @classmethod
    def _safe_path(cls, value: str) -> str:
        safe = validate_relative_package_path(value)
        if any(safe.lower().endswith(suffix) for suffix in EXECUTABLE_SUFFIXES):
            raise ValueError("executable entry points are blocked in v2.6")
        return safe

    @field_validator("kind")
    @classmethod
    def _safe_kind(cls, value: str) -> str:
        if value.lower() in {"python", "javascript", "executable", "shell", "binary"}:
            raise ValueError("entry point kind cannot execute code")
        return value


class PackageManifestV2(BaseModel):
    package_id: str
    name: str
    version: str
    package_type: PackageTypeV2
    description: str = ""
    author: str | None = None
    engine_version_min: str = "2.6"
    engine_version_max: str | None = None
    schema_version: str = "2.6"
    target_project_modes: list[str] = Field(default_factory=list)
    target_worlds: list[str] = Field(default_factory=list)
    dependencies: list[PackageDependency] = Field(default_factory=list)
    optional_dependencies: list[PackageDependency] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    permissions: ModulePermissionSet = Field(default_factory=ModulePermissionSet)
    included_files: list[PackageFileEntry] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)
    entry_points: list[PackageEntryPoint] = Field(default_factory=list)
    compatibility_notes: list[str] = Field(default_factory=list)
    migration_notes: list[str] = Field(default_factory=list)
    mature_policy: MatureModPolicy = Field(default_factory=MatureModPolicy)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {"extra": "forbid"}

    @field_validator("target_project_modes")
    @classmethod
    def _validate_modes(cls, value: list[str]) -> list[str]:
        allowed = {"novel", "tavern", "world", "cross_mode", "quality", "provider", "all"}
        invalid = sorted(set(value) - allowed)
        if invalid:
            raise ValueError(f"unsupported target project modes: {', '.join(invalid)}")
        return value

    @field_validator("checksums")
    @classmethod
    def _validate_checksums(cls, value: dict[str, str]) -> dict[str, str]:
        for path, checksum in value.items():
            validate_relative_package_path(path)
            if checksum and not checksum.startswith("sha256:"):
                raise ValueError("checksums must use sha256:<hex> format")
        return value

    @model_validator(mode="after")
    def _validate_security(self) -> "PackageManifestV2":
        permission_report = validate_module_permissions(self.permissions)
        if not permission_report.ok:
            raise ValueError("; ".join(permission_report.errors))
        text = json.dumps(self.model_dump(mode="json", exclude={"created_at"}), ensure_ascii=False)
        if contains_secret_text(text):
            raise ValueError("manifest contains secret-like text")
        mature_text = json.dumps(self.mature_policy.model_dump(mode="json"), ensure_ascii=False).lower()
        if "can_access_hidden_facts" in mature_text and '"can_access_hidden_facts": true' in mature_text:
            raise ValueError("mature package policy cannot access hidden facts")
        for entry in self.included_files:
            if any(entry.path.lower().endswith(suffix) for suffix in EXECUTABLE_SUFFIXES):
                raise ValueError(f"executable payload is blocked: {entry.path}")
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "name": self.name,
            "version": self.version,
            "package_type": self.package_type.value,
            "target_project_modes": self.target_project_modes,
            "target_worlds": self.target_worlds,
            "permissions": self.permissions.safe_summary(),
            "mature_policy": self.mature_policy.safe_summary(),
            "entry_point_count": len(self.entry_points),
            "included_file_count": len(self.included_files),
        }
