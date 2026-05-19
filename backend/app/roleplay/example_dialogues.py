from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.world_state import (
    ExampleDialogue,
    ExampleDialogueFactPolicy,
    ExampleDialogueMessage,
    ExampleDialogueVisibility,
    FactVisibility,
    GameState,
)
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.roleplay.character_cards import CharacterCardImportReport


class ExampleDialogueBundle(BaseModel):
    example_dialogues: list[ExampleDialogue] = Field(default_factory=list)


class ExampleDialogueListResponse(BaseModel):
    world_id: str
    entries: list[ExampleDialogue] = Field(default_factory=list)


class ExampleDialogueDraftRequest(BaseModel):
    entries: list[ExampleDialogue] = Field(default_factory=list)


class ExampleDialoguePreviewResponse(BaseModel):
    world_id: str
    entries: list[ExampleDialogue] = Field(default_factory=list)
    yaml_content: str
    validation: ValidationReport


class ExampleDialogueSaveResponse(ExampleDialoguePreviewResponse):
    saved: bool = False


def build_example_dialogue_context(state: GameState, npc_id: str, *, limit: int = 3) -> list[str]:
    """Return prompt-safe dialogue examples for one NPC.

    These are style references only. They do not become facts, do not grant NPC
    knowledge, and are filtered against hidden/discoverable facts.
    """
    examples = [
        example
        for example in state.example_dialogues.values()
        if example.character_id == npc_id and _is_prompt_safe_for_dialogue(state, example)
    ]
    npc = state.npcs.get(npc_id)
    if npc is not None and npc.example_dialogue_refs:
        ref_order = {example_id: index for index, example_id in enumerate(npc.example_dialogue_refs)}
        examples.sort(key=lambda example: (ref_order.get(example.id, len(ref_order)), example.id))
    else:
        examples.sort(key=lambda example: example.id)
    return [_summary_for_prompt(example) for example in examples[:limit]]


def example_dialogue_from_character_card_report(
    report: CharacterCardImportReport,
    *,
    character_id: str,
    dialogue_id: str | None = None,
) -> ExampleDialogue | None:
    lines = [line for line in report.example_dialogue_candidate.lines if line.strip()]
    if not lines:
        return None
    return ExampleDialogue(
        id=dialogue_id or f"{character_id}_card_example",
        character_id=character_id,
        source="character_card_import",
        messages=[ExampleDialogueMessage(speaker=report.normalized_card.name, text=line) for line in lines],
        tags=sorted(set(report.normalized_card.tags + ["character_card_import"])),
        style_notes=["Imported style example. Not an authoritative fact."],
        visibility=ExampleDialogueVisibility.AUTHORING_ONLY,
        fact_policy=ExampleDialogueFactPolicy.FLAVOR_ONLY,
    )


def list_example_dialogues(world_id: str, service: ContentAuthoringService) -> ExampleDialogueListResponse:
    try:
        content = service.read_file(world_id, "example_dialogues.yaml")
    except Exception:
        return ExampleDialogueListResponse(world_id=world_id, entries=[])
    bundle = _parse_example_dialogue_yaml(content)
    return ExampleDialogueListResponse(world_id=world_id, entries=bundle.example_dialogues)


def preview_example_dialogues(
    world_id: str,
    request: ExampleDialogueDraftRequest,
    service: ContentAuthoringService,
) -> ExampleDialoguePreviewResponse:
    yaml_content = _to_yaml(request.entries)
    validation = service.validate_draft(world_id, "example_dialogues.yaml", yaml_content)
    _add_example_dialogue_policy_issues(request.entries, validation)
    return ExampleDialoguePreviewResponse(
        world_id=world_id,
        entries=request.entries,
        yaml_content=yaml_content,
        validation=validation,
    )


def validate_example_dialogues(
    world_id: str,
    request: ExampleDialogueDraftRequest,
    service: ContentAuthoringService,
) -> ExampleDialoguePreviewResponse:
    return preview_example_dialogues(world_id, request, service)


