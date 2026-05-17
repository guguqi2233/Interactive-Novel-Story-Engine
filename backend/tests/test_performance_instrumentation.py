from pathlib import Path
from random import Random

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.core.instrumentation import get_performance_recorder, set_performance_logging_enabled
from app.db.repository import SQLiteSaveRepository
from app.engine.action_dispatcher import ActionDispatcher
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.main import app
from app.session_store import InMemorySessionStore, create_initial_state


@pytest.fixture(autouse=True)
def reset_perf_recorder() -> None:
    recorder = get_performance_recorder()
    recorder.clear()
    set_performance_logging_enabled(False)
    yield
    recorder.clear()
    set_performance_logging_enabled(False)


def _make_loop() -> GameLoop:
    provider = FakeLLMProvider(
        json_responses=[
            {
                "action_type": "observe",
                "raw_text": "observe",
                "confidence": 1.0,
                "requires_clarification": False,
            },
            {
                "text": "你看清了周围。",
                "suggested_actions": ["observe"],
                "short_summary": "Observed.",
            },
        ]
    )
    return GameLoop(
        state=create_initial_state(world_id="mist_valley"),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(1),
    )


def test_perf_logging_disabled_has_no_side_effect() -> None:
    set_performance_logging_enabled(False)

    _make_loop().step("observe")

    assert get_performance_recorder().recent() == []


def test_perf_logging_enabled_records_game_loop_sample() -> None:
    set_performance_logging_enabled(True)

    _make_loop().step("observe")

    samples = get_performance_recorder().recent()
    assert len(samples) == 1
    sample = samples[0]
    assert sample.name == "game_loop.step"
    assert sample.duration_ms >= 0
    assert set(sample.stage_durations_ms) >= {
        "intent_parse",
        "action_resolve",
        "apply_delta",
        "world_tick",
        "narrator",
    }


def _make_client(tmp_path: Path, *, debug_enabled: bool, perf_enabled: bool) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "perf.db")
    app.state.settings = Settings(
        enable_debug_api=debug_enabled,
        enable_perf_logging=perf_enabled,
        llm_provider="mock",
        llm_api_key="super-secret-test-key",
    )
    return TestClient(app)


def test_debug_performance_api_disabled_returns_forbidden(tmp_path: Path) -> None:
    client = _make_client(tmp_path, debug_enabled=False, perf_enabled=True)

    response = client.get("/debug/performance/recent")

    assert response.status_code == 403


def test_debug_performance_api_enabled_returns_summary(tmp_path: Path) -> None:
    client = _make_client(tmp_path, debug_enabled=True, perf_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]
    client.post("/game/input", json={"session_id": session_id, "player_input": "search"})

    response = client.get("/debug/performance/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    assert payload["enabled"] is True
    assert payload["sample_count"] >= 1
    assert any(entry["name"] == "game_loop.step" for entry in payload["entries"])


def test_performance_api_does_not_return_api_key(tmp_path: Path) -> None:
    client = _make_client(tmp_path, debug_enabled=True, perf_enabled=True)
    session_id = client.post("/game/start").json()["session_id"]
    client.post("/game/input", json={"session_id": session_id, "player_input": "search"})

    payload = client.get("/debug/performance/recent").text

    assert "super-secret-test-key" not in payload
    assert "llm_api_key" not in payload
    assert "sk-" not in payload
    assert "state_deltas" not in payload
