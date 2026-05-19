from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.character_pack_builder import CharacterPack, CharacterPackManifest
from app.engine.content.validator import ValidationReport, ValidationSeverity


class NPCPackGeneratorError(ValueError):
    """Raised when an NPC pack generator draft is invalid or unsafe."""


class NPCPackHiddenSecret(BaseModel):
    id: str
    text: str
    visibility: str = "hidden"
    hidden: bool = True


class NPCPackCandidate(BaseModel):
    id: str
    name: str
    location_id: str
    faction_id: str | None = None
    archetype: str
    personality: str
    rp_profile: dict[str, Any] = Field(default_factory=dict)
    voice_profile: dict[str, Any] = Field(default_factory=dict)
    hidden_secrets: list[NPCPackHiddenSecret] = Field(default_factory=list)


class NPCPackRelationshipCandidate(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str = "acquaintance"
    trust: int = 0
    fear: int = 0
    affinity: int = 0
    obligation: int = 0
    known_by_player: bool = False


class NPCPackGeneratorDraft(BaseModel):
    target_world_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    pack_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    theme: str = "local ensemble"
    faction_ids: list[str] = Field(default_factory=list)
    location_ids: list[str] = Field(default_factory=list)
    npc_count: int = Field(default=3, ge=1, le=50)
    archetypes: list[str] = Field(default_factory=lambda: ["guide", "witness", "rival"])
    rp_style: str = "grounded"
    simulation_preset_ids: list[str] = Field(default_factory=list)
    relationship_density: float = Field(default=0.25, ge=0.0, le=1.0)
    hidden_secret_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_assisted: bool = False


class NPCPackGeneratedContent(BaseModel):
    npc_candidates: list[NPCPackCandidate] = Field(default_factory=list)
    rp_profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)
    voice_profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)
    relationship_candidates: list[NPCPackRelationshipCandidate] = Field(default_factory=list)
    goal_candidates: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    schedule_candidates: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


class NPCPackGeneratorPreview(BaseModel):
    draft: NPCPackGeneratorDraft
    generated: NPCPackGeneratedContent
    yaml_contents: dict[str, str] = Field(default_factory=dict)
    validation: ValidationReport
    writes_to_disk: bool = False
    applied: bool = False
    exported_pack: CharacterPack | None = None
    confirmation_required: bool = False


class NPCPackGeneratorApplyRequest(BaseModel):
    draft: NPCPackGeneratorDraft
    confirm_apply: bool = False
    confirm_warnings: bool = False


class NPCPackGeneratorExportRequest(BaseModel):
    draft: NPCPackGeneratorDraft
    safe_export: bool = True


def preview_npc_pack_generator(
    draft: NPCPackGeneratorDraft,
    service: ContentAuthoringService,
) -> NPCPackGeneratorPreview:
    report = ValidationReport(world_id=draft.target_world_id)
    _validate_draft(draft, service, report)
    generated = _generate_content(draft) if not report.errors else NPCPackGeneratedContent()
    yaml_contents = _generated_to_yaml(draft, generated, service, report) if not report.errors else {}
    if not report.errors:
        draft_report = service.validate_drafts(draft.target_world_id, yaml_contents)
        report.errors.extend(draft_report.errors)
        report.warnings.extend(draft_report.warnings)
        report.suggestions.extend(draft_report.suggestions)
    return NPCPackGeneratorPreview(
        draft=draft,
        generated=generated,
        yaml_contents=yaml_contents,
        validation=report,
        writes_to_disk=False,
        applied=False,
        confirmation_required=report.ok and bool(report.warnings),
    )


def validate_npc_pack_generator(
    draft: NPCPackGeneratorDraft,
    service: ContentAuthoringService,
) -> NPCPackGeneratorPreview:
    return preview_npc_pack_generator(draft, service)


