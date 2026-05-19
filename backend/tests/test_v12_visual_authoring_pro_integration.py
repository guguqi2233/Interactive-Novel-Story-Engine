import json
from pathlib import Path
from shutil import copytree
from typing import Any

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.scenario_templates import ScenarioTemplateRenderer
from app.engine.content.validation_gate import AuthoringOperationType, AuthoringValidationGate, AuthoringValidationGateRequest, AuthoringValidationGateResult
from app.main import app
from app.session_store import InMemorySessionStore


SECRET_TEXT = "A sealed letter is hidden beneath a loose paving stone."
API_KEY = "test-secret-placeholder"


def _client(tmp_path: Path, *, authoring: bool = True) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore(worlds_root=str(worlds_root))
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v12.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = tmp_path / "mods"
    app.state.scenario_template_renderer = ScenarioTemplateRenderer(Path("templates"), worlds_root)
    app.state.settings = Settings(
        enable_authoring_api=authoring,
        enable_debug_api=True,
        enable_playtest_api=True,
        llm_provider="local_stub",
        llm_api_key=API_KEY,
    )
    return TestClient(app)


def test_v12_authoring_boundary_gate_and_visual_editor_roundtrips(tmp_path: Path, monkeypatch: Any) -> None:
    client = _client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    before_state = client.get(f"/game/state/{session_id}").json()
    world_path = tmp_path / "worlds" / "mist_valley"
    before_locations = (world_path / "locations.yaml").read_text(encoding="utf-8")
    gate_calls: list[AuthoringOperationType] = []
    original_gate = AuthoringValidationGate.evaluate

    def wrapped_gate(self: AuthoringValidationGate, request: AuthoringValidationGateRequest) -> AuthoringValidationGateResult:
        gate_calls.append(request.operation_type)
        return original_gate(self, request)

    monkeypatch.setattr(AuthoringValidationGate, "evaluate", wrapped_gate)

    map_graph = client.get("/authoring/worlds/mist_valley/map").json()["graph"]
    map_graph["nodes"][0]["x"] += 7
    assert client.post("/authoring/worlds/mist_valley/map/preview", json={"graph": map_graph}).json()["validation"]["ok"] is True
    assert (world_path / "locations.yaml").read_text(encoding="utf-8") == before_locations
    assert client.post("/authoring/worlds/mist_valley/map/validate", json={"graph": map_graph}).json()["ok"] is True
    assert (world_path / "locations.yaml").read_text(encoding="utf-8") == before_locations
    assert client.put("/authoring/worlds/mist_valley/map", json={"graph": map_graph}).json()["saved"] is True

    quest_graph = client.get("/authoring/worlds/mist_valley/quests/graph").json()
    assert client.post("/authoring/worlds/mist_valley/quests/graph/preview", json={"graph": quest_graph}).json()["validation"]["ok"] is True
    assert client.put("/authoring/worlds/mist_valley/quests/graph", json={"graph": quest_graph, "confirm_warnings": True}).json()["validation"]["ok"] is True

    social_graph = client.get("/authoring/worlds/mist_valley/social/graph").json()
    assert client.post("/authoring/worlds/mist_valley/social/graph/preview", json={"graph": social_graph}).json()["validation"]["ok"] is True
    assert client.put("/authoring/worlds/mist_valley/social/graph", json={"graph": social_graph, "confirm_warnings": True}).json()["validation"]["ok"] is True

    economy_graph = client.get("/authoring/worlds/mist_valley/economy").json()
    assert client.post("/authoring/worlds/mist_valley/economy/preview", json={"graph": economy_graph}).json()["validation"]["ok"] is True
    assert client.put("/authoring/worlds/mist_valley/economy", json={"graph": economy_graph, "confirm_warnings": True}).json()["validation"]["ok"] is True

    consequence_graph = client.get("/authoring/worlds/mist_valley/rumor-crime").json()
    assert client.post("/authoring/worlds/mist_valley/rumor-crime/preview", json={"graph": consequence_graph}).json()["validation"]["ok"] is True
    assert client.put("/authoring/worlds/mist_valley/rumor-crime", json={"graph": consequence_graph, "confirm_warnings": True}).json()["validation"]["ok"] is True

    assert AuthoringOperationType.SAVE in gate_calls
    assert client.get(f"/game/state/{session_id}").json() == before_state


