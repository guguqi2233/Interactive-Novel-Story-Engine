from collections import Counter, defaultdict
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.world_state import FactVisibility, QuestTriggerType, QuestVisibility
from app.engine.content.world_loader import (
    FactDef,
    FactionDef,
    ItemDef,
    LocationDef,
    NPCDef,
    QuestDef,
    RumorDef,
    WorldLoaderError,
    WorldManifest,
)


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    SUGGESTION = "suggestion"


class ValidationIssue(BaseModel):
    severity: ValidationSeverity
    path: str
    message: str


class ValidationReport(BaseModel):
    world_id: str
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    suggestions: list[ValidationIssue] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, severity: ValidationSeverity, path: str, message: str) -> None:
        issue = ValidationIssue(severity=severity, path=path, message=message)
        if severity == ValidationSeverity.ERROR:
            self.errors.append(issue)
        elif severity == ValidationSeverity.WARNING:
            self.warnings.append(issue)
        else:
            self.suggestions.append(issue)


class RawWorldPack(BaseModel):
    manifest: WorldManifest | None = None
    locations: list[LocationDef] = Field(default_factory=list)
    npcs: list[NPCDef] = Field(default_factory=list)
    items: list[ItemDef] = Field(default_factory=list)
    quests: list[QuestDef] = Field(default_factory=list)
    facts: list[FactDef] = Field(default_factory=list)
    factions: list[FactionDef] = Field(default_factory=list)
    rumors: list[RumorDef] = Field(default_factory=list)


CONTENT_FILES: dict[str, str] = {
    "locations.yaml": "locations",
    "npcs.yaml": "npcs",
    "items.yaml": "items",
    "quests.yaml": "quests",
    "facts.yaml": "facts",
    "factions.yaml": "factions",
    "rumors.yaml": "rumors",
}


def validate_world_pack(world_id: str, worlds_root: str | Path = "worlds") -> ValidationReport:
    world_path = Path(worlds_root) / world_id
    report = ValidationReport(world_id=world_id)
    if not world_path.exists():
        report.add(ValidationSeverity.ERROR, str(world_path), f"World pack not found: {world_id}")
        return report

    pack = _load_raw_pack(world_path, report)
    _validate_unique_ids(pack, report)
    _validate_references(pack, report)
    _validate_visibility_boundaries(pack, report)
    _add_authoring_suggestions(pack, report)
    return report


def format_validation_report(report: ValidationReport) -> str:
    lines = [
        f"World validation report: {report.world_id}",
        f"errors: {len(report.errors)}",
        f"warnings: {len(report.warnings)}",
        f"suggestions: {len(report.suggestions)}",
    ]
    for title, issues in (
        ("ERRORS", report.errors),
        ("WARNINGS", report.warnings),
        ("SUGGESTIONS", report.suggestions),
    ):
        if not issues:
            continue
        lines.append("")
        lines.append(title)
        for issue in issues:
            lines.append(f"- [{issue.severity}] {issue.path}: {issue.message}")
    return "\n".join(lines)


def _load_raw_pack(world_path: Path, report: ValidationReport) -> RawWorldPack:
    manifest = _load_model(
        world_path / "manifest.yaml",
        WorldManifest,
        report,
        required=True,
    )
    return RawWorldPack(
        manifest=manifest,
        locations=_load_model_list(world_path / "locations.yaml", "locations", LocationDef, report),
        npcs=_load_model_list(world_path / "npcs.yaml", "npcs", NPCDef, report),
        items=_load_model_list(world_path / "items.yaml", "items", ItemDef, report),
        quests=_load_model_list(world_path / "quests.yaml", "quests", QuestDef, report),
        facts=_load_model_list(world_path / "facts.yaml", "facts", FactDef, report),
        factions=_load_model_list(world_path / "factions.yaml", "factions", FactionDef, report),
        rumors=_load_model_list(world_path / "rumors.yaml", "rumors", RumorDef, report),
    )


def _load_model(
    path: Path,
    model_type: type[WorldManifest],
    report: ValidationReport,
    *,
    required: bool,
) -> WorldManifest | None:
    if not path.exists():
        if required:
            report.add(ValidationSeverity.ERROR, path.name, f"Missing content file: {path.name}")
        return None
    try:
        data = _read_yaml_mapping(path)
        return model_type.model_validate(data)
    except (WorldLoaderError, ValidationError, ValueError) as exc:
        report.add(ValidationSeverity.ERROR, path.name, f"Schema validation failed: {exc}")
        return None


