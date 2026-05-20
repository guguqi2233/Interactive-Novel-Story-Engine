from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta
from app.engine.actions.schemas import ActionResult


class GameplayModuleConcept(StrEnum):
    GAMEPLAY_MODULE = "gameplay_module"
    ACTION_MOD = "action_mod"
    DECLARATIVE_ACTION = "declarative_action"
    RULE_MODULE = "rule_module"
    MODULE_STATE_EXTENSION = "module_state_extension"
    MODULE_EVENT_TYPE = "module_event_type"
    MODULE_DEBUG_DATA = "module_debug_data"
    ACTION_AFFORDANCE = "action_affordance"
    MODULE_PERMISSION = "module_permission"


class ModulePermission(StrEnum):
    REGISTER_ACTION = "register_action"
    REGISTER_OBJECT_AFFORDANCE = "register_object_affordance"
    DECLARE_PRECONDITIONS = "declare_preconditions"
    DECLARE_CHECKS = "declare_checks"
    DECLARE_EFFECTS = "declare_effects"
    DECLARE_STATE_DELTA_TEMPLATE = "declare_state_delta_template"
    DECLARE_EVENT_TYPE = "declare_event_type"
    DECLARE_SAVE_MIGRATION_DEFAULTS = "declare_save_migration_defaults"
    DECLARE_QUALITY_TESTS = "declare_quality_tests"
    EXECUTE_ARBITRARY_CODE = "execute_arbitrary_code"
    DIRECT_GAME_STATE_WRITE = "direct_game_state_write"
    DIRECT_DATABASE_WRITE = "direct_database_write"
    READ_SECRETS = "read_secrets"
    NETWORK_ACCESS = "network_access"
    LLM_ADJUDICATION = "llm_adjudication"
    BYPASS_VISIBILITY = "bypass_visibility"
    SKIP_EVENT_LOG = "skip_event_log"


class GameplayModuleOperation(StrEnum):
    PREVIEW = "preview"
    VALIDATE = "validate"
    IMPORT = "import"
    ENABLE = "enable"
    REGISTER_ACTION = "register_action"
    EXECUTE_ACTION = "execute_action"
    DEBUG_TRACE = "debug_trace"


class GameplayModuleDecision(StrEnum):
    ALLOW = "allow"
    BLOCK_DIRECT_GAME_STATE_MUTATION = "block_direct_game_state_mutation"
    BLOCK_MISSING_STATE_DELTA = "block_missing_state_delta"
    BLOCK_MISSING_EVENT = "block_missing_event"
    BLOCK_FORBIDDEN_PERMISSION = "block_forbidden_permission"
    BLOCK_LLM_ADJUDICATION = "block_llm_adjudication"
    BLOCK_VISIBILITY_BYPASS = "block_visibility_bypass"
    BLOCK_SECRET_ACCESS = "block_secret_access"
    BLOCK_NETWORK_ACCESS = "block_network_access"


class ModuleReportVisibility(StrEnum):
    NORMAL = "normal"
    DEBUG = "debug"


class ModuleDebugData(BaseModel):
    module_id: str
    safe_summary: str
    hidden_output: dict[str, Any] = Field(default_factory=dict)
    debug_reasons: list[str] = Field(default_factory=list)

    def normal_report(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "safe_summary": self.safe_summary,
            "hidden_output_count": len(self.hidden_output),
            "hidden_output_refs": sorted(self.hidden_output),
            "debug_reason_count": len(self.debug_reasons),
        }


class ActionAffordance(BaseModel):
    id: str
    action_type: str
    target_kind: str
    visible_to_player: bool = True
    required_permissions: list[ModulePermission] = Field(
        default_factory=lambda: [ModulePermission.REGISTER_OBJECT_AFFORDANCE]
    )


class ModuleStateExtension(BaseModel):
    path_prefix: str
    default_value: Any
    migration_required: bool = True
    player_visible: bool = False


class ModuleEventType(BaseModel):
    id: str
    visible_to_player_by_default: bool = False
    debug_only: bool = False


class DeclarativeAction(BaseModel):
    id: str
    action_type: str
    preconditions: list[str] = Field(default_factory=list)
    checks: list[str] = Field(default_factory=list)
    effects: list[StateDelta] = Field(default_factory=list)
    event_type: str
    hidden_output_keys: list[str] = Field(default_factory=list)


