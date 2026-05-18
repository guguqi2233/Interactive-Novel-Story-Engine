import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.session_store import create_initial_state


def make_client(tmp_path: Path, *, enabled: bool = True) -> TestClient:
    app.state.settings = Settings(
        enable_authoring_api=enabled,
        llm_provider="mock",
        llm_api_key="sk-test-fake-not-real",
    )
    app.state.scenarios_root = tmp_path / "scenarios"
    return TestClient(app)


def valid_scenario_payload() -> dict[str, object]:
    return {
        "id": "mist_valley_opening_authoring",
        "world_id": "mist_valley",
        "name": "Opening authoring smoke",
        "description": "Authoring scenario smoke test.",
        "input_sequence": ["observe"],
        "expected_visible_facts": ["village_square_is_misty"],
        "forbidden_visible_facts": ["sealed_letter_under_stone"],
        "expected_quest_states": {},
        "expected_inventory": [],
        "max_turns": 3,
        "tags": ["authoring", "visibility"],
    }


def test_scenario_authoring_api_disabled(tmp_path: Path) -> None:
    client = make_client(tmp_path, enabled=False)

    response = client.get("/authoring/scenarios")

    assert response.status_code == 403
    assert response.json()["detail"] == "Authoring API is disabled"


def test_valid_scenario_can_be_saved_and_listed(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    scenario = valid_scenario_payload()

    saved = client.put(f"/authoring/scenarios/{scenario['id']}", json={"scenario": scenario})
    listed = client.get("/authoring/scenarios")
    loaded = client.get(f"/authoring/scenarios/{scenario['id']}")

    assert saved.status_code == 200, saved.text
    assert saved.json()["validation"]["ok"] is True
    assert saved.json()["writes_to_disk"] is True
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["scenarios"]] == [scenario["id"]]
    assert loaded.status_code == 200
    assert loaded.json()["scenario"]["forbidden_visible_facts"] == ["sealed_letter_under_stone"]


def test_invalid_scenario_is_caught_before_save(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    scenario = valid_scenario_payload()
    scenario["expected_visible_facts"] = ["missing_fact"]

    response = client.put(f"/authoring/scenarios/{scenario['id']}", json={"scenario": scenario})

    assert response.status_code == 200
    payload = response.json()
    assert payload["writes_to_disk"] is False
    assert payload["validation"]["ok"] is False
    assert payload["validation"]["errors"][0]["code"] == "scenario_unknown_fact"
    assert not (tmp_path / "scenarios" / f"{scenario['id']}.json").exists()


def test_scenario_preview_does_not_write_disk(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    scenario = valid_scenario_payload()

    response = client.post("/authoring/scenarios/preview", json={"scenario": scenario})

    assert response.status_code == 200
    assert response.json()["writes_to_disk"] is False
    assert not (tmp_path / "scenarios").exists()


def test_scenario_authoring_path_traversal_rejected(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    scenario = valid_scenario_payload()
    scenario["id"] = "../escape"

    response = client.put("/authoring/scenarios/..%2Fescape", json={"scenario": scenario})

    assert response.status_code in {400, 404}
    assert not (tmp_path / "escape.json").exists()


def test_scenario_authoring_does_not_modify_active_game_state(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    state = create_initial_state(world_id="mist_valley")
    before = state.model_dump(mode="json")

    response = client.post("/authoring/scenarios/preview", json={"scenario": valid_scenario_payload()})

    assert response.status_code == 200
    assert state.model_dump(mode="json") == before


def test_scenario_authoring_response_does_not_leak_secret_text(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post("/authoring/scenarios/preview", json={"scenario": valid_scenario_payload()})
    serialized = json.dumps(response.json(), ensure_ascii=False)

    assert response.status_code == 200
    assert "A sealed letter is hidden beneath a loose paving stone." not in serialized
    assert "sk-test-fake-not-real" not in serialized
