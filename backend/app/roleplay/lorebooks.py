import json
import re
from enum import StrEnum
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity


class LorebookImportError(ValueError):
    """Raised when a local lorebook import is invalid or unsafe."""


class LorebookInputFormat(StrEnum):
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    AUTO = "auto"


class LorebookEntryCategory(StrEnum):
    FLAVOR_LORE = "flavor_lore"
    STRUCTURED_FACT = "structured_fact_candidate"
    HIDDEN_FACT = "hidden_fact_candidate"
    UNSAFE = "unsafe_entry"


class LorebookImport(BaseModel):
    raw_content: str = Field(min_length=1)
    input_format: LorebookInputFormat = LorebookInputFormat.AUTO
    source_name: str | None = None


class LorebookEntry(BaseModel):
    key: str | None = None
    keywords: list[str] = Field(default_factory=list)
    content: str = Field(min_length=1)
    insertion_order: int = 100
    enabled: bool = True
    comment: str | None = None
    note: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("keywords", "tags", mode="before")
    @classmethod
    def _coerce_string_list(cls, value: object) -> object:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in re.split(r"[,;\n]", value) if item.strip()]
        return value

    @model_validator(mode="before")
    @classmethod
    def _accept_tavern_aliases(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "key" not in normalized and "keys" in normalized:
            keys = normalized.get("keys")
            if isinstance(keys, list) and keys:
                normalized["key"] = str(keys[0])
                normalized.setdefault("keywords", [str(item) for item in keys])
        if "keywords" not in normalized and "key" in normalized:
            normalized["keywords"] = [str(normalized["key"])]
        if "content" not in normalized and "text" in normalized:
            normalized["content"] = normalized["text"]
        if "comment" not in normalized and "comments" in normalized:
            normalized["comment"] = normalized["comments"]
        return normalized


class ClassifiedLorebookEntry(BaseModel):
    category: LorebookEntryCategory
    key: str | None = None
    keywords: list[str] = Field(default_factory=list)
    insertion_order: int = 100
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)
    safe_summary: str
    reason: str


