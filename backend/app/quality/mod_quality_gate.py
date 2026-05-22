from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from app.platform.extension_certification import CertificationService
from app.platform.mod_compatibility_matrix import ModCompatibilityService
from app.platform.module_browser import ModuleBrowserService


class ModQualityGateConfig(BaseModel):
    require_action_tests: bool = True
    fail_on_warnings: bool = False


class ModQualityGateResult(BaseModel):
    ok: bool
    package_id: str
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    certification_level: str = "unknown"
    compatibility_status: str = "unknown"

    def safe_summary(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "package_id": self.package_id,
            "blocker_count": len(self.blockers),
            "warning_count": len(self.warnings),
            "certification_level": self.certification_level,
            "compatibility_status": self.compatibility_status,
        }


def run_mod_quality_gate(project_root: Path, package_id: str, config: ModQualityGateConfig | None = None) -> ModQualityGateResult:
    config = config or ModQualityGateConfig()
    browser = ModuleBrowserService(project_root)
    detail = browser.get_module(package_id)
    matrix = ModCompatibilityService(browser).build_matrix([package_id])
    cert = CertificationService(browser).certify_package(package_id)
    blockers = [*detail.summary.errors]
    warnings = [*detail.summary.warnings, *cert.reasons]
    for entry in matrix.entries:
        blockers.extend(entry.errors)
        warnings.extend(entry.warnings)
    if config.require_action_tests and detail.summary.package_type == "action_mod":
        warnings.append("action mod tests should be included and run before release")
    ok = not blockers and (not warnings or not config.fail_on_warnings) and cert.ok
    return ModQualityGateResult(
        ok=ok,
        package_id=package_id,
        blockers=blockers,
        warnings=warnings,
        certification_level=cert.level.value,
        compatibility_status="compatible" if matrix.ok else "blocked",
    )
