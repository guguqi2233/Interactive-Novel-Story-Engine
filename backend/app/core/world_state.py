from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator

from app.compatibility.contracts import GAMESTATE_CONTRACT_VERSION

CURRENT_GAME_STATE_SCHEMA_VERSION = "0.6"


def _sorted_strings(values: set[str]) -> list[str]:
    return sorted(values)


def _sorted_string_sets(values: dict[str, set[str]]) -> dict[str, list[str]]:
    return {
        key: sorted(item_values)
        for key, item_values in sorted(values.items())
    }


class ActorCondition(StrEnum):
    HEALTHY = "healthy"
    WOUNDED = "wounded"
    CRITICAL = "critical"
    INCAPACITATED = "incapacitated"
    DEAD = "dead"


class PrimaryEmotion(StrEnum):
    CALM = "calm"
    ANGRY = "angry"
    AFRAID = "afraid"
    SAD = "sad"
    JOYFUL = "joyful"
    SUSPICIOUS = "suspicious"
    DEFENSIVE = "defensive"
    AFFECTIONATE = "affectionate"
    ASHAMED = "ashamed"
    EXCITED = "excited"


class EmotionalState(BaseModel):
    primary_emotion: PrimaryEmotion = PrimaryEmotion.CALM
    intensity: int = Field(default=0, ge=0, le=100)
    stability: int = Field(default=70, ge=0, le=100)
    stress: int = Field(default=0, ge=0, le=100)
    trust_tone: str = "neutral"
    fear_tone: str = "steady"
    affection_tone: str = "reserved"
    last_emotional_event_id: str | None = None
    expires_turn: int | None = Field(default=None, ge=0)


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


class MagicResourceState(BaseModel):
    mana: int = Field(default=0, ge=0)
    max_mana: int = Field(default=0, ge=0)
    focus: int = Field(default=0, ge=0)
    max_focus: int = Field(default=0, ge=0)
    cooldowns: dict[str, int] = Field(default_factory=dict)
    active_effects: list[str] = Field(default_factory=list)


class HackableState(BaseModel):
    id: str
    target_type: str = "terminal"
    location_id: str | None = None
    security_state: str = "locked"
    access_level: int = Field(default=0, ge=0)
    difficulty: int = Field(default=10, ge=0)
    monitored: bool = False
    hidden: bool = False
    discovered_by: list[str] = Field(default_factory=list)
    linked_fact_ids: list[str] = Field(default_factory=list)
    alarm_level: int = Field(default=0, ge=0)
    intrusion_trace: int = Field(default=0, ge=0)
    disabled: bool = False
    tags: list[str] = Field(default_factory=list)


class HackingToolState(BaseModel):
    id: str
    owner_id: str = "player"
    power: int = Field(default=0, ge=0)
    uses_remaining: int | None = Field(default=None, ge=0)
    tags: list[str] = Field(default_factory=list)


class NetworkNodeState(BaseModel):
    id: str
    connected_target_ids: list[str] = Field(default_factory=list)
    alert_level: int = Field(default=0, ge=0)
    compromised: bool = False
    hidden: bool = False
    discovered_by: list[str] = Field(default_factory=list)


class CraftingStationState(BaseModel):
    id: str
    location_id: str
    tags: list[str] = Field(default_factory=list)
    visible: bool = True
    hidden: bool = False
    discovered_by: list[str] = Field(default_factory=list)


class EvidenceState(BaseModel):
    id: str
    fact_id: str | None = None
    location_id: str | None = None
    discovered: bool = False
    visible: bool = True
    hidden: bool = False
    discovered_by: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class TestimonyState(BaseModel):
    id: str
    npc_id: str
    fact_ids: list[str] = Field(default_factory=list)
    contradiction_ids: list[str] = Field(default_factory=list)
    known_to_player: bool = False
    hidden: bool = False
    tags: list[str] = Field(default_factory=list)


class HypothesisStatus(StrEnum):
    DRAFT = "draft"
    WEAK = "weak"
    VALID = "valid"
    ACCUSED = "accused"
    CORRECT = "correct"
    WRONG = "wrong"


class HypothesisState(BaseModel):
    id: str
    suspect_id: str | None = None
    required_evidence_ids: list[str] = Field(default_factory=list)
    supporting_fact_ids: list[str] = Field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.DRAFT
    correct_suspect_id: str | None = None
    quest_id: str | None = None
    quest_objective_id: str | None = None
    hidden_truth_fact_id: str | None = None
    known_to_player: bool = False


