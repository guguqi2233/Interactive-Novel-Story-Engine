from fastapi import FastAPI, HTTPException

from app.api import GameInputRequest, GameInputResponse, GameStateResponse, StartGameResponse
from app.config import get_settings
from app.engine.content.world_loader import WorldLoaderError
from app.llm.provider_base import LLMProviderError
from app.session_store import InMemorySessionStore, build_visible_state

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.state.session_store = InMemorySessionStore()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


def get_session_store() -> InMemorySessionStore:
    return app.state.session_store


@app.post("/game/start", response_model=StartGameResponse)
def start_game() -> StartGameResponse:
    try:
        session_id, game_loop = get_session_store().create_session()
    except WorldLoaderError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return StartGameResponse(
        session_id=session_id,
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
