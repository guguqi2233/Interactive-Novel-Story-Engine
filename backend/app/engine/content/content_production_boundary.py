from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ContentProductionConcept(StrEnum):
    PRODUCTION_DRAFT = "production_draft"
    GENERATED_CONTENT_CANDIDATE = "generated_content_candidate"
    BATCH_IMPORT_CANDIDATE = "batch_import_candidate"
    PRODUCTION_PACKAGE = "production_package"
    PACKAGE_MANIFEST = "package_manifest"
    EXPLICIT_APPLY = "explicit_apply"
    VALIDATION_REQUIRED = "validation_required"
    QUALITY_REQUIRED = "quality_required"
    ACTIVE_WORLD_PACK = "active_world_pack"
    ACTIVE_GAME_STATE = "active_game_state"


class ContentProductionOperation(StrEnum):
    GENERATE = "generate"
    PREVIEW = "preview"
    VALIDATE = "validate"
    BATCH_IMPORT_DRY_RUN = "batch_import_dry_run"
    BUILD_PACKAGE = "build_package"
    SAVE = "save"
    APPLY = "apply"
    BATCH_APPLY = "batch_apply"


class ContentProductionDecision(StrEnum):
    ALLOW = "allow"
    BLOCK_ACTIVE_GAME_STATE = "block_active_game_state"
    BLOCK_MISSING_DRY_RUN = "block_missing_dry_run"
    BLOCK_MISSING_EXPLICIT_APPLY = "block_missing_explicit_apply"
    BLOCK_VALIDATION_GATE = "block_validation_gate"
    BLOCK_QUALITY_GATE = "block_quality_gate"
    BLOCK_SCRIPT_EXECUTION = "block_script_execution"


class ProductionReportVisibility(StrEnum):
    NORMAL = "normal"
    DEBUG = "debug"


class ProductionHiddenContentRef(BaseModel):
    id: str
    kind: str
    redacted: bool = True


class ProductionSafeSummary(BaseModel):
    title: str
    visible_item_count: int = 0
    hidden_item_count: int = 0
    hidden_refs: list[ProductionHiddenContentRef] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ContentProductionDraft(BaseModel):
    id: str
    draft_type: str
    content: dict[str, Any] = Field(default_factory=dict)
    hidden_content: dict[str, Any] = Field(default_factory=dict)
    source: str = "local"

    def normal_report(self) -> ProductionSafeSummary:
        return ProductionSafeSummary(
            title=self.id,
            visible_item_count=len(self.content),
            hidden_item_count=len(self.hidden_content),
            hidden_refs=[
                ProductionHiddenContentRef(id=key, kind="hidden_content")
                for key in sorted(self.hidden_content)
            ],
        )


class ContentProductionCheckRequest(BaseModel):
    operation: ContentProductionOperation
    explicit_apply: bool = False
    dry_run_completed: bool = False
    validation_gate_passed: bool = False
    quality_gate_passed: bool = False
    attempts_active_game_state_write: bool = False
    executes_script: bool = False
    report_visibility: ProductionReportVisibility = ProductionReportVisibility.NORMAL


class ContentProductionCheckResponse(BaseModel):
    operation: ContentProductionOperation
    decision: ContentProductionDecision
    writes_disk: bool
    modifies_active_game_state: bool
    requires_validation_gate: bool
    requires_quality_gate: bool
    requires_explicit_apply: bool
    requires_dry_run: bool
    script_execution_allowed: bool = False
    notes: list[str] = Field(default_factory=list)


