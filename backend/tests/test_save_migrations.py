import json
from pathlib import Path

import pytest

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    CURRENT_GAME_STATE_SCHEMA_VERSION,
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    PlayerState,
    load_game_state_payload,
)
from app.db.migrations import (
    CURRENT_SAVE_SCHEMA_VERSION,
    LEGACY_SCHEMA_VERSION,
    MigrationError,
    MigrationRegistry,
    SaveMigration,
    create_default_registry,
    detect_schema_version,
)
from app.db.migration_service import MigrationService
from app.db.repository import SaveRepositoryError, SQLiteSaveRepository


def make_state() -> GameState:
    return GameState(
        world_id="migration-world",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Town Square")},
        facts={
            "public_fact": FactState(
                id="public_fact",
                text="The square is open.",
                visibility=FactVisibility.PUBLIC,
            ),
            "hidden_fact": FactState(
                id="hidden_fact",
                text="A sealed cache is below the stones.",
                visibility=FactVisibility.HIDDEN,
            ),
        },
        player_visible_facts={"public_fact"},
    )


def make_event() -> Event:
    return Event(
        event_id="event-1",
        turn=1,
        actor_id="player",
        action_type="wait",
        result="success",
        visible_to_player=True,
        state_deltas=[
            StateDelta(
                operation=StateDeltaOperation.INC,
                path="turn",
                value=1,
            )
        ],
        allow_empty_delta=False,
    )


def make_repository(tmp_path: Path, registry: MigrationRegistry | None = None) -> SQLiteSaveRepository:
    return SQLiteSaveRepository(tmp_path / "migration.db", migration_registry=registry)


def legacy_save_data_from_state(state: GameState) -> dict[str, object]:
    payload = state.model_dump(mode="json")
    payload.pop("schema_version", None)
    return {
        "save_id": "save-1",
        "state_json": json.dumps(payload),
        "engine_version": "legacy",
        "schema_version": "legacy",
        "world_id": state.world_id,
        "world_version": "unknown",
        "content_pack_version": "unknown",
        "migration_history": "[]",
    }


def force_legacy_save(repository: SQLiteSaveRepository, save_id: str, state: GameState) -> None:
    repository.create_save(save_id, state)
    payload = state.model_dump(mode="json")
    payload.pop("schema_version", None)
    with repository._connect() as connection:  # noqa: SLF001 - test fixture setup
        connection.execute(
            """
            UPDATE save_games
            SET state_json = ?, schema_version = 'legacy', engine_version = 'legacy'
            WHERE save_id = ?
            """,
            (json.dumps(payload), save_id),
        )


def test_missing_schema_version_is_detected_as_legacy() -> None:
    save_data = legacy_save_data_from_state(make_state())
    save_data.pop("schema_version", None)

    assert detect_schema_version(save_data) == LEGACY_SCHEMA_VERSION


def test_registry_migrates_legacy_save_data_to_current_version() -> None:
    registry = create_default_registry()
    migrated, report = registry.migrate_to_latest("save-1", legacy_save_data_from_state(make_state()))
    state = load_game_state_payload(json.loads(migrated["state_json"]))

    assert report.source_version == LEGACY_SCHEMA_VERSION
    assert report.target_version == CURRENT_SAVE_SCHEMA_VERSION
    assert [entry.migration_id for entry in report.applied_migrations] == ["legacy->0.6"]
    assert migrated["schema_version"] == CURRENT_SAVE_SCHEMA_VERSION
    assert state.schema_version == CURRENT_GAME_STATE_SCHEMA_VERSION


def test_repository_migration_records_history_and_preserves_events(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    force_legacy_save(repository, "save-1", make_state())
    repository.append_event("save-1", make_event())

    report = repository.migrate_save("save-1")
    save = repository.get_save("save-1")
    events = repository.list_events("save-1")

    assert report.success is True
    assert save.schema_version == CURRENT_SAVE_SCHEMA_VERSION
    assert "legacy->0.6" in save.migration_history
    assert [event.event_id for event in events] == ["event-1"]


def test_migration_after_state_is_valid_and_hidden_facts_stay_hidden(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    force_legacy_save(repository, "save-1", make_state())

    repository.migrate_save("save-1")
    migrated_state = repository.load_save("save-1")

    assert migrated_state.schema_version == CURRENT_GAME_STATE_SCHEMA_VERSION
    assert "public_fact" in migrated_state.player_visible_facts
    assert "hidden_fact" not in migrated_state.player_visible_facts
    assert migrated_state.facts["hidden_fact"].visibility == FactVisibility.HIDDEN


def test_dry_run_does_not_write_database(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    force_legacy_save(repository, "save-1", make_state())

    report = repository.migrate_save("save-1", dry_run=True)
    save = repository.get_save("save-1")

    assert report.dry_run is True
    assert report.applied_migrations
    assert save.schema_version == "legacy"
    assert save.migration_history == "[]"


def test_failed_migration_does_not_overwrite_original_save(tmp_path: Path) -> None:
    class BrokenMigration(SaveMigration):
        source_version = LEGACY_SCHEMA_VERSION
        target_version = CURRENT_SAVE_SCHEMA_VERSION
        description = "broken migration"

        def can_migrate(self, save_data: dict[str, object]) -> bool:
            return True

        def migrate(self, save_data: dict[str, object]) -> dict[str, object]:
            raise MigrationError("boom")

    registry = MigrationRegistry()
    registry.register(BrokenMigration())
    repository = make_repository(tmp_path, registry)
    force_legacy_save(repository, "save-1", make_state())
    before = repository.get_save("save-1")

    with pytest.raises(SaveRepositoryError, match="Could not migrate save save-1"):
        repository.migrate_save("save-1")

    after = repository.get_save("save-1")
    assert after.state_json == before.state_json
    assert after.schema_version == "legacy"
    assert after.migration_history == "[]"


def test_current_save_load_still_round_trips(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    state = make_state()

    repository.create_save("save-1", state)
    loaded = repository.load_save("save-1")
    save = repository.get_save("save-1")

    assert loaded == state
    assert save.schema_version == CURRENT_SAVE_SCHEMA_VERSION
    assert save.world_id == state.world_id


def test_save_records_enabled_mod_versions(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    state = make_state()

    save = repository.save_snapshot(
        "save-1",
        state,
        events=[],
        enabled_mods={"mist_mod": "0.1.0"},
    )

    assert json.loads(save.enabled_mods) == [{"id": "mist_mod", "version": "0.1.0"}]


def test_migration_status_warns_on_mod_version_mismatch(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    repository.save_snapshot(
        "save-1",
        make_state(),
        events=[],
        enabled_mods={"mist_mod": "0.1.0"},
    )

    status = MigrationService(repository).status(
        "save-1",
        available_mod_versions={"mist_mod": "0.2.0"},
    )

    assert any("version mismatch" in warning for warning in status.warnings)
