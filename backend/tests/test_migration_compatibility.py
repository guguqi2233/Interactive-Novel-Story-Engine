import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from app.core.event_log import Event
from app.core.world_state import (
    CURRENT_GAME_STATE_SCHEMA_VERSION,
    FactVisibility,
    GameState,
)
from app.db.migrations import CURRENT_SAVE_SCHEMA_VERSION
from app.db.repository import SaveRepositoryError, SQLiteSaveRepository
from app.llm.memory_store import MemoryRecord, MemoryVisibility


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "saves"


def load_fixture_save(file_name: str) -> dict[str, Any]:
    with (FIXTURE_ROOT / file_name).open(encoding="utf-8") as handle:
        return json.load(handle)


def insert_fixture_save(
    repository: SQLiteSaveRepository,
    fixture: dict[str, Any],
) -> None:
    state_json = fixture.get("state_json")
    if state_json is None:
        state_json = json.dumps(fixture["state"], ensure_ascii=False, sort_keys=True)
    migration_history = fixture.get("migration_history", [])
    if not isinstance(migration_history, str):
        migration_history = json.dumps(
            migration_history,
            ensure_ascii=False,
            sort_keys=True,
        )

    with repository._connect() as connection:  # noqa: SLF001 - fixture DB setup
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
                migration_history,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (
                fixture["save_id"],
                state_json,
                fixture.get("engine_version", "legacy"),
                fixture.get("schema_version", "legacy"),
                fixture.get("world_id", "fixture_world"),
                fixture.get("world_version", "unknown"),
                fixture.get("content_pack_version", "unknown"),
                migration_history,
            ),
        )
        for sequence, raw_event in enumerate(fixture.get("events", [])):
            event = Event.model_validate(raw_event)
            connection.execute(
                """
                INSERT INTO stored_events (event_id, save_id, turn, event_json, sequence, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    event.event_id,
                    fixture["save_id"],
                    event.turn,
                    event.model_dump_json(),
                    sequence,
                ),
            )
        for raw_memory in fixture.get("memories", []):
            memory = MemoryRecord.model_validate(raw_memory)
            connection.execute(
                """
                INSERT INTO stored_memories (memory_id, save_id, memory_json, created_turn, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
                """,
                (
                    memory.id,
                    fixture["save_id"],
                    memory.model_dump_json(),
                    memory.created_turn,
                ),
            )
        connection.commit()


def assert_save_migrated(
    repository: SQLiteSaveRepository,
    save_id: str,
) -> GameState:
    save = repository.get_save(save_id)
    state = repository.load_save(save_id)

    assert save.schema_version == CURRENT_SAVE_SCHEMA_VERSION
    assert state.schema_version == CURRENT_GAME_STATE_SCHEMA_VERSION
    assert f"->{CURRENT_SAVE_SCHEMA_VERSION}" in save.migration_history
    return state


def assert_save_latest(
    repository: SQLiteSaveRepository,
    save_id: str,
) -> GameState:
    save = repository.get_save(save_id)
    state = repository.load_save(save_id)

    assert save.schema_version == CURRENT_SAVE_SCHEMA_VERSION
    assert state.schema_version == CURRENT_GAME_STATE_SCHEMA_VERSION
    return state


def assert_no_visibility_leak(state: GameState) -> None:
    for fact_id, fact in state.facts.items():
        if fact.visibility in {FactVisibility.HIDDEN, FactVisibility.DISCOVERABLE}:
            assert fact_id not in state.player_visible_facts


def make_repository(tmp_path: Path) -> SQLiteSaveRepository:
    return SQLiteSaveRepository(tmp_path / "migration_compatibility.db")


@pytest.mark.parametrize(
    ("fixture_name", "expected_migration_id"),
    [
        ("legacy_save.json", "legacy->0.6"),
        ("v03_like_save.json", "0.3->0.6"),
        ("v04_like_save.json", "0.4->0.6"),
        ("v05_like_save.json", "0.5->0.6"),
    ],
)
def test_fixture_save_migrates_to_latest(
    tmp_path: Path,
    fixture_name: str,
    expected_migration_id: str,
) -> None:
    repository = make_repository(tmp_path)
    fixture = load_fixture_save(fixture_name)
    insert_fixture_save(repository, fixture)

    report = repository.migrate_save(fixture["save_id"])
    migrated_state = assert_save_migrated(repository, fixture["save_id"])

    assert report.success is True
    assert [entry.migration_id for entry in report.applied_migrations] == [
        expected_migration_id
    ]
    assert_no_visibility_leak(migrated_state)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "v06_like_save.json",
        "v07_like_save.json",
        "v08_like_save.json",
        "v09_like_save.json",
    ],
)
def test_current_schema_v06_to_v09_like_saves_are_idempotent_latest(
    tmp_path: Path,
    fixture_name: str,
) -> None:
    repository = make_repository(tmp_path)
    fixture = load_fixture_save(fixture_name)
    insert_fixture_save(repository, fixture)
    before = repository.get_save(fixture["save_id"])

    dry_run = repository.migrate_save(fixture["save_id"], dry_run=True)
    after_dry_run = repository.get_save(fixture["save_id"])
    apply_report = repository.migrate_save(fixture["save_id"])
    after_apply = repository.get_save(fixture["save_id"])
    latest_state = assert_save_latest(repository, fixture["save_id"])

    assert dry_run.dry_run is True
    assert dry_run.applied_migrations == []
    assert dry_run.warnings == ["Save already at target schema version."]
    assert after_dry_run.state_json == before.state_json
    assert after_dry_run.migration_history == before.migration_history
    assert apply_report.applied_migrations == []
    assert apply_report.warnings == ["Save already at target schema version."]
    assert after_apply.state_json == before.state_json
    assert after_apply.migration_history == before.migration_history
    assert_no_visibility_leak(latest_state)


def test_migration_apply_is_idempotent_after_legacy_migration(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    fixture = load_fixture_save("legacy_save.json")
    insert_fixture_save(repository, fixture)

    first = repository.migrate_save(fixture["save_id"])
    after_first = repository.get_save(fixture["save_id"])
    second = repository.migrate_save(fixture["save_id"])
    after_second = repository.get_save(fixture["save_id"])

    assert [entry.migration_id for entry in first.applied_migrations] == ["legacy->0.6"]
    assert second.applied_migrations == []
    assert second.warnings == ["Save already at target schema version."]
    assert after_second.state_json == after_first.state_json
    assert after_second.migration_history == after_first.migration_history


def test_migration_preserves_event_log(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    fixture = load_fixture_save("v03_like_save.json")
    insert_fixture_save(repository, fixture)

    repository.migrate_save(fixture["save_id"])

    assert [event.event_id for event in repository.list_events(fixture["save_id"])] == [
        "fixture-v03-event-1"
    ]


def test_migration_history_is_written(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    fixture = load_fixture_save("v04_like_save.json")
    insert_fixture_save(repository, fixture)

    repository.migrate_save(fixture["save_id"])
    save = repository.get_save(fixture["save_id"])
    history = json.loads(save.migration_history)

    assert history[0]["migration_id"] == "0.4->0.6"
    assert history[0]["source_version"] == "0.4"
    assert history[0]["target_version"] == "0.6"


def test_hidden_facts_remain_hidden_after_migration(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    fixture = load_fixture_save("hidden_facts_save.json")
    insert_fixture_save(repository, fixture)

    repository.migrate_save(fixture["save_id"])
    state = repository.load_save(fixture["save_id"])

    assert "public_notice" in state.player_visible_facts
    assert "hidden_cache" not in state.player_visible_facts
    assert "discoverable_mark" not in state.player_visible_facts
    assert state.facts["hidden_cache"].visibility == FactVisibility.HIDDEN
    assert state.facts["discoverable_mark"].visibility == FactVisibility.DISCOVERABLE
    assert_no_visibility_leak(state)


def test_debug_memory_remains_debug_or_hidden_after_migration(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    fixture = load_fixture_save("debug_memory_save.json")
    insert_fixture_save(repository, fixture)

    repository.migrate_save(fixture["save_id"])
    memories = {
        memory.id: memory
        for memory in repository.list_memories(fixture["save_id"])
    }

    assert memories["debug-memory-1"].visibility == MemoryVisibility.DEBUG_ONLY
    assert memories["hidden-memory-1"].visibility == MemoryVisibility.HIDDEN


def test_old_content_pack_version_is_preserved(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    fixture = load_fixture_save("old_content_pack_version_save.json")
    insert_fixture_save(repository, fixture)

    repository.migrate_save(fixture["save_id"])
    save = repository.get_save(fixture["save_id"])

    assert save.content_pack_version == "0.1.0"
    assert_save_migrated(repository, fixture["save_id"])


def test_corrupted_save_fails_safely_without_overwriting_original(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    fixture = load_fixture_save("corrupted_save.json")
    insert_fixture_save(repository, fixture)
    before = repository.get_save(fixture["save_id"])

    with pytest.raises(SaveRepositoryError, match="Could not migrate save fixture-corrupted"):
        repository.migrate_save(fixture["save_id"])

    after = repository.get_save(fixture["save_id"])
    assert after.state_json == before.state_json
    assert after.schema_version == before.schema_version
    assert after.migration_history == before.migration_history


def test_fixture_files_do_not_contain_real_api_keys() -> None:
    for fixture_path in FIXTURE_ROOT.glob("*.json"):
        text = fixture_path.read_text(encoding="utf-8")

        assert "sk-" not in text
        assert "OPENAI_API_KEY" not in text
        assert "LLM_API_KEY" not in text


def test_corrupted_fixture_can_be_inserted_without_uncaught_sql_errors(
    tmp_path: Path,
) -> None:
    repository = make_repository(tmp_path)
    fixture = load_fixture_save("corrupted_save.json")

    try:
        insert_fixture_save(repository, fixture)
    except sqlite3.Error as exc:  # pragma: no cover - documents intended failure mode
        pytest.fail(f"Fixture insert should not raise sqlite errors: {exc}")

    assert repository.get_save(fixture["save_id"]).state_json == "{not valid json"
