from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.platform.security import safe_identifier


AUTHORING_EXTENSION_CONTRACT_VERSION = "2"


class AuthoringExtensionPermissions(BaseModel):
    execute_code: bool = False
    access_network: bool = False
    access_filesystem: bool = False
    modify_game_state_directly: bool = False


class AuthoringExtensionManifest(BaseModel):
    extension_id: str
    name: str
    version: str
    contract_version: str = AUTHORING_EXTENSION_CONTRACT_VERSION
    target_entity_types: list[str] = Field(default_factory=list)
    panel_metadata: dict[str, str] = Field(default_factory=dict)
    form_schema_refs: list[str] = Field(default_factory=list)
    validation_refs: list[str] = Field(default_factory=list)
    preview_refs: list[str] = Field(default_factory=list)
    save_policy: Literal["validation_gate_required"] = "validation_gate_required"
    permissions: AuthoringExtensionPermissions = Field(default_factory=AuthoringExtensionPermissions)

    @field_validator("extension_id")
    @classmethod
    def validate_extension_id(cls, value: str) -> str:
        if not safe_identifier(value):
            raise ValueError("Unsafe extension_id")
        return value

    @model_validator(mode="after")
    def validate_safe_extension(self) -> "AuthoringExtensionManifest":
        if self.contract_version != AUTHORING_EXTENSION_CONTRACT_VERSION:
            raise ValueError("Unsupported authoring extension contract_version")
        unsafe = [name for name, value in self.permissions.model_dump().items() if value]
        if unsafe:
            raise ValueError(f"Unsafe authoring extension permissions: {', '.join(unsafe)}")
        return self


class AuthoringExtensionValidationReport(BaseModel):
    extension_id: str
    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AuthoringExtensionRegistry:
    def __init__(self) -> None:
        self._extensions: dict[str, AuthoringExtensionManifest] = {}

    def register(self, manifest: AuthoringExtensionManifest) -> AuthoringExtensionValidationReport:
        self._extensions[manifest.extension_id] = manifest
        return AuthoringExtensionValidationReport(extension_id=manifest.extension_id, ok=True)

    def list_safe_summaries(self) -> list[dict[str, object]]:
        return [
            {
                "extension_id": manifest.extension_id,
                "name": manifest.name,
                "version": manifest.version,
                "target_entity_types": manifest.target_entity_types,
                "save_policy": manifest.save_policy,
            }
            for manifest in sorted(self._extensions.values(), key=lambda item: item.extension_id)
        ]

    def validate_save_policy(self, extension_id: str, *, validation_gate_used: bool) -> AuthoringExtensionValidationReport:
        manifest = self._extensions.get(extension_id)
        if manifest is None:
            return AuthoringExtensionValidationReport(extension_id=extension_id, ok=False, errors=["Extension not registered"])
        if manifest.save_policy == "validation_gate_required" and not validation_gate_used:
            return AuthoringExtensionValidationReport(extension_id=extension_id, ok=False, errors=["AuthoringValidationGate is required"])
        return AuthoringExtensionValidationReport(extension_id=extension_id, ok=True)

