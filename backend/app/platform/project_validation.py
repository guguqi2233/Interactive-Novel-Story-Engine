from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from app.engine.content.validator import validate_world_pack
from app.platform.narrative_project import NarrativeProject
from app.platform.project_workspace import PROJECT_MANIFEST, PROJECT_DIRECTORIES
from app.platform.security import contains_secret_text, redact_text, validate_relative_package_path


class ProjectValidationIssue(BaseModel):
    severity: Literal["error", "warning", "suggestion"]
    code: str
    message: str
    path: str | None = None
    safe_details: dict[str, str] = Field(default_factory=dict)


class ProjectValidationReport(BaseModel):
    project_id: str | None = None
    ok: bool = False
    profile: Literal["normal", "debug"] = "normal"
    errors: list[ProjectValidationIssue] = Field(default_factory=list)
    warnings: list[ProjectValidationIssue] = Field(default_factory=list)
    suggestions: list[ProjectValidationIssue] = Field(default_factory=list)
    summary: dict[str, int] = Field(default_factory=dict)

    def finalize(self) -> "ProjectValidationReport":
        self.ok = not self.errors
        self.summary = {"errors": len(self.errors), "warnings": len(self.warnings), "suggestions": len(self.suggestions)}
        return self

    def normal_copy(self) -> "ProjectValidationReport":
        return ProjectValidationReport(
            project_id=self.project_id,
            ok=self.ok,
            profile="normal",
            errors=[_redact_issue(issue) for issue in self.errors],
            warnings=[_redact_issue(issue) for issue in self.warnings],
            suggestions=[_redact_issue(issue) for issue in self.suggestions],
            summary=self.summary,
        )


def validate_project(project_root: str | Path, *, profile: Literal["normal", "debug"] = "normal") -> ProjectValidationReport:
    root = Path(project_root).resolve()
    report = ProjectValidationReport(profile=profile)
    manifest = root / PROJECT_MANIFEST
    if not manifest.exists():
        report.errors.append(_issue("error", "project_manifest_missing", "project.yaml is missing", "project.yaml"))
        return report.finalize()
    try:
        payload = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        project = NarrativeProject.model_validate(payload)
        report.project_id = project.project_id
    except Exception as exc:
        report.errors.append(_issue("error", "project_manifest_invalid", f"Invalid project.yaml: {exc}", "project.yaml"))
        return report.finalize()
    for directory in PROJECT_DIRECTORIES:
        if not (root / directory).exists():
            report.warnings.append(_issue("warning", "project_directory_missing", f"Project directory is missing: {directory}", directory))
    if project.default_world_id:
        world_root = root / "world" / "content_pack"
        world_path = world_root / project.default_world_id
        if world_path.exists():
            world_report = validate_world_pack(project.default_world_id, worlds_root=world_root)
            for item in world_report.errors:
                report.errors.append(_issue("error", f"world_{item.code}", item.message, item.file))
            for item in world_report.warnings:
                report.warnings.append(_issue("warning", f"world_{item.code}", item.message, item.file))
        else:
            report.errors.append(_issue("error", "default_world_missing", "default_world_id does not exist in project world content pack", "world/content_pack"))
    known_refs = _collect_project_refs(root)
    _scan_project_files(root, report)
    _validate_cross_mode_link_files(root, report, known_refs)
    return report.finalize().normal_copy() if profile == "normal" else report.finalize()


def _scan_project_files(root: Path, report: ProjectValidationReport) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        try:
            validate_relative_package_path(rel)
        except ValueError as exc:
            report.errors.append(_issue("error", "forbidden_export_candidate", str(exc), rel))
            continue
        if path.stat().st_size < 512_000:
            text = path.read_text(encoding="utf-8", errors="ignore")
            lowered = text.lower()
            if _contains_project_secret_text(text):
                report.errors.append(_issue("error", "secret_like_text", "Secret-like text found in project file", rel))
            if ("hidden fact" in lowered or "npc_secret" in lowered or "debug_memory" in lowered) and not rel.startswith(("quality/", "world/content_pack/")):
                report.warnings.append(_issue("warning", "hidden_leak_risk", "Hidden/debug marker found outside explicit world/quality context", rel))


def _validate_cross_mode_link_files(root: Path, report: ProjectValidationReport, known_refs: set[str]) -> None:
    for path in sorted(root.rglob("cross_mode_links.json")):
        rel = path.relative_to(root).as_posix()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.errors.append(_issue("error", "cross_mode_links_invalid_json", f"Invalid CrossModeLink registry: {exc}", rel))
            continue
        links = payload.get("links", payload) if isinstance(payload, dict) else payload
        if not isinstance(links, list):
            report.errors.append(_issue("error", "cross_mode_links_invalid_shape", "CrossModeLink registry must be a list or contain a links list", rel))
            continue
        for index, link in enumerate(links):
            if not isinstance(link, dict):
                report.errors.append(_issue("error", "cross_mode_link_invalid", "CrossModeLink entry must be an object", f"{rel}#{index}"))
                continue
            if link.get("status") == "broken":
                report.errors.append(_issue("error", "cross_mode_link_broken", "CrossModeLink is marked broken", f"{rel}#{index}"))
            if not link.get("source_ref") or not link.get("target_ref"):
                report.errors.append(_issue("error", "cross_mode_link_invalid_ref", "CrossModeLink must include source_ref and target_ref", f"{rel}#{index}"))
                continue
            if link["source_ref"] not in known_refs:
                report.errors.append(_issue("error", "cross_mode_link_source_missing", "CrossModeLink source_ref does not resolve to a known project reference", f"{rel}#{index}"))
            if link["target_ref"] not in known_refs:
                report.errors.append(_issue("error", "cross_mode_link_target_missing", "CrossModeLink target_ref does not resolve to a known project reference", f"{rel}#{index}"))


def _collect_project_refs(root: Path) -> set[str]:
    refs: set[str] = set()
    mode_prefixes = {
        "novel": "novel",
        "tavern": "tavern",
        "world": "world",
        "scripts": "script",
        "quality": "quality",
        "providers": "provider",
    }
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        refs.add(rel)
        refs.add(Path(rel).with_suffix("").as_posix())
        parts = rel.split("/")
        if parts:
            prefix = mode_prefixes.get(parts[0])
            if prefix:
                refs.add(f"{prefix}:{Path(rel).stem}")
                refs.add(f"{prefix}:{Path(rel).with_suffix('').as_posix()}")
                refs.add(f"{prefix}:{Path('/'.join(parts[1:])).with_suffix('').as_posix()}")
    return refs


def _contains_project_secret_text(text: str) -> bool:
    scrubbed = re.sub(r'(?i)["\']?api_key_env["\']?\s*[:=]\s*["\']?[^,"\'\n}]+["\']?', '"env_ref": "[ENV_REF]"', text)
    return contains_secret_text(scrubbed)


def _issue(severity: Literal["error", "warning", "suggestion"], code: str, message: str, path: str | None = None) -> ProjectValidationIssue:
    return ProjectValidationIssue(severity=severity, code=code, message=message, path=path)


def _redact_issue(issue: ProjectValidationIssue) -> ProjectValidationIssue:
    return issue.model_copy(update={"message": redact_text(issue.message), "safe_details": {key: redact_text(value) for key, value in issue.safe_details.items()}})
