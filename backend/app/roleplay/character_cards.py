import json
import re
from enum import StrEnum
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity


class CharacterCardImportError(ValueError):
    """Raised when a local character card import is invalid or unsafe."""


class CharacterCardInputFormat(StrEnum):
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"
    AUTO = "auto"


class CharacterCardEntryCategory(StrEnum):
    RP_PROFILE = "rp_profile_candidate"
    VOICE_PROFILE = "voice_profile_candidate"
    EXAMPLE_DIALOGUE = "example_dialogue_candidate"
    FLAVOR_LORE = "flavor_lore_candidate"
    STRUCTURED_FACT = "structured_fact_candidate"
    HIDDEN_FACT = "hidden_fact_candidate"
    UNSAFE = "unsafe_or_unsupported_entries"


class CharacterCardImport(BaseModel):
    raw_content: str = Field(min_length=1)
    input_format: CharacterCardInputFormat = CharacterCardInputFormat.AUTO
    source_name: str | None = None


class NormalizedCharacterCard(BaseModel):
    name: str
    description: str = ""
    personality: str = ""
    scenario: str = ""
    first_message: str = ""
    example_dialogue: list[str] = Field(default_factory=list)
    creator_notes: str = ""
    system_prompt: str = ""
    tags: list[str] = Field(default_factory=list)
    extra_fields: dict[str, str] = Field(default_factory=dict)

    @field_validator("example_dialogue", "tags", mode="before")
    @classmethod
    def _coerce_list(cls, value: object) -> object:
        if value is None:
            return []
        if isinstance(value, str):
            return [line.strip() for line in value.splitlines() if line.strip()]
        if isinstance(value, list):
            coerced: list[str] = []
            for item in value:
                if isinstance(item, str):
                    coerced.append(item)
                elif isinstance(item, dict) and len(item) == 1:
                    key, child = next(iter(item.items()))
                    coerced.append(f"{key}: {child}")
                else:
                    coerced.append(_stringify(item))
            return coerced
        return value


class CharacterCardClassifiedEntry(BaseModel):
    category: CharacterCardEntryCategory
    source_field: str
    text: str
    safe_summary: str
    reason: str


class RPProfileCandidate(BaseModel):
    name: str
    description: str = ""
    personality_summary: str = ""
    scenario_summary: str = ""
    tags: list[str] = Field(default_factory=list)


class VoiceProfileCandidate(BaseModel):
    name: str
    style_notes: list[str] = Field(default_factory=list)
    first_message: str = ""


class ExampleDialogueCandidate(BaseModel):
    lines: list[str] = Field(default_factory=list)


class CandidateWorldFact(BaseModel):
    source_field: str
    text: str
    visibility: str
    safe_summary: str


class CharacterCardImportReport(BaseModel):
    ok: bool
    source_format: CharacterCardInputFormat
    normalized_card: NormalizedCharacterCard
    rp_profile_candidate: RPProfileCandidate
    voice_profile_candidate: VoiceProfileCandidate
    example_dialogue_candidate: ExampleDialogueCandidate
    flavor_lore_candidate: list[CandidateWorldFact] = Field(default_factory=list)
    structured_fact_candidate: list[CandidateWorldFact] = Field(default_factory=list)
    hidden_fact_candidate: list[CandidateWorldFact] = Field(default_factory=list)
    unsafe_or_unsupported_entries: list[CharacterCardClassifiedEntry] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CharacterCardApplyRequest(CharacterCardImport):
    world_id: str
    candidate_npc_id: str | None = None
    confirm_save: bool = False


class CharacterCardApplyReport(BaseModel):
    applied: bool
    world_id: str
    npc_id: str | None = None
    validation_ok: bool = False
    import_report: CharacterCardImportReport
    validation: ValidationReport
    warnings: list[str] = Field(default_factory=list)


