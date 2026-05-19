from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.core.world_state import (
    EmotionalState,
    ExampleDialogue,
    ExampleDialogueFactPolicy,
    ExampleDialogueVisibility,
    FactVisibility,
    RPProfile,
    VoiceProfile,
)
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.roleplay.character_cards import CharacterCardImport, CharacterCardImportReport, preview_character_card_import
from app.roleplay.example_dialogues import ExampleDialogueDraftRequest, preview_example_dialogues


class RPCharacterAuthoringError(ValueError):
    """Raised when RP character authoring input is invalid."""


class RPCharacterAuthoringProfile(BaseModel):
    npc_id: str
    name: str
    location_id: str
    personality: str = ""
    visible: bool = True
    hidden: bool = False
    knowledge: list[str] = Field(default_factory=list)
    rp_profile: RPProfile = Field(default_factory=RPProfile)
    voice_profile: VoiceProfile = Field(default_factory=VoiceProfile)
    default_emotional_state: EmotionalState = Field(default_factory=EmotionalState)
    relationship_expression: dict[str, str] = Field(default_factory=dict)
    example_dialogue_refs: list[str] = Field(default_factory=list)
    example_dialogues: list[ExampleDialogue] = Field(default_factory=list)
    lorebook_links: list[str] = Field(default_factory=list)
    scene_mood_preferences: list[str] = Field(default_factory=list)
    private_field_visibility: dict[str, str] = Field(default_factory=lambda: {"private_self_summary": "hidden"})
    import_report: CharacterCardImportReport | None = None
    safety_flags: list[str] = Field(default_factory=list)


class RPCharacterAuthoring(BaseModel):
    world_id: str
    characters: list[RPCharacterAuthoringProfile] = Field(default_factory=list)


class RPCharacterAuthoringPreview(BaseModel):
    world_id: str
    graph: RPCharacterAuthoring
    yaml_contents: dict[str, str]
    validation: ValidationReport
    confirmation_required: bool = False


class RPCharacterAuthoringSaveResponse(RPCharacterAuthoringPreview):
    saved: bool = False


class RPCharacterImportPreviewRequest(CharacterCardImport):
    npc_id: str | None = None


class RPCharacterSafeExportRequest(BaseModel):
    npc_id: str


class RPCharacterSafeExportResponse(BaseModel):
    world_id: str
    npc_id: str
    card: dict[str, Any]
    excluded_fields: list[str] = Field(default_factory=list)


def parse_rp_character_authoring(world_id: str, service: ContentAuthoringService) -> RPCharacterAuthoring:
    npc_data = _read_list_file(service, world_id, "npcs.yaml", "npcs")
    examples = _read_example_dialogues(service, world_id)
    scene_mood_ids = [str(item.get("id", "")) for item in _read_list_file(service, world_id, "scene_moods.yaml", "scene_mood_presets", required=False)]
    characters: list[RPCharacterAuthoringProfile] = []
    for npc in npc_data:
        npc_id = str(npc.get("id", ""))
        refs = [str(ref) for ref in npc.get("example_dialogue_refs", [])]
        npc_examples = [example for example in examples if example.character_id == npc_id or example.id in refs]
        rp_profile = RPProfile.model_validate(npc.get("rp_profile") or {})
        characters.append(
            RPCharacterAuthoringProfile(
                npc_id=npc_id,
                name=str(npc.get("name", npc_id)),
                location_id=str(npc.get("location_id", "")),
                personality=str(npc.get("personality", "")),
                visible=bool(npc.get("visible", True)),
                hidden=bool(npc.get("hidden", False)),
                knowledge=[str(item) for item in npc.get("knowledge", [])],
                rp_profile=rp_profile,
                voice_profile=VoiceProfile.model_validate(npc.get("voice_profile") or {}),
                default_emotional_state=EmotionalState.model_validate(npc.get("emotional_state") or {}),
                relationship_expression=_relationship_expression_from_profile(rp_profile),
                example_dialogue_refs=refs,
                example_dialogues=npc_examples,
                lorebook_links=_lorebook_links(npc),
                scene_mood_preferences=_scene_mood_preferences(npc, scene_mood_ids),
                safety_flags=_safety_flags(rp_profile, npc_examples),
            )
        )
    return RPCharacterAuthoring(world_id=world_id, characters=characters)


