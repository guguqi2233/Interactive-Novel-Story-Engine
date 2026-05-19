from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import ALLOWED_AUTHORING_FILES, LIST_FILE_KEYS, ContentAuthoringService
from app.engine.content.local_content_library import LocalContentLibraryService
from app.engine.content.validator import ValidationReport
from app.engine.content.world_branching import BranchMigrationImpact, WorldBranch, WorldBranchService


class AuthoringProjectStatus(BaseModel):
    status: str = "unknown"
    errors: int = 0
    warnings: int = 0
    last_run_at: str | None = None
    summary: str = ""


class AuthoringRecentEdit(BaseModel):
    label: str
    content_type: str
    updated_at: str


class AuthoringPackageStatus(BaseModel):
    total: int = 0
    by_type: dict[str, int] = Field(default_factory=dict)


class AuthoringProjectSummary(BaseModel):
    local_only: bool = True
    active_world: str | None = None
    active_world_name: str | None = None
    active_branch: str | None = None
    active_branch_name: str | None = None
    recent_edits: list[AuthoringRecentEdit] = Field(default_factory=list)
    validation_status: AuthoringProjectStatus = Field(default_factory=AuthoringProjectStatus)
    quality_gate_status: AuthoringProjectStatus = Field(default_factory=AuthoringProjectStatus)
    content_counts: dict[str, int] = Field(default_factory=dict)
    open_warnings: list[str] = Field(default_factory=list)
    migration_impact: list[str] = Field(default_factory=list)
    package_status: AuthoringPackageStatus = Field(default_factory=AuthoringPackageStatus)
    hidden_details_redacted: bool = True
    sensitive_details_redacted: bool = True


def build_authoring_project_summary(
    *,
    world_id: str | None,
    branch_id: str | None,
    authoring_service: ContentAuthoringService,
    branch_service: WorldBranchService,
    library_service: LocalContentLibraryService,
    quality_gate_results: list[Any],
) -> AuthoringProjectSummary:
    worlds = authoring_service.list_worlds()
    selected_world_id = world_id or (worlds[0].world_id if worlds else None)
    selected_world = None
    if selected_world_id is not None:
        selected_world = authoring_service.get_world_summary(selected_world_id)

    branches = branch_service.list_branches(selected_world_id) if selected_world_id else []
    selected_branch = _select_branch(branches, branch_id)
    validation = authoring_service.validate_world(selected_world_id) if selected_world_id else ValidationReport(world_id="")
    library = library_service.list_items()

    summary = AuthoringProjectSummary(
        active_world=selected_world.world_id if selected_world else None,
        active_world_name=selected_world.name if selected_world else None,
        active_branch=selected_branch.branch_id if selected_branch else None,
        active_branch_name=selected_branch.name if selected_branch else None,
        recent_edits=_recent_edits(authoring_service.worlds_root, selected_world_id),
        validation_status=_validation_status(validation),
        quality_gate_status=_quality_gate_status(selected_world_id, quality_gate_results),
        content_counts=_content_counts(authoring_service.worlds_root, selected_world_id, branch_count=len(branches)),
        open_warnings=_safe_warning_labels(validation),
        migration_impact=_migration_impact(branch_service, selected_world_id, selected_branch),
        package_status=_package_status(library.items),
    )
    return summary


def _select_branch(branches: list[WorldBranch], branch_id: str | None) -> WorldBranch | None:
    if branch_id:
        return next((branch for branch in branches if branch.branch_id == branch_id), None)
    return sorted(branches, key=lambda branch: branch.created_at, reverse=True)[0] if branches else None


def _recent_edits(worlds_root: Path, world_id: str | None) -> list[AuthoringRecentEdit]:
    if world_id is None:
        return []
    world_path = (worlds_root / world_id).resolve()
    edits: list[tuple[float, AuthoringRecentEdit]] = []
    for file_name in ALLOWED_AUTHORING_FILES:
        path = world_path / file_name
        if not path.exists() or not path.is_file():
            continue
        stat = path.stat()
        edits.append(
            (
                stat.st_mtime,
                AuthoringRecentEdit(
                    label=f"worlds/{world_id}/{file_name}",
                    content_type=file_name.removesuffix(".yaml"),
                    updated_at=datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
                ),
            )
        )
    return [edit for _, edit in sorted(edits, key=lambda item: item[0], reverse=True)[:8]]


def _validation_status(report: ValidationReport) -> AuthoringProjectStatus:
    errors = len(report.errors)
    warnings = len(report.warnings)
    return AuthoringProjectStatus(
        status="passed" if report.ok else "blocked",
        errors=errors,
        warnings=warnings,
        summary=f"{errors} errors, {warnings} warnings",
    )


def _quality_gate_status(world_id: str | None, results: list[Any]) -> AuthoringProjectStatus:
    latest = None
    for result in reversed(results):
        if world_id is None or getattr(result, "world_id", None) == world_id:
            latest = result
            break
    if latest is None:
        return AuthoringProjectStatus(status="not_run", summary="No local quality gate run recorded.")
    blockers = len(getattr(latest, "blockers", []) or [])
    errors = len(getattr(latest, "errors", []) or []) + blockers
    warnings = len(getattr(latest, "warnings", []) or [])
    passed = bool(getattr(latest, "passed", False))
    return AuthoringProjectStatus(
        status="passed" if passed else "blocked",
        errors=errors,
        warnings=warnings,
        last_run_at=getattr(latest, "created_at", None),
        summary=f"{blockers} blockers, {warnings} warnings",
    )


def _content_counts(worlds_root: Path, world_id: str | None, *, branch_count: int) -> dict[str, int]:
    counts: dict[str, int] = {"branches": branch_count}
    if world_id is None:
        return counts
    world_path = worlds_root / world_id
    for file_name, root_key in LIST_FILE_KEYS.items():
        data = _read_yaml_mapping(world_path / file_name)
        value = data.get(root_key, [])
        counts[root_key] = len(value) if isinstance(value, list) else 0
    return counts


def _safe_warning_labels(report: ValidationReport) -> list[str]:
    labels: list[str] = []
    for issue in [*report.errors, *report.warnings]:
        severity = getattr(issue.severity, "value", str(issue.severity))
        labels.append(f"{severity}:{issue.file}:{issue.path}:{issue.code}")
    return labels[:12]


def _migration_impact(
    branch_service: WorldBranchService,
    world_id: str | None,
    branch: WorldBranch | None,
) -> list[str]:
    if world_id is None or branch is None:
        return []
    try:
        diff = branch_service.diff_world(world_id, branch.branch_id)
    except Exception:
        return ["branch_diff_unavailable"]
    return [_migration_label(impact) for impact in diff.migration_impacts[:12]]


def _migration_label(impact: BranchMigrationImpact) -> str:
    return f"{impact.entity.file}:{impact.entity.entity_type}:{impact.entity.entity_id}"


def _package_status(items: list[Any]) -> AuthoringPackageStatus:
    by_type: dict[str, int] = {}
    for item in items:
        key = getattr(getattr(item, "content_type", None), "value", str(getattr(item, "content_type", "unknown")))
        by_type[key] = by_type.get(key, 0) + 1
    return AuthoringPackageStatus(total=len(items), by_type=by_type)


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}
