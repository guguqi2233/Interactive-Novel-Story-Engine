from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field, model_validator

from app.engine.content.character_pack_builder import (
    CharacterPack,
    CharacterPackExportRequest,
    CharacterPackImportRequest,
)
from app.engine.content.validator import ValidationReport, ValidationSeverity


ProfileKind = Literal["safe", "authoring", "strict"]


class ExportProfile(BaseModel):
    profile_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    kind: ProfileKind = "safe"
    include_world: bool = True
    include_characters: bool = True
    include_templates: bool = False
    include_scenarios: bool = False
    include_prompt_profiles: bool = False
    include_hidden_authoring_data: bool = False
    redact_hidden_text: bool = True
    include_quality_reports: bool = False
    include_test_fixtures: bool = False
    forbids_api_keys: bool = True

    @model_validator(mode="after")
    def validate_export_profile(self) -> "ExportProfile":
        if not self.forbids_api_keys:
            raise ValueError("Export profiles cannot allow API keys.")
        if self.include_hidden_authoring_data and not self.redact_hidden_text and self.kind != "authoring":
            raise ValueError("Hidden authoring data without redaction is only valid for explicit authoring profiles.")
        return self


class ImportProfile(BaseModel):
    profile_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    kind: ProfileKind = "safe"
    allow_overwrite: bool = False
    allow_hidden_authoring_data: bool = False
    require_validation: bool = True
    require_quality_gate: bool = True
    require_migration_check: bool = True
    reject_executables: bool = True
    reject_unknown_schema: bool = True
    forbids_api_keys: bool = True

    @model_validator(mode="after")
    def validate_import_profile(self) -> "ImportProfile":
        if not self.forbids_api_keys:
            raise ValueError("Import profiles cannot allow API keys.")
        if not self.require_validation:
            raise ValueError("Import profiles must require validation.")
        if not self.reject_executables:
            raise ValueError("Import profiles must reject executables.")
        return self


ProfileT = TypeVar("ProfileT", ExportProfile, ImportProfile)


class ImportExportProfileCatalog(BaseModel):
    export_profiles: list[ExportProfile]
    import_profiles: list[ImportProfile]


def default_export_profiles() -> list[ExportProfile]:
    return [
        ExportProfile(profile_id="safe", name="Safe Export", kind="safe"),
        ExportProfile(
            profile_id="authoring_redacted",
            name="Authoring Export (Redacted)",
            kind="authoring",
            include_templates=True,
            include_scenarios=True,
            include_prompt_profiles=True,
            include_hidden_authoring_data=True,
            redact_hidden_text=True,
            include_quality_reports=True,
            include_test_fixtures=True,
        ),
    ]


def default_import_profiles() -> list[ImportProfile]:
    return [
        ImportProfile(profile_id="safe", name="Safe Import", kind="safe"),
        ImportProfile(
            profile_id="strict",
            name="Strict Import",
            kind="strict",
            allow_overwrite=False,
            allow_hidden_authoring_data=False,
            require_validation=True,
            require_quality_gate=True,
            require_migration_check=True,
            reject_executables=True,
            reject_unknown_schema=True,
        ),
        ImportProfile(
            profile_id="authoring_review",
            name="Authoring Review Import",
            kind="authoring",
            allow_hidden_authoring_data=True,
            require_validation=True,
            require_quality_gate=True,
            require_migration_check=True,
            reject_executables=True,
            reject_unknown_schema=True,
        ),
    ]


def get_import_export_profile_catalog() -> ImportExportProfileCatalog:
    return ImportExportProfileCatalog(
        export_profiles=default_export_profiles(),
        import_profiles=default_import_profiles(),
    )


def get_export_profile(profile_id: str) -> ExportProfile:
    return _get_profile(default_export_profiles(), profile_id, "export")


def get_import_profile(profile_id: str) -> ImportProfile:
    return _get_profile(default_import_profiles(), profile_id, "import")


