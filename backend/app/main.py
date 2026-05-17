import json
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.api import (
    AuthoringCreateWorldRequest,
    AuthoringCreateWorldResponse,
    AuthoringFileListResponse,
    AuthoringFilePreviewResponse,
    AuthoringFileResponse,
    AuthoringDraftFileRequest,
    AuthoringFileWriteRequest,
    AuthoringFileWriteResponse,
    AuthoringModListResponse,
    AuthoringModSummaryResponse,
    AuthoringModValidationResponse,
    AuthoringDiffSummaryResponse,
    AuthoringImpactAnalysisResponse,
    AuthoringValidationIssueResponse,
    AuthoringValidationResponse,
    AuthoringWorldDetailResponse,
    AuthoringWorldListResponse,
    AuthoringWorldSummaryResponse,
    DeleteSaveResponse,
    GameInputRequest,
    GameInputResponse,
    GameStateResponse,
    DebugEventListResponse,
    DebugEventResponse,
    DebugPerformanceRecentResponse,
    DebugPerformanceSampleResponse,
    DebugPerformanceSummaryEntryResponse,
    DebugPerformanceSummaryResponse,
    LoadGameResponse,
    MigrationHistoryEntryResponse,
    MigrationInfoResponse,
    MigrationListResponse,
    SaveGameResponse,
    SaveListResponse,
    SaveMigrationResponse,
    SaveMigrationStatusResponse,
    SaveSummaryResponse,
    StartGameRequest,
    StartGameResponse,
)
from app.config import get_settings
from app.core.event_log import Event
from app.core.instrumentation import (
    get_performance_recorder,
    performance_logging_enabled,
    set_performance_logging_enabled,
)
from app.core.world_state import GameState
from app.db.models import SaveGame
from app.db.migration_service import MigrationService
from app.db.repository import SaveRepositoryError, SQLiteSaveRepository
from app.db.save_service import SaveService
from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.mod_loader import ModInfo, ModLoader, ModLoaderError, ModValidationReport
from app.engine.content.validator import ValidationReport
from app.engine.content.world_loader import WorldLoaderError
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.time import format_game_time
from app.engine.rules.graphs import (
    FactionGraph,
    RelationshipGraph,
    build_faction_graph,
    build_relationship_graph,
)
from app.llm.provider_base import LLMProviderError
from app.session_store import InMemorySessionStore, build_visible_state


