from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.platform.package_manifest_v2 import PackageManifestV2, PackageTypeV2
from app.platform.pack_validation import (
    PackValidationReport,
    validate_manifest_type,
    validate_no_executables,
    validate_no_hidden_leak,
    validate_no_secrets,
)


class ScriptPackV2(BaseModel):
    manifest: PackageManifestV2
    scenarios: list[dict[str, Any]] = Field(default_factory=list)
    quest_drafts: list[dict[str, Any]] = Field(default_factory=list)
    novel_outline_drafts: list[dict[str, Any]] = Field(default_factory=list)
    tavern_scene_presets: list[dict[str, Any]] = Field(default_factory=list)
    cross_mode_templates: list[dict[str, Any]] = Field(default_factory=list)
    quality_checks: list[dict[str, Any]] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return {
            **self.manifest.safe_summary(),
            "scenario_count": len(self.scenarios),
            "quest_draft_count": len(self.quest_drafts),
            "novel_outline_draft_count": len(self.novel_outline_drafts),
            "tavern_scene_preset_count": len(self.tavern_scene_presets),
            "cross_mode_template_count": len(self.cross_mode_templates),
        }


def validate_script_pack(pack: ScriptPackV2) -> PackValidationReport:
    report = PackValidationReport(safe_summary=pack.safe_summary())
    validate_manifest_type(pack.manifest, PackageTypeV2.SCRIPT_PACK, report)
    validate_no_executables(pack.manifest, report)
    validate_no_secrets(pack.model_dump(mode="json"), report)
    validate_no_hidden_leak(
        {
            "scenarios": pack.scenarios,
            "quest_drafts": pack.quest_drafts,
            "novel_outline_drafts": pack.novel_outline_drafts,
            "tavern_scene_presets": pack.tavern_scene_presets,
            "cross_mode_templates": pack.cross_mode_templates,
        },
        report,
        severity="error",
    )
    return report


def _load_pack_file(pack_path: Path) -> dict[str, Any]:
    text = pack_path.read_text(encoding="utf-8")
    if pack_path.suffix.lower() in {".yaml", ".yml"}:
        loaded = yaml.safe_load(text)
    else:
        import json

        loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("script pack root must be an object")
    return loaded


def validate_script_pack_file(pack_path: Path) -> PackValidationReport:
    try:
        pack = ScriptPackV2.model_validate(_load_pack_file(pack_path))
    except (ValidationError, ValueError) as exc:
        return PackValidationReport(ok=False, errors=[str(exc)])
    return validate_script_pack(pack)


def list_script_pack_contents(pack_path: Path) -> dict[str, Any]:
    pack = ScriptPackV2.model_validate(_load_pack_file(pack_path))
    return pack.safe_summary()
