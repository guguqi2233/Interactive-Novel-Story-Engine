from __future__ import annotations

import base64
import re
from io import BytesIO
from pathlib import PurePosixPath
from typing import Any
from zipfile import BadZipFile, ZipFile

from pydantic import BaseModel, Field, model_validator

from app.engine.content.character_pack_builder import (
    CharacterPack,
    CharacterPackFactCandidate,
    CharacterPackManifest,
)
from app.roleplay.character_cards import (
    CharacterCardImport,
    CharacterCardImportError,
    CharacterCardImportReport,
    CharacterCardImporter,
)


class BatchCharacterCardSource(BaseModel):
    source_name: str
    raw_content: str
    input_format: str = "auto"


class BatchCharacterCardImportRequest(BaseModel):
    target_world_id: str
    sources: list[BatchCharacterCardSource] = Field(default_factory=list)
    pasted_texts: list[str] = Field(default_factory=list)
    zip_base64: str | None = None
    selected_names: list[str] = Field(default_factory=list)
    pack_id: str | None = None
    pack_name: str | None = None

    @model_validator(mode="after")
    def validate_has_input(self) -> "BatchCharacterCardImportRequest":
        if not self.sources and not self.pasted_texts and not self.zip_base64:
            raise ValueError("Batch character import requires sources, pasted_texts, or zip_base64.")
        return self


class BatchCharacterCardUnsafeEntry(BaseModel):
    source_name: str
    reason: str
    safe_summary: str = ""


class BatchCharacterCardImportReport(BaseModel):
    target_world_id: str
    parsed_count: int = 0
    failed_count: int = 0
    unsafe_count: int = 0
    duplicate_names: list[str] = Field(default_factory=list)
    candidate_characters: list[dict[str, Any]] = Field(default_factory=list)
    rp_profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)
    voice_profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)
    example_dialogues: list[dict[str, Any]] = Field(default_factory=list)
    unsafe_entries: list[BatchCharacterCardUnsafeEntry] = Field(default_factory=list)
    character_pack_draft: CharacterPack
    writes_to_disk: bool = False
    active_game_state_modified: bool = False


def preview_batch_character_card_import(request: BatchCharacterCardImportRequest) -> BatchCharacterCardImportReport:
    return _build_batch_report(request, selected_only=False)


def apply_batch_character_card_import_draft(request: BatchCharacterCardImportRequest) -> BatchCharacterCardImportReport:
    return _build_batch_report(request, selected_only=True)


def export_batch_character_card_pack(request: BatchCharacterCardImportRequest) -> CharacterPack:
    return apply_batch_character_card_import_draft(request).character_pack_draft


def _build_batch_report(request: BatchCharacterCardImportRequest, *, selected_only: bool) -> BatchCharacterCardImportReport:
    importer = CharacterCardImporter()
    sources = _collect_sources(request)
    selected = set(request.selected_names)
    seen_names: dict[str, int] = {}
    reports: list[CharacterCardImportReport] = []
    failures: list[BatchCharacterCardUnsafeEntry] = []
    unsafe: list[BatchCharacterCardUnsafeEntry] = []
    candidates: list[dict[str, Any]] = []
    rp_profiles: dict[str, dict[str, Any]] = {}
    voice_profiles: dict[str, dict[str, Any]] = {}
    examples: list[dict[str, Any]] = []
    facts: list[CharacterPackFactCandidate] = []
    for source in sources:
        try:
            report = importer.generate_import_report(
                CharacterCardImport(
                    raw_content=source.raw_content,
                    input_format=source.input_format,  # type: ignore[arg-type]
                    source_name=source.source_name,
                )
            )
        except (CharacterCardImportError, ValueError) as exc:
            failures.append(BatchCharacterCardUnsafeEntry(source_name=source.source_name, reason=str(exc)))
            continue
        reports.append(report)
        name = report.normalized_card.name
        seen_names[name] = seen_names.get(name, 0) + 1
        if report.unsafe_or_unsupported_entries:
            unsafe.extend(
                BatchCharacterCardUnsafeEntry(
                    source_name=source.source_name,
                    reason=entry.reason,
                    safe_summary=entry.safe_summary,
                )
                for entry in report.unsafe_or_unsupported_entries
            )
        if selected_only and selected and name not in selected:
            continue
        npc_id = _unique_id(name, seen_names[name])
        character = _candidate_character(npc_id, report)
        candidates.append(character)
        rp_profiles[npc_id] = character["rp_profile"]
        voice_profiles[npc_id] = character["voice_profile"]
        examples.extend(_example_dialogues(npc_id, report))
        facts.extend(_fact_candidates(npc_id, report))
    duplicate_names = sorted(name for name, count in seen_names.items() if count > 1)
    pack = CharacterPack(
        manifest=CharacterPackManifest(
            pack_id=request.pack_id or f"{request.target_world_id}_batch_characters",
            name=request.pack_name or f"{request.target_world_id} Batch Character Pack",
            source_world_id=request.target_world_id,
            exported_at="draft",
            character_ids=[str(candidate["id"]) for candidate in candidates],
            safe_export=True,
            includes_hidden_facts=False,
        ),
        characters=candidates,
        rp_profiles=rp_profiles,
        voice_profiles=voice_profiles,
        example_dialogues=examples,
        fact_candidates=facts,
    )
    return BatchCharacterCardImportReport(
        target_world_id=request.target_world_id,
        parsed_count=len(reports),
        failed_count=len(failures),
        unsafe_count=len(unsafe),
        duplicate_names=duplicate_names,
        candidate_characters=candidates,
        rp_profiles=rp_profiles,
        voice_profiles=voice_profiles,
        example_dialogues=examples,
        unsafe_entries=[*failures, *unsafe],
        character_pack_draft=pack,
    )


