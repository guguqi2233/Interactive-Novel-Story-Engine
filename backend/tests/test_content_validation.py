from pathlib import Path

import pytest

from app.engine.content.validator import ValidationReport, ValidationSeverity, validate_world_pack
from app.tools.validate_world import main as validate_world_main


def write_valid_world(root: Path, world_id: str = "test_world") -> Path:
    world_path = root / world_id
    world_path.mkdir(parents=True)
    (world_path / "manifest.yaml").write_text(
        """
world_id: test_world
name: Test World
version: 0.4.0
start_location_id: square
""".strip(),
        encoding="utf-8",
    )
    (world_path / "locations.yaml").write_text(
        """
locations:
  - id: square
    name: Square
    description: A quiet square.
    exits:
      north: forge
    visible_objects:
      - notice
  - id: forge
    name: Forge
    description: A warm forge.
    exits:
      south: square
""".strip(),
        encoding="utf-8",
    )
    (world_path / "npcs.yaml").write_text(
        """
npcs:
  - id: smith
    name: Smith
    location_id: forge
    faction_id: council
    personality: Practical.
    knowledge:
      - public_fact
    schedule:
      - time_of_day: morning
        location_id: forge
        activity: working
""".strip(),
        encoding="utf-8",
    )
    (world_path / "items.yaml").write_text(
        """
items:
  - id: notice
    name: Notice
    description: A public notice.
    location_id: square
    portable: false
  - id: key
    name: Key
    description: A small iron key.
    owner_id: player
    portable: true
""".strip(),
        encoding="utf-8",
    )
    (world_path / "quests.yaml").write_text(
        """
quests:
  - id: first_quest
    title: First Quest
    description: Ask the smith about the notice.
    initial_stage: ask
    visibility: public
    stages:
      - id: ask
        title: Ask
        description: Speak with the smith.
        objectives:
          - talk_to_smith
        next_stages: []
    triggers:
      - type: npc_talked
        id: smith
        action: complete_objective
        objective_id: talk_to_smith
""".strip(),
        encoding="utf-8",
    )
    (world_path / "facts.yaml").write_text(
        """
facts:
  - id: public_fact
    text: The square is open at dawn.
    visibility: public
    known_by:
      - player
      - smith
    tags:
      - public
  - id: hidden_fact
    text: The key opens the council vault.
    visibility: hidden
    known_by:
      - smith
    tags:
      - secret
""".strip(),
        encoding="utf-8",
    )
    (world_path / "factions.yaml").write_text(
        """
factions:
  - id: council
    name: Council
    description: Local civic leaders.
    default_reputation: 0
    known_by_player: true
    tags:
      - civic
""".strip(),
        encoding="utf-8",
    )
    (world_path / "rumors.yaml").write_text(
        """
rumors:
  - id: notice_rumor
    fact_id: public_fact
    text_for_player: People discuss the public notice.
    truth_status: "true"
    known_by_npcs:
      - smith
    known_by_factions:
      - council
    known_by_player: true
    spread_level: 1
    tags:
      - public
""".strip(),
        encoding="utf-8",
    )
    return world_path


def messages(report: ValidationReport, severity: ValidationSeverity) -> list[str]:
    issues = {
        ValidationSeverity.ERROR: report.errors,
        ValidationSeverity.WARNING: report.warnings,
        ValidationSeverity.SUGGESTION: report.suggestions,
    }[severity]
    return [issue.message for issue in issues]


def test_valid_world_pack_validation_passes(tmp_path: Path) -> None:
    write_valid_world(tmp_path)

    report = validate_world_pack("test_world", worlds_root=tmp_path)

    assert report.ok
    assert report.errors == []


def test_invalid_exit_reports_error(tmp_path: Path) -> None:
    world_path = write_valid_world(tmp_path)
    (world_path / "locations.yaml").write_text(
        (world_path / "locations.yaml").read_text(encoding="utf-8").replace("north: forge", "north: void"),
        encoding="utf-8",
    )

    report = validate_world_pack("test_world", worlds_root=tmp_path)

    assert not report.ok
    assert any("Exit points to missing location: void" in message for message in messages(report, ValidationSeverity.ERROR))


def test_invalid_npc_location_reports_error(tmp_path: Path) -> None:
    world_path = write_valid_world(tmp_path)
    (world_path / "npcs.yaml").write_text(
        (world_path / "npcs.yaml").read_text(encoding="utf-8").replace("location_id: forge", "location_id: nowhere", 1),
        encoding="utf-8",
    )

    report = validate_world_pack("test_world", worlds_root=tmp_path)

    assert any("NPC references missing location: nowhere" in message for message in messages(report, ValidationSeverity.ERROR))


def test_invalid_faction_id_reports_error(tmp_path: Path) -> None:
    world_path = write_valid_world(tmp_path)
    (world_path / "npcs.yaml").write_text(
        (world_path / "npcs.yaml").read_text(encoding="utf-8").replace("faction_id: council", "faction_id: missing_faction"),
        encoding="utf-8",
    )

    report = validate_world_pack("test_world", worlds_root=tmp_path)

    assert any("NPC references missing faction: missing_faction" in message for message in messages(report, ValidationSeverity.ERROR))


def test_missing_quest_trigger_fact_reports_error(tmp_path: Path) -> None:
    world_path = write_valid_world(tmp_path)
    quest_text = (world_path / "quests.yaml").read_text(encoding="utf-8")
    quest_text += """

  - id: fact_quest
    title: Fact Quest
    description: Discover a fact.
    initial_stage: discover
    visibility: hidden
    stages:
      - id: discover
        title: Discover
        description: Find the clue.
        objectives:
          - find_fact
        next_stages: []
    triggers:
      - type: fact_discovered
        id: missing_fact
        action: complete_objective
        objective_id: find_fact
"""
    (world_path / "quests.yaml").write_text(quest_text, encoding="utf-8")

    report = validate_world_pack("test_world", worlds_root=tmp_path)

    assert any("Trigger references missing fact: missing_fact" in message for message in messages(report, ValidationSeverity.ERROR))


def test_hidden_fact_player_known_warning_does_not_fail(tmp_path: Path) -> None:
    world_path = write_valid_world(tmp_path)
    (world_path / "facts.yaml").write_text(
        (world_path / "facts.yaml").read_text(encoding="utf-8").replace(
            "known_by:\n      - smith\n    tags:\n      - secret",
            "known_by:\n      - player\n      - smith\n    tags:\n      - secret",
        ),
        encoding="utf-8",
    )

    report = validate_world_pack("test_world", worlds_root=tmp_path)

    assert report.ok
    assert any("Hidden fact is marked known_by player" in message for message in messages(report, ValidationSeverity.WARNING))


def test_cli_exit_code_is_zero_for_warnings_and_nonzero_for_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    world_path = write_valid_world(tmp_path)
    (world_path / "facts.yaml").write_text(
        (world_path / "facts.yaml").read_text(encoding="utf-8").replace(
            "known_by:\n      - smith\n    tags:\n      - secret",
            "known_by:\n      - player\n      - smith\n    tags:\n      - secret",
        ),
        encoding="utf-8",
    )

    assert validate_world_main(["test_world", "--worlds-root", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert "warnings: 1" in output

    (world_path / "npcs.yaml").write_text(
        (world_path / "npcs.yaml").read_text(encoding="utf-8").replace("faction_id: council", "faction_id: missing"),
        encoding="utf-8",
    )

    assert validate_world_main(["test_world", "--worlds-root", str(tmp_path)]) == 1
