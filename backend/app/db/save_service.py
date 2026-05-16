from app.core.game_loop import GameLoop, GameLoopResult
from app.db.repository import SQLiteSaveRepository


class SaveService:
    def __init__(self, repository: SQLiteSaveRepository) -> None:
        self._repository = repository

    def create_save(self, save_id: str, game_loop: GameLoop) -> None:
        self._repository.save_snapshot(save_id, game_loop.state, game_loop.event_log.list_events())

    def persist_step(self, save_id: str, result: GameLoopResult) -> None:
        self._repository.save_state(save_id, result.state)
        if result.event is not None:
            self._repository.append_event(save_id, result.event)

    def save_game_loop(self, save_id: str, game_loop: GameLoop) -> None:
        self._repository.save_snapshot(save_id, game_loop.state, game_loop.event_log.list_events())

