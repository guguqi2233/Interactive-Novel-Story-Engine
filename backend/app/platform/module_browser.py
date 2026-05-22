from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.platform.module_permissions import ModulePermissionSet, validate_module_permissions
from app.platform.package_manifest_v2 import EXECUTABLE_SUFFIXES, PackageManifestV2
from app.platform.security import contains_secret_text, redact_text, validate_relative_package_path


LOCAL_MODULE_DIRS = ("modules", "mods", "packages", "extensions", "gameplay_modules")
MANIFEST_NAMES = ("package_manifest_v2.json", "package_manifest_v2.yaml", "package_manifest_v2.yml", "package_v2_manifest.json", "gameplay_module.yaml", "gameplay_module.yml")


class ModuleBrowserSummary(BaseModel):
    package_id: str
    name: str
    version: str
    package_type: str
    permissions: dict[str, Any] = Field(default_factory=dict)
    validation_status: str = "unknown"
    compatibility_status: str = "unknown"
    permission_risk_level: str = "low"
    local_only: bool = True
    safe_path_hint: str = ""
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ModuleBrowserDetail(BaseModel):
    summary: ModuleBrowserSummary
    manifest: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    target_worlds: list[str] = Field(default_factory=list)
    target_project_modes: list[str] = Field(default_factory=list)


class ModuleScanReport(BaseModel):
    ok: bool
    modules: list[ModuleBrowserSummary] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    local_only: bool = True


class ModulePermissionSummary(BaseModel):
    package_id: str
    package_type: str
    permission_summary: dict[str, Any]
    dangerous_permissions: list[str] = Field(default_factory=list)
    risk_level: str = "low"


