from __future__ import annotations

import json
import re
from enum import StrEnum
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.core.world_state import ExampleDialogue, ExampleDialogueVisibility, FactVisibility, NPCState
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.llm.prompt_profiles import PromptProfile
from app.roleplay.character_cards import (
    CharacterCardApplyReport,
    CharacterCardApplyRequest,
    CharacterCardImport,
    CharacterCardImportError,
    CharacterCardImportReport,
    CharacterCardImporter,
)
from app.roleplay.example_dialogues import ExampleDialogueBundle, ExampleDialogueDraftRequest
from app.roleplay.lorebooks import (
    LorebookApplyReport,
    LorebookApplyRequest,
    LorebookClassifier,
    LorebookImport,
    LorebookImportError,
    LorebookImportReport,
)


class TavernCompatibilityError(ValueError):
    """Raised when a tavern compatibility request is invalid or unsafe."""


class TavernResourceType(StrEnum):
    CHARACTER_CARD = "character_card"
    LOREBOOK = "lorebook"
    EXAMPLE_DIALOGUE = "example_dialogue"
    PROMPT_PRESET = "prompt_preset"


class TavernExportType(StrEnum):
    CHARACTER_CARD = "character_card"
    LOREBOOK = "lorebook"
    PROMPT_PROFILE = "prompt_profile"


class TavernExportMode(StrEnum):
    SAFE = "safe"
    AUTHORING_DEBUG = "authoring_debug"


class TavernCompatibilityFinding(BaseModel):
    code: str
    severity: str = "warning"
    message: str
    safe_details: dict[str, str] = Field(default_factory=dict)


class TavernCompatibilityReport(BaseModel):
    ok: bool
    resource_type: TavernResourceType | TavernExportType
    mode: str = "preview"
    parsed: bool = False
    classified: bool = False
    unsafe_detected: bool = False
    writes_to_disk: bool = False
    requires_explicit_apply: bool = True
    findings: list[TavernCompatibilityFinding] = Field(default_factory=list)
    character_card_report: CharacterCardImportReport | None = None
    lorebook_report: LorebookImportReport | None = None
    example_dialogue_preview: dict[str, Any] | None = None
    prompt_profile_candidate: PromptProfile | None = None
    export_payload: dict[str, Any] | None = None


class TavernCompatibilityImportRequest(BaseModel):
    resource_type: TavernResourceType
    raw_content: str = Field(min_length=1)
    input_format: str = "auto"
    source_name: str | None = None
    world_id: str | None = None
    confirm_save: bool = False

    @field_validator("source_name")
    @classmethod
    def validate_source_name(cls, value: str | None) -> str | None:
        if value is not None and not _safe_source_name(value):
            raise ValueError("source_name must not contain path traversal or path separators")
        return value


class TavernCompatibilityApplyRequest(TavernCompatibilityImportRequest):
    world_id: str
    confirm_save: bool = False
    candidate_id: str | None = None


class TavernCompatibilityApplyReport(BaseModel):
    applied: bool
    report: TavernCompatibilityReport
    character_apply: CharacterCardApplyReport | None = None
    lorebook_apply: LorebookApplyReport | None = None
    validation: ValidationReport


class TavernCompatibilityExportRequest(BaseModel):
    export_type: TavernExportType
    world_id: str
    npc_id: str | None = None
    prompt_profile_id: str | None = None
    mode: TavernExportMode = TavernExportMode.SAFE


