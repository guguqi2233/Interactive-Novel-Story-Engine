from __future__ import annotations

from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity


class CharacterPackError(ValueError):
    """Raised when a local character pack is invalid or unsafe."""


class CharacterPackManifest(BaseModel):
    pack_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    version: str = "1.0"
    source_world_id: str | None = None
    exported_at: str
    character_ids: list[str] = Field(default_factory=list)
    safe_export: bool = True
    includes_hidden_facts: bool = False
    files: list[str] = Field(default_factory=list)


class CharacterPackFile(BaseModel):
    path: str
    content: str = ""


class CharacterPackLoreEntry(BaseModel):
    id: str
    text: str
    visibility: str = "public"
    tags: list[str] = Field(default_factory=list)


class CharacterPackFactCandidate(BaseModel):
    id: str
    text: str
    visibility: str = "public"
    known_by: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class CharacterPack(BaseModel):
    manifest: CharacterPackManifest
    characters: list[dict[str, Any]] = Field(default_factory=list)
    rp_profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)
    voice_profiles: dict[str, dict[str, Any]] = Field(default_factory=dict)
    example_dialogues: list[dict[str, Any]] = Field(default_factory=list)
    dialogue_scene_templates: list[dict[str, Any]] = Field(default_factory=list)
    group_scene_templates: list[dict[str, Any]] = Field(default_factory=list)
    flavor_lore: list[CharacterPackLoreEntry] = Field(default_factory=list)
    fact_candidates: list[CharacterPackFactCandidate] = Field(default_factory=list)
    files: list[CharacterPackFile] = Field(default_factory=list)


class CharacterPackExportRequest(BaseModel):
    world_id: str
    character_ids: list[str] = Field(default_factory=list)
    name: str | None = None
    safe_export: bool = True
    include_hidden_facts: bool = False
    export_profile_id: str | None = None


class CharacterPackImportRequest(BaseModel):
    world_id: str
    pack: CharacterPack
    confirm_apply: bool = False
    confirm_warnings: bool = False
    import_profile_id: str | None = None


class CharacterPackImportPreview(BaseModel):
    world_id: str
    pack_id: str
    would_write_files: list[str] = Field(default_factory=list)
    yaml_contents: dict[str, str] = Field(default_factory=dict)
    validation: ValidationReport
    confirmation_required: bool = False
    applied: bool = False


SCRIPT_SUFFIXES = {
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".exe",
    ".js",
    ".mjs",
    ".ps1",
    ".py",
    ".sh",
    ".vbs",
}
SECRET_TOKENS = ("api_key", "apikey", "secret_key", "private_key", "bearer ", "sk-", "BEGIN PRIVATE KEY")
REMOTE_URL_TOKENS = ("http://", "https://")


