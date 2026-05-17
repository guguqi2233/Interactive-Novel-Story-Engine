from pydantic import BaseModel, Field

from app.core.state_delta import StateDelta


class VisibleTimeResponse(BaseModel):
    day: int
    minutes_of_day: int
    time_of_day: str
    formatted: str


class VisibleLocationResponse(BaseModel):
    id: str
    name: str
    exits: dict[str, str] = Field(default_factory=dict)


class VisibleObjectResponse(BaseModel):
    id: str


class VisibleNPCResponse(BaseModel):
    id: str
    mood: str
    relationship_to_player: int
    condition: str = "healthy"


class KnownFactResponse(BaseModel):
    id: str
    text: str | None = None
    tags: list[str] = Field(default_factory=list)


class VisibleQuestObjectiveResponse(BaseModel):
    id: str
    completed: bool = False


class VisibleQuestResponse(BaseModel):
    id: str
    title: str
    name: str
    description: str = ""
    status: str
    current_stage: str
    stage_title: str
    stage_description: str = ""
    objectives: list[VisibleQuestObjectiveResponse] = Field(default_factory=list)


class VisibleFactionResponse(BaseModel):
    id: str
    name: str
    description: str = ""
    reputation: int
    band: str
    tags: list[str] = Field(default_factory=list)


class VisibleRumorResponse(BaseModel):
    id: str
    text_for_player: str
    truth_status: str
    spread_level: int
    tags: list[str] = Field(default_factory=list)


class VisibleCrimeResponse(BaseModel):
    id: str
    crime_type: str
    location_id: str
    severity: int
    status: str
    created_turn: int


class VisibleRelationshipResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    trust: int
    fear: int
    affinity: int
    obligation: int
    tags: list[str] = Field(default_factory=list)


class VisibleFactionConflictResponse(BaseModel):
    faction_id: str
    alert_level: int
    conflict_level: int
    relationships_to_other_factions: dict[str, int] = Field(default_factory=dict)
    conflict_tags: list[str] = Field(default_factory=list)


class VisibleStateResponse(BaseModel):
    world_id: str
    turn: int
    time: VisibleTimeResponse
    location: VisibleLocationResponse
    inventory: list[VisibleObjectResponse] = Field(default_factory=list)
    visible_objects: list[VisibleObjectResponse] = Field(default_factory=list)
    visible_npcs: list[VisibleNPCResponse] = Field(default_factory=list)
    known_facts: list[KnownFactResponse] = Field(default_factory=list)
    quests: list[VisibleQuestResponse] = Field(default_factory=list)
    factions: list[VisibleFactionResponse] = Field(default_factory=list)
    known_rumors: list[VisibleRumorResponse] = Field(default_factory=list)
    known_crimes: list[VisibleCrimeResponse] = Field(default_factory=list)
    relationships: list[VisibleRelationshipResponse] = Field(default_factory=list)
    faction_conflicts: list[VisibleFactionConflictResponse] = Field(default_factory=list)


class StartGameRequest(BaseModel):
    world_id: str | None = None


class StartGameResponse(BaseModel):
    session_id: str
    world_id: str
    visible_state: VisibleStateResponse
    turn: int


class GameInputRequest(BaseModel):
    session_id: str
    player_input: str = Field(min_length=1)


class GameInputResponse(BaseModel):
    narrative_text: str
    suggested_actions: list[str]
    visible_state: VisibleStateResponse
    turn: int


class GameStateResponse(BaseModel):
    session_id: str
    visible_state: VisibleStateResponse
    turn: int


class SaveSummaryResponse(BaseModel):
    save_id: str
    world_id: str
    world_name: str
    turn: int
    current_location_name: str
    formatted_time: str
    created_at: str
    updated_at: str
    player_summary: str | None = None


class SaveListResponse(BaseModel):
    saves: list[SaveSummaryResponse] = Field(default_factory=list)


class SaveGameResponse(BaseModel):
    save_id: str
    session_id: str
    world_id: str
    turn: int


class DeleteSaveResponse(BaseModel):
    save_id: str
    deleted: bool = True


class LoadGameResponse(BaseModel):
    save_id: str
    session_id: str
    visible_state: VisibleStateResponse
    turn: int


class DebugEventResponse(BaseModel):
    turn: int
    event_id: str
    actor_id: str
    action_type: str
    result: str
    state_deltas: list[StateDelta] = Field(default_factory=list)
    visible_to_player: bool
    created_at: str


class DebugEventListResponse(BaseModel):
    local_only: bool = True
    events: list[DebugEventResponse] = Field(default_factory=list)


class AuthoringValidationIssueResponse(BaseModel):
    severity: str
    file: str
    path: str
    code: str
    message: str
    ref_id: str | None = None
    suggestion: str | None = None


class AuthoringValidationResponse(BaseModel):
    world_id: str
    ok: bool
    errors: list[AuthoringValidationIssueResponse] = Field(default_factory=list)
    warnings: list[AuthoringValidationIssueResponse] = Field(default_factory=list)
    suggestions: list[AuthoringValidationIssueResponse] = Field(default_factory=list)


class AuthoringWorldSummaryResponse(BaseModel):
    world_id: str
    name: str | None = None
    description: str = ""
    version: str | None = None
    file_count: int = 0


class AuthoringWorldListResponse(BaseModel):
    local_only: bool = True
    worlds: list[AuthoringWorldSummaryResponse] = Field(default_factory=list)


class AuthoringWorldDetailResponse(BaseModel):
    local_only: bool = True
    world: AuthoringWorldSummaryResponse
    files: list[str] = Field(default_factory=list)
    validation: AuthoringValidationResponse


class AuthoringFileListResponse(BaseModel):
    local_only: bool = True
    world_id: str
    files: list[str] = Field(default_factory=list)


class AuthoringFileResponse(BaseModel):
    local_only: bool = True
    world_id: str
    file_name: str
    content: str


class AuthoringFileWriteRequest(BaseModel):
    content: str


class AuthoringFileWriteResponse(BaseModel):
    local_only: bool = True
    world_id: str
    file_name: str
    validation: AuthoringValidationResponse


class AuthoringCreateWorldRequest(BaseModel):
    world_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    description: str = ""
    start_location_id: str = Field(default="start", pattern=r"^[A-Za-z0-9_-]+$")


class AuthoringCreateWorldResponse(BaseModel):
    local_only: bool = True
    world: AuthoringWorldSummaryResponse
    validation: AuthoringValidationResponse


class AuthoringModSummaryResponse(BaseModel):
    id: str
    name: str
    version: str
    engine_version_min: str
    engine_version_max: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    entry_worlds: list[str] = Field(default_factory=list)
    content_paths: list[str] = Field(default_factory=list)
    author: str | None = None
    description: str = ""


class AuthoringModListResponse(BaseModel):
    local_only: bool = True
    mods: list[AuthoringModSummaryResponse] = Field(default_factory=list)


class AuthoringModValidationResponse(BaseModel):
    local_only: bool = True
    mod_id: str
    ok: bool
    errors: list[AuthoringValidationIssueResponse] = Field(default_factory=list)
    warnings: list[AuthoringValidationIssueResponse] = Field(default_factory=list)
    suggestions: list[AuthoringValidationIssueResponse] = Field(default_factory=list)
    world_report_ids: list[str] = Field(default_factory=list)
