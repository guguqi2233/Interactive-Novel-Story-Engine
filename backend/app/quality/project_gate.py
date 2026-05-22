from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.platform.project_validation import ProjectValidationReport, validate_project
from app.platform.security import redact_text
from app.quality.gate import QualityGateConfig, QualityGateProfile, run_quality_gate


class ProjectQualityGateConfig(BaseModel):
    profile: Literal["fast", "standard", "strict"] = "standard"
    run_world_quality_gate: bool = True
    fail_on_warning: bool = False
    include_debug_details: bool = False
    include_cross_mode: bool = False
    include_rp_mature: bool = True


class ProjectQualityGateCheck(BaseModel):
    check_id: str
    status: Literal["pass", "fail", "warning", "skip"]
    message: str
    category: str = "project"
    safe_details: dict[str, str] = Field(default_factory=dict)


class ProjectQualityGateResult(BaseModel):
    project_id: str | None = None
    passed: bool = False
    checks: list[ProjectQualityGateCheck] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    report_refs: list[str] = Field(default_factory=list)
    summary: dict[str, int | str | None] = Field(default_factory=dict)

    def model_dump_normal(self) -> dict:
        payload = self.model_dump(mode="json")
        payload["blockers"] = [redact_text(item) for item in self.blockers]
        payload["errors"] = [redact_text(item) for item in self.errors]
        payload["warnings"] = [redact_text(item) for item in self.warnings]
        return payload


def run_project_quality_gate(project_path: str | Path, config: ProjectQualityGateConfig | None = None) -> ProjectQualityGateResult:
    cfg = config or ProjectQualityGateConfig()
    validation = validate_project(project_path, profile="normal")
    result = ProjectQualityGateResult(project_id=validation.project_id)
    _add_validation(result, validation)
    _try_novel_gate(project_path, result)
    _try_tavern_gate(project_path, result)
    if cfg.include_cross_mode:
        _try_cross_mode_gate(project_path, result)
    if cfg.include_rp_mature:
        _try_rp_mature_gate(project_path, result)
    if cfg.run_world_quality_gate and validation.project_id:
        _try_world_gate(project_path, result, cfg)
    if cfg.fail_on_warning and result.warnings:
        result.blockers.append("Project quality gate configured to fail on warnings.")
    result.passed = not result.blockers and not result.errors
    result.summary = {
        "checks": len(result.checks),
        "blockers": len(result.blockers),
        "errors": len(result.errors),
        "warnings": len(result.warnings),
        "profile": cfg.profile,
    }
    return result


def _add_validation(result: ProjectQualityGateResult, validation: ProjectValidationReport) -> None:
    if validation.ok:
        result.checks.append(ProjectQualityGateCheck(check_id="project_validation", status="pass", message="Project validation passed."))
    else:
        result.checks.append(ProjectQualityGateCheck(check_id="project_validation", status="fail", message="Project validation failed."))
    for issue in validation.errors:
        result.errors.append(f"{issue.code}: {issue.message}")
        result.blockers.append(f"{issue.code}: {issue.message}")
    for issue in validation.warnings:
        result.warnings.append(f"{issue.code}: {issue.message}")
    for issue in validation.suggestions:
        result.suggestions.append(f"{issue.code}: {issue.message}")


def _try_world_gate(project_path: str | Path, result: ProjectQualityGateResult, cfg: ProjectQualityGateConfig) -> None:
    root = Path(project_path)
    content_root = root / "world" / "content_pack"
    if not content_root.exists():
        result.checks.append(ProjectQualityGateCheck(check_id="world_quality_gate", status="skip", message="No world content pack section.", category="world"))
        return
    worlds = sorted(path.name for path in content_root.iterdir() if path.is_dir())
    if not worlds:
        result.checks.append(ProjectQualityGateCheck(check_id="world_quality_gate", status="skip", message="No world packs found.", category="world"))
        return
    profile = QualityGateProfile.FAST if cfg.profile == "fast" else QualityGateProfile.STANDARD
    gate = run_quality_gate(worlds[0], QualityGateConfig(profile=profile, min_health_score=0), worlds_root=content_root)
    result.report_refs.append(f"world_quality_gate:{worlds[0]}")
    if gate.passed:
        result.checks.append(ProjectQualityGateCheck(check_id="world_quality_gate", status="pass", message="World quality gate passed.", category="world"))
    else:
        result.checks.append(ProjectQualityGateCheck(check_id="world_quality_gate", status="fail", message="World quality gate failed.", category="world"))
        result.blockers.extend(gate.blockers)
        result.errors.extend(gate.errors)
        result.warnings.extend(gate.warnings)


