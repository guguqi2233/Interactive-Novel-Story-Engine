from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

from app.core.world_state import (
    ExampleDialogue,
    ExampleDialogueVisibility,
    FactState,
    FactVisibility,
    EmotionalState,
    FactionState,
    GameState,
    LocationState,
    NPCGoalState,
    NPCState,
    NPCScheduleEntry,
    PlayerState,
    QuestStage,
    QuestState,
    QuestStatus,
    QuestTrigger,
    QuestTriggerAction,
    QuestTriggerType,
    QuestVisibility,
    ReputationState,
    RelationshipState,
    RPProfile,
    RumorState,
    RumorTruthStatus,
    SceneMoodPreset,
    VoiceProfile,
    WorldObjectState,
)


class WorldLoaderError(ValueError):
    """Raised when a content pack is missing or internally inconsistent."""


class WorldManifest(BaseModel):
    world_id: str
    name: str
    version: str = "0.1.0"
    start_location_id: str
    description: str = ""


class MapVisibility(StrEnum):
    PUBLIC = "public"
    HIDDEN = "hidden"
    DISCOVERABLE = "discoverable"


class MapVisualEdgeType(StrEnum):
    EXIT = "exit"
    ONE_WAY = "one_way"
    LOCKED = "locked"
    HIDDEN = "hidden"
    CONDITIONAL = "conditional"


class LocationVisualDef(BaseModel):
    x: float = Field(default=0.0, allow_inf_nan=False)
    y: float = Field(default=0.0, allow_inf_nan=False)
    region_id: str | None = None
    icon: str | None = None
    color_tag: str | None = None
    display_group: str | None = None
    notes: str | None = None
    visibility: MapVisibility = MapVisibility.PUBLIC
    tags: list[str] = Field(default_factory=list)


class MapVisualNode(BaseModel):
    id: str
    name: str
    location_id: str
    x: float = Field(default=0.0, allow_inf_nan=False)
    y: float = Field(default=0.0, allow_inf_nan=False)
    region_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    visibility: MapVisibility = MapVisibility.PUBLIC
    icon: str | None = None
    color_tag: str | None = None
    display_group: str | None = None


class MapVisualEdge(BaseModel):
    source_location_id: str
    target_location_id: str
    edge_type: MapVisualEdgeType = MapVisualEdgeType.EXIT
    label: str
    visibility: MapVisibility = MapVisibility.PUBLIC


class MapVisualGraph(BaseModel):
    nodes: list[MapVisualNode] = Field(default_factory=list)
    edges: list[MapVisualEdge] = Field(default_factory=list)


class LocationDef(BaseModel):
    id: str
    name: str
    description: str
    exits: dict[str, str] = Field(default_factory=dict)
    visible_objects: list[str] = Field(default_factory=list)
    cover_level: int = Field(default=0, ge=0)
    light_level: int = Field(default=5, ge=0)
    visual: LocationVisualDef | None = None


class NPCDef(BaseModel):
    id: str
    name: str
    location_id: str
    personality: str
    faction_id: str | None = None
    knowledge: list[str] = Field(default_factory=list)
    goals: list[str | NPCGoalState] = Field(default_factory=list)
    priorities: dict[str, int] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    current_goal_id: str | None = None
    plan_state: dict[str, Any] = Field(default_factory=dict)
    visible: bool = True
    hidden: bool = False
    discovered_by: list[str] = Field(default_factory=list)
    schedule: list[NPCScheduleEntry] = Field(default_factory=list)
    merchant: bool = False
    shop_inventory: list[str] = Field(default_factory=list)
    buy_price_modifier: float = Field(default=1.0, ge=0.0)
    sell_price_modifier: float = Field(default=0.5, ge=0.0)
    rp_profile: RPProfile = Field(default_factory=RPProfile)
    voice_profile: VoiceProfile = Field(default_factory=VoiceProfile)
    dialogue_style: str = ""
    speech_habits: list[str] = Field(default_factory=list)
    taboo_topics: list[str] = Field(default_factory=list)
    emotional_mask: str = ""
    example_dialogue_refs: list[str] = Field(default_factory=list)
    emotional_state: EmotionalState = Field(default_factory=EmotionalState)