class TavernCompatibilityService:
    """Local-only tavern compatibility adapter.

    It routes untrusted resources through deterministic parsers/classifiers and
    returns safe previews. Apply is explicit and authoring-only. Export omits
    API keys, raw GameState, save data, and hidden facts in safe mode.
    """

    def preview_import(self, request: TavernCompatibilityImportRequest) -> TavernCompatibilityReport:
        _reject_unsafe_raw(request.raw_content)
        if request.resource_type == TavernResourceType.CHARACTER_CARD:
            return self._preview_character_card(request)
        if request.resource_type == TavernResourceType.LOREBOOK:
            return self._preview_lorebook(request)
        if request.resource_type == TavernResourceType.EXAMPLE_DIALOGUE:
            return self._preview_example_dialogue(request)
        if request.resource_type == TavernResourceType.PROMPT_PRESET:
            return self._preview_prompt_preset(request)
        raise TavernCompatibilityError(f"Unsupported tavern resource type: {request.resource_type}")

    def apply_import(
        self,
        request: TavernCompatibilityApplyRequest,
        authoring_service: ContentAuthoringService,
    ) -> TavernCompatibilityApplyReport:
        preview = self.preview_import(request)
        validation = ValidationReport(world_id=request.world_id)
        if not request.confirm_save:
            validation.add(
                ValidationSeverity.ERROR,
                "tavern_import",
                "Tavern compatibility import apply requires explicit confirm_save=true.",
                code="tavern_apply_requires_confirmation",
            )
            return TavernCompatibilityApplyReport(applied=False, report=preview, validation=validation)
        if preview.unsafe_detected:
            validation.add(
                ValidationSeverity.ERROR,
                "tavern_import",
                "Unsafe tavern resource entries must be removed before apply.",
                code="tavern_apply_contains_unsafe_entries",
            )
            return TavernCompatibilityApplyReport(applied=False, report=preview, validation=validation)
        if request.resource_type == TavernResourceType.CHARACTER_CARD:
            apply = CharacterCardImporter().apply_to_world(
                CharacterCardApplyRequest(
                    raw_content=request.raw_content,
                    input_format=request.input_format,  # type: ignore[arg-type]
                    source_name=request.source_name,
                    world_id=request.world_id,
                    candidate_npc_id=request.candidate_id,
                    confirm_save=True,
                ),
                authoring_service,
            )
            return TavernCompatibilityApplyReport(
                applied=apply.applied,
                report=preview.model_copy(update={"writes_to_disk": apply.applied, "mode": "apply"}),
                character_apply=apply,
                validation=apply.validation,
            )
        if request.resource_type == TavernResourceType.LOREBOOK:
            apply = LorebookClassifier().apply_to_world(
                LorebookApplyRequest(
                    raw_content=request.raw_content,
                    input_format=request.input_format,  # type: ignore[arg-type]
                    source_name=request.source_name,
                    world_id=request.world_id,
                    confirm_save=True,
                ),
                authoring_service,
            )
            return TavernCompatibilityApplyReport(
                applied=apply.applied,
                report=preview.model_copy(update={"writes_to_disk": apply.applied, "mode": "apply"}),
                lorebook_apply=apply,
                validation=apply.validation,
            )
        validation.add(
            ValidationSeverity.ERROR,
            "tavern_import",
            f"Apply is not supported for {request.resource_type}; save through the dedicated authoring editor.",
            code="tavern_apply_unsupported_resource_type",
        )
        return TavernCompatibilityApplyReport(applied=False, report=preview, validation=validation)

    def export_resource(
        self,
        request: TavernCompatibilityExportRequest,
        authoring_service: ContentAuthoringService,
        prompt_profiles: list[PromptProfile],
    ) -> TavernCompatibilityReport:
        if request.export_type == TavernExportType.CHARACTER_CARD:
            return self._export_character_card(request, authoring_service)
        if request.export_type == TavernExportType.LOREBOOK:
            return self._export_lorebook(request, authoring_service)
        if request.export_type == TavernExportType.PROMPT_PROFILE:
            return self._export_prompt_profile(request, prompt_profiles)
        raise TavernCompatibilityError(f"Unsupported tavern export type: {request.export_type}")

    def _preview_character_card(self, request: TavernCompatibilityImportRequest) -> TavernCompatibilityReport:
        report = CharacterCardImporter().generate_import_report(
            CharacterCardImport(
                raw_content=request.raw_content,
                input_format=request.input_format,  # type: ignore[arg-type]
                source_name=request.source_name,
            )
        )
        return TavernCompatibilityReport(
            ok=report.ok,
            resource_type=TavernResourceType.CHARACTER_CARD,
            parsed=True,
            classified=True,
            unsafe_detected=bool(report.unsafe_or_unsupported_entries),
            findings=_findings_from_character_report(report),
            character_card_report=report,
        )

    def _preview_lorebook(self, request: TavernCompatibilityImportRequest) -> TavernCompatibilityReport:
        report = LorebookClassifier().generate_import_report(
            LorebookImport(
                raw_content=request.raw_content,
                input_format=request.input_format,  # type: ignore[arg-type]
                source_name=request.source_name,
            )
        )
        return TavernCompatibilityReport(
            ok=report.ok,
            resource_type=TavernResourceType.LOREBOOK,
            parsed=True,
            classified=True,
            unsafe_detected=bool(report.unsafe_entry),
            findings=_findings_from_lorebook_report(report),
            lorebook_report=report,
        )

    def _preview_example_dialogue(self, request: TavernCompatibilityImportRequest) -> TavernCompatibilityReport:
        entries = _parse_example_dialogue_payload(request.raw_content)
        preview = None
        findings: list[TavernCompatibilityFinding] = []
        unsafe = any(entry.visibility == ExampleDialogueVisibility.UNSAFE for entry in entries)
        if request.world_id:
            validation = ValidationReport(world_id=request.world_id)
            draft = ExampleDialogueDraftRequest(entries=entries)
            preview = {
                "world_id": request.world_id,
                "entry_count": len(entries),
                "validation": validation.model_dump(mode="json"),
                "entries": [entry.model_dump(mode="json") for entry in draft.entries],
            }
        if unsafe:
            findings.append(
                TavernCompatibilityFinding(
                    code="example_dialogue_contains_unsafe_entries",
                    severity="error",
                    message="Unsafe example dialogue is quarantined and cannot enter RP prompts.",
                )
            )
        return TavernCompatibilityReport(
            ok=not unsafe,
            resource_type=TavernResourceType.EXAMPLE_DIALOGUE,
            parsed=True,
            classified=True,
            unsafe_detected=unsafe,
            findings=findings,
            example_dialogue_preview=preview or {"entry_count": len(entries)},
        )

    def _preview_prompt_preset(self, request: TavernCompatibilityImportRequest) -> TavernCompatibilityReport:
        payload = _parse_mapping_payload(request.raw_content)
        try:
            profile = PromptProfile.model_validate(payload)
        except ValidationError as exc:
            raise TavernCompatibilityError(f"Invalid prompt preset: {exc}") from exc
        return TavernCompatibilityReport(
            ok=True,
            resource_type=TavernResourceType.PROMPT_PRESET,
            parsed=True,
            classified=True,
            prompt_profile_candidate=profile,
        )

    def _export_character_card(
        self,
        request: TavernCompatibilityExportRequest,
        authoring_service: ContentAuthoringService,
    ) -> TavernCompatibilityReport:
        if not request.npc_id:
            raise TavernCompatibilityError("npc_id is required for character card export")
        npc = _read_npc(authoring_service, request.world_id, request.npc_id)
        payload = _npc_to_safe_character_card(npc, request.mode)
        return _safe_export_report(TavernExportType.CHARACTER_CARD, payload, request.mode)

    def _export_lorebook(
        self,
        request: TavernCompatibilityExportRequest,
        authoring_service: ContentAuthoringService,
    ) -> TavernCompatibilityReport:
        payload = _safe_lorebook_export(authoring_service, request.world_id, request.mode)
        return _safe_export_report(TavernExportType.LOREBOOK, payload, request.mode)

    def _export_prompt_profile(
        self,
        request: TavernCompatibilityExportRequest,
        prompt_profiles: list[PromptProfile],
    ) -> TavernCompatibilityReport:
        profile_id = request.prompt_profile_id or "default_safe"
        profile = next((profile for profile in prompt_profiles if profile.id == profile_id), None)
        if profile is None:
            raise TavernCompatibilityError(f"Prompt profile not found: {profile_id}")
        payload = {
            "type": "prompt_profile",
            "profile": profile.model_dump(mode="json", exclude_none=True),
            "warnings": ["Prompt profiles are style/config metadata and cannot change visibility or GameState."],
        }
        return _safe_export_report(TavernExportType.PROMPT_PROFILE, payload, request.mode)


