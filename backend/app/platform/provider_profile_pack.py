from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from app.platform.package_manifest_v2 import PackageManifestV2, PackageTypeV2
from app.platform.pack_validation import PackValidationReport, validate_manifest_type, validate_no_executables


class ProviderProfilePack(BaseModel):
    manifest: PackageManifestV2
    provider_profiles: list[dict[str, Any]] = Field(default_factory=list)
    model_profiles: list[dict[str, Any]] = Field(default_factory=list)
    routing_templates: list[dict[str, Any]] = Field(default_factory=list)
    capability_matrix: dict[str, Any] | None = None

    def safe_summary(self) -> dict[str, Any]:
        return {
            **self.manifest.safe_summary(),
            "provider_profile_count": len(self.provider_profiles),
            "model_profile_count": len(self.model_profiles),
            "imports_disabled_by_default": True,
        }


def _find_forbidden_provider_secret(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).lower()
            if lowered in {"api_key", "authorization", "x-api-key"}:
                return str(key)
            if lowered == "headers" and isinstance(value, dict):
                for header_key in value:
                    if "auth" in str(header_key).lower() or "key" in str(header_key).lower():
                        return f"headers.{header_key}"
            found = _find_forbidden_provider_secret(value)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_forbidden_provider_secret(item)
            if found:
                return found
    return None


def validate_provider_profile_pack(pack: ProviderProfilePack) -> PackValidationReport:
    report = PackValidationReport(safe_summary=pack.safe_summary())
    validate_manifest_type(pack.manifest, PackageTypeV2.PROVIDER_PROFILE_PACK, report)
    validate_no_executables(pack.manifest, report)
    forbidden = _find_forbidden_provider_secret(pack.model_dump(mode="json"))
    if forbidden:
        report.add_error(f"provider profile pack cannot contain secret field: {forbidden}")
    text = json.dumps(pack.model_dump(mode="json"), ensure_ascii=False, default=str)
    if "sk-" in text and "sk-test" not in text and "sk-fake" not in text:
        report.add_error("provider profile pack contains API-key-like text")
    for profile in pack.provider_profiles:
        if profile.get("enabled") is True:
            report.add_warning("imported provider profiles should be disabled until user confirmation")
    return report
