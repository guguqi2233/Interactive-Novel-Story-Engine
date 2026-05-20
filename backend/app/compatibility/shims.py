from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import BaseModel, Field


class CompatibilityShimWarning(BaseModel):
    shim_type: str
    path: str
    message: str


class CompatibilityShimResult(BaseModel):
    payload: dict[str, Any]
    warnings: list[CompatibilityShimWarning] = Field(default_factory=list)


def apply_compatibility_shims(payload: dict[str, Any], *, scope: str) -> CompatibilityShimResult:
    """Apply conservative legacy shims without changing visibility semantics."""
    migrated = deepcopy(payload)
    warnings: list[CompatibilityShimWarning] = []

    if scope in {"content_pack", "package"}:
        _rename_field(
            migrated,
            "content_schema_version",
            "schema_version",
            warnings,
            scope=scope,
        )

    if scope in {"module_manifest", "action_mod", "prompt_profile", "package"}:
        if "contract_version" not in migrated:
            warnings.append(
                CompatibilityShimWarning(
                    shim_type="legacy_version_detection",
                    path="contract_version",
                    message="Legacy payload is missing contract_version; validation must decide whether legacy mode is allowed.",
                )
            )

    return CompatibilityShimResult(payload=migrated, warnings=warnings)


def _rename_field(
    payload: dict[str, Any],
    old_name: str,
    new_name: str,
    warnings: list[CompatibilityShimWarning],
    *,
    scope: str,
) -> None:
    if old_name in payload and new_name not in payload:
        payload[new_name] = payload[old_name]
        warnings.append(
            CompatibilityShimWarning(
                shim_type="field_rename",
                path=f"{scope}.{old_name}",
                message=f"Mapped deprecated field {old_name} to {new_name}.",
            )
        )
