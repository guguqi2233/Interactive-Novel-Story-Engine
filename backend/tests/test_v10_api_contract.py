import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


FORBIDDEN_PLAYER_TOKENS = {
    "api_key",
    "llm_api_key",
    "super-secret-test-key",
    "hidden_facts",
    "npc_secrets",
    "hidden_witness",
    "state_deltas",
    "debug_memory",
    "hidden_details_debug_only",
    "raw_state",
    "state_json",
    "sealed_letter_under_stone",
}


@pytest.fixture()
def contract_client(tmp_path: Path):
    original_state: dict[str, Any] = {
        name: getattr(app.state, name, None)
        for name in (
            "settings",
            "session_store",
            "save_repository",
            "worlds_root",
            "narrative_eval_reports",
            "playtest_reports",
            "benchmark_reports",
            "world_health_scores",
            "quality_gate_results",
        )
    }
    original_has = {name: hasattr(app.state, name) for name in original_state}
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v10_api_contract.db")
    app.state.settings = Settings(
        enable_authoring_api=False,
        enable_debug_api=False,
        enable_eval_api=False,
        enable_playtest_api=False,
        enable_perf_logging=False,
        llm_provider="mock",
        llm_api_key="super-secret-test-key",
    )
    for name in ("narrative_eval_reports", "playtest_reports", "benchmark_reports", "world_health_scores", "quality_gate_results"):
        setattr(app.state, name, [])
    try:
        yield TestClient(app)
    finally:
        for name, value in original_state.items():
            if original_has[name]:
                setattr(app.state, name, value)
            elif hasattr(app.state, name):
                delattr(app.state, name)


def assert_no_player_forbidden_tokens(payload: object) -> None:
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    for token in FORBIDDEN_PLAYER_TOKENS:
        assert token.lower() not in serialized


def test_v10_openapi_contains_frozen_core_api_paths(contract_client: TestClient) -> None:
    paths = contract_client.get("/openapi.json").json()["paths"]

    expected_paths = {
        "/health",
        "/studio/status",
        "/studio/config-summary",
        "/game/start",
        "/game/input",
        "/game/state/{session_id}",
        "/game/saves",
        "/game/{session_id}/save",
        "/game/load/{save_id}",
        "/game/saves/{save_id}",
        "/saves/{save_id}/migration-status",
        "/saves/{save_id}/migrate-dry-run",
        "/saves/{save_id}/migrate",
        "/migrations",
        "/authoring/worlds",
        "/authoring/worlds/{world_id}/validate",
        "/authoring/worlds/{world_id}/map",
        "/authoring/worlds/{world_id}/quests/graph",
        "/authoring/templates",
        "/authoring/mods",
        "/debug/sessions/{session_id}/timeline",
        "/debug/performance/summary",
        "/playtests/run",
        "/scenarios/regression/run",
        "/quality/worlds/{world_id}/gate/run",
        "/quality/benchmarks/run",
    }

    missing = expected_paths.difference(paths)
    assert not missing


def test_v10_player_api_response_contract_and_visibility_boundary(contract_client: TestClient) -> None:
    start = contract_client.post("/game/start")
    assert start.status_code == 200
    start_payload = start.json()
    assert set(start_payload) == {"session_id", "world_id", "visible_state", "turn"}
    assert start_payload["world_id"] == "mist_valley"
    assert isinstance(start_payload["turn"], int)
    assert_no_player_forbidden_tokens(start_payload)

    state = contract_client.get(f"/game/state/{start_payload['session_id']}")
    assert state.status_code == 200
    state_payload = state.json()
    assert set(state_payload) == {"session_id", "visible_state", "turn"}
    visible_state = state_payload["visible_state"]
    assert set(visible_state) >= {
        "world_id",
        "turn",
        "time",
        "location",
        "inventory",
        "visible_objects",
        "visible_npcs",
        "known_facts",
        "quests",
        "factions",
        "known_rumors",
        "known_crimes",
        "relationships",
        "faction_conflicts",
    }
    assert_no_player_forbidden_tokens(state_payload)

    save = contract_client.post(f"/game/{start_payload['session_id']}/save")
    saves = contract_client.get("/game/saves")
    assert save.status_code == 200
    assert saves.status_code == 200
    assert set(save.json()) == {"save_id", "session_id", "world_id", "turn"}
    assert set(saves.json()) == {"saves"}
    assert_no_player_forbidden_tokens(save.json())
    assert_no_player_forbidden_tokens(saves.json())


def test_v10_local_tooling_apis_are_gated_when_disabled(contract_client: TestClient) -> None:
    disabled_requests = [
        ("get", "/authoring/worlds", None, "Authoring API is disabled"),
        ("get", "/debug/performance/summary", None, "Debug API is disabled"),
        ("get", "/evals/narrative/recent", None, "Debug API is disabled"),
        ("get", "/playtests/recent", None, "Playtest API is disabled"),
        ("get", "/scenarios/regression", None, "Scenario regression API is disabled"),
        ("post", "/quality/worlds/mist_valley/gate/run", {}, "Quality API is disabled"),
        ("post", "/quality/benchmarks/run", {"world_id": "mist_valley"}, "Benchmark API is disabled"),
    ]

    for method, path, body, detail in disabled_requests:
        response = getattr(contract_client, method)(path, json=body) if body is not None else getattr(contract_client, method)(path)
        assert response.status_code == 403, path
        assert response.json()["detail"] == detail
        assert "super-secret-test-key" not in response.text


def test_v10_studio_safe_summary_contract_does_not_leak_secrets(contract_client: TestClient) -> None:
    status = contract_client.get("/studio/status")
    config = contract_client.get("/studio/config-summary")

    assert status.status_code == 200
    assert config.status_code == 200
    status_payload = status.json()
    config_payload = config.json()
    assert status_payload["local_only"] is True
    assert status_payload["backend_status"] == "ok"
    assert status_payload["authoring_api_enabled"] is False
    assert status_payload["debug_api_enabled"] is False
    assert config_payload["local_only"] is True
    assert config_payload["api_key_configured"] is True
    assert "super-secret-test-key" not in status.text
    assert "super-secret-test-key" not in config.text
    assert "llm_api_key" not in status.text
    assert "llm_api_key" not in config.text


def test_v10_gitignore_covers_local_secrets_and_build_artifacts() -> None:
    ignored_patterns = Path(".gitignore").read_text(encoding="utf-8").splitlines()
    required_patterns = {
        ".env",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        "*.log",
        ".cache/",
        ".pytest_cache/",
        "logs/",
        "node_modules/",
        "frontend/dist/",
        "desktop-dist/",
        "desktop-build/",
        "desktop-release/",
        "electron-dist/",
        "tauri-dist/",
        "src-tauri/target/",
    }

    missing = required_patterns.difference(ignored_patterns)

    assert not missing
