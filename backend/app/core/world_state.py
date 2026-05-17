from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ActorCondition(StrEnum):
    HEALTHY = "healthy"
    WOUNDED = "wounded"
    CRITICAL = "critical"
    INCAPACITATED = "incapacitated"
    DEAD = "dead"


class PlayerState(BaseModel):
    id: str = "player"
    location_id: str = "start"
    inventory: list[str] = Field(default_factory=list)
    currency: int = Field(default=20, ge=0)
    health: int = 100
    hp: int = 10
    max_hp: int = 10
    alive: bool = True
    condition: ActorCondition = ActorCondition.HEALTHY
    stamina: int = 10
    max_stamina: int = 10
    attack: int = 3
    defense: int = 1
    combat_stance: str = "neutral"
    status_effects: list[str] = Field(default_factory=list)
    stealth_modifier: int = 0


class NPCGoalStatus(StrEnum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class NPCGoalState(BaseModel):
    id: str
    description: str = ""
    priority: int = 0
    status: NPCGoalStatus = NPCGoalStatus.INACTIVE
    conditions: list[str] = Field(default_factory=list)
    desired_state: dict[str, Any] = Field(default_factory=dict)
    allowed_actions: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)


class NPCState(BaseModel):
    id: str
    location_id: str
    faction_id: str | None = None
    visible: bool = True
    hidden: bool = False
    discovered_by: list[str] = Field(default_factory=list)
    mood: str = "neutral"
    relationship_to_player: int = 0
    alertness: int = 0
    suspicion: int = 0
    hp: int = 10
    max_hp: int = 10
    alive: bool = True
    condition: ActorCondition = ActorCondition.HEALTHY
    stamina: int = 10
    max_stamina: int = 10
    attack: int = 2
    defense: int = 1
    combat_stance: str = "neutral"
    status_effects: list[str] = Field(default_factory=list)
    hostile_to: list[str] = Field(default_factory=list)
    knowledge: list[str] = Field(default_factory=list)
    goals: list[str | NPCGoalState] = Field(default_factory=list)
    priorities: dict[str, int] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    current_goal_id: str | None = None
    plan_state: dict[str, Any] = Field(default_factory=dict)
    secrets: list[str] = Field(default_factory=list)
    schedule: list["NPCScheduleEntry"] = Field(default_factory=list)
    current_activity: str | None = None
    merchant: bool = False
    shop_inventory: list[str] = Field(default_factory=list)
    buy_price_modifier: float = Field(default=1.0, ge=0.0)
    sell_price_modifier: float = Field(default=0.5, ge=0.0)


class NPCScheduleEntry(BaseModel):
    time_of_day: str
    location_id: str
    activity: str


class LockState(StrEnum):
    INTACT = "intact"
    SCRATCHED = "scratched"
    DAMAGED = "damaged"
    BROKEN = "broken"
    OPENED = "opened"


class WorldObjectState(BaseModel):
    id: str
    name: str | None = None
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
    lock_state: LockState = LockState.INTACT

    @model_validator(mode="after")
    def validate_single_placement(self) -> "WorldObjectState":
        placements = [
            self.location_id is not None,
            self.owner_id is not None,
            self.container_id is not None,
        ]
        if sum(placements) > 1:
            raise ValueError("WorldObjectState cannot have multiple placements")
        return self


class LocationState(BaseModel):
    id: str
    name: str
    exits: dict[str, str] = Field(default_factory=dict)
    visible_objects: list[str] = Field(default_factory=list)
    cover_level: int = Field(default=0, ge=0)
    light_level: int = Field(default=5, ge=0)


class GameTime(BaseModel):
    day: int = 1
    minutes_of_day: int = Field(default=8 * 60, ge=0, lt=24 * 60)


class FactVisibility(StrEnum):
    PUBLIC = "public"
    HIDDEN = "hidden"
    DISCOVERABLE = "discoverable"


class FactState(BaseModel):
    id: str
    text: str | None = None
    visibility: FactVisibility = FactVisibility.HIDDEN
    public: bool = False
    secret: bool = False
    known_by: set[str] = Field(default_factory=set)
    tags: list[str] = Field(default_factory=list)


class QuestVisibility(StrEnum):
    PUBLIC = "public"
    HIDDEN = "hidden"