class ModuleBrowserService:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def scan(self) -> ModuleScanReport:
        modules: list[ModuleBrowserSummary] = []
        errors: list[str] = []
        for base in self._allowed_roots():
            if not base.exists():
                continue
            for manifest_path in self._manifest_paths(base):
                detail = self._detail_from_manifest(manifest_path)
                modules.append(detail.summary)
        modules.sort(key=lambda item: (item.package_type, item.package_id))
        return ModuleScanReport(ok=not errors, modules=modules, errors=errors)

    def list_modules(self) -> list[ModuleBrowserSummary]:
        return self.scan().modules

    def get_module(self, package_id: str) -> ModuleBrowserDetail:
        validate_relative_package_path(package_id)
        for manifest_path in self._all_manifest_paths():
            detail = self._detail_from_manifest(manifest_path)
            if detail.summary.package_id == package_id:
                return detail
        raise FileNotFoundError(package_id)

    def validate_module(self, package_id: str) -> dict[str, Any]:
        detail = self.get_module(package_id)
        return {"ok": detail.summary.validation_status == "valid", "errors": detail.summary.errors, "warnings": detail.summary.warnings}

    def permissions(self, package_id: str) -> ModulePermissionSummary:
        detail = self.get_module(package_id)
        permissions = ModulePermissionSet.model_validate(detail.manifest.get("permissions", {}))
        report = validate_module_permissions(permissions)
        return ModulePermissionSummary(
            package_id=detail.summary.package_id,
            package_type=detail.summary.package_type,
            permission_summary=permissions.safe_summary(),
            dangerous_permissions=report.dangerous_permissions,
            risk_level=report.risk_level.value,
        )

    def permissions_summary(self) -> list[ModulePermissionSummary]:
        return [self.permissions(module.package_id) for module in self.list_modules()]

    def compatibility(self, package_id: str) -> dict[str, Any]:
        detail = self.get_module(package_id)
        missing_dependencies = [dep for dep in detail.dependencies if dep not in {module.package_id for module in self.list_modules()}]
        return {
            "package_id": package_id,
            "status": "blocked" if missing_dependencies or detail.summary.errors else "compatible",
            "missing_dependencies": missing_dependencies,
            "conflicts": detail.conflicts,
            "target_worlds": detail.target_worlds,
            "target_project_modes": detail.target_project_modes,
        }

    def _allowed_roots(self) -> list[Path]:
        return [(self.project_root / name).resolve() for name in LOCAL_MODULE_DIRS]

    def _manifest_paths(self, base: Path) -> list[Path]:
        paths: list[Path] = []
        for name in MANIFEST_NAMES:
            paths.extend(base.rglob(name))
        return [path for path in paths if self._is_allowed(path)]

    def _all_manifest_paths(self) -> list[Path]:
        paths: list[Path] = []
        for root in self._allowed_roots():
            if root.exists():
                paths.extend(self._manifest_paths(root))
        return paths

    def _is_allowed(self, path: Path) -> bool:
        resolved = path.resolve()
        return any(resolved == root or root in resolved.parents for root in self._allowed_roots())

    def _detail_from_manifest(self, manifest_path: Path) -> ModuleBrowserDetail:
        errors: list[str] = []
        warnings: list[str] = []
        manifest_data: dict[str, Any] = {}
        try:
            manifest_data = _read_manifest(manifest_path)
        except Exception as exc:
            errors.append(f"manifest parse failed: {exc}")
        package_id = str(manifest_data.get("package_id") or manifest_data.get("module_id") or manifest_path.parent.name)
        package_type = str(manifest_data.get("package_type") or manifest_data.get("module_type") or "unknown")
        name = str(manifest_data.get("name") or package_id)
        version = str(manifest_data.get("version") or "0.0.0")
        permissions = manifest_data.get("permissions", {})
        permission_summary: dict[str, Any] = {}
        risk_level = "low"
        try:
            permission_set = ModulePermissionSet.model_validate(permissions if isinstance(permissions, dict) else {})
            permission_report = validate_module_permissions(permission_set)
            permission_summary = permission_set.safe_summary()
            risk_level = permission_report.risk_level.value
            errors.extend(permission_report.errors)
            warnings.extend(permission_report.warnings)
        except Exception as exc:
            errors.append(f"permission parse failed: {exc}")
        executable = _contains_executable(manifest_path.parent)
        if executable:
            errors.append("executable payload detected")
        if _contains_secret(manifest_path.parent):
            errors.append("secret-like content detected")
        try:
            if manifest_path.name.startswith("package_manifest_v2"):
                PackageManifestV2.model_validate(manifest_data)
        except Exception as exc:
            errors.append(f"manifest v2 validation failed: {redact_text(str(exc))}")
        summary = ModuleBrowserSummary(
            package_id=package_id,
            name=name,
            version=version,
            package_type=package_type,
            permissions=permission_summary,
            validation_status="valid" if not errors else "invalid",
            compatibility_status="unknown" if errors else "compatible",
            permission_risk_level=risk_level,
            safe_path_hint=manifest_path.parent.name,
            warnings=warnings,
            errors=errors,
        )
        return ModuleBrowserDetail(
            summary=summary,
            manifest=_safe_manifest(manifest_data),
            dependencies=[_dep_id(dep) for dep in manifest_data.get("dependencies", []) if _dep_id(dep)],
            conflicts=[str(item) for item in manifest_data.get("conflicts", [])],
            target_worlds=[str(item) for item in manifest_data.get("target_worlds", [])],
            target_project_modes=[str(item) for item in manifest_data.get("target_project_modes", [])],
        )


def _read_manifest(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    loaded = yaml.safe_load(text) if path.suffix.lower() in {".yaml", ".yml"} else json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("manifest must be an object")
    return loaded


def _dep_id(dep: Any) -> str:
    if isinstance(dep, str):
        return dep
    if isinstance(dep, dict):
        return str(dep.get("package_id") or "")
    return ""


def _contains_executable(root: Path) -> bool:
    for path in root.rglob("*"):
        if path.is_file() and any(path.name.lower().endswith(suffix) for suffix in EXECUTABLE_SUFFIXES):
            return True
    return False


def _contains_secret(root: Path) -> bool:
    for path in root.rglob("*"):
        if not path.is_file() or path.stat().st_size > 256_000:
            continue
        if any(part in {"node_modules", "dist", ".git"} for part in path.parts):
            continue
        try:
            validate_relative_package_path(path.relative_to(root).as_posix())
        except ValueError:
            return True
        try:
            if contains_secret_text(path.read_text(encoding="utf-8", errors="ignore")):
                return True
        except OSError:
            continue
    return False


def _safe_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    text = redact_text(json.dumps(manifest, ensure_ascii=False, default=str))
    return json.loads(text)