def apply_npc_pack_generator(
    request: NPCPackGeneratorApplyRequest,
    service: ContentAuthoringService,
) -> NPCPackGeneratorPreview:
    preview = validate_npc_pack_generator(request.draft, service)
    if not request.confirm_apply:
        preview.validation.add(
            ValidationSeverity.ERROR,
            "npc_pack_generator.apply",
            "NPC pack apply requires explicit confirmation.",
            code="npc_pack_apply_requires_confirmation",
        )
        preview.confirmation_required = True
        return preview
    if not preview.validation.ok or (preview.validation.warnings and not request.confirm_warnings):
        preview.confirmation_required = preview.validation.ok and bool(preview.validation.warnings)
        return preview
    validation = service.write_files(
        request.draft.target_world_id,
        preview.yaml_contents,
        confirm_warnings=request.confirm_warnings,
    )
    preview.validation = validation
    preview.writes_to_disk = validation.ok
    preview.applied = validation.ok
    preview.confirmation_required = validation.ok and bool(validation.warnings) and not request.confirm_warnings
    return preview


def export_npc_pack_generator(
    request: NPCPackGeneratorExportRequest,
    service: ContentAuthoringService,
) -> NPCPackGeneratorPreview:
    preview = validate_npc_pack_generator(request.draft, service)
    if not preview.validation.ok:
        return preview
    preview.exported_pack = _generated_to_character_pack(request.draft, preview.generated, safe_export=request.safe_export)
    return preview


def _validate_draft(draft: NPCPackGeneratorDraft, service: ContentAuthoringService, report: ValidationReport) -> None:
    ids = _load_world_ids(draft.target_world_id, service, report)
    for faction_id in draft.faction_ids:
        if faction_id not in ids["factions"]:
            report.add(
                ValidationSeverity.ERROR,
                f"npc_pack_generator.faction_ids.{faction_id}",
                f"Unknown faction id: {faction_id}",
                code="npc_pack_missing_faction",
                ref_id=faction_id,
            )
    for location_id in draft.location_ids:
        if location_id not in ids["locations"]:
            report.add(
                ValidationSeverity.ERROR,
                f"npc_pack_generator.location_ids.{location_id}",
                f"Unknown location id: {location_id}",
                code="npc_pack_missing_location",
                ref_id=location_id,
            )
    unsafe_text = "\n".join(
        [
            draft.theme,
            draft.rp_style,
            *draft.archetypes,
            *draft.simulation_preset_ids,
        ]
    ).lower()
    if any(token in unsafe_text for token in ("sk-", "api_key", "apikey", ".env", "http://", "https://", "script")):
        report.add(
            ValidationSeverity.ERROR,
            "npc_pack_generator.safety",
            "NPC pack drafts cannot contain API keys, environment references, scripts, or remote URLs.",
            code="npc_pack_unsafe_reference",
        )