class ItemDef(BaseModel):
    id: str
    name: str
    description: str = ""
    location_id: str | None = None
    owner_id: str | None = None
    container_id: str | None = None
    portable: bool = False
    visible: bool = True
    hidden: bool = False
    discoverable: bool = False
    discovered_by: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    base_price: int = Field(default=0, ge=0)
    tradeable: bool = True
    rarity: str = "common"
    locked: bool = False
    lock_difficulty: int = Field(default=0, ge=0)
    lock_state: str = "intact"

    @model_validator(mode="after")
    def validate_placement(self) -> "ItemDef":
        placements = [
            self.location_id is not None,
            self.owner_id is not None,
            self.container_id is not None,
        ]
        if sum(placements) == 0:
            raise ValueError("ItemDef requires location_id, owner_id, or container_id")
        if sum(placements) > 1:
            raise ValueError("ItemDef cannot have multiple placements")
        return self


class QuestStageDef(BaseModel):
    id: str
    title: str
    description: str = ""
    objectives: list[str] = Field(default_factory=list)
    next_stages: list[str] = Field(default_factory=list)
    failure_stages: list[str] = Field(default_factory=list)
    alternate_stages: list[str] = Field(default_factory=list)


class QuestTriggerDef(BaseModel):
    type: QuestTriggerType
    id: str
    action: QuestTriggerAction = QuestTriggerAction.ACTIVATE
    objective_id: str | None = None
    next_stage: str | None = None


class QuestDef(BaseModel):
    id: str
    title: str
    description: str = ""
    initial_stage: str
    stages: list[QuestStageDef]
    visibility: QuestVisibility = QuestVisibility.HIDDEN
    triggers: list[QuestTriggerDef] = Field(default_factory=list)
    rewards: list[str | dict[str, Any]] = Field(default_factory=list)


