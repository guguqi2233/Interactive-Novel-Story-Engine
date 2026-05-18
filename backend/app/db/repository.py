import json
import sqlite3
from pathlib import Path
from time import perf_counter

from app.core.event_log import Event
from app.core.instrumentation import record_performance_sample
from app.core.world_state import GameState, load_game_state_payload
from app.db.migrations import (
    CURRENT_ENGINE_VERSION,
    CURRENT_SAVE_SCHEMA_VERSION,
    MigrationRegistry,
    MigrationReport,
    create_default_registry,
)
from app.db.models import SaveGame, StoredEvent, StoredMemory
from app.llm.memory_store import MemoryRecord


class SaveRepositoryError(RuntimeError):
    """Raised when save storage cannot complete an operation."""


class SQLiteSaveRepository:
    def __init__(
        self,
        database_path: str | Path,
        migration_registry: MigrationRegistry | None = None,
    ) -> None:
        self.database_path = str(database_path)
        self._migration_registry = migration_registry or create_default_registry()
        self._initialize_schema()

    def create_save(self, save_id: str, state: GameState) -> SaveGame:
        state_json = _dump_model_json(state)
        metadata = _metadata_for_state(state)
        with self._connect() as connection:
            try:
                connection.execute(
                    """
                    INSERT INTO save_games (
                        save_id,
                        state_json,
                        engine_version,
                        schema_version,
                        world_id,
                        world_version,
                        content_pack_version,
                        enabled_mods,
                        migration_history,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """,
                    (
                        save_id,
                        state_json,
                        metadata["engine_version"],
                        metadata["schema_version"],
                        metadata["world_id"],
                        metadata["world_version"],
                        metadata["content_pack_version"],
                        metadata["enabled_mods"],
                        metadata["migration_history"],
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise SaveRepositoryError(f"Save already exists: {save_id}") from exc
            row = connection.execute(
                f"{_SAVE_SELECT} WHERE save_id = ?",
                (save_id,),
            ).fetchone()
        return _row_to_save(row)

    def list_saves(self, world_id: str | None = None) -> list[SaveGame]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    save_id,
                    state_json,
                    engine_version,
                    schema_version,
                    world_id,
                    world_version,
                    content_pack_version,
                    enabled_mods,
                    migration_history,
                    created_at,
                    updated_at
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

    def get_save(self, save_id: str) -> SaveGame:
        with self._connect() as connection:
            row = connection.execute(
                f"{_SAVE_SELECT} WHERE save_id = ?",
                (save_id,),
            ).fetchone()
        if row is None:
            raise SaveRepositoryError(f"Save not found: {save_id}")
        return _row_to_save(row)

    def load_save(self, save_id: str) -> GameState:
        started = perf_counter()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT state_json FROM save_games WHERE save_id = ?",
                (save_id,),
            ).fetchone()
        if row is None:
            raise SaveRepositoryError(f"Save not found: {save_id}")
        state = load_game_state_payload(json.loads(row["state_json"]))
        record_performance_sample(
            "save.load",
            (perf_counter() - started) * 1000,
            tags={"operation": "load_save"},
        )
        return state

    def save_state(self, save_id: str, state: GameState) -> SaveGame:
        started = perf_counter()
        state_json = _dump_model_json(state)
        metadata = _metadata_for_state(state)
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE save_games
                SET
                    state_json = ?,
                    engine_version = ?,
                    schema_version = ?,
                    world_id = ?,
                    world_version = ?,
                    content_pack_version = ?,
                    enabled_mods = ?,
                    updated_at = datetime('now')
                WHERE save_id = ?
                """,
                (
                    state_json,
                    metadata["engine_version"],
                    metadata["schema_version"],
                    metadata["world_id"],
                    metadata["world_version"],
                    metadata["content_pack_version"],
                    metadata["enabled_mods"],
                    save_id,
                ),
            )
            if cursor.rowcount == 0:
                raise SaveRepositoryError(f"Save not found: {save_id}")
            row = connection.execute(
                f"{_SAVE_SELECT} WHERE save_id = ?",
                (save_id,),
            ).fetchone()
        save = _row_to_save(row)
        record_performance_sample(
            "save.write",
            (perf_counter() - started) * 1000,
            tags={"operation": "save_state"},
        )
        return save

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
        enabled_mods: dict[str, str] | None = None,
    ) -> SaveGame:
        started = perf_counter()
        state_json = _dump_model_json(state)
        metadata = _metadata_for_state(state)
        if enabled_mods is not None:
            metadata["enabled_mods"] = json.dumps(
                [
                    {"id": mod_id, "version": version}
                    for mod_id, version in sorted(enabled_mods.items())
                ]
            )
        with self._connect() as connection:
            try:
                connection.execute("BEGIN")
                connection.execute(
                    """
                    INSERT INTO save_games (
                        save_id,
                        state_json,
                        engine_version,
                        schema_version,
                        world_id,
                        world_version,
                        content_pack_version,
                        enabled_mods,
                        migration_history,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', datetime('now'), datetime('now'))
                    ON CONFLICT(save_id) DO UPDATE SET
                        state_json = excluded.state_json,
                        engine_version = excluded.engine_version,
                        schema_version = excluded.schema_version,
                        world_id = excluded.world_id,
                        world_version = excluded.world_version,
                        content_pack_version = excluded.content_pack_version,
                        enabled_mods = excluded.enabled_mods,
                        updated_at = datetime('now')
                    """,
                    (
                        save_id,
                        state_json,
                        metadata["engine_version"],
                        metadata["schema_version"],
                        metadata["world_id"],
                        metadata["world_version"],
                        metadata["content_pack_version"],
                        metadata["enabled_mods"],
                    ),
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
                    f"{_SAVE_SELECT} WHERE save_id = ?",
                    (save_id,),
                ).fetchone()
                connection.commit()
            except sqlite3.IntegrityError as exc:
                connection.rollback()
                raise SaveRepositoryError(f"Could not save snapshot: {save_id}") from exc
            except Exception:
                connection.rollback()
                raise
        save = _row_to_save(row)
        record_performance_sample(
            "save.write",
            (perf_counter() - started) * 1000,
            tags={"operation": "save_snapshot"},
        )
        return save

    def migrate_save(
        self,
        save_id: str,
        *,
        dry_run: bool = False,
        create_backup: bool = True,
    ) -> MigrationReport:
        with self._connect() as connection:
            try:
                connection.execute("BEGIN")
                row = connection.execute(
                    f"{_SAVE_SELECT} WHERE save_id = ?",
                    (save_id,),
                ).fetchone()
                if row is None:
                    raise SaveRepositoryError(f"Save not found: {save_id}")
                save_data = dict(row)
                backup_save_id = f"{save_id}.backup"
                migrated_data, report = self._migration_registry.migrate_to_latest(
                    save_id,
                    save_data,
                    dry_run=dry_run,
                    backup_save_id=backup_save_id if create_backup and not dry_run else None,
                )
                if dry_run:
                    connection.rollback()
                    return report
                if create_backup and report.applied_migrations:
                    self._create_backup_in_connection(connection, save_id, backup_save_id)
                if report.applied_migrations:
                    connection.execute(
                        """
                        UPDATE save_games
                        SET
                            state_json = ?,
                            engine_version = ?,
                            schema_version = ?,
                            world_id = ?,
                            world_version = ?,
                            content_pack_version = ?,
                            enabled_mods = ?,
                            migration_history = ?,
                            updated_at = datetime('now')
                        WHERE save_id = ?
                        """,
                        (
                            migrated_data["state_json"],
                            migrated_data["engine_version"],
                            migrated_data["schema_version"],
                            migrated_data["world_id"],
                            migrated_data["world_version"],
                            migrated_data["content_pack_version"],
                            migrated_data.get("enabled_mods", "[]"),
                            migrated_data["migration_history"],
                            save_id,
                        ),
                    )
                connection.commit()
                return report
            except SaveRepositoryError:
                connection.rollback()
                raise
            except Exception as exc:
                connection.rollback()
                raise SaveRepositoryError(f"Could not migrate save {save_id}: {exc}") from exc

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
                    engine_version TEXT NOT NULL DEFAULT 'legacy',
                    schema_version TEXT NOT NULL DEFAULT 'legacy',
                    world_id TEXT NOT NULL DEFAULT 'unknown',
                    world_version TEXT NOT NULL DEFAULT 'unknown',
                    content_pack_version TEXT NOT NULL DEFAULT 'unknown',
                    enabled_mods TEXT NOT NULL DEFAULT '[]',
                    migration_history TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._ensure_save_metadata_columns(connection)
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

    def _ensure_save_metadata_columns(self, connection: sqlite3.Connection) -> None:
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(save_games)").fetchall()
        }
        defaults = {
            "engine_version": "'legacy'",
            "schema_version": "'legacy'",
            "world_id": "'unknown'",
            "world_version": "'unknown'",
            "content_pack_version": "'unknown'",
            "enabled_mods": "'[]'",
            "migration_history": "'[]'",
        }
        for column, default in defaults.items():
            if column not in columns:
                connection.execute(
                    f"ALTER TABLE save_games ADD COLUMN {column} TEXT NOT NULL DEFAULT {default}"
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

    def _create_backup_in_connection(
        self,
        connection: sqlite3.Connection,
        save_id: str,
        backup_save_id: str,
    ) -> None:
        existing_backup = connection.execute(
            "SELECT 1 FROM save_games WHERE save_id = ?",
            (backup_save_id,),
        ).fetchone()
        if existing_backup is not None:
            backup_save_id = f"{backup_save_id}.{self._next_event_sequence(connection, save_id)}"
        connection.execute(
            f"""
            INSERT INTO save_games (
                save_id,
                state_json,
                engine_version,
                schema_version,
                world_id,
                world_version,
                content_pack_version,
                enabled_mods,
                migration_history,
                created_at,
                updated_at
            )
            SELECT
                ?,
                state_json,
                engine_version,
                schema_version,
                world_id,
                world_version,
                content_pack_version,
                enabled_mods,
                migration_history,
                created_at,
                datetime('now')
            FROM save_games
            WHERE save_id = ?
            """,
            (backup_save_id, save_id),
        )
        for row in connection.execute(
            """
            SELECT event_id, turn, event_json, sequence
            FROM stored_events
            WHERE save_id = ?
            ORDER BY sequence ASC
            """,
            (save_id,),
        ).fetchall():
            connection.execute(
                """
                INSERT INTO stored_events (event_id, save_id, turn, event_json, sequence, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    f"{backup_save_id}:{row['event_id']}",
                    backup_save_id,
                    row["turn"],
                    row["event_json"],
                    row["sequence"],
                ),
            )
        for row in connection.execute(
            """
            SELECT memory_id, memory_json, created_turn
            FROM stored_memories
            WHERE save_id = ?
            ORDER BY created_turn DESC, memory_id ASC
            """,
            (save_id,),
        ).fetchall():
            connection.execute(
                """
                INSERT INTO stored_memories (memory_id, save_id, memory_json, created_turn, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                """,
                (row["memory_id"], backup_save_id, row["memory_json"], row["created_turn"]),
            )


def _dump_model_json(model: GameState | Event | MemoryRecord) -> str:
    return model.model_dump_json()


_SAVE_SELECT = """
SELECT
    save_id,
    state_json,
    engine_version,
    schema_version,
    world_id,
    world_version,
    content_pack_version,
    enabled_mods,
    migration_history,
    created_at,
    updated_at
FROM save_games
"""


def _metadata_for_state(state: GameState) -> dict[str, str]:
    return {
        "engine_version": CURRENT_ENGINE_VERSION,
        "schema_version": state.schema_version or CURRENT_SAVE_SCHEMA_VERSION,
        "world_id": state.world_id,
        "world_version": "unknown",
        "content_pack_version": "unknown",
        "enabled_mods": "[]",
        "migration_history": "[]",
    }


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
