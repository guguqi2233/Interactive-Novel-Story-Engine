from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


COMPATIBILITY_CONTRACT_VERSION = "1.8"
GAMESTATE_CONTRACT_VERSION = "1.8"
STATEDELTA_CONTRACT_VERSION = "1.8"
EVENTLOG_CONTRACT_VERSION = "1.8"
CONTENT_PACK_SCHEMA_CONTRACT_VERSION = "1.8"
SAVE_MIGRATION_CONTRACT_VERSION = "1.8"
MODULE_CONTRACT_VERSION = "1.8"
ACTION_MOD_CONTRACT_VERSION = "1.8"
PROMPT_PROFILE_CONTRACT_VERSION = "1.8"
PROVIDER_CONTRACT_VERSION = "1.8"
PACKAGE_CONTRACT_VERSION = "1.8"
AUTHORING_API_CONTRACT_VERSION = "1.8"
DEBUG_API_CONTRACT_VERSION = "1.8"
QUALITY_GATE_CONTRACT_VERSION = "1.8"


class CompatibilityStatus(StrEnum):
    COMPATIBLE = "compatible"
    MIGRATION_REQUIRED = "migration_required"
    DEPRECATED = "deprecated"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class DeprecatedField(BaseModel):
    field_path: str
    introduced_version: str
    deprecated_version: str
    removal_version: str | None = None
    replacement: str
    migration_strategy: str
    warning_level: str = "warning"


class CompatibilityIssue(BaseModel):
    code: str
    message: str
    severity: str = "warning"
    path: str = ""


class CompatibilityPolicy(BaseModel):
    contract_version: str = COMPATIBILITY_CONTRACT_VERSION
    breaking_change_requires_migration_or_major_bump: bool = True
    deprecated_field_requires_metadata: bool = True
    save_migration_must_preserve_event_log: bool = True
    package_import_requires_compatibility_check: bool = True
    modules_require_contract_version: bool = True
    prompt_provider_profiles_require_contract_version: bool = True


class CompatibilityCheckResult(BaseModel):
    ok: bool
    status: CompatibilityStatus = CompatibilityStatus.COMPATIBLE
    issues: list[CompatibilityIssue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


DEPRECATED_FIELDS: tuple[DeprecatedField, ...] = (
    DeprecatedField(
        field_path="content_pack.manifest.content_schema_version",
        introduced_version="0.6",
        deprecated_version="1.8",
        replacement="schema_version",
        migration_strategy="Map content_schema_version to schema_version during legacy content-pack loading.",
    ),
)


def validate_contract_version(
    value: str | None,
    *,
    expected: str,
    path: str,
    allow_legacy: bool = False,
) -> CompatibilityCheckResult:
    issues: list[CompatibilityIssue] = []
    warnings: list[str] = []
    if not value:
        if allow_legacy:
            warnings.append(f"{path} missing contract_version; legacy compatibility shim required.")
            return CompatibilityCheckResult(
                ok=True,
                status=CompatibilityStatus.MIGRATION_REQUIRED,
                warnings=warnings,
            )
        issues.append(
            CompatibilityIssue(
                code="missing_contract_version",
                message=f"{path} must declare contract_version.",
                severity="error",
                path=path,
            )
        )
        return CompatibilityCheckResult(ok=False, status=CompatibilityStatus.UNSUPPORTED, issues=issues)
    if value != expected:
        issues.append(
            CompatibilityIssue(
                code="unsupported_contract_version",
                message=f"{path} contract_version {value} is not supported by contract {expected}.",
                severity="error",
                path=path,
            )
        )
        return CompatibilityCheckResult(ok=False, status=CompatibilityStatus.UNSUPPORTED, issues=issues)
    return CompatibilityCheckResult(ok=True)


def deprecated_field_warnings(payload: dict[str, Any]) -> list[CompatibilityIssue]:
    issues: list[CompatibilityIssue] = []
    for field in DEPRECATED_FIELDS:
        if _contains_path(payload, field.field_path.split(".")):
            issues.append(
                CompatibilityIssue(
                    code="deprecated_field",
                    message=(
                        f"{field.field_path} is deprecated since {field.deprecated_version}; "
                        f"use {field.replacement}. Migration: {field.migration_strategy}"
                    ),
                    severity=field.warning_level,
                    path=field.field_path,
                )
            )
    return issues


def _contains_path(payload: dict[str, Any], parts: list[str]) -> bool:
    current: Any = payload
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return True
