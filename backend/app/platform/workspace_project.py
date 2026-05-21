from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from app.platform.security import redacted_path, safe_identifier


class WorkspaceProjectManifest(BaseModel):
    workspace_id: str
    name: str
    version: str = "2.0.0"
    contract_version: str = "2"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    worlds_dir: str = "worlds"
    campaigns_dir: str = "campaigns"
    modules_dir: str = "modules"
    packages_dir: str = "packages"
    templates_dir: str = "templates"
    backups_dir: str = "backups"
    settings_ref: str = "settings.json"
    safe_metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("workspace_id")
    @classmethod
    def validate_workspace_id(cls, value: str) -> str:
        if not safe_identifier(value):
            raise ValueError("Unsafe workspace_id")
        return value


class WorkspaceProjectReport(BaseModel):
    ok: bool
    manifest: WorkspaceProjectManifest | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    path_redacted: str | None = None


class WorkspaceProjectService:
    def __init__(self, workspace_root: str | Path) -> None:
        self.workspace_root = Path(workspace_root)

    def init_project(self, workspace_id: str, name: str) -> WorkspaceProjectReport:
        manifest = WorkspaceProjectManifest(workspace_id=workspace_id, name=name)
        return WorkspaceProjectReport(ok=True, manifest=manifest, path_redacted=redacted_path(self.workspace_root))

    def validate_project(self, manifest: WorkspaceProjectManifest) -> WorkspaceProjectReport:
        errors: list[str] = []
        for field in ("worlds_dir", "campaigns_dir", "modules_dir", "packages_dir", "templates_dir", "backups_dir"):
            value = getattr(manifest, field)
            if Path(value).is_absolute() or ".." in Path(value).parts:
                errors.append(f"{field} must stay inside workspace")
        return WorkspaceProjectReport(ok=not errors, manifest=manifest, errors=errors, path_redacted=redacted_path(self.workspace_root))

