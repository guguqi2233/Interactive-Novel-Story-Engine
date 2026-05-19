from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.character_pack_builder import CharacterPack
from app.engine.content.mod_loader import FORBIDDEN_CODE_SUFFIXES, ModLoader
from app.engine.content.scenario_templates import ScenarioTemplateRenderer
from app.engine.content.script_package_builder import SECRET_TOKENS, SENSITIVE_FILE_NAMES, SENSITIVE_SUFFIXES
from app.engine.content.validator import ValidationIssue, ValidationReport, ValidationSeverity, validate_world_pack


class ContentBatchValidationError(ValueError):
    """Raised when a batch validation request is unsafe."""


class BatchPackageType(StrEnum):
    WORLD = "world"
    CHARACTER_PACK = "character_pack"
    QUEST_PACK = "quest_pack"
    TEMPLATE_PACK = "template_pack"
    MOD_PACKAGE = "mod_package"
    SCRIPT_PACKAGE = "script_package"


class ContentBatchValidationTarget(BaseModel):
    package_type: BatchPackageType
    id: str
    path: str | None = None


class ContentBatchValidationRequest(BaseModel):
    targets: list[ContentBatchValidationTarget] = Field(default_factory=list)
    worlds_root: str = "worlds"
    packages_root: str = "packages"
    templates_root: str = "templates"
    mods_root: str = "mods"
    normal_report: bool = True


class ContentBatchPackageReport(BaseModel):
    package_type: BatchPackageType
    id: str
    status: str
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    suggestions: list[ValidationIssue] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class ContentBatchValidationReport(BaseModel):
    total: int = 0
    passed: int = 0
    warning: int = 0
    failed: int = 0
    blockers: list[str] = Field(default_factory=list)
    per_package_report: list[ContentBatchPackageReport] = Field(default_factory=list)
    aggregate_issues: list[ValidationIssue] = Field(default_factory=list)