def preview_tavern_import(request: TavernCompatibilityImportRequest) -> TavernCompatibilityReport:
    return TavernCompatibilityService().preview_import(request)


def apply_tavern_import(
    request: TavernCompatibilityApplyRequest,
    authoring_service: ContentAuthoringService,
) -> TavernCompatibilityApplyReport:
    return TavernCompatibilityService().apply_import(request, authoring_service)


def export_tavern_resource(
    request: TavernCompatibilityExportRequest,
    authoring_service: ContentAuthoringService,
    prompt_profiles: list[PromptProfile],
) -> TavernCompatibilityReport:
    return TavernCompatibilityService().export_resource(request, authoring_service, prompt_profiles)


def _reject_unsafe_raw(raw: str) -> None:
    if re.search(r"https?://", raw, flags=re.IGNORECASE):
        raise TavernCompatibilityError("Remote URLs are not supported by tavern compatibility import.")
    lowered = raw.lower()
    if any(marker in lowered for marker in ("<script", "<?php", "#!/bin/", "powershell.exe", "cmd.exe")):
        raise TavernCompatibilityError("Executable/script-like tavern resources are not supported.")


def _safe_source_name(value: str) -> bool:
    return ".." not in value and "/" not in value and "\\" not in value


def _findings_from_character_report(report: CharacterCardImportReport) -> list[TavernCompatibilityFinding]:
    findings: list[TavernCompatibilityFinding] = []
    if report.unsafe_or_unsupported_entries:
        findings.append(
            TavernCompatibilityFinding(
                code="character_card_unsafe_entries",
                severity="error",
                message="Character card contains unsafe prompt/control entries.",
                safe_details={"count": str(len(report.unsafe_or_unsupported_entries))},
            )
        )
    if report.hidden_fact_candidate:
        findings.append(
            TavernCompatibilityFinding(
                code="character_card_hidden_candidates",
                severity="warning",
                message="Character card contains hidden fact candidates that require visibility review.",
                safe_details={"count": str(len(report.hidden_fact_candidate))},
            )
        )
    return findings