def preview_rp_character_import(request: RPCharacterImportPreviewRequest) -> CharacterCardImportReport:
    return preview_character_card_import(CharacterCardImport(**request.model_dump()))


def rp_character_to_yaml(
    world_id: str,
    graph: RPCharacterAuthoring,
    service: ContentAuthoringService,
) -> dict[str, str]:
    if graph.world_id != world_id:
        raise RPCharacterAuthoringError(f"Graph world_id does not match route world_id: {graph.world_id} != {world_id}")
    npc_data = _read_list_file(service, world_id, "npcs.yaml", "npcs")
    by_id = {character.npc_id: character for character in graph.characters}
    updated_npcs: list[dict[str, Any]] = []
    for npc in npc_data:
        npc_id = str(npc.get("id", ""))
        character = by_id.get(npc_id)
        if character is None:
            updated_npcs.append(dict(npc))
            continue
        updated = dict(npc)
        updated.update(
            {
                "name": character.name,
                "location_id": character.location_id,
                "personality": character.personality,
                "visible": character.visible,
                "hidden": character.hidden,
                "knowledge": character.knowledge,
                "rp_profile": character.rp_profile.model_dump(mode="json", exclude_none=True),
                "voice_profile": character.voice_profile.model_dump(mode="json", exclude_none=True),
                "emotional_state": character.default_emotional_state.model_dump(mode="json", exclude_none=True),
                "example_dialogue_refs": character.example_dialogue_refs,
            }
        )
        updated_npcs.append(_without_empty_lists(updated))
    all_examples = _merge_examples(_read_example_dialogues(service, world_id), graph.characters)
    return {
        "npcs.yaml": yaml.safe_dump({"npcs": updated_npcs}, sort_keys=False, allow_unicode=True),
        "example_dialogues.yaml": yaml.safe_dump(
            {"example_dialogues": [entry.model_dump(mode="json", exclude_none=True) for entry in sorted(all_examples, key=lambda item: item.id)]},
            sort_keys=False,
            allow_unicode=True,
        ),
    }


def preview_rp_character_authoring(
    world_id: str,
    graph: RPCharacterAuthoring,
    service: ContentAuthoringService,
) -> RPCharacterAuthoringPreview:
    yaml_contents = rp_character_to_yaml(world_id, graph, service)
    validation = service.validate_drafts(world_id, yaml_contents)
    _add_rp_character_validation(validation, graph, service)
    return RPCharacterAuthoringPreview(
        world_id=world_id,
        graph=_with_safety_flags(graph),
        yaml_contents=yaml_contents,
        validation=validation,
        confirmation_required=validation.ok and bool(validation.warnings),
    )


def validate_rp_character_authoring(
    world_id: str,
    graph: RPCharacterAuthoring,
    service: ContentAuthoringService,
) -> RPCharacterAuthoringPreview:
    return preview_rp_character_authoring(world_id, graph, service)


def save_rp_character_authoring(
    world_id: str,
    graph: RPCharacterAuthoring,
    service: ContentAuthoringService,
    *,
    confirm_warnings: bool = False,
) -> RPCharacterAuthoringSaveResponse:
    preview = preview_rp_character_authoring(world_id, graph, service)
    if not preview.validation.ok or (preview.validation.warnings and not confirm_warnings):
        return RPCharacterAuthoringSaveResponse(**preview.model_dump(), saved=False)
    validation = service.write_files(world_id, preview.yaml_contents, confirm_warnings=confirm_warnings)
    return RPCharacterAuthoringSaveResponse(
        world_id=world_id,
        graph=preview.graph,
        yaml_contents=preview.yaml_contents,
        validation=validation,
        confirmation_required=validation.ok and bool(validation.warnings) and not confirm_warnings,
        saved=validation.ok,
    )