class ContentProductionPolicy(BaseModel):
    local_only: bool = True
    generator_outputs_draft_only: bool = True
    preview_writes_disk: bool = False
    validate_writes_disk: bool = False
    batch_import_writes_active_world_by_default: bool = False
    apply_requires_explicit_confirmation: bool = True
    apply_requires_validation_gate: bool = True
    batch_apply_requires_dry_run: bool = True
    quality_gate_required_for_package: bool = True
    hidden_content_in_normal_report: bool = False
    package_executes_scripts: bool = False
    active_game_state_writes_allowed: bool = False
    provider_factory_only: bool = True
    concepts: list[ContentProductionConcept] = Field(
        default_factory=lambda: list(ContentProductionConcept)
    )

    def check(self, request: ContentProductionCheckRequest) -> ContentProductionCheckResponse:
        writes_disk = request.operation in {
            ContentProductionOperation.SAVE,
            ContentProductionOperation.APPLY,
            ContentProductionOperation.BATCH_APPLY,
            ContentProductionOperation.BUILD_PACKAGE,
        }
        modifies_active_game_state = request.attempts_active_game_state_write
        requires_validation = request.operation in {
            ContentProductionOperation.SAVE,
            ContentProductionOperation.APPLY,
            ContentProductionOperation.BATCH_APPLY,
            ContentProductionOperation.BUILD_PACKAGE,
        }
        requires_quality = request.operation == ContentProductionOperation.BUILD_PACKAGE
        requires_explicit_apply = request.operation in {
            ContentProductionOperation.APPLY,
            ContentProductionOperation.BATCH_APPLY,
        }
        requires_dry_run = request.operation == ContentProductionOperation.BATCH_APPLY
        notes: list[str] = []

        decision = ContentProductionDecision.ALLOW
        if request.executes_script or self.package_executes_scripts:
            decision = ContentProductionDecision.BLOCK_SCRIPT_EXECUTION
            notes.append("Production packages and imports must not execute scripts.")
        elif modifies_active_game_state and not self.active_game_state_writes_allowed:
            decision = ContentProductionDecision.BLOCK_ACTIVE_GAME_STATE
            notes.append("Content production cannot directly modify active GameState.")
        elif requires_dry_run and self.batch_apply_requires_dry_run and not request.dry_run_completed:
            decision = ContentProductionDecision.BLOCK_MISSING_DRY_RUN
            notes.append("Batch apply requires a completed dry-run.")
        elif requires_explicit_apply and self.apply_requires_explicit_confirmation and not request.explicit_apply:
            decision = ContentProductionDecision.BLOCK_MISSING_EXPLICIT_APPLY
            notes.append("Apply requires explicit confirmation.")
        elif requires_validation and self.apply_requires_validation_gate and not request.validation_gate_passed:
            decision = ContentProductionDecision.BLOCK_VALIDATION_GATE
            notes.append("Save/apply/import/export/build operations require AuthoringValidationGate.")
        elif requires_quality and self.quality_gate_required_for_package and not request.quality_gate_passed:
            decision = ContentProductionDecision.BLOCK_QUALITY_GATE
            notes.append("Package build requires Quality Gate approval.")

        if request.operation in {ContentProductionOperation.PREVIEW, ContentProductionOperation.VALIDATE}:
            notes.append("Preview and validate are read-only checks and do not write disk.")
        if request.operation == ContentProductionOperation.GENERATE:
            notes.append("Generators produce drafts/candidates/packages only.")
        if request.operation == ContentProductionOperation.BATCH_IMPORT_DRY_RUN:
            notes.append("Batch import dry-run does not write active world packs.")

        return ContentProductionCheckResponse(
            operation=request.operation,
            decision=decision,
            writes_disk=writes_disk,
            modifies_active_game_state=modifies_active_game_state,
            requires_validation_gate=requires_validation,
            requires_quality_gate=requires_quality,
            requires_explicit_apply=requires_explicit_apply,
            requires_dry_run=requires_dry_run,
            notes=notes,
        )


def default_content_production_policy() -> ContentProductionPolicy:
    return ContentProductionPolicy()


def check_content_production_boundary(
    request: ContentProductionCheckRequest,
    policy: ContentProductionPolicy | None = None,
) -> ContentProductionCheckResponse:
    return (policy or default_content_production_policy()).check(request)
