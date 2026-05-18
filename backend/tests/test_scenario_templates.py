from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.scenario_templates import ScenarioTemplateError, ScenarioTemplateRenderer
from app.main import app
from app.session_store import InMemorySessionStore


REQUIRED_VARIABLES = {
    "world_id": "test_world",
    "world_name": "Test World",
    "start_location_id": "square",
    "npc_id": "mara",
    "npc_name": "Mara",
}


def _copy_templates(tmp_path: Path) -> Path:
    templates_root = tmp_path / "templates"
    templates_root.mkdir()
    copytree(Path("templates"), templates_root, dirs_exist_ok=True)
    return templates_root


def test_list_templates_returns_example(tmp_path: Path) -> None:
    renderer = ScenarioTemplateRenderer(
        templates_root=_copy_templates(tmp_path),
        worlds_root=tmp_path / "worlds",
    )

    templates = renderer.list_templates()

    assert [template.id for template in templates] == ["basic_village_world"]
    assert templates[0].template_type == "world"


def test_preview_template_does_not_write_disk(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    renderer = ScenarioTemplateRenderer(
        templates_root=_copy_templates(tmp_path),
        worlds_root=worlds_root,
    )

    preview = renderer.preview_template("basic_village_world", REQUIRED_VARIABLES)

    assert preview.writes_to_disk is False
    assert preview.validation_report is not None
    assert preview.validation_report.ok
    assert not (worlds_root / "test_world").exists()


def test_render_template_generates_valid_yaml(tmp_path: Path) -> None:
    renderer = ScenarioTemplateRenderer(
        templates_root=_copy_templates(tmp_path),
        worlds_root=tmp_path / "worlds",
    )
    template = renderer.get_template("basic_village_world")

    rendered = renderer.render_template(template, REQUIRED_VARIABLES)
    validation = renderer.validate_rendered_content(rendered)

    assert validation is not None
    assert validation.ok
    assert {file.file_name for file in rendered.files} >= {"manifest.yaml", "locations.yaml", "npcs.yaml"}
    assert "world_id: test_world" in rendered.files[0].content


def test_invalid_variables_return_clear_error(tmp_path: Path) -> None:
    renderer = ScenarioTemplateRenderer(
        templates_root=_copy_templates(tmp_path),
        worlds_root=tmp_path / "worlds",
    )

    variables = dict(REQUIRED_VARIABLES)
    variables.pop("npc_name")

    try:
        renderer.preview_template("basic_village_world", variables)
    except ScenarioTemplateError as exc:
        assert "Missing required template variables" in str(exc)
    else:
        raise AssertionError("Expected ScenarioTemplateError")


def test_template_rejects_path_traversal_variable(tmp_path: Path) -> None:
    renderer = ScenarioTemplateRenderer(
        templates_root=_copy_templates(tmp_path),
        worlds_root=tmp_path / "worlds",
    )
    variables = dict(REQUIRED_VARIABLES)
    variables["world_id"] = "../escape"

    try:
        renderer.preview_template("basic_village_world", variables)
    except ScenarioTemplateError as exc:
        assert "Unsafe template variable value" in str(exc)
    else:
        raise AssertionError("Expected ScenarioTemplateError")


def test_apply_template_requires_confirmation_and_writes_valid_world(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    renderer = ScenarioTemplateRenderer(
        templates_root=_copy_templates(tmp_path),
        worlds_root=worlds_root,
    )

    try:
        renderer.apply_template("basic_village_world", REQUIRED_VARIABLES)
    except ScenarioTemplateError as exc:
        assert "explicit confirmation" in str(exc)
    else:
        raise AssertionError("Expected ScenarioTemplateError")

    preview = renderer.apply_template("basic_village_world", REQUIRED_VARIABLES, confirm_apply=True)

    assert preview.writes_to_disk is True
    assert preview.target_world_id == "test_world"
    assert preview.validation_report is not None
    assert preview.validation_report.ok
    assert (worlds_root / "test_world" / "manifest.yaml").exists()


def test_template_directory_rejects_executable_files(tmp_path: Path) -> None:
    templates_root = _copy_templates(tmp_path)
    (templates_root / "evil.py").write_text("print('nope')", encoding="utf-8")
    renderer = ScenarioTemplateRenderer(
        templates_root=templates_root,
        worlds_root=tmp_path / "worlds",
    )

    try:
        renderer.list_templates()
    except ScenarioTemplateError as exc:
        assert "Executable files are not allowed" in str(exc)
    else:
        raise AssertionError("Expected ScenarioTemplateError")


def test_template_preview_does_not_modify_active_game_state(tmp_path: Path) -> None:
    templates_root = _copy_templates(tmp_path)
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "templates_api.db")
    app.state.worlds_root = worlds_root
    app.state.scenario_template_renderer = ScenarioTemplateRenderer(
        templates_root=templates_root,
        worlds_root=worlds_root,
    )
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)

    start_response = client.post("/game/start", json={"world_id": "mist_valley"})
    session_id = start_response.json()["session_id"]
    before_state = client.get(f"/game/state/{session_id}").json()
    preview_response = client.post(
        "/authoring/templates/basic_village_world/preview",
        json={"variables": REQUIRED_VARIABLES},
    )
    after_state = client.get(f"/game/state/{session_id}").json()

    assert preview_response.status_code == 200
    assert preview_response.json()["writes_to_disk"] is False
    assert before_state == after_state
    assert not (worlds_root / "test_world").exists()


def test_authoring_template_api_rejects_path_traversal(tmp_path: Path) -> None:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "templates_api.db")
    app.state.scenario_template_renderer = ScenarioTemplateRenderer(
        templates_root=_copy_templates(tmp_path),
        worlds_root=tmp_path / "worlds",
    )
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)

    response = client.post(
        "/authoring/templates/basic_village_world/preview",
        json={"variables": {**REQUIRED_VARIABLES, "world_id": "../escape"}},
    )

    assert response.status_code == 400
    assert "Unsafe template variable value" in response.json()["detail"]


def test_authoring_template_api_get_and_apply(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "templates_api.db")
    app.state.scenario_template_renderer = ScenarioTemplateRenderer(
        templates_root=_copy_templates(tmp_path),
        worlds_root=worlds_root,
    )
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)

    detail_response = client.get("/authoring/templates/basic_village_world")
    apply_response = client.post(
        "/authoring/templates/basic_village_world/apply",
        json={"variables": REQUIRED_VARIABLES, "confirm_apply": True},
    )

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == "basic_village_world"
    assert apply_response.status_code == 200
    assert apply_response.json()["writes_to_disk"] is True
    assert apply_response.json()["target_world_id"] == "test_world"
    assert (worlds_root / "test_world" / "manifest.yaml").exists()
