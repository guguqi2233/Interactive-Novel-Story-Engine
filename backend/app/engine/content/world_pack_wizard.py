from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.validator import ValidationReport, ValidationSeverity, validate_world_pack
from app.engine.content.validation_gate import (
    AuthoringOperationType,
    AuthoringValidationGate,
    AuthoringValidationGateRequest,
)


class WorldPackWizardError(ValueError):
    """Raised when a world pack wizard operation is invalid or unsafe."""


class WorldPackWizardStep(StrEnum):
    BASIC_INFO = "basic_info"
    GENRE_TONE = "genre_tone"
    STARTING_REGION = "starting_region"
    SYSTEMS = "systems"
    PREVIEW = "preview"
    VALIDATE = "validate"
    APPLY = "apply"


class WorldPackWizardDraft(BaseModel):
    world_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1)
    genre: str = Field(default="fantasy", min_length=1)
    tone: str = Field(default="grounded", min_length=1)
    description: str = ""
    starting_location: str = Field(default="start", pattern=r"^[A-Za-z0-9_-]+$")
    location_seed_count: int = Field(default=1, ge=1, le=20)
    npc_seed_count: int = Field(default=1, ge=0, le=50)
    quest_seed_count: int = Field(default=1, ge=0, le=50)
    enabled_systems: list[str] = Field(default_factory=lambda: ["quests", "roleplay", "npc_simulation"])
    default_prompt_profile: str = "default_safe"
    default_quality_profile: str = "standard"
    llm_assisted: bool = False
    current_step: WorldPackWizardStep = WorldPackWizardStep.BASIC_INFO


class WorldPackWizardGeneratedFile(BaseModel):
    file_name: str
    content: str


class WorldPackWizardPreview(BaseModel):
    local_only: bool = True
    draft: WorldPackWizardDraft
    generated_files: list[WorldPackWizardGeneratedFile] = Field(default_factory=list)
    validation: ValidationReport | None = None
    writes_to_disk: bool = False
    applied: bool = False
    gate_allowed_to_save: bool = False
    confirmation_required: bool = False


class WorldPackWizardApplyRequest(BaseModel):
    draft: WorldPackWizardDraft
    confirm_apply: bool = False
    confirm_warnings: bool = False