def export_character_pack(
    request: CharacterPackExportRequest,
    service: ContentAuthoringService,
) -> CharacterPack:
    world_id = request.world_id
    npcs = _read_list_file(service, world_id, "npcs.yaml", "npcs")
    selected_ids = set(request.character_ids) if request.character_ids else {str(npc.get("id", "")) for npc in npcs}
    selected = [npc for npc in npcs if str(npc.get("id", "")) in selected_ids]
    hidden_terms = _hidden_fact_terms(service, world_id)
    safe_characters: list[dict[str, Any]] = []
    rp_profiles: dict[str, dict[str, Any]] = {}
    voice_profiles: dict[str, dict[str, Any]] = {}
    for npc in selected:
        npc_id = str(npc.get("id", ""))
        exported_npc = _safe_character_payload(npc, safe_export=request.safe_export)
        if not request.safe_export:
            exported_npc = dict(npc)
        rp_profile = dict(npc.get("rp_profile") or {})
        voice_profile = dict(npc.get("voice_profile") or {})
        if request.safe_export:
            rp_profile.pop("private_self_summary", None)
            exported_npc.pop("knowledge", None)
            exported_npc.pop("secrets", None)
        safe_characters.append(exported_npc)
        if rp_profile:
            rp_profiles[npc_id] = rp_profile
        if voice_profile:
            voice_profiles[npc_id] = voice_profile

    examples = [
        example
        for example in _read_list_file(service, world_id, "example_dialogues.yaml", "example_dialogues", required=False)
        if str(example.get("character_id", "")) in selected_ids
        and (not request.safe_export or _is_safe_example(example, hidden_terms))
    ]
    dialogue_scenes = [
        template
        for template in _read_list_file(service, world_id, "dialogue_scenes.yaml", "dialogue_scenes", required=False)
        if _template_mentions_character(template, selected_ids)
        and (not request.safe_export or not _contains_any_hidden_text(template, hidden_terms))
    ]
    group_scenes = [
        template
        for template in _read_list_file(service, world_id, "group_rp_scenes.yaml", "group_rp_scenes", required=False)
        if _template_mentions_character(template, selected_ids)
        and (not request.safe_export or not _contains_any_hidden_text(template, hidden_terms))
    ]
    source_facts = [
        fact
        for fact in _read_list_file(service, world_id, "facts.yaml", "facts", required=False)
        if request.include_hidden_facts or str(fact.get("visibility", "hidden")) == "public"
    ]
    fact_candidates = [] if request.safe_export and not request.include_hidden_facts else [
        CharacterPackFactCandidate(
            id=str(fact.get("id", "")),
            text=str(fact.get("text", "")),
            visibility=str(fact.get("visibility", "hidden")),
            known_by=[str(item) for item in fact.get("known_by", []) if isinstance(item, str)],
            tags=[str(item) for item in fact.get("tags", []) if isinstance(item, str)],
        )
        for fact in source_facts
    ]
    manifest = CharacterPackManifest(
        pack_id=f"{world_id}_characters",
        name=request.name or f"{world_id} Character Pack",
        source_world_id=world_id,
        exported_at=datetime.now(UTC).isoformat(),
        character_ids=[str(npc.get("id", "")) for npc in selected],
        safe_export=request.safe_export,
        includes_hidden_facts=bool(request.include_hidden_facts and not request.safe_export),
    )
    return CharacterPack(
        manifest=manifest,
        characters=safe_characters,
        rp_profiles=rp_profiles,
        voice_profiles=voice_profiles,
        example_dialogues=examples,
        dialogue_scene_templates=dialogue_scenes,
        group_scene_templates=group_scenes,
        flavor_lore=[
            CharacterPackLoreEntry(
                id=str(fact.get("id", "")),
                text=str(fact.get("text", "")),
                visibility=str(fact.get("visibility", "hidden")),
                tags=[str(item) for item in fact.get("tags", []) if isinstance(item, str)],
            )
            for fact in source_facts
        ],
        fact_candidates=fact_candidates,
    )


def import_character_pack_dry_run(
    request: CharacterPackImportRequest,
    service: ContentAuthoringService,
) -> CharacterPackImportPreview:
    report = ValidationReport(world_id=request.world_id)
    _add_pack_security_validation(report, request.pack)
    yaml_contents = _pack_to_yaml_contents(request.world_id, request.pack, service, report)
    if not report.errors:
        draft_report = service.validate_drafts(request.world_id, yaml_contents) if yaml_contents else service.validate_world(request.world_id)
        report.errors.extend(draft_report.errors)
        report.warnings.extend(draft_report.warnings)
        report.suggestions.extend(draft_report.suggestions)
    return CharacterPackImportPreview(
        world_id=request.world_id,
        pack_id=request.pack.manifest.pack_id,
        would_write_files=sorted(yaml_contents),
        yaml_contents=yaml_contents,
        validation=report,
        confirmation_required=report.ok and bool(report.warnings),
        applied=False,
    )


def apply_character_pack_import(
    request: CharacterPackImportRequest,
    service: ContentAuthoringService,
) -> CharacterPackImportPreview:
    preview = import_character_pack_dry_run(request, service)
    if not request.confirm_apply:
        preview.validation.add(
            ValidationSeverity.ERROR,
            "character_pack.import_apply",
            "Character pack import apply requires explicit confirmation.",
            code="character_pack_apply_requires_confirmation",
            suggestion="Set confirm_apply to true after reviewing the dry-run report.",
        )
        preview.confirmation_required = True
        return preview
    if not preview.validation.ok or (preview.validation.warnings and not request.confirm_warnings):
        preview.confirmation_required = preview.validation.ok and bool(preview.validation.warnings)
        return preview
    validation = service.write_files(
        request.world_id,
        preview.yaml_contents,
        confirm_warnings=request.confirm_warnings,
    )
    return CharacterPackImportPreview(
        world_id=request.world_id,
        pack_id=request.pack.manifest.pack_id,
        would_write_files=preview.would_write_files,
        yaml_contents=preview.yaml_contents,
        validation=validation,
        confirmation_required=validation.ok and bool(validation.warnings) and not request.confirm_warnings,
        applied=validation.ok,
    )


