import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.quality import QualityIssueSeverity
from app.quality.quest_analysis import QuestCompletionCoverage, analyze_quest_completion


def test_valid_quest_graph_has_no_blocker() -> None:
    analysis = analyze_quest_completion("mist_valley")

    assert analysis.total_quests == 2
    assert analysis.hidden_quests == 1
    assert not any(issue.severity == QualityIssueSeverity.BLOCKER for issue in analysis.quality_report.issues)
    assert not analysis.missing_next_stage_refs
    assert analysis.quality_report.summary["total_quests"] == 2


def test_missing_next_stage_is_caught(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        """
quests:
  - id: broken
    title: Broken
    description: Broken path.
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: []
        next_stages: [missing]
    triggers: []
""",
    )

    analysis = analyze_quest_completion("test_world", worlds_root=tmp_path)

    assert analysis.missing_next_stage_refs[0].ref_id == "missing"
    assert any(issue.category == "quest_missing_next_stage" for issue in analysis.quality_report.issues)


def test_unreachable_stage_is_warning(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        """
quests:
  - id: unreachable
    title: Unreachable
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: []
        next_stages: []
      - id: orphan
        title: Orphan
        objectives: []
        next_stages: []
    triggers: []
""",
    )

    analysis = analyze_quest_completion("test_world", worlds_root=tmp_path)

    assert analysis.unreachable_stages[0].stage_id == "orphan"
    assert analysis.unreachable_stages[0].severity == QualityIssueSeverity.WARNING


def test_objective_without_completion_path_is_reported(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        """
quests:
  - id: objective_gap
    title: Objective Gap
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [find_key]
        next_stages: []
    triggers: []
""",
    )

    analysis = analyze_quest_completion("test_world", worlds_root=tmp_path)

    assert analysis.objectives_without_completion_path[0].objective_id == "find_key"
    assert any("completion trigger" in issue.message for issue in analysis.quality_report.issues)


def test_circular_path_is_warning(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        """
quests:
  - id: loop
    title: Loop
    initial_stage: a
    visibility: public
    stages:
      - id: a
        title: A
        objectives: []
        next_stages: [b]
      - id: b
        title: B
        objectives: []
        next_stages: [a]
    triggers: []
""",
    )

    analysis = analyze_quest_completion("test_world", worlds_root=tmp_path)

    assert analysis.circular_paths[0].quest_id == "loop"
    assert analysis.circular_paths[0].severity == QualityIssueSeverity.WARNING


def test_hidden_quest_normal_report_does_not_leak_text(tmp_path: Path) -> None:
    hidden_title = "The Hidden Monarch Letter"
    write_world(
        tmp_path,
        f"""
quests:
  - id: hidden_q
    title: {hidden_title}
    description: Secret description text.
    initial_stage: start
    visibility: hidden
    stages:
      - id: start
        title: Hidden Start
        objectives: [secret_objective]
        next_stages: []
    triggers: []
""",
    )

    analysis = analyze_quest_completion("test_world", worlds_root=tmp_path)
    normal_payload = json.dumps(analysis.model_dump_normal(), ensure_ascii=False)

    assert hidden_title not in normal_payload
    assert "Secret description text" not in normal_payload
    assert "hidden_q" in normal_payload


def test_scenario_coverage_marks_completed_path() -> None:
    analysis = analyze_quest_completion(
        "mist_valley",
        coverage=QuestCompletionCoverage(completed_quest_ids=["missing_tools"]),
    )

    assert analysis.scenario_covered_completed_quests == ["missing_tools"]
    assert any(metric.name == "scenario_covered_completed_quests" and metric.value == 1 for metric in analysis.quality_report.metrics)


def test_quest_completion_analysis_api(tmp_path: Path) -> None:
    app.state.worlds_root = "worlds"
    client = TestClient(app)

    response = client.post(
        "/quality/worlds/mist_valley/quests/analyze",
        json={"coverage": {"completed_quest_ids": ["missing_tools"]}},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_id"] == "mist_valley"
    assert payload["scenario_covered_completed_quests"] == ["missing_tools"]
    serialized = json.dumps(payload, ensure_ascii=False)
    assert "A hidden letter may explain" not in serialized


def write_world(root: Path, quests_yaml: str) -> None:
    world = root / "test_world"
    world.mkdir()
    (world / "manifest.yaml").write_text(
        """
world_id: test_world
name: Test World
version: "1.0"
start_location_id: square
""",
        encoding="utf-8",
    )
    (world / "locations.yaml").write_text(
        """
locations:
  - id: square
    name: Square
    description: Start.
    exits: {}
""",
        encoding="utf-8",
    )
    (world / "npcs.yaml").write_text("npcs: []\n", encoding="utf-8")
    (world / "items.yaml").write_text("items: []\n", encoding="utf-8")
    (world / "facts.yaml").write_text("facts: []\n", encoding="utf-8")
    (world / "factions.yaml").write_text("factions: []\n", encoding="utf-8")
    (world / "rumors.yaml").write_text("rumors: []\n", encoding="utf-8")
    (world / "relationships.yaml").write_text("relationships: []\n", encoding="utf-8")
    (world / "quests.yaml").write_text(quests_yaml, encoding="utf-8")
