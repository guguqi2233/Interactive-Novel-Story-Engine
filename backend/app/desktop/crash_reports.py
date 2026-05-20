from __future__ import annotations

import re
from datetime import UTC, datetime
from traceback import format_exception
from uuid import uuid4

from pydantic import BaseModel, Field


class CrashReport(BaseModel):
    id: str
    timestamp: str
    component: str
    error_type: str
    safe_message: str
    stack_redacted: str
    context_safe_summary: dict[str, str] = Field(default_factory=dict)


class CrashReportListResponse(BaseModel):
    local_only: bool = True
    reports: list[CrashReport] = Field(default_factory=list)


class CrashReportService:
    """Local-only crash report store with mandatory redaction."""

    def __init__(self, *, max_reports: int = 50) -> None:
        self.max_reports = max_reports
        self._reports: dict[str, CrashReport] = {}

    def record_backend_exception(
        self,
        exc: BaseException,
        *,
        component: str = "backend",
        context: dict[str, object] | None = None,
    ) -> CrashReport:
        stack = "".join(format_exception(type(exc), exc, exc.__traceback__))
        report = CrashReport(
            id=f"crash-{uuid4().hex}",
            timestamp=datetime.now(UTC).isoformat(),
            component=_safe_token(component),
            error_type=_safe_token(type(exc).__name__),
            safe_message=self.redact_report(str(exc)),
            stack_redacted=self.redact_report(stack),
            context_safe_summary={
                _safe_token(key): self.redact_report(str(value))
                for key, value in (context or {}).items()
                if _safe_context_key(key)
            },
        )
        self._reports[report.id] = report
        self._trim()
        return report

    def list_crash_reports(self) -> list[CrashReport]:
        return sorted(self._reports.values(), key=lambda report: report.timestamp, reverse=True)

    def read_crash_report(self, report_id: str) -> CrashReport:
        report = self._reports.get(report_id)
        if report is None:
            raise KeyError(report_id)
        return report

    def delete_crash_report(self, report_id: str) -> bool:
        return self._reports.pop(report_id, None) is not None

    def redact_report(self, text: str) -> str:
        return redact_crash_report_text(text)

    def _trim(self) -> None:
        ordered = self.list_crash_reports()
        for report in ordered[self.max_reports :]:
            self._reports.pop(report.id, None)


def redact_crash_report_text(text: str) -> str:
    redacted = text
    redacted = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[REDACTED_API_KEY]", redacted)
    redacted = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+", r"\1[REDACTED]", redacted)
    redacted = re.sub(r"(?i)(api[_-]?key|llm_api_key|openai_api_key)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", redacted)
    redacted = re.sub(r"(?i)(password|database_password)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", redacted)
    redacted = re.sub(r"(?is)(raw[_ -]?env|environment)\s*[:=]\s*\{.*?\}", r"\1=[REDACTED]", redacted)
    redacted = re.sub(r"(?is)(raw[_ -]?prompt|prompt)\s*[:=]\s*([\"']).*?\2", r"\1=[REDACTED_PROMPT]", redacted)
    redacted = re.sub(r"(?i)hidden fact[^.\n]*", "hidden fact [REDACTED]", redacted)
    redacted = re.sub(r"(?i)hidden_fact_text\s*[:=]\s*[^\n]+", "hidden_fact_text=[REDACTED]", redacted)
    return redacted


def _safe_token(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.:-]", "_", value.strip())
    return cleaned[:80] or "unknown"


def _safe_context_key(key: str) -> bool:
    lowered = key.lower()
    forbidden = ("api", "key", "secret", "password", "env", "prompt", "hidden")
    return not any(token in lowered for token in forbidden)