def export_safe_character_card(
    world_id: str,
    request: RPCharacterSafeExportRequest,
    service: ContentAuthoringService,
) -> RPCharacterSafeExportResponse:
    graph = parse_rp_character_authoring(world_id, service)
    character = next((candidate for candidate in graph.characters if candidate.npc_id == request.npc_id), None)
    if character is None:
        raise RPCharacterAuthoringError(f"Unknown NPC id: {request.npc_id}")
    safe_examples = [
        _example_to_safe_lines(example)
        for example in character.example_dialogues
        if _example_is_safe_for_export(example)
    ]
    card = {
        "name": character.name,
        "description": character.rp_profile.public_persona,
        "personality": character.personality,
        "voice": {
            "tone": character.voice_profile.tone,
            "sentence_length": character.voice_profile.sentence_length,
            "vocabulary_style": character.voice_profile.vocabulary_style,
            "catchphrases": character.voice_profile.catchphrases,
            "speech_habits": character.voice_profile.speech_habits,
            "silence_style": character.voice_profile.silence_style,
            "emotional_tells": character.voice_profile.emotional_tells,
        },
        "example_dialogue": [line for lines in safe_examples for line in lines],
        "tags": ["safe_export", "rp_character"],
    }
    return RPCharacterSafeExportResponse(
        world_id=world_id,
        npc_id=request.npc_id,
        card=card,
        excluded_fields=[
            "private_self_summary",
            "knowledge",
            "hidden_facts",
            "taboo_topics",
            "debug_state",
            "unsafe_example_dialogue",
        ],
    )


