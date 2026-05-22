from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.platform.package_manifest_v2 import PackageManifestV2, PackageTypeV2
from app.platform.pack_validation import (
    PackValidationReport,
    collect_ids,
    validate_manifest_type,
    validate_no_executables,
    validate_no_hidden_leak,
    validate_no_secrets,
    validate_unique,
)


class WorldPatchOperation(StrEnum):
    ADD = "add"
    SET = "set"
    INC = "inc"
    REMOVE = "remove"


class WorldExtensionPatch(BaseModel):
    target: str
    path: str
    operation: WorldPatchOperation
    value: Any | None = None
    destructive: bool = False

    @model_validator(mode="after")
    def _validate_patch(self) -> "WorldExtensionPatch":
        if self.destructive:
            raise ValueError("destructive overrides are blocked by default")
        if self.path.startswith("/") or ".." in self.path.split("."):
            raise ValueError("unsafe patch path")
        return self


class WorldExtensionPack(BaseModel):
    manifest: PackageManifestV2
    locations_add: list[dict[str, Any]] = Field(default_factory=list)
    npcs_add: list[dict[str, Any]] = Field(default_factory=list)
    items_add: list[dict[str, Any]] = Field(default_factory=list)
    quests_add: list[dict[str, Any]] = Field(default_factory=list)
    facts_add: list[dict[str, Any]] = Field(default_factory=list)
    factions_add: list[dict[str, Any]] = Field(default_factory=list)
    rumors_add: list[dict[str, Any]] = Field(default_factory=list)
    relationships_add: list[dict[str, Any]] = Field(default_factory=list)
    patches: list[WorldExtensionPatch] = Field(default_factory=list)

    def safe_summary(self) -> dict[str, Any]:
        return {
            **self.manifest.safe_summary(),
            "locations_add": len(self.locations_add),
            "npcs_add": len(self.npcs_add),
            "quests_add": len(self.quests_add),
            "patch_count": len(self.patches),
            "modifies_active_game_state": False,
        }


def validate_world_extension_pack(pack: WorldExtensionPack, *, existing_ids: set[str] | None = None) -> PackValidationReport:
    report = PackValidationReport(safe_summary=pack.safe_summary())
    validate_manifest_type(pack.manifest, PackageTypeV2.WORLD_EXTENSION_PACK, report)
    validate_no_executables(pack.manifest, report)
    validate_no_secrets(pack.model_dump(mode="json"), report)
    validate_no_hidden_leak(pack.model_dump(mode="json"), report)
    existing_ids = existing_ids or set()
    for label, items in {
        "location id": pack.locations_add,
        "npc id": pack.npcs_add,
        "item id": pack.items_add,
        "quest id": pack.quests_add,
        "fact id": pack.facts_add,
        "faction id": pack.factions_add,
        "rumor id": pack.rumors_add,
        "relationship id": pack.relationships_add,
    }.items():
        ids = collect_ids(items, "id", f"{label.split()[0]}_id")
        validate_unique(ids, label, report)
        for item_id in ids:
            if item_id in existing_ids:
                report.add_error(f"id conflict detected: {item_id}")
    for patch in pack.patches:
        if patch.target not in existing_ids:
            report.add_error(f"patch target missing or unconfirmed: {patch.target}")
    return report