def _load_model_list(
    path: Path,
    key: str,
    model_type: type[LocationDef]
    | type[NPCDef]
    | type[ItemDef]
    | type[QuestDef]
    | type[FactDef]
    | type[FactionDef]
    | type[RumorDef],
    report: ValidationReport,
) -> list[Any]:
    if not path.exists():
        report.add(ValidationSeverity.ERROR, path.name, f"Missing content file: {path.name}")
        return []
    try:
        data = _read_yaml_mapping(path)
    except WorldLoaderError as exc:
        report.add(ValidationSeverity.ERROR, path.name, str(exc))
        return []
    raw_items = data.get(key, [])
    if not isinstance(raw_items, list):
        report.add(ValidationSeverity.ERROR, path.name, f"Expected list key: {key}")
        return []

    parsed_items: list[Any] = []
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            report.add(
                ValidationSeverity.ERROR,
                f"{path.name}.{key}[{index}]",
                "Expected mapping item",
            )
            continue
        try:
            parsed_items.append(model_type.model_validate(item))
        except ValidationError as exc:
            item_id = item.get("id", index)
            report.add(
                ValidationSeverity.ERROR,
                f"{path.name}.{key}[{item_id}]",
                f"Schema validation failed: {exc}",
            )
    return parsed_items


def _validate_unique_ids(pack: RawWorldPack, report: ValidationReport) -> None:
    groups: dict[str, list[str]] = {
        "locations": [item.id for item in pack.locations],
        "npcs": [item.id for item in pack.npcs],
        "items": [item.id for item in pack.items],
        "quests": [item.id for item in pack.quests],
        "facts": [item.id for item in pack.facts],
        "factions": [item.id for item in pack.factions],
        "rumors": [item.id for item in pack.rumors],
    }
    for group_name, ids in groups.items():
        for item_id, count in Counter(ids).items():
            if count > 1:
                report.add(
                    ValidationSeverity.ERROR,
                    group_name,
                    f"Duplicate id within {group_name}: {item_id}",
                )

    owners: dict[str, list[str]] = defaultdict(list)
    for group_name, ids in groups.items():
        for item_id in ids:
            owners[item_id].append(group_name)
    for item_id, group_names in owners.items():
        if len(group_names) > 1:
            report.add(
                ValidationSeverity.WARNING,
                "ids",
                f"Id is reused across content types: {item_id} ({', '.join(group_names)})",
            )


def _validate_references(pack: RawWorldPack, report: ValidationReport) -> None:
    location_ids = {location.id for location in pack.locations}
    npc_ids = {npc.id for npc in pack.npcs}
    item_ids = {item.id for item in pack.items}
    fact_ids = {fact.id for fact in pack.facts}
    faction_ids = {faction.id for faction in pack.factions}

    if pack.manifest and pack.manifest.start_location_id not in location_ids:
        report.add(
            ValidationSeverity.ERROR,
            "manifest.yaml.start_location_id",
            f"Missing location: {pack.manifest.start_location_id}",
        )

    for location in pack.locations:
        for direction, target_location_id in location.exits.items():
            if target_location_id not in location_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"locations.yaml.{location.id}.exits.{direction}",
                    f"Exit points to missing location: {target_location_id}",
                )
        for object_id in location.visible_objects:
            if object_id not in item_ids:
                report.add(
                    ValidationSeverity.WARNING,
                    f"locations.yaml.{location.id}.visible_objects",
                    f"Visible object is not defined in items.yaml: {object_id}",
                )

    for npc in pack.npcs:
        if npc.location_id not in location_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"npcs.yaml.{npc.id}.location_id",
                f"NPC references missing location: {npc.location_id}",
            )
        if npc.faction_id and npc.faction_id not in faction_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"npcs.yaml.{npc.id}.faction_id",
                f"NPC references missing faction: {npc.faction_id}",
            )
        for schedule_index, schedule_entry in enumerate(npc.schedule):
            if schedule_entry.location_id not in location_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"npcs.yaml.{npc.id}.schedule[{schedule_index}].location_id",
                    f"Schedule references missing location: {schedule_entry.location_id}",
                )

    for item in pack.items:
        placements = [
            item.location_id is not None,
            item.owner_id is not None,
            item.container_id is not None,
        ]
        if sum(placements) > 1:
            report.add(
                ValidationSeverity.ERROR,
                f"items.yaml.{item.id}",
                "Item cannot have multiple placements",
            )
        if item.location_id and item.location_id not in location_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"items.yaml.{item.id}.location_id",
                f"Item references missing location: {item.location_id}",
            )
        if item.owner_id and item.owner_id != "player" and item.owner_id not in npc_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"items.yaml.{item.id}.owner_id",
                f"Item references missing owner: {item.owner_id}",
            )
        if item.container_id and item.container_id not in item_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"items.yaml.{item.id}.container_id",
                f"Item references missing container: {item.container_id}",
            )
        if item.lock_difficulty < 0:
            report.add(
                ValidationSeverity.ERROR,
                f"items.yaml.{item.id}.lock_difficulty",
                "Lock difficulty must be non-negative",
            )

    for fact in pack.facts:
        for actor_id in fact.known_by:
            if actor_id != "player" and actor_id not in npc_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"facts.yaml.{fact.id}.known_by",
                    f"Fact known_by references missing NPC: {actor_id}",
                )

    for rumor in pack.rumors:
        if rumor.fact_id and rumor.fact_id not in fact_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"rumors.yaml.{rumor.id}.fact_id",
                f"Rumor references missing fact: {rumor.fact_id}",
            )
        for npc_id in rumor.known_by_npcs:
            if npc_id not in npc_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"rumors.yaml.{rumor.id}.known_by_npcs",
                    f"Rumor references missing NPC: {npc_id}",
                )
        for faction_id in rumor.known_by_factions:
            if faction_id not in faction_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"rumors.yaml.{rumor.id}.known_by_factions",
                    f"Rumor references missing faction: {faction_id}",
                )

    for quest in pack.quests:
        _validate_quest(quest, report, fact_ids, item_ids, npc_ids, location_ids)