class SurvivalState(BaseModel):
    actor_id: str = "player"
    fatigue: int = Field(default=0, ge=0, le=100)
    hunger: int = Field(default=0, ge=0, le=100)
    thirst: int = Field(default=0, ge=0, le=100)
    exposure: int = Field(default=0, ge=0, le=100)
    last_rest_turn: int | None = Field(default=None, ge=0)


class TravelRouteState(BaseModel):
    id: str
    from_location_id: str
    to_location_id: str
    time_cost: int = Field(default=0, ge=0)
    fatigue_cost: int = Field(default=0, ge=0)
    hunger_cost: int = Field(default=0, ge=0)
    thirst_cost: int = Field(default=0, ge=0)
    risk_level: int = Field(default=0, ge=0)
    weather_tags: list[str] = Field(default_factory=list)
    hidden: bool = False
    discovered_by: list[str] = Field(default_factory=list)


class WeatherState(BaseModel):
    location_id: str
    condition: str = "clear"
    severity: int = Field(default=0, ge=0, le=100)
    tags: list[str] = Field(default_factory=list)


class CampState(BaseModel):
    id: str
    location_id: str
    established_by: str = "player"
    quality: int = Field(default=0, ge=0, le=100)
    active: bool = True


class FacilityState(BaseModel):
    id: str
    domain_id: str
    facility_type: str
    level: int = Field(default=1, ge=1)
    income: int = Field(default=0, ge=0)
    upkeep: int = Field(default=0, ge=0)
    staff_slots: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)


class BaseInventoryState(BaseModel):
    domain_id: str
    item_ids: list[str] = Field(default_factory=list)
    currency: int = Field(default=0, ge=0)


class StaffAssignmentState(BaseModel):
    id: str
    domain_id: str
    npc_id: str
    facility_id: str | None = None
    role: str = "worker"
    active: bool = True


class DomainUpgradeDefinition(BaseModel):
    id: str
    facility_type: str
    target_level: int = Field(default=2, ge=2)
    cost: int = Field(default=0, ge=0)
    income_delta: int = 0
    upkeep_delta: int = 0
    required_tags: list[str] = Field(default_factory=list)


class DomainState(BaseModel):
    id: str
    name: str = ""
    location_id: str
    owner_id: str = "player"
    claimed: bool = False
    treasury: int = Field(default=0, ge=0)
    risk_level: int = Field(default=0, ge=0, le=100)
    facility_ids: list[str] = Field(default_factory=list)
    staff_assignment_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class StealthState(BaseModel):
    actor_id: str = "player"
    hidden: bool = False
    stealth_score: int = Field(default=0, ge=0, le=100)
    shadowing_target_id: str | None = None
    distracted_npc_ids: list[str] = Field(default_factory=list)
    decoy_item_id: str | None = None
    last_noise_event_id: str | None = None
    last_detection_result: str | None = None


class NoiseEvent(BaseModel):
    id: str
    location_id: str
    source_actor_id: str = "player"
    volume: int = Field(default=0, ge=0, le=100)
    turn: int = Field(default=0, ge=0)
    attracts_npc_ids: list[str] = Field(default_factory=list)
    hidden_source: bool = False


class CoverState(BaseModel):
    id: str
    location_id: str
    cover_level: int = Field(default=0, ge=0, le=10)
    light_level: int = Field(default=5, ge=0, le=10)
    tags: list[str] = Field(default_factory=list)


class DetectionCheckResult(BaseModel):
    observer_id: str | None = None
    detected: bool = False
    score: int = Field(default=0, ge=0)
    difficulty: int = Field(default=0, ge=0)
    hidden_observer: bool = False
    safe_summary: str = ""


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


class NPCIntentStatus(StrEnum):
    QUEUED = "queued"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class NPCIntent(BaseModel):
    id: str
    npc_id: str
    intent_type: str
    priority: int = 0
    status: NPCIntentStatus = NPCIntentStatus.QUEUED
    source_event_id: str | None = None
    source_goal_id: str | None = None
    target_id: str | None = None
    target_type: str | None = None
    created_turn: int = Field(default=0, ge=0)
    expires_turn: int | None = Field(default=None, ge=0)
    preconditions: list[str] = Field(default_factory=list)
    debug_reason: str | None = None


class NPCPlanStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class NPCPlanStepType(StrEnum):
    MOVE = "move"
    TALK = "talk"
    REPORT = "report"
    SPREAD_RUMOR = "spread_rumor"
    REST = "rest"
    GUARD = "guard"
    AVOID = "avoid"
    SEEK_ITEM = "seek_item"


class NPCPlanStepStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class NPCPlanStep(BaseModel):
    step_type: NPCPlanStepType
    target_id: str | None = None
    preconditions: list[str] = Field(default_factory=list)
    expected_result: str = ""
    status: NPCPlanStepStatus = NPCPlanStepStatus.PLANNED


class NPCPlan(BaseModel):
    id: str
    npc_id: str
    source_intent_id: str
    goal_id: str | None = None
    status: NPCPlanStatus = NPCPlanStatus.PLANNED
    steps: list[NPCPlanStep] = Field(default_factory=list)
    current_step_index: int = Field(default=0, ge=0)
    created_turn: int = Field(default=0, ge=0)
    expires_turn: int | None = Field(default=None, ge=0)


class NPCFactionDutyStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class NPCFactionDutyType(StrEnum):
    GUARD_LOCATION = "guard_location"
    PATROL_ROUTE = "patrol_route"
    REPORT_CRIME_TO_FACTION = "report_crime_to_faction"
    PROTECT_FACTION_MEMBER = "protect_faction_member"
    REFUSE_HOSTILE_ACTOR = "refuse_hostile_actor"
    SPREAD_FACTION_RUMOR = "spread_faction_rumor"
    SEEK_INFORMATION = "seek_information"
    ENFORCE_CURFEW = "enforce_curfew"


class NPCFactionDuty(BaseModel):
    id: str
    duty_type: NPCFactionDutyType
    priority: int = 0
    status: NPCFactionDutyStatus = NPCFactionDutyStatus.ACTIVE
    faction_id: str | None = None
    target_id: str | None = None
    target_type: str | None = None
    route_location_ids: list[str] = Field(default_factory=list)
    required_fact_ids: list[str] = Field(default_factory=list)
    required_rumor_ids: list[str] = Field(default_factory=list)
    required_crime_ids: list[str] = Field(default_factory=list)
    created_turn: int = Field(default=0, ge=0)
    expires_turn: int | None = Field(default=None, ge=0)
    debug_reason: str | None = None


class NPCSocialDisposition(BaseModel):
    trust_player: int = Field(default=0, ge=-100, le=100)
    fear_player: int = Field(default=0, ge=0, le=100)
    loyalty_to_faction: int = Field(default=0, ge=0, le=100)
    loyalty_to_npcs: dict[str, int] = Field(default_factory=dict)
    moral_flexibility: int = Field(default=50, ge=0, le=100)
    risk_tolerance: int = Field(default=50, ge=0, le=100)
    conflict_tolerance: int = Field(default=50, ge=0, le=100)
    secrecy_preference: int = Field(default=50, ge=0, le=100)


class RPProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    public_persona: str = ""
    private_self_summary: str | None = None
    attachment_style: str = ""
    trust_expression_style: str = ""
    conflict_expression_style: str = ""
    intimacy_expression_style: str = ""
    deception_style: str = ""
    boundaries: list[str] = Field(default_factory=list)


class VoiceProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tone: str = ""
    sentence_length: str = "mixed"
    vocabulary_style: str = ""
    catchphrases: list[str] = Field(default_factory=list)
    speech_habits: list[str] = Field(default_factory=list)
    silence_style: str = ""
    emotional_tells: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_sentence_length(self) -> "VoiceProfile":
        allowed = {"short", "medium", "long", "mixed"}
        if self.sentence_length not in allowed:
            raise ValueError(f"sentence_length must be one of {sorted(allowed)}")
        return self


