from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.quality.content_coverage import ContentCoverageReport, ContentCoverageSummary
from app.quality.content_coverage_planner import ContentCoveragePlanRequest, build_content_coverage_plan
from app.quality.reports import WorldQualityReport


def _summary(
    *,
    total: int,
    covered: int,
    uncovered_ids: list[str] | None = None,
) -> ContentCoverageSummary:
    uncovered_ids = uncovered_ids or []
    uncovered = max(total - covered, 0)
    return ContentCoverageSummary(
        total=total,
        covered=covered,
        uncovered=uncovered,
        coverage_percent=round((covered / total) * 100, 2) if total else 0,
        covered_ids=[f"covered_{index}" for index in range(covered)],
        uncovered_ids=uncovered_ids,
        safe_summary=f"{covered}/{total} covered",
    )


def _report(**overrides: ContentCoverageSummary | dict[str, int]) -> ContentCoverageReport:
    values: dict[str, ContentCoverageSummary | dict[str, int] | WorldQualityReport | str] = {
        "world_id": "planner_world",
        "locations": _summary(total=4, covered=4),
        "npcs": _summary(total=4, covered=4),
        "items": _summary(total=2, covered=2),
        "quests": _summary(total=3, covered=3),
        "facts": _summary(total=4, covered=4),
        "factions": _summary(total=1, covered=1),
        "rumors": _summary(total=1, covered=1),
        "crimes": _summary(total=1, covered=1),
        "combat_encounters": _summary(total=1, covered=1),
        "shops_trade": _summary(total=1, covered=1),
        "hidden_entities_redacted": {},
        "quality_report": WorldQualityReport(world_id="planner_world"),
    }
    values.update(overrides)
    return ContentCoverageReport(**values)  # type: ignore[arg-type]


def test_low_npc_coverage_produces_npc_suggestion() -> None:
    report = _report(npcs=_summary(total=5, covered=1, uncovered_ids=["merchant", "witness"]))

    plan = build_content_coverage_plan(
        ContentCoveragePlanRequest(
            target_world="planner_world",
            current_content_coverage_report=report,
        )
    )

    assert plan.missing_npc_archetypes
    assert plan.missing_npc_archetypes[0].recommended_tool == "npc_pack_generator"


def test_missing_quest_coverage_produces_quest_suggestion() -> None:
    report = _report(quests=_summary(total=4, covered=1, uncovered_ids=["starter_quest"]))

    plan = build_content_coverage_plan(
        ContentCoveragePlanRequest(
            target_world="planner_world",
            current_content_coverage_report=report,
        )
    )

    assert plan.missing_quest_types
    assert plan.missing_quest_types[0].recommended_tool == "quest_pack_generator"


def test_missing_hidden_leak_scenarios_produces_eval_suggestion() -> None:
    report = _report(hidden_entities_redacted={"facts": 2})

    plan = build_content_coverage_plan(
        ContentCoveragePlanRequest(
            target_world="planner_world",
            current_content_coverage_report=report,
        )
    )

    assert plan.missing_scenario_regressions
    assert "hidden leak" in plan.missing_scenario_regressions[0].summary


def test_hidden_details_do_not_enter_normal_report() -> None:
    report = _report(
        npcs=_summary(total=4, covered=1, uncovered_ids=["secret_informant", "hidden_traitor"]),
        hidden_entities_redacted={"facts": 1},
    )

    plan = build_content_coverage_plan(
        ContentCoveragePlanRequest(
            target_world="planner_world",
            current_content_coverage_report=report,
        )
    )

    payload = plan.model_dump_json()
    assert "secret_informant" not in payload
    assert "hidden_traitor" not in payload
    assert "[redacted]" in payload


def test_content_coverage_plan_api_returns_plan() -> None:
    previous_settings = getattr(app.state, "settings", None)
    previous_worlds_root = getattr(app.state, "worlds_root", None)
    app.state.settings = Settings(enable_authoring_api=True, enable_quality_api=True, llm_provider="mock")
    app.state.worlds_root = Path("worlds")
    try:
        response = TestClient(app).post(
            "/production/content-coverage-plan",
            json={"target_world": "mist_valley", "genre": "mystery", "desired_complexity": "medium"},
        )
    finally:
        if previous_settings is None:
            app.state._state.pop("settings", None)
        else:
            app.state.settings = previous_settings
        if previous_worlds_root is None:
            app.state._state.pop("worlds_root", None)
        else:
            app.state.worlds_root = previous_worlds_root

    assert response.status_code == 200
    payload = response.json()
    assert payload["world_id"] == "mist_valley"
    assert payload["normal_report"] is True