def _generate_content(draft: NPCPackGeneratorDraft) -> NPCPackGeneratedContent:
    locations = draft.location_ids or ["start"]
    factions = draft.faction_ids or [None]
    archetypes = draft.archetypes or ["local"]
    secret_count = int(draft.npc_count * draft.hidden_secret_ratio)
    candidates: list[NPCPackCandidate] = []
    goals: dict[str, list[dict[str, Any]]] = {}
    schedules: dict[str, list[dict[str, Any]]] = {}
    rp_profiles: dict[str, dict[str, Any]] = {}
    voice_profiles: dict[str, dict[str, Any]] = {}
    for index in range(draft.npc_count):
        npc_id = f"{draft.pack_id}_npc_{index + 1}"
        archetype = archetypes[index % len(archetypes)]
        location_id = locations[index % len(locations)]
        faction_id = factions[index % len(factions)]
        hidden_secrets = []
        if index < secret_count:
            hidden_secrets.append(
                NPCPackHiddenSecret(
                    id=f"{npc_id}_secret",
                    text=f"{npc_id} has a hidden {draft.theme} secret.",
                )
            )
        rp_profile = {
            "public_persona": f"A {draft.rp_style} {archetype} tied to {draft.theme}.",
            "private_self_summary": f"Hidden authoring-only motive for {npc_id}." if hidden_secrets else None,
            "boundaries": ["local_engine_rules_apply"],
        }
        voice_profile = {
            "tone": draft.rp_style,
            "sentence_length": "mixed",
            "vocabulary_style": archetype,
            "catchphrases": [],
            "speech_habits": [],
        }
        candidate = NPCPackCandidate(
            id=npc_id,
            name=f"{archetype.title()} {index + 1}",
            location_id=location_id,
            faction_id=faction_id,
            archetype=archetype,
            personality=f"{draft.rp_style.title()} {archetype} shaped by {draft.theme}.",
            rp_profile={key: value for key, value in rp_profile.items() if value is not None},
            voice_profile=voice_profile,
            hidden_secrets=hidden_secrets,
        )
        candidates.append(candidate)
        rp_profiles[npc_id] = candidate.rp_profile
        voice_profiles[npc_id] = candidate.voice_profile
        goals[npc_id] = [
            {
                "id": f"{npc_id}_settle_in",
                "description": f"Act as a {archetype} within the generated NPC pack.",
                "priority": 1,
                "status": "active",
                "conditions": [],
                "desired_state": {"npc_pack_role": archetype},
                "allowed_actions": ["talk_to_npc", "spread_rumor"],
                "forbidden_actions": ["attack"],
            }
        ]
        schedules[npc_id] = [
            {"time_of_day": "morning", "location_id": location_id, "activity": f"serving as {archetype}"},
            {"time_of_day": "evening", "location_id": location_id, "activity": "reviewing local rumors"},
        ]
    return NPCPackGeneratedContent(
        npc_candidates=candidates,
        rp_profiles=rp_profiles,
        voice_profiles=voice_profiles,
        relationship_candidates=_relationships(draft, candidates),
        goal_candidates=goals,
        schedule_candidates=schedules,
    )


def _relationships(
    draft: NPCPackGeneratorDraft,
    candidates: list[NPCPackCandidate],
) -> list[NPCPackRelationshipCandidate]:
    if len(candidates) < 2 or draft.relationship_density <= 0:
        return []
    target_count = max(1, int(len(candidates) * draft.relationship_density))
    relationships: list[NPCPackRelationshipCandidate] = []
    for index, source in enumerate(candidates):
        if len(relationships) >= target_count:
            break
        target = candidates[(index + 1) % len(candidates)]
        relationships.append(
            NPCPackRelationshipCandidate(
                id=f"{source.id}_{target.id}_generated",
                source_id=source.id,
                target_id=target.id,
                relation_type="generated_contact",
                trust=1,
                affinity=1,
                known_by_player=False,
            )
        )
    return relationships


def _generated_to_yaml(
    draft: NPCPackGeneratorDraft,
    generated: NPCPackGeneratedContent,
    service: ContentAuthoringService,
    report: ValidationReport,
) -> dict[str, str]:
    existing_npcs = _read_list_file(service, draft.target_world_id, "npcs.yaml", "npcs", report)
    existing_facts = _read_list_file(service, draft.target_world_id, "facts.yaml", "facts", report)
    existing_relationships = _read_list_file(
        service,
        draft.target_world_id,
        "relationships.yaml",
        "relationships",
        report,
        required=False,
    )
    if report.errors:
        return {}
    existing_npc_ids = {str(npc.get("id", "")) for npc in existing_npcs if isinstance(npc, dict)}
    if any(candidate.id in existing_npc_ids for candidate in generated.npc_candidates):
        report.add(
            ValidationSeverity.ERROR,
            "npc_pack_generator.npc_ids",
            "Generated NPC id collides with an existing NPC.",
            code="npc_pack_duplicate_npc",
        )
        return {}
    npc_entries = [_candidate_to_npc_yaml(candidate, generated, draft) for candidate in generated.npc_candidates]
    fact_entries = [
        {
            "id": secret.id,
            "text": secret.text,
            "visibility": "hidden",
            "known_by": [candidate.id],
            "tags": ["npc_pack_generator", "secret"],
        }
        for candidate in generated.npc_candidates
        for secret in candidate.hidden_secrets
    ]
    relationship_entries = [
        relationship.model_dump(mode="json")
        for relationship in generated.relationship_candidates
    ]
    yaml_contents = {
        "npcs.yaml": yaml.safe_dump({"npcs": existing_npcs + npc_entries}, sort_keys=False, allow_unicode=True),
        "facts.yaml": yaml.safe_dump({"facts": existing_facts + fact_entries}, sort_keys=False, allow_unicode=True),
    }
    if relationship_entries:
        yaml_contents["relationships.yaml"] = yaml.safe_dump(
            {"relationships": existing_relationships + relationship_entries},
            sort_keys=False,
            allow_unicode=True,
        )
    return yaml_contents


