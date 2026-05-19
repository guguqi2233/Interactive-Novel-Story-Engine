from __future__ import annotations

import base64
import re
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any
from zipfile import BadZipFile, ZipFile

import yaml
from pydantic import BaseModel, Field, model_validator

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport
from app.roleplay.lorebooks import (
    ClassifiedLorebookEntry,
    LorebookClassifier,
    LorebookImport,
    LorebookImportError,
)


class BatchLorebookSource(BaseModel):
    source_name: str
    raw_content: str
    input_format: str = "auto"


class BatchLorebookClassificationRequest(BaseModel):
    target_world_id: str
    sources: list[BatchLorebookSource] = Field(default_factory=list)
    zip_base64: str | None = None
    selected_keys: list[str] = Field(default_factory=list)
    authoring_debug: bool = False

    @model_validator(mode="after")
    def validate_has_input(self) -> "BatchLorebookClassificationRequest":
        if not self.sources and not self.zip_base64:
            raise ValueError("Batch lorebook classification requires sources or zip_base64.")
        return self


class BatchLorebookUnsafeEntry(BaseModel):
    source_name: str
    key: str | None = None
    reason: str
    safe_summary: str = ""


class BatchLorebookClassificationReport(BaseModel):
    target_world_id: str
    total_entries: int = 0
    flavor_lore: list[ClassifiedLorebookEntry] = Field(default_factory=list)
    structured_fact_candidates: list[ClassifiedLorebookEntry] = Field(default_factory=list)
    hidden_fact_candidates: list[ClassifiedLorebookEntry] = Field(default_factory=list)
    unsafe_entries: list[BatchLorebookUnsafeEntry] = Field(default_factory=list)
    duplicate_keys: list[str] = Field(default_factory=list)
    prompt_injection_warnings: list[str] = Field(default_factory=list)
    validation: ValidationReport | None = None
    yaml_draft: str = ""
    writes_to_disk: bool = False
    normal_report: bool = True


def preview_batch_lorebook_classification(request: BatchLorebookClassificationRequest) -> BatchLorebookClassificationReport:
    return _build_report(request, service=None, selected_only=False)


def apply_batch_lorebook_classification_draft(
    request: BatchLorebookClassificationRequest,
    service: ContentAuthoringService,
) -> BatchLorebookClassificationReport:
    return _build_report(request, service=service, selected_only=True)


def _build_report(
    request: BatchLorebookClassificationRequest,
    *,
    service: ContentAuthoringService | None,
    selected_only: bool,
) -> BatchLorebookClassificationReport:
    classifier = LorebookClassifier()
    all_flavor: list[ClassifiedLorebookEntry] = []
    all_structured: list[ClassifiedLorebookEntry] = []
    all_hidden: list[ClassifiedLorebookEntry] = []
    unsafe: list[BatchLorebookUnsafeEntry] = []
    key_counts: dict[str, int] = {}
    total = 0
    for source in _collect_sources(request):
        try:
            report = classifier.generate_import_report(
                LorebookImport(
                    raw_content=source.raw_content,
                    input_format=source.input_format,  # type: ignore[arg-type]
                    source_name=source.source_name,
                )
            )
        except (LorebookImportError, ValueError) as exc:
            unsafe.append(BatchLorebookUnsafeEntry(source_name=source.source_name, reason=str(exc)))
            continue
        total += report.total_entries
        for entry in [*report.flavor_lore, *report.structured_fact_candidate, *report.hidden_fact_candidate, *report.unsafe_entry]:
            if entry.key:
                key_counts[entry.key] = key_counts.get(entry.key, 0) + 1
        all_flavor.extend(report.flavor_lore)
        all_structured.extend(report.structured_fact_candidate)
        all_hidden.extend(report.hidden_fact_candidate)
        unsafe.extend(
            BatchLorebookUnsafeEntry(
                source_name=source.source_name,
                key=entry.key,
                reason=entry.reason,
                safe_summary=entry.safe_summary,
            )
            for entry in report.unsafe_entry
        )
    duplicate_keys = sorted(key for key, count in key_counts.items() if count > 1 and key)
    selected = set(request.selected_keys)
    structured = _filter_selected(all_structured, selected, selected_only)
    hidden = _filter_selected(all_hidden, selected, selected_only)
    yaml_draft = ""
    validation: ValidationReport | None = None
    if service is not None:
        raw_yaml_draft = _facts_yaml_draft(request.target_world_id, structured, hidden, service, redact_hidden_text=False)
        validation = service.validate_drafts(request.target_world_id, {"facts.yaml": raw_yaml_draft})
        yaml_draft = raw_yaml_draft if request.authoring_debug else _facts_yaml_draft(
            request.target_world_id,
            structured,
            hidden,
            service,
            redact_hidden_text=True,
        )
    hidden_report = all_hidden if request.authoring_debug else [_redact_hidden_entry(entry) for entry in all_hidden]
    return BatchLorebookClassificationReport(
        target_world_id=request.target_world_id,
        total_entries=total,
        flavor_lore=all_flavor,
        structured_fact_candidates=all_structured,
        hidden_fact_candidates=hidden_report,
        unsafe_entries=unsafe,
        duplicate_keys=duplicate_keys,
        prompt_injection_warnings=[entry.reason for entry in unsafe if "prompt" in entry.reason.lower() or "control" in entry.reason.lower()],
        validation=validation,
        yaml_draft=yaml_draft,
        normal_report=not request.authoring_debug,
    )


