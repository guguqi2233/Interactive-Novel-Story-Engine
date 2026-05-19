from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.dialogue_scene_authoring import (
    DialogueSceneAuthoring,
    DialogueSceneTemplate,
    parse_dialogue_scene_authoring,
    preview_dialogue_scene_authoring,
    save_dialogue_scene_authoring,
)
from app.engine.content.world_loader import WorldLoader
from app.main import app
from app.session_store import InMemorySessionStore


def _copy_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def _client(tmp_path: Path, worlds_root: Path) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "dialogue_scene_authoring.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def _valid_graph() -> DialogueSceneAuthoring:
    return DialogueSceneAuthoring(
        world_id="mist_valley",
        templates=[
            DialogueSceneTemplate(
                id="ask_harlan_about_tools",
                name="Ask Harlan About Tools",
                participant_ids=["harlan"],
                focus_npc_id="harlan",
                location_id="blacksmith",
                dialogue_mode="focused",
                scene_mood="mist_tension",
                opening_context="The forge is cold and Harlan is guarded.",
                allowed_topics=["missing_tools"],
                forbidden_topics=["mayor_hides_missing_tools"],
                required_visible_facts=[],
                possible_outcomes=[],
            )
        ],
    )


def test_valid_dialogue_scene_template_can_save(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)

    response = save_dialogue_scene_authoring("mist_valley", _valid_graph(), service)

    assert response.saved
    parsed = parse_dialogue_scene_authoring("mist_valley", service)
    assert parsed.templates[0].id == "ask_harlan_about_tools"


def test_invalid_participant_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = _valid_graph()
    graph.templates[0].participant_ids = ["missing_npc"]
    graph.templates[0].focus_npc_id = "missing_npc"

    preview = preview_dialogue_scene_authoring("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "dialogue_scene_missing_participant" for issue in preview.validation.errors)


def test_hidden_topic_does_not_enter_prompt_preview(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = _valid_graph()
    graph.templates[0].allowed_topics = ["missing_tools", "mayor_hides_missing_tools"]
    graph.templates[0].opening_context = "Ask about mayor_hides_missing_tools without leaking it."

    preview = preview_dialogue_scene_authoring("mist_valley", graph, service)

    assert "mayor_hides_missing_tools" not in preview.prompt_preview["ask_harlan_about_tools"]


def test_dialogue_scene_preview_api_does_not_write_files(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    scene_path = worlds_root / "mist_valley" / "dialogue_scenes.yaml"
    before_exists = scene_path.exists()

    response = client.post("/authoring/worlds/mist_valley/dialogue-scenes/preview", json=_valid_graph().model_dump(mode="json"))

    assert response.status_code == 200
    assert response.json()["validation"]["ok"] is True
    assert scene_path.exists() is before_exists


def test_dialogue_scene_authoring_does_not_modify_active_game_state(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    state = WorldLoader(worlds_root).load("mist_valley").to_game_state()

    preview = preview_dialogue_scene_authoring("mist_valley", _valid_graph(), service)

    assert preview.validation.ok
    assert state.turn == 0
    assert state.npcs["harlan"].location_id == "blacksmith"
    assert not hasattr(state, "dialogue_sessions")
