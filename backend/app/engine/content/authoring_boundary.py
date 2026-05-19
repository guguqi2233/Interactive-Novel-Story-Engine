from enum import StrEnum

from pydantic import BaseModel, Field

from app.engine.content.validator import ValidationReport


class AuthoringBoundaryConcept(StrEnum):
    AUTHORING_DRAFT = "authoring_draft"
    PREVIEW_RESULT = "preview_result"
    VALIDATION_REPORT = "validation_report"
    EXPLICIT_SAVE = "explicit_save"
    ACTIVE_WORLD_PACK = "active_world_pack"
    ACTIVE_GAME_STATE = "active_game_state"
    MIGRATION_IMPACT = "migration_impact"
    HIDDEN_AUTHORING_FIELD = "hidden_authoring_field"
    PLAYER_VISIBLE_CONTENT = "player_visible_content"


class AuthoringOperation(StrEnum):
    DRAFT = "draft"
    PREVIEW = "preview"
    VALIDATE = "validate"
    SAVE = "save"
    APPLY_TO_ACTIVE_SESSION = "apply_to_active_session"


class AuthoringSurfaceKind(StrEnum):
    RAW_YAML = "raw_yaml"
    VISUAL_EDITOR = "visual_editor"
    IMPORT_EXPORT = "import_export"
    TEMPLATE = "template"
    PACKAGE = "package"


class AuthoringSaveDecision(StrEnum):
    ALLOW = "allow"
    BLOCK_VALIDATION_ERRORS = "block_validation_errors"
    REQUIRE_WARNING_CONFIRMATION = "require_warning_confirmation"
    BLOCK_ACTIVE_GAME_STATE_APPLY = "block_active_game_state_apply"


class AuthoringBoundaryPolicy(BaseModel):
    local_only: bool = True
    draft_modifies_active_game_state: bool = False
    preview_writes_disk: bool = False
    validate_writes_disk: bool = False
    save_writes_content_pack_only: bool = True
    apply_to_active_session_allowed: bool = False
    validation_errors_block_save: bool = True
    warnings_require_confirmation: bool = True
    hidden_authoring_fields_player_visible: bool = False
    provider_factory_only: bool = True
    import_export_executes_code: bool = False
    concepts: list[AuthoringBoundaryConcept] = Field(
        default_factory=lambda: list(AuthoringBoundaryConcept)
    )

    def decide_save(
        self,
        validation_report: ValidationReport,
        *,
        confirm_warnings: bool = False,
        apply_to_active_session: bool = False,
    ) -> AuthoringSaveDecision:
        if apply_to_active_session and not self.apply_to_active_session_allowed:
            return AuthoringSaveDecision.BLOCK_ACTIVE_GAME_STATE_APPLY
        if self.validation_errors_block_save and not validation_report.ok:
            return AuthoringSaveDecision.BLOCK_VALIDATION_ERRORS
        if (
            self.warnings_require_confirmation
            and validation_report.warnings
            and not confirm_warnings
        ):
            return AuthoringSaveDecision.REQUIRE_WARNING_CONFIRMATION
        return AuthoringSaveDecision.ALLOW


class AuthoringBoundaryCheckRequest(BaseModel):
    operation: AuthoringOperation
    surface_kind: AuthoringSurfaceKind = AuthoringSurfaceKind.VISUAL_EDITOR
    confirm_warnings: bool = False
    attempts_active_game_state_apply: bool = False
    validation_error_count: int = 0
    validation_warning_count: int = 0


class AuthoringBoundaryCheckResponse(BaseModel):
    local_only: bool = True
    operation: AuthoringOperation
    surface_kind: AuthoringSurfaceKind
    writes_disk: bool
    modifies_active_game_state: bool
    requires_validation: bool
    requires_explicit_save: bool
    requires_warning_confirmation: bool
    decision: AuthoringSaveDecision
    notes: list[str] = Field(default_factory=list)


def default_authoring_boundary_policy() -> AuthoringBoundaryPolicy:
    return AuthoringBoundaryPolicy()


def check_authoring_boundary(
    request: AuthoringBoundaryCheckRequest,
    policy: AuthoringBoundaryPolicy | None = None,
) -> AuthoringBoundaryCheckResponse:
    active_policy = policy or default_authoring_boundary_policy()
    writes_disk = request.operation == AuthoringOperation.SAVE
    modifies_active_game_state = (
        request.operation == AuthoringOperation.APPLY_TO_ACTIVE_SESSION
        or request.attempts_active_game_state_apply
    )
    decision = AuthoringSaveDecision.ALLOW
    notes: list[str] = []

    if modifies_active_game_state and not active_policy.apply_to_active_session_allowed:
        decision = AuthoringSaveDecision.BLOCK_ACTIVE_GAME_STATE_APPLY
        notes.append("Authoring operations cannot apply directly to active GameState.")
    elif request.operation == AuthoringOperation.SAVE:
        if request.validation_error_count > 0:
            decision = AuthoringSaveDecision.BLOCK_VALIDATION_ERRORS
            notes.append("Validation errors block editor saves.")
        elif request.validation_warning_count > 0 and not request.confirm_warnings:
            decision = AuthoringSaveDecision.REQUIRE_WARNING_CONFIRMATION
            notes.append("Validation warnings require explicit confirmation.")

    if request.operation in {AuthoringOperation.PREVIEW, AuthoringOperation.VALIDATE}:
        notes.append("Preview and validate are read-only draft checks and do not write disk.")
    if request.operation == AuthoringOperation.DRAFT:
        notes.append("Authoring drafts are content candidates, not runtime state.")
    if request.operation == AuthoringOperation.SAVE:
        notes.append("Save writes validated content-pack files only.")

    return AuthoringBoundaryCheckResponse(
        operation=request.operation,
        surface_kind=request.surface_kind,
        writes_disk=writes_disk,
        modifies_active_game_state=modifies_active_game_state,
        requires_validation=request.operation == AuthoringOperation.SAVE,
        requires_explicit_save=request.operation in {
            AuthoringOperation.DRAFT,
            AuthoringOperation.PREVIEW,
            AuthoringOperation.VALIDATE,
        },
        requires_warning_confirmation=(
            request.operation == AuthoringOperation.SAVE
            and request.validation_warning_count > 0
            and not request.confirm_warnings
        ),
        decision=decision,
        notes=notes,
    )
