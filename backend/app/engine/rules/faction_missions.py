from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    FactionMissionDefinition,
    FactionMissionReward,
    FactionMissionState,
    GameState,
    QuestStage,
    QuestState,
    QuestStatus,
    QuestVisibility,
    SocialConsequenceState,
)
from app.engine.rules.factions import ReputationBand, reputation_band


class FactionMissionRuleError(ValueError):
    """Raised when faction mission rules cannot resolve cleanly."""


class FactionMissionType(StrEnum):
    COURIER = "courier"
    SABOTAGE = "sabotage"
    INVESTIGATION = "investigation"
    PROTECTION = "protection"
    NEGOTIATION = "negotiation"
    BOUNTY = "bounty"
    INFILTRATION = "infiltration"


class FactionMissionAvailability(BaseModel):
    mission_id: str
    available: bool
    reason: str = ""


class FactionMissionOperationResult(BaseModel):
    mission_id: str
    state_deltas: list[StateDelta] = Field(default_factory=list)
    event: Event
    accepted: bool = False
    completed: bool = False
    failed: bool = False
    rejected_reason: str | None = None


def available_faction_missions(state: GameState, faction_id: str | None = None) -> list[FactionMissionDefinition]:
    return [
        mission
        for mission in sorted(state.faction_mission_definitions.values(), key=lambda item: item.id)
        if (faction_id is None or mission.faction_id == faction_id)
        and mission_available(state, mission.id).available
        and not mission.hidden
        and _faction_known_to_player(state, mission.faction_id)
    ]


def mission_available(state: GameState, mission_id: str) -> FactionMissionAvailability:
    mission = _mission_definition(state, mission_id)
    faction = state.factions.get(mission.faction_id)
    if faction is None:
        return FactionMissionAvailability(mission_id=mission_id, available=False, reason="missing_faction")
    if reputation_band(faction.reputation.value) == ReputationBand.HOSTILE:
        return FactionMissionAvailability(mission_id=mission_id, available=False, reason="hostile_faction")
    if faction.reputation.value < mission.min_reputation:
        return FactionMissionAvailability(mission_id=mission_id, available=False, reason="reputation_below_threshold")
    if mission.max_reputation is not None and faction.reputation.value > mission.max_reputation:
        return FactionMissionAvailability(mission_id=mission_id, available=False, reason="reputation_above_threshold")
    if not set(mission.required_conflict_tags).issubset(set(faction.conflict_tags)):
        return FactionMissionAvailability(mission_id=mission_id, available=False, reason="missing_conflict_tag")
    if not set(mission.required_known_fact_ids).issubset(state.player_visible_facts):
        return FactionMissionAvailability(mission_id=mission_id, available=False, reason="missing_known_fact")
    if any(state.faction_missions.get(prereq_id, FactionMissionState(id="", definition_id="", faction_id="")).status != "completed" for prereq_id in mission.prerequisite_mission_ids):
        return FactionMissionAvailability(mission_id=mission_id, available=False, reason="missing_prior_mission")
    if mission.blocked_by_player_crime and _player_has_open_crime(state, mission.faction_id):
        return FactionMissionAvailability(mission_id=mission_id, available=False, reason="player_crime_block")
    current = state.faction_missions.get(mission.id)
    if current is not None and current.status in {"accepted", "completed", "failed"}:
        return FactionMissionAvailability(mission_id=mission_id, available=False, reason=f"mission_{current.status}")
    return FactionMissionAvailability(mission_id=mission_id, available=True, reason="available")