def save_example_dialogues(
    world_id: str,
    request: ExampleDialogueDraftRequest,
    service: ContentAuthoringService,
) -> ExampleDialogueSaveResponse:
    preview = preview_example_dialogues(world_id, request, service)
    if not preview.validation.ok:
        return ExampleDialogueSaveResponse(**preview.model_dump(), saved=False)
    validation = service.write_file(world_id, "example_dialogues.yaml", preview.yaml_content)
    _add_example_dialogue_policy_issues(request.entries, validation)
    return ExampleDialogueSaveResponse(
        world_id=world_id,
        entries=request.entries,
        yaml_content=preview.yaml_content,
        validation=validation,
        saved=validation.ok,
    )


def _is_prompt_safe_for_dialogue(state: GameState, example: ExampleDialogue) -> bool:
    if example.visibility != ExampleDialogueVisibility.PROMPT_SAFE:
        return False
    if example.fact_policy == ExampleDialogueFactPolicy.UNSAFE:
        return False
    text = _joined_example_text(example).lower()
    if _looks_like_prompt_injection(text):
        return False
    for fact_id, fact in state.facts.items():
        if not _mentions_fact(text, fact_id, fact.text):
            continue
        player_knows = fact_id in state.player_visible_facts or fact.visibility == FactVisibility.PUBLIC
        npc_knows = fact_id in set(state.npcs.get(example.character_id, None).knowledge if example.character_id in state.npcs else []) or fact_id in state.npc_knowledge.get(example.character_id, set())
        if not (player_knows and npc_knows):
            return False
    return True


def _summary_for_prompt(example: ExampleDialogue) -> str:
    lines = []
    for message in example.messages[:4]:
        speaker = f"{message.speaker}: " if message.speaker else ""
        lines.append(f"{speaker}{message.text}")
    notes = "; ".join(example.style_notes[:3])
    tags = ",".join(sorted(set(example.tags)))
    return f"example={example.id}; tags={tags}; notes={notes}; lines={' | '.join(lines)}"


def _parse_example_dialogue_yaml(content: str) -> ExampleDialogueBundle:
    try:
        raw = yaml.safe_load(content) or {}
        return ExampleDialogueBundle.model_validate(raw)
    except (yaml.YAMLError, ValidationError) as exc:
        raise ValueError(f"Invalid example_dialogues.yaml: {exc}") from exc


def _to_yaml(entries: list[ExampleDialogue]) -> str:
    payload: dict[str, Any] = {
        "example_dialogues": [
            entry.model_dump(mode="json", exclude_none=True)
            for entry in sorted(entries, key=lambda item: item.id)
        ]
    }
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)


def _add_example_dialogue_policy_issues(entries: list[ExampleDialogue], validation: ValidationReport) -> None:
    seen: set[str] = set()
    for entry in entries:
        if entry.id in seen:
            validation.add(
                ValidationSeverity.ERROR,
                f"example_dialogues.{entry.id}",
                f"Duplicate example dialogue id: {entry.id}",
                code="duplicate_example_dialogue_id",
            )
        seen.add(entry.id)
        if entry.visibility == ExampleDialogueVisibility.UNSAFE or entry.fact_policy == ExampleDialogueFactPolicy.UNSAFE:
            validation.add(
                ValidationSeverity.WARNING,
                f"example_dialogues.{entry.id}",
                "Unsafe example dialogue is quarantined and will never enter RP prompts.",
                code="example_dialogue_quarantined",
            )
        if _looks_like_prompt_injection(_joined_example_text(entry).lower()):
            validation.add(
                ValidationSeverity.ERROR,
                f"example_dialogues.{entry.id}",
                "Example dialogue contains prompt-control language and must be marked unsafe or removed.",
                code="example_dialogue_prompt_injection",
            )


def _joined_example_text(example: ExampleDialogue) -> str:
    return "\n".join(message.text for message in example.messages)


def _mentions_fact(text: str, fact_id: str, fact_text: str | None) -> bool:
    if fact_id.lower() in text:
        return True
    return bool(fact_text and fact_text.lower() in text)


def _looks_like_prompt_injection(text: str) -> bool:
    return any(
        token in text
        for token in (
            "ignore previous",
            "ignore all previous",
            "system prompt",
            "developer message",
            "reveal hidden",
            "bypass visibility",
            "modify gamestate",
            "state_delta",
        )
    )