def _findings_from_lorebook_report(report: LorebookImportReport) -> list[TavernCompatibilityFinding]:
    findings: list[TavernCompatibilityFinding] = []
    if report.unsafe_entry:
        findings.append(
            TavernCompatibilityFinding(
                code="lorebook_unsafe_entries",
                severity="error",
                message="Lorebook contains unsafe prompt/control entries.",
                safe_details={"count": str(len(report.unsafe_entry))},
            )
        )
    if report.hidden_fact_candidate:
        findings.append(
            TavernCompatibilityFinding(
                code="lorebook_hidden_candidates",
                severity="warning",
                message="Lorebook contains hidden fact candidates that are excluded from safe export/prompt context.",
                safe_details={"count": str(len(report.hidden_fact_candidate))},
            )
        )
    return findings


def _parse_mapping_payload(raw: str) -> dict[str, Any]:
    _reject_unsafe_raw(raw)
    for parser in (json.loads, yaml.safe_load):
        try:
            payload = parser(raw)
        except Exception:
            continue
        if isinstance(payload, dict):
            return payload
    raise TavernCompatibilityError("Payload must be JSON or YAML mapping.")


def _parse_example_dialogue_payload(raw: str) -> list[ExampleDialogue]:
    payload = _parse_mapping_payload(raw)
    try:
        if "example_dialogues" in payload:
            return ExampleDialogueBundle.model_validate(payload).example_dialogues
        return [ExampleDialogue.model_validate(payload)]
    except ValidationError as exc:
        raise TavernCompatibilityError(f"Invalid example dialogue payload: {exc}") from exc


