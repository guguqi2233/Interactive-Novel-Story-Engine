from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ModulePermissionRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


DANGEROUS_PERMISSION_KEYS: set[str] = {
    "execute_code",
    "access_filesystem",
    "access_network",
    "read_secrets",
    "write_database",
    "modify_game_state_directly",
    "bypass_visibility",
    "call_llm",
}

SAFE_PERMISSION_KEYS: set[str] = {
    "add_content",
    "add_templates",
    "add_prompt_profile",
    "add_provider_profile_template",
    "add_declarative_action",
    "add_rp_profile",
    "add_narrative_style",
}


def _default_category() -> dict[str, bool]:
    return {}


class ModulePermissionSet(BaseModel):
    content_permissions: dict[str, bool] = Field(default_factory=_default_category)
    action_permissions: dict[str, bool] = Field(default_factory=_default_category)
    rule_permissions: dict[str, bool] = Field(default_factory=_default_category)
    prompt_permissions: dict[str, bool] = Field(default_factory=_default_category)
    provider_permissions: dict[str, bool] = Field(default_factory=_default_category)
    file_permissions: dict[str, bool] = Field(default_factory=_default_category)
    network_permissions: dict[str, bool] = Field(default_factory=_default_category)
    secret_permissions: dict[str, bool] = Field(default_factory=_default_category)
    state_permissions: dict[str, bool] = Field(default_factory=_default_category)

    @field_validator("*", mode="before")
    @classmethod
    def _coerce_category(cls, value: Any) -> dict[str, bool]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("permission category must be an object")
        return {str(key): bool(enabled) for key, enabled in value.items()}

    def requested_permissions(self) -> dict[str, bool]:
        merged: dict[str, bool] = {}
        for category in self.model_fields:
            for key, enabled in getattr(self, category).items():
                if enabled:
                    merged[key] = True
        return merged

    def dangerous_permissions(self) -> list[str]:
        requested = self.requested_permissions()
        return sorted(key for key in requested if key in DANGEROUS_PERMISSION_KEYS)

    def safe_permissions(self) -> list[str]:
        requested = self.requested_permissions()
        return sorted(key for key in requested if key in SAFE_PERMISSION_KEYS)

    def risk_level(self) -> ModulePermissionRisk:
        if self.dangerous_permissions():
            return ModulePermissionRisk.BLOCKED
        unknown = sorted(
            key
            for key in self.requested_permissions()
            if key not in SAFE_PERMISSION_KEYS and key not in DANGEROUS_PERMISSION_KEYS
        )
        if unknown:
            return ModulePermissionRisk.MEDIUM
        if self.safe_permissions():
            return ModulePermissionRisk.LOW
        return ModulePermissionRisk.LOW

    def safe_summary(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level().value,
            "dangerous_permissions": self.dangerous_permissions(),
            "safe_permissions": self.safe_permissions(),
            "requested_permissions": sorted(self.requested_permissions()),
        }


class PermissionValidationReport(BaseModel):
    ok: bool
    risk_level: ModulePermissionRisk
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    dangerous_permissions: list[str] = Field(default_factory=list)
    safe_permissions: list[str] = Field(default_factory=list)


def validate_module_permissions(permissions: ModulePermissionSet) -> PermissionValidationReport:
    dangerous = permissions.dangerous_permissions()
    errors = [f"dangerous permission is blocked in v2.6: {permission}" for permission in dangerous]
    requested = permissions.requested_permissions()
    unknown = sorted(
        key for key in requested if key not in SAFE_PERMISSION_KEYS and key not in DANGEROUS_PERMISSION_KEYS
    )
    warnings = [f"unknown permission requires review: {permission}" for permission in unknown]
    return PermissionValidationReport(
        ok=not errors,
        risk_level=permissions.risk_level(),
        errors=errors,
        warnings=warnings,
        dangerous_permissions=dangerous,
        safe_permissions=permissions.safe_permissions(),
    )