def _try_novel_gate(project_path: str | Path, result: ProjectQualityGateResult) -> None:
    try:
        from app.platform.novel_studio import NovelConsistencyChecker, NovelRepository
    except Exception:
        return
    repo = NovelRepository(project_path)
    if not (Path(project_path) / "novel" / "manuscripts").exists():
        result.checks.append(ProjectQualityGateCheck(check_id="novel_quality_gate", status="skip", message="No Novel Studio section.", category="novel"))
        return
    try:
        manuscripts = repo.list_manuscripts()
        if not manuscripts:
            result.checks.append(ProjectQualityGateCheck(check_id="novel_quality_gate", status="skip", message="No novel manuscripts.", category="novel"))
            return
        report = NovelConsistencyChecker(repo).check(manuscripts[0].manuscript_id)
    except Exception as exc:
        result.checks.append(ProjectQualityGateCheck(check_id="novel_quality_gate", status="fail", message="Novel quality gate failed.", category="novel"))
        result.errors.append(redact_text(str(exc)))
        result.blockers.append("novel_quality_gate: failed to run")
        return
    if report.status == "fail":
        result.checks.append(ProjectQualityGateCheck(check_id="novel_quality_gate", status="fail", message="Novel consistency failed.", category="novel"))
        for issue in report.issues:
            if issue.severity in {"error", "blocker"}:
                result.errors.append(f"{issue.code}: {issue.message}")
                if issue.severity == "blocker":
                    result.blockers.append(f"{issue.code}: {issue.message}")
            else:
                result.warnings.append(f"{issue.code}: {issue.message}")
    elif report.status == "warning":
        result.checks.append(ProjectQualityGateCheck(check_id="novel_quality_gate", status="warning", message="Novel consistency warnings.", category="novel"))
        result.warnings.extend(f"{issue.code}: {issue.message}" for issue in report.issues)
    else:
        result.checks.append(ProjectQualityGateCheck(check_id="novel_quality_gate", status="pass", message="Novel consistency passed.", category="novel"))


def _try_tavern_gate(project_path: str | Path, result: ProjectQualityGateResult) -> None:
    root = Path(project_path)
    tavern_root = root / "tavern"
    if not tavern_root.exists():
        result.checks.append(ProjectQualityGateCheck(check_id="tavern_boundary_gate", status="skip", message="No Tavern Studio section.", category="tavern"))
        return
    try:
        from app.evals.tavern_boundary import run_default_tavern_boundary_evals
    except Exception:
        return
    report = run_default_tavern_boundary_evals()
    result.report_refs.append("tavern_boundary_gate:default")
    if report.failed:
        result.checks.append(ProjectQualityGateCheck(check_id="tavern_boundary_gate", status="fail", message="Tavern boundary evals failed.", category="tavern"))
        result.blockers.append("tavern_boundary_gate: failed")
        result.errors.append("tavern_boundary_gate: failed")
    else:
        result.checks.append(ProjectQualityGateCheck(check_id="tavern_boundary_gate", status="pass", message="Tavern boundary evals passed.", category="tavern"))


def _try_cross_mode_gate(project_path: str | Path, result: ProjectQualityGateResult) -> None:
    try:
        from app.platform.cross_mode import CrossModeConflictDetector, CrossModeLinkReviewService, validate_cross_mode_project
    except Exception as exc:
        result.checks.append(ProjectQualityGateCheck(check_id="cross_mode_quality_gate", status="fail", message="Cross-mode quality gate unavailable.", category="cross_mode"))
        result.errors.append(redact_text(str(exc)))
        result.blockers.append("cross_mode_quality_gate: unavailable")
        return

    validation = validate_cross_mode_project(project_path, profile="normal")
    conflict_report = CrossModeConflictDetector(project_path).detect()
    link_review = CrossModeLinkReviewService(project_path).review()
    if validation.ok and conflict_report.ok and link_review.ok:
        result.checks.append(ProjectQualityGateCheck(check_id="cross_mode_quality_gate", status="pass", message="Cross-mode validation passed.", category="cross_mode"))
    else:
        result.checks.append(ProjectQualityGateCheck(check_id="cross_mode_quality_gate", status="fail", message="Cross-mode validation failed.", category="cross_mode"))
    for issue in validation.blockers:
        result.blockers.append(f"{issue.code}: {issue.message}")
    for issue in validation.errors:
        result.errors.append(f"{issue.code}: {issue.message}")
    for issue in validation.warnings:
        result.warnings.append(f"{issue.code}: {issue.message}")
    for conflict in conflict_report.conflicts:
        if conflict.severity == "blocker":
            result.blockers.append(f"{conflict.conflict_type}: {redact_text(conflict.safe_summary)}")
        elif conflict.severity == "error":
            result.errors.append(f"{conflict.conflict_type}: {redact_text(conflict.safe_summary)}")
        elif conflict.severity == "warning":
            result.warnings.append(f"{conflict.conflict_type}: {redact_text(conflict.safe_summary)}")
    for link_id in link_review.broken_links:
        result.blockers.append(f"cross_mode_link_broken: {redact_text(link_id)}")
    for link_id in link_review.hidden_target_risks:
        result.errors.append(f"cross_mode_hidden_target_risk: {redact_text(link_id)}")


def _try_rp_mature_gate(project_path: str | Path, result: ProjectQualityGateResult) -> None:
    try:
        from app.platform.rp_mature import RPMatureQualityGateConfig, run_rp_mature_quality_gate
    except Exception as exc:
        result.checks.append(ProjectQualityGateCheck(check_id="rp_mature_quality_gate", status="fail", message="RP/Mature quality gate unavailable.", category="rp_mature"))
        result.errors.append(redact_text(str(exc)))
        result.blockers.append("rp_mature_quality_gate: unavailable")
        return
    gate = run_rp_mature_quality_gate(project_path, RPMatureQualityGateConfig())
    result.report_refs.append("rp_mature_quality_gate:default")
    if gate.passed:
        result.checks.append(ProjectQualityGateCheck(check_id="rp_mature_quality_gate", status="pass", message="RP/Mature quality gate passed.", category="rp_mature"))
    else:
        result.checks.append(ProjectQualityGateCheck(check_id="rp_mature_quality_gate", status="fail", message="RP/Mature quality gate failed.", category="rp_mature"))
        result.blockers.extend(gate.blockers)
        result.errors.extend(gate.errors)
        result.warnings.extend(gate.warnings)
