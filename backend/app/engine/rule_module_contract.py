from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class RuleModulePermissions(BaseModel):
    can_add_actions: bool = False
    can_add_state_schema: bool = False
    can_add_validation_rules: bool = False
    can_add_tick_rules: bool = False
    can_call_llm: bool = False
    can_access_filesystem: bool = False
    can_access_network: bool = False
    can_execute_code: bool = False


class RuleModuleValidationReport(BaseModel):
    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RuleModuleManifest(BaseModel):
    module_id: str
    name: str
    version: str
    description: str = ""
    required_engine_version: str = "2.6"
    provided_systems: list[str] = Field(default_factory=list)
    required_state_schema_extensions: list[dict[str, Any]] = Field(default_factory=list)
    actions_provided: list[str] = Field(default_factory=list)
    rules_provided: list[str] = Field(default_factory=list)
    permissions: RuleModulePermissions = Field(default_factory=RuleModulePermissions)
    compatibility_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_permissions(self) -> "RuleModuleManifest":
        report = validate_rule_module_manifest(self)
        if report.errors:
            raise ValueError("; ".join(report.errors))
        return self

    def safe_summary(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "name": self.name,
            "version": self.version,
            "provided_systems": self.provided_systems,
            "actions_provided": self.actions_provided,
            "rules_provided": self.rules_provided,
            "experimental": True,
        }


def validate_rule_module_manifest(manifest: RuleModuleManifest) -> RuleModuleValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    if manifest.permissions.can_execute_code:
        errors.append("rule modules cannot execute code in v2.6")
    if manifest.permissions.can_call_llm:
        errors.append("rule modules cannot call LLMs in v2.6")
    if manifest.permissions.can_access_filesystem:
        errors.append("rule modules cannot access filesystem in v2.6")
    if manifest.permissions.can_access_network:
        errors.append("rule modules cannot access network in v2.6")
    if manifest.required_state_schema_extensions:
        warnings.append("state schema extension requires migration review")
    for action_id in manifest.actions_provided:
        if not action_id or "/" in action_id or "\\" in action_id or ".." in action_id:
            errors.append(f"unsafe action ref: {action_id}")
    return RuleModuleValidationReport(ok=not errors, errors=errors, warnings=warnings)
