from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from app.platform.security import redact_text, safe_identifier


class ModAuditActor(StrEnum):
    USER = "user"
    SYSTEM = "system"
    CODEX = "codex"
    TEST = "test"


class ModAuditResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    REJECTED = "rejected"
    DRY_RUN = "dry_run"


class ModAuditRecord(BaseModel):
    audit_id: str = Field(default_factory=lambda: f"mod_audit_{uuid4().hex}")
    project_id: str
    package_id: str
    action_type: str
    actor: ModAuditActor = ModAuditActor.SYSTEM
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    result: ModAuditResult
    safe_summary: str
    risk_level: str = "low"
    related_report_ids: list[str] = Field(default_factory=list)

    def normal_summary(self) -> dict[str, str | list[str]]:
        return {
            "audit_id": self.audit_id,
            "project_id": self.project_id,
            "package_id": self.package_id,
            "action_type": self.action_type,
            "actor": self.actor.value,
            "timestamp": self.timestamp.isoformat(),
            "result": self.result.value,
            "safe_summary": redact_text(self.safe_summary),
            "risk_level": self.risk_level,
            "related_report_ids": self.related_report_ids,
        }


class ModAuditRepository:
    def __init__(self, project_root: Path, project_id: str) -> None:
        self.audit_dir = project_root.resolve() / "modules" / "audit"
        self.project_id = project_id
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def append(self, record: ModAuditRecord) -> ModAuditRecord:
        if not safe_identifier(record.audit_id):
            raise ValueError("unsafe audit_id")
        safe_id = record.audit_id
        path = self.audit_dir / f"{safe_id}.json"
        path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        return record

    def list_records(self) -> list[ModAuditRecord]:
        records = [ModAuditRecord.model_validate_json(path.read_text(encoding="utf-8")) for path in self.audit_dir.glob("*.json")]
        return sorted(records, key=lambda record: record.timestamp, reverse=True)

    def get(self, audit_id: str) -> ModAuditRecord:
        if not safe_identifier(audit_id):
            raise ValueError("unsafe audit_id")
        safe_id = audit_id
        path = self.audit_dir / f"{safe_id}.json"
        if not path.exists():
            raise FileNotFoundError(audit_id)
        return ModAuditRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def append_action(
        self,
        *,
        package_id: str,
        action_type: str,
        result: ModAuditResult,
        safe_summary: str,
        actor: ModAuditActor = ModAuditActor.SYSTEM,
        risk_level: str = "low",
        related_report_ids: list[str] | None = None,
    ) -> ModAuditRecord:
        record = ModAuditRecord(
            project_id=self.project_id,
            package_id=package_id,
            action_type=action_type,
            result=result,
            actor=actor,
            safe_summary=redact_text(safe_summary),
            risk_level=risk_level,
            related_report_ids=related_report_ids or [],
        )
        return self.append(record)