class CharacterCardImporter:
    """Converts untrusted character cards into safe authoring candidates."""

    def parse_card(self, card: CharacterCardImport) -> tuple[dict[str, Any], CharacterCardInputFormat]:
        raw = card.raw_content.strip()
        if _looks_like_remote_reference(raw):
            raise CharacterCardImportError("Remote URLs are not supported by character card import.")
        if _looks_like_executable_payload(raw):
            raise CharacterCardImportError("Executable/script-like character card payloads are not supported.")

        formats = (
            [card.input_format]
            if card.input_format != CharacterCardInputFormat.AUTO
            else [CharacterCardInputFormat.JSON, CharacterCardInputFormat.YAML, CharacterCardInputFormat.TEXT]
        )
        errors: list[str] = []
        for input_format in formats:
            try:
                return self._parse_as(raw, input_format), input_format
            except CharacterCardImportError as exc:
                errors.append(str(exc))
        raise CharacterCardImportError("; ".join(errors) or "Unable to parse character card.")

    def normalize_card(self, payload: dict[str, Any]) -> NormalizedCharacterCard:
        aliases = {
            "name": ("name", "char_name", "character_name"),
            "description": ("description", "desc", "character_description"),
            "personality": ("personality", "personality_summary", "traits"),
            "scenario": ("scenario", "setting", "context"),
            "first_message": ("first_message", "first_mes", "greeting"),
            "example_dialogue": ("example_dialogue", "mes_example", "example_messages"),
            "creator_notes": ("creator_notes", "creatorcomment", "creator_notes_multiline"),
            "system_prompt": ("system_prompt", "system", "system_instruction"),
            "tags": ("tags", "tagline"),
        }
        normalized: dict[str, Any] = {}
        consumed: set[str] = set()
        for target, keys in aliases.items():
            for key in keys:
                if key in payload:
                    normalized[target] = payload[key]
                    consumed.add(key)
                    break
        normalized.setdefault("name", "Imported Character")
        normalized["extra_fields"] = {
            str(key): _stringify(value)
            for key, value in payload.items()
            if key not in consumed and value not in (None, "")
        }
        try:
            return NormalizedCharacterCard.model_validate(normalized)
        except ValidationError as exc:
            raise CharacterCardImportError(f"Invalid character card fields: {exc}") from exc

    def classify_fields(self, card: NormalizedCharacterCard) -> list[CharacterCardClassifiedEntry]:
        entries: list[CharacterCardClassifiedEntry] = []
        field_values: dict[str, str] = {
            "description": card.description,
            "personality": card.personality,
            "scenario": card.scenario,
            "first_message": card.first_message,
            "creator_notes": card.creator_notes,
            "system_prompt": card.system_prompt,
            **card.extra_fields,
        }
        for field_name, text in field_values.items():
            text = text.strip()
            if not text:
                continue
            category, reason = _classify_text(field_name, text)
            entries.append(
                CharacterCardClassifiedEntry(
                    category=category,
                    source_field=field_name,
                    text=text,
                    safe_summary=_safe_summary(text),
                    reason=reason,
                )
            )
        for index, line in enumerate(card.example_dialogue):
            entries.append(
                CharacterCardClassifiedEntry(
                    category=CharacterCardEntryCategory.EXAMPLE_DIALOGUE,
                    source_field=f"example_dialogue[{index}]",
                    text=line,
                    safe_summary=_safe_summary(line),
                    reason="Example dialogue is style reference only.",
                )
            )
        return entries

    def generate_candidate_rp_profile(self, card: NormalizedCharacterCard) -> RPProfileCandidate:
        return RPProfileCandidate(
            name=card.name,
            description=card.description,
            personality_summary=card.personality,
            scenario_summary=card.scenario,
            tags=sorted(set(card.tags + ["imported_character_card"])),
        )

    def generate_candidate_voice_profile(self, card: NormalizedCharacterCard) -> VoiceProfileCandidate:
        notes = [item for item in [card.personality, card.description] if item]
        return VoiceProfileCandidate(name=card.name, style_notes=notes[:3], first_message=card.first_message)

    def generate_candidate_world_facts(
        self,
        entries: list[CharacterCardClassifiedEntry],
    ) -> tuple[list[CandidateWorldFact], list[CandidateWorldFact], list[CandidateWorldFact]]:
        flavor: list[CandidateWorldFact] = []
        structured: list[CandidateWorldFact] = []
        hidden: list[CandidateWorldFact] = []
        for entry in entries:
            fact = CandidateWorldFact(
                source_field=entry.source_field,
                text=entry.text,
                visibility="flavor",
                safe_summary=entry.safe_summary,
            )
            if entry.category == CharacterCardEntryCategory.FLAVOR_LORE:
                flavor.append(fact)
            elif entry.category == CharacterCardEntryCategory.STRUCTURED_FACT:
                structured.append(fact.model_copy(update={"visibility": "candidate_structured"}))
            elif entry.category == CharacterCardEntryCategory.HIDDEN_FACT:
                hidden.append(fact.model_copy(update={"visibility": "hidden_candidate"}))
        return flavor, structured, hidden

    def generate_import_report(self, card: CharacterCardImport) -> CharacterCardImportReport:
        payload, source_format = self.parse_card(card)
        normalized = self.normalize_card(payload)
        entries = self.classify_fields(normalized)
        flavor, structured, hidden = self.generate_candidate_world_facts(entries)
        unsafe = [entry for entry in entries if entry.category == CharacterCardEntryCategory.UNSAFE]
        example_lines = [entry.text for entry in entries if entry.category == CharacterCardEntryCategory.EXAMPLE_DIALOGUE]
        warnings = [
            "system_prompt and creator_notes are treated as untrusted authoring notes and never enter RP prompts."
        ] if unsafe else []
        return CharacterCardImportReport(
            ok=not unsafe,
            source_format=source_format,
            normalized_card=normalized,
            rp_profile_candidate=self.generate_candidate_rp_profile(normalized),
            voice_profile_candidate=self.generate_candidate_voice_profile(normalized),
            example_dialogue_candidate=ExampleDialogueCandidate(lines=example_lines),
            flavor_lore_candidate=flavor,
            structured_fact_candidate=structured,
            hidden_fact_candidate=hidden,
            unsafe_or_unsupported_entries=unsafe,
            warnings=warnings,
        )

    def validate_import(self, card: CharacterCardImport) -> CharacterCardImportReport:
        return self.generate_import_report(card)

    def apply_to_world(
        self,
        request: CharacterCardApplyRequest,
        authoring_service: ContentAuthoringService,
    ) -> CharacterCardApplyReport:
        report = self.generate_import_report(request)
        validation = ValidationReport(world_id=request.world_id)
        warnings = list(report.warnings)
        if report.unsafe_or_unsupported_entries:
            validation.add(
                ValidationSeverity.ERROR,
                "character_card_import",
                "Character card contains unsafe or unsupported prompt/control entries.",
                code="character_card_contains_unsafe_entries",
                suggestion="Remove or quarantine system_prompt/creator_notes before applying.",
            )
            return CharacterCardApplyReport(
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
                "character_card_import",
                "Character card import apply requires explicit confirm_save=true.",
                code="character_card_apply_requires_confirmation",
            )
            return CharacterCardApplyReport(
                applied=False,
                world_id=request.world_id,
                validation_ok=False,
                import_report=report,
                validation=validation,
                warnings=warnings,
            )
        npc_id = request.candidate_npc_id or _slugify(report.normalized_card.name)
        proposed_npcs = self._npcs_yaml_with_candidate(request.world_id, npc_id, report, authoring_service)
        validation = authoring_service.write_file(request.world_id, "npcs.yaml", proposed_npcs)
        return CharacterCardApplyReport(
            applied=validation.ok,
            world_id=request.world_id,
            npc_id=npc_id if validation.ok else None,
            validation_ok=validation.ok,
            import_report=report,
            validation=validation,
            warnings=warnings,
        )

    def _parse_as(self, raw: str, input_format: CharacterCardInputFormat) -> dict[str, Any]:
        if input_format == CharacterCardInputFormat.JSON:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise CharacterCardImportError(f"Invalid JSON character card: {exc}") from exc
        elif input_format == CharacterCardInputFormat.YAML:
            try:
                data = yaml.safe_load(raw)
            except yaml.YAMLError as exc:
                raise CharacterCardImportError(f"Invalid YAML character card: {exc}") from exc
        elif input_format == CharacterCardInputFormat.TEXT:
            data = _parse_text_card(raw)
        else:
            raise CharacterCardImportError(f"Unsupported input format: {input_format}")
        if not isinstance(data, dict):
            raise CharacterCardImportError("Character card payload must be a mapping/object.")
        return data

    def _npcs_yaml_with_candidate(
        self,
        world_id: str,
        npc_id: str,
        report: CharacterCardImportReport,
        authoring_service: ContentAuthoringService,
    ) -> str:
        if not _is_safe_id(npc_id):
            raise CharacterCardImportError(f"Invalid candidate NPC id: {npc_id}")
        existing = yaml.safe_load(authoring_service.read_file(world_id, "npcs.yaml")) or {}
        if not isinstance(existing, dict):
            raise CharacterCardImportError("npcs.yaml must contain a mapping.")
        npcs = existing.get("npcs", [])
        if not isinstance(npcs, list):
            raise CharacterCardImportError("npcs.yaml must contain an npcs list.")
        if any(isinstance(npc, dict) and npc.get("id") == npc_id for npc in npcs):
            raise CharacterCardImportError(f"NPC already exists: {npc_id}")
        start_location_id = _read_start_location_id(authoring_service, world_id)
        npcs.append(
            {
                "id": npc_id,
                "name": report.normalized_card.name,
                "location_id": start_location_id,
                "personality": report.rp_profile_candidate.personality_summary
                or report.rp_profile_candidate.description
                or "Imported roleplay character candidate.",
                "knowledge": [],
                "visible": True,
                "hidden": False,
                "rp_profile": {
                    "public_persona": report.rp_profile_candidate.description,
                    "attachment_style": "",
                    "trust_expression_style": "",
                    "conflict_expression_style": "",
                    "intimacy_expression_style": "",
                    "deception_style": "",
                    "boundaries": [],
                },
                "voice_profile": {
                    "tone": "",
                    "sentence_length": "mixed",
                    "vocabulary_style": "",
                    "catchphrases": [],
                    "speech_habits": report.voice_profile_candidate.style_notes,
                    "silence_style": "",
                    "emotional_tells": [],
                },
                "dialogue_style": report.voice_profile_candidate.first_message,
                "example_dialogue_refs": [],
            }
        )
        existing["npcs"] = npcs
        return yaml.safe_dump(existing, sort_keys=False, allow_unicode=True)