def _pack_to_yaml_contents(
    world_id: str,
    pack: CharacterPack,
    service: ContentAuthoringService,
    report: ValidationReport,
) -> dict[str, str]:
    existing_npcs = _read_list_file(service, world_id, "npcs.yaml", "npcs")
    existing_ids = {str(npc.get("id", "")) for npc in existing_npcs}
    new_characters: list[dict[str, Any]] = []
    for character in pack.characters:
        npc_id = str(character.get("id", ""))
        if not npc_id:
            report.add(ValidationSeverity.ERROR, "character_pack.characters", "Character is missing id.", code="character_pack_character_missing_id")
            continue
        if npc_id in existing_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"character_pack.characters.{npc_id}",
                "Character pack import does not automatically overwrite existing NPC ids.",
                code="character_pack_npc_already_exists",
                ref_id=npc_id,
            )
            continue
        new_characters.append(_merge_profile_payload(character, pack))
    proposed: dict[str, str] = {}
    if new_characters:
        proposed["npcs.yaml"] = yaml.safe_dump(
            {"npcs": existing_npcs + new_characters},
            sort_keys=False,
            allow_unicode=True,
        )
    _append_list_file(proposed, service, world_id, "example_dialogues.yaml", "example_dialogues", pack.example_dialogues)
    _append_list_file(proposed, service, world_id, "dialogue_scenes.yaml", "dialogue_scenes", pack.dialogue_scene_templates)
    _append_list_file(proposed, service, world_id, "group_rp_scenes.yaml", "group_rp_scenes", pack.group_scene_templates)
    safe_facts = [
        fact.model_dump(mode="json")
        for fact in pack.fact_candidates
        if fact.visibility == "public"
    ]
    if safe_facts:
        _append_list_file(proposed, service, world_id, "facts.yaml", "facts", safe_facts)
    return proposed


def _merge_profile_payload(character: dict[str, Any], pack: CharacterPack) -> dict[str, Any]:
    npc_id = str(character.get("id", ""))
    merged = dict(character)
    if npc_id in pack.rp_profiles:
        merged["rp_profile"] = pack.rp_profiles[npc_id]
    if npc_id in pack.voice_profiles:
        merged["voice_profile"] = pack.voice_profiles[npc_id]
    merged.pop("player_visible_facts", None)
    merged.pop("api_key", None)
    return {key: value for key, value in merged.items() if value not in (None, [], {})}


def _append_list_file(
    proposed: dict[str, str],
    service: ContentAuthoringService,
    world_id: str,
    file_name: str,
    root_key: str,
    new_items: list[dict[str, Any]],
) -> None:
    if not new_items:
        return
    existing = _read_list_file(service, world_id, file_name, root_key, required=False)
    proposed[file_name] = yaml.safe_dump(
        {root_key: existing + [dict(item) for item in new_items]},
        sort_keys=False,
        allow_unicode=True,
    )


