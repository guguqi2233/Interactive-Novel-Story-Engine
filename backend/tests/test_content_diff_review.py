from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def _client(tmp_path: Path) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "diff_review.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def test_diff_review_detects_added_removed_changed_entities(tmp_path: Path) -> None:
    client = _client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/items.yaml").json()["content"]
    proposed = original.replace("id: iron_nails", "id: iron_nails_removed", 1)
    proposed = proposed.replace("Sealed Letter", "Changed Letter", 1)
    proposed += "\n  - id: diff_review_item\n    name: Diff Review Item\n    description: New.\n    location_id: village_square\n    portable: true\n"

    response = client.post(
        "/authoring/diff/review",
        json={
            "base": {"world_id": "mist_valley"},
            "proposed": {"world_id": "mist_valley", "files": {"items.yaml": proposed}},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert any(item["entity_id"] == "diff_review_item" for item in payload["added"])
    assert any(item["entity_id"] == "iron_nails" for item in payload["removed"])
    assert any(item["entity_id"] == "sealed_letter" for item in payload["changed"])


def test_diff_review_detects_visibility_risk(tmp_path: Path) -> None:
    client = _client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/facts.yaml").json()["content"]
    proposed = original.replace("visibility: public", "visibility: hidden", 1)

    response = client.post(
        "/authoring/diff/review",
        json={
            "base": {"world_id": "mist_valley"},
            "proposed": {"world_id": "mist_valley", "files": {"facts.yaml": proposed}},
        },
    )

    assert response.status_code == 200
    assert response.json()["visibility_risk"]


def test_diff_review_normal_view_redacts_hidden_details(tmp_path: Path) -> None:
    client = _client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/facts.yaml").json()["content"]
    proposed = original.replace("A sealed letter is hidden beneath a loose paving stone.", "A hidden murder weapon is beneath the shrine.")

    response = client.post(
        "/authoring/diff/review",
        json={
            "base": {"world_id": "mist_valley"},
            "proposed": {"world_id": "mist_valley", "files": {"facts.yaml": proposed}},
            "normal_view": True,
        },
    )

    assert response.status_code == 200
    text = response.text
    assert "hidden murder weapon" not in text
    assert "details redacted" in text
    assert all(":" in issue and "hidden murder weapon" not in issue for issue in response.json()["validation_issues"])


def test_diff_review_rejects_path_traversal(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post(
        "/authoring/diff/review",
        json={
            "base": {"world_id": "mist_valley"},
            "proposed": {"world_id": "mist_valley", "files": {"../facts.yaml": "facts: []"}},
        },
    )

    assert response.status_code == 400
    assert "authoring-allowed" in response.json()["detail"]