def _collect_sources(request: BatchCharacterCardImportRequest) -> list[BatchCharacterCardSource]:
    sources = list(request.sources)
    for index, text in enumerate(request.pasted_texts):
        if text.strip():
            sources.append(BatchCharacterCardSource(source_name=f"pasted_{index + 1}", raw_content=text))
    if request.zip_base64:
        sources.extend(_sources_from_zip(request.zip_base64))
    return sources


def _sources_from_zip(zip_base64: str) -> list[BatchCharacterCardSource]:
    try:
        raw = base64.b64decode(zip_base64)
        archive = ZipFile(BytesIO(raw))
    except (ValueError, BadZipFile) as exc:
        raise ValueError("Invalid character card zip payload.") from exc
    sources: list[BatchCharacterCardSource] = []
    with archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            path = _safe_zip_path(info.filename)
            if path.suffix.lower() in {".exe", ".bat", ".cmd", ".com", ".dll", ".js", ".mjs", ".ps1", ".py", ".sh", ".vbs"}:
                raise ValueError("Character card zip contains executable content.")
            if path.suffix.lower() not in {".json", ".yaml", ".yml", ".txt"}:
                continue
            content = archive.read(info).decode("utf-8")
            sources.append(BatchCharacterCardSource(source_name=str(path), raw_content=content))
    return sources


def _safe_zip_path(name: str) -> PurePosixPath:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if normalized.startswith("/") or normalized.startswith("~") or ".." in path.parts:
        raise ValueError("Character card zip path escapes package root.")
    return path


def _candidate_character(npc_id: str, report: CharacterCardImportReport) -> dict[str, Any]:
    return {
        "id": npc_id,
        "name": report.normalized_card.name,
        "location_id": "start",
        "personality": report.rp_profile_candidate.personality_summary or report.rp_profile_candidate.description,
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
        "example_dialogue_refs": [f"{npc_id}_example_{index + 1}" for index, _ in enumerate(report.example_dialogue_candidate.lines)],
    }


def _example_dialogues(npc_id: str, report: CharacterCardImportReport) -> list[dict[str, Any]]:
    return [
        {
            "id": f"{npc_id}_example_{index + 1}",
            "character_id": npc_id,
            "lines": [line],
            "visibility": "prompt_safe",
            "fact_policy": "style_only",
        }
        for index, line in enumerate(report.example_dialogue_candidate.lines)
    ]


def _fact_candidates(npc_id: str, report: CharacterCardImportReport) -> list[CharacterPackFactCandidate]:
    candidates: list[CharacterPackFactCandidate] = []
    for index, fact in enumerate([*report.flavor_lore_candidate, *report.structured_fact_candidate]):
        candidates.append(
            CharacterPackFactCandidate(
                id=f"{npc_id}_candidate_fact_{index + 1}",
                text=fact.safe_summary,
                visibility="public",
                tags=["batch_import_candidate"],
            )
        )
    return candidates


def _unique_id(name: str, occurrence: int) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", name.strip().lower()).strip("_") or "imported_character"
    suffix = f"_{occurrence}" if occurrence > 1 else ""
    return f"{slug[:42]}{suffix}"
