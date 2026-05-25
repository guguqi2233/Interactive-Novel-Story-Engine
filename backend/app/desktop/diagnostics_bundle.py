from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from app.desktop.local_logs import LocalLogService, SafeLogEntry
from app.desktop.studio_policy import DesktopStudioPolicy, ExportBundle, redact_desktop_secret_text
from app.llm.provider_redaction import provider_redactor


class DiagnosticsBundleManifest(BaseModel):
    bundle_id: str
    created_at: str
    local_only: bool = True
    debug_bundle: bool = False
    included_sections: list[str] = Field(default_factory=list)
    excluded_sections: list[str] = Field(default_factory=list)
    redaction_policy: str = "desktop_safe_redaction"
    contains_secrets: bool = False
    contains_hidden_debug_mature_private: bool = False


class DiagnosticsBundlePreview(BaseModel):
    local_only: bool = True
    writes_file: bool = False
    manifest: DiagnosticsBundleManifest
    safe_payload: dict[str, object]
    warnings: list[str] = Field(default_factory=list)


class DiagnosticsBundleCreateRequest(BaseModel):
    project_id: str = "local_project"
    include_debug: bool = False
    explicit_confirm_debug: bool = False


class DiagnosticsBundleCreateResponse(BaseModel):
    local_only: bool = True
    created: bool
    bundle_path_summary: str | None = None
    manifest: DiagnosticsBundleManifest
    warnings: list[str] = Field(default_factory=list)


class DiagnosticsBundleValidation(BaseModel):
    local_only: bool = True
    valid: bool
    manifest: DiagnosticsBundleManifest | None = None
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class DiagnosticsBundleService:
    def __init__(self, repo_root: Path, *, debug_enabled: bool = False, policy: DesktopStudioPolicy | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self.debug_enabled = debug_enabled
        self.policy = policy or DesktopStudioPolicy()
        self.export_root = self.repo_root / "exports" / "diagnostics"

    def preview_bundle(self, request: DiagnosticsBundleCreateRequest) -> DiagnosticsBundlePreview:
        debug_included = bool(request.include_debug and request.explicit_confirm_debug and self.debug_enabled)
        manifest = DiagnosticsBundleManifest(
            bundle_id=f"diagnostics_{uuid4().hex[:12]}",
            created_at=datetime.now(UTC).isoformat(),
            debug_bundle=debug_included,
            included_sections=[
                "app_version",
                "environment_safe_summary",
                "project_safe_summary",
                "backend_health_safe_summary",
                "provider_safe_summary",
                "quality_gate_summary",
                "module_status_summary",
                "recent_safe_errors",
                "redacted_logs",
                "validation_reports_normal_view",
            ],
            excluded_sections=[
                ".env",
                "API key",
                "provider secrets",
                "local provider secret store",
                "raw env",
                "raw prompt/output",
                "hidden facts",
                "NPC secrets",
                "debug memory",
                "raw state_deltas",
                "mature/private content",
                "database files",
                "full save files",
            ],
        )
        payload = self._safe_payload(request.project_id, debug_included=debug_included)
        return DiagnosticsBundlePreview(manifest=manifest, safe_payload=payload, warnings=[] if debug_included or not request.include_debug else ["debug_bundle_requires_explicit_confirm_and_ENABLE_DEBUG_API"])

    def create_bundle(self, request: DiagnosticsBundleCreateRequest) -> DiagnosticsBundleCreateResponse:
        preview = self.preview_bundle(request)
        self.export_root.mkdir(parents=True, exist_ok=True)
        bundle_path = self.export_root / f"{preview.manifest.bundle_id}.zip"
        with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", preview.manifest.model_dump_json(indent=2))
            archive.writestr("safe_payload.json", json.dumps(preview.safe_payload, indent=2))
        validation = self.validate_bundle(str(bundle_path))
        if not validation.valid:
            raise ValueError("diagnostics bundle validation failed")
        return DiagnosticsBundleCreateResponse(created=True, bundle_path_summary=_safe_path_summary(bundle_path), manifest=preview.manifest, warnings=preview.warnings)

    def validate_bundle(self, bundle_path: str) -> DiagnosticsBundleValidation:
        path = Path(bundle_path).resolve()
        if not path.exists() or path.suffix.lower() != ".zip":
            return DiagnosticsBundleValidation(valid=False, blockers=["bundle_not_found_or_not_zip"])
        with zipfile.ZipFile(path, "r") as archive:
            names = archive.namelist()
            decision = self.policy.validate_export_bundle(ExportBundle(file_paths=names, content_preview=""))
            if not decision.allowed:
                return DiagnosticsBundleValidation(valid=False, blockers=decision.blockers)
            if "manifest.json" not in names:
                return DiagnosticsBundleValidation(valid=False, blockers=["manifest_missing"])
            text = archive.read("manifest.json").decode("utf-8")
            payload = archive.read("safe_payload.json").decode("utf-8") if "safe_payload.json" in names else ""
            desktop_redaction = redact_desktop_secret_text(text + payload)
            provider_redaction = provider_redactor.redact_text(desktop_redaction.text)
            if desktop_redaction.redaction_count or provider_redaction.redaction_count:
                return DiagnosticsBundleValidation(valid=False, blockers=["sensitive_text_detected"])
            return DiagnosticsBundleValidation(valid=True, manifest=DiagnosticsBundleManifest.model_validate_json(text))

    def _safe_payload(self, project_id: str, *, debug_included: bool) -> dict[str, object]:
        logs = LocalLogService(self.repo_root, debug_enabled=self.debug_enabled).list_safe_logs(limit=20, include_debug=debug_included).logs
        return {
            "app": {"version": "0.1.0", "local_only": True},
            "project": {"project_id": project_id, "safe_summary": True},
            "backend_health": {"status": "available"},
            "provider": {"configured": "safe_summary_only", "credential_status": "redacted"},
            "quality_gate": {"status": "not_run"},
            "modules": {"status": "safe_summary_only"},
            "recent_safe_errors": [],
            "redacted_logs": [entry.model_dump(mode="json") for entry in logs],
            "validation_reports": {"normal_view": True},
        }


def _safe_path_summary(path: Path) -> str:
    parts = path.parts
    if len(parts) <= 2:
        return path.name
    return f".../{parts[-2]}/{parts[-1]}".replace("\\", "/")