def _add_pack_security_validation(report: ValidationReport, pack: CharacterPack) -> None:
    for file in pack.files:
        _validate_pack_path(report, file.path)
        if file.content.startswith("#!") or "<script" in file.content.lower():
            report.add(
                ValidationSeverity.ERROR,
                f"character_pack.files.{file.path}",
                "Character packs cannot contain executable scripts.",
                code="character_pack_executable_file_rejected",
                ref_id=file.path,
            )
    for path in pack.manifest.files:
        _validate_pack_path(report, path)
    for text in _iter_strings(pack.model_dump(mode="json")):
        lowered = text.lower()
        if any(token in lowered for token in SECRET_TOKENS):
            report.add(
                ValidationSeverity.ERROR,
                "character_pack",
                "Character pack contains API key or sensitive configuration text.",
                code="character_pack_secret_rejected",
            )
            break
    for text in _iter_strings(pack.model_dump(mode="json")):
        lowered = text.lower()
        if any(token in lowered for token in REMOTE_URL_TOKENS):
            report.add(
                ValidationSeverity.ERROR,
                "character_pack",
                "Character pack import cannot read or reference remote URLs.",
                code="character_pack_remote_url_rejected",
            )
            break
    hidden_candidates = [candidate.id for candidate in pack.fact_candidates if candidate.visibility != "public"]
    if hidden_candidates and pack.manifest.safe_export:
        report.add(
            ValidationSeverity.WARNING,
            "character_pack.fact_candidates",
            "Hidden fact candidates are present in a safe pack and will not be imported by default.",
            code="character_pack_hidden_facts_skipped",
            ref_id=",".join(hidden_candidates),
        )


def _validate_pack_path(report: ValidationReport, path: str) -> None:
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if normalized.startswith("/") or normalized.startswith("~") or ".." in pure.parts:
        report.add(
            ValidationSeverity.ERROR,
            f"character_pack.files.{path}",
            "Character pack file path escapes the package root.",
            code="character_pack_path_traversal_rejected",
            ref_id=path,
        )
    if pure.suffix.lower() in SCRIPT_SUFFIXES:
        report.add(
            ValidationSeverity.ERROR,
            f"character_pack.files.{path}",
            "Executable files are not allowed in character packs.",
            code="character_pack_executable_file_rejected",
            ref_id=path,
        )


def _safe_character_payload(npc: dict[str, Any], *, safe_export: bool) -> dict[str, Any]:
    allowed = {
        "id",
        "name",
        "location_id",
        "faction_id",
        "personality",
        "visible",
        "hidden",
        "rp_profile",
        "voice_profile",
        "emotional_state",
        "example_dialogue_refs",
        "lorebook_links",
        "scene_mood_preferences",
    }
    payload = {key: value for key, value in npc.items() if key in allowed}
    if safe_export:
        payload.pop("hidden", None)
    return payload


def _read_list_file(
    service: ContentAuthoringService,
    world_id: str,
    file_name: str,
    root_key: str,
    *,
    required: bool = True,
) -> list[dict[str, Any]]:
    try:
        content = service.read_file(world_id, file_name)
    except Exception as exc:
        if required:
            raise CharacterPackError(str(exc)) from exc
        return []
    data = yaml.safe_load(content) or {}
    values = data.get(root_key, []) if isinstance(data, dict) else []
    return [dict(item) for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _hidden_fact_terms(service: ContentAuthoringService, world_id: str) -> set[str]:
    terms: set[str] = set()
    for fact in _read_list_file(service, world_id, "facts.yaml", "facts", required=False):
        if str(fact.get("visibility", "")) != "public":
            terms.add(str(fact.get("id", "")))
            text = str(fact.get("text", ""))
            if text:
                terms.add(text)
    return terms


def _contains_any_hidden_text(value: Any, hidden_terms: set[str]) -> bool:
    lower_terms = {term.lower() for term in hidden_terms if term}
    return any(term in text.lower() for text in _iter_strings(value) for term in lower_terms)


def _is_safe_example(example: dict[str, Any], hidden_terms: set[str]) -> bool:
    visibility = str(example.get("visibility", "prompt_safe"))
    fact_policy = str(example.get("fact_policy", "public_only"))
    return visibility == "prompt_safe" and fact_policy != "unsafe" and not _contains_any_hidden_text(example, hidden_terms)


def _template_mentions_character(template: dict[str, Any], selected_ids: set[str]) -> bool:
    participants = {str(item) for item in template.get("participant_ids", []) if isinstance(item, str)}
    focus = str(template.get("focus_npc_id", ""))
    role_npcs = {str(role.get("npc_id", "")) for role in template.get("required_roles", []) if isinstance(role, dict)}
    return bool((participants | role_npcs | {focus}) & selected_ids)


def _iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for key, child in value.items() for item in _iter_strings(key) + _iter_strings(child)]
    if isinstance(value, list):
        return [item for child in value for item in _iter_strings(child)]
    return []
