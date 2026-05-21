from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from app.db.migrations import CURRENT_ENGINE_VERSION
from app.platform.security import safe_identifier


PLUGIN_CONTRACT_VERSION = "2"


class PluginPermissions(BaseModel):
    execute_code: bool = False
    access_network: bool = False
    access_filesystem: bool = False
    call_llm: bool = False
    modify_game_state_directly: bool = False


class PluginManifest(BaseModel):
    plugin_id: str
    name: str
    version: str
    contract_version: str = PLUGIN_CONTRACT_VERSION
    plugin_type: Literal["module_bundle", "content_bundle", "authoring_extension", "hybrid"] = "hybrid"
    engine_version_min: str = CURRENT_ENGINE_VERSION
    dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    included_modules: list[str] = Field(default_factory=list)
    included_content_packs: list[str] = Field(default_factory=list)
    included_prompt_profiles: list[str] = Field(default_factory=list)
    included_authoring_extensions: list[str] = Field(default_factory=list)
    included_templates: list[str] = Field(default_factory=list)
    included_script_packages: list[str] = Field(default_factory=list)
    permissions: PluginPermissions = Field(default_factory=PluginPermissions)
    checksums: dict[str, str] = Field(default_factory=dict)
    redaction_policy: str = "safe_no_secrets"

    @field_validator("plugin_id")
    @classmethod
    def validate_plugin_id(cls, value: str) -> str:
        if not safe_identifier(value):
            raise ValueError("Unsafe plugin_id")
        return value

    @model_validator(mode="after")
    def validate_contract(self) -> "PluginManifest":
        if self.contract_version != PLUGIN_CONTRACT_VERSION:
            raise ValueError("Unsupported plugin contract_version")
        unsafe = [name for name, value in self.permissions.model_dump().items() if value]
        if unsafe:
            raise ValueError(f"Unsafe plugin permissions: {', '.join(unsafe)}")
        return self


class PluginValidationReport(BaseModel):
    plugin_id: str
    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PluginSummary(BaseModel):
    plugin_id: str
    name: str
    version: str
    plugin_type: str
    included_modules: list[str] = Field(default_factory=list)
    included_content_packs: list[str] = Field(default_factory=list)
    safe_permissions: PluginPermissions = Field(default_factory=PluginPermissions)
    status: str = "discovered"


class PluginLoader:
    def __init__(self, plugins_root: str | Path = "plugins") -> None:
        self.plugins_root = Path(plugins_root)

    def discover(self) -> list[PluginManifest]:
        if not self.plugins_root.exists():
            return []
        manifests: list[PluginManifest] = []
        for path in sorted(self.plugins_root.iterdir(), key=lambda item: item.name):
            manifest_path = path / "plugin.yaml"
            if path.is_dir() and manifest_path.exists():
                manifests.append(self.load_manifest_only(manifest_path))
        return manifests

    def load_manifest_only(self, manifest_path: str | Path) -> PluginManifest:
        resolved = Path(manifest_path).resolve()
        root = self.plugins_root.resolve()
        if root != resolved and root not in resolved.parents:
            raise ValueError("Plugin manifest escapes plugin root")
        data = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError("Plugin manifest must be a mapping")
        return PluginManifest.model_validate(data)


class PluginRegistry:
    def __init__(self, loader: PluginLoader | None = None) -> None:
        self.loader = loader or PluginLoader()

    def list_plugins(self) -> list[PluginSummary]:
        summaries: list[PluginSummary] = []
        for manifest in self.loader.discover():
            summaries.append(
                PluginSummary(
                    plugin_id=manifest.plugin_id,
                    name=manifest.name,
                    version=manifest.version,
                    plugin_type=manifest.plugin_type,
                    included_modules=manifest.included_modules,
                    included_content_packs=manifest.included_content_packs,
                    safe_permissions=manifest.permissions,
                    status="validated",
                )
            )
        return summaries

    def validate_plugin(self, manifest: PluginManifest) -> PluginValidationReport:
        return PluginValidationReport(plugin_id=manifest.plugin_id, ok=True)