def apply_export_profile_to_character_pack(pack: CharacterPack, profile: ExportProfile) -> CharacterPack:
    serialized = pack.model_dump(mode="json")
    if _contains_api_key(serialized):
        raise ValueError("Export profile blocked API key or sensitive configuration text.")
    redacted = pack.model_copy(deep=True)
    if not profile.include_hidden_authoring_data:
        redacted.manifest.includes_hidden_facts = False
        redacted.fact_candidates = [candidate for candidate in redacted.fact_candidates if candidate.visibility == "public"]
        redacted.flavor_lore = [entry for entry in redacted.flavor_lore if entry.visibility == "public"]
        for character in redacted.characters:
            _drop_hidden_character_fields(character)
        for profile_payload in redacted.rp_profiles.values():
            profile_payload.pop("private_self_summary", None)
    elif profile.redact_hidden_text:
        redacted.manifest.includes_hidden_facts = True
        for candidate in redacted.fact_candidates:
            if candidate.visibility != "public":
                candidate.text = "[redacted]"
                if "hidden_authoring_data" not in candidate.tags:
                    candidate.tags.append("hidden_authoring_data")
        for entry in redacted.flavor_lore:
            if entry.visibility != "public":
                entry.text = "[redacted]"
                if "hidden_authoring_data" not in entry.tags:
                    entry.tags.append("hidden_authoring_data")
        for character in redacted.characters:
            if "hidden" in character:
                character["hidden"] = "[redacted]"
    if _contains_api_key(redacted.model_dump(mode="json")):
        raise ValueError("Export profile blocked API key or sensitive configuration text.")
    return redacted


def character_pack_export_request_for_profile(
    request: CharacterPackExportRequest,
    profile: ExportProfile,
) -> CharacterPackExportRequest:
    return request.model_copy(
        update={
            "safe_export": not profile.include_hidden_authoring_data,
            "include_hidden_facts": profile.include_hidden_authoring_data,
        }
    )


def validate_character_pack_import_profile(
    request: CharacterPackImportRequest,
    profile: ImportProfile,
) -> ValidationReport:
    report = ValidationReport(world_id=request.world_id)
    if profile.reject_executables:
        for file in request.pack.files:
            if _is_unsafe_package_path(file.path):
                report.add(
                    ValidationSeverity.ERROR,
                    f"import_profile.files.{file.path}",
                    "Import profile rejected package content path traversal.",
                    code="import_profile_path_traversal_rejected",
                    ref_id=file.path,
                )
                continue
            lowered = file.path.lower()
            if lowered.endswith((".bat", ".cmd", ".com", ".dll", ".exe", ".js", ".mjs", ".ps1", ".py", ".sh", ".vbs")):
                report.add(
                    ValidationSeverity.ERROR,
                    f"import_profile.files.{file.path}",
                    "Import profile rejected executable package content.",
                    code="import_profile_executable_rejected",
                    ref_id=file.path,
                )
    if not profile.allow_hidden_authoring_data:
        hidden_ids = [candidate.id for candidate in request.pack.fact_candidates if candidate.visibility != "public"]
        if hidden_ids:
            report.add(
                ValidationSeverity.WARNING,
                "import_profile.hidden_authoring_data",
                "Import profile does not allow hidden authoring data; hidden fact candidates will remain review-only.",
                code="import_profile_hidden_authoring_data_skipped",
                ref_id=",".join(hidden_ids),
            )
    if _contains_api_key(request.pack.model_dump(mode="json")):
        report.add(
            ValidationSeverity.ERROR,
            "import_profile.secrets",
            "Import profile rejected API key or sensitive configuration text.",
            code="import_profile_api_key_rejected",
        )
    if not profile.require_validation:
        report.add(
            ValidationSeverity.ERROR,
            "import_profile.validation",
            "Import profile must require validation.",
            code="import_profile_validation_required",
        )
    return report


def _get_profile(profiles: list[ProfileT], profile_id: str, kind: str) -> ProfileT:
    for profile in profiles:
        if profile.profile_id == profile_id:
            return profile
    raise ValueError(f"Unknown {kind} profile: {profile_id}")


def _drop_hidden_character_fields(character: dict[str, Any]) -> None:
    for key in ("hidden", "knowledge", "secrets", "player_visible_facts", "api_key"):
        character.pop(key, None)


def _contains_api_key(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(token in lowered for token in ("sk-", "api_key", "apikey", "secret_key", "private_key", "bearer "))
    if isinstance(value, dict):
        return any(_contains_api_key(key) or _contains_api_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_api_key(child) for child in value)
    return False


def _is_unsafe_package_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    return (
        not normalized
        or normalized.startswith("/")
        or ":" in normalized
        or ".." in parts
    )