class SceneMoodPreset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    description: str = ""
    tone: str = "neutral"
    pacing: str = "steady"
    sensory_focus: list[str] = Field(default_factory=list)
    metaphor_style: str = ""
    dialogue_pressure: str = "medium"
    allowed_intensity_range: list[int] = Field(default_factory=lambda: [0, 100])
    forbidden_content_rules: list[str] = Field(default_factory=list)
    compatible_genres: list[str] = Field(default_factory=list)

    @field_validator("dialogue_pressure")
    @classmethod
    def validate_dialogue_pressure(cls, value: str) -> str:
        allowed = {"low", "medium", "high", "volatile"}
        if value not in allowed:
            raise ValueError(f"dialogue_pressure must be one of {sorted(allowed)}")
        return value

    @field_validator("allowed_intensity_range")
    @classmethod
    def validate_intensity_range(cls, value: list[int]) -> list[int]:
        if len(value) != 2:
            raise ValueError("allowed_intensity_range must contain [min, max]")
        minimum, maximum = value
        if minimum < 0 or maximum > 100 or minimum > maximum:
            raise ValueError("allowed_intensity_range must satisfy 0 <= min <= max <= 100")
        return value


class ExampleDialogueVisibility(StrEnum):
    PROMPT_SAFE = "prompt_safe"
    AUTHORING_ONLY = "authoring_only"
    DEBUG_ONLY = "debug_only"
    UNSAFE = "unsafe"


class ExampleDialogueFactPolicy(StrEnum):
    FLAVOR_ONLY = "flavor_only"
    MAY_REFERENCE_KNOWN_FACTS = "may_reference_known_facts"
    UNSAFE = "unsafe"


class ExampleDialogueMessage(BaseModel):
    speaker: str = ""
    text: str

    @model_validator(mode="before")
    @classmethod
    def accept_string_message(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"speaker": "", "text": data}
        return data


class ExampleDialogue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    character_id: str
    source: str = "authoring"
    messages: list[ExampleDialogueMessage] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    style_notes: list[str] = Field(default_factory=list)
    visibility: ExampleDialogueVisibility = ExampleDialogueVisibility.AUTHORING_ONLY
    fact_policy: ExampleDialogueFactPolicy = ExampleDialogueFactPolicy.FLAVOR_ONLY

    @field_validator("messages", mode="before")
    @classmethod
    def coerce_messages(cls, value: object) -> object:
        if value is None:
            return []
        if isinstance(value, str):
            return [{"speaker": "", "text": line.strip()} for line in value.splitlines() if line.strip()]
        return value

    @model_validator(mode="after")
    def validate_prompt_safe_policy(self) -> "ExampleDialogue":
        if self.visibility == ExampleDialogueVisibility.PROMPT_SAFE and self.fact_policy == ExampleDialogueFactPolicy.UNSAFE:
            raise ValueError("prompt_safe example dialogue cannot use unsafe fact_policy")
        return self


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
    intent_queue: list[NPCIntent] = Field(default_factory=list)
    plans: list[NPCPlan] = Field(default_factory=list)
    faction_duties: list[NPCFactionDuty] = Field(default_factory=list)
    social_disposition: NPCSocialDisposition = Field(default_factory=NPCSocialDisposition)
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
    rp_profile: RPProfile = Field(default_factory=RPProfile)
    voice_profile: VoiceProfile = Field(default_factory=VoiceProfile)
    dialogue_style: str = ""
    speech_habits: list[str] = Field(default_factory=list)
    taboo_topics: list[str] = Field(default_factory=list)
    emotional_mask: str = ""
    example_dialogue_refs: list[str] = Field(default_factory=list)
    emotional_state: EmotionalState = Field(default_factory=EmotionalState)


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

    @field_serializer("known_by", when_used="json")
    def serialize_known_by(self, known_by: set[str]) -> list[str]:
        return _sorted_strings(known_by)


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
    FACTION_REPUTATION = "faction_reputation"


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

    @field_serializer("completed_objectives", when_used="json")
    def serialize_completed_objectives(self, completed_objectives: set[str]) -> list[str]:
        return _sorted_strings(completed_objectives)


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


class FactionMissionReward(BaseModel):
    reputation_delta: int = 0
    currency: int = Field(default=0, ge=0)
    item_ids: list[str] = Field(default_factory=list)


class FactionMissionDefinition(BaseModel):
    id: str
    faction_id: str
    mission_type: str
    title: str
    description: str = ""
    min_reputation: int = 0
    max_reputation: int | None = None
    required_conflict_tags: list[str] = Field(default_factory=list)
    required_known_fact_ids: list[str] = Field(default_factory=list)
    prerequisite_mission_ids: list[str] = Field(default_factory=list)
    blocked_by_player_crime: bool = False
    hidden: bool = False
    quest_id: str | None = None
    reward: FactionMissionReward = Field(default_factory=FactionMissionReward)
    failure_reputation_delta: int = 0
    tags: list[str] = Field(default_factory=list)


