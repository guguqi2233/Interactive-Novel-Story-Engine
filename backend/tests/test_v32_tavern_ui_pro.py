from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository
from app.platform.tavern_studio import TavernMessage, TavernRepository, TavernSession, TavernSpeakerType, TavernVisibility
from app.config import Settings


def _client(tmp_path: Path) -> tuple[TestClient, TavernRepository]:
    repo = ProjectRepository(tmp_path)
    project = NarrativeProject(project_id="demo", name="Demo", project_root=str(tmp_path / "demo"))
    repo.save_project(project)
    app.state.project_repository = repo
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    tavern = TavernRepository(Path(repo.load_project("demo").project_root))
    tavern.save_session(TavernSession(session_id="s1", project_id="demo", title="Safe Session", character_ids=["mira"]))
    tavern.append_message(TavernMessage(message_id="m1", session_id="s1", speaker_type=TavernSpeakerType.USER, content="hello there"))
    tavern.append_message(TavernMessage(message_id="m2", session_id="s1", speaker_type=TavernSpeakerType.CHARACTER, content="mature_only private memory", visibility=TavernVisibility.MATURE_ONLY))
    return TestClient(app), tavern


def test_v32_tavern_preferences_recovery_export_and_safety_are_safe(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    preferences = client.put(
        "/projects/demo/tavern/preferences",
        json={"default_character_id": "mira", "default_session_id": "s1", "mature_module_visible": False},
    )
    assert preferences.status_code == 200
    assert preferences.json()["mature_module_visible"] is False
    assert "api_key" not in json.dumps(preferences.json()).lower()

    rejected = client.put("/projects/demo/tavern/preferences", json={"default_character_id": "sk-real-looking-secret"})
    assert rejected.status_code == 400

    recovery = client.post(
        "/projects/demo/tavern/recovery",
        json={"record_id": "r1", "target_type": "message", "target_id": "s1", "safe_draft_text": "unsaved local line", "safe_metadata": {"local_only": True}},
    )
    assert recovery.status_code == 200
    assert "sk-" not in recovery.text.lower()
    assert "hidden fact" not in recovery.text.lower()

    preview = client.post(
        "/projects/demo/tavern/sessions/export-preview",
        json={"scope": "current_session", "session_ids": ["s1"], "format": "json_safe"},
    )
    assert preview.status_code == 200
    assert preview.json()["dry_run"] is True
    assert preview.json()["message_count"] == 1

    exported = client.post(
        "/projects/demo/tavern/sessions/export",
        json={"scope": "current_session", "session_ids": ["s1"], "format": "json_safe", "explicit_confirm": True},
    )
    assert exported.status_code == 200
    payload = json.dumps(exported.json(), ensure_ascii=False).lower()
    assert "mature_only" not in payload
    assert "api_key" not in payload
    assert "state_delta" not in payload

    safety = client.post("/projects/demo/tavern/rp-safety/run")
    assert safety.status_code == 200
    assert "api_key" not in safety.text.lower()


def test_v32_world_npc_safe_summary_and_adapter_do_not_leak_secrets(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    npcs = client.get("/projects/demo/world/npcs/safe-summary?world_id=mist_valley")
    assert npcs.status_code == 200
    assert "npc secret" not in json.dumps(npcs.json()).lower()

    items = npcs.json()["npcs"]
    if items:
        adapted = client.post("/projects/demo/tavern/adapt-world-npc", json={"world_id": "mist_valley", "npc_id": items[0]["npc_id"], "mode": "player_safe"})
        assert adapted.status_code == 200
        payload = json.dumps(adapted.json(), ensure_ascii=False).lower()
        assert "npc secret" not in payload
        assert "hidden fact" not in payload
