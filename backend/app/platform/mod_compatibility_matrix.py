from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.platform.module_browser import ModuleBrowserService


class ModCompatibilityEntry(BaseModel):
    package_id: str
    compatible: bool
    status: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    load_order_index: int | None = None


class ModCompatibilityMatrix(BaseModel):
    ok: bool
    entries: list[ModCompatibilityEntry] = Field(default_factory=list)
    conflicts_summary: list[str] = Field(default_factory=list)
    load_order: list[str] = Field(default_factory=list)


class ModSelectionCheckRequest(BaseModel):
    package_ids: list[str] = Field(default_factory=list)


class ModSelectionCheckResult(BaseModel):
    ok: bool
    matrix: ModCompatibilityMatrix
    selected_package_ids: list[str] = Field(default_factory=list)


class ModCompatibilityService:
    def __init__(self, browser: ModuleBrowserService) -> None:
        self.browser = browser

    def build_matrix(self, selected_package_ids: list[str] | None = None) -> ModCompatibilityMatrix:
        modules = self.browser.list_modules()
        selected = set(selected_package_ids or [module.package_id for module in modules])
        available = {module.package_id for module in modules}
        entries: list[ModCompatibilityEntry] = []
        conflicts: list[str] = []
        for module in modules:
            if module.package_id not in selected:
                continue
            detail = self.browser.get_module(module.package_id)
            errors = list(module.errors)
            warnings = list(module.warnings)
            for dep in detail.dependencies:
                if dep not in available:
                    errors.append(f"missing dependency: {dep}")
            for conflict in detail.conflicts:
                if conflict in selected:
                    errors.append(f"conflicts with selected package: {conflict}")
                    conflicts.append(f"{module.package_id} conflicts with {conflict}")
            if module.permission_risk_level == "blocked":
                errors.append("dangerous permission blocked")
            entries.append(ModCompatibilityEntry(package_id=module.package_id, compatible=not errors, status="compatible" if not errors else "blocked", errors=errors, warnings=warnings))
        load_order = _deterministic_load_order(entries, {entry.package_id: self.browser.get_module(entry.package_id).dependencies for entry in entries})
        for index, package_id in enumerate(load_order):
            for entry in entries:
                if entry.package_id == package_id:
                    entry.load_order_index = index
        return ModCompatibilityMatrix(ok=all(entry.compatible for entry in entries), entries=entries, conflicts_summary=sorted(set(conflicts)), load_order=load_order)

    def check_selection(self, request: ModSelectionCheckRequest) -> ModSelectionCheckResult:
        matrix = self.build_matrix(request.package_ids)
        return ModSelectionCheckResult(ok=matrix.ok, matrix=matrix, selected_package_ids=request.package_ids)


def _deterministic_load_order(entries: list[ModCompatibilityEntry], deps: dict[str, list[str]]) -> list[str]:
    pending = sorted(entry.package_id for entry in entries)
    resolved: list[str] = []
    while pending:
        progressed = False
        for package_id in list(pending):
            if all(dep in resolved or dep not in pending for dep in deps.get(package_id, [])):
                resolved.append(package_id)
                pending.remove(package_id)
                progressed = True
        if not progressed:
            resolved.extend(sorted(pending))
            break
    return resolved