class FactionMissionState(BaseModel):
    id: str
    definition_id: str
    faction_id: str
    status: str = "available"
    quest_id: str | None = None
    accepted_turn: int | None = Field(default=None, ge=0)
    completed_turn: int | None = Field(default=None, ge=0)
    failed_turn: int | None = Field(default=None, ge=0)
    hidden: bool = False
    known_to_player: bool = False


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

    @field_serializer("known_by_npcs", "known_by_factions", "known_by", when_used="json")
    def serialize_known_by_sets(self, values: set[str]) -> list[str]:
        return _sorted_strings(values)


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


class SocialMoveDefinition(BaseModel):
    id: str
    move_type: str
    label: str = ""
    required_fact_ids: list[str] = Field(default_factory=list)
    required_leverage_ids: list[str] = Field(default_factory=list)
    currency_cost: int = Field(default=0, ge=0)
    difficulty: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)


class SocialMoveResult(BaseModel):
    move_type: str
    target_id: str | None = None
    success: bool = False
    revealed_fact_ids: list[str] = Field(default_factory=list)
    relationship_delta: int = 0
    suspicion_delta: int = 0
    safe_summary: str = ""


class LeverageState(BaseModel):
    id: str
    target_npc_id: str
    fact_id: str
    known_by_player: bool = False
    strength: int = Field(default=0, ge=0, le=100)
    used: bool = False
    hidden: bool = False
    tags: list[str] = Field(default_factory=list)


class CombatStatus(StrEnum):
    ACTIVE = "active"
    ENDED = "ended"


class CombatantStance(StrEnum):
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    CAUTIOUS = "cautious"
    FLEEING = "fleeing"
    INCAPACITATED = "incapacitated"


class CombatStance(StrEnum):
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    CAUTIOUS = "cautious"
    FLEEING = "fleeing"
    INCAPACITATED = "incapacitated"


class WeaponProfile(BaseModel):
    id: str
    tags: list[str] = Field(default_factory=list)
    damage_bonus: int = 0
    attack_bonus: int = 0
    non_lethal: bool = False
    allowed_stances: list[CombatStance] = Field(default_factory=list)


class CombatStatusEffect(BaseModel):
    id: str
    label: str = ""
    blocks_action: bool = False
    defense_modifier: int = 0
    damage_modifier: int = 0
    duration_turns: int | None = Field(default=None, ge=0)
    tags: list[str] = Field(default_factory=list)


