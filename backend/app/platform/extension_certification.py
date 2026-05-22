from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from app.platform.mod_compatibility_matrix import ModCompatibilityService
from app.platform.module_browser import ModuleBrowserService


class ExtensionCertificationLevel(StrEnum):
    SAFE_CONTENT = "safe_content"
    SAFE_STYLE = "safe_style"
    VERIFIED_ACTION = "verified_action"
    EXPERIMENTAL_RULE_MODULE = "experimental_rule_module"
    UNSAFE_BLOCKED = "unsafe_blocked"


class ExtensionCertificationReport(BaseModel):
    package_id: str
    level: ExtensionCertificationLevel
    ok: bool
    reasons: list[str] = Field(default_factory=list)
    safe_summary: dict[str, str] = Field(default_factory=dict)


class CertificationService:
    def __init__(self, browser: ModuleBrowserService) -> None:
        self.browser = browser

    def certify_package(self, package_id: str) -> ExtensionCertificationReport:
        detail = self.browser.get_module(package_id)
        matrix = ModCompatibilityService(self.browser).build_matrix([package_id])
        reasons = [*detail.summary.errors, *matrix.conflicts_summary]
        if detail.summary.validation_status != "valid" or not matrix.ok:
            level = ExtensionCertificationLevel.UNSAFE_BLOCKED
        elif detail.summary.package_type == "narrative_style_mod":
            level = ExtensionCertificationLevel.SAFE_STYLE
        elif detail.summary.package_type == "action_mod":
            level = ExtensionCertificationLevel.VERIFIED_ACTION
            reasons.append("verified_action assumes included action tests pass under the local harness")
        elif detail.summary.package_type == "rule_module":
            level = ExtensionCertificationLevel.EXPERIMENTAL_RULE_MODULE
            reasons.append("rule modules are contract-only in v2.6")
        else:
            level = ExtensionCertificationLevel.SAFE_CONTENT
        return ExtensionCertificationReport(package_id=package_id, level=level, ok=level != ExtensionCertificationLevel.UNSAFE_BLOCKED, reasons=reasons, safe_summary={"package_type": detail.summary.package_type, "local_only": "true"})

    def certify_package_set(self, package_ids: list[str]) -> list[ExtensionCertificationReport]:
        return [self.certify_package(package_id) for package_id in package_ids]


def certify_package_path(package_path: Path) -> ExtensionCertificationReport:
    browser = ModuleBrowserService(package_path.parent)
    return CertificationService(browser).certify_package(package_path.name)