def _candidate_to_npc_yaml(
    candidate: NPCPackCandidate,
    generated: NPCPackGeneratedContent,
    draft: NPCPackGeneratorDraft,
) -> dict[str, Any]:
    secret_ids = [secret.id for secret in candidate.hidden_secrets]
    return {
        "id": candidate.id,
        "name": candidate.name,
        "location_id": candidate.location_id,
        "faction_id": candidate.faction_id,
        "personality": candidate.personality,
        "knowledge": secret_ids,
        "secrets": secret_ids,
        "goals": generated.goal_candidates.get(candidate.id, []),
        "schedule": generated.schedule_candidates.get(candidate.id, []),
        "rp_profile": candidate.rp_profile,
        "voice_profile": candidate.voice_profile,
        "plan_state": {
            "npc_pack_generator": {
                "pack_id": draft.pack_id,
                "simulation_preset_ids": draft.simulation_preset_ids,
            }
        },
    }


def _generated_to_character_pack(
    draft: NPCPackGeneratorDraft,
    generated: NPCPackGeneratedContent,
    *,
    safe_export: bool,
) -> CharacterPack:
    characters = []
    for candidate in generated.npc_candidates:
        payload = _candidate_to_npc_yaml(candidate, generated, draft)
        if safe_export:
            payload.pop("knowledge", None)
            payload.pop("secrets", None)
            payload.get("rp_profile", {}).pop("private_self_summary", None)
        characters.append(payload)
    return CharacterPack(
        manifest=CharacterPackManifest(
            pack_id=draft.pack_id,
            name=f"{draft.theme.title()} NPC Pack",
            source_world_id=draft.target_world_id,
            exported_at=datetime.now(UTC).isoformat(),
            character_ids=[candidate.id for candidate in generated.npc_candidates],
            safe_export=safe_export,
            includes_hidden_facts=False,
            files=[],
        ),
        characters=characters,
        rp_profiles={
            npc_id: {key: value for key, value in profile.items() if not (safe_export and key == "private_self_summary")}
            for npc_id, profile in generated.rp_profiles.items()
        },
        voice_profiles=generated.voice_profiles,
        fact_candidates=[],
    )


def _load_world_ids(
    world_id: str,
    service: ContentAuthoringService,
    report: ValidationReport,
) -> dict[str, set[str]]:
    return {
        "locations": {str(item.get("id", "")) for item in _read_list_file(service, world_id, "locations.yaml", "locations", report)},
        "factions": {str(item.get("id", "")) for item in _read_list_file(service, world_id, "factions.yaml", "factions", report, required=False)},
    }


def _read_list_file(
    service: ContentAuthoringService,
    world_id: str,
    file_name: str,
    root_key: str,
    report: ValidationReport,
    *,
    required: bool = True,
) -> list[dict[str, Any]]:
    try:
        content = service.read_file(world_id, file_name)
    except AuthoringError:
        if required:
            report.add(
                ValidationSeverity.ERROR,
                file_name,
                f"Required content file is missing: {file_name}",
                code="npc_pack_missing_file",
            )
        return []
    try:
        data = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        report.add(ValidationSeverity.ERROR, file_name, f"Invalid YAML: {exc}", code="npc_pack_invalid_yaml")
        return []
    values = data.get(root_key, []) if isinstance(data, dict) else []
    return [dict(item) for item in values if isinstance(item, dict)]
