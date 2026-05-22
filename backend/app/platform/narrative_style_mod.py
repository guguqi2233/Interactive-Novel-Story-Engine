from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.platform.package_manifest_v2 import PackageManifestV2, PackageTypeV2
from app.platform.pack_validation import PackValidationReport, validate_manifest_type, validate_no_secrets


FORBIDDEN_STYLE_BEHAVIORS = {
    "modify_state",
    "access_hidden_facts",
    "override_action_result",
    "create_key_items",
    "complete_quests",
}


class NarrativeStyleMod(BaseModel):
    manifest: PackageManifestV2
    style_id: str
    name: str
    description: str = ""
    target_modes: list[Literal["novel", "tavern", "world", "cross_mode"]] = Field(default_factory=list)
    tone: str = ""
    pacing: str = ""
    perspective: str = ""
    sensory_focus: list[str] = Field(default_factory=list)
    sentence_style: str = ""
    max_length_hint: int | None = None
    forbidden_behaviors: list[str] = Field(default_factory=list)

    def to_prompt_profile_preset(self) -> dict[str, Any]:
        return {
            "prompt_profile_id": f"style_{self.style_id}",
            "display_name": self.name,
            "mode_scopes": self.target_modes,
            "style": {
                "tone": self.tone,
                "pacing": self.pacing,
                "perspective": self.perspective,
                "sensory_focus": self.sensory_focus,
                "sentence_style": self.sentence_style,
                "max_length_hint": self.max_length_hint,
            },
            "can_access_hidden_facts": False,
            "can_modify_state": False,
            "can_override_action_result": False,
        }

    def safe_summary(self) -> dict[str, Any]:
        return {
            **self.manifest.safe_summary(),
            "style_id": self.style_id,
            "name": self.name,
            "target_modes": self.target_modes,
            "fact_authority": "expression_only",
        }


def validate_narrative_style_mod(mod: NarrativeStyleMod) -> PackValidationReport:
    report = PackValidationReport(safe_summary=mod.safe_summary())
    validate_manifest_type(mod.manifest, PackageTypeV2.NARRATIVE_STYLE_MOD, report)
    validate_no_secrets(mod.model_dump(mode="json"), report)
    for behavior in FORBIDDEN_STYLE_BEHAVIORS:
        if behavior in mod.forbidden_behaviors:
            report.add_error(f"style mod cannot request behavior: {behavior}")
    preset = mod.to_prompt_profile_preset()
    if any(preset.get(key) for key in ("can_access_hidden_facts", "can_modify_state", "can_override_action_result")):
        report.add_error("converted prompt profile expands permissions")
    return report
