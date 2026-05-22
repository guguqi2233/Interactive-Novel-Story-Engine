from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from app.platform.package_manifest_v2 import PackageManifestV2, PackageTypeV2
from app.platform.pack_validation import PackValidationReport, collect_ids, validate_manifest_type, validate_no_secrets, validate_unique


FORBIDDEN_PROMPT_FLAGS = {
    "can_access_hidden_facts",
    "can_modify_state",
    "can_override_action_result",
    "can_bypass_visibility",
}


class PromptProfilePack(BaseModel):
    manifest: PackageManifestV2
    prompt_profiles: list[dict[str, Any]] = Field(default_factory=list)
    style_presets: list[dict[str, Any]] = Field(default_factory=list)
    mode_scopes: list[str] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return {
            **self.manifest.safe_summary(),
            "prompt_profile_count": len(self.prompt_profiles),
            "style_preset_count": len(self.style_presets),
            "mode_scopes": self.mode_scopes,
        }


def validate_prompt_profile_pack(pack: PromptProfilePack) -> PackValidationReport:
    report = PackValidationReport(safe_summary=pack.safe_summary())
    validate_manifest_type(pack.manifest, PackageTypeV2.PROMPT_PROFILE_PACK, report)
    validate_no_secrets(pack.model_dump(mode="json"), report)
    ids = collect_ids(pack.prompt_profiles, "prompt_profile_id", "profile_id", "id")
    validate_unique(ids, "prompt profile id", report)
    text = json.dumps(pack.prompt_profiles, ensure_ascii=False, default=str)
    for flag in FORBIDDEN_PROMPT_FLAGS:
        if flag in text:
            report.add_error(f"prompt profile permission is blocked: {flag}")
    return report