def test_v12_rp_authoring_templates_merge_diff_import_and_visibility(tmp_path: Path, monkeypatch: Any) -> None:
    client = _client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    state_text = client.get(f"/game/state/{session_id}").text
    assert SECRET_TEXT not in state_text
    assert "state_deltas" not in state_text

    rp_graph = client.get("/authoring/worlds/mist_valley/rp/characters/pro").json()
    rp_graph["characters"][0]["rp_profile"]["private_self_summary"] = "Private inner fear."
    rp_preview = client.post("/authoring/worlds/mist_valley/rp/characters/pro/preview", json=rp_graph)
    assert rp_preview.status_code == 200
    safe_card = client.post("/authoring/worlds/mist_valley/rp/characters/pro/safe-export", json={"npc_id": rp_graph["characters"][0]["npc_id"]})
    assert "Private inner fear." not in safe_card.text
    assert "private_self_summary" not in client.get(f"/game/state/{session_id}").text

    dialogue = client.get("/authoring/worlds/mist_valley/dialogue-scenes").json()
    assert client.post("/authoring/worlds/mist_valley/dialogue-scenes/preview", json=dialogue).status_code == 200
    assert SECRET_TEXT not in client.post("/authoring/worlds/mist_valley/dialogue-scenes/preview", json=dialogue).text

    group = client.get("/authoring/worlds/mist_valley/group-rp-scenes").json()
    bad_group = json.loads(json.dumps(group))
    if not bad_group["templates"]:
        bad_group["templates"].append(
            {
                "id": "v12_group",
                "name": "V12 Group",
                "scene_type": "meeting",
                "participant_ids": ["harlan"],
                "required_roles": [{"role_id": "speaker", "npc_id": "harlan", "label": "Speaker", "required": True}],
                "location_id": "blacksmith",
                "turn_order_policy": "round_robin",
                "speaker_selection_policy": "deterministic",
                "scene_mood": None,
                "starting_tension": 10,
                "opening_public_context": "",
                "allowed_topics": [],
                "forbidden_topics": [],
                "exit_conditions": [],
                "allow_dead_participants": False,
            }
        )
    bad_group["templates"][0]["participant_ids"].append("missing_npc")
    assert any(
            issue["code"] == "group_rp_scene_missing_participant"
        for issue in client.post("/authoring/worlds/mist_valley/group-rp-scenes/validate", json=bad_group).json()["validation"]["errors"]
    )

    pack = client.post("/authoring/character-packs/export", json={"world_id": "mist_valley"}).text
    assert API_KEY not in pack
    assert SECRET_TEXT not in pack

    before_manifest = (tmp_path / "worlds" / "mist_valley" / "manifest.yaml").read_text(encoding="utf-8")
    template_preview = client.post(
        "/authoring/template-wizard/preview",
        json={"id": "v12_preview", "name": "V12 Preview", "template_type": "questline", "target_world_id": "mist_valley", "variables": {"quest_id": "v12_q", "quest_title": "V12 Quest"}},
    )
    assert template_preview.status_code == 200
    assert (tmp_path / "worlds" / "mist_valley" / "manifest.yaml").read_text(encoding="utf-8") == before_manifest

    client.post("/authoring/worlds/mist_valley/branches", json={"branch_id": "ours", "name": "ours"})
    client.post("/authoring/worlds/mist_valley/branches", json={"branch_id": "theirs", "name": "theirs"})
    theirs = tmp_path / "worlds" / ".branches" / "mist_valley" / "theirs" / "npcs.yaml"
    theirs.write_text(theirs.read_text(encoding="utf-8").replace("name: Harlan", "name: Harlan Theirs"), encoding="utf-8")
    ours = tmp_path / "worlds" / ".branches" / "mist_valley" / "ours" / "npcs.yaml"
    ours.write_text(ours.read_text(encoding="utf-8").replace("name: Harlan", "name: Harlan Ours"), encoding="utf-8")
    merge = client.post("/authoring/worlds/mist_valley/merge/preview", json={"ours": "ours", "theirs": "theirs"}).json()
    assert merge["conflicts"]

    facts = (tmp_path / "worlds" / "mist_valley" / "facts.yaml").read_text(encoding="utf-8").replace("visibility: hidden", "visibility: public", 1)
    diff = client.post(
        "/authoring/diff/review",
        json={
            "base": {"world_id": "mist_valley"},
            "proposed": {"world_id": "mist_valley", "files": {"facts.yaml": facts}},
            "diff_types": ["visibility_diff"],
        },
    )
    assert diff.status_code == 200
    assert diff.json()["visibility_risk"]

    calls: list[AuthoringOperationType] = []
    original_gate = AuthoringValidationGate.evaluate

    def wrapped_gate(self: AuthoringValidationGate, request: AuthoringValidationGateRequest) -> AuthoringValidationGateResult:
        calls.append(request.operation_type)
        return original_gate(self, request)

    monkeypatch.setattr(AuthoringValidationGate, "evaluate", wrapped_gate)
    archive = client.get("/authoring/export/worlds/mist_valley").json()["archive_base64"]
    assert client.post("/authoring/import/packages/apply", json={"archive_base64": archive, "overwrite": True, "confirm_apply": True}).status_code == 200
    assert AuthoringOperationType.APPLY_PACK in calls


