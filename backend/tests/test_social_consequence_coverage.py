import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.main import app
from app.playtesting.runner import PlaytestActionRecord, PlaytestFinalStateSummary, PlaytestReport
from app.quality import QualityIssueSeverity
from app.quality.social_consequence_coverage import analyze_social_consequence_coverage


def test_missing_faction_effect_is_error(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        rumors_yaml="""
rumors:
  - id: missing_faction_rumor
    fact_id: public_fact
    text_for_player: A public rumor.
    known_by_factions: [missing_faction]
    tags: [crime]
""",
    )

    report = analyze_social_consequence_coverage("test_world", worlds_root=tmp_path)

    assert report.missing_faction_effect_issues
    assert report.missing_faction_effect_issues[0].severity == QualityIssueSeverity.ERROR
    assert report.missing_faction_effect_issues[0].safe_details["faction_id"] == "missing_faction"


def test_rumor_hidden_fact_leakage_is_reported_without_normal_text_leak(tmp_path: Path) -> None:
    hidden_text = "The mayor hid the ledger below the old well."
    write_world(
        tmp_path,
        facts_yaml=f"""
facts:
  - id: hidden_ledger
    text: {hidden_text}
    visibility: hidden
    known_by: [harlan]
""",
        rumors_yaml=f"""
rumors:
  - id: leaking_rumor
    fact_id: hidden_ledger
    text_for_player: {hidden_text}
    known_by_npcs: [harlan]
    tags: [crime]
""",
    )

    report = analyze_social_consequence_coverage("test_world", worlds_root=tmp_path)
    normal_payload = json.dumps(report.model_dump_normal(), ensure_ascii=False)
    debug_payload = json.dumps(report.model_dump(mode="json"), ensure_ascii=False)

    assert report.hidden_fact_leakage_risks
    assert report.hidden_fact_leakage_risks[0].severity == QualityIssueSeverity.WARNING
    assert hidden_text not in normal_payload
    assert hidden_text in debug_payload


def test_untriggerable_consequence_is_warning(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        rumors_yaml="""
rumors:
  - id: orphan_rumor
    fact_id: public_fact
    text_for_player: Nobody can start this rumor.
    known_by_npcs: []
    known_by_factions: []
    known_by_player: false
    tags: [crime]
""",
    )

    report = analyze_social_consequence_coverage("test_world", worlds_root=tmp_path)

    assert report.untriggerable_consequence_issues
    assert report.untriggerable_consequence_issues[0].severity == QualityIssueSeverity.WARNING
    assert report.orphan_consequence_rules == 1


def test_duplicate_consequence_risk_is_warning(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        rumors_yaml="""
rumors:
  - id: duplicate_rumor
    fact_id: public_fact
    text_for_player: Same rumor.
    known_by_npcs: [harlan]
    tags: [crime]
  - id: duplicate_rumor
    fact_id: public_fact
    text_for_player: Same rumor.
    known_by_npcs: [harlan]
    tags: [crime]
""",
    )

    report = analyze_social_consequence_coverage("test_world", worlds_root=tmp_path)

    assert report.duplicate_consequence_risks
    assert report.duplicate_consequence_risks[0].severity == QualityIssueSeverity.WARNING


def test_playtest_triggered_rumor_updates_coverage_metric(tmp_path: Path) -> None:
    write_world(tmp_path)
    playtest_report = PlaytestReport(
        strategy="crime_social_path",
        world_id="test_world",
        seed=123,
        turns_run=1,
        actions_taken=[
            PlaytestActionRecord(
                step=0,
                turn_before=0,
                turn_after=1,
                input_text="wait",
                action_type="rumor_spread",
                result="success",
                event_id="event_rumor",
            )
        ],
        final_state_summary=PlaytestFinalStateSummary(
            world_id="test_world",
            turn=1,
            location_id="square",
            event_count=1,
        ),
    )
    event = Event(
        event_id="event_rumor_delta",
        turn=1,
        actor_id="system",
        action_type="rumor_spread",
        result="success",
        visible_to_player=False,
        state_deltas=[
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path="rumors.public_rumor.known_by_npcs",
                value="mira",
                metadata={"source": "rumor_propagation", "rumor_id": "public_rumor"},
            )
        ],
    )

    report = analyze_social_consequence_coverage(
        "test_world",
        worlds_root=tmp_path,
        events=[event],
        playtest_reports=[playtest_report],
    )

    assert report.rumors_propagated >= 2
    assert any(metric.name == "rumors_propagated" and metric.value >= 2 for metric in report.quality_report.metrics)


def test_social_consequence_coverage_api(tmp_path: Path) -> None:
    write_world(
        tmp_path,
        rumors_yaml="""
rumors:
  - id: missing_faction_rumor
    fact_id: public_fact
    text_for_player: A public rumor.
    known_by_factions: [missing_faction]
    tags: [crime]
""",
    )
    previous_worlds_root = getattr(app.state, "worlds_root", None)
    app.state.worlds_root = tmp_path
    client = TestClient(app)
    try:
        response = client.post("/quality/worlds/test_world/social-consequences/analyze", json={})
    finally:
        app.state.worlds_root = previous_worlds_root or "worlds"

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_id"] == "test_world"
    assert payload["missing_faction_effect_issues"][0]["severity"] == "error"


def write_world(
    root: Path,
    *,
    facts_yaml: str | None = None,
    factions_yaml: str | None = None,
    rumors_yaml: str | None = None,
) -> None:
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
    (world / "items.yaml").write_text("items: []\n", encoding="utf-8")
    (world / "npcs.yaml").write_text(
        """
npcs:
  - id: harlan
    name: Harlan
    location_id: square
    faction_id: village_council
    personality: Watchful.
""",
        encoding="utf-8",
    )
    (world / "quests.yaml").write_text("quests: []\n", encoding="utf-8")
    (world / "facts.yaml").write_text(
        facts_yaml
        or """
facts:
  - id: public_fact
    text: The square is public.
    visibility: public
    known_by: [player]
""",
        encoding="utf-8",
    )
    (world / "factions.yaml").write_text(
        factions_yaml
        or """
factions:
  - id: village_council
    name: Village Council
    known_by_player: true
""",
        encoding="utf-8",
    )
    (world / "rumors.yaml").write_text(
        rumors_yaml
        or """
rumors:
  - id: public_rumor
    fact_id: public_fact
    text_for_player: A harmless rumor.
    known_by_npcs: [harlan]
    known_by_factions: [village_council]
    tags: [crime]
""",
        encoding="utf-8",
    )
    (world / "relationships.yaml").write_text("relationships: []\n", encoding="utf-8")