def _collect_sources(request: BatchLorebookClassificationRequest) -> list[BatchLorebookSource]:
    sources = list(request.sources)
    if request.zip_base64:
        sources.extend(_sources_from_zip(request.zip_base64))
    return sources


def _sources_from_zip(zip_base64: str) -> list[BatchLorebookSource]:
    try:
        archive = ZipFile(BytesIO(base64.b64decode(zip_base64)))
    except (ValueError, BadZipFile) as exc:
        raise ValueError("Invalid lorebook zip payload.") from exc
    sources: list[BatchLorebookSource] = []
    with archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            path = _safe_zip_path(info.filename)
            if path.suffix.lower() in {".exe", ".bat", ".cmd", ".com", ".dll", ".js", ".mjs", ".ps1", ".py", ".sh", ".vbs"}:
                raise ValueError("Lorebook zip contains executable content.")
            if path.suffix.lower() not in {".json", ".yaml", ".yml", ".txt"}:
                continue
            sources.append(BatchLorebookSource(source_name=str(path), raw_content=archive.read(info).decode("utf-8")))
    return sources


def _facts_yaml_draft(
    world_id: str,
    structured: list[ClassifiedLorebookEntry],
    hidden: list[ClassifiedLorebookEntry],
    service: ContentAuthoringService,
    *,
    redact_hidden_text: bool,
) -> str:
    existing = yaml.safe_load(service.read_file(world_id, "facts.yaml")) or {}
    facts = existing.get("facts", []) if isinstance(existing, dict) else []
    existing_ids = {str(fact.get("id", "")) for fact in facts if isinstance(fact, dict)}
    for entry in structured:
        fact_id = _unique_fact_id(entry, existing_ids)
        existing_ids.add(fact_id)
        facts.append(
            {
                "id": fact_id,
                "text": entry.safe_summary,
                "visibility": "public",
                "known_by": ["player"],
                "tags": sorted(set(entry.tags + ["batch_lorebook", "structured_fact_candidate"])),
            }
        )
    for entry in hidden:
        fact_id = _unique_fact_id(entry, existing_ids)
        existing_ids.add(fact_id)
        facts.append(
            {
                "id": fact_id,
                "text": "[redacted hidden lorebook entry]" if redact_hidden_text else entry.safe_summary,
                "visibility": "hidden",
                "known_by": [],
                "tags": sorted(set(entry.tags + ["batch_lorebook", "hidden_fact_candidate"])),
            }
        )
    return yaml.safe_dump({"facts": facts}, sort_keys=False, allow_unicode=True)


def _filter_selected(
    entries: list[ClassifiedLorebookEntry],
    selected: set[str],
    selected_only: bool,
) -> list[ClassifiedLorebookEntry]:
    if not selected_only or not selected:
        return entries
    return [entry for entry in entries if (entry.key or "") in selected]


def _redact_hidden_entry(entry: ClassifiedLorebookEntry) -> ClassifiedLorebookEntry:
    return entry.model_copy(update={"safe_summary": "[redacted hidden lorebook entry]"})


def _safe_zip_path(name: str) -> PurePosixPath:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if normalized.startswith("/") or normalized.startswith("~") or ".." in path.parts:
        raise ValueError("Lorebook zip path escapes package root.")
    return path


def _unique_fact_id(entry: ClassifiedLorebookEntry, existing_ids: set[str]) -> str:
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", (entry.key or entry.safe_summary[:32]).lower()).strip("_") or "lore"
    candidate = f"batch_lore_{base[:44]}"
    suffix = 2
    while candidate in existing_ids:
        candidate = f"batch_lore_{base[:40]}_{suffix}"
        suffix += 1
    return candidate
