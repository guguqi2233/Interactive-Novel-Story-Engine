from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.world_loader import WorldLoader
from app.roleplay.rp_scenario_templates import RPScenarioTemplateError, RPScenarioTemplateRenderer
from app.main import app
from app.session_store import InMemorySessionStore


def _copy_rp_templates(tmp_path: Path) -> Path:
    templates_root = tmp_path / "rp"
    templates_root.mkdir()
    copytree(Path("templates") / "rp", templates_root, dirs_exist_ok=True)
    return templates_root


def test_rp_scenario_templates_load() -> None:
    renderer = RPScenarioTemplateRenderer(Path("templates") / "rp")

    templates = renderer.list_templates()

    assert {template.id for template in templates} >= {"first_meeting", "interrogation", "group_meeting"}
    assert all(template.suggested_dialogue_mode for template in templates)


def test_missing_required_participant_is_validation_error(tmp_path: Path) -> None:
    renderer = RPScenarioTemplateRenderer(_copy_rp_templates(tmp_path))

    preview = renderer.preview_template("first_meeting", participant_ids=["mira"])

    assert any("Missing required participants" in error for error in preview.errors)


def test_required_visible_fact_missing_blocks_apply(tmp_path: Path) -> None:
    templates_root = tmp_path / "rp"
    templates_root.mkdir()
    (templates_root / "needs_secret.yaml").write_text(
        """
id: needs_secret
name: Needs Secret
scene_type: secret_reveal
required_participants:
  - harlan
suggested_dialogue_mode: focused
allowed_topics:
  - safe-topic
forbidden_topics:
  - sealed_letter_under_stone
required_visible_facts:
  - sealed_letter_under_stone
""".strip(),
        encoding="utf-8",
    )
    renderer = RPScenarioTemplateRenderer(templates_root)
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.player.location_id = "blacksmith"

    preview = renderer.preview_template("needs_secret", state=state)

    assert any("Required visible facts are not known" in error for error in preview.errors)
    try:
        renderer.apply_template("needs_secret", state=state, confirm_apply=True)
    except RPScenarioTemplateError as exc:
        assert "Required visible facts are not known" in str(exc)
    else:
        raise AssertionError("Expected RPScenarioTemplateError")


def test_forbidden_hidden_topic_is_filtered_from_draft(tmp_path: Path) -> None:
    renderer = RPScenarioTemplateRenderer(_copy_rp_templates(tmp_path))

    preview = renderer.preview_template("interrogation")

    assert "sealed_letter_under_stone" not in preview.draft.active_topics
    assert "mayor_hides_missing_tools" not in preview.draft.active_topics


def test_rp_template_preview_and_apply_do_not_modify_game_state(tmp_path: Path) -> None:
    renderer = RPScenarioTemplateRenderer(_copy_rp_templates(tmp_path))
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    state.player.location_id = "blacksmith"
    before = state.model_dump(mode="json")

    preview = renderer.preview_template("first_meeting", state=state)
    applied = renderer.apply_template("first_meeting", state=state, confirm_apply=True)

    assert preview.writes_to_disk is False
    assert preview.modifies_game_state is False
    assert applied.applied is True
    assert applied.draft.dialogue_session_draft is not None
    assert state.model_dump(mode="json") == before


def test_rp_scenario_template_api_is_authoring_only_and_safe(tmp_path: Path) -> None:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "rp_templates.db")
    app.state.rp_scenario_template_renderer = RPScenarioTemplateRenderer(_copy_rp_templates(tmp_path))
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)

    list_response = client.get("/authoring/rp-scenario-templates")
    preview_response = client.post(
        "/authoring/rp-scenario-templates/interrogation/preview",
        json={"participant_ids": ["harlan"]},
    )
    apply_response = client.post(
        "/authoring/rp-scenario-templates/interrogation/apply",
        json={"participant_ids": ["harlan"], "confirm_apply": True},
    )

    assert list_response.status_code == 200
    assert preview_response.status_code == 200
    assert preview_response.json()["writes_to_disk"] is False
    assert preview_response.json()["modifies_game_state"] is False
    assert "sealed_letter_under_stone" not in preview_response.json()["draft"]["active_topics"]
    assert apply_response.status_code == 200
    assert apply_response.json()["applied"] is True


def test_rp_scenario_template_api_disabled(tmp_path: Path) -> None:
    app.state.rp_scenario_template_renderer = RPScenarioTemplateRenderer(_copy_rp_templates(tmp_path))
    app.state.settings = Settings(enable_authoring_api=False, llm_provider="mock")
    client = TestClient(app)

    response = client.get("/authoring/rp-scenario-templates")

    assert response.status_code == 403