def _sqlite_path_from_url(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        return database_url.removeprefix("sqlite:///")
    if database_url.startswith("sqlite://"):
        return database_url.removeprefix("sqlite://")
    return database_url


settings = get_settings()
set_performance_logging_enabled(settings.enable_perf_logging)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.state.session_store = InMemorySessionStore()
app.state.save_repository = SQLiteSaveRepository(_sqlite_path_from_url(settings.database_url))


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


def get_session_store() -> InMemorySessionStore:
    return app.state.session_store


def get_save_repository() -> SQLiteSaveRepository:
    return app.state.save_repository


def get_migration_service() -> MigrationService:
    return MigrationService(get_save_repository())


def debug_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(active_settings.enable_debug_api)


def sync_runtime_settings() -> None:
    active_settings = getattr(app.state, "settings", settings)
    set_performance_logging_enabled(bool(active_settings.enable_perf_logging))


def authoring_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(active_settings.enable_authoring_api)


def require_debug_api() -> None:
    sync_runtime_settings()
    if not debug_api_enabled():
        raise HTTPException(status_code=403, detail="Debug API is disabled")


def require_authoring_api() -> None:
    if not authoring_api_enabled():
        raise HTTPException(status_code=403, detail="Authoring API is disabled")


def get_worlds_root() -> str:
    return str(getattr(app.state, "worlds_root", "worlds"))


def get_mods_root() -> str:
    return str(getattr(app.state, "mods_root", "mods"))


def get_authoring_service() -> ContentAuthoringService:
    return ContentAuthoringService(get_worlds_root())


def get_mod_loader() -> ModLoader:
    return ModLoader(get_mods_root())


@app.post("/game/start", response_model=StartGameResponse)
def start_game(request: StartGameRequest | None = None) -> StartGameResponse:
    world_id = request.world_id if request else None
    try:
        session_id, game_loop = get_session_store().create_session(world_id)
    except WorldLoaderError as exc:
        status_code = 404 if str(exc).startswith("World pack not found:") else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    return StartGameResponse(
        session_id=session_id,
        world_id=game_loop.state.world_id,
        visible_state=build_visible_state(game_loop.state),
        turn=game_loop.state.turn,
    )


@app.post("/game/input", response_model=GameInputResponse)
def submit_game_input(request: GameInputRequest) -> GameInputResponse:
    sync_runtime_settings()
    game_loop = get_session_store().get_session(request.session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {request.session_id}")

    try:
        result = game_loop.step(request.player_input)
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return GameInputResponse(
        narrative_text=result.narrative.text,
        suggested_actions=result.narrative.suggested_actions,
        visible_state=build_visible_state(result.state),
        turn=result.state.turn,
    )


@app.get("/game/state/{session_id}", response_model=GameStateResponse)
def get_game_state(session_id: str) -> GameStateResponse:
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")

    return GameStateResponse(
        session_id=session_id,
        visible_state=build_visible_state(game_loop.state),
        turn=game_loop.state.turn,
    )


@app.get("/game/{session_id}/graphs/relationships", response_model=RelationshipGraph)
def get_player_relationship_graph(session_id: str) -> RelationshipGraph:
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_relationship_graph(game_loop.state, debug=False)


@app.get("/game/{session_id}/graphs/factions", response_model=FactionGraph)
def get_player_faction_graph(session_id: str) -> FactionGraph:
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_faction_graph(game_loop.state, debug=False)


@app.get("/game/saves", response_model=SaveListResponse)
def list_saves(world_id: str | None = None) -> SaveListResponse:
    try:
        saves = get_save_repository().list_saves(world_id=world_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return SaveListResponse(
        saves=[
            _save_summary_response(save)
            for save in saves
        ]
    )


def _save_summary_response(save: SaveGame) -> SaveSummaryResponse:
    state = GameState.model_validate_json(save.state_json)
    location = state.locations.get(state.player.location_id)
    return SaveSummaryResponse(
        save_id=save.save_id,
        world_id=state.world_id,
        world_name=_world_name_for_state(state),
        turn=state.turn,
        current_location_name=location.name if location else state.player.location_id,
        formatted_time=format_game_time(state),
        created_at=save.created_at.isoformat(),
        updated_at=save.updated_at.isoformat(),
        player_summary=f"Turn {state.turn} at {location.name if location else state.player.location_id}",
        enabled_mods=_enabled_mods_from_save(save),
    )


def _enabled_mods_from_save(save: SaveGame) -> dict[str, str]:
    try:
        payload = json.loads(save.enabled_mods)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, list):
        return {}
    result: dict[str, str] = {}
    for item in payload:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            result[item["id"]] = str(item.get("version", "unknown"))
    return result


def _world_name_for_state(state: GameState) -> str:
    try:
        pack = WorldLoader(get_worlds_root()).load(state.world_id)
    except Exception:
        return state.world_id
    return pack.manifest.name


@app.post("/game/{session_id}/save", response_model=SaveGameResponse)
def save_game(session_id: str) -> SaveGameResponse:
    sync_runtime_settings()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")

    save_id = str(uuid4())
    try:
        SaveService(get_save_repository()).save_game_loop(save_id, game_loop)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return SaveGameResponse(
        save_id=save_id,
        session_id=session_id,
        world_id=game_loop.state.world_id,
        turn=game_loop.state.turn,
    )


@app.delete("/game/saves/{save_id}", response_model=DeleteSaveResponse)
def delete_save(save_id: str) -> DeleteSaveResponse:
    try:
        get_save_repository().delete_save(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DeleteSaveResponse(save_id=save_id)


@app.post("/game/load/{save_id}", response_model=LoadGameResponse)
def load_game(save_id: str) -> LoadGameResponse:
    sync_runtime_settings()
    repository = get_save_repository()
    try:
        state = repository.load_save(save_id)
        events = repository.list_events(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    session_id, game_loop = get_session_store().restore_session(state, events)
    return LoadGameResponse(
        save_id=save_id,
        session_id=session_id,
        visible_state=build_visible_state(game_loop.state),
        turn=game_loop.state.turn,
    )


@app.get("/game/saves/{save_id}/migration-status", response_model=SaveMigrationStatusResponse)
def get_save_migration_status(save_id: str) -> SaveMigrationStatusResponse:
    return _get_save_migration_status(save_id)


@app.get("/saves/{save_id}/migration-status", response_model=SaveMigrationStatusResponse)
def get_save_migration_status_alias(save_id: str) -> SaveMigrationStatusResponse:
    return _get_save_migration_status(save_id)


def _get_save_migration_status(save_id: str) -> SaveMigrationStatusResponse:
    try:
        status = get_migration_service().status(
            save_id,
            available_mod_versions={
                mod.manifest.id: mod.manifest.version
                for mod in get_mod_loader().discover_mods()
            },
        )
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SaveMigrationStatusResponse(
        save_id=status.save_id,
        engine_version=status.engine_version,
        schema_version=status.schema_version,
        world_id=status.world_id,
        world_version=status.world_version,
        content_pack_version=status.content_pack_version,
        needs_migration=status.needs_migration,
        target_schema_version=status.target_schema_version,
        migration_path=[item.migration_id for item in status.migration_path],
        warnings=status.warnings,
    )


@app.post("/game/saves/{save_id}/migrate-dry-run", response_model=SaveMigrationResponse)
def dry_run_save_migration(save_id: str) -> SaveMigrationResponse:
    return _dry_run_save_migration(save_id)


@app.post("/saves/{save_id}/migrate-dry-run", response_model=SaveMigrationResponse)
def dry_run_save_migration_alias(save_id: str) -> SaveMigrationResponse:
    return _dry_run_save_migration(save_id)


def _dry_run_save_migration(save_id: str) -> SaveMigrationResponse:
    try:
        report = get_migration_service().dry_run(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _migration_response(report)


@app.post("/game/saves/{save_id}/migrate", response_model=SaveMigrationResponse)
def migrate_save(save_id: str) -> SaveMigrationResponse:
    return _migrate_save(save_id)


@app.post("/saves/{save_id}/migrate", response_model=SaveMigrationResponse)
def migrate_save_alias(save_id: str) -> SaveMigrationResponse:
    return _migrate_save(save_id)


def _migrate_save(save_id: str) -> SaveMigrationResponse:
    try:
        report = get_migration_service().apply(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _migration_response(report)


@app.get("/migrations", response_model=MigrationListResponse)
def list_migrations() -> MigrationListResponse:
    return MigrationListResponse(
        migrations=[
            MigrationInfoResponse(
                migration_id=migration.migration_id,
                source_version=migration.source_version,
                target_version=migration.target_version,
                description=migration.description,
            )
            for migration in get_migration_service().list_available_migrations()
        ]
    )


@app.get("/debug/sessions/{session_id}/events", response_model=DebugEventListResponse)
def get_debug_session_events(session_id: str) -> DebugEventListResponse:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return DebugEventListResponse(
        events=[_debug_event_response(event) for event in game_loop.event_log.list_events()]
    )


@app.get("/debug/sessions/{session_id}/graphs/relationships", response_model=RelationshipGraph)
def get_debug_relationship_graph(session_id: str) -> RelationshipGraph:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_relationship_graph(game_loop.state, debug=True)


@app.get("/debug/sessions/{session_id}/graphs/factions", response_model=FactionGraph)
def get_debug_faction_graph(session_id: str) -> FactionGraph:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return build_faction_graph(game_loop.state, debug=True)


@app.get("/debug/saves/{save_id}/events", response_model=DebugEventListResponse)
def get_debug_save_events(save_id: str) -> DebugEventListResponse:
    require_debug_api()
    try:
        events = get_save_repository().list_events(save_id)
    except SaveRepositoryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DebugEventListResponse(
        events=[_debug_event_response(event) for event in events]
    )


@app.get("/debug/performance/recent", response_model=DebugPerformanceRecentResponse)
def get_debug_performance_recent(limit: int = 50) -> DebugPerformanceRecentResponse:
    require_debug_api()
    recorder = get_performance_recorder()
    return DebugPerformanceRecentResponse(
        enabled=performance_logging_enabled(),
        samples=[
            DebugPerformanceSampleResponse(
                sample_id=sample.sample_id,
                name=sample.name,
                duration_ms=sample.duration_ms,
                started_at=sample.started_at.isoformat(),
                stage_durations_ms=sample.stage_durations_ms,
                tags=sample.tags,
            )
            for sample in recorder.recent(limit)
        ],
    )


@app.get("/debug/performance/summary", response_model=DebugPerformanceSummaryResponse)
def get_debug_performance_summary() -> DebugPerformanceSummaryResponse:
    require_debug_api()
    summary = get_performance_recorder().summary()
    return DebugPerformanceSummaryResponse(
        enabled=summary.enabled,
        sample_count=summary.sample_count,
        entries=[
            DebugPerformanceSummaryEntryResponse(
                name=entry.name,
                count=entry.count,
                total_duration_ms=entry.total_duration_ms,
                average_duration_ms=entry.average_duration_ms,
                max_duration_ms=entry.max_duration_ms,
            )
            for entry in summary.entries
        ],
    )


def _debug_event_response(event: Event) -> DebugEventResponse:
    return DebugEventResponse(
        turn=event.turn,
        event_id=event.event_id,
        actor_id=event.actor_id,
        action_type=event.action_type,
        result=event.result,
        state_deltas=event.state_deltas,
        visible_to_player=event.visible_to_player,
        created_at=event.created_at.isoformat(),
    )


def _migration_response(report: object) -> SaveMigrationResponse:
    return SaveMigrationResponse(
        save_id=getattr(report, "save_id"),
        source_version=getattr(report, "source_version"),
        target_version=getattr(report, "target_version"),
        dry_run=getattr(report, "dry_run"),
        backup_save_id=getattr(report, "backup_save_id"),
        success=getattr(report, "success"),
        warnings=getattr(report, "warnings"),
        applied_migrations=[
            MigrationHistoryEntryResponse(
                migration_id=entry.migration_id,
                source_version=entry.source_version,
                target_version=entry.target_version,
                description=entry.description,
                applied_at=entry.applied_at,
            )
            for entry in getattr(report, "applied_migrations")
        ],
    )


@app.get("/authoring/worlds", response_model=AuthoringWorldListResponse)
def list_authoring_worlds() -> AuthoringWorldListResponse:
    require_authoring_api()
    service = get_authoring_service()
    return AuthoringWorldListResponse(
        worlds=[_authoring_world_response(world) for world in service.list_worlds()]
    )


@app.post("/authoring/worlds", response_model=AuthoringCreateWorldResponse)
def create_authoring_world(request: AuthoringCreateWorldRequest) -> AuthoringCreateWorldResponse:
    require_authoring_api()
    try:
        world, report = get_authoring_service().create_world(
            request.world_id,
            request.name,
            request.description,
            request.start_location_id,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringCreateWorldResponse(
        world=_authoring_world_response(world),
        validation=_authoring_validation_response(report),
    )


@app.get("/authoring/worlds/{world_id}", response_model=AuthoringWorldDetailResponse)
def get_authoring_world(world_id: str) -> AuthoringWorldDetailResponse:
    require_authoring_api()
    service = get_authoring_service()
    try:
        world = service.get_world_summary(world_id)
        report = service.validate_world(world_id)
        files = service.list_files(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthoringWorldDetailResponse(
        world=_authoring_world_response(world),
        files=files,
        validation=_authoring_validation_response(report),
    )


@app.get("/authoring/worlds/{world_id}/files", response_model=AuthoringFileListResponse)
def list_authoring_files(world_id: str) -> AuthoringFileListResponse:
    require_authoring_api()
    try:
        files = get_authoring_service().list_files(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AuthoringFileListResponse(world_id=world_id, files=files)


@app.get("/authoring/worlds/{world_id}/files/{file_name}", response_model=AuthoringFileResponse)
def read_authoring_file(world_id: str, file_name: str) -> AuthoringFileResponse:
    require_authoring_api()
    try:
        content = get_authoring_service().read_file(world_id, file_name)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringFileResponse(world_id=world_id, file_name=file_name, content=content)


@app.put("/authoring/worlds/{world_id}/files/{file_name}", response_model=AuthoringFileWriteResponse)
def write_authoring_file(
    world_id: str,
    file_name: str,
    request: AuthoringFileWriteRequest,
) -> AuthoringFileWriteResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().write_file(world_id, file_name, request.content)
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not report.ok:
        raise HTTPException(
            status_code=400,
            detail=_authoring_validation_response(report).model_dump(mode="json"),
        )
    return AuthoringFileWriteResponse(
        world_id=world_id,
        file_name=file_name,
        validation=_authoring_validation_response(report),
    )


@app.post(
    "/authoring/worlds/{world_id}/preview-file-change",
    response_model=AuthoringFilePreviewResponse,
)
def preview_authoring_file_change(
    world_id: str,
    request: AuthoringDraftFileRequest,
) -> AuthoringFilePreviewResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().preview_file_change(
            world_id,
            request.file_name,
            request.proposed_content,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_preview_response(world_id, request.file_name, report)


@app.post(
    "/authoring/worlds/{world_id}/validate-draft",
    response_model=AuthoringValidationResponse,
)
def validate_authoring_draft(
    world_id: str,
    request: AuthoringDraftFileRequest,
) -> AuthoringValidationResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().validate_draft(
            world_id,
            request.file_name,
            request.proposed_content,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_validation_response(report)


@app.post(
    "/authoring/worlds/{world_id}/impact-analysis",
    response_model=AuthoringImpactAnalysisResponse,
)
def analyze_authoring_draft_impact(
    world_id: str,
    request: AuthoringDraftFileRequest,
) -> AuthoringImpactAnalysisResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().analyze_file_impact(
            world_id,
            request.file_name,
            request.proposed_content,
        )
    except AuthoringError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_impact_response(report)


@app.post("/authoring/worlds/{world_id}/validate", response_model=AuthoringValidationResponse)
def validate_authoring_world(world_id: str) -> AuthoringValidationResponse:
    require_authoring_api()
    try:
        report = get_authoring_service().validate_world(world_id)
    except AuthoringError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _authoring_validation_response(report)


@app.get("/authoring/mods", response_model=AuthoringModListResponse)
def list_authoring_mods() -> AuthoringModListResponse:
    require_authoring_api()
    try:
        mods = get_mod_loader().discover_mods()
    except ModLoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AuthoringModListResponse(mods=[_authoring_mod_response(mod) for mod in mods])


@app.post("/authoring/mods/{mod_id}/validate", response_model=AuthoringModValidationResponse)
def validate_authoring_mod(mod_id: str) -> AuthoringModValidationResponse:
    require_authoring_api()
    try:
        report = get_mod_loader().validate_mod(mod_id)
    except ModLoaderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _authoring_mod_validation_response(report)


def _authoring_world_response(world: object) -> AuthoringWorldSummaryResponse:
    return AuthoringWorldSummaryResponse(
        world_id=getattr(world, "world_id"),
        name=getattr(world, "name"),
        description=getattr(world, "description"),
        version=getattr(world, "version"),
        file_count=getattr(world, "file_count"),
    )


def _authoring_mod_response(mod: ModInfo) -> AuthoringModSummaryResponse:
    manifest = mod.manifest
    return AuthoringModSummaryResponse(
        id=manifest.id,
        name=manifest.name,
        version=manifest.version,
        engine_version_min=manifest.engine_version_min,
        engine_version_max=manifest.engine_version_max,
        content_schema_version=manifest.content_schema_version,
        dependencies=manifest.dependencies,
        optional_dependencies=manifest.optional_dependencies,
        conflicts=manifest.conflicts,
        load_order_hint=manifest.load_order_hint,
        compatible_worlds=manifest.compatible_worlds,
        migration_notes=manifest.migration_notes,
        entry_worlds=manifest.entry_worlds,
        content_paths=manifest.content_paths,
        author=manifest.author,
        description=manifest.description,
    )


def _authoring_mod_validation_response(report: ModValidationReport) -> AuthoringModValidationResponse:
    return AuthoringModValidationResponse(
        mod_id=report.mod_id,
        ok=report.ok,
        errors=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.errors
        ],
        warnings=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.warnings
        ],
        suggestions=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.suggestions
        ],
        world_report_ids=sorted(report.world_reports),
    )


def _authoring_preview_response(
    world_id: str,
    file_name: str,
    report: object,
) -> AuthoringFilePreviewResponse:
    return AuthoringFilePreviewResponse(
        world_id=world_id,
        file_name=file_name,
        parsed_ok=getattr(report, "parsed_ok"),
        validation_report=_authoring_validation_response(getattr(report, "validation_report")),
        normalized_yaml=getattr(report, "normalized_yaml"),
        diff_summary=AuthoringDiffSummaryResponse.model_validate(
            getattr(report, "diff_summary").model_dump(mode="json")
        ),
        affected_refs=getattr(report, "affected_refs"),
        potential_save_migration_required=getattr(
            report,
            "potential_save_migration_required",
        ),
        impact=_authoring_impact_response(getattr(report, "impact")),
    )


def _authoring_impact_response(report: object) -> AuthoringImpactAnalysisResponse:
    return AuthoringImpactAnalysisResponse.model_validate(report.model_dump(mode="json"))


def _authoring_validation_response(report: ValidationReport) -> AuthoringValidationResponse:
    return AuthoringValidationResponse(
        world_id=report.world_id,
        ok=report.ok,
        errors=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.errors
        ],
        warnings=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.warnings
        ],
        suggestions=[
            AuthoringValidationIssueResponse(
                severity=issue.severity,
                file=issue.file,
                path=issue.path,
                code=issue.code,
                message=issue.message,
                ref_id=issue.ref_id,
                suggestion=issue.suggestion,
            )
            for issue in report.suggestions
        ],
    )
