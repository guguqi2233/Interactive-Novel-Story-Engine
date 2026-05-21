from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.platform.narrative_project import NarrativeProject, utc_now_iso
from app.platform.project_workspace import (
    PROJECT_MANIFEST,
    create_project_workspace,
    resolve_safe_project_root,
    validate_project_workspace,
)


class ProjectSummary(BaseModel):
    project_id: str
    name: str
    path_redacted: str
    schema_version: str
    safe_status: str = "ok"


class ProjectRepository:
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create_project(self, project: NarrativeProject, *, dry_run: bool = False) -> NarrativeProject:
        project_root = resolve_safe_project_root(project.project_root, base_root=self.root)
        if not dry_run:
            create_project_workspace(project_root, project, base_root=self.root)
        return project.model_copy(update={"project_root": str(project_root)})

    def load_project(self, project_id_or_root: str | Path) -> NarrativeProject:
        root = self._resolve_project_root(project_id_or_root)
        manifest = root / PROJECT_MANIFEST
        if not manifest.exists():
            raise ValueError(f"Project manifest not found: {project_id_or_root}")
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        project = NarrativeProject.model_validate(data)
        return project.model_copy(update={"project_root": str(root)})

    def save_project(self, project: NarrativeProject) -> NarrativeProject:
        root = resolve_safe_project_root(project.project_root, base_root=self.root)
        if not root.exists():
            create_project_workspace(root, project, base_root=self.root)
        manifest = root / PROJECT_MANIFEST
        updated = project.model_copy(update={"updated_at": utc_now_iso(), "project_root": str(root)})
        manifest.write_text(yaml.safe_dump(updated.model_dump(mode="json"), sort_keys=True, allow_unicode=True), encoding="utf-8")
        return updated

    def list_projects(self) -> list[ProjectSummary]:
        summaries: list[ProjectSummary] = []
        for manifest in sorted(self.root.glob(f"*/{PROJECT_MANIFEST}")):
            try:
                project = NarrativeProject.model_validate(yaml.safe_load(manifest.read_text(encoding="utf-8")) or {})
            except Exception:
                continue
            summaries.append(
                ProjectSummary(
                    project_id=project.project_id,
                    name=project.name,
                    path_redacted=f".../{manifest.parent.name}",
                    schema_version=project.schema_version,
                )
            )
        return summaries

    def update_project_metadata(
        self,
        project_id_or_root: str | Path,
        *,
        name: str | None = None,
        description: str | None = None,
        default_world_id: str | None = None,
        active_campaign_id: str | None = None,
    ) -> NarrativeProject:
        project = self.load_project(project_id_or_root)
        updates: dict[str, object] = {"updated_at": utc_now_iso()}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if default_world_id is not None:
            updates["default_world_id"] = default_world_id
        if active_campaign_id is not None:
            updates["active_campaign_id"] = active_campaign_id
        return self.save_project(project.model_copy(update=updates))

    def validate_project(self, project_id_or_root: str | Path) -> dict[str, object]:
        project = self.load_project(project_id_or_root)
        report = validate_project_workspace(project.project_root, base_root=self.root)
        return {"ok": report.ok and not report.missing, "workspace": report.model_dump(mode="json")}

    def _resolve_project_root(self, project_id_or_root: str | Path) -> Path:
        raw = Path(project_id_or_root)
        if raw.exists() or str(project_id_or_root).endswith(PROJECT_MANIFEST) or any(sep in str(project_id_or_root) for sep in ("/", "\\")):
            root = raw.parent if raw.name == PROJECT_MANIFEST else raw
            return resolve_safe_project_root(root, base_root=self.root)
        for manifest in self.root.glob(f"*/{PROJECT_MANIFEST}"):
            data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
            if data.get("project_id") == str(project_id_or_root):
                return manifest.parent.resolve()
        raise ValueError(f"Unknown project: {project_id_or_root}")


class ProjectCreateRequest(BaseModel):
    project_id: str = "local_project"
    name: str = "Local Narrative Project"
    description: str = ""
    project_root: str
    default_world_id: str | None = None
    dry_run: bool = False


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    default_world_id: str | None = None
    active_campaign_id: str | None = None


class ProjectListResponse(BaseModel):
    projects: list[ProjectSummary] = Field(default_factory=list)