def _read_npc(authoring_service: ContentAuthoringService, world_id: str, npc_id: str) -> NPCState:
    raw = yaml.safe_load(authoring_service.read_file(world_id, "npcs.yaml")) or {}
    for item in raw.get("npcs", []):
        if isinstance(item, dict) and item.get("id") == npc_id:
            payload = dict(item)
            payload.setdefault("location_id", "start")
            return NPCState.model_validate(payload)
    raise TavernCompatibilityError(f"NPC not found: {npc_id}")


def _npc_to_safe_character_card(npc: NPCState, mode: TavernExportMode) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": npc.id,
        "description": npc.rp_profile.public_persona,
        "personality": npc.dialogue_style or npc.voice_profile.tone,
        "first_message": "",
        "example_dialogue": [],
        "tags": ["local_studio_export", "rp_profile"],
        "voice_profile": npc.voice_profile.model_dump(mode="json"),
        "rp_profile": npc.rp_profile.model_dump(mode="json", exclude={"private_self_summary"}),
    }
    warnings = ["Safe export excludes private_self_summary, NPC secrets, runtime state, credentials, and save data."]
    if mode == TavernExportMode.AUTHORING_DEBUG and npc.rp_profile.private_self_summary:
        payload["rp_profile"]["private_self_summary_debug_only"] = "[authoring-debug omitted from safe prompts]"
        warnings.append("Authoring debug mode was requested; hidden/private details remain redacted in this export.")
    payload["warnings"] = warnings
    return payload


def _safe_lorebook_export(
    authoring_service: ContentAuthoringService,
    world_id: str,
    mode: TavernExportMode,
) -> dict[str, Any]:
    raw = yaml.safe_load(authoring_service.read_file(world_id, "facts.yaml")) or {}
    entries: list[dict[str, Any]] = []
    skipped_hidden = 0
    for fact in raw.get("facts", []):
        if not isinstance(fact, dict):
            continue
        visibility = fact.get("visibility", "hidden")
        if visibility != FactVisibility.PUBLIC.value and mode == TavernExportMode.SAFE:
            skipped_hidden += 1
            continue
        if visibility == FactVisibility.HIDDEN.value and mode == TavernExportMode.AUTHORING_DEBUG:
            skipped_hidden += 1
            continue
        entries.append(
            {
                "key": fact.get("id", "fact"),
                "keywords": [fact.get("id", "fact")],
                "content": fact.get("text", ""),
                "tags": sorted(set(fact.get("tags", []) + ["local_studio_export"])),
                "enabled": True,
            }
        )
    return {
        "type": "lorebook",
        "entries": entries,
        "warnings": [
            "Safe lorebook export excludes hidden facts, runtime state, save data, and credentials.",
            f"hidden_or_debug_entries_skipped={skipped_hidden}",
        ],
    }


def _safe_export_report(
    resource_type: TavernExportType,
    payload: dict[str, Any],
    mode: TavernExportMode,
) -> TavernCompatibilityReport:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).lower()
    findings: list[TavernCompatibilityFinding] = []
    if "sk-" in serialized or "api key" in serialized:
        findings.append(
            TavernCompatibilityFinding(
                code="export_sensitive_marker_detected",
                severity="error",
                message="Export payload contains sensitive configuration markers.",
            )
        )
    if "gamestate" in serialized or "state_delta" in serialized:
        findings.append(
            TavernCompatibilityFinding(
                code="export_raw_state_marker_detected",
                severity="error",
                message="Export payload contains raw state markers.",
            )
        )
    return TavernCompatibilityReport(
        ok=not any(finding.severity == "error" for finding in findings),
        resource_type=resource_type,
        mode=f"export:{mode.value}",
        parsed=True,
        classified=True,
        unsafe_detected=bool(findings),
        writes_to_disk=False,
        requires_explicit_apply=False,
        findings=findings,
        export_payload=payload,
    )
