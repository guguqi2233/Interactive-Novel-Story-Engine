from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.desktop.studio_policy import redact_desktop_secret_text


LogLevel = Literal["debug", "info", "warning", "error", "unknown"]


class SafeLogEntry(BaseModel):
    timestamp: str
    level: LogLevel = "unknown"
    category: str = "local"
    source: str
    message: str
    redacted: bool = False


class LocalLogListResponse(BaseModel):
    local_only: bool = True
    debug_included: bool = False
    logs: list[SafeLogEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LocalLogService:
    def __init__(self, repo_root: Path, *, debug_enabled: bool = False) -> None:
        self.repo_root = repo_root.resolve()
        self.logs_root = (self.repo_root / "logs").resolve()
        self.debug_enabled = debug_enabled

    def redact_log_line(self, line: str) -> tuple[str, bool]:
        redacted = redact_desktop_secret_text(line)
        return redacted.text, redacted.redaction_count > 0

    def list_safe_logs(
        self,
        *,
        level: str | None = None,
        category: str | None = None,
        limit: int = 100,
        include_debug: bool = False,
    ) -> LocalLogListResponse:
        if include_debug and not self.debug_enabled:
            return LocalLogListResponse(debug_included=False, warnings=["debug_logs_require_ENABLE_DEBUG_API"])
        entries: list[SafeLogEntry] = []
        if not self.logs_root.exists():
            return LocalLogListResponse(debug_included=include_debug and self.debug_enabled, logs=[])
        for path in sorted(self.logs_root.glob("*.log")):
            if not self._allowed_log_path(path):
                continue
            entries.extend(self._read_log_file(path, limit=max(1, limit)))
        filtered = self.filter_logs(entries, level=level, category=category)
        return LocalLogListResponse(debug_included=include_debug and self.debug_enabled, logs=filtered[-limit:])

    def filter_logs(
        self,
        logs: list[SafeLogEntry],
        *,
        level: str | None = None,
        category: str | None = None,
    ) -> list[SafeLogEntry]:
        filtered = logs
        if level:
            filtered = [entry for entry in filtered if entry.level == level]
        if category:
            filtered = [entry for entry in filtered if entry.category == category]
        return filtered

    def _allowed_log_path(self, path: Path) -> bool:
        try:
            resolved = path.resolve()
        except OSError:
            return False
        return self.logs_root == resolved.parent and resolved.suffix.lower() == ".log"

    def _read_log_file(self, path: Path, *, limit: int) -> list[SafeLogEntry]:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
        except OSError:
            return []
        entries: list[SafeLogEntry] = []
        for line in lines:
            message, redacted = self.redact_log_line(line)
            entries.append(
                SafeLogEntry(
                    timestamp=datetime.now(UTC).isoformat(),
                    level=_level_for_line(message),
                    category=_category_for_path(path),
                    source=path.name,
                    message=message[:1000],
                    redacted=redacted,
                )
            )
        return entries


def _level_for_line(line: str) -> LogLevel:
    lowered = line.lower()
    if "error" in lowered or "traceback" in lowered:
        return "error"
    if "warn" in lowered:
        return "warning"
    if "debug" in lowered:
        return "debug"
    if "info" in lowered:
        return "info"
    return "unknown"


def _category_for_path(path: Path) -> str:
    name = path.name.lower()
    if "backend" in name:
        return "backend"
    if "frontend" in name:
        return "frontend"
    return "desktop"