class ActionMod(BaseModel):
    id: str
    module_id: str
    declarative_action: DeclarativeAction
    permissions: list[ModulePermission] = Field(
        default_factory=lambda: [
            ModulePermission.REGISTER_ACTION,
            ModulePermission.DECLARE_PRECONDITIONS,
            ModulePermission.DECLARE_CHECKS,
            ModulePermission.DECLARE_EFFECTS,
            ModulePermission.DECLARE_STATE_DELTA_TEMPLATE,
            ModulePermission.DECLARE_EVENT_TYPE,
        ]
    )


class GameplayModule(BaseModel):
    id: str
    name: str
    action_mods: list[ActionMod] = Field(default_factory=list)
    affordances: list[ActionAffordance] = Field(default_factory=list)
    state_extensions: list[ModuleStateExtension] = Field(default_factory=list)
    event_types: list[ModuleEventType] = Field(default_factory=list)
    permissions: list[ModulePermission] = Field(default_factory=list)
    quality_tests: list[str] = Field(default_factory=list)


class ModuleActionCandidate(BaseModel):
    module_id: str
    action_id: str
    action_result: ActionResult
    event: Event | None = None
    module_debug_data: ModuleDebugData | None = None
    attempts_direct_game_state_mutation: bool = False
    uses_llm_as_judge: bool = False
    bypasses_visibility: bool = False
    permissions_used: list[ModulePermission] = Field(default_factory=list)


class GameplayModuleBoundaryCheckRequest(BaseModel):
    operation: GameplayModuleOperation
    permissions_requested: list[ModulePermission] = Field(default_factory=list)
    action_candidate: ModuleActionCandidate | None = None
    attempts_direct_game_state_mutation: bool = False
    attempts_database_write: bool = False
    attempts_secret_read: bool = False
    attempts_network_access: bool = False
    uses_llm_as_judge: bool = False
    bypasses_visibility: bool = False
    skips_event_log: bool = False


class GameplayModuleBoundaryCheckResponse(BaseModel):
    operation: GameplayModuleOperation
    decision: GameplayModuleDecision
    allowed_permissions: list[ModulePermission]
    forbidden_permissions: list[ModulePermission]
    requires_state_delta: bool
    requires_event: bool
    modifies_active_game_state: bool
    notes: list[str] = Field(default_factory=list)