def _add_rp_character_validation(
    validation: ValidationReport,
    graph: RPCharacterAuthoring,
    service: ContentAuthoringService,
) -> None:
    hidden_facts = _hidden_facts(service, graph.world_id)
    for character in graph.characters:
        if character.rp_profile.private_self_summary and character.private_field_visibility.get("private_self_summary") != "hidden":
            validation.add(
                ValidationSeverity.ERROR,
                f"npcs.yaml.{character.npc_id}.rp_profile.private_self_summary",
                "private_self_summary must remain hidden.",
                code="rp_private_self_summary_not_hidden",
                ref_id=character.npc_id,
            )
        public_text = "\n".join([character.rp_profile.public_persona, character.personality])
        for fact_id, fact_text in hidden_facts.items():
            if _mentions_hidden_fact(public_text, fact_id, fact_text):
                validation.add(
                    ValidationSeverity.ERROR,
                    f"npcs.yaml.{character.npc_id}.rp_profile.public_persona",
                    "Hidden fact appears in player-facing RP profile text.",
                    code="rp_profile_hidden_fact_leak",
                    ref_id=character.npc_id,
                )
        for field_name, text in _prompt_control_fields(character).items():
            if _looks_like_prompt_injection(text):
                validation.add(
                    ValidationSeverity.ERROR,
                    f"npcs.yaml.{character.npc_id}.{field_name}",
                    "RP character field contains prompt-control language.",
                    code="rp_character_unsafe_prompt",
                    ref_id=character.npc_id,
                )
        for example in character.example_dialogues:
            if example.id in character.example_dialogue_refs and not _example_is_safe_for_prompt(example):
                validation.add(
                    ValidationSeverity.ERROR,
                    f"example_dialogues.{example.id}",
                    "Referenced example dialogue is not prompt safe.",
                    code="rp_character_unsafe_example_ref",
                    ref_id=example.id,
                )
            if _looks_like_prompt_injection(_joined_example_text(example)):
                validation.add(
                    ValidationSeverity.ERROR,
                    f"example_dialogues.{example.id}",
                    "Example dialogue contains prompt-control language.",
                    code="rp_character_example_prompt_injection",
                    ref_id=example.id,
                )
    examples = [example for character in graph.characters for example in character.example_dialogues]
    if examples:
        example_validation = preview_example_dialogues(
            graph.world_id,
            ExampleDialogueDraftRequest(entries=examples),
            service,
        ).validation
        validation.errors.extend(example_validation.errors)
        validation.warnings.extend(example_validation.warnings)
        validation.suggestions.extend(example_validation.suggestions)


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
            raise RPCharacterAuthoringError(str(exc)) from exc
        return []
    data = yaml.safe_load(content) or {}
    values = data.get(root_key, []) if isinstance(data, dict) else []
    return [dict(item) for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _read_example_dialogues(service: ContentAuthoringService, world_id: str) -> list[ExampleDialogue]:
    return [ExampleDialogue.model_validate(item) for item in _read_list_file(service, world_id, "example_dialogues.yaml", "example_dialogues", required=False)]


def _merge_examples(existing: list[ExampleDialogue], characters: list[RPCharacterAuthoringProfile]) -> list[ExampleDialogue]:
    by_id = {example.id: example for example in existing}
    for character in characters:
        for example in character.example_dialogues:
            by_id[example.id] = example
    return list(by_id.values())


def _hidden_facts(service: ContentAuthoringService, world_id: str) -> dict[str, str]:
    hidden: dict[str, str] = {}
    for fact in _read_list_file(service, world_id, "facts.yaml", "facts", required=False):
        visibility = str(fact.get("visibility", ""))
        if visibility != FactVisibility.PUBLIC:
            hidden[str(fact.get("id", ""))] = str(fact.get("text", ""))
    return hidden


def _relationship_expression_from_profile(profile: RPProfile) -> dict[str, str]:
    return {
        "trust": profile.trust_expression_style,
        "conflict": profile.conflict_expression_style,
        "intimacy": profile.intimacy_expression_style,
        "deception": profile.deception_style,
        "attachment": profile.attachment_style,
    }


def _lorebook_links(npc: dict[str, Any]) -> list[str]:
    values = npc.get("lorebook_links", npc.get("lorebook_refs", []))
    return [str(item) for item in values] if isinstance(values, list) else []


def _scene_mood_preferences(npc: dict[str, Any], scene_mood_ids: list[str]) -> list[str]:
    values = npc.get("scene_mood_preferences", [])
    if isinstance(values, list):
        return [str(item) for item in values]
    return scene_mood_ids[:0]


def _safety_flags(profile: RPProfile, examples: list[ExampleDialogue]) -> list[str]:
    flags: list[str] = []
    if profile.private_self_summary:
        flags.append("hidden_private_summary")
    if any(not _example_is_safe_for_prompt(example) for example in examples):
        flags.append("unsafe_or_authoring_only_examples")
    return flags


def _with_safety_flags(graph: RPCharacterAuthoring) -> RPCharacterAuthoring:
    return graph.model_copy(update={"characters": [character.model_copy(update={"safety_flags": _safety_flags(character.rp_profile, character.example_dialogues)}) for character in graph.characters]})


def _prompt_control_fields(character: RPCharacterAuthoringProfile) -> dict[str, str]:
    return {
        "personality": character.personality,
        "rp_profile.public_persona": character.rp_profile.public_persona,
        "voice_profile.tone": character.voice_profile.tone,
        "voice_profile.vocabulary_style": character.voice_profile.vocabulary_style,
        "dialogue_examples": _joined_example_texts(character.example_dialogues),
    }


def _example_is_safe_for_prompt(example: ExampleDialogue) -> bool:
    return example.visibility == ExampleDialogueVisibility.PROMPT_SAFE and example.fact_policy != ExampleDialogueFactPolicy.UNSAFE


def _example_is_safe_for_export(example: ExampleDialogue) -> bool:
    return _example_is_safe_for_prompt(example) and not _looks_like_prompt_injection(_joined_example_text(example))


def _example_to_safe_lines(example: ExampleDialogue) -> list[str]:
    return [message.text for message in example.messages[:4]]


def _joined_example_text(example: ExampleDialogue) -> str:
    return "\n".join(message.text for message in example.messages).lower()


def _joined_example_texts(examples: list[ExampleDialogue]) -> str:
    return "\n".join(_joined_example_text(example) for example in examples)


def _mentions_hidden_fact(text: str, fact_id: str, fact_text: str) -> bool:
    lower = text.lower()
    return bool(fact_id and fact_id.lower() in lower) or bool(fact_text and fact_text.lower() in lower)


def _looks_like_prompt_injection(text: str) -> bool:
    lower = text.lower()
    return any(
        token in lower
        for token in (
            "ignore previous",
            "ignore all previous",
            "system prompt",
            "developer message",
            "reveal hidden",
            "bypass visibility",
            "modify gamestate",
            "state_delta",
            "write gamestate",
            "override",
            "jailbreak",
        )
    )


def _without_empty_lists(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None and value != []}
