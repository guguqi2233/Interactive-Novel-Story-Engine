from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field


class LocalReleaseNoteSummary(BaseModel):
    version: str
    title: str
    path: str
    summary: str
    upgrade_notes: list[str] = Field(default_factory=list)
    known_limitations: list[str] = Field(default_factory=list)


class LocalUpdateNotesIndex(BaseModel):
    local_only: bool = True
    current_version: str
    release_notes: list[LocalReleaseNoteSummary] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LocalUpdateNotesService:
    """Builds a safe, local-only release notes index from docs files."""

    def __init__(self, docs_root: Path, *, current_version: str = "v1.7") -> None:
        self.docs_root = docs_root.resolve()
        self.current_version = current_version

    def build_index(self) -> LocalUpdateNotesIndex:
        warnings: list[str] = []
        notes: list[LocalReleaseNoteSummary] = []
        for path in sorted(self.docs_root.glob("V*_RELEASE_NOTES.md"), key=_release_sort_key, reverse=True):
            try:
                resolved = path.resolve()
                if self.docs_root not in resolved.parents and resolved != self.docs_root:
                    warnings.append(f"Skipped release note outside docs root: {path.name}")
                    continue
                notes.append(self._read_release_note(resolved))
            except OSError:
                warnings.append(f"Could not read release note: {path.name}")

        for expected in _expected_versions():
            expected_path = self.docs_root / f"{expected.upper().replace('.', '_')}_RELEASE_NOTES.md"
            if not expected_path.exists():
                warnings.append(f"Missing release notes for {expected}.")

        return LocalUpdateNotesIndex(
            current_version=self.current_version,
            release_notes=notes,
            warnings=warnings,
        )

    def _read_release_note(self, path: Path) -> LocalReleaseNoteSummary:
        text = _redact_sensitive_text(path.read_text(encoding="utf-8"))
        title = _first_heading(text) or path.stem.replace("_", " ")
        version = _version_from_name(path.name)
        return LocalReleaseNoteSummary(
            version=version,
            title=title,
            path=f"docs/{path.name}",
            summary=_first_body_line(text),
            upgrade_notes=_extract_section_items(text, ["从", "升级注意事项", "Upgrade"]),
            known_limitations=_extract_section_items(text, ["已知限制", "Known Limitations"]),
        )


def _expected_versions() -> list[str]:
    return [f"v1.{index}" for index in range(0, 8)]


def _release_sort_key(path: Path) -> tuple[int, int]:
    match = re.search(r"V(\d+)_(\d+)_RELEASE_NOTES\.md$", path.name, re.IGNORECASE)
    if not match:
        return (-1, -1)
    return (int(match.group(1)), int(match.group(2)))


def _version_from_name(name: str) -> str:
    match = re.search(r"V(\d+)_(\d+)_RELEASE_NOTES\.md$", name, re.IGNORECASE)
    if not match:
        return name.removesuffix(".md").lower()
    return f"v{match.group(1)}.{match.group(2)}"


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return None


def _first_body_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped[:240]
    return "Local release notes are available."


def _extract_section_items(text: str, section_markers: list[str]) -> list[str]:
    lines = text.splitlines()
    collected: list[str] = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if in_section:
                break
            in_section = any(marker.lower() in stripped.lower() for marker in section_markers)
            continue
        if not in_section:
            continue
        if not stripped:
            continue
        cleaned = stripped.lstrip("-*0123456789. ").strip()
        if cleaned:
            collected.append(cleaned[:240])
        if len(collected) >= 8:
            break
    return collected


def _redact_sensitive_text(text: str) -> str:
    redacted = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[REDACTED_API_KEY]", text)
    redacted = re.sub(r"(?i)(api[_-]?key|authorization|llm_api_key)\s*[:=]\s*\S+", r"\1=[REDACTED]", redacted)
    return redacted
