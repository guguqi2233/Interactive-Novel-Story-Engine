import json
from pathlib import Path

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.timeline_replay import replay_dry_run, state_checksum
from app.core.world_state import (
    CURRENT_GAME_STATE_SCHEMA_VERSION,
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    PlayerState,
)
from app.db.migration_service import MigrationService
from app.db.repository import SQLiteSaveRepository
from app.engine.content.import_export import ImportExportService
from app.quality.save_load_stress import run_save_load_migration_stress


def test_100_turn_playtest_style_save_load_is_stable(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "stress.db")
    initial_state = make_state()
    final_state, events = make_stress_events(initial_state, count=120)

    report = run_save_load_migration_stress(
        repository=repository,
        save_id="stress-save",
        initial_state=final_state,
        events=events,
        save_load_cycles=5,
    )

    assert report.turns == 120
    assert report.event_count == 120
    assert report.state_delta_count == 240
    assert _scenario(report, "multiple_save_load_cycles").passed
    assert repository.load_save("stress-save") == final_state
    assert len(repository.list_events("stress-save")) == 120


def test_multiple_save_load_cycles_keep_gamestate_consistent(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "stress.db")
    initial_state = make_state()
    final_state, events = make_stress_events(initial_state, count=25)
    repository.save_snapshot("stress-save", final_state, events)
    expected_checksum = state_checksum(final_state)

    for _ in range(5):
        loaded_state = repository.load_save("stress-save")
        loaded_events = repository.list_events("stress-save")
        repository.save_snapshot("stress-save", loaded_state, loaded_events)

    assert state_checksum(repository.load_save("stress-save")) == expected_checksum
    assert [event.event_id for event in repository.list_events("stress-save")] == [event.event_id for event in events]


def test_migration_dry_run_does_not_write_database(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "stress.db")
    final_state, events = make_stress_events(make_state(), count=5)
    repository.save_snapshot("legacy-save", final_state, events)
    force_legacy_save(repository, "legacy-save", final_state)

    dry_run = MigrationService(repository).dry_run("legacy-save")
    after = repository.get_save("legacy-save")

    assert dry_run.dry_run is True
    assert dry_run.applied_migrations
    assert after.schema_version == "legacy"
    assert after.migration_history == "[]"


def test_migration_apply_preserves_event_log(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "stress.db")
    final_state, events = make_stress_events(make_state(), count=12)
    repository.save_snapshot("legacy-save", final_state, events)
    force_legacy_save(repository, "legacy-save", final_state)

    report = MigrationService(repository).apply("legacy-save")
    save = repository.get_save("legacy-save")
    loaded_events = repository.list_events("legacy-save")

    assert report.success is True
    assert save.schema_version != "legacy"
    assert [event.event_id for event in loaded_events] == [event.event_id for event in events]


def test_import_export_save_bundle_reports_migration_status(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "stress.db")
    final_state, events = make_stress_events(make_state(), count=10)
    repository.save_snapshot("stress-save", final_state, events)
    service = ImportExportService(
        worlds_root=tmp_path / "worlds",
        mods_root=tmp_path / "mods",
        templates_root=tmp_path / "templates",
        repository=repository,
    )

    report = run_save_load_migration_stress(
        repository=repository,
        save_id="stress-save",
        initial_state=final_state,
        events=events,
        save_load_cycles=2,
        import_export_service=service,
        import_overwrite=True,
    )

    assert _scenario(report, "import_export_save_bundle").passed
    assert report.import_dry_run is not None
    assert report.import_dry_run.ok is True
    assert report.import_result is not None
    assert report.import_result.imported is True
    assert report.import_result.migration_needed is False


def test_replay_dry_run_is_deterministic(tmp_path: Path) -> None:
    _ = tmp_path
    initial_state = make_state()
    _, events = make_stress_events(initial_state, count=20)

    first = replay_dry_run(initial_state, events)
    second = replay_dry_run(initial_state, events)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.event_count == 20
    assert not first.invariant_violations


def test_hidden_facts_do_not_leak_to_stress_report_normal_view(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "stress.db")
    hidden_text = "The cellar contains a forbidden witness ledger."
    initial_state = make_state(hidden_text=hidden_text)
    final_state, events = make_stress_events(initial_state, count=3)

    report = run_save_load_migration_stress(
        repository=repository,
        save_id="stress-save",
        initial_state=final_state,
        events=events,
        save_load_cycles=1,
    )

    normal_payload = json.dumps(report.model_dump_normal(), ensure_ascii=False)

    assert hidden_text not in normal_payload
    assert "hidden_details_debug_only" not in normal_payload


def make_state(*, hidden_text: str = "A sealed cache is below the square.") -> GameState:
    return GameState(
        world_id="stress_world",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Square")},
        facts={
            "public_fact": FactState(
                id="public_fact",
                text="The square is public.",
                visibility=FactVisibility.PUBLIC,
                known_by={"player"},
            ),
            "hidden_fact": FactState(
                id="hidden_fact",
                text=hidden_text,
                visibility=FactVisibility.HIDDEN,
                known_by=set(),
            ),
        },
        player_visible_facts={"public_fact"},
    )


def make_stress_events(initial_state: GameState, *, count: int) -> tuple[GameState, list[Event]]:
    state = initial_state.model_copy(deep=True)
    events: list[Event] = []
    for index in range(1, count + 1):
        deltas = [
            StateDelta(
                operation=StateDeltaOperation.INC,
                path="turn",
                value=1,
                reason="Stress turn increment.",
            ),
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"flags.stress_{index}",
                value=True,
                reason="Stress flag set.",
            ),
        ]
        event = Event(
            event_id=f"stress-event-{index:03d}",
            turn=index,
            actor_id="player" if index % 2 else "system",
            action_type="wait" if index % 2 else "world_tick",
            result="success",
            visible_to_player=index % 2 == 1,
            state_deltas=deltas,
        )
        for delta in deltas:
            state = apply_delta(state, delta)
        events.append(event)
    return state, events


def force_legacy_save(repository: SQLiteSaveRepository, save_id: str, state: GameState) -> None:
    payload = state.model_dump(mode="json")
    payload.pop("schema_version", None)
    with repository._connect() as connection:  # noqa: SLF001 - controlled legacy fixture setup
        connection.execute(
            """
            UPDATE save_games
            SET state_json = ?, schema_version = 'legacy', engine_version = 'legacy'
            WHERE save_id = ?
            """,
            (json.dumps(payload), save_id),
        )


def _scenario(report: object, name: str) -> object:
    return next(scenario for scenario in report.scenarios if scenario.name == name)