def accept_faction_mission(state: GameState, mission_id: str) -> FactionMissionOperationResult:
    mission = _mission_definition(state, mission_id)
    availability = mission_available(state, mission_id)
    if not availability.available:
        return _operation_result(state, mission, [], result="rejected", accepted=False, rejected_reason=availability.reason)
    event_id = f"faction-mission-accept-{mission_id}-{state.turn}"
    mission_state = FactionMissionState(
        id=mission.id,
        definition_id=mission.id,
        faction_id=mission.faction_id,
        status="accepted",
        quest_id=_quest_id(mission),
        accepted_turn=state.turn,
        hidden=mission.hidden,
        known_to_player=not mission.hidden and _faction_known_to_player(state, mission.faction_id),
    )
    quest = _quest_for_mission(mission, mission_state.quest_id or _quest_id(mission))
    deltas = [
        StateDelta(operation=StateDeltaOperation.SET, path=f"faction_missions.{mission.id}", value=mission_state.model_dump(mode="json"), caused_by_event_id=event_id, reason="Faction mission accepted."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"quests.{quest.id}", value=quest.model_dump(mode="json"), caused_by_event_id=event_id, reason="Faction mission created quest state."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"quests.{quest.id}.status", value=QuestStatus.ACTIVE, caused_by_event_id=event_id, reason="Faction mission quest activated."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"quests.{quest.id}.known_to_player", value=not mission.hidden, caused_by_event_id=event_id, reason="Faction mission quest visibility set."),
    ]
    return _operation_result(state, mission, deltas, result="accepted", accepted=True, event_id=event_id)


def complete_faction_mission(state: GameState, mission_id: str) -> FactionMissionOperationResult:
    mission = _mission_definition(state, mission_id)
    current = state.faction_missions.get(mission_id)
    if current is None or current.status != "accepted":
        return _operation_result(state, mission, [], result="rejected", rejected_reason="mission_not_accepted")
    event_id = f"faction-mission-complete-{mission_id}-{state.turn}"
    quest_id = current.quest_id or _quest_id(mission)
    deltas = [
        StateDelta(operation=StateDeltaOperation.SET, path=f"faction_missions.{mission.id}.status", value="completed", caused_by_event_id=event_id, reason="Faction mission completed."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"faction_missions.{mission.id}.completed_turn", value=state.turn, caused_by_event_id=event_id, reason="Faction mission completion turn recorded."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"quests.{quest_id}.status", value=QuestStatus.COMPLETED, caused_by_event_id=event_id, reason="Faction mission quest completed."),
        *_reward_deltas(state, mission.faction_id, mission.reward, event_id),
    ]
    return _operation_result(state, mission, deltas, result="completed", completed=True, event_id=event_id)


def fail_faction_mission(state: GameState, mission_id: str, reason: str = "mission_failed") -> FactionMissionOperationResult:
    mission = _mission_definition(state, mission_id)
    current = state.faction_missions.get(mission_id)
    if current is None or current.status != "accepted":
        return _operation_result(state, mission, [], result="rejected", rejected_reason="mission_not_accepted")
    event_id = f"faction-mission-fail-{mission_id}-{state.turn}"
    quest_id = current.quest_id or _quest_id(mission)
    consequence = SocialConsequenceState(
        id=f"faction_mission_failure_{mission_id}",
        consequence_type="faction_mission_failure",
        source_event_id=event_id,
        tags=[mission.faction_id, reason],
        known_to_player=not mission.hidden,
    )
    deltas = [
        StateDelta(operation=StateDeltaOperation.SET, path=f"faction_missions.{mission.id}.status", value="failed", caused_by_event_id=event_id, reason="Faction mission failed."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"faction_missions.{mission.id}.failed_turn", value=state.turn, caused_by_event_id=event_id, reason="Faction mission failure turn recorded."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"quests.{quest_id}.status", value=QuestStatus.FAILED, caused_by_event_id=event_id, reason="Faction mission quest failed."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"social_consequences.{consequence.id}", value=consequence.model_dump(mode="json"), caused_by_event_id=event_id, reason="Faction mission failure consequence recorded."),
    ]
    if mission.failure_reputation_delta:
        deltas.append(StateDelta(operation=StateDeltaOperation.INC, path=f"factions.{mission.faction_id}.reputation.value", value=mission.failure_reputation_delta, caused_by_event_id=event_id, reason="Faction mission failure changed reputation.", metadata={"source": "faction_mission"}))
    return _operation_result(state, mission, deltas, result="failed", failed=True, event_id=event_id)


