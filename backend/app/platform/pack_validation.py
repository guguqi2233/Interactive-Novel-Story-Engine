from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field

from app.platform.package_manifest_v2 import EXECUTABLE_SUFFIXES, PackageManifestV2, PackageTypeV2
from app.platform.security import contains_secret_text, redact_text


HIDDEN_LEAK_PATTERNS = (
    re.compile(r"hidden[_ -]?fact", re.IGNORECASE),
    re.compile(r"npc[_ -]?secret", re.IGNORECASE),
    re.compile(r"debug[_ -]?memory", re.IGNORECASE),
    re.compile(r"raw[_ -]?state[_ -]?delta", re.IGNORECASE),
)


class PackValidationReport(BaseModel):
    ok: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    safe_summary: dict[str, Any] = Field(default_factory=dict)

    def add_error(self, message: str) -> None:
        self.ok = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


def validate_manifest_type(manifest: PackageManifestV2, expected: PackageTypeV2, report: PackValidationReport) -> None:
    if manifest.package_type != expected:
        report.add_error(f"manifest package_type must be {expected.value}")


def validate_no_secrets(payload: Any, report: PackValidationReport) -> None:
    text = json.dumps(payload, ensure_ascii=False, default=str)
    if contains_secret_text(text):
        report.add_error("package contains secret-like text")


def validate_no_executables(manifest: PackageManifestV2, report: PackValidationReport) -> None:
    paths = [entry.path for entry in manifest.included_files] + [entry.path for entry in manifest.entry_points]
    for path in paths:
        if any(path.lower().endswith(suffix) for suffix in EXECUTABLE_SUFFIXES):
            report.add_error(f"executable payload is blocked: {path}")


def validate_no_hidden_leak(payload: Any, report: PackValidationReport, *, severity: str = "error") -> None:
    text = json.dumps(payload, ensure_ascii=False, default=str)
    for pattern in HIDDEN_LEAK_PATTERNS:
        if pattern.search(text):
            if severity == "warning":
                report.add_warning(f"hidden/debug leak marker requires review: {pattern.pattern}")
            else:
                report.add_error(f"hidden/debug leak marker is blocked: {pattern.pattern}")


def collect_ids(items: list[dict[str, Any]], *keys: str) -> list[str]:
    ids: list[str] = []
    for item in items:
        for key in keys:
            value = item.get(key)
            if isinstance(value, str) and value:
                ids.append(value)
                break
    return ids


def validate_unique(ids: list[str], label: str, report: PackValidationReport) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            report.add_error(f"duplicate {label}: {item_id}")
        seen.add(item_id)


def safe_payload_summary(payload: Any) -> str:
    return redact_text(json.dumps(payload, ensure_ascii=False, default=str)[:1000])
