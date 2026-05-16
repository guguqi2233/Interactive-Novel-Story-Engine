from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.api import (
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
from app.engine.content.world_loader import WorldLoaderError
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


def require_debug_api() -> None:
    if not debug_api_enabled():
        raise HTTPException(status_code=403, detail="Debug API is disabled")


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
def list_saves() -> SaveListResponse:
    try:
        saves = get_save_repository().list_saves()
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
    return SaveSummaryResponse(
        save_id=save.save_id,
        world_id=state.world_id,
        turn=state.turn,
        created_at=save.created_at.isoformat(),
        updated_at=save.updated_at.isoformat(),
    )


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
