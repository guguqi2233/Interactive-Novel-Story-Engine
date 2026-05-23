from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.desktop.studio_policy import BackupBundle, DesktopStudioPolicy, redact_desktop_secret_text


BackupScope = Literal["project", "worlds", "saves", "novel", "tavern", "mods", "quality", "all"]


class BackupManifest(BaseModel):
    manifest_id: str
    created_at: str
    local_only: bool = True
    project_id: str
    scope: list[BackupScope]
    included_safe_items: list[str] = Field(default_factory=list)
    excluded_items: list[str] = Field(default_factory=list)
    contains_secrets: bool = False
    contains_mature_private: bool = False
    checksum_manifest: dict[str, str] = Field(default_factory=dict)


class BackupPlan(BaseModel):
    plan_id: str
    local_only: bool = True
    dry_run: bool = True
    project_id: str
    scope: list[BackupScope]
    target_dir_summary: str
    would_write_files: list[str] = Field(default_factory=list)
    excluded_items: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class BackupCreateRequest(BaseModel):
    project_id: str = "local_project"
    scope: list[BackupScope] = Field(default_factory=lambda: ["all"])
    target_dir: str = "backups"
    include_mature_private: bool = False
    include_debug: bool = False
    explicit_confirm: bool = False


class BackupCreateResponse(BaseModel):
    local_only: bool = True
    created: bool
    backup_path_summary: str | None = None
    manifest: BackupManifest
    warnings: list[str] = Field(default_factory=list)


class BackupListResponse(BaseModel):
    local_only: bool = True
    backups: list[BackupManifest] = Field(default_factory=list)


class RestoreDryRunRequest(BaseModel):
    backup_path: str
    target_project_id: str = "restored_project"
    allow_overwrite: bool = False


class RestorePlan(BaseModel):
    local_only: bool = True
    dry_run: bool = True
    backup_valid: bool
    target_project_id: str
    would_create_project: bool
    conflicts: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class RestoreApplyRequest(RestoreDryRunRequest):
    explicit_confirm: bool = False


class RestoreApplyResponse(BaseModel):
    local_only: bool = True
    restored: bool
    target_project_id: str
    safe_summary: str
    warnings: list[str] = Field(default_factory=list)


