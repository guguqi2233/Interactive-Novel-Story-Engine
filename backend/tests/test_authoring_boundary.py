from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_boundary import (
    AuthoringBoundaryCheckRequest,
    AuthoringOperation,
    AuthoringSaveDecision,
    check_authoring_boundary,
    default_authoring_boundary_policy,
)
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.main import app
from app.session_store import InMemorySessionStore


def make_client(tmp_path: Path, authoring_enabled: bool = True) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore(worlds_root=str(worlds_root))
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "authoring_boundary.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(
        enable_authoring_api=authoring_enabled,
        llm_provider="mock",
        llm_api_key="sk-test-fake-not-real",
    )
    return TestClient(app)


def test_authoring_boundary_policy_blocks_active_game_state_apply() -> None:
    policy = default_authoring_boundary_policy()
    report = ValidationReport(world_id="mist_valley")

    decision = policy.decide_save(report, apply_to_active_session=True)

    assert decision == AuthoringSaveDecision.BLOCK_ACTIVE_GAME_STATE_APPLY
    assert policy.draft_modifies_active_game_state is False
    assert policy.preview_writes_disk is False
    assert policy.validate_writes_disk is False
    assert policy.apply_to_active_session_allowed is False


def test_authoring_boundary_check_marks_preview_read_only() -> None:
    result = check_authoring_boundary(
        AuthoringBoundaryCheckRequest(operation=AuthoringOperation.PREVIEW)
    )

    assert result.writes_disk is False
    assert result.modifies_active_game_state is False
    assert result.decision == AuthoringSaveDecision.ALLOW


def test_authoring_boundary_check_requires_warning_confirmation() -> None:
    result = check_authoring_boundary(
        AuthoringBoundaryCheckRequest(
            operation=AuthoringOperation.SAVE,
            validation_warning_count=1,
        )
    )

    assert result.requires_warning_confirmation is True
    assert result.decision == AuthoringSaveDecision.REQUIRE_WARNING_CONFIRMATION


def test_authoring_boundary_api_reports_default_contract(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/authoring/pro/boundary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    assert payload["draft_modifies_active_game_state"] is False
    assert payload["preview_writes_disk"] is False
    assert payload["validate_writes_disk"] is False
    assert payload["save_writes_content_pack_only"] is True
    assert payload["apply_to_active_session_allowed"] is False
    assert payload["hidden_authoring_fields_player_visible"] is False


def test_preview_does_not_write_disk(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/facts.yaml").json()["content"]
    proposed = original + """
  - id: boundary_preview_fact
    text: Preview-only boundary fact.
    visibility: public
    known_by:
      - player
    tags: []
"""

    response = client.post(
        "/authoring/worlds/mist_valley/preview-file-change",
        json={"file_name": "facts.yaml", "proposed_content": proposed},
    )
    after = client.get("/authoring/worlds/mist_valley/files/facts.yaml").json()["content"]

    assert response.status_code == 200
    assert "boundary_preview_fact" in response.text
    assert after == original


def test_validate_does_not_write_disk(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/facts.yaml").json()["content"]
    proposed = original + """
  - id: boundary_validate_fact
    text: Validate-only boundary fact.
    visibility: public
    known_by:
      - player
    tags: []
"""

    response = client.post(
        "/authoring/worlds/mist_valley/validate-draft",
        json={"file_name": "facts.yaml", "proposed_content": proposed},
    )
    after = client.get("/authoring/worlds/mist_valley/files/facts.yaml").json()["content"]

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert after == original


def test_save_requires_validation_before_write(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]
    invalid = """locations:
  - id: village_square
    name: Broken Square
    description: Broken exit.
    exits:
      nowhere: missing_location
"""

    response = client.put(
        "/authoring/worlds/mist_valley/files/locations.yaml",
        json={"content": invalid},
    )
    after = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]

    assert response.status_code == 400
    assert response.json()["detail"]["ok"] is False
    assert after == original


def test_save_with_warnings_requires_confirmation_without_writing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    service = ContentAuthoringService(worlds_root)
    original = service.read_file("mist_valley", "facts.yaml")
    proposed = original + """
  - id: warning_requires_confirmation
    text: Warning confirmation fact.
    visibility: public
    known_by:
      - player
    tags: []
"""
    warning_report = ValidationReport(world_id="mist_valley")
    warning_report.add(
        ValidationSeverity.WARNING,
        "facts.yaml",
        "Synthetic warning for confirmation test.",
        code="synthetic_warning",
    )

    monkeypatch.setattr(service, "validate_draft", lambda *_args, **_kwargs: warning_report)

    report = service.write_file("mist_valley", "facts.yaml", proposed)
    after = service.read_file("mist_valley", "facts.yaml")

    assert report.ok is True
    assert report.warnings
    assert after == original


def test_authoring_draft_does_not_modify_active_game_state(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    start_response = client.post("/game/start", json={"world_id": "mist_valley"})
    session_id = start_response.json()["session_id"]
    original_state = client.get(f"/game/state/{session_id}").json()["visible_state"]
    original = client.get("/authoring/worlds/mist_valley/files/locations.yaml").json()["content"]
    proposed = original.replace("Village Square", "Boundary Draft Square")

    response = client.post(
        "/authoring/worlds/mist_valley/preview-file-change",
        json={"file_name": "locations.yaml", "proposed_content": proposed},
    )
    after_state = client.get(f"/game/state/{session_id}").json()["visible_state"]

    assert response.status_code == 200
    assert after_state == original_state


def test_hidden_authoring_fields_do_not_enter_player_api(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    original = client.get("/authoring/worlds/mist_valley/files/npcs.yaml").json()["content"]
    secret = "Harlan privately knows the sealed mayoral confession."
    proposed = original.replace(
        "    personality: Wary, practical, and slow to trust strangers.",
        (
            "    personality: Wary, practical, and slow to trust strangers.\n"
            "    rp_profile:\n"
            "      public_persona: A cautious village blacksmith.\n"
            f"      private_self_summary: {secret}"
        ),
    )

    save_response = client.put(
        "/authoring/worlds/mist_valley/files/npcs.yaml",
        json={"content": proposed},
    )
    start_response = client.post("/game/start", json={"world_id": "mist_valley"})
    session_id = start_response.json()["session_id"]
    state_response = client.get(f"/game/state/{session_id}")

    assert save_response.status_code == 200
    assert state_response.status_code == 200
    combined_player_payload = start_response.text + state_response.text
    assert secret not in combined_player_payload
    assert "private_self_summary" not in combined_player_payload