class WorldPackWizard:
    def __init__(self, worlds_root: str | Path = "worlds") -> None:
        self.worlds_root = Path(worlds_root).resolve()
        self.validation_gate = AuthoringValidationGate(self.worlds_root)

    def create_draft(self, **values: Any) -> WorldPackWizardDraft:
        draft = WorldPackWizardDraft(**values)
        self._validate_draft_values(draft)
        return draft

    def preview_files(self, draft: WorldPackWizardDraft) -> WorldPackWizardPreview:
        report = ValidationReport(world_id=draft.world_id)
        self._add_draft_issues(draft, report)
        files = self._generate_files(draft) if not report.errors else []
        validation = self._validate_generated_world(draft, files, report)
        return WorldPackWizardPreview(
            draft=draft.model_copy(update={"current_step": WorldPackWizardStep.PREVIEW}),
            generated_files=files,
            validation=validation,
            writes_to_disk=False,
            applied=False,
        )

    def validate_draft(self, draft: WorldPackWizardDraft) -> WorldPackWizardPreview:
        preview = self.preview_files(draft)
        preview.draft.current_step = WorldPackWizardStep.VALIDATE
        return preview

    def apply_to_worlds_directory(self, request: WorldPackWizardApplyRequest) -> WorldPackWizardPreview:
        preview = self.validate_draft(request.draft)
        if preview.validation is None:
            preview.validation = ValidationReport(world_id=request.draft.world_id)
        if not request.confirm_apply:
            preview.validation.add(
                ValidationSeverity.ERROR,
                "world_pack_wizard.apply",
                "World Pack Wizard apply requires explicit confirmation.",
                code="world_pack_wizard_apply_requires_confirmation",
            )
            preview.confirmation_required = True
            return preview
        if not preview.validation.ok or (preview.validation.warnings and not request.confirm_warnings):
            preview.confirmation_required = bool(preview.validation.warnings and not request.confirm_warnings)
            return preview

        gate = self.validation_gate.evaluate(
            AuthoringValidationGateRequest(
                world_id=request.draft.world_id,
                operation_type=AuthoringOperationType.APPLY_TEMPLATE,
                draft_content={file.file_name: file.content for file in preview.generated_files},
                affected_files=[file.file_name for file in preview.generated_files],
                validation_report=preview.validation,
                confirm_warnings=request.confirm_warnings,
            )
        )
        preview.validation = gate.validation_report
        preview.gate_allowed_to_save = gate.allowed_to_save
        preview.confirmation_required = gate.confirmation_required
        if not gate.allowed_to_save:
            return preview

        world_path = self._safe_new_world_path(request.draft.world_id)
        world_path.mkdir(parents=True)
        try:
            for file in preview.generated_files:
                (world_path / file.file_name).write_text(file.content, encoding="utf-8")
            final_validation = validate_world_pack(request.draft.world_id, worlds_root=self.worlds_root)
            if not final_validation.ok:
                preview.validation = final_validation
                self._remove_created_world(world_path)
                return preview
        except Exception:
            self._remove_created_world(world_path)
            raise
        preview.validation = final_validation
        preview.writes_to_disk = True
        preview.applied = True
        preview.draft.current_step = WorldPackWizardStep.APPLY
        return preview

    def _validate_draft_values(self, draft: WorldPackWizardDraft) -> None:
        report = ValidationReport(world_id=draft.world_id)
        self._add_draft_issues(draft, report)
        if report.errors:
            raise WorldPackWizardError(report.errors[0].message)

    def _add_draft_issues(self, draft: WorldPackWizardDraft, report: ValidationReport) -> None:
        if (self.worlds_root / draft.world_id).exists():
            report.add(
                ValidationSeverity.ERROR,
                "world_pack_wizard.world_id",
                "World pack already exists.",
                code="world_pack_wizard_world_exists",
                ref_id=draft.world_id,
            )
        unsafe_text = "\n".join(
            [draft.description, draft.default_prompt_profile, draft.default_quality_profile, *draft.enabled_systems]
        ).lower()
        if any(token in unsafe_text for token in ("sk-", "api_key", "apikey", ".env", "http://", "https://")):
            report.add(
                ValidationSeverity.ERROR,
                "world_pack_wizard.safety",
                "World Pack Wizard drafts cannot contain remote URLs, API keys, or environment file references.",
                code="world_pack_wizard_unsafe_reference",
            )
        for system in draft.enabled_systems:
            if not system.replace("_", "").replace("-", "").isalnum():
                report.add(
                    ValidationSeverity.ERROR,
                    "world_pack_wizard.enabled_systems",
                    "Enabled system identifiers must be local slug values.",
                    code="world_pack_wizard_invalid_system",
                    ref_id=system,
                )

    def _validate_generated_world(
        self,
        draft: WorldPackWizardDraft,
        files: list[WorldPackWizardGeneratedFile],
        report: ValidationReport,
    ) -> ValidationReport:
        if report.errors:
            return report
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "worlds"
            world_path = root / draft.world_id
            world_path.mkdir(parents=True)
            for file in files:
                (world_path / file.file_name).write_text(file.content, encoding="utf-8")
            validation = validate_world_pack(draft.world_id, worlds_root=root)
        report.errors.extend(validation.errors)
        report.warnings.extend(validation.warnings)
        report.suggestions.extend(validation.suggestions)
        return report

    def _safe_new_world_path(self, world_id: str) -> Path:
        world_path = (self.worlds_root / world_id).resolve()
        if world_path.parent != self.worlds_root:
            raise WorldPackWizardError("World pack path escapes the worlds root.")
        if world_path.exists():
            raise WorldPackWizardError("World pack already exists.")
        return world_path

    def _generate_files(self, draft: WorldPackWizardDraft) -> list[WorldPackWizardGeneratedFile]:
        locations = self._locations(draft)
        npcs = self._npcs(draft, locations)
        quests = self._quests(draft, npcs)
        facts = self._facts(draft, locations, npcs)
        files: dict[str, dict[str, Any]] = {
            "manifest.yaml": {
                "world_id": draft.world_id,
                "name": draft.name,
                "version": "0.1.0",
                "start_location_id": draft.starting_location,
                "description": draft.description or f"A {draft.tone} {draft.genre} world pack draft.",
                "genre": draft.genre,
                "tone": draft.tone,
                "default_prompt_profile": draft.default_prompt_profile,
                "default_quality_profile": draft.default_quality_profile,
                "enabled_systems": draft.enabled_systems,
            },
            "locations.yaml": {"locations": locations},
            "npcs.yaml": {"npcs": npcs},
            "items.yaml": {"items": []},
            "quests.yaml": {"quests": quests},
            "facts.yaml": {"facts": facts},
        }
        if "factions" in draft.enabled_systems or "faction_conflict" in draft.enabled_systems:
            files["factions.yaml"] = {"factions": []}
        if "rumors" in draft.enabled_systems or "npc_simulation" in draft.enabled_systems:
            files["rumors.yaml"] = {"rumors": []}
        return [
            WorldPackWizardGeneratedFile(
                file_name=file_name,
                content=yaml.safe_dump(content, sort_keys=False, allow_unicode=True),
            )
            for file_name, content in files.items()
        ]

    def _locations(self, draft: WorldPackWizardDraft) -> list[dict[str, Any]]:
        count = max(1, draft.location_seed_count)
        locations: list[dict[str, Any]] = []
        for index in range(count):
            location_id = draft.starting_location if index == 0 else f"{draft.starting_location}_{index + 1}"
            exits = {}
            if index == 0 and count > 1:
                exits["east"] = f"{draft.starting_location}_2"
            elif index > 0:
                exits["west"] = draft.starting_location
            locations.append(
                {
                    "id": location_id,
                    "name": "Starting Region" if index == 0 else f"Seed Location {index + 1}",
                    "description": self._public_text(
                        f"A {draft.tone} {draft.genre} location prepared by the World Pack Wizard."
                    ),
                    "exits": exits,
                    "visual": {
                        "x": index * 160,
                        "y": 0,
                        "region_id": "starting_region",
                        "icon": "marker",
                        "color_tag": "starter",
                        "display_group": "starting_region",
                    },
                }
            )
        return locations

    def _npcs(self, draft: WorldPackWizardDraft, locations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        npcs: list[dict[str, Any]] = []
        for index in range(draft.npc_seed_count):
            npc_id = "guide" if index == 0 else f"npc_seed_{index + 1}"
            npcs.append(
                {
                    "id": npc_id,
                    "name": "Local Guide" if index == 0 else f"Seed NPC {index + 1}",
                    "location_id": locations[index % len(locations)]["id"],
                    "personality": self._public_text(f"{draft.tone.title()} and suitable for {draft.genre} play."),
                    "knowledge": ["world_pack_started"],
                    "goals": [],
                }
            )
        return npcs

    def _quests(self, draft: WorldPackWizardDraft, npcs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        quests: list[dict[str, Any]] = []
        npc_id = npcs[0]["id"] if npcs else "guide"
        for index in range(draft.quest_seed_count):
            quest_id = "first_steps" if index == 0 else f"seed_quest_{index + 1}"
            objective_id = f"begin_{quest_id}"
            quests.append(
                {
                    "id": quest_id,
                    "title": "First Steps" if index == 0 else f"Seed Quest {index + 1}",
                    "description": self._public_text("A starter quest draft generated for local editing."),
                    "initial_stage": "start",
                    "visibility": "public",
                    "stages": [
                        {
                            "id": "start",
                            "title": "Start",
                            "description": "Begin the local world draft.",
                            "objectives": [objective_id],
                            "next_stages": [],
                        }
                    ],
                    "triggers": [
                        {
                            "type": "npc_talked",
                            "id": npc_id,
                            "action": "complete_objective",
                            "objective_id": objective_id,
                        }
                    ],
                }
            )
        return quests

    def _facts(
        self,
        draft: WorldPackWizardDraft,
        locations: list[dict[str, Any]],
        npcs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        known_by = ["player", *[npc["id"] for npc in npcs]]
        return [
            {
                "id": "world_pack_started",
                "text": self._public_text(f"{draft.name} has a validated local starting point."),
                "visibility": "public",
                "known_by": known_by,
                "tags": ["world_pack_wizard", f"location:{locations[0]['id']}"],
            }
        ]

    def _public_text(self, text: str) -> str:
        return text.replace("sk-", "redacted-").replace(".env", "environment file")

    def _remove_created_world(self, world_path: Path) -> None:
        if not world_path.exists():
            return
        for child in world_path.iterdir():
            if child.is_file():
                child.unlink()
        world_path.rmdir()