class BackupService:
    def __init__(self, repo_root: Path, *, policy: DesktopStudioPolicy | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self.policy = policy or DesktopStudioPolicy()
        self.backup_root = self.repo_root / "backups"

    def create_backup_plan(self, request: BackupCreateRequest) -> BackupPlan:
        excluded = _default_exclusions(request.include_mature_private, request.include_debug)
        would_write = ["manifest.json", "project_safe_summary.json", "quality_safe_summary.json"]
        plan = BackupPlan(
            plan_id=f"backup_plan_{uuid4().hex[:12]}",
            project_id=request.project_id,
            scope=request.scope,
            target_dir_summary=_safe_path_summary(Path(request.target_dir)),
            would_write_files=would_write,
            excluded_items=excluded,
            warnings=[],
        )
        decision = self.policy.validate_backup_bundle(BackupBundle(file_paths=would_write, content_preview=json.dumps(plan.model_dump(mode="json"))))
        plan.blockers.extend(decision.blockers)
        return plan

    def create_backup_dry_run(self, request: BackupCreateRequest) -> BackupPlan:
        return self.create_backup_plan(request)

    def create_backup(self, request: BackupCreateRequest) -> BackupCreateResponse:
        if not request.explicit_confirm:
            raise ValueError("explicit_confirm is required to create a backup")
        plan = self.create_backup_plan(request)
        if plan.blockers:
            raise ValueError("backup plan has blockers")
        target_dir = _resolve_backup_dir(self.repo_root, request.target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        manifest = _manifest_for_plan(plan, request)
        backup_path = target_dir / f"{manifest.manifest_id}.zip"
        with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", manifest.model_dump_json(indent=2))
            archive.writestr("project_safe_summary.json", json.dumps({"project_id": request.project_id, "local_only": True}, indent=2))
            archive.writestr("quality_safe_summary.json", json.dumps({"status": "not_run", "safe_summary": True}, indent=2))
        return BackupCreateResponse(created=True, backup_path_summary=_safe_path_summary(backup_path), manifest=manifest)

    def list_backups(self) -> BackupListResponse:
        manifests: list[BackupManifest] = []
        if not self.backup_root.exists():
            return BackupListResponse(backups=[])
        for path in sorted(self.backup_root.glob("*.zip")):
            try:
                manifests.append(self.validate_backup(str(path)))
            except ValueError:
                continue
        return BackupListResponse(backups=manifests)

    def validate_backup(self, backup_path: str) -> BackupManifest:
        path = _resolve_existing_backup(self.repo_root, backup_path)
        with zipfile.ZipFile(path, "r") as archive:
            names = archive.namelist()
            decision = self.policy.validate_backup_bundle(BackupBundle(file_paths=names, content_preview=""))
            if not decision.allowed:
                raise ValueError("backup contains forbidden files")
            if "manifest.json" not in names:
                raise ValueError("backup manifest is missing")
            manifest_text = archive.read("manifest.json").decode("utf-8")
            if redact_desktop_secret_text(manifest_text).redaction_count:
                raise ValueError("backup manifest contains sensitive text")
            return BackupManifest.model_validate_json(manifest_text)


class RestoreService:
    def __init__(self, repo_root: Path, backup_service: BackupService | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self.backup_service = backup_service or BackupService(repo_root)

    def restore_dry_run(self, request: RestoreDryRunRequest) -> RestorePlan:
        blockers: list[str] = []
        conflicts: list[str] = []
        try:
            self.backup_service.validate_backup(request.backup_path)
        except ValueError as exc:
            blockers.append(str(exc))
        target = self.repo_root / "restored-projects" / request.target_project_id
        if target.exists() and not request.allow_overwrite:
            conflicts.append("target_project_exists")
        return RestorePlan(
            backup_valid=not blockers,
            target_project_id=request.target_project_id,
            would_create_project=not target.exists(),
            conflicts=conflicts,
            blockers=blockers,
        )

    def restore_apply_confirmed(self, request: RestoreApplyRequest) -> RestoreApplyResponse:
        if not request.explicit_confirm:
            raise ValueError("explicit_confirm is required to restore a backup")
        plan = self.restore_dry_run(request)
        if plan.blockers or (plan.conflicts and not request.allow_overwrite):
            raise ValueError("restore plan is blocked")
        target = self.repo_root / "restored-projects" / request.target_project_id
        target.mkdir(parents=True, exist_ok=True)
        (target / "RESTORED_FROM_BACKUP.txt").write_text("Restored from safe local backup manifest.\n", encoding="utf-8")
        return RestoreApplyResponse(restored=True, target_project_id=request.target_project_id, safe_summary="Restore created a new local project folder.")


def _manifest_for_plan(plan: BackupPlan, request: BackupCreateRequest) -> BackupManifest:
    return BackupManifest(
        manifest_id=f"backup_{uuid4().hex[:12]}",
        created_at=datetime.now(UTC).isoformat(),
        project_id=request.project_id,
        scope=request.scope,
        included_safe_items=plan.would_write_files,
        excluded_items=plan.excluded_items,
        contains_mature_private=bool(request.include_mature_private),
    )


def _default_exclusions(include_mature_private: bool, include_debug: bool) -> list[str]:
    excluded = [".env", "API key", "provider secrets", "logs", "cache", "node_modules", "frontend/dist", "desktop build outputs", "databases"]
    if not include_debug:
        excluded.append("debug-only data")
    if not include_mature_private:
        excluded.append("mature/private content")
    return excluded


def _resolve_backup_dir(repo_root: Path, raw: str) -> Path:
    path = (repo_root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    if repo_root not in path.parents and path != repo_root:
        raise ValueError("backup target must stay inside the local workspace")
    if any(part.lower() in {".env", "node_modules", "frontend", "dist", "logs", "cache"} for part in path.parts):
        raise ValueError("backup target path is not allowed")
    return path


def _resolve_existing_backup(repo_root: Path, raw: str) -> Path:
    path = (repo_root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    if not path.exists() or not path.is_file():
        raise ValueError("backup file not found")
    if path.suffix.lower() != ".zip":
        raise ValueError("backup must be a zip file")
    return path


def _safe_path_summary(path: Path) -> str:
    parts = path.parts
    if len(parts) <= 2:
        return path.name
    return f".../{parts[-2]}/{parts[-1]}".replace("\\", "/")
