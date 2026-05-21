from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository
from app.platform.project_workspace import create_project_workspace
from app.platform.security import contains_secret_text, validate_relative_package_path


class ProjectMigrationCopy(BaseModel):
    source: str
    target: str
    section: str


class ProjectMigrationPlan(BaseModel):
    can_migrate: bool
    source_root: str
    target_project_root: str
    project_id: str
    project_name: str
    copies: list[ProjectMigrationCopy] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ProjectMigrationReport(BaseModel):
    dry_run: bool
    applied: bool = False
    plan: ProjectMigrationPlan
    migration_history: list[dict[str, str]] = Field(default_factory=list)


MAPPING = {
    "worlds": "world/content_pack",
    "saves": "world/saves",
    "mods": "scripts/mods",
    "modules": "scripts/mods",
    "action_mods": "scripts/mods",
    "templates": "scripts/templates",
    "providers": "providers",
    "quality_reports": "quality/reports",
    "scenario_suites": "quality/reports",
}


def detect_v2_0_workspace(old_root: str | Path) -> bool:
    root = Path(old_root)
    return any((root / name).exists() for name in ("worlds", "saves", "mods", "modules", "templates", "providers", "quality_reports"))


def plan_project_migration(
    old_root: str | Path,
    new_project_root: str | Path,
    *,
    project_id: str = "migrated_project",
    project_name: str = "Migrated Narrative Project",
) -> ProjectMigrationPlan:
    source = Path(old_root).resolve()
    target = Path(new_project_root).resolve()
    blockers: list[str] = []
    warnings: list[str] = []
    copies: list[ProjectMigrationCopy] = []
    skipped: list[str] = []
    if not detect_v2_0_workspace(source):
        blockers.append("source does not look like a v2.0 workspace")
    if target.exists():
        blockers.append("target project root already exists")
    for source_name, target_name in MAPPING.items():
        section_root = source / source_name
        if not section_root.exists():
            continue
        for path in sorted(item for item in section_root.rglob("*") if item.is_file()):
            rel = path.relative_to(source).as_posix()
            if _skip_file(path, rel):
                skipped.append(rel)
                continue
            target_rel = f"{target_name}/{path.relative_to(section_root).as_posix()}"
            try:
                validate_relative_package_path(target_rel)
            except ValueError:
                skipped.append(rel)
                continue
            copies.append(ProjectMigrationCopy(source=str(path), target=target_rel, section=target_name))
    if not copies:
        warnings.append("no migratable files found")
    return ProjectMigrationPlan(
        can_migrate=not blockers,
        source_root=str(source),
        target_project_root=str(target),
        project_id=project_id,
        project_name=project_name,
        copies=copies,
        skipped=skipped,
        blockers=blockers,
        warnings=warnings,
    )


def migrate_project_dry_run(old_root: str | Path, new_project_root: str | Path, **kwargs: str) -> ProjectMigrationReport:
    plan = plan_project_migration(old_root, new_project_root, **kwargs)
    return ProjectMigrationReport(dry_run=True, plan=plan)


def migrate_project_apply(
    old_root: str | Path,
    new_project_root: str | Path,
    repository: ProjectRepository,
    *,
    confirm_apply: bool = False,
    **kwargs: str,
) -> ProjectMigrationReport:
    plan = plan_project_migration(old_root, new_project_root, **kwargs)
    if not confirm_apply:
        plan.blockers.append("confirm_apply is required")
        plan.can_migrate = False
        return ProjectMigrationReport(dry_run=False, plan=plan)
    if not plan.can_migrate:
        return ProjectMigrationReport(dry_run=False, plan=plan)
    target = Path(plan.target_project_root)
    project = NarrativeProject(project_id=plan.project_id, name=plan.project_name, project_root=str(target))
    create_project_workspace(target, project, base_root=repository.root)
    for item in plan.copies:
        destination = target / item.target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item.source, destination)
    history = [{
        "migration_id": "v2.0-workspace-to-v2.1-narrative-project",
        "source_root": plan.source_root,
        "target_project_root": plan.target_project_root,
        "created_at": datetime.now(UTC).isoformat(),
    }]
    project.migration_history = history
    repository.save_project(project)
    return ProjectMigrationReport(dry_run=False, applied=True, plan=plan, migration_history=history)


def _skip_file(path: Path, rel: str) -> bool:
    lowered = rel.lower().replace("\\", "/")
    if any(part in lowered.split("/") for part in (".env", "node_modules", "dist", "logs", "cache", "caches", "backups", "crash-reports", "__pycache__")):
        return True
    if path.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".log", ".exe", ".bat", ".cmd", ".ps1", ".sh", ".py", ".js"}:
        return True
    try:
        if path.stat().st_size < 512_000 and contains_secret_text(path.read_text(encoding="utf-8", errors="ignore")):
            return True
    except OSError:
        return True
    return False