class FactDef(BaseModel):
    id: str
    text: str
    visibility: FactVisibility
    known_by: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class FactionDef(BaseModel):
    id: str
    name: str
    description: str = ""
    default_reputation: int = 0
    known_by_player: bool = False
    relations: dict[str, int] = Field(default_factory=dict)
    conflict_tags: list[str] = Field(default_factory=list)
    default_conflict_level: int = Field(default=0, ge=0)
    default_alert_level: int = Field(default=0, ge=0)
    resources: dict[str, int | float | str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def accept_v041_field_names(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "default_reputation" not in normalized and "initial_reputation" in normalized:
            normalized["default_reputation"] = normalized["initial_reputation"]
        if "known_by_player" not in normalized and "known_to_player" in normalized:
            normalized["known_by_player"] = normalized["known_to_player"]
        return normalized


class RumorDef(BaseModel):
    id: str
    source_event_id: str | None = None
    fact_id: str | None = None
    text_for_player: str | None = None
    truth_status: RumorTruthStatus = RumorTruthStatus.UNKNOWN
    known_by_npcs: list[str] = Field(default_factory=list)
    known_by_factions: list[str] = Field(default_factory=list)
    known_by_player: bool = False
    spread_level: int = Field(default=0, ge=0)
    created_turn: int = 0
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_field_names(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if "text_for_player" not in normalized and "text" in normalized:
            normalized["text_for_player"] = normalized["text"]
        if "known_by_npcs" not in normalized and "known_by" in normalized:
            normalized["known_by_npcs"] = normalized["known_by"]
        if "known_by_player" not in normalized and "known_to_player" in normalized:
            normalized["known_by_player"] = normalized["known_to_player"]
        if "spread_level" not in normalized and "credibility" in normalized:
            normalized["spread_level"] = normalized["credibility"]
        return normalized


class RelationshipDef(BaseModel):
    id: str | None = None
    source_id: str
    target_id: str
    relation_type: str
    trust: int = 0
    fear: int = 0
    affinity: int = 0
    obligation: int = 0
    tags: list[str] = Field(default_factory=list)
    known_by_player: bool = False

    def relationship_id(self) -> str:
        return self.id or f"{self.source_id}:{self.relation_type}:{self.target_id}"


class WorldPack(BaseModel):
    manifest: WorldManifest
    locations: list[LocationDef]
    npcs: list[NPCDef]
    items: list[ItemDef] = Field(default_factory=list)
    quests: list[QuestDef] = Field(default_factory=list)
    facts: list[FactDef] = Field(default_factory=list)
    factions: list[FactionDef] = Field(default_factory=list)
    rumors: list[RumorDef] = Field(default_factory=list)
    relationships: list[RelationshipDef] = Field(default_factory=list)
    scene_mood_presets: list[SceneMoodPreset] = Field(default_factory=list)
    example_dialogues: list[ExampleDialogue] = Field(default_factory=list)

    def to_game_state(self) -> GameState:
        factions = {
            faction.id: FactionState(
                id=faction.id,
                name=faction.name,
                description=faction.description,
                reputation=ReputationState(
                    value=faction.default_reputation,
                    known_to_player=faction.known_by_player,
                ),
                relationships_to_other_factions=faction.relations,
                conflict_level=faction.default_conflict_level,
                alert_level=faction.default_alert_level,
                resources=faction.resources,
                known_by_player=faction.known_by_player,
                conflict_tags=faction.conflict_tags,
                tags=faction.tags,
            )
            for faction in self.factions
        }
        facts = {
            fact.id: FactState(
                id=fact.id,
                text=fact.text,
                visibility=fact.visibility,
                public=fact.visibility == FactVisibility.PUBLIC,
                secret=fact.visibility == FactVisibility.HIDDEN,
                known_by=set(fact.known_by),
                tags=fact.tags,
            )
            for fact in self.facts
        }
        quests = {
            quest.id: QuestState(
                id=quest.id,
                title=quest.title,
                description=quest.description,
                initial_stage=quest.initial_stage,
                current_stage=quest.initial_stage,
                stages={
                    stage.id: QuestStage(
                        id=stage.id,
                        title=stage.title,
                        description=stage.description,
                        objectives=stage.objectives,
                        next_stages=stage.next_stages,
                    )
                    for stage in quest.stages
                },
                visibility=quest.visibility,
                status=(
                    QuestStatus.ACTIVE
                    if quest.visibility == QuestVisibility.PUBLIC
                    else QuestStatus.INACTIVE
                ),
                known_to_player=quest.visibility == QuestVisibility.PUBLIC,
                triggers=[
                    QuestTrigger(
                        type=trigger.type,
                        id=trigger.id,
                        action=trigger.action,
                        objective_id=trigger.objective_id,
                        next_stage=trigger.next_stage,
                    )
                    for trigger in quest.triggers
                ],
            )
            for quest in self.quests
        }
        rumors = {
            rumor.id: RumorState(
                id=rumor.id,
                source_event_id=rumor.source_event_id,
                fact_id=rumor.fact_id,
                text_for_player=rumor.text_for_player,
                truth_status=rumor.truth_status,
                known_by_npcs=set(rumor.known_by_npcs),
                known_by_factions=set(rumor.known_by_factions),
                known_by_player=rumor.known_by_player,
                spread_level=rumor.spread_level,
                created_turn=rumor.created_turn,
                text=rumor.text_for_player,
                known_by=set(rumor.known_by_npcs) | set(rumor.known_by_factions),
                credibility=rumor.spread_level,
                known_to_player=rumor.known_by_player,
                tags=rumor.tags,
            )
            for rumor in self.rumors
        }
        relationships = {
            relationship.relationship_id(): RelationshipState(
                id=relationship.relationship_id(),
                source_id=relationship.source_id,
                target_id=relationship.target_id,
                relation_type=relationship.relation_type,
                trust=relationship.trust,
                fear=relationship.fear,
                affinity=relationship.affinity,
                obligation=relationship.obligation,
                tags=relationship.tags,
                known_by_player=relationship.known_by_player,
            )
            for relationship in self.relationships
        }
        return GameState(
            world_id=self.manifest.world_id,
            player=PlayerState(location_id=self.manifest.start_location_id),
            locations={
                location.id: LocationState(
                    id=location.id,
                    name=location.name,
                    exits=_runtime_visible_exits(location, self.locations),
                    visible_objects=location.visible_objects,
                    cover_level=location.cover_level,
                    light_level=location.light_level,
                )
                for location in self.locations
            },
            objects={
                item.id: WorldObjectState(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    location_id=item.location_id,
                    owner_id=item.owner_id,
                    container_id=item.container_id,
                    portable=item.portable,
                    visible=item.visible,
                    hidden=item.hidden,
                    discoverable=item.discoverable,
                    discovered_by=item.discovered_by,
                    tags=item.tags,
                    base_price=item.base_price,
                    tradeable=item.tradeable,
                    rarity=item.rarity,
                    locked=item.locked,
                    lock_difficulty=item.lock_difficulty,
                    lock_state=item.lock_state,
                )
                for item in self.items
            },
            npcs={
                npc.id: NPCState(
                    id=npc.id,
                    location_id=npc.location_id,
                    faction_id=npc.faction_id,
                    visible=npc.visible,
                    hidden=npc.hidden,
                    discovered_by=npc.discovered_by,
                    knowledge=npc.knowledge,
                    goals=npc.goals,
                    priorities=npc.priorities,
                    constraints=npc.constraints,
                    current_goal_id=npc.current_goal_id,
                    plan_state=npc.plan_state,
                    schedule=npc.schedule,
                    merchant=npc.merchant,
                    shop_inventory=npc.shop_inventory,
                    buy_price_modifier=npc.buy_price_modifier,
                    sell_price_modifier=npc.sell_price_modifier,
                    rp_profile=npc.rp_profile,
                    voice_profile=npc.voice_profile,
                    dialogue_style=npc.dialogue_style,
                    speech_habits=npc.speech_habits,
                    taboo_topics=npc.taboo_topics,
                    emotional_mask=npc.emotional_mask,
                    example_dialogue_refs=npc.example_dialogue_refs,
                    emotional_state=npc.emotional_state,
                )
                for npc in self.npcs
            },
            npc_knowledge={npc.id: set(npc.knowledge) for npc in self.npcs},
            facts=facts,
            player_visible_facts={
                fact.id for fact in self.facts if fact.visibility == FactVisibility.PUBLIC
            },
            quests=quests,
            factions=factions,
            rumors=rumors,
            relationships=relationships,
            scene_mood_presets={preset.id: preset for preset in self.scene_mood_presets},
            example_dialogues={example.id: example for example in self.example_dialogues},
        )


def _runtime_visible_exits(location: LocationDef, locations: list[LocationDef]) -> dict[str, str]:
    """Keep authoring-hidden locations out of player-visible runtime exits."""
    by_id = {item.id: item for item in locations}
    visible_exits: dict[str, str] = {}
    for label, target_id in location.exits.items():
        target = by_id.get(target_id)
        if target is None:
            visible_exits[label] = target_id
            continue
        source_visibility = location.visual.visibility if location.visual else MapVisibility.PUBLIC
        target_visibility = target.visual.visibility if target.visual else MapVisibility.PUBLIC
        if source_visibility == MapVisibility.HIDDEN or target_visibility == MapVisibility.HIDDEN:
            continue
        visible_exits[label] = target_id
    return visible_exits


class WorldLoader:
    def __init__(self, worlds_root: str | Path = "worlds") -> None:
        self.worlds_root = Path(worlds_root)

    def load(self, world_id: str) -> WorldPack:
        world_path = self.worlds_root / world_id
        if not world_path.exists():
            raise WorldLoaderError(f"World pack not found: {world_id}")

        try:
            pack = WorldPack(
                manifest=WorldManifest.model_validate(_read_yaml_file(world_path / "manifest.yaml")),
                locations=[
                    LocationDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "locations.yaml", "locations")
                ],
                npcs=[
                    NPCDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "npcs.yaml", "npcs")
                ],
                items=[
                    ItemDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "items.yaml", "items", required=False)
                ],
                quests=[
                    QuestDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "quests.yaml", "quests", required=False)
                ],
                facts=[
                    FactDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "facts.yaml", "facts", required=False)
                ],
                factions=[
                    FactionDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "factions.yaml", "factions", required=False)
                ],
                rumors=[
                    RumorDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "rumors.yaml", "rumors", required=False)
                ],
                relationships=[
                    RelationshipDef.model_validate(item)
                    for item in _read_yaml_list(world_path / "relationships.yaml", "relationships", required=False)
                ],
                scene_mood_presets=[
                    SceneMoodPreset.model_validate(item)
                    for item in _read_yaml_list(world_path / "scene_moods.yaml", "scene_mood_presets", required=False)
                ],
                example_dialogues=[
                    ExampleDialogue.model_validate(item)
                    for item in _read_yaml_list(world_path / "example_dialogues.yaml", "example_dialogues", required=False)
                ],
            )
        except ValidationError as exc:
            raise WorldLoaderError(f"World pack schema validation failed: {exc}") from exc

        self._validate_references(pack)
        return pack

    def _validate_references(self, pack: WorldPack) -> None:
        location_ids = {location.id for location in pack.locations}
        npc_ids = {npc.id for npc in pack.npcs}
        faction_ids = {faction.id for faction in pack.factions}
        item_ids = {item.id for item in pack.items}

        if pack.manifest.start_location_id not in location_ids:
            raise WorldLoaderError(
                f"Manifest start_location_id does not exist: {pack.manifest.start_location_id}"
            )

        for location in pack.locations:
            for direction, target_location_id in location.exits.items():
                if target_location_id not in location_ids:
                    raise WorldLoaderError(
                        f"Location {location.id} exit {direction} points to missing location: "
                        f"{target_location_id}"
                    )

        for npc in pack.npcs:
            if npc.location_id not in location_ids:
                raise WorldLoaderError(
                    f"NPC {npc.id} references missing location_id: {npc.location_id}"
                )
            if npc.faction_id and npc.faction_id not in faction_ids:
                raise WorldLoaderError(
                    f"NPC {npc.id} references missing faction_id: {npc.faction_id}"
                )
            for schedule_entry in npc.schedule:
                if schedule_entry.location_id not in location_ids:
                    raise WorldLoaderError(
                        f"NPC {npc.id} schedule references missing location_id: "
                        f"{schedule_entry.location_id}"
                    )
            for item_id in npc.shop_inventory:
                if item_id not in item_ids:
                    raise WorldLoaderError(
                        f"NPC {npc.id} shop_inventory references missing item id: {item_id}"
                    )

        for faction in pack.factions:
            for target_faction_id in faction.relations:
                if target_faction_id not in faction_ids:
                    raise WorldLoaderError(
                        f"Faction {faction.id} relation references missing faction id: {target_faction_id}"
                    )

        for item in pack.items:
            has_valid_location = item.location_id in location_ids if item.location_id else False
            has_valid_owner = item.owner_id in npc_ids or item.owner_id == "player" if item.owner_id else False
            has_container = item.container_id is not None
            if not has_valid_location and not has_valid_owner and not has_container:
                raise WorldLoaderError(
                    f"Item {item.id} must reference an existing location_id, owner_id, or container_id"
                )

        for fact in pack.facts:
            for actor_id in fact.known_by:
                if actor_id != "player" and actor_id not in npc_ids:
                    raise WorldLoaderError(
                        f"Fact {fact.id} known_by references missing NPC id: {actor_id}"
                    )

        fact_ids = {fact.id for fact in pack.facts}
        actor_ids = npc_ids | {"player"}
        for rumor in pack.rumors:
            if rumor.fact_id and rumor.fact_id not in fact_ids:
                raise WorldLoaderError(
                    f"Rumor {rumor.id} references missing fact id: {rumor.fact_id}"
                )
            for npc_id in rumor.known_by_npcs:
                if npc_id not in npc_ids and npc_id not in faction_ids:
                    raise WorldLoaderError(
                        f"Rumor {rumor.id} known_by_npcs references missing NPC id: {npc_id}"
                    )
            for faction_id in rumor.known_by_factions:
                if faction_id not in faction_ids:
                    raise WorldLoaderError(
                        f"Rumor {rumor.id} known_by_factions references missing faction id: {faction_id}"
                    )
        relationship_ids: set[str] = set()
        for relationship in pack.relationships:
            relationship_id = relationship.relationship_id()
            if relationship_id in relationship_ids:
                raise WorldLoaderError(f"Duplicate relationship id: {relationship_id}")
            relationship_ids.add(relationship_id)
            if relationship.source_id not in actor_ids:
                raise WorldLoaderError(
                    f"Relationship {relationship_id} source_id references missing NPC id: {relationship.source_id}"
                )
            if relationship.target_id not in actor_ids:
                raise WorldLoaderError(
                    f"Relationship {relationship_id} target_id references missing NPC id: {relationship.target_id}"
                )
        for quest in pack.quests:
            stage_ids = {stage.id for stage in quest.stages}
            if quest.initial_stage not in stage_ids:
                raise WorldLoaderError(
                    f"Quest {quest.id} initial_stage does not exist: {quest.initial_stage}"
                )
            for stage in quest.stages:
                for next_stage in stage.next_stages:
                    if next_stage not in stage_ids:
                        raise WorldLoaderError(
                            f"Quest {quest.id} stage {stage.id} references missing next_stage: "
                            f"{next_stage}"
                        )
                for failure_stage in stage.failure_stages:
                    if failure_stage not in stage_ids:
                        raise WorldLoaderError(
                            f"Quest {quest.id} stage {stage.id} references missing failure_stage: "
                            f"{failure_stage}"
                        )
                for alternate_stage in stage.alternate_stages:
                    if alternate_stage not in stage_ids:
                        raise WorldLoaderError(
                            f"Quest {quest.id} stage {stage.id} references missing alternate_stage: "
                            f"{alternate_stage}"
                        )
            objective_ids = {
                objective_id
                for stage in quest.stages
                for objective_id in stage.objectives
            }
            for trigger in quest.triggers:
                if trigger.type == QuestTriggerType.FACT_DISCOVERED and trigger.id not in fact_ids:
                    raise WorldLoaderError(
                        f"Quest {quest.id} trigger references missing fact id: {trigger.id}"
                    )
                if trigger.type == QuestTriggerType.ITEM_ACQUIRED and trigger.id not in item_ids:
                    raise WorldLoaderError(
                        f"Quest {quest.id} trigger references missing item id: {trigger.id}"
                    )
                if trigger.type == QuestTriggerType.NPC_TALKED and trigger.id not in npc_ids:
                    raise WorldLoaderError(
                        f"Quest {quest.id} trigger references missing NPC id: {trigger.id}"
                    )
                if trigger.type == QuestTriggerType.LOCATION_VISITED and trigger.id not in location_ids:
                    raise WorldLoaderError(
                        f"Quest {quest.id} trigger references missing location id: {trigger.id}"
                    )
                if trigger.type == QuestTriggerType.FACTION_REPUTATION and trigger.id not in faction_ids:
                    raise WorldLoaderError(
                        f"Quest {quest.id} trigger references missing faction id: {trigger.id}"
                    )
                if trigger.objective_id and trigger.objective_id not in objective_ids:
                    raise WorldLoaderError(
                        f"Quest {quest.id} trigger references missing objective id: "
                        f"{trigger.objective_id}"
                    )
                if trigger.next_stage and trigger.next_stage not in stage_ids:
                    raise WorldLoaderError(
                        f"Quest {quest.id} trigger references missing next_stage: "
                        f"{trigger.next_stage}"
                    )

        mood_preset_ids: set[str] = set()
        for preset in pack.scene_mood_presets:
            if preset.id in mood_preset_ids:
                raise WorldLoaderError(f"Duplicate scene mood preset id: {preset.id}")
            mood_preset_ids.add(preset.id)

        example_ids: set[str] = set()
        facts_by_id = {fact.id: fact for fact in pack.facts}
        for example in pack.example_dialogues:
            if example.id in example_ids:
                raise WorldLoaderError(f"Duplicate example dialogue id: {example.id}")
            example_ids.add(example.id)
            if example.character_id not in npc_ids:
                raise WorldLoaderError(
                    f"Example dialogue {example.id} references missing character_id: {example.character_id}"
                )
            if example.visibility == ExampleDialogueVisibility.PROMPT_SAFE:
                unsafe_fact_id = _prompt_unsafe_example_fact_id(example, facts_by_id)
                if unsafe_fact_id is not None:
                    raise WorldLoaderError(
                        f"Example dialogue {example.id} references hidden or unknown fact in prompt_safe content: "
                        f"{unsafe_fact_id}"
                    )

        if example_ids:
            for npc in pack.npcs:
                for example_id in npc.example_dialogue_refs:
                    if example_id not in example_ids:
                        raise WorldLoaderError(
                            f"NPC {npc.id} example_dialogue_refs references missing example dialogue id: {example_id}"
                        )


