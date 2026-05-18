from collections.abc import Callable
from random import Random
from uuid import uuid4

from app.core.event_log import Event, EventLog
from app.core.game_loop import GameLoop
from app.core.world_state import CombatState, GameState
from app.api import (
    KnownFactResponse,
    VisibleLocationResponse,
    VisibleNPCResponse,
    VisibleObjectResponse,
    VisibleFactionResponse,
    VisibleRumorResponse,
    VisibleCrimeResponse,
    VisibleCombatSummaryResponse,
    VisibleRelationshipResponse,
    VisibleFactionConflictResponse,
    VisibleQuestObjectiveResponse,
    VisibleQuestResponse,
    VisibleStateResponse,
    VisibleTimeResponse,
)
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.inventory import get_inventory
from app.engine.rules.factions import get_visible_factions
from app.engine.rules.crime import get_player_known_crimes
from app.engine.rules.quests import get_visible_quests
from app.engine.rules.rumors import get_visible_rumors
from app.engine.rules.relationships import get_visible_relationships
from app.engine.rules.faction_conflict import get_visible_faction_conflicts
from app.engine.rules.time import format_game_time, get_time_of_day
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.llm.provider_factory import create_llm_provider
from app.llm.provider_base import LLMProvider
from app.llm.prompt_profiles import get_default_prompt_profile_store

ProviderFactory = Callable[[], LLMProvider]


class InMemorySessionStore:
    def __init__(
        self,
        provider_factory: ProviderFactory | None = None,
        worlds_root: str = "worlds",
        default_world_id: str = "mist_valley",
    ) -> None:
        self._sessions: dict[str, GameLoop] = {}
        self._provider_factory = provider_factory or create_llm_provider
        self._world_loader = WorldLoader(worlds_root)
        self._default_world_id = default_world_id

    def create_session(self, world_id: str | None = None) -> tuple[str, GameLoop]:
        session_id = str(uuid4())
        game_loop = self._build_game_loop(
            state=create_initial_state(self._world_loader, world_id or self._default_world_id),
            event_log=EventLog(),
        )
        self._sessions[session_id] = game_loop
        return session_id, game_loop

    def restore_session(self, state: GameState, events: list[Event] | None = None) -> tuple[str, GameLoop]:
        session_id = str(uuid4())
        game_loop = self._build_game_loop(
            state=state,
            event_log=EventLog(events or []),
        )
        self._sessions[session_id] = game_loop
        return session_id, game_loop

    def _build_game_loop(self, state: GameState, event_log: EventLog) -> GameLoop:
        provider = self._provider_factory()
        prompt_profile = get_default_prompt_profile_store().get_selected_profile()
        return GameLoop(
            state=state,
            event_log=event_log,
            intent_parser=IntentParser(provider, prompt_profile=prompt_profile),
            action_dispatcher=ActionDispatcher(),
            narrator=Narrator(provider, prompt_profile=prompt_profile),
            rng=Random(),
        )

    def get_session(self, session_id: str) -> GameLoop | None:
        return self._sessions.get(session_id)


def create_initial_state(world_loader: WorldLoader | None = None, world_id: str = "mist_valley") -> GameState:
    loader = world_loader or WorldLoader("worlds")
    return loader.load(world_id).to_game_state()


