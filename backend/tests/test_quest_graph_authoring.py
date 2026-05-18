from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import QuestVisibility
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.quest_graph import (
    QuestRewardNode,
    parse_quest_graph,
    preview_quest_graph,
    quest_graph_to_yaml,
    quest_yaml_to_graph,
)
from app.main import app
from app.session_store import InMemorySessionStore, build_visible_state


def _copy_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def test_quests_yaml_converts_to_graph(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    graph = parse_quest_graph("mist_valley", ContentAuthoringService(worlds_root))

    assert graph.world_id == "mist_valley"
    assert [quest.id for quest in graph.quests] == ["missing_tools", "sealed_letter_mystery"]
    assert any(edge.type == "next_stage" and edge.target == "missing_tools:follow_bridge_clue" for edge in graph.edges)


def test_graph_converts_back_to_valid_yaml(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_quest_graph("mist_valley", service)
    graph.quests[0].stages[0].title = "Speak Carefully With Harlan"

    yaml_content = quest_graph_to_yaml(graph)
    validation = service.validate_draft("mist_valley", "quests.yaml", yaml_content)

    assert "Speak Carefully With Harlan" in yaml_content
    assert validation.ok


def test_quest_graph_roundtrip_preserves_rewards_and_failure_paths(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_quest_graph("mist_valley", service)
    quest = graph.quests[0]
    quest.rewards.append(QuestRewardNode(id="coin_reward", text="A pouch of coins", reward_type="currency"))
    quest.stages[0].failure_stages = [quest.stages[1].id]
    quest.stages[0].alternate_stages = [quest.stages[1].id]

    reparsed = quest_yaml_to_graph("mist_valley", quest_graph_to_yaml(graph))
    reparsed_quest = reparsed.quests[0]

    assert reparsed_quest.rewards[0].id == "coin_reward"
    assert reparsed_quest.rewards[0].text == "A pouch of coins"
    assert reparsed_quest.stages[0].failure_stages == [quest.stages[1].id]
    assert reparsed_quest.stages[0].alternate_stages == [quest.stages[1].id]
    assert any(edge.type == "failure_path" for edge in reparsed.edges)


def test_invalid_edge_is_caught_by_validation(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_quest_graph("mist_valley", service)
    graph.quests[0].stages[0].next_stages = ["missing_stage"]

    preview = preview_quest_graph("mist_valley", graph, service)
    validation = service.validate_draft("mist_valley", "quests.yaml", preview.yaml_content)

    assert not validation.ok
    assert any("missing_stage" in issue.message for issue in validation.errors)


def test_missing_trigger_reference_is_caught_by_validation(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_quest_graph("mist_valley", service)
    graph.quests[0].triggers[0].id = "missing_npc"

    preview = preview_quest_graph("mist_valley", graph, service)

    assert not preview.validation.ok
    assert any("missing_npc" in issue.message for issue in preview.validation.errors)


def test_unreachable_stage_produces_warning(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_quest_graph("mist_valley", service)
    graph.quests[0].stages.append(
        type(graph.quests[0].stages[0])(
            id="forgotten_branch",
            title="Forgotten Branch",
            description="A branch not connected to the start.",
            objectives=[],
            next_stages=[],
        )
    )

    preview = preview_quest_graph("mist_valley", graph, service)

    assert preview.validation.ok
    assert any(issue.code == "quest_unreachable_stage" for issue in preview.validation.warnings)


def test_hidden_quest_not_in_player_visible_state(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    from app.engine.content.world_loader import WorldLoader

    state = WorldLoader(worlds_root).load("mist_valley").to_game_state()
    assert state.quests["sealed_letter_mystery"].visibility == QuestVisibility.HIDDEN

    visible = build_visible_state(state)

    assert [quest.id for quest in visible.quests] == ["missing_tools"]


def test_quest_graph_preview_api_does_not_write_disk(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "quest_graph.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)

    graph_response = client.get("/authoring/worlds/mist_valley/quests/graph")
    graph_payload = graph_response.json()
    original_content = (worlds_root / "mist_valley" / "quests.yaml").read_text(encoding="utf-8")
    graph_payload["quests"][0]["stages"][0]["title"] = "Edited In Preview"

    preview_response = client.post(
        "/authoring/worlds/mist_valley/quests/graph/preview",
        json={"graph": graph_payload},
    )
    after_content = (worlds_root / "mist_valley" / "quests.yaml").read_text(encoding="utf-8")

    assert graph_response.status_code == 200
    assert preview_response.status_code == 200
    assert preview_response.json()["validation"]["ok"] is True
    assert "Edited In Preview" in preview_response.json()["yaml_content"]
    assert after_content == original_content


def test_quest_graph_save_api_validates_before_writing(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "quest_graph_save.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)

    graph_payload = client.get("/authoring/worlds/mist_valley/quests/graph").json()
    original_content = (worlds_root / "mist_valley" / "quests.yaml").read_text(encoding="utf-8")
    graph_payload["quests"][0]["stages"][0]["title"] = "Saved Quest Stage"
    saved = client.put(
        "/authoring/worlds/mist_valley/quests/graph",
        json={"graph": graph_payload},
    )
    persisted = (worlds_root / "mist_valley" / "quests.yaml").read_text(encoding="utf-8")

    assert saved.status_code == 200
    assert saved.json()["saved"] is True
    assert "Saved Quest Stage" in persisted
    assert persisted != original_content

    graph_payload["quests"][0]["stages"][0]["next_stages"] = ["missing_stage"]
    rejected = client.put(
        "/authoring/worlds/mist_valley/quests/graph",
        json={"graph": graph_payload},
    )
    persisted_after_reject = (worlds_root / "mist_valley" / "quests.yaml").read_text(encoding="utf-8")

    assert rejected.status_code == 200
    assert rejected.json()["saved"] is False
    assert "missing_stage" not in persisted_after_reject


def test_quest_graph_save_requires_validation(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    graph = parse_quest_graph("mist_valley", service)
    graph.quests[0].stages[0].next_stages = ["missing_stage"]
    yaml_content = quest_graph_to_yaml(graph)

    report = service.write_file("mist_valley", "quests.yaml", yaml_content)
    persisted = (worlds_root / "mist_valley" / "quests.yaml").read_text(encoding="utf-8")

    assert not report.ok
    assert "missing_stage" not in persisted