def _read_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise WorldLoaderError(f"Missing content file: {path.name}")
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise WorldLoaderError(f"Expected YAML mapping in file: {path.name}")
    return data


def _read_yaml_list(path: Path, key: str, required: bool = True) -> list[dict[str, Any]]:
    if not path.exists():
        if required:
            raise WorldLoaderError(f"Missing content file: {path.name}")
        return []
    data = _read_yaml_file(path)
    raw_items = data.get(key, [])
    if not isinstance(raw_items, list):
        raise WorldLoaderError(f"Expected list key '{key}' in file: {path.name}")
    return [_ensure_mapping(item, path.name) for item in raw_items]


def _ensure_mapping(item: Any, filename: str) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise WorldLoaderError(f"Expected mapping items in file: {filename}")
    return item


def _prompt_unsafe_example_fact_id(example: ExampleDialogue, facts_by_id: dict[str, FactDef]) -> str | None:
    text = " ".join(message.text for message in example.messages).lower()
    for fact in facts_by_id.values():
        if not _example_mentions_fact(text, fact):
            continue
        player_knows = fact.visibility == FactVisibility.PUBLIC or "player" in fact.known_by
        npc_knows_fact = example.character_id in fact.known_by
        if not (player_knows and npc_knows_fact):
            return fact.id
    return None


def _example_mentions_fact(example_text: str, fact: FactDef) -> bool:
    if fact.id.lower() in example_text:
        return True
    return bool(fact.text and fact.text.lower() in example_text)
