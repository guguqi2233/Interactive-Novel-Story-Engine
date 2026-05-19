from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.core.world_state import FactVisibility, QuestVisibility
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.crime import CRIME_TYPES
from app.llm.prompt_profiles import PromptProfileStore, get_default_prompt_profile_store


class ReferenceKind(StrEnum):
    LOCATION = "location"
    NPC = "NPC"
    ITEM = "item"
    FACT = "fact"
    QUEST = "quest"
    QUEST_STAGE = "quest_stage"
    FACTION = "faction"
    RELATIONSHIP = "relationship"
    RUMOR = "rumor"
    CRIME_TYPE = "crime type"
    RP_PROFILE = "RP profile"
    SCENE_MOOD = "scene mood"
    PROMPT_PROFILE = "prompt profile"


class ReferenceIndexItem(BaseModel):
    id: str
    kind: ReferenceKind
    label: str
    hidden: bool = False
    player_visible: bool = False
    authoring_safe_metadata: dict[str, Any] = Field(default_factory=dict)


class ReferenceIndex(BaseModel):
    local_only: bool = True
    world_id: str
    items: list[ReferenceIndexItem] = Field(default_factory=list)

    def by_kind(self, kind: ReferenceKind) -> list[ReferenceIndexItem]:
        return [item for item in self.items if item.kind == kind]