class ContentBatchValidator:
    def __init__(
        self,
        *,
        worlds_root: str | Path = "worlds",
        packages_root: str | Path = "packages",
        templates_root: str | Path = "templates",
        mods_root: str | Path = "mods",
    ) -> None:
        self.worlds_root = Path(worlds_root).resolve()
        self.packages_root = Path(packages_root).resolve()
        self.templates_root = Path(templates_root).resolve()
        self.mods_root = Path(mods_root).resolve()

    def validate(self, request: ContentBatchValidationRequest) -> ContentBatchValidationReport:
        report = ContentBatchValidationReport(total=len(request.targets))
        for target in request.targets:
            package_report = self._validate_target(target, normal_report=request.normal_report)
            report.per_package_report.append(package_report)
            report.blockers.extend(package_report.blockers)
            report.aggregate_issues.extend(package_report.errors)
            report.aggregate_issues.extend(package_report.warnings)
            if package_report.status == "failed":
                report.failed += 1
            elif package_report.status == "warning":
                report.warning += 1
            else:
                report.passed += 1
        report.aggregate_issues = [_redact_issue(issue) for issue in report.aggregate_issues]
        report.blockers = [_redact_text(blocker) for blocker in report.blockers]
        return report

    def _validate_target(self, target: ContentBatchValidationTarget, *, normal_report: bool) -> ContentBatchPackageReport:
        try:
            validation = self._dispatch(target)
        except Exception as exc:
            validation = ValidationReport(world_id=target.id)
            validation.add(
                ValidationSeverity.ERROR,
                f"batch.{target.package_type.value}.{target.id}",
                str(exc),
                code="batch_validation_failed",
            )
        errors = [_redact_issue(issue) for issue in validation.errors] if normal_report else validation.errors
        warnings = [_redact_issue(issue) for issue in validation.warnings] if normal_report else validation.warnings
        suggestions = [_redact_issue(issue) for issue in validation.suggestions] if normal_report else validation.suggestions
        status = "failed" if errors else "warning" if warnings else "passed"
        return ContentBatchPackageReport(
            package_type=target.package_type,
            id=target.id,
            status=status,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            blockers=[issue.message for issue in errors],
        )

    def _dispatch(self, target: ContentBatchValidationTarget) -> ValidationReport:
        if target.package_type == BatchPackageType.WORLD:
            return validate_world_pack(_safe_id(target.id), worlds_root=self.worlds_root)
        if target.package_type == BatchPackageType.MOD_PACKAGE:
            return ModLoader(self.mods_root).validate_mod(_safe_id(target.id))
        if target.package_type == BatchPackageType.TEMPLATE_PACK:
            return self._validate_template_pack(target)
        if target.package_type == BatchPackageType.CHARACTER_PACK:
            return self._validate_character_pack(target)
        if target.package_type == BatchPackageType.QUEST_PACK:
            return self._validate_yaml_pack(target, "quest_pack", required_keys={"quests"})
        if target.package_type == BatchPackageType.SCRIPT_PACKAGE:
            return self._validate_script_package(target)
        raise ContentBatchValidationError(f"Unsupported package type: {target.package_type}")

    def _validate_template_pack(self, target: ContentBatchValidationTarget) -> ValidationReport:
        report = ValidationReport(world_id=target.id)
        try:
            ScenarioTemplateRenderer(self.templates_root, self.worlds_root).list_templates()
        except Exception as exc:
            report.add(ValidationSeverity.ERROR, "templates", str(exc), code="batch_template_pack_invalid")
        return report

    def _validate_character_pack(self, target: ContentBatchValidationTarget) -> ValidationReport:
        report = ValidationReport(world_id=target.id)
        path = self._safe_package_path(target)
        data = _read_yaml_or_json(path)
        try:
            CharacterPack.model_validate(data)
        except Exception as exc:
            report.add(ValidationSeverity.ERROR, str(path.name), str(exc), code="batch_character_pack_invalid")
        return report

    def _validate_yaml_pack(
        self,
        target: ContentBatchValidationTarget,
        pack_label: str,
        *,
        required_keys: set[str],
    ) -> ValidationReport:
        report = ValidationReport(world_id=target.id)
        path = self._safe_package_path(target)
        data = _read_yaml_or_json(path)
        if not isinstance(data, dict):
            report.add(ValidationSeverity.ERROR, path.name, f"{pack_label} must be a mapping.", code="batch_package_not_mapping")
            return report
        for key in sorted(required_keys):
            if key not in data:
                report.add(ValidationSeverity.ERROR, path.name, f"{pack_label} missing required key: {key}", code="batch_package_missing_key")
        return report

    def _validate_script_package(self, target: ContentBatchValidationTarget) -> ValidationReport:
        report = ValidationReport(world_id=target.id)
        path = self._safe_package_path(target)
        if path.is_file():
            self._validate_script_package_file(path, report)
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_file():
                    self._validate_script_package_file(child, report)
        return report

    def _validate_script_package_file(self, path: Path, report: ValidationReport) -> None:
        name = path.name.lower()
        suffix = path.suffix.lower()
        if suffix in FORBIDDEN_CODE_SUFFIXES:
            report.add(ValidationSeverity.ERROR, path.name, "Script package contains executable code.", code="batch_script_executable_rejected")
        if name in SENSITIVE_FILE_NAMES or suffix in SENSITIVE_SUFFIXES:
            report.add(
                ValidationSeverity.ERROR,
                path.name,
                "Script package contains sensitive config, database, or log files.",
                code="batch_script_sensitive_file_rejected",
            )
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return
        lowered = text.lower()
        if any(token.lower() in lowered for token in SECRET_TOKENS):
            report.add(
                ValidationSeverity.ERROR,
                path.name,
                "Script package contains API key or sensitive configuration text.",
                code="batch_script_secret_rejected",
            )

    def _safe_package_path(self, target: ContentBatchValidationTarget) -> Path:
        raw = target.path or target.id
        if any(token in raw.lower() for token in (".env", "api_key", "apikey")):
            raise ContentBatchValidationError("Sensitive config paths are not allowed in batch validation.")
        candidate = (self.packages_root / raw).resolve()
        if self.packages_root != candidate and self.packages_root not in candidate.parents:
            raise ContentBatchValidationError("Package path escapes package root.")
        if not candidate.exists():
            raise ContentBatchValidationError(f"Package path not found: {raw}")
        return candidate


def validate_content_batch(request: ContentBatchValidationRequest) -> ContentBatchValidationReport:
    validator = ContentBatchValidator(
        worlds_root=request.worlds_root,
        packages_root=request.packages_root,
        templates_root=request.templates_root,
        mods_root=request.mods_root,
    )
    return validator.validate(request)


def _safe_id(value: str) -> str:
    if not value or any(char in value for char in "\\/.:"):
        raise ContentBatchValidationError(f"Invalid package id: {value}")
    return value


def _read_yaml_or_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        import json

        return json.loads(text)
    return yaml.safe_load(text) or {}


def _redact_issue(issue: ValidationIssue) -> ValidationIssue:
    payload = issue.model_dump(mode="json")
    payload["message"] = _redact_text(str(payload.get("message", "")))
    payload["suggestion"] = _redact_text(str(payload.get("suggestion", ""))) if payload.get("suggestion") else None
    return ValidationIssue.model_validate(payload)


def _redact_text(value: str) -> str:
    redacted = value
    for token in ("hidden", "secret", "private_self_summary", "api_key", "apikey", "sk-"):
        redacted = redacted.replace(token, "[redacted]")
        redacted = redacted.replace(token.upper(), "[redacted]")
    return redacted
