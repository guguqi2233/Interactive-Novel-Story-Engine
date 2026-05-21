from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.platform.narrative_project import NarrativeProject, validate_project_relative_path


PROJECT_MANIFEST = "project.yaml"
PROJECT_DIRECTORIES = (
    "novel/manuscripts",
    "novel/outlines",
    "novel/chapters",
    "novel/scenes",
    "novel/arcs",
    "novel/plot_threads",
    "novel/foreshadowing",
    "novel/drafts",
    "novel/exports",
    "tavern/characters",
    "tavern/sessions",
    "tavern/messages",
    "tavern/lorebooks",
    "tavern/scene_presets",
    "tavern/memory",
    "tavern/proposals",
    "tavern/scenes",
    "tavern/profiles",
    "world/content_pack",
    "world/saves",
    "world/campaigns",
    "scripts/quests",
    "scripts/templates",
    "scripts/mods",
    "providers/profiles",
    "quality/reports",
    "quality/playtests",
    "quality/evals",
    "exports",
)


class ProjectWorkspaceLayout(BaseModel):
    manifest_file: str = PROJECT_MANIFEST
    directories: list[str] = Field(default_factory=lambda: list(PROJECT_DIRECTORIES))


class ProjectWorkspaceOperation(BaseModel):
    dry_run: bool
    project_root: str
    manifest_path: str
    directories: list[str] = Field(default_factory=list)
    created: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def resolve_safe_project_root(project_root: str | Path, *, base_root: str | Path | None = None) -> Path:
    root = Path(project_root)
    base = Path(base_root).resolve() if base_root is not None else None
    resolved = root.resolve()
    if any(part == ".." for part in root.parts) or root.name.lower().startswith(".env"):
        raise ValueError(f"Unsafe project root: {project_root}")
    if base is not None and not (resolved == base or base in resolved.parents):
        raise ValueError("Project root is outside allowed base root")
    return resolved


def list_project_sections() -> list[str]:
    return list(PROJECT_DIRECTORIES)


def create_project_workspace(
    project_root: str | Path,
    project: NarrativeProject | None = None,
    *,
    dry_run: bool = False,
    base_root: str | Path | None = None,
) -> ProjectWorkspaceOperation:
    root = resolve_safe_project_root(project_root, base_root=base_root)
    project_data = project or NarrativeProject(project_root=str(root))
    created: list[str] = []
    errors: list[str] = []
    for directory in PROJECT_DIRECTORIES:
        try:
            safe = validate_project_relative_path(directory)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        target = root / safe
        created.append(str(target))
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
    manifest = root / PROJECT_MANIFEST
    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            yaml.safe_dump(project_data.model_dump(mode="json"), sort_keys=True, allow_unicode=True),
            encoding="utf-8",
        )
    return ProjectWorkspaceOperation(
        dry_run=dry_run,
        project_root=str(root),
        manifest_path=str(manifest),
        directories=list(PROJECT_DIRECTORIES),
        created=created,
        errors=errors,
    )


def validate_project_workspace(project_root: str | Path, *, base_root: str | Path | None = None) -> ProjectWorkspaceOperation:
    root = resolve_safe_project_root(project_root, base_root=base_root)
    missing: list[str] = []
    errors: list[str] = []
    manifest = root / PROJECT_MANIFEST
    if not manifest.exists():
        errors.append("project.yaml is missing")
    else:
        try:
            NarrativeProject.model_validate(yaml.safe_load(manifest.read_text(encoding="utf-8")) or {})
        except Exception as exc:
            errors.append(f"Invalid project.yaml: {exc}")
    for directory in PROJECT_DIRECTORIES:
        target = root / validate_project_relative_path(directory)
        if not target.exists():
            missing.append(directory)
    return ProjectWorkspaceOperation(
        dry_run=True,
        project_root=str(root),
        manifest_path=str(manifest),
        directories=list(PROJECT_DIRECTORIES),
        missing=missing,
        errors=errors,
    )
