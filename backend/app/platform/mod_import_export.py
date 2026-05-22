from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.platform.module_browser import ModuleBrowserService
from app.platform.package_manifest_v2 import EXECUTABLE_SUFFIXES, PackageManifestV2
from app.platform.rp_mature import MatureExportFilter, MatureExportPolicy, contains_forbidden_mature_policy_text
from app.platform.security import contains_secret_text, sha256_bytes, validate_relative_package_path


class ModImportDryRunReport(BaseModel):
    ok: bool
    package_id: str | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    writes_to_disk: bool = False
    migration_required: bool = False
    action_conflicts: list[str] = Field(default_factory=list)
    mature_package: bool = False


class ModImportApplyResult(BaseModel):
    ok: bool
    package_id: str
    installed_path: str
    enabled: bool = False
    warnings: list[str] = Field(default_factory=list)
    mature_package: bool = False


class ModExportResult(BaseModel):
    ok: bool
    package_id: str
    file_count: int
    checksums: dict[str, str] = Field(default_factory=dict)


class ModImportExportService:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def import_dry_run(self, package_bytes: bytes) -> ModImportDryRunReport:
        errors: list[str] = []
        warnings: list[str] = []
        package_id: str | None = None
        try:
            with zipfile.ZipFile(io.BytesIO(package_bytes)) as archive:
                names = archive.namelist()
                manifest_name = next((name for name in names if Path(name).name == "package_manifest_v2.json"), None)
                if not manifest_name:
                    errors.append("package_manifest_v2.json missing")
                manifest: PackageManifestV2 | None = None
                if manifest_name:
                    manifest_data = json.loads(archive.read(manifest_name).decode("utf-8"))
                    manifest = PackageManifestV2.model_validate(manifest_data)
                    package_id = manifest.package_id
                    if manifest.mature_policy.contains_mature_content or manifest.mature_policy.requires_mature_module:
                        warnings.append(f"mature_package_detected:{manifest.package_id}")
                for name in names:
                    try:
                        validate_relative_package_path(name)
                    except ValueError as exc:
                        errors.append(f"forbidden path: {exc}")
                        continue
                    if any(name.lower().endswith(suffix) for suffix in EXECUTABLE_SUFFIXES):
                        errors.append(f"executable payload blocked: {name}")
                        continue
                    data = archive.read(name)
                    if _file_contains_forbidden_secret(data.decode("utf-8", errors="ignore"), package_type=manifest.package_type.value if manifest else ""):
                        errors.append(f"secret-like content blocked: {name}")
                    if contains_forbidden_mature_policy_text(data.decode("utf-8", errors="ignore")):
                        errors.append(f"unsafe mature policy content blocked: {name}")
                    _collect_v27_module_warnings(name, data.decode("utf-8", errors="ignore"), warnings, errors)
                if manifest_name:
                    existing = {module.package_id for module in ModuleBrowserService(self.project_root).list_modules()}
                    if package_id in existing:
                        errors.append(f"duplicate package_id: {package_id}")
                    for path, expected in manifest.checksums.items():
                        try:
                            safe_path = validate_relative_package_path(path)
                        except ValueError as exc:
                            errors.append(f"forbidden checksum path: {exc}")
                            continue
                        try:
                            actual = f"sha256:{sha256_bytes(archive.read(safe_path))}"
                        except KeyError:
                            errors.append(f"checksum file missing: {path}")
                            continue
                        if actual != expected:
                            errors.append(f"checksum mismatch: {path}")
        except Exception as exc:
            errors.append(str(exc))
        action_conflicts = sorted({warning.removeprefix("action conflict: ") for warning in warnings if warning.startswith("action conflict: ")})
        return ModImportDryRunReport(
            ok=not errors,
            package_id=package_id,
            errors=errors,
            warnings=warnings,
            migration_required=any("migration_required" in warning for warning in warnings),
            action_conflicts=action_conflicts,
            mature_package=any(warning.startswith("mature_package_detected:") for warning in warnings),
        )

    def import_apply(self, package_bytes: bytes, *, confirm: bool) -> ModImportApplyResult:
        dry_run = self.import_dry_run(package_bytes)
        if not confirm:
            raise ValueError("explicit confirmation is required for module import")
        if not dry_run.ok or not dry_run.package_id:
            raise ValueError("; ".join(dry_run.errors) or "import dry-run failed")
        target = self.project_root / "modules" / "imported" / dry_run.package_id
        target.mkdir(parents=True, exist_ok=False)
        with zipfile.ZipFile(io.BytesIO(package_bytes)) as archive:
            for member in archive.namelist():
                safe_member = validate_relative_package_path(member)
                destination = (target / safe_member).resolve()
                if target.resolve() not in destination.parents and target.resolve() != destination:
                    raise ValueError("zip slip rejected")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(member))
        return ModImportApplyResult(ok=True, package_id=dry_run.package_id, installed_path=target.name, warnings=dry_run.warnings, mature_package=dry_run.mature_package, enabled=False)

    def disable_module_preserve_state(self, package_id: str) -> dict[str, Any]:
        return {"package_id": package_id, "enabled": False, "state_preserved": True}

    def remove_module_state(self, package_id: str, *, confirm_destructive: bool = False) -> dict[str, Any]:
        if not confirm_destructive:
            raise ValueError("destructive module state removal requires explicit confirmation")
        return {"package_id": package_id, "removed": True}

    def export_package(self, package_id: str, mature_export_policy: MatureExportPolicy | None = None) -> ModExportResult:
        detail = ModuleBrowserService(self.project_root).get_module(package_id)
        package_dir = self._package_dir(package_id)
        export_filter = MatureExportFilter()
        policy = mature_export_policy or MatureExportPolicy()
        checksums: dict[str, str] = {}
        file_count = 0
        for path in package_dir.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(package_dir).as_posix()
            validate_relative_package_path(relative)
            if any(relative.lower().endswith(suffix) for suffix in EXECUTABLE_SUFFIXES):
                raise ValueError(f"executable payload blocked: {relative}")
            data = path.read_bytes()
            if _file_contains_forbidden_secret(data.decode("utf-8", errors="ignore"), package_type=detail.summary.package_type):
                raise ValueError(f"secret-like content blocked: {relative}")
            text = data.decode("utf-8", errors="ignore")
            if ("mature_only" in text.lower() or "contains_mature_content" in text.lower()) and not policy.include_mature_content:
                continue
            filtered = export_filter.filter_text(text, policy) if _looks_text(relative, data) else text
            if filtered is None:
                raise ValueError(f"secret-like content blocked: {relative}")
            encoded = filtered.encode("utf-8") if _looks_text(relative, data) else data
            checksums[relative] = f"sha256:{sha256_bytes(encoded)}"
            file_count += 1
        return ModExportResult(ok=True, package_id=detail.summary.package_id, file_count=file_count, checksums=checksums)

    def _package_dir(self, package_id: str) -> Path:
        detail = ModuleBrowserService(self.project_root).get_module(package_id)
        for root_name in ("modules", "mods", "packages", "extensions", "gameplay_modules"):
            candidate = self.project_root / root_name / detail.summary.safe_path_hint
            if candidate.exists():
                return candidate.resolve()
            for manifest in (self.project_root / root_name).rglob("package_manifest_v2.json"):
                try:
                    data = json.loads(manifest.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if data.get("package_id") == package_id:
                    return manifest.parent.resolve()
        raise FileNotFoundError(package_id)


def _file_contains_forbidden_secret(text: str, *, package_type: str) -> bool:
    if package_type == "provider_profile_pack":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return contains_secret_text(text)
        return _provider_payload_has_raw_secret(payload)
    return contains_secret_text(text)


def _provider_payload_has_raw_secret(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).lower()
            if lowered in {"api_key", "authorization", "x-api-key"}:
                return True
            if lowered == "headers" and isinstance(value, dict):
                if any("auth" in str(header).lower() or "key" in str(header).lower() for header in value):
                    return True
            if _provider_payload_has_raw_secret(value):
                return True
    if isinstance(payload, list):
        return any(_provider_payload_has_raw_secret(item) for item in payload)
    if isinstance(payload, str):
        return "sk-" in payload and not any(marker in payload for marker in ("sk-test", "sk-fake", "sk-redacted", "sk-placeholder", "sk-example"))
    return False


def _looks_text(path: str, data: bytes) -> bool:
    return Path(path).suffix.lower() in {".json", ".yaml", ".yml", ".txt", ".md", ".csv"} or b"\x00" not in data[:256]


def _collect_v27_module_warnings(name: str, text: str, warnings: list[str], errors: list[str]) -> None:
    lowered_name = name.lower()
    if lowered_name.endswith(("module_state.json", "state_extension.json", "state_schema.json")):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            errors.append(f"invalid module state schema json: {name}")
            return
        namespace = payload.get("namespace") if isinstance(payload, dict) else None
        module_id = payload.get("module_id") if isinstance(payload, dict) else None
        if module_id and namespace != f"state.modules.{module_id}":
            errors.append(f"module state schema must use state.modules namespace: {name}")
        if isinstance(payload, dict) and payload.get("migration_required"):
            warnings.append(f"migration_required: {module_id or name}")
    if lowered_name.endswith(("actions.json", "action_mod.json")):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return
        actions = payload.get("actions") if isinstance(payload, dict) else None
        if isinstance(actions, list):
            seen: set[str] = set()
            for action in actions:
                action_id = action.get("id") or action.get("action_id") if isinstance(action, dict) else None
                if action_id in seen:
                    warnings.append(f"action conflict: {action_id}")
                if action_id:
                    seen.add(action_id)
