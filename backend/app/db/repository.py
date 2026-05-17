import json
import sqlite3
from pathlib import Path

from app.core.event_log import Event
from app.core.world_state import GameState, load_game_state_payload
from app.db.models import SaveGame, StoredEvent, StoredMemory
from app.llm.memory_store import MemoryRecord


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

    def list_saves(self, world_id: str | None = None) -> list[SaveGame]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT save_id, state_json, created_at, updated_at
                FROM save_games
                ORDER BY updated_at DESC, save_id ASC
                """
            ).fetchall()
        saves = [_row_to_save(row) for row in rows]
        if world_id is None:
            return saves
        return [
            save
            for save in saves
            if load_game_state_payload(json.loads(save.state_json)).world_id == world_id
        ]

    def load_save(self, save_id: str) -> GameState:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state_json FROM save_games WHERE save_id = ?",
                (save_id,),
            ).fetchone()
        if row is None:
            raise SaveRepositoryError(f"Save not found: {save_id}")
        return load_game_state_payload(json.loads(row["state_json"]))

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
                sequence = self._next_event_sequence(connection, save_id)
                connection.execute(
                    """
                    INSERT INTO stored_events (event_id, save_id, turn, event_json, sequence, created_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (event.event_id, save_id, event.turn, event_json, sequence),
                )
            except sqlite3.IntegrityError as exc:
                raise SaveRepositoryError(f"Event already exists: {event.event_id}") from exc
            row = connection.execute(
                """
                SELECT event_id, save_id, turn, event_json, sequence, created_at
                FROM stored_events
                WHERE event_id = ?
                """,
                (event.event_id,),
            ).fetchone()
        return _row_to_event(row)

    def save_snapshot(
        self,
        save_id: str,
        state: GameState,
        events: list[Event],
        memories: list[MemoryRecord] | None = None,
    ) -> SaveGame:
        state_json = _dump_model_json(state)
        with self._connect() as connection:
            try:
                connection.execute("BEGIN")
                connection.execute(
                    """
                    INSERT INTO save_games (save_id, state_json, created_at, updated_at)
                    VALUES (?, ?, datetime('now'), datetime('now'))
                    ON CONFLICT(save_id) DO UPDATE SET
                        state_json = excluded.state_json,
                        updated_at = datetime('now')
                    """,
                    (save_id, state_json),
                )
                connection.execute(
                    "DELETE FROM stored_events WHERE save_id = ?",
                    (save_id,),
                )
                for sequence, event in enumerate(events):
                    connection.execute(
                        """
                        INSERT INTO stored_events (event_id, save_id, turn, event_json, sequence, created_at)
                        VALUES (?, ?, ?, ?, ?, datetime('now'))
                        """,
                        (event.event_id, save_id, event.turn, _dump_model_json(event), sequence),
                    )
                if memories is not None:
                    self._replace_memories(connection, save_id, memories)
                row = connection.execute(
                    "SELECT save_id, state_json, created_at, updated_at FROM save_games WHERE save_id = ?",
                    (save_id,),
                ).fetchone()
                connection.commit()
            except sqlite3.IntegrityError as exc:
                connection.rollback()
                raise SaveRepositoryError(f"Could not save snapshot: {save_id}") from exc
            except Exception:
                connection.rollback()
                raise
        return _row_to_save(row)

    def delete_save(self, save_id: str) -> None:
        with self._connect() as connection:
            try:
                connection.execute("BEGIN")
                if not self._save_exists_in_connection(connection, save_id):
                    raise SaveRepositoryError(f"Save not found: {save_id}")
                connection.execute("DELETE FROM stored_events WHERE save_id = ?", (save_id,))
                connection.execute("DELETE FROM stored_memories WHERE save_id = ?", (save_id,))
                connection.execute("DELETE FROM save_games WHERE save_id = ?", (save_id,))
                connection.commit()
            except SaveRepositoryError:
                connection.rollback()
                raise
            except Exception:
                connection.rollback()
                raise

    def save_memories(self, save_id: str, memories: list[MemoryRecord]) -> list[MemoryRecord]:
        if not self._save_exists(save_id):
            raise SaveRepositoryError(f"Save not found: {save_id}")
        with self._connect() as connection:
            try:
                connection.execute("BEGIN")
                self._replace_memories(connection, save_id, memories)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        return list(memories)

    def append_memory(self, save_id: str, memory: MemoryRecord) -> StoredMemory:
        if not self._save_exists(save_id):
            raise SaveRepositoryError(f"Save not found: {save_id}")
        with self._connect() as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO stored_memories (memory_id, save_id, memory_json, created_turn, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(save_id, memory_id) DO UPDATE SET
                        memory_json = excluded.memory_json,
                        created_turn = excluded.created_turn
                    """,
                    (
                        memory.id,
                        save_id,
                        _dump_model_json(memory),
                        memory.created_turn,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise SaveRepositoryError(f"Could not store memory: {memory.id}") from exc
            row = connection.execute(
                """
                SELECT memory_id, save_id, memory_json, created_turn, created_at
                FROM stored_memories
                WHERE save_id = ? AND memory_id = ?
                """,
                (save_id, memory.id),
            ).fetchone()
        return _row_to_memory(row)

    def list_memories(self, save_id: str) -> list[MemoryRecord]:
        if not self._save_exists(save_id):
            raise SaveRepositoryError(f"Save not found: {save_id}")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT memory_json
                FROM stored_memories
                WHERE save_id = ?
                ORDER BY created_turn DESC, memory_id ASC
                """,
                (save_id,),
            ).fetchall()
        return [MemoryRecord.model_validate(json.loads(row["memory_json"])) for row in rows]

    def list_events(self, save_id: str) -> list[Event]:
        if not self._save_exists(save_id):
            raise SaveRepositoryError(f"Save not found: {save_id}")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_json
                FROM stored_events
                WHERE save_id = ?
                ORDER BY sequence ASC
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
                    sequence INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (save_id) REFERENCES save_games(save_id)
                )
                """
            )
            self._ensure_event_sequence_column(connection)
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stored_events_save_sequence
                ON stored_events(save_id, sequence)
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS stored_memories (
                    memory_id TEXT NOT NULL,
                    save_id TEXT NOT NULL,
                    memory_json TEXT NOT NULL,
                    created_turn INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (save_id, memory_id),
                    FOREIGN KEY (save_id) REFERENCES save_games(save_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stored_memories_save_turn
                ON stored_memories(save_id, created_turn)
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _save_exists(self, save_id: str) -> bool:
        with self._connect() as connection:
            return self._save_exists_in_connection(connection, save_id)
        return False

    def _save_exists_in_connection(self, connection: sqlite3.Connection, save_id: str) -> bool:
        row = connection.execute(
            "SELECT 1 FROM save_games WHERE save_id = ?",
            (save_id,),
        ).fetchone()
        return row is not None

    def _next_event_sequence(self, connection: sqlite3.Connection, save_id: str) -> int:
        row = connection.execute(
            "SELECT COALESCE(MAX(sequence), -1) + 1 AS next_sequence FROM stored_events WHERE save_id = ?",
            (save_id,),
        ).fetchone()
        if row is None:
            return 0
        return int(row["next_sequence"])

    def _ensure_event_sequence_column(self, connection: sqlite3.Connection) -> None:
        columns = connection.execute("PRAGMA table_info(stored_events)").fetchall()
        if any(row["name"] == "sequence" for row in columns):
            return
        connection.execute(
            "ALTER TABLE stored_events ADD COLUMN sequence INTEGER NOT NULL DEFAULT 0"
        )

    def _replace_memories(
        self,
        connection: sqlite3.Connection,
        save_id: str,
        memories: list[MemoryRecord],
    ) -> None:
        connection.execute(
            "DELETE FROM stored_memories WHERE save_id = ?",
            (save_id,),
        )
        for memory in memories:
            connection.execute(
                """
                INSERT INTO stored_memories (memory_id, save_id, memory_json, created_turn, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                """,
                (memory.id, save_id, _dump_model_json(memory), memory.created_turn),
            )


def _dump_model_json(model: GameState | Event | MemoryRecord) -> str:
    return model.model_dump_json()


def _row_to_save(row: sqlite3.Row | None) -> SaveGame:
    if row is None:
        raise SaveRepositoryError("Expected save row")
    return SaveGame.model_validate(dict(row))


def _row_to_event(row: sqlite3.Row | None) -> StoredEvent:
    if row is None:
        raise SaveRepositoryError("Expected event row")
    return StoredEvent.model_validate(dict(row))


def _row_to_memory(row: sqlite3.Row | None) -> StoredMemory:
    if row is None:
        raise SaveRepositoryError("Expected memory row")
    return StoredMemory.model_validate(dict(row))
