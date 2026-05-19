from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.campaign_starter_kit import (
    CampaignStarterKitBuildRequest,
    CampaignStarterKitDraft,
    build_campaign_starter_kit,
    export_campaign_starter_script_package,
    preview_campaign_starter_kit,
)
from app.main import app
from app.session_store import InMemorySessionStore


def _draft(**overrides: object) -> CampaignStarterKitDraft:
    values: dict[str, object] = {
        "campaign_id": "starter_mist",
        "name": "Starter Mist",
        "genre": "mystery",
        "tone": "grounded",
        "starting_region": "square",
        "core_conflict": "missing heirloom",
        "npc_count": 3,
        "questline_count": 1,
        "faction_count": 2,
        "mystery_enabled": True,
        "RP_focus_level": "medium",
        "target_playtime_hours": 2,
    }
    values.update(overrides)
    return CampaignStarterKitDraft(**values)


def _client(tmp_path: Path) -> TestClient:
    worlds_root = tmp_path / "worlds"
    worlds_root.mkdir()
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "campaign_starter.db")
    app.state.session_store = InMemorySessionStore(worlds_root=worlds_root)
    app.state.worlds_root = worlds_root
    return TestClient(app)


def test_campaign_starter_draft_can_be_generated(tmp_path: Path) -> None:
    preview = preview_campaign_starter_kit(_draft(), worlds_root=str(tmp_path / "worlds"))

    assert preview.validation.ok
    assert preview.world_pack_draft.world_id == "starter_mist"
    assert preview.npc_pack_draft.npc_count == 3
    assert preview.quest_pack_draft.quest_count == 1
    assert preview.faction_draft is not None
    assert preview.mystery_draft is not None


def test_preview_does_not_write_disk(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    preview = preview_campaign_starter_kit(_draft(), worlds_root=str(worlds_root))

    assert preview.writes_to_disk is False
    assert not (worlds_root / "starter_mist").exists()


def test_build_requires_validation_and_confirmation(tmp_path: Path) -> None:
    blocked = build_campaign_starter_kit(
        CampaignStarterKitBuildRequest(draft=_draft(), confirm_build=False),
        worlds_root=str(tmp_path / "worlds"),
    )

    assert not blocked.built
    assert any(issue.code == "campaign_starter_build_requires_confirmation" for issue in blocked.validation.errors)

    built = build_campaign_starter_kit(
        CampaignStarterKitBuildRequest(draft=_draft(), confirm_build=True),
        worlds_root=str(tmp_path / "worlds"),
    )

    assert built.validation.ok
    assert built.quality_gate_dry_run.quality_gate_dry_run is True
    assert built.built


def test_quality_gate_dry_run_runs(tmp_path: Path) -> None:
    preview = preview_campaign_starter_kit(_draft(), worlds_root=str(tmp_path / "worlds"))

    assert preview.quality_gate_dry_run.validation_ok
    assert preview.quality_gate_dry_run.summary["world"] == "starter_mist"
    assert preview.quality_gate_config["hidden_leak_check"] is True


def test_script_package_draft_and_export_generated(tmp_path: Path) -> None:
    preview = preview_campaign_starter_kit(_draft(), worlds_root=str(tmp_path / "worlds"))

    assert preview.script_package_draft.validation.ok
    assert preview.script_package_draft.manifest.package_id == "starter_mist_starter_script"

    archive = export_campaign_starter_script_package(_draft())
    assert archive.archive_base64
    with ZipFile(BytesIO(base64.b64decode(archive.archive_base64)), "r") as zip_file:
        assert "script_package_manifest.json" in zip_file.namelist()
        assert "campaign_starter/manifest.json" in zip_file.namelist()


def test_active_game_state_not_modified(tmp_path: Path) -> None:
    preview = preview_campaign_starter_kit(_draft(), worlds_root=str(tmp_path / "worlds"))

    assert preview.active_game_state_modified is False
    assert not (tmp_path / "world_engine.db").exists()


def test_api_preview_campaign_starter(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post("/production/campaign-starter/preview", json=_draft().model_dump(mode="json"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["validation"]["ok"] is True
    assert payload["writes_to_disk"] is False