def build_visible_state(state: GameState) -> VisibleStateResponse:
    location = state.locations.get(state.player.location_id)
    location_id = state.player.location_id
    visible_objects = [
        VisibleObjectResponse(id=world_object.id)
        for world_object in state.objects.values()
        if _object_visible_to_player(state, world_object.id, location_id)
    ]
    inventory = [
        VisibleObjectResponse(id=item.id)
        for item in get_inventory(state, state.player.id)
    ]
    visible_npcs = [
        VisibleNPCResponse(
            id=npc.id,
            mood=npc.mood,
            relationship_to_player=npc.relationship_to_player,
            condition=npc.condition.value,
        )
        for npc in state.npcs.values()
        if npc.location_id == location_id and _npc_visible_to_player(state, npc.id)
    ]
    known_facts = [
        KnownFactResponse(id=fact_id, text=state.facts.get(fact_id).text, tags=state.facts.get(fact_id).tags)
        for fact_id in sorted(state.player_visible_facts)
        if fact_id in state.facts
    ]
    quests = []
    for quest in get_visible_quests(state):
        stage = quest.stages.get(quest.current_stage)
        stage_objectives = stage.objectives if stage else []
        quests.append(
            VisibleQuestResponse(
                id=quest.id,
                title=quest.title,
                name=quest.title,
                description=quest.description,
                status=quest.status.value,
                current_stage=quest.current_stage,
                stage_title=stage.title if stage else quest.current_stage,
                stage_description=stage.description if stage else "",
                objectives=[
                    VisibleQuestObjectiveResponse(
                        id=objective_id,
                        completed=objective_id in quest.completed_objectives,
                    )
                    for objective_id in stage_objectives
                ],
            )
        )
    return VisibleStateResponse(
        world_id=state.world_id,
        turn=state.turn,
        time=VisibleTimeResponse(
            day=state.current_time.day,
            minutes_of_day=state.current_time.minutes_of_day,
            time_of_day=get_time_of_day(state),
            formatted=format_game_time(state),
        ),
        location=VisibleLocationResponse(
            id=location_id,
            name=location.name if location else location_id,
            exits=location.exits if location else {},
        ),
        inventory=inventory,
        visible_objects=visible_objects,
        visible_npcs=visible_npcs,
        known_facts=known_facts,
        quests=quests,
        factions=[
            VisibleFactionResponse(
                id=faction.id,
                name=faction.name,
                description=faction.description,
                reputation=faction.reputation,
                band=faction.band.value,
                tags=faction.tags,
            )
            for faction in get_visible_factions(state)
        ],
        known_rumors=[
            VisibleRumorResponse(
                id=rumor.id,
                text_for_player=rumor.text_for_player,
                truth_status=rumor.truth_status.value,
                spread_level=rumor.spread_level,
                tags=rumor.tags,
            )
            for rumor in get_visible_rumors(state)
        ],
        known_crimes=[
            VisibleCrimeResponse(
                id=crime.id,
                crime_type=crime.crime_type,
                location_id=crime.location_id,
                severity=crime.severity,
                status=crime.status.value,
                created_turn=crime.created_turn,
            )
            for crime in get_player_known_crimes(state)
        ],
        relationships=[
            VisibleRelationshipResponse(
                id=relationship.id,
                source_id=relationship.source_id,
                target_id=relationship.target_id,
                relation_type=relationship.relation_type,
                trust=relationship.trust,
                fear=relationship.fear,
                affinity=relationship.affinity,
                obligation=relationship.obligation,
                tags=relationship.tags,
            )
            for relationship in get_visible_relationships(state)
        ],
        faction_conflicts=[
            VisibleFactionConflictResponse(
                faction_id=conflict.faction_id,
                alert_level=conflict.alert_level,
                conflict_level=conflict.conflict_level,
                relationships_to_other_factions=conflict.relationships_to_other_factions,
                conflict_tags=conflict.conflict_tags,
            )
            for conflict in get_visible_faction_conflicts(state)
        ],
        active_combat=_visible_combat_summary(state),
    )


def _object_visible_to_player(state: GameState, object_id: str, location_id: str) -> bool:
    world_object = state.objects.get(object_id)
    if world_object is None:
        return False
    if world_object.location_id != location_id or not world_object.visible:
        return False
    return not world_object.hidden or state.player.id in world_object.discovered_by


def _npc_visible_to_player(state: GameState, npc_id: str) -> bool:
    npc = state.npcs.get(npc_id)
    if npc is None or not npc.visible:
        return False
    return not npc.hidden or state.player.id in npc.discovered_by


def _visible_combat_summary(state: GameState) -> VisibleCombatSummaryResponse | None:
    for raw_combat in state.combats.values():
        combat = raw_combat if isinstance(raw_combat, CombatState) else CombatState.model_validate(raw_combat)
        if combat.status != "active" or combat.location_id != state.player.location_id:
            continue
        visible_combatants = [
            actor_id
            for actor_id in combat.combatant_ids
            if actor_id == state.player.id or _npc_visible_to_player(state, actor_id)
        ]
        return VisibleCombatSummaryResponse(
            combat_id=combat.id,
            location_id=combat.location_id,
            status=combat.status.value,
            player_stance=state.player.combat_stance,
            player_condition=state.player.condition.value,
            player_status_effects=list(state.player.status_effects),
            visible_combatants=visible_combatants,
        )
    return None