def preview_character_card_import(card: CharacterCardImport) -> CharacterCardImportReport:
    return CharacterCardImporter().generate_import_report(card)


def validate_character_card_import(card: CharacterCardImport) -> CharacterCardImportReport:
    return CharacterCardImporter().validate_import(card)


def apply_character_card_import(
    request: CharacterCardApplyRequest,
    authoring_service: ContentAuthoringService,
) -> CharacterCardApplyReport:
    return CharacterCardImporter().apply_to_world(request, authoring_service)


def _parse_text_card(raw: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    current_key = "description"
    chunks: dict[str, list[str]] = {current_key: []}
    for line in raw.splitlines():
        match = re.match(r"^\s*([A-Za-z_ -]{2,32})\s*:\s*(.*)$", line)
        if match:
            current_key = match.group(1).strip().lower().replace(" ", "_").replace("-", "_")
            chunks.setdefault(current_key, [])
            if match.group(2).strip():
                chunks[current_key].append(match.group(2).strip())
            continue
        chunks.setdefault(current_key, []).append(line)
    for key, lines in chunks.items():
        text = "\n".join(line for line in lines if line.strip()).strip()
        if text:
            fields[key] = text
    if "name" not in fields:
        first_line = raw.splitlines()[0].strip() if raw.splitlines() else "Imported Character"
        fields["name"] = first_line[:80] or "Imported Character"
    return fields


def _classify_text(field_name: str, text: str) -> tuple[CharacterCardEntryCategory, str]:
    lower = text.lower()
    if field_name in {"system_prompt", "creator_notes"} or _contains_unsafe_instruction(lower):
        return CharacterCardEntryCategory.UNSAFE, "Untrusted prompt/control instruction is not allowed in RP context."
    if _contains_hidden_marker(lower):
        return CharacterCardEntryCategory.HIDDEN_FACT, "Spoiler/secret markers require hidden fact review."
    if field_name in {"scenario"} or _contains_structured_fact_marker(lower):
        return CharacterCardEntryCategory.STRUCTURED_FACT, "Scenario-like text may become structured fact only after review."
    if field_name in {"description", "personality", "first_message"}:
        return CharacterCardEntryCategory.FLAVOR_LORE, "Roleplay flavor is non-authoritative."
    return CharacterCardEntryCategory.FLAVOR_LORE, "Imported text is treated as non-authoritative flavor."


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
        "control instruction",
    )
    return any(marker in lower for marker in markers)