class GameplayModulePolicy(BaseModel):
    local_only: bool = True
    action_registry_required: bool = True
    state_delta_required: bool = True
    event_required: bool = True
    arbitrary_code_execution_allowed: bool = False
    direct_game_state_mutation_allowed: bool = False
    direct_database_write_allowed: bool = False
    secret_read_allowed: bool = False
    network_access_allowed: bool = False
    llm_adjudication_allowed: bool = False
    visibility_bypass_allowed: bool = False
    hidden_output_player_visible: bool = False
    concepts: list[GameplayModuleConcept] = Field(default_factory=lambda: list(GameplayModuleConcept))
    allowed_permissions: list[ModulePermission] = Field(
        default_factory=lambda: [
            ModulePermission.REGISTER_ACTION,
            ModulePermission.REGISTER_OBJECT_AFFORDANCE,
            ModulePermission.DECLARE_PRECONDITIONS,
            ModulePermission.DECLARE_CHECKS,
            ModulePermission.DECLARE_EFFECTS,
            ModulePermission.DECLARE_STATE_DELTA_TEMPLATE,
            ModulePermission.DECLARE_EVENT_TYPE,
            ModulePermission.DECLARE_SAVE_MIGRATION_DEFAULTS,
            ModulePermission.DECLARE_QUALITY_TESTS,
        ]
    )

    def check(self, request: GameplayModuleBoundaryCheckRequest) -> GameplayModuleBoundaryCheckResponse:
        notes: list[str] = []
        forbidden = [
            permission
            for permission in request.permissions_requested
            if permission not in self.allowed_permissions
        ]
        if request.action_candidate is not None:
            forbidden.extend(
                permission
                for permission in request.action_candidate.permissions_used
                if permission not in self.allowed_permissions
            )
        forbidden = sorted(set(forbidden), key=lambda item: item.value)

        modifies_active_game_state = request.attempts_direct_game_state_mutation or bool(
            request.action_candidate and request.action_candidate.attempts_direct_game_state_mutation
        )
        uses_llm_as_judge = request.uses_llm_as_judge or bool(
            request.action_candidate and request.action_candidate.uses_llm_as_judge
        )
        bypasses_visibility = request.bypasses_visibility or bool(
            request.action_candidate and request.action_candidate.bypasses_visibility
        )
        skips_event_log = request.skips_event_log

        decision = GameplayModuleDecision.ALLOW
        if forbidden:
            decision = GameplayModuleDecision.BLOCK_FORBIDDEN_PERMISSION
            notes.append("Gameplay modules are declarative and cannot request forbidden permissions.")
        elif modifies_active_game_state and not self.direct_game_state_mutation_allowed:
            decision = GameplayModuleDecision.BLOCK_DIRECT_GAME_STATE_MUTATION
            notes.append("Gameplay modules cannot directly modify active GameState.")
        elif request.attempts_database_write and not self.direct_database_write_allowed:
            decision = GameplayModuleDecision.BLOCK_FORBIDDEN_PERMISSION
            notes.append("Gameplay modules cannot write databases directly.")
        elif request.attempts_secret_read and not self.secret_read_allowed:
            decision = GameplayModuleDecision.BLOCK_SECRET_ACCESS
            notes.append("Gameplay modules cannot read .env, API keys, or local secrets.")
        elif request.attempts_network_access and not self.network_access_allowed:
            decision = GameplayModuleDecision.BLOCK_NETWORK_ACCESS
            notes.append("Gameplay modules cannot access the network.")
        elif uses_llm_as_judge and not self.llm_adjudication_allowed:
            decision = GameplayModuleDecision.BLOCK_LLM_ADJUDICATION
            notes.append("LLM output cannot decide gameplay results.")
        elif bypasses_visibility and not self.visibility_bypass_allowed:
            decision = GameplayModuleDecision.BLOCK_VISIBILITY_BYPASS
            notes.append("Gameplay modules cannot bypass Visibility or NPC Knowledge.")
        elif request.action_candidate is not None and self.state_delta_required and not request.action_candidate.action_result.state_deltas:
            decision = GameplayModuleDecision.BLOCK_MISSING_STATE_DELTA
            notes.append("Module action effects must return at least one StateDelta.")
        elif request.action_candidate is not None and self.event_required and request.action_candidate.event is None:
            decision = GameplayModuleDecision.BLOCK_MISSING_EVENT
            notes.append("Module actions must record an Event.")
        elif request.action_candidate is not None and self.event_required and not request.action_candidate.event.state_deltas:
            decision = GameplayModuleDecision.BLOCK_MISSING_EVENT
            notes.append("Module action Event must include StateDelta records.")
        elif skips_event_log and not request.action_candidate:
            decision = GameplayModuleDecision.BLOCK_MISSING_EVENT
            notes.append("Gameplay module operations cannot skip EventLog.")

        if request.operation in {GameplayModuleOperation.PREVIEW, GameplayModuleOperation.VALIDATE, GameplayModuleOperation.IMPORT}:
            notes.append("Preview, validate, and import are metadata/package checks and do not mutate active GameState.")
        if request.operation == GameplayModuleOperation.EXECUTE_ACTION:
            notes.append("Runtime module actions must resolve through ActionRegistry and produce structured ActionResult.")

        return GameplayModuleBoundaryCheckResponse(
            operation=request.operation,
            decision=decision,
            allowed_permissions=self.allowed_permissions,
            forbidden_permissions=forbidden,
            requires_state_delta=request.operation == GameplayModuleOperation.EXECUTE_ACTION,
            requires_event=request.operation == GameplayModuleOperation.EXECUTE_ACTION,
            modifies_active_game_state=modifies_active_game_state,
            notes=notes,
        )


def default_gameplay_module_policy() -> GameplayModulePolicy:
    return GameplayModulePolicy()


def check_gameplay_module_boundary(
    request: GameplayModuleBoundaryCheckRequest,
    policy: GameplayModulePolicy | None = None,
) -> GameplayModuleBoundaryCheckResponse:
    return (policy or default_gameplay_module_policy()).check(request)
