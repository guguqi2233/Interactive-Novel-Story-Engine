from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.template_wizard import (
    TemplateWizardDraft,
    TemplateWizardType,
    apply_template_wizard_draft,
    preview_template_wizard_draft,
)
from app.engine.content.validation_gate import AuthoringValidationGateResult
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.main import app
from app.session_store import InMemorySessionStore


def _copy_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def _client(tmp_path: Path, worlds_root: Path) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "template_wizard.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def test_world_template_wizard_draft_generates_valid_world(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    draft = TemplateWizardDraft(
        id="wizard_world",
        name="Wizard World",
        template_type=TemplateWizardType.WORLD,
        variables={"world_id": "wizard_world", "world_name": "Wizard World"},
    )

    preview = preview_template_wizard_draft(draft, service)

    assert preview.validation and preview.validation.ok
    assert {file.file_name for file in preview.generated_files} >= {"manifest.yaml", "locations.yaml", "npcs.yaml"}
    assert not (worlds_root / "wizard_world").exists()


def test_questline_template_wizard_draft_generates(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    draft = TemplateWizardDraft(
        id="find_relic",
        name="Find Relic",
        template_type=TemplateWizardType.QUESTLINE,
        target_world_id="mist_valley",
        variables={"location_id": "village_square"},
    )

    preview = preview_template_wizard_draft(draft, service)

    assert preview.validation and preview.validation.ok
    assert preview.generated_files[0].file_name == "quests.yaml"
    assert "find_relic" in preview.generated_files[0].content


def test_group_rp_scene_template_wizard_draft_generates(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    draft = TemplateWizardDraft(
        id="council_meeting",
        name="Council Meeting",
        template_type=TemplateWizardType.GROUP_RP_SCENE,
        target_world_id="mist_valley",
        variables={"participant_ids": "harlan", "location_id": "village_square"},
    )

    preview = preview_template_wizard_draft(draft, service)

    assert preview.validation and preview.validation.ok
    assert preview.generated_files[0].file_name == "group_rp_scenes.yaml"
    assert "council_meeting" in preview.generated_files[0].content


def test_invalid_variables_are_caught(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    draft = TemplateWizardDraft(
        id="bad_template",
        name="Bad",
        template_type=TemplateWizardType.QUESTLINE,
        target_world_id="mist_valley",
        variables={"location_id": "../secrets"},
    )

    preview = preview_template_wizard_draft(draft, service)

    assert preview.validation and not preview.validation.ok
    assert any(issue.code == "template_wizard_invalid_variable" for issue in preview.validation.errors)


def test_template_wizard_preview_does_not_write_disk(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    before = (worlds_root / "mist_valley" / "quests.yaml").read_text(encoding="utf-8")
    client = _client(tmp_path, worlds_root)

    response = client.post(
        "/authoring/template-wizard/preview",
        json={
            "id": "preview_quest",
            "name": "Preview Quest",
            "template_type": "questline",
            "target_world_id": "mist_valley",
            "variables": {"location_id": "village_square"},
        },
    )

    assert response.status_code == 200
    assert response.json()["validation"]["ok"] is True
    assert (worlds_root / "mist_valley" / "quests.yaml").read_text(encoding="utf-8") == before


def test_template_wizard_apply_requires_validation_and_confirmation(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    before = (worlds_root / "mist_valley" / "quests.yaml").read_text(encoding="utf-8")

    unconfirmed = client.post(
        "/authoring/template-wizard/apply",
        json={
            "draft": {
                "id": "apply_quest",
                "name": "Apply Quest",
                "template_type": "questline",
                "target_world_id": "mist_valley",
                "variables": {"npc_id": "missing_npc"},
            },
            "confirm_apply": False,
        },
    )
    assert unconfirmed.status_code == 200
    assert any(issue["code"] == "template_wizard_apply_requires_confirmation" for issue in unconfirmed.json()["validation"]["errors"])

    confirmed_invalid = client.post(
        "/authoring/template-wizard/apply",
        json={
            "draft": {
                "id": "apply_quest",
                "name": "Apply Quest",
                "template_type": "questline",
                "target_world_id": "mist_valley",
                "variables": {"npc_id": "missing_npc"},
            },
            "confirm_apply": True,
        },
    )

    assert confirmed_invalid.status_code == 200
    assert confirmed_invalid.json()["applied"] is False
    assert confirmed_invalid.json()["validation"]["ok"] is False
    assert (worlds_root / "mist_valley" / "quests.yaml").read_text(encoding="utf-8") == before


def test_world_template_apply_uses_validation_gate_before_writing(tmp_path: Path, monkeypatch) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    draft = TemplateWizardDraft(
        id="blocked_world",
        name="Blocked World",
        template_type=TemplateWizardType.WORLD,
        variables={"world_id": "blocked_world", "world_name": "Blocked World"},
    )
    calls: list[str] = []

    def fake_evaluate(request):
        calls.append(request.operation_type.value)
        report = request.validation_report or ValidationReport(world_id=request.world_id)
        report.add(ValidationSeverity.ERROR, "template_wizard", "Blocked by test gate.", code="test_gate_block")
        return AuthoringValidationGateResult(validation_report=report, allowed_to_save=False)

    monkeypatch.setattr(service.validation_gate, "evaluate", fake_evaluate)

    preview = apply_template_wizard_draft(
        type("Request", (), {"draft": draft, "confirm_apply": True, "confirm_warnings": True})(),
        service,
    )

    assert calls == ["apply_template"]
    assert preview.applied is False
    assert not (worlds_root / "blocked_world").exists()