def _contains_hidden_marker(lower: str) -> bool:
    markers = ("secret", "hidden", "spoiler", "true identity", "real identity", "classified")
    return any(marker in lower for marker in markers)


def _contains_structured_fact_marker(lower: str) -> bool:
    markers = ("location", "quest", "faction", "npc", "item", "world fact", "canon")
    return any(marker in lower for marker in markers)


def _looks_like_remote_reference(raw: str) -> bool:
    return bool(re.search(r"https?://", raw, flags=re.IGNORECASE))


def _looks_like_executable_payload(raw: str) -> bool:
    lowered = raw.lower()
    return any(marker in lowered for marker in ("<script", "<?php", "#!/bin/", "powershell.exe", "cmd.exe"))


def _safe_summary(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= 120:
        return cleaned
    return f"{cleaned[:117]}..."


def _stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip().lower()).strip("_")
    return slug[:48] or "imported_character"


def _is_safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-"} for character in value)


def _read_start_location_id(authoring_service: ContentAuthoringService, world_id: str) -> str:
    manifest = yaml.safe_load(authoring_service.read_file(world_id, "manifest.yaml")) or {}
    if isinstance(manifest, dict) and isinstance(manifest.get("start_location_id"), str):
        return manifest["start_location_id"]
    return "start"
