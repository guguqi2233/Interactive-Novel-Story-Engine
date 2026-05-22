from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.platform.package_manifest_v2 import PackageManifestV2, PackageTypeV2
from app.platform.pack_validation import PackValidationReport, validate_manifest_type, validate_no_secrets


class RPProfilePatchOperation(StrEnum):
    ADD = "add"
    SET = "set"
    REMOVE = "remove"


ALLOWED_RP_PATCH_PREFIXES = {
    "tone",
    "voice",
    "style",
    "emotion",
    "dialogue",
    "relationship_tone",
    "catchphrases",
    "baseline_mood",
}


class RPProfilePatch(BaseModel):
    target_profile_id: str
    path: str
    operation: RPProfilePatchOperation
    value: Any | None = None


class RPProfileMod(BaseModel):
    manifest: PackageManifestV2
    add_rp_profile: list[dict[str, Any]] = Field(default_factory=list)
    patch_rp_profile: list[RPProfilePatch] = Field(default_factory=list)
    add_voice_profile: list[dict[str, Any]] = Field(default_factory=list)
    patch_voice_profile: list[RPProfilePatch] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return {
            **self.manifest.safe_summary(),
            "add_rp_profile_count": len(self.add_rp_profile),
            "patch_rp_profile_count": len(self.patch_rp_profile),
            "add_voice_profile_count": len(self.add_voice_profile),
            "patch_voice_profile_count": len(self.patch_voice_profile),
        }


def validate_rp_profile_mod(mod: RPProfileMod, *, existing_profile_ids: set[str] | None = None) -> PackValidationReport:
    report = PackValidationReport(safe_summary=mod.safe_summary())
    validate_manifest_type(mod.manifest, PackageTypeV2.RP_PROFILE_MOD, report)
    validate_no_secrets(mod.model_dump(mode="json"), report)
    existing_profile_ids = existing_profile_ids or set()
    for patch in [*mod.patch_rp_profile, *mod.patch_voice_profile]:
        if patch.target_profile_id not in existing_profile_ids:
            report.add_error(f"patch target profile does not exist: {patch.target_profile_id}")
        root = patch.path.split(".", 1)[0]
        if root not in ALLOWED_RP_PATCH_PREFIXES:
            report.add_error(f"RP profile patch path is blocked: {patch.path}")
        if "knowledge" in patch.path or "hidden" in patch.path or "game_state" in patch.path:
            report.add_error(f"RP profile patch cannot alter world knowledge or hidden access: {patch.path}")
    return report