class CombatEncounterDefinition(BaseModel):
    id: str
    location_id: str | None = None
    combatant_ids: list[str] = Field(default_factory=list)
    difficulty_tags: list[str] = Field(default_factory=list)
    public_combat: bool = True
    hidden: bool = False
    tags: list[str] = Field(default_factory=list)


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
    schema_version: str = CURRENT_GAME_STATE_SCHEMA_VERSION
    engine_version: str = "0.6.0"
    contract_version: str = GAMESTATE_CONTRACT_VERSION
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
    faction_mission_definitions: dict[str, FactionMissionDefinition] = Field(default_factory=dict)
    faction_missions: dict[str, FactionMissionState] = Field(default_factory=dict)
    rumors: dict[str, RumorState] = Field(default_factory=dict)
    crimes: dict[str, CrimeState] = Field(default_factory=dict)
    witnesses: dict[str, WitnessRecord] = Field(default_factory=dict)
    social_consequences: dict[str, SocialConsequenceState] = Field(default_factory=dict)
    social_flags: dict[str, bool | int | float | str] = Field(default_factory=dict)
    relationships: dict[str, RelationshipState] = Field(default_factory=dict)
    social_moves: dict[str, SocialMoveDefinition] = Field(default_factory=dict)
    leverages: dict[str, LeverageState] = Field(default_factory=dict)
    combats: dict[str, CombatState] = Field(default_factory=dict)
    weapon_profiles: dict[str, WeaponProfile] = Field(default_factory=dict)
    combat_status_effects: dict[str, CombatStatusEffect] = Field(default_factory=dict)
    combat_encounters: dict[str, CombatEncounterDefinition] = Field(default_factory=dict)
    magic_resources: dict[str, MagicResourceState] = Field(default_factory=dict)
    hackables: dict[str, HackableState] = Field(default_factory=dict)
    hacking_tools: dict[str, HackingToolState] = Field(default_factory=dict)
    network_nodes: dict[str, NetworkNodeState] = Field(default_factory=dict)
    crafting_stations: dict[str, CraftingStationState] = Field(default_factory=dict)
    evidence: dict[str, EvidenceState] = Field(default_factory=dict)
    testimonies: dict[str, TestimonyState] = Field(default_factory=dict)
    hypotheses: dict[str, HypothesisState] = Field(default_factory=dict)
    survival: dict[str, SurvivalState] = Field(default_factory=dict)
    travel_routes: dict[str, TravelRouteState] = Field(default_factory=dict)
    weather: dict[str, WeatherState] = Field(default_factory=dict)
    camps: dict[str, CampState] = Field(default_factory=dict)
    domains: dict[str, DomainState] = Field(default_factory=dict)
    facilities: dict[str, FacilityState] = Field(default_factory=dict)
    base_inventories: dict[str, BaseInventoryState] = Field(default_factory=dict)
    staff_assignments: dict[str, StaffAssignmentState] = Field(default_factory=dict)
    domain_upgrades: dict[str, DomainUpgradeDefinition] = Field(default_factory=dict)
    stealth: dict[str, StealthState] = Field(default_factory=dict)
    noise_events: dict[str, NoiseEvent] = Field(default_factory=dict)
    cover_states: dict[str, CoverState] = Field(default_factory=dict)
    scene_mood_presets: dict[str, SceneMoodPreset] = Field(default_factory=dict)
    example_dialogues: dict[str, ExampleDialogue] = Field(default_factory=dict)

    @field_serializer("player_visible_facts", when_used="json")
    def serialize_player_visible_facts(self, player_visible_facts: set[str]) -> list[str]:
        return _sorted_strings(player_visible_facts)

    @field_serializer("npc_knowledge", when_used="json")
    def serialize_npc_knowledge(self, npc_knowledge: dict[str, set[str]]) -> dict[str, list[str]]:
        return _sorted_string_sets(npc_knowledge)


def migrate_game_state_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Fill fields added after v0.3 so older save JSON can be validated."""
    migrated = dict(payload)
    migrated.setdefault("schema_version", CURRENT_GAME_STATE_SCHEMA_VERSION)
    migrated.setdefault("engine_version", "0.6.0")
    migrated.setdefault("contract_version", GAMESTATE_CONTRACT_VERSION)
    migrated.setdefault("factions", {})
    migrated.setdefault("rumors", {})
    migrated.setdefault("crimes", {})
    migrated.setdefault("witnesses", {})
    migrated.setdefault("social_consequences", {})
    migrated.setdefault("social_flags", {})
    migrated.setdefault("relationships", {})
    migrated.setdefault("social_moves", {})
    migrated.setdefault("leverages", {})
    migrated.setdefault("combats", {})
    migrated.setdefault("faction_mission_definitions", {})
    migrated.setdefault("faction_missions", {})
    migrated.setdefault("weapon_profiles", {})
    migrated.setdefault("combat_status_effects", {})
    migrated.setdefault("combat_encounters", {})
    migrated.setdefault("magic_resources", {})
    migrated.setdefault("hackables", {})
    migrated.setdefault("hacking_tools", {})
    migrated.setdefault("network_nodes", {})
    migrated.setdefault("crafting_stations", {})
    migrated.setdefault("evidence", {})
    migrated.setdefault("testimonies", {})
    migrated.setdefault("hypotheses", {})
    migrated.setdefault("survival", {})
    migrated.setdefault("travel_routes", {})
    migrated.setdefault("weather", {})
    migrated.setdefault("camps", {})
    migrated.setdefault("domains", {})
    migrated.setdefault("facilities", {})
    migrated.setdefault("base_inventories", {})
    migrated.setdefault("staff_assignments", {})
    migrated.setdefault("domain_upgrades", {})
    migrated.setdefault("stealth", {})
    migrated.setdefault("noise_events", {})
    migrated.setdefault("cover_states", {})
    migrated.setdefault("scene_mood_presets", {})
    migrated.setdefault("example_dialogues", {})
    return migrated


def load_game_state_payload(payload: dict[str, Any]) -> GameState:
    return GameState.model_validate(migrate_game_state_payload(payload))
