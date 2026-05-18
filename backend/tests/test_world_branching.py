from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def make_client(tmp_path: Path, authoring_enabled: bool = True) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "branching.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(
        enable_authoring_api=authoring_enabled,
        llm_provider="mock",
        llm_api_key="test-api-key-placeholder",
    )
    return TestClient(app)


def test_create_branch_copies_only_content_files(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    world_path = tmp_path / "worlds" / "mist_valley"
    (world_path / ".env").write_text("OPENAI_API_KEY=sk-real-looking-but-local", encoding="utf-8")
    (world_path / "debug.db").write_text("sqlite", encoding="utf-8")
    (world_path / "cache").mkdir()
    (world_path / "cache" / "tmp.log").write_text("cache", encoding="utf-8")

    response = client.post(
        "/authoring/worlds/mist_valley/branches",
        json={"branch_id": "mist_valley_draft", "name": "Draft"},
    )

    assert response.status_code == 200
    payload = response.json()
    branch_path = tmp_path / "worlds" / ".branches" / "mist_valley" / "mist_valley_draft"
    assert payload["branch"]["branch_id"] == "mist_valley_draft"
    assert (branch_path / "manifest.yaml").exists()
    assert not (branch_path / ".env").exists()
    assert not (branch_path / "debug.db").exists()
    assert not (branch_path / "cache").exists()
    assert "sk-real-looking" not in response.text


def test_list_branches_and_authoring_worlds_ignore_branch_storage(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.post(
        "/authoring/worlds/mist_valley/branches",
        json={"branch_id": "draft_a", "name": "Draft A"},
    )

    branches_response = client.get("/authoring/worlds/mist_valley/branches")
    worlds_response = client.get("/authoring/worlds")

    assert branches_response.status_code == 200
    assert [branch["branch_id"] for branch in branches_response.json()["branches"]] == ["draft_a"]
    assert [world["world_id"] for world in worlds_response.json()["worlds"]] == ["mist_valley"]


def test_diff_detects_added_removed_and_changed_entities(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.post(
        "/authoring/worlds/mist_valley/branches",
        json={"branch_id": "draft_diff", "name": "Diff Draft"},
    )
    branch_items = tmp_path / "worlds" / ".branches" / "mist_valley" / "draft_diff" / "items.yaml"
    content = branch_items.read_text(encoding="utf-8")
    content = content.replace("id: sealed_letter", "id: sealed_letter_branch", 1)
    content = content.replace("Sealed Letter", "Branch Sealed Letter", 1)
    content = content.replace("Weather-stained notices curl under rusted nails.", "Updated branch notices.", 1)
    content += "\n  - id: branch_only_item\n    name: Branch Only\n    description: Draft item.\n    portable: true\n"
    branch_items.write_text(content, encoding="utf-8")

    response = client.get("/authoring/worlds/mist_valley/diff", params={"other": "draft_diff"})

    assert response.status_code == 200
    diff = response.json()["diff"]
    added_ids = {entity["entity_id"] for entity in diff["added_entities"]}
    removed_ids = {entity["entity_id"] for entity in diff["removed_entities"]}
    changed_ids = {entity["entity_id"] for entity in diff["changed_entities"]}
    assert {"sealed_letter_branch", "branch_only_item"} <= added_ids
    assert "sealed_letter" in removed_ids
    assert changed_ids
    assert diff["migration_impacts"]


def test_diff_draft_reports_broken_reference_and_visibility_risk(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    facts = (tmp_path / "worlds" / "mist_valley" / "facts.yaml").read_text(encoding="utf-8")
    rumors = """
rumors:
  - id: unsafe_hidden_rumor
    fact_id: sealed_letter_under_stone
    text_for_player: A sealed letter is hidden beneath a loose paving stone.
    truth_status: unknown
    known_by_player: true
  - id: broken_reference_rumor
    fact_id: fact_does_not_exist
    text_for_player: Something unverified is moving through town.
    truth_status: unknown
    known_by_player: true
"""

    response = client.post(
        "/authoring/worlds/mist_valley/diff-draft",
        json={"proposed_files": {"rumors.yaml": rumors, "facts.yaml": facts}},
    )

    assert response.status_code == 200
    diff = response.json()["diff"]
    assert diff["broken_references"]
    assert diff["visibility_risks"]
    assert "test-api-key-placeholder" not in response.text


def test_branch_operations_do_not_modify_active_game_state(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    start_response = client.post("/game/start", json={"world_id": "mist_valley"})
    before_state = client.get(f"/game/state/{start_response.json()['session_id']}").json()

    branch_response = client.post(
        "/authoring/worlds/mist_valley/branches",
        json={"branch_id": "state_safe_branch", "name": "State Safe"},
    )
    diff_response = client.get("/authoring/worlds/mist_valley/diff", params={"other": "state_safe_branch"})
    after_state = client.get(f"/game/state/{start_response.json()['session_id']}").json()

    assert branch_response.status_code == 200
    assert diff_response.status_code == 200
    assert after_state == before_state


def test_branch_path_traversal_rejected(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/authoring/worlds/mist_valley/branches",
        json={"branch_id": "../escape", "name": "Bad"},
    )

    assert response.status_code == 400
    assert "Invalid branch_id" in response.json()["detail"]
