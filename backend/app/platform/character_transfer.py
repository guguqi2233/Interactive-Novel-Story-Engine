from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.platform.security import safe_identifier


class CharacterTransferPackage(BaseModel):
    package_id: str
    character_id: str
    source_world_id: str
    contract_version: str = "2"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    public_identity: dict[str, str] = Field(default_factory=dict)
    rp_profile: dict[str, str] = Field(default_factory=dict)
    voice_profile: dict[str, str] = Field(default_factory=dict)
    public_history: list[str] = Field(default_factory=list)
    selected_memories_redacted: list[str] = Field(default_factory=list)
    checksums: dict[str, str] = Field(default_factory=dict)


class CharacterTransferPlan(BaseModel):
    ok: bool
    target_world_id: str
    mapping_warnings: list[str] = Field(default_factory=list)
    hidden_redacted: bool = True


class CharacterTransferReport(BaseModel):
    ok: bool
    dry_run: bool = True
    applied: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CharacterTransferService:
    def export_character(self, character_id: str, source_world_id: str, *, public_identity: dict[str, str] | None = None) -> CharacterTransferPackage:
        if not safe_identifier(character_id) or not safe_identifier(source_world_id):
            raise ValueError("Unsafe character/world id")
        return CharacterTransferPackage(
            package_id=f"{character_id}_transfer",
            character_id=character_id,
            source_world_id=source_world_id,
            public_identity=public_identity or {"id": character_id},
            checksums={"manifest": "metadata-only"},
        )

    def import_dry_run(self, package: CharacterTransferPackage, target_world_id: str) -> CharacterTransferReport:
        warnings = []
        if package.source_world_id == target_world_id:
            warnings.append("Source and target world are identical.")
        return CharacterTransferReport(ok=True, dry_run=True, warnings=warnings)

    def import_apply(self, package: CharacterTransferPackage, target_world_id: str, *, confirm_apply: bool = False) -> CharacterTransferReport:
        if not confirm_apply:
            return CharacterTransferReport(ok=False, dry_run=False, errors=["confirm_apply is required"])
        return CharacterTransferReport(ok=True, dry_run=False, applied=True)

