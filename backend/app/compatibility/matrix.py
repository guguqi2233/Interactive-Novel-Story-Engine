from __future__ import annotations

from pydantic import BaseModel, Field

from app.compatibility.contracts import (
    ACTION_MOD_CONTRACT_VERSION,
    CONTENT_PACK_SCHEMA_CONTRACT_VERSION,
    DEBUG_API_CONTRACT_VERSION,
    EVENTLOG_CONTRACT_VERSION,
    GAMESTATE_CONTRACT_VERSION,
    MODULE_CONTRACT_VERSION,
    PACKAGE_CONTRACT_VERSION,
    PROMPT_PROFILE_CONTRACT_VERSION,
    PROVIDER_CONTRACT_VERSION,
    QUALITY_GATE_CONTRACT_VERSION,
    SAVE_MIGRATION_CONTRACT_VERSION,
    STATEDELTA_CONTRACT_VERSION,
    CompatibilityStatus,
)
from app.core.world_state import CURRENT_GAME_STATE_SCHEMA_VERSION
from app.db.migrations import CURRENT_ENGINE_VERSION, CURRENT_SAVE_SCHEMA_VERSION


class CompatibilityMatrixEntry(BaseModel):
    contract: str
    current_version: str
    status: CompatibilityStatus = CompatibilityStatus.COMPATIBLE
    notes: str = ""


class CompatibilityMatrix(BaseModel):
    engine_version: str = CURRENT_ENGINE_VERSION
    game_state_schema_version: str = CURRENT_GAME_STATE_SCHEMA_VERSION
    save_version: str = CURRENT_SAVE_SCHEMA_VERSION
    entries: list[CompatibilityMatrixEntry] = Field(default_factory=list)


class CompatibilityCheckRequest(BaseModel):
    contract: str
    version: str


class CompatibilityCheckResponse(BaseModel):
    contract: str
    version: str
    status: CompatibilityStatus
    reason: str


def build_compatibility_matrix() -> CompatibilityMatrix:
    return CompatibilityMatrix(
        entries=[
            CompatibilityMatrixEntry(contract="GameState", current_version=GAMESTATE_CONTRACT_VERSION),
            CompatibilityMatrixEntry(contract="StateDelta", current_version=STATEDELTA_CONTRACT_VERSION),
            CompatibilityMatrixEntry(contract="EventLog", current_version=EVENTLOG_CONTRACT_VERSION),
            CompatibilityMatrixEntry(contract="ContentPack", current_version=CONTENT_PACK_SCHEMA_CONTRACT_VERSION),
            CompatibilityMatrixEntry(contract="SaveMigration", current_version=SAVE_MIGRATION_CONTRACT_VERSION),
            CompatibilityMatrixEntry(contract="ModuleManifest", current_version=MODULE_CONTRACT_VERSION),
            CompatibilityMatrixEntry(contract="ActionMod", current_version=ACTION_MOD_CONTRACT_VERSION),
            CompatibilityMatrixEntry(contract="PromptProfile", current_version=PROMPT_PROFILE_CONTRACT_VERSION),
            CompatibilityMatrixEntry(contract="ProviderGateway", current_version=PROVIDER_CONTRACT_VERSION),
            CompatibilityMatrixEntry(contract="Package", current_version=PACKAGE_CONTRACT_VERSION),
            CompatibilityMatrixEntry(contract="DebugAPI", current_version=DEBUG_API_CONTRACT_VERSION),
            CompatibilityMatrixEntry(contract="QualityGate", current_version=QUALITY_GATE_CONTRACT_VERSION),
        ]
    )


def check_compatibility(request: CompatibilityCheckRequest) -> CompatibilityCheckResponse:
    matrix = build_compatibility_matrix()
    entry = next((item for item in matrix.entries if item.contract == request.contract), None)
    if entry is None:
        return CompatibilityCheckResponse(
            contract=request.contract,
            version=request.version,
            status=CompatibilityStatus.UNKNOWN,
            reason="Unknown contract.",
        )
    if request.version == entry.current_version:
        return CompatibilityCheckResponse(
            contract=request.contract,
            version=request.version,
            status=CompatibilityStatus.COMPATIBLE,
            reason="Version matches current stable contract.",
        )
    if request.version in {"legacy", "0.3", "0.4", "0.5", "0.6", "1.0"}:
        return CompatibilityCheckResponse(
            contract=request.contract,
            version=request.version,
            status=CompatibilityStatus.MIGRATION_REQUIRED,
            reason="Legacy version requires compatibility shim or migration.",
        )
    return CompatibilityCheckResponse(
        contract=request.contract,
        version=request.version,
        status=CompatibilityStatus.UNSUPPORTED,
        reason="Version is not in the local compatibility matrix.",
    )
