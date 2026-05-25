from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.fake_provider import FakeLLMProvider
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository
from app.platform.tavern_studio import GeneratedTavernReply, TavernCharacter, TavernRepository, TavernSession


def _client(tmp_path: Path) -> tuple[TestClient, TavernRepository]:
    project_root = tmp_path / "demo"
    repo = ProjectRepository(tmp_path)
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    app.state.project_repository = repo
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    app.state.tavern_llm_provider = FakeLLMProvider(
        json_responses=[
            GeneratedTavernReply(content="安全的 fake RP 回复。", speaker_id="mira", safety_notes=["fake_provider"]).model_dump(mode="json"),
            GeneratedTavernReply(content="安全的 fake 多 NPC 回复。", speaker_id="mira", safety_notes=["fake_provider"]).model_dump(mode="json"),
        ]
    )
    tavern = TavernRepository(project_root)
    tavern.create_tavern_character(
        TavernCharacter(
            tavern_character_id="mira",
            project_id="demo",
            display_name="米拉",
            description="本地 RP 角色。",
        )
    )
    tavern.create_tavern_character(
        TavernCharacter(
            tavern_character_id="orin",
            project_id="demo",
            display_name="奥林",
            description="第二位本地 RP 角色。",
        )
    )
    tavern.create_session(TavernSession(session_id="s1", project_id="demo", title="本地 RP", character_ids=["mira", "orin"]))
    return TestClient(app), tavern


def test_v37_tavern_cn_fake_reply_path_is_safe_and_non_world_mutating(tmp_path: Path) -> None:
    previous_provider = getattr(app.state, "tavern_llm_provider", None)
    client, tavern = _client(tmp_path)
    try:
        _assert_tavern_cn_workflow(client, tavern)
    finally:
        if previous_provider is None and hasattr(app.state, "tavern_llm_provider"):
            delattr(app.state, "tavern_llm_provider")
        elif previous_provider is not None:
            app.state.tavern_llm_provider = previous_provider


def _assert_tavern_cn_workflow(client: TestClient, tavern: TavernRepository) -> None:

    mature_settings = client.get("/projects/demo/mature/settings")
    assert mature_settings.status_code == 200
    mature_payload = mature_settings.json()
    assert mature_payload["policy"]["enabled"] is False
    assert any("disabled by default" in item for item in mature_payload["warnings"])

    chat = client.post(
        "/projects/demo/tavern/sessions/s1/chat",
        json={"user_message": "你好，来一段本地 RP。", "character_id": "mira"},
    )
    assert chat.status_code == 200
    assert chat.json()["content"] == "安全的 fake RP 回复。"
    assert tavern.load_session("s1").message_refs

    scene = client.post(
        "/projects/demo/tavern/multi-scenes",
        json={"scene_id": "scene1", "session_id": "s1", "title": "多 NPC 场景", "participant_ids": ["mira", "orin"]},
    )
    assert scene.status_code == 200
    generated = client.post("/projects/demo/tavern/multi-scenes/scene1/next-reply")
    assert generated.status_code == 200
    assert generated.json()["message"]["content"] == "安全的 fake 多 NPC 回复。"

    payload = json.dumps({"chat": chat.json(), "scene": generated.json()}, ensure_ascii=False).lower()
    assert "api_key" not in payload
    assert "authorization" not in payload
    assert "npc secret" not in payload
    assert "hidden fact" not in payload
    assert "mature_only" not in payload
    assert "state_delta" not in payload
    assert generated.json()["message"]["proposed_world_effects"] == []
