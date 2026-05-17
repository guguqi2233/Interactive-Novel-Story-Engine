from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.api import (
    AuthoringCreateWorldRequest,
    AuthoringCreateWorldResponse,
    AuthoringFileListResponse,
    AuthoringFileResponse,
    AuthoringFileWriteRequest,
    AuthoringFileWriteResponse,
    AuthoringModListResponse,
    AuthoringModSummaryResponse,
    AuthoringModValidationResponse,
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
    LoadGameResponse,
    SaveGameResponse,
    SaveListResponse,
    SaveSummaryResponse,
    StartGameRequest,
    StartGameResponse,
)
from app.config import get_settings
from app.core.event_log import Event
from app.core.world_state import GameState
from app.db.models import SaveGame
from app.db.repository import SaveRepositoryError, SQLiteSaveRepository
from app.db.save_service import SaveService
from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.mod_loader import ModInfo, ModLoader, ModLoaderError, ModValidationReport
from app.engine.content.validator import ValidationReport
from app.engine.content.world_loader import WorldLoaderError
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.time import format_game_time
from app.llm.provider_base import LLMProviderError
from app.session_store import InMemorySessionStore, build_visible_state


def _sqlite_path_from_url(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        return database_url.removeprefix("sqlite:///")
    if database_url.startswith("sqlite://"):
        return database_url.removeprefix("sqlite://")
    return database_url


settings = get_settings()

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


def debug_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(active_settings.enable_debug_api)


def authoring_api_enabled() -> bool:
    active_settings = getattr(app.state, "settings", settings)
    return bool(active_settings.enable_authoring_api)


def require_debug_api() -> None:
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
    )


def _world_name_for_state(state: GameState) -> str:
    try:
        pack = WorldLoader(get_worlds_root()).load(state.world_id)
    except Exception:
        return state.world_id
    return pack.manifest.name


@app.post("/game/{session_id}/save", response_model=SaveGameResponse)
def save_game(session_id: str) -> SaveGameResponse:
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


@app.get("/debug/sessions/{session_id}/events", response_model=DebugEventListResponse)
def get_debug_session_events(session_id: str) -> DebugEventListResponse:
    require_debug_api()
    game_loop = get_session_store().get_session(session_id)
    if game_loop is None:
        raise HTTPException(status_code=404, detail=f"Unknown game session: {session_id}")
    return DebugEventListResponse(
        events=[_debug_event_response(event) for event in game_loop.event_log.list_events()]
    )


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
        dependencies=manifest.dependencies,
        conflicts=manifest.conflicts,
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
