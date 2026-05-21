from __future__ import annotations

import hashlib
import re
from pathlib import Path


FORBIDDEN_PACKAGE_NAMES = {
    ".env",
    "env",
    "secrets.yaml",
    "secrets.yml",
    "secrets.json",
}
FORBIDDEN_PACKAGE_SUFFIXES = {
    ".bat",
    ".cmd",
    ".com",
    ".db",
    ".dll",
    ".exe",
    ".js",
    ".log",
    ".msi",
    ".ps1",
    ".py",
    ".sh",
    ".sqlite",
    ".sqlite3",
}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY"),
    re.compile(r"(?i)(api[_-]?key|authorization|bearer\s+)"),
)


def safe_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value))


def validate_relative_package_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    parts = Path(normalized).parts
    if Path(normalized).is_absolute() or normalized.startswith("/") or ".." in parts or normalized in {"", "."}:
        raise ValueError(f"Unsafe package path: {path}")
    name = Path(normalized).name.lower()
    if name in FORBIDDEN_PACKAGE_NAMES or Path(name).suffix.lower() in FORBIDDEN_PACKAGE_SUFFIXES:
        raise ValueError(f"Forbidden package file: {path}")
    if normalized.lower().startswith(("logs/", "cache/", "caches/", "node_modules/", "frontend/dist/", "backups/", "crash-reports/")):
        raise ValueError(f"Forbidden package directory: {path}")
    return normalized


def contains_secret_text(text: str) -> bool:
    lowered = text.lower()
    if any(marker in lowered for marker in ("sk-test", "sk-fake", "sk-redacted", "sk-placeholder", "sk-example")):
        return False
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def redact_text(text: str) -> str:
    redacted = re.sub(r"sk-[A-Za-z0-9_-]{8,}", "[REDACTED_API_KEY]", text)
    redacted = re.sub(r"BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY.*?END (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY", "[REDACTED_PRIVATE_KEY]", redacted, flags=re.S)
    return redacted


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def redacted_path(path: str | Path) -> str:
    p = Path(path)
    if len(p.parts) <= 2:
        return p.name
    return f".../{p.parent.name}/{p.name}"

