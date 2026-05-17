import json
from pathlib import Path

import pytest

from app.core.world_state import GameState, LocationState, PlayerState
from app.db.repository import SQLiteSaveRepository
from app.tools.migrate_save import main


def make_state() -> GameState:
    return GameState(
        world_id="cli-world",
        player=PlayerState(location_id="start"),
        locations={"start": LocationState(id="start", name="Start")},
    )


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


def test_cli_list_outputs_available_migrations(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "legacy->0.6" in output


def test_cli_dry_run_outputs_report_without_writing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "cli.db"
    repository = SQLiteSaveRepository(db_path)
    force_legacy_save(repository, "save-1", make_state())

    exit_code = main(
        [
            "--database-url",
            str(db_path),
            "--save-id",
            "save-1",
            "--dry-run",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "current version: legacy" in output
    assert "target version: 0.6" in output
    assert "dry run: True" in output
    assert repository.get_save("save-1").schema_version == "legacy"


def test_cli_apply_migrates_save(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path = tmp_path / "cli.db"
    repository = SQLiteSaveRepository(db_path)
    force_legacy_save(repository, "save-1", make_state())

    exit_code = main(
        [
            "--database-url",
            str(db_path),
            "--save-id",
            "save-1",
            "--apply",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "backup save id: save-1.backup" in output
    assert repository.get_save("save-1").schema_version == "0.6"
