import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.quality import QualityIssue, QualityIssueSeverity, WorldQualityReport


@pytest.fixture()
def restore_app_settings():
    original_settings = getattr(app.state, "settings", None)
    original_world_health_scores = getattr(app.state, "world_health_scores", None)
    try:
        yield
    finally:
        if original_settings is None:
            if hasattr(app.state, "settings"):
                delattr(app.state, "settings")
        else:
            app.state.settings = original_settings
        app.state.world_health_scores = original_world_health_scores or []


def test_quality_api_endpoints_are_gated_when_local_quality_flags_disabled(restore_app_settings) -> None:
    app.state.settings = Settings(
        enable_debug_api=False,
        enable_eval_api=False,
        enable_playtest_api=False,
        enable_perf_logging=False,
        llm_provider="mock",
    )
    client = TestClient(app)

    requests = [
        ("get", "/quality/worlds/mist_valley/health", None),
        ("post", "/quality/worlds/mist_valley/coverage/run", {}),
        ("post", "/quality/worlds/mist_valley/quests/analyze", {}),
        ("post", "/quality/worlds/mist_valley/dead-ends/analyze", {}),
        ("post", "/quality/worlds/mist_valley/npc-coverage/analyze", {}),
        ("post", "/quality/worlds/mist_valley/schedules/analyze", {}),
        ("post", "/quality/worlds/mist_valley/economy/analyze", {}),
        ("post", "/quality/worlds/mist_valley/combat/analyze", {}),
        ("post", "/quality/worlds/mist_valley/social-consequences/analyze", {}),
        ("post", "/quality/worlds/mist_valley/branch-regression/run", {}),
        ("post", "/quality/mods/compatibility-stress/run", {}),
        ("post", "/quality/worlds/mist_valley/gate/run", {}),
    ]

    for method, path, body in requests:
        response = getattr(client, method)(path, json=body) if body is not None else getattr(client, method)(path)
        assert response.status_code == 403, path


def test_quality_api_normal_payload_strips_debug_only_hidden_details(restore_app_settings) -> None:
    hidden_text = "the sealed-room clue says the mayor is the culprit"
    app.state.settings = Settings(
        enable_debug_api=False,
        enable_eval_api=True,
        enable_playtest_api=False,
        enable_perf_logging=False,
        llm_provider="mock",
    )
    report = WorldQualityReport(
        world_id="mist_valley",
        categories=["visibility"],
        issues=[
            QualityIssue(
                id="visibility:hidden",
                severity=QualityIssueSeverity.ERROR,
                category="visibility",
                message="Hidden detail kept out of normal API payload.",
                safe_details={"safe": "summary"},
                hidden_details_debug_only={"hidden_text": hidden_text},
            )
        ],
        summary={"hidden_details_debug_only": {"hidden_text": hidden_text}},
    )
    app.state.world_health_scores = []
    app.state.world_health_scores.append(report)  # type: ignore[arg-type]
    client = TestClient(app)

    response = client.get("/quality/worlds/mist_valley/health")

    assert response.status_code == 200
    payload = response.json()
    serialized = json.dumps(payload, ensure_ascii=False)
    assert hidden_text not in serialized
    assert "hidden_details_debug_only" not in serialized
    assert "safe" in serialized
