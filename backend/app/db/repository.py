import json
import sqlite3
from pathlib import Path

from app.core.event_log import Event
from app.core.world_state import GameState
from app.db.models import SaveGame, StoredEvent


class SaveRepositoryError(RuntimeError):
    """Raised when save storage cannot complete an operation."""


class SQLiteSaveRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self._initialize_schema()

    def create_save(self, save_id: str, state: GameState) -> SaveGame:
        state_json = _dump_model_json(state)
        with self._connect() as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO save_games (save_id, state_json, created_at, updated_at)
                    VALUES (?, ?, datetime('now'), datetime('now'))
                    """,
                    (save_id, state_json),
                )
            except sqlite3.IntegrityError as exc:
                raise SaveRepositoryError(f"Save already exists: {save_id}") from exc
            row = connection.execute(
                "SELECT save_id, state_json, created_at, updated_at FROM save_games WHERE save_id = ?",
                (save_id,),
            ).fetchone()
        return _row_to_save(row)

    def load_save(self, save_id: str) -> GameState:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state_json FROM save_games WHERE save_id = ?",
                (save_id,),
            ).fetchone()
        if row is None:
            raise SaveRepositoryError(f"Save not found: {save_id}")
        return GameState.model_validate(json.loads(row["state_json"]))

    def save_state(self, save_id: str, state: GameState) -> SaveGame:
        state_json = _dump_model_json(state)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE save_games
                SET state_json = ?, updated_at = datetime('now')
                WHERE save_id = ?
                """,
                (state_json, save_id),
            )
            if cursor.rowcount == 0:
                raise SaveRepositoryError(f"Save not found: {save_id}")
            row = connection.execute(
                "SELECT save_id, state_json, created_at, updated_at FROM save_games WHERE save_id = ?",
                (save_id,),
            ).fetchone()
        return _row_to_save(row)

    def append_event(self, save_id: str, event: Event) -> StoredEvent:
        if not self._save_exists(save_id):
            raise SaveRepositoryError(f"Save not found: {save_id}")
        event_json = _dump_model_json(event)
        with self._connect() as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO stored_events (event_id, save_id, turn, event_json, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                    """,
                    (event.event_id, save_id, event.turn, event_json),
                )
            except sqlite3.IntegrityError as exc:
                raise SaveRepositoryError(f"Event already exists: {event.event_id}") from exc
            row = connection.execute(
                """
                SELECT event_id, save_id, turn, event_json, created_at
                FROM stored_events
                WHERE event_id = ?
                """,
                (event.event_id,),
            ).fetchone()
        return _row_to_event(row)

    def list_events(self, save_id: str) -> list[Event]:
        if not self._save_exists(save_id):
            raise SaveRepositoryError(f"Save not found: {save_id}")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_json
                FROM stored_events
                WHERE save_id = ?
                ORDER BY turn ASC, created_at ASC, event_id ASC
                """,
                (save_id,),
            ).fetchall()
        return [Event.model_validate(json.loads(row["event_json"])) for row in rows]

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS save_games (
                    save_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS stored_events (
                    event_id TEXT PRIMARY KEY,
                    save_id TEXT NOT NULL,
                    turn INTEGER NOT NULL,
                    event_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (save_id) REFERENCES save_games(save_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stored_events_save_turn
                ON stored_events(save_id, turn)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _save_exists(self, save_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM save_games WHERE save_id = ?",
                (save_id,),
            ).fetchone()
        return row is not None


def _dump_model_json(model: GameState | Event) -> str:
    return model.model_dump_json()


def _row_to_save(row: sqlite3.Row | None) -> SaveGame:
    if row is None:
        raise SaveRepositoryError("Expected save row")
    return SaveGame.model_validate(dict(row))


def _row_to_event(row: sqlite3.Row | None) -> StoredEvent:
    if row is None:
        raise SaveRepositoryError("Expected event row")
    return StoredEvent.model_validate(dict(row))

