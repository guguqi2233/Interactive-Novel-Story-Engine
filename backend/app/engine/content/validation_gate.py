from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Any

from pydantic import BaseModel, Field

from app.engine.content.validator import ValidationReport, ValidationSeverity, validate_world_pack


class AuthoringOperationType(StrEnum):
    SAVE = "save"
    MERGE = "merge"
    IMPORT = "import"
    EXPORT = "export"
    APPLY_TEMPLATE = "apply_template"
    APPLY_PACK = "apply_pack"


class AuthoringValidationGateRequest(BaseModel):
    world_id: str
    operation_type: AuthoringOperationType
    draft_content: dict[str, str] = Field(default_factory=dict)
    affected_files: list[str] = Field(default_factory=list)
    confirm_warnings: bool = False
    debug_override_hidden_risk: bool = False
    validation_report: ValidationReport | None = None


class AuthoringValidationGateResult(BaseModel):
    validation_report: ValidationReport
    quality_warnings: list[str] = Field(default_factory=list)
    migration_impact: list[str] = Field(default_factory=list)
    hidden_leak_risks: list[str] = Field(default_factory=list)
    allowed_to_save: bool = False
    confirmation_required: bool = False


class AuthoringValidationGate:
    """Shared authoring save gate for local content writes and package apply paths."""

    def __init__(self, worlds_root: str | Path = "worlds", *, max_quality_warnings: int = 50) -> None:
        self.worlds_root = Path(worlds_root)
        self.max_quality_warnings = max_quality_warnings

    def evaluate(self, request: AuthoringValidationGateRequest) -> AuthoringValidationGateResult:
        validation = request.validation_report or self._validate_draft(request.world_id, request.draft_content)
        quality_warnings = _quality_warnings(validation)[: self.max_quality_warnings]
        hidden_risks = _hidden_leak_risks(validation)
        migration_impact = self._migration_impact(request)
        confirmation_required = bool(validation.warnings or quality_warnings) and not request.confirm_warnings
        blocked_by_hidden = bool(hidden_risks) and not request.debug_override_hidden_risk
        allowed = validation.ok and not blocked_by_hidden and not confirmation_required
        if blocked_by_hidden:
            _append_gate_error(validation, hidden_risks)
        return AuthoringValidationGateResult(
            validation_report=validation,
            quality_warnings=quality_warnings,
            migration_impact=migration_impact,
            hidden_leak_risks=hidden_risks,
            allowed_to_save=allowed,
            confirmation_required=confirmation_required,
        )

    def _validate_draft(self, world_id: str, draft_content: dict[str, str]) -> ValidationReport:
        if not draft_content:
            return validate_world_pack(world_id, worlds_root=self.worlds_root)
        with TemporaryDirectory() as temp_dir:
            temp_worlds = Path(temp_dir) / "worlds"
            source = self.worlds_root / world_id
            draft_world = temp_worlds / world_id
            copytree(source, draft_world)
            for file_name, content in draft_content.items():
                (draft_world / file_name).write_text(content, encoding="utf-8")
            return validate_world_pack(world_id, worlds_root=temp_worlds)

    def _migration_impact(self, request: AuthoringValidationGateRequest) -> list[str]:
        impacts: list[str] = []
        for file_name in request.affected_files:
            if file_name in {"locations.yaml", "npcs.yaml", "items.yaml", "quests.yaml", "facts.yaml", "factions.yaml"}:
                impacts.append(f"{file_name}: review deleted or renamed ids before {request.operation_type.value}")
        return impacts if request.operation_type in {AuthoringOperationType.MERGE, AuthoringOperationType.IMPORT, AuthoringOperationType.APPLY_PACK} else []


def _quality_warnings(report: ValidationReport) -> list[str]:
    return [f"{issue.file}:{issue.path}:{issue.code}" for issue in report.warnings]


def _hidden_leak_risks(report: ValidationReport) -> list[str]:
    risks: list[str] = []
    for issue in [*report.errors, *report.warnings]:
        haystack = f"{issue.code} {issue.message}".lower()
        if "leak" in haystack or "hidden_fact" in haystack or "reveals_hidden" in haystack:
            risks.append(f"{issue.file}:{issue.path}:{issue.code}")
    return sorted(set(risks))


def _append_gate_error(report: ValidationReport, risks: list[str]) -> None:
    report.add(
        ValidationSeverity.ERROR,
        "authoring.validation_gate",
        f"Authoring Validation Gate blocked hidden leak risk: {', '.join(risks)}",
        code="authoring_gate_hidden_leak_blocked",
    )