class QuestStatus(StrEnum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestTriggerType(StrEnum):
    FACT_DISCOVERED = "fact_discovered"
    ITEM_ACQUIRED = "item_acquired"
    NPC_TALKED = "npc_talked"
    LOCATION_VISITED = "location_visited"


class QuestTriggerAction(StrEnum):
    ACTIVATE = "activate"
    ADVANCE = "advance"
    COMPLETE_OBJECTIVE = "complete_objective"


class QuestTrigger(BaseModel):
    type: QuestTriggerType
    id: str
    action: QuestTriggerAction = QuestTriggerAction.ACTIVATE
    objective_id: str | None = None
    next_stage: str | None = None


class QuestStage(BaseModel):
    id: str
    title: str
    description: str = ""
    objectives: list[str] = Field(default_factory=list)
    next_stages: list[str] = Field(default_factory=list)


class QuestState(BaseModel):
    id: str
    title: str
    description: str = ""
    initial_stage: str
    current_stage: str
    stages: dict[str, QuestStage] = Field(default_factory=dict)
    visibility: QuestVisibility = QuestVisibility.HIDDEN
    status: QuestStatus = QuestStatus.INACTIVE
    known_to_player: bool = False
    completed_objectives: set[str] = Field(default_factory=set)
    triggers: list[QuestTrigger] = Field(default_factory=list)


class ReputationState(BaseModel):
    value: int = 0
    known_to_player: bool = False
    recent_reasons: list[str] = Field(default_factory=list)


class FactionState(BaseModel):
    id: str
    name: str
    description: str = ""
    reputation: ReputationState = Field(default_factory=ReputationState)
    relationships_to_other_factions: dict[str, int] = Field(default_factory=dict)
    conflict_level: int = Field(default=0, ge=0)
    alert_level: int = Field(default=0, ge=0)
    resources: dict[str, int | float | str] = Field(default_factory=dict)
    known_by_player: bool = False
    conflict_tags: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class RumorStatus(StrEnum):
    ACTIVE = "active"
    STALE = "stale"
    DISPROVEN = "disproven"


class RumorTruthStatus(StrEnum):
    TRUE = "true"
    FALSE = "false"
    DISTORTED = "distorted"
    UNKNOWN = "unknown"


class RumorState(BaseModel):
    id: str
    source_event_id: str | None = None
    fact_id: str | None = None
    text_for_player: str | None = None
    truth_status: RumorTruthStatus = RumorTruthStatus.UNKNOWN
    known_by_npcs: set[str] = Field(default_factory=set)
    known_by_factions: set[str] = Field(default_factory=set)
    known_by_player: bool = False
    spread_level: int = Field(default=0, ge=0)
    created_turn: int = 0
    text: str | None = None
    known_by: set[str] = Field(default_factory=set)
    credibility: int = Field(default=0, ge=0)
    status: RumorStatus = RumorStatus.ACTIVE
    tags: list[str] = Field(default_factory=list)
    known_to_player: bool = False

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        migrated = dict(data)
        if migrated.get("text_for_player") is None and migrated.get("text") is not None:
            migrated["text_for_player"] = migrated["text"]
        if "known_by_player" not in migrated and "known_to_player" in migrated:
            migrated["known_by_player"] = migrated["known_to_player"]
        if "known_by_npcs" not in migrated and "known_by" in migrated:
            migrated["known_by_npcs"] = migrated["known_by"]
        if "spread_level" not in migrated and "credibility" in migrated:
            migrated["spread_level"] = migrated["credibility"]
        return migrated


class CrimeStatus(StrEnum):
    HIDDEN = "hidden"
    WITNESSED = "witnessed"
    REPORTED = "reported"
    RESOLVED = "resolved"


class WitnessReportIntent(StrEnum):
    NONE = "none"
    LATER = "later"
    IMMEDIATE = "immediate"


class CrimeState(BaseModel):
    id: str
    crime_type: str
    actor_id: str
    victim_id: str | None = None
    target_id: str | None = None
    location_id: str
    turn: int = 0
    created_turn: int = 0
    witness_ids: list[str] = Field(default_factory=list)
    witnessed_by: list[str] = Field(default_factory=list)
    reported_to_factions: list[str] = Field(default_factory=list)
    reported_to: list[str] = Field(default_factory=list)
    severity: int = Field(default=1, ge=0)
    known_to_player: bool = False
    status: CrimeStatus = CrimeStatus.HIDDEN
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        migrated = dict(data)
        if "created_turn" not in migrated and "turn" in migrated:
            migrated["created_turn"] = migrated["turn"]
        if "witnessed_by" not in migrated and "witness_ids" in migrated:
            migrated["witnessed_by"] = migrated["witness_ids"]
        if "reported_to" not in migrated and "reported_to_factions" in migrated:
            migrated["reported_to"] = migrated["reported_to_factions"]
        return migrated


class WitnessRecord(BaseModel):
    id: str = ""
    npc_id: str
    crime_id: str | None = None
    fact_id: str | None = None
    certainty: int = Field(default=0, ge=0)
    saw_actor: bool = True
    saw_target: bool = True
    report_intent: WitnessReportIntent = WitnessReportIntent.NONE
    confidence: int = Field(default=0, ge=0)
    reported: bool = False
    known_to_player: bool = False

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        migrated = dict(data)
        if "certainty" not in migrated and "confidence" in migrated:
            migrated["certainty"] = migrated["confidence"]
        if "confidence" not in migrated and "certainty" in migrated:
            migrated["confidence"] = migrated["certainty"]
        if not migrated.get("id") and migrated.get("npc_id") and migrated.get("crime_id"):
            migrated["id"] = f"{migrated['crime_id']}:{migrated['npc_id']}"
        return migrated


class SocialConsequenceState(BaseModel):
    id: str
    consequence_type: str
    source_event_id: str | None = None
    due_turn: int | None = None
    resolved: bool = False
    state_deltas: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    known_to_player: bool = False


class RelationshipState(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    trust: int = 0
    fear: int = 0
    affinity: int = 0
    obligation: int = 0
    tags: list[str] = Field(default_factory=list)
    known_by_player: bool = False


class CombatStatus(StrEnum):
    ACTIVE = "active"
    ENDED = "ended"


class CombatantStance(StrEnum):
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    FLEEING = "fleeing"
    INCAPACITATED = "incapacitated"


class CombatantState(BaseModel):
    actor_id: str
    hp: int = Field(default=10, ge=0)
    max_hp: int = Field(default=10, ge=1)
    stamina: int | None = Field(default=10, ge=0)
    status_effects: list[str] = Field(default_factory=list)
    stance: CombatantStance = CombatantStance.AGGRESSIVE


class CombatState(BaseModel):
    id: str
    location_id: str
    combatant_ids: list[str] = Field(default_factory=list)
    status: CombatStatus = CombatStatus.ACTIVE
    started_turn: int = 0
    ended_turn: int | None = None


class GameState(BaseModel):
    world_id: str
    turn: int = 0
    current_time: GameTime = Field(default_factory=GameTime)
    player: PlayerState = Field(default_factory=PlayerState)
    locations: dict[str, LocationState] = Field(default_factory=dict)
    objects: dict[str, WorldObjectState] = Field(default_factory=dict)
    npcs: dict[str, NPCState] = Field(default_factory=dict)
    flags: dict[str, bool | int | float | str] = Field(default_factory=dict)
    facts: dict[str, FactState] = Field(default_factory=dict)
    player_visible_facts: set[str] = Field(default_factory=set)
    npc_knowledge: dict[str, set[str]] = Field(default_factory=dict)
    quests: dict[str, QuestState] = Field(default_factory=dict)
    delayed_consequences: list[dict[str, Any]] = Field(default_factory=list)
    factions: dict[str, FactionState] = Field(default_factory=dict)
    rumors: dict[str, RumorState] = Field(default_factory=dict)
    crimes: dict[str, CrimeState] = Field(default_factory=dict)
    witnesses: dict[str, WitnessRecord] = Field(default_factory=dict)
    social_consequences: dict[str, SocialConsequenceState] = Field(default_factory=dict)
    social_flags: dict[str, bool | int | float | str] = Field(default_factory=dict)
    relationships: dict[str, RelationshipState] = Field(default_factory=dict)
    combats: dict[str, CombatState] = Field(default_factory=dict)


def migrate_game_state_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Fill fields added after v0.3 so older save JSON can be validated."""
    migrated = dict(payload)
    migrated.setdefault("factions", {})
    migrated.setdefault("rumors", {})
    migrated.setdefault("crimes", {})
    migrated.setdefault("witnesses", {})
    migrated.setdefault("social_consequences", {})
    migrated.setdefault("social_flags", {})
    migrated.setdefault("relationships", {})
    migrated.setdefault("combats", {})
    return migrated


def load_game_state_payload(payload: dict[str, Any]) -> GameState:
    return GameState.model_validate(migrate_game_state_payload(payload))