def _validate_quest(
    quest: QuestDef,
    report: ValidationReport,
    fact_ids: set[str],
    item_ids: set[str],
    npc_ids: set[str],
    location_ids: set[str],
) -> None:
    stage_ids = {stage.id for stage in quest.stages}
    objective_ids = {
        objective_id
        for stage in quest.stages
        for objective_id in stage.objectives
    }
    if quest.initial_stage not in stage_ids:
        report.add(
            ValidationSeverity.ERROR,
            f"quests.yaml.{quest.id}.initial_stage",
            f"Initial stage does not exist: {quest.initial_stage}",
        )
    for stage in quest.stages:
        for next_stage in stage.next_stages:
            if next_stage not in stage_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"quests.yaml.{quest.id}.stages.{stage.id}.next_stages",
                    f"Next stage does not exist: {next_stage}",
                )
    for trigger in quest.triggers:
        if trigger.type == QuestTriggerType.FACT_DISCOVERED and trigger.id not in fact_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"quests.yaml.{quest.id}.triggers.{trigger.id}",
                f"Trigger references missing fact: {trigger.id}",
            )
        if trigger.type == QuestTriggerType.ITEM_ACQUIRED and trigger.id not in item_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"quests.yaml.{quest.id}.triggers.{trigger.id}",
                f"Trigger references missing item: {trigger.id}",
            )
        if trigger.type == QuestTriggerType.NPC_TALKED and trigger.id not in npc_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"quests.yaml.{quest.id}.triggers.{trigger.id}",
                f"Trigger references missing NPC: {trigger.id}",
            )
        if trigger.type == QuestTriggerType.LOCATION_VISITED and trigger.id not in location_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"quests.yaml.{quest.id}.triggers.{trigger.id}",
                f"Trigger references missing location: {trigger.id}",
            )
        if trigger.objective_id and trigger.objective_id not in objective_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"quests.yaml.{quest.id}.triggers.{trigger.id}.objective_id",
                f"Trigger references missing objective: {trigger.objective_id}",
            )
        if trigger.next_stage and trigger.next_stage not in stage_ids:
            report.add(
                ValidationSeverity.ERROR,
                f"quests.yaml.{quest.id}.triggers.{trigger.id}.next_stage",
                f"Trigger references missing stage: {trigger.next_stage}",
            )


def _validate_visibility_boundaries(pack: RawWorldPack, report: ValidationReport) -> None:
    hidden_facts = {
        fact.id: fact
        for fact in pack.facts
        if fact.visibility == FactVisibility.HIDDEN
    }
    for fact_id, fact in hidden_facts.items():
        if "player" in fact.known_by:
            report.add(
                ValidationSeverity.WARNING,
                f"facts.yaml.{fact_id}.known_by",
                "Hidden fact is marked known_by player; prefer public/discoverable visibility or remove player.",
            )

    for rumor in pack.rumors:
        if not rumor.fact_id or rumor.fact_id not in hidden_facts or not rumor.text_for_player:
            continue
        hidden_text = (hidden_facts[rumor.fact_id].text or "").strip().lower()
        rumor_text = rumor.text_for_player.strip().lower()
        if rumor.known_by_player and hidden_text and hidden_text in rumor_text:
            report.add(
                ValidationSeverity.WARNING,
                f"rumors.yaml.{rumor.id}.text_for_player",
                "Player-known rumor appears to include the full hidden fact text.",
            )

    for quest in pack.quests:
        if quest.visibility != QuestVisibility.PUBLIC:
            continue
        public_text = " ".join([quest.title, quest.description]).lower()
        for fact_id, fact in hidden_facts.items():
            hidden_text = (fact.text or "").strip().lower()
            if hidden_text and hidden_text in public_text:
                report.add(
                    ValidationSeverity.WARNING,
                    f"quests.yaml.{quest.id}",
                    f"Public quest text appears to reveal hidden fact: {fact_id}",
                )


def _add_authoring_suggestions(pack: RawWorldPack, report: ValidationReport) -> None:
    if not pack.factions:
        report.add(
            ValidationSeverity.SUGGESTION,
            "factions.yaml",
            "Add at least one faction before using reputation or crime consequences.",
        )
    if not pack.rumors:
        report.add(
            ValidationSeverity.SUGGESTION,
            "rumors.yaml",
            "Seed rumors are optional, but useful for social consequence testing.",
        )


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
    except yaml.YAMLError as exc:
        raise WorldLoaderError(f"Invalid YAML in file: {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise WorldLoaderError(f"Expected YAML mapping in file: {path.name}")
    return data
