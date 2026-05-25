from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.desktop.studio_policy import redact_desktop_secret_text


RecoverySeverity = Literal["info", "warning", "error", "blocker"]
RecoveryDisposition = Literal["safe_auto", "needs_confirmation", "manual_only", "destructive_blocked"]


class RecoveryIssue(BaseModel):
    issue_id: str
    category: str
    severity: RecoverySeverity
    safe_summary: str
    suggested_action: str
    disposition: RecoveryDisposition


class RecoveryPlan(BaseModel):
    plan_id: str
    local_only: bool = True
    generated_at: str
    dry_run: bool = True
    issues: list[RecoveryIssue] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RecoveryApplyRequest(BaseModel):
    explicit_confirm: bool = False
    allow_destructive: bool = False


class RecoveryApplyResponse(BaseModel):
    local_only: bool = True
    applied: bool
    safe_summary: str
    warnings: list[str] = Field(default_factory=list)


class RecoveryService:
    """Local deterministic recovery suggestions.

    This service does not read secrets, call providers, upload reports, or
    mutate GameState. Destructive recovery remains blocked.
    """

    def detect_recovery_issues(
        self,
        *,
        provider_secret_configured: bool,
        database_configured: bool,
        debug_enabled: bool,
        quality_blockers: int = 0,
    ) -> list[RecoveryIssue]:
        issues: list[RecoveryIssue] = []
        if not provider_secret_configured:
            issues.append(
                RecoveryIssue(
                    issue_id="provider_missing_secret",
                    category="provider",
                    severity="warning",
                    safe_summary="Provider secret reference is missing or not configured.",
                    suggested_action="Configure api_key_env, secret_ref, or local_secret_ref in Provider Setup Wizard, or use mock/local_stub.",
                    disposition="manual_only",
                )
            )
        if not database_configured:
            issues.append(
                RecoveryIssue(
                    issue_id="database_unavailable",
                    category="database",
                    severity="error",
                    safe_summary="Database configuration is unavailable.",
                    suggested_action="Review Local Config Wizard and DATABASE_URL guidance.",
                    disposition="manual_only",
                )
            )
        if not debug_enabled:
            issues.append(
                RecoveryIssue(
                    issue_id="debug_api_disabled",
                    category="debug",
                    severity="info",
                    safe_summary="Debug API is disabled.",
                    suggested_action="Enable ENABLE_DEBUG_API only for trusted local diagnostics.",
                    disposition="manual_only",
                )
            )
        if quality_blockers:
            issues.append(
                RecoveryIssue(
                    issue_id="quality_gate_blockers",
                    category="quality",
                    severity="blocker",
                    safe_summary=f"{quality_blockers} quality blocker(s) require review.",
                    suggested_action="Open Quality Dashboard and resolve blockers manually.",
                    disposition="manual_only",
                )
            )
        issues.append(
            RecoveryIssue(
                issue_id="destructive_recovery_guard",
                category="safety",
                severity="info",
                safe_summary="Destructive recovery actions are blocked by default.",
                suggested_action="Use backup dry-run and explicit restore confirmation for data-changing operations.",
                disposition="destructive_blocked",
            )
        )
        return issues

    def build_recovery_plan(self, issues: list[RecoveryIssue]) -> RecoveryPlan:
        safe_issues = [
            issue.model_copy(update={"safe_summary": redact_desktop_secret_text(issue.safe_summary).text})
            for issue in issues
        ]
        return RecoveryPlan(
            plan_id=f"recovery_{uuid4().hex[:12]}",
            generated_at=datetime.now(UTC).isoformat(),
            issues=safe_issues,
            actions=[issue.suggested_action for issue in safe_issues if issue.disposition != "destructive_blocked"],
            blockers=[issue.issue_id for issue in safe_issues if issue.severity == "blocker"],
            warnings=[issue.issue_id for issue in safe_issues if issue.severity == "warning"],
        )

    def dry_run_recovery(self, issues: list[RecoveryIssue]) -> RecoveryPlan:
        return self.build_recovery_plan(issues)

    def apply_safe_recovery_confirmed(self, issues: list[RecoveryIssue], request: RecoveryApplyRequest) -> RecoveryApplyResponse:
        if not request.explicit_confirm:
            raise ValueError("explicit_confirm is required for recovery apply")
        if any(issue.disposition == "destructive_blocked" for issue in issues) and request.allow_destructive:
            raise ValueError("destructive recovery is blocked")
        return RecoveryApplyResponse(applied=True, safe_summary="Only safe acknowledgement actions were applied; project data was not modified.")