def test_v12_reference_picker_and_draft_history_boundaries(tmp_path: Path) -> None:
    client = _client(tmp_path)
    refs = client.get("/authoring/worlds/mist_valley/references")
    assert refs.status_code == 200
    payload = refs.json()
    assert ("location", "village_square") in {(item["kind"], item["id"]) for item in payload["items"]}
    hidden = next(item for item in payload["items"] if item["id"] == "sealed_letter_under_stone")
    assert hidden["hidden"] is True
    assert SECRET_TEXT not in refs.text
    assert client.get("/game/worlds/mist_valley/references").status_code == 404

    content = (tmp_path / "worlds" / "mist_valley" / "locations.yaml").read_text(encoding="utf-8")
    snapshot = client.post(
        "/authoring/drafts/snapshot",
        json={"world_id": "mist_valley", "label": "v12", "draft_content": {"locations.yaml": content}, "max_history": 1},
    )
    assert snapshot.status_code == 200
    draft_id = snapshot.json()["draft_id"]
    restored = client.post(f"/authoring/drafts/{draft_id}/restore").json()
    assert restored["writes_to_disk"] is False
    assert restored["requires_validation_before_save"] is True
    assert client.post(
        "/authoring/worlds/mist_valley/validate-draft",
        json={"file_name": "locations.yaml", "proposed_content": restored["snapshot"]["draft_content"]["locations.yaml"]},
    ).json()["ok"] is True
    rejected = client.post(
        "/authoring/drafts/snapshot",
        json={"world_id": "mist_valley", "draft_content": {"manifest.yaml": f"llm_api_key: {API_KEY}"}},
    )
    assert rejected.status_code == 400
    assert API_KEY not in client.get("/authoring/drafts").text


def test_v12_disabled_authoring_player_ui_and_mock_provider_boundaries(tmp_path: Path) -> None:
    client = _client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    visible = client.get(f"/game/state/{session_id}").text
    assert SECRET_TEXT not in visible
    assert "state_deltas" not in visible
    assert API_KEY not in visible

    app_source = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    api_source = Path("frontend/src/api.ts").read_text(encoding="utf-8")
    assert "ReferencePicker" in app_source
    assert "fetchReferenceIndex" in api_source
    assert "authoring api is disabled" in app_source.lower()

    disabled = _client(tmp_path / "disabled", authoring=False)
    assert disabled.get("/authoring/worlds").status_code == 403
    assert disabled.get("/authoring/drafts").status_code == 403
    assert app.state.settings.llm_provider in {"local_stub", "mock", "fake"}