class LorebookImportReport(BaseModel):
    ok: bool
    source_format: LorebookInputFormat
    total_entries: int
    flavor_lore: list[ClassifiedLorebookEntry] = Field(default_factory=list)
    structured_fact_candidate: list[ClassifiedLorebookEntry] = Field(default_factory=list)
    hidden_fact_candidate: list[ClassifiedLorebookEntry] = Field(default_factory=list)
    unsafe_entry: list[ClassifiedLorebookEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LorebookApplyRequest(LorebookImport):
    world_id: str
    confirm_save: bool = False


class LorebookApplyReport(BaseModel):
    applied: bool
    world_id: str
    validation_ok: bool = False
    import_report: LorebookImportReport
    validation: ValidationReport
    warnings: list[str] = Field(default_factory=list)


class LorebookClassifier:
    """Deterministic rule classifier for tavern-style lorebook/world-info entries."""

    def parse_lorebook(self, request: LorebookImport) -> tuple[list[LorebookEntry], LorebookInputFormat]:
        raw = request.raw_content.strip()
        if _looks_like_remote_reference(raw):
            raise LorebookImportError("Remote URLs are not supported by lorebook import.")
        if _looks_like_executable_payload(raw):
            raise LorebookImportError("Executable/script-like lorebook payloads are not supported.")

        formats = (
            [request.input_format]
            if request.input_format != LorebookInputFormat.AUTO
            else [LorebookInputFormat.JSON, LorebookInputFormat.YAML, LorebookInputFormat.TEXT]
        )
        errors: list[str] = []
        for input_format in formats:
            try:
                return self._parse_as(raw, input_format), input_format
            except LorebookImportError as exc:
                errors.append(str(exc))
        raise LorebookImportError("; ".join(errors) or "Unable to parse lorebook.")

    def classify_entry(self, entry: LorebookEntry) -> ClassifiedLorebookEntry:
        category, reason = self._classify(entry)
        return ClassifiedLorebookEntry(
            category=category,
            key=entry.key,
            keywords=entry.keywords,
            insertion_order=entry.insertion_order,
            enabled=entry.enabled,
            tags=sorted(set(entry.tags)),
            safe_summary=_safe_summary(entry.content),
            reason=reason,
        )

    def detect_hidden_fact(self, entry: LorebookEntry) -> bool:
        lower = _entry_text(entry).lower()
        return _contains_hidden_marker(lower)

    def detect_world_fact(self, entry: LorebookEntry) -> bool:
        lower = _entry_text(entry).lower()
        return _contains_structured_fact_marker(lower)

    def detect_flavor_lore(self, entry: LorebookEntry) -> bool:
        return not self.detect_hidden_fact(entry) and not self.detect_world_fact(entry) and not self.detect_prompt_injection(entry)

    def detect_prompt_injection(self, entry: LorebookEntry) -> bool:
        return _contains_unsafe_instruction(_entry_text(entry).lower())

    def generate_import_report(self, request: LorebookImport) -> LorebookImportReport:
        entries, source_format = self.parse_lorebook(request)
        classified = [self.classify_entry(entry) for entry in entries if entry.enabled]
        disabled_count = len([entry for entry in entries if not entry.enabled])
        report = LorebookImportReport(
            ok=not any(entry.category == LorebookEntryCategory.UNSAFE for entry in classified),
            source_format=source_format,
            total_entries=len(entries),
            flavor_lore=[entry for entry in classified if entry.category == LorebookEntryCategory.FLAVOR_LORE],
            structured_fact_candidate=[entry for entry in classified if entry.category == LorebookEntryCategory.STRUCTURED_FACT],
            hidden_fact_candidate=[entry for entry in classified if entry.category == LorebookEntryCategory.HIDDEN_FACT],
            unsafe_entry=[entry for entry in classified if entry.category == LorebookEntryCategory.UNSAFE],
            warnings=[],
        )
        if disabled_count:
            report.warnings.append(f"{disabled_count} disabled lorebook entries were ignored.")
        if report.unsafe_entry:
            report.warnings.append("Unsafe prompt/control entries are quarantined and cannot be applied.")
        return report

    def validate_import(self, request: LorebookImport) -> LorebookImportReport:
        return self.generate_import_report(request)

    def apply_to_world(
        self,
        request: LorebookApplyRequest,
        authoring_service: ContentAuthoringService,
    ) -> LorebookApplyReport:
        report = self.generate_import_report(request)
        validation = ValidationReport(world_id=request.world_id)
        warnings = list(report.warnings)
        if report.unsafe_entry:
            validation.add(
                ValidationSeverity.ERROR,
                "lorebook_import",
                "Lorebook contains unsafe prompt/control entries.",
                code="lorebook_contains_unsafe_entries",
                suggestion="Remove unsafe entries before applying.",
            )
            return LorebookApplyReport(
                applied=False,
                world_id=request.world_id,
                validation_ok=False,
                import_report=report,
                validation=validation,
                warnings=warnings,
            )
        if not request.confirm_save:
            validation.add(
                ValidationSeverity.ERROR,
                "lorebook_import",
                "Lorebook import apply requires explicit confirm_save=true.",
                code="lorebook_apply_requires_confirmation",
            )
            return LorebookApplyReport(
                applied=False,
                world_id=request.world_id,
                validation_ok=False,
                import_report=report,
                validation=validation,
                warnings=warnings,
            )
        if not report.structured_fact_candidate and not report.hidden_fact_candidate:
            validation.add(
                ValidationSeverity.ERROR,
                "lorebook_import",
                "Lorebook apply has no structured or hidden fact candidates to save.",
                code="lorebook_apply_no_fact_candidates",
            )
            return LorebookApplyReport(
                applied=False,
                world_id=request.world_id,
                validation_ok=False,
                import_report=report,
                validation=validation,
                warnings=warnings,
            )
        content = self._facts_yaml_with_candidates(request.world_id, report, authoring_service)
        validation = authoring_service.write_file(request.world_id, "facts.yaml", content)
        return LorebookApplyReport(
            applied=validation.ok,
            world_id=request.world_id,
            validation_ok=validation.ok,
            import_report=report,
            validation=validation,
            warnings=warnings,
        )

    def _classify(self, entry: LorebookEntry) -> tuple[LorebookEntryCategory, str]:
        if self.detect_prompt_injection(entry):
            return LorebookEntryCategory.UNSAFE, "Prompt/control instruction is unsafe and cannot enter RP prompts."
        if self.detect_hidden_fact(entry):
            return LorebookEntryCategory.HIDDEN_FACT, "Secret/spoiler markers require hidden fact visibility."
        if self.detect_world_fact(entry):
            return LorebookEntryCategory.STRUCTURED_FACT, "World-rule/canon text must become structured content first."
        return LorebookEntryCategory.FLAVOR_LORE, "Flavor lore is non-authoritative style/context only."

    def _parse_as(self, raw: str, input_format: LorebookInputFormat) -> list[LorebookEntry]:
        if input_format == LorebookInputFormat.JSON:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise LorebookImportError(f"Invalid JSON lorebook: {exc}") from exc
        elif input_format == LorebookInputFormat.YAML:
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError as exc:
                raise LorebookImportError(f"Invalid YAML lorebook: {exc}") from exc
        elif input_format == LorebookInputFormat.TEXT:
            data = _parse_text_lorebook(raw)
        else:
            raise LorebookImportError(f"Unsupported input format: {input_format}")
        return _coerce_entries(data)

    def _facts_yaml_with_candidates(
        self,
        world_id: str,
        report: LorebookImportReport,
        authoring_service: ContentAuthoringService,
    ) -> str:
        existing = yaml.safe_load(authoring_service.read_file(world_id, "facts.yaml")) or {}
        if not isinstance(existing, dict):
            raise LorebookImportError("facts.yaml must contain a mapping.")
        facts = existing.get("facts", [])
        if not isinstance(facts, list):
            raise LorebookImportError("facts.yaml must contain a facts list.")
        existing_ids = {fact.get("id") for fact in facts if isinstance(fact, dict)}
        for entry in report.structured_fact_candidate:
            fact_id = _unique_fact_id(entry, existing_ids)
            existing_ids.add(fact_id)
            facts.append(
                {
                    "id": fact_id,
                    "text": entry.safe_summary,
                    "visibility": "public",
                    "known_by": ["player"],
                    "tags": sorted(set(entry.tags + ["lorebook_import", "structured_fact_candidate"])),
                }
            )
        for entry in report.hidden_fact_candidate:
            fact_id = _unique_fact_id(entry, existing_ids)
            existing_ids.add(fact_id)
            facts.append(
                {
                    "id": fact_id,
                    "text": entry.safe_summary,
                    "visibility": "hidden",
                    "known_by": [],
                    "tags": sorted(set(entry.tags + ["lorebook_import", "hidden_fact_candidate"])),
                }
            )
        existing["facts"] = facts
        return yaml.safe_dump(existing, sort_keys=False, allow_unicode=True)


def preview_lorebook_import(request: LorebookImport) -> LorebookImportReport:
    return LorebookClassifier().generate_import_report(request)


def validate_lorebook_import(request: LorebookImport) -> LorebookImportReport:
    return LorebookClassifier().validate_import(request)


def apply_lorebook_import(
    request: LorebookApplyRequest,
    authoring_service: ContentAuthoringService,
) -> LorebookApplyReport:
    return LorebookClassifier().apply_to_world(request, authoring_service)


def flavor_context_from_lorebook_report(report: LorebookImportReport) -> list[str]:
    return [entry.safe_summary for entry in report.flavor_lore if entry.enabled]


def _coerce_entries(data: object) -> list[LorebookEntry]:
    if isinstance(data, dict):
        raw_entries = data.get("entries") or data.get("lorebook") or data.get("world_info") or data.get("items")
        if raw_entries is None:
            raw_entries = [data]
    elif isinstance(data, list):
        raw_entries = data
    else:
        raise LorebookImportError("Lorebook payload must be a mapping, list, or text.")
    if not isinstance(raw_entries, list):
        raise LorebookImportError("Lorebook entries must be a list.")
    entries: list[LorebookEntry] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            raise LorebookImportError("Lorebook entry must be a mapping/object.")
        try:
            entries.append(LorebookEntry.model_validate(raw_entry))
        except ValidationError as exc:
            raise LorebookImportError(f"Invalid lorebook entry: {exc}") from exc
    return entries


def _parse_text_lorebook(raw: str) -> dict[str, list[dict[str, object]]]:
    entries: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    body: list[str] = []
    for line in raw.splitlines():
        if line.strip().startswith("### "):
            if current is not None:
                current["content"] = "\n".join(body).strip()
                entries.append(current)
            key = line.strip()[4:].strip()
            current = {"key": key, "keywords": [key], "content": ""}
            body = []
        else:
            body.append(line)
    if current is None:
        first_line = raw.splitlines()[0].strip() if raw.splitlines() else "lore"
        current = {"key": first_line[:48] or "lore", "keywords": [first_line[:48] or "lore"], "content": raw}
    else:
        current["content"] = "\n".join(body).strip()
    entries.append(current)
    return {"entries": entries}


def _entry_text(entry: LorebookEntry) -> str:
    return " ".join(
        [
            entry.key or "",
            " ".join(entry.keywords),
            entry.content,
            entry.comment or "",
            entry.note or "",
            " ".join(entry.tags),
        ]
    )


def _contains_unsafe_instruction(lower: str) -> bool:
    markers = (
        "ignore previous",
        "ignore all previous",
        "developer message",
        "system prompt",
        "jailbreak",
        "bypass",
        "override",
        "api key",
        "write gamestate",
        "modify gamestate",
        "state_delta",
        "hidden rule",
        "system instruction",
        "always reveal",
    )
    return any(marker in lower for marker in markers)


def _contains_hidden_marker(lower: str) -> bool:
    markers = ("secret", "hidden", "spoiler", "true identity", "real identity", "classified", "unknown to player")
    return any(marker in lower for marker in markers)


def _contains_structured_fact_marker(lower: str) -> bool:
    markers = (
        "world rule",
        "canon",
        "fact:",
        "location:",
        "npc:",
        "item:",
        "quest:",
        "faction:",
        "reputation:",
        "law:",
    )
    return any(marker in lower for marker in markers)


def _looks_like_remote_reference(raw: str) -> bool:
    return bool(re.search(r"https?://", raw, flags=re.IGNORECASE))


def _looks_like_executable_payload(raw: str) -> bool:
    lowered = raw.lower()
    return any(marker in lowered for marker in ("<script", "<?php", "#!/bin/", "powershell.exe", "cmd.exe"))


def _safe_summary(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= 140:
        return cleaned
    return f"{cleaned[:137]}..."


def _unique_fact_id(entry: ClassifiedLorebookEntry, existing_ids: set[object]) -> str:
    base = _slugify(entry.key or (entry.keywords[0] if entry.keywords else entry.safe_summary[:32]))
    candidate = f"lore_{base}"
    suffix = 2
    while candidate in existing_ids:
        candidate = f"lore_{base}_{suffix}"
        suffix += 1
    return candidate


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip().lower()).strip("_")
    return slug[:48] or "entry"