def build_reference_index(
    world_id: str,
    *,
    worlds_root: str = "worlds",
    prompt_profile_store: PromptProfileStore | None = None,
) -> ReferenceIndex:
    pack = WorldLoader(worlds_root).load(world_id)
    prompt_profiles = (prompt_profile_store or get_default_prompt_profile_store()).list_profiles()
    items: list[ReferenceIndexItem] = []

    for location in pack.locations:
        items.append(
            ReferenceIndexItem(
                id=location.id,
                kind=ReferenceKind.LOCATION,
                label=location.name,
                player_visible=True,
                authoring_safe_metadata={"exit_count": len(location.exits)},
            )
        )

    for npc in pack.npcs:
        hidden = bool(npc.hidden or not npc.visible)
        items.append(
            ReferenceIndexItem(
                id=npc.id,
                kind=ReferenceKind.NPC,
                label=_safe_label(npc.id, npc.name, hidden),
                hidden=hidden,
                player_visible=not hidden,
                authoring_safe_metadata={
                    "location_id": npc.location_id,
                    "faction_id": npc.faction_id,
                    "has_rp_profile": bool(npc.rp_profile.public_persona or npc.voice_profile.tone),
                },
            )
        )
        if npc.rp_profile.public_persona or npc.voice_profile.tone:
            items.append(
                ReferenceIndexItem(
                    id=npc.id,
                    kind=ReferenceKind.RP_PROFILE,
                    label=_safe_label(npc.id, npc.name, hidden),
                    hidden=hidden,
                    player_visible=False,
                    authoring_safe_metadata={"npc_id": npc.id, "private_fields_redacted": True},
                )
            )

    for item in pack.items:
        hidden = bool(item.hidden or not item.visible)
        items.append(
            ReferenceIndexItem(
                id=item.id,
                kind=ReferenceKind.ITEM,
                label=_safe_label(item.id, item.name, hidden),
                hidden=hidden,
                player_visible=not hidden,
                authoring_safe_metadata={
                    "location_id": item.location_id,
                    "owner_id": item.owner_id,
                    "tradeable": item.tradeable,
                    "base_price": item.base_price,
                },
            )
        )

    for fact in pack.facts:
        hidden = fact.visibility == FactVisibility.HIDDEN
        items.append(
            ReferenceIndexItem(
                id=fact.id,
                kind=ReferenceKind.FACT,
                label=fact.id if hidden else fact.text,
                hidden=hidden,
                player_visible=fact.visibility == FactVisibility.PUBLIC,
                authoring_safe_metadata={
                    "visibility": fact.visibility.value,
                    "tag_count": len(fact.tags),
                    "known_by_count": len(fact.known_by),
                    "text_redacted": hidden,
                },
            )
        )

    for quest in pack.quests:
        hidden = quest.visibility == QuestVisibility.HIDDEN
        items.append(
            ReferenceIndexItem(
                id=quest.id,
                kind=ReferenceKind.QUEST,
                label=_safe_label(quest.id, quest.title, hidden),
                hidden=hidden,
                player_visible=quest.visibility == QuestVisibility.PUBLIC,
                authoring_safe_metadata={"stage_count": len(quest.stages), "initial_stage": quest.initial_stage},
            )
        )
        for stage in quest.stages:
            items.append(
                ReferenceIndexItem(
                    id=f"{quest.id}:{stage.id}",
                    kind=ReferenceKind.QUEST_STAGE,
                    label=_safe_label(f"{quest.id}:{stage.id}", f"{quest.title} / {stage.title}", hidden),
                    hidden=hidden,
                    player_visible=quest.visibility == QuestVisibility.PUBLIC,
                    authoring_safe_metadata={"quest_id": quest.id, "stage_id": stage.id},
                )
            )

    for faction in pack.factions:
        hidden = not faction.known_by_player
        items.append(
            ReferenceIndexItem(
                id=faction.id,
                kind=ReferenceKind.FACTION,
                label=_safe_label(faction.id, faction.name, hidden),
                hidden=hidden,
                player_visible=faction.known_by_player,
                authoring_safe_metadata={
                    "alert_level": faction.default_alert_level,
                    "conflict_level": faction.default_conflict_level,
                    "tag_count": len(faction.tags),
                },
            )
        )

    for relationship in pack.relationships:
        hidden = bool(relationship.hidden_relationship or not relationship.known_by_player)
        items.append(
            ReferenceIndexItem(
                id=relationship.relationship_id(),
                kind=ReferenceKind.RELATIONSHIP,
                label=f"{relationship.source_id} {relationship.relation_type} {relationship.target_id}",
                hidden=hidden,
                player_visible=not hidden,
                authoring_safe_metadata={
                    "source_id": relationship.source_id,
                    "target_id": relationship.target_id,
                    "relation_type": relationship.relation_type,
                    "tone_preset": relationship.tone_preset,
                },
            )
        )

    for rumor in pack.rumors:
        hidden = not rumor.known_by_player
        items.append(
            ReferenceIndexItem(
                id=rumor.id,
                kind=ReferenceKind.RUMOR,
                label=_safe_label(rumor.id, rumor.text_for_player or rumor.id, hidden),
                hidden=hidden,
                player_visible=rumor.known_by_player,
                authoring_safe_metadata={
                    "fact_id": rumor.fact_id,
                    "truth_status": rumor.truth_status.value,
                    "spread_level": rumor.spread_level,
                },
            )
        )

    for crime_type in sorted(CRIME_TYPES):
        items.append(
            ReferenceIndexItem(
                id=crime_type,
                kind=ReferenceKind.CRIME_TYPE,
                label=crime_type.replace("_", " ").title(),
                player_visible=False,
            )
        )

    for preset in pack.scene_mood_presets:
        items.append(
            ReferenceIndexItem(
                id=preset.id,
                kind=ReferenceKind.SCENE_MOOD,
                label=preset.name,
                player_visible=False,
                authoring_safe_metadata={"tone": preset.tone, "pacing": preset.pacing},
            )
        )

    for profile in prompt_profiles:
        items.append(
            ReferenceIndexItem(
                id=profile.id,
                kind=ReferenceKind.PROMPT_PROFILE,
                label=profile.name,
                player_visible=False,
                authoring_safe_metadata={"enabled": profile.enabled, "scene_mood_preset_id": profile.scene_mood_preset_id},
            )
        )

    return ReferenceIndex(world_id=world_id, items=sorted(items, key=lambda item: (item.kind.value, item.id)))


def _safe_label(entity_id: str, label: str, hidden: bool) -> str:
    return entity_id if hidden else label
