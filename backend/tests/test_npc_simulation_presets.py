from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.npc_simulation_presets import (
    NPCSimulationPreset,
    NPCSimulationPresetApplyRequest,
    list_npc_simulation_presets,
    preview_npc_simulation_preset,
)
from app.engine.content.validation_gate import AuthoringValidationGate, AuthoringValidationGateRequest, AuthoringValidationGateResult
from app.engine.content.world_loader import WorldLoader
from app.main import app
from app.session_store import InMemorySessionStore


def _copy_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def test_npc_simulation_presets_load() -> None:
    presets = list_npc_simulation_presets()

    assert {preset.id for preset in presets} >= {"guard", "merchant", "investigator"}
    assert all(preset.goals for preset in presets)


def test_invalid_preset_unknown_fact_is_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    preset = NPCSimulationPreset(
        id="invalid_unknown_fact",
        name="Invalid",
        goals=[
            {
                "id": "requires_unknown_fact",
                "description": "This must fail validation.",
                "priority": 10,
                "conditions": ["fact:missing_fact_for_preset"],
                "allowed_actions": ["talk_to_npc"],
            }
        ],
    )

    preview = preview_npc_simulation_preset(
        "mist_valley",
        "harlan",
        NPCSimulationPresetApplyRequest(preset=preset),
        service,
    )

    assert not preview.validation.ok
    assert any(issue.code == "npc_simulation_preset_unknown_fact" for issue in preview.validation.errors)


def test_apply_preset_only_returns_draft_and_leaves_active_state_unchanged(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    original_content = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")
    original_state = WorldLoader(worlds_root).load("mist_valley").to_game_state()

    preview = preview_npc_simulation_preset(
        "mist_valley",
        "harlan",
        NPCSimulationPresetApplyRequest(preset_id="guard"),
        service,
    )
    after_content = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")
    after_state = WorldLoader(worlds_root).load("mist_valley").to_game_state()

    assert preview.validation.ok
    assert "guard_assigned_location" in preview.yaml_content
    assert after_content == original_content
    assert after_state.npcs["harlan"].faction_duties == original_state.npcs["harlan"].faction_duties


def test_preset_preview_uses_authoring_validation_gate(tmp_path: Path, monkeypatch) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    calls: list[AuthoringValidationGateRequest] = []
    original = AuthoringValidationGate.evaluate

    def wrapped(self: AuthoringValidationGate, request: AuthoringValidationGateRequest) -> AuthoringValidationGateResult:
        calls.append(request)
        return original(self, request)

    monkeypatch.setattr(AuthoringValidationGate, "evaluate", wrapped)

    preview = preview_npc_simulation_preset(
        "mist_valley",
        "harlan",
        NPCSimulationPresetApplyRequest(preset_id="merchant"),
        service,
    )

    assert preview.validation_gate.validation_report.world_id == "mist_valley"
    assert calls
    assert calls[0].affected_files == ["npcs.yaml"]


def test_npc_simulation_preset_api_preview_and_apply_draft(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "npc_simulation_preset.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)
    original_content = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")

    listed = client.get("/authoring/npc-simulation-presets")
    preview = client.post(
        "/authoring/worlds/mist_valley/npcs/harlan/simulation-preset/preview",
        json={"preset_id": "guard"},
    )
    applied = client.post(
        "/authoring/worlds/mist_valley/npcs/harlan/simulation-preset/apply-draft",
        json={"preset_id": "guard"},
    )
    after_content = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")

    assert listed.status_code == 200
    assert any(preset["id"] == "guard" for preset in listed.json()["presets"])
    assert preview.status_code == 200
    assert preview.json()["validation"]["ok"] is True
    assert applied.status_code == 200
    assert "guard_assigned_location" in applied.json()["yaml_content"]
    assert after_content == original_content
