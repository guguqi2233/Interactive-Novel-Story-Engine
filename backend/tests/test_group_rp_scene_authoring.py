from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.group_rp_scene_authoring import (
    GroupRPParticipantRole,
    GroupRPSceneAuthoring,
    GroupRPSceneTemplate,
    parse_group_rp_scene_authoring,
    preview_group_rp_scene_authoring,
    save_group_rp_scene_authoring,
)
from app.engine.content.world_loader import WorldLoader
from app.main import app
from app.session_store import InMemorySessionStore


def _copy_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    _append_mira(worlds_root)
    return worlds_root


def _append_mira(worlds_root: Path, *, condition: str | None = None) -> None:
    path = worlds_root / "mist_valley" / "npcs.yaml"
    extra = "\n  - id: mira\n    name: Mira\n    location_id: blacksmith\n    personality: Sharp, watchful, and formal.\n    knowledge:\n      - old_bridge_creaks_at_midnight\n"
    if condition:
        extra += f"    condition: {condition}\n"
    path.write_text(path.read_text(encoding="utf-8") + extra, encoding="utf-8")


def _client(tmp_path: Path, worlds_root: Path) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "group_rp_scene_authoring.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def _valid_graph() -> GroupRPSceneAuthoring:
    return GroupRPSceneAuthoring(
        world_id="mist_valley",
        templates=[
            GroupRPSceneTemplate(
                id="blacksmith_standoff",
                name="Blacksmith Standoff",
                scene_type="standoff",
                participant_ids=["harlan", "mira"],
                required_roles=[
                    GroupRPParticipantRole(role_id="accuser", npc_id="mira", label="Accuser"),
                    GroupRPParticipantRole(role_id="witness", npc_id="harlan", label="Witness"),
                ],
                location_id="blacksmith",
                turn_order_policy="tension_priority",
                speaker_selection_policy="relationship_tension",
                scene_mood="mist_tension",
                starting_tension=70,
                opening_public_context="The forge is crowded and every word lands hard.",
                allowed_topics=["missing_tools"],
                forbidden_topics=["sealed_letter_under_stone"],
                exit_conditions=["truth_acknowledged"],
            )
        ],
    )


def test_valid_group_scene_template_can_save(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)

    response = save_group_rp_scene_authoring("mist_valley", _valid_graph(), service)

    assert response.saved
    parsed = parse_group_rp_scene_authoring("mist_valley", service)
    assert parsed.templates[0].id == "blacksmith_standoff"


def test_missing_participant_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = _valid_graph()
    graph.templates[0].participant_ids.append("missing_npc")

    preview = preview_group_rp_scene_authoring("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "group_rp_scene_missing_participant" for issue in preview.validation.errors)


def test_hidden_fact_in_opening_context_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = _valid_graph()
    graph.templates[0].opening_public_context = "Everyone knows sealed_letter_under_stone."

    preview = preview_group_rp_scene_authoring("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "group_rp_scene_hidden_fact_in_opening" for issue in preview.validation.errors)
    assert "sealed_letter_under_stone" not in preview.safe_prompt_preview["blacksmith_standoff"]


def test_dead_participant_policy_blocks_unless_explicit(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    _append_mira(worlds_root, condition="dead")
    service = ContentAuthoringService(worlds_root)
    graph = _valid_graph()

    blocked = preview_group_rp_scene_authoring("mist_valley", graph, service)
    graph.templates[0].allow_dead_participants = True
    allowed = preview_group_rp_scene_authoring("mist_valley", graph, service)

    assert any(issue.code == "group_rp_scene_dead_participant_not_allowed" for issue in blocked.validation.errors)
    assert allowed.validation.ok


def test_group_rp_scene_preview_api_does_not_write_files(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    scene_path = worlds_root / "mist_valley" / "group_rp_scenes.yaml"
    before_exists = scene_path.exists()

    response = client.post("/authoring/worlds/mist_valley/group-rp-scenes/preview", json=_valid_graph().model_dump(mode="json"))

    assert response.status_code == 200
    assert response.json()["validation"]["ok"] is True
    assert scene_path.exists() is before_exists


def test_group_rp_scene_authoring_does_not_modify_active_game_state(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    state = WorldLoader(worlds_root).load("mist_valley").to_game_state()

    preview = preview_group_rp_scene_authoring("mist_valley", _valid_graph(), service)

    assert preview.validation.ok
    assert state.turn == 0
    assert "mira" in state.npcs
    assert not hasattr(state, "group_dialogue_scenes")