def _reward_deltas(state: GameState, faction_id: str, reward: FactionMissionReward, event_id: str) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    if reward.reputation_delta:
        deltas.append(StateDelta(operation=StateDeltaOperation.INC, path=f"factions.{faction_id}.reputation.value", value=reward.reputation_delta, caused_by_event_id=event_id, reason="Faction mission reward changed reputation.", metadata={"source": "faction_mission"}))
    if reward.currency:
        deltas.append(StateDelta(operation=StateDeltaOperation.INC, path="player.currency", value=reward.currency, caused_by_event_id=event_id, reason="Faction mission reward granted currency.", metadata={"source": "faction_mission"}))
    for item_id in reward.item_ids:
        if item_id in state.objects:
            deltas.append(StateDelta(operation=StateDeltaOperation.SET, path=f"objects.{item_id}.owner_id", value=state.player.id, caused_by_event_id=event_id, reason="Faction mission reward granted item.", metadata={"source": "faction_mission"}))
    return deltas


def _operation_result(
    state: GameState,
    mission: FactionMissionDefinition,
    deltas: list[StateDelta],
    *,
    result: str,
    accepted: bool = False,
    completed: bool = False,
    failed: bool = False,
    rejected_reason: str | None = None,
    event_id: str | None = None,
) -> FactionMissionOperationResult:
    event = Event(
        event_id=event_id or f"faction-mission-{result}-{mission.id}-{state.turn}",
        turn=state.turn,
        actor_id="system",
        action_type="faction_mission",
        result=result,
        target_id=mission.id,
        state_deltas=deltas,
        visible_to_player=not mission.hidden and _faction_known_to_player(state, mission.faction_id),
        allow_empty_delta=not deltas,
    )
    return FactionMissionOperationResult(mission_id=mission.id, state_deltas=deltas, event=event, accepted=accepted, completed=completed, failed=failed, rejected_reason=rejected_reason)


def _quest_for_mission(mission: FactionMissionDefinition, quest_id: str) -> QuestState:
    stage = QuestStage(id="start", title=mission.title, description=mission.description, objectives=[f"{mission.id}_objective"])
    return QuestState(
        id=quest_id,
        title=mission.title,
        description=mission.description,
        initial_stage="start",
        current_stage="start",
        stages={"start": stage},
        visibility=QuestVisibility.HIDDEN if mission.hidden else QuestVisibility.PUBLIC,
        status=QuestStatus.INACTIVE,
        known_to_player=False,
    )


def _quest_id(mission: FactionMissionDefinition) -> str:
    return mission.quest_id or f"faction_mission_{mission.id}"


def _mission_definition(state: GameState, mission_id: str) -> FactionMissionDefinition:
    mission = state.faction_mission_definitions.get(mission_id)
    if mission is None:
        raise FactionMissionRuleError(f"Unknown faction mission: {mission_id}")
    if mission.mission_type not in {item.value for item in FactionMissionType}:
        raise FactionMissionRuleError(f"Unsupported faction mission type: {mission.mission_type}")
    return mission


def _faction_known_to_player(state: GameState, faction_id: str) -> bool:
    faction = state.factions.get(faction_id)
    if faction is None:
        return False
    return faction.known_by_player or faction.reputation.known_to_player


def _player_has_open_crime(state: GameState, faction_id: str) -> bool:
    for crime in state.crimes.values():
        if crime.status in {"resolved", "reported"}:
            continue
        target_npc = state.npcs.get(crime.victim_id or crime.target_id or "")
        if target_npc is not None and target_npc.faction_id == faction_id:
            return True
    return False
