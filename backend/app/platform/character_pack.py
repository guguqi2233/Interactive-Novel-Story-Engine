from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.platform.package_manifest_v2 import PackageManifestV2, PackageTypeV2
from app.platform.pack_validation import (
    PackValidationReport,
    collect_ids,
    safe_payload_summary,
    validate_manifest_type,
    validate_no_executables,
    validate_no_secrets,
    validate_unique,
)


class CharacterPack(BaseModel):
    manifest: PackageManifestV2
    character_profiles: list[dict[str, Any]] = Field(default_factory=list)
    tavern_characters: list[dict[str, Any]] = Field(default_factory=list)
    rp_profiles: list[dict[str, Any]] = Field(default_factory=list)
    voice_profiles: list[dict[str, Any]] = Field(default_factory=list)
    character_cards: list[dict[str, Any]] = Field(default_factory=list)
    world_npc_drafts: list[dict[str, Any]] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return {
            **self.manifest.safe_summary(),
            "character_profile_count": len(self.character_profiles),
            "tavern_character_count": len(self.tavern_characters),
            "world_npc_draft_count": len(self.world_npc_drafts),
            "public_preview": safe_payload_summary(
                {
                    "character_profiles": [
                        {key: value for key, value in item.items() if "private" not in key and "secret" not in key}
                        for item in self.character_profiles
                    ]
                }
            ),
        }


def validate_character_pack(pack: CharacterPack) -> PackValidationReport:
    report = PackValidationReport(safe_summary=pack.safe_summary())
    validate_manifest_type(pack.manifest, PackageTypeV2.CHARACTER_PACK, report)
    validate_no_executables(pack.manifest, report)
    validate_no_secrets(pack.model_dump(mode="json"), report)
    ids = collect_ids(pack.character_profiles + pack.tavern_characters, "character_id", "id")
    validate_unique(ids, "character id", report)
    rp_ids = set(collect_ids(pack.rp_profiles, "rp_profile_id", "id"))
    voice_ids = set(collect_ids(pack.voice_profiles, "voice_profile_id", "id"))
    for character in pack.tavern_characters:
        rp_ref = character.get("rp_profile_id")
        voice_ref = character.get("voice_profile_id")
        if rp_ref and rp_ref not in rp_ids:
            report.add_error(f"invalid rp_profile ref: {rp_ref}")
        if voice_ref and voice_ref not in voice_ids:
            report.add_error(f"invalid voice_profile ref: {voice_ref}")
    return report
