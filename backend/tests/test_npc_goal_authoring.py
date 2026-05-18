from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import NPCGoalState, NPCGoalStatus
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.npc_goal_authoring import (
    NPCGoalAuthoringGraph,
    npc_goal_graph_to_yaml,
    npc_yaml_to_goal_graph,
    parse_npc_goal_graph,
    preview_npc_goal_graph,
)
from app.engine.content.world_loader import WorldLoader
from app.main import app
from app.session_store import InMemorySessionStore, build_visible_state


def _copy_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def test_npc_goals_yaml_parses_to_authoring_graph(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)

    graph = parse_npc_goal_graph("mist_valley", ContentAuthoringService(worlds_root))

    assert graph.world_id == "mist_valley"
    assert graph.npcs[0].npc_id == "harlan"
    assert [goal.id for goal in graph.npcs[0].goals] == ["share_bridge_warning", "recover_missing_tools"]


def test_npc_goal_graph_roundtrip_preserves_goal_fields(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_npc_goal_graph("mist_valley", service)
    graph.npcs[0].goals[0].description = "Warn people before the bridge fails."
    graph.npcs[0].goals[0].allowed_actions.append("guard_location")

    yaml_content = npc_goal_graph_to_yaml("mist_valley", graph, service)
    reparsed = npc_yaml_to_goal_graph("mist_valley", yaml_content)

    assert reparsed.npcs[0].goals[0].description == "Warn people before the bridge fails."
    assert "guard_location" in reparsed.npcs[0].goals[0].allowed_actions


def test_invalid_goal_condition_reference_is_reported(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_npc_goal_graph("mist_valley", service)
    graph.npcs[0].goals[0].conditions = ["fact:missing_fact"]

    preview = preview_npc_goal_graph("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "npc_goal_missing_fact" for issue in preview.validation.errors)


def test_invalid_allowed_action_is_reported(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_npc_goal_graph("mist_valley", service)
    graph.npcs[0].goals[0].allowed_actions = ["teleport_to_secret"]

    preview = preview_npc_goal_graph("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any(issue.code == "npc_goal_invalid_allowed_action" for issue in preview.validation.errors)


def test_preview_api_does_not_write_npcs_yaml_or_active_state(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "npc_goal_authoring.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)
    original_content = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")
    active_state = WorldLoader(worlds_root).load("mist_valley").to_game_state()

    graph_payload = client.get("/authoring/worlds/mist_valley/npcs/goals").json()
    graph_payload["npcs"][0]["goals"][0]["description"] = "Edited in preview only."
    preview_response = client.post(
        "/authoring/worlds/mist_valley/npcs/goals/preview",
        json={"graph": graph_payload},
    )
    after_content = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")

    assert preview_response.status_code == 200
    assert preview_response.json()["validation"]["ok"] is True
    assert after_content == original_content
    assert active_state.npcs["harlan"].goals[0].description != "Edited in preview only."  # type: ignore[union-attr]


def test_save_api_validates_before_writing(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "npc_goal_save.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)

    graph_payload = client.get("/authoring/worlds/mist_valley/npcs/goals").json()
    graph_payload["npcs"][0]["goals"][0]["status"] = NPCGoalStatus.BLOCKED.value
    saved = client.put("/authoring/worlds/mist_valley/npcs/goals", json={"graph": graph_payload})
    persisted = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")

    assert saved.status_code == 200
    assert saved.json()["saved"] is True
    assert "blocked" in persisted

    graph_payload["npcs"][0]["goals"][0]["conditions"] = ["location:missing_location"]
    rejected = client.put("/authoring/worlds/mist_valley/npcs/goals", json={"graph": graph_payload})
    persisted_after_reject = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")

    assert rejected.status_code == 200
    assert rejected.json()["saved"] is False
    assert "missing_location" not in persisted_after_reject


def test_hidden_npc_goal_not_in_player_visible_state(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    content = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")
    content = content.replace("hidden: false", "hidden: true") if "hidden: false" in content else content.replace("    merchant: true", "    hidden: true\n    merchant: true")
    (worlds_root / "mist_valley" / "npcs.yaml").write_text(content, encoding="utf-8")

    state = WorldLoader(worlds_root).load("mist_valley").to_game_state()
    visible = build_visible_state(state)

    assert all(npc.id != "harlan" for npc in visible.visible_npcs)
    assert "share_bridge_warning" not in visible.model_dump_json()
