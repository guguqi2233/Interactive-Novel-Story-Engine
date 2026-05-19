from pathlib import Path
from shutil import copytree
from typing import Any

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.quest_graph import parse_quest_graph, save_quest_graph
from app.engine.content.rp_character_authoring import parse_rp_character_authoring, save_rp_character_authoring
from app.engine.content.validation_gate import (
    AuthoringOperationType,
    AuthoringValidationGate,
    AuthoringValidationGateRequest,
    AuthoringValidationGateResult,
)
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.main import app
from app.session_store import InMemorySessionStore


def _worlds(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def _client(tmp_path: Path) -> TestClient:
    worlds_root = _worlds(tmp_path)
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "gate.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = tmp_path / "mods"
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def test_valid_draft_allowed_to_save(tmp_path: Path) -> None:
    worlds_root = _worlds(tmp_path)
    service = ContentAuthoringService(worlds_root)
    content = service.read_file("mist_valley", "locations.yaml")

    result = service.validation_gate.evaluate(
        AuthoringValidationGateRequest(
            world_id="mist_valley",
            operation_type=AuthoringOperationType.SAVE,
            draft_content={"locations.yaml": content},
            affected_files=["locations.yaml"],
        )
    )

    assert result.allowed_to_save is True


def test_validation_error_blocks_save(tmp_path: Path) -> None:
    worlds_root = _worlds(tmp_path)
    service = ContentAuthoringService(worlds_root)
    bad_npcs = service.read_file("mist_valley", "npcs.yaml").replace("location_id: blacksmith", "location_id: missing_place")

    result = service.validation_gate.evaluate(
        AuthoringValidationGateRequest(
            world_id="mist_valley",
            operation_type=AuthoringOperationType.SAVE,
            draft_content={"npcs.yaml": bad_npcs},
            affected_files=["npcs.yaml"],
        )
    )

    assert result.allowed_to_save is False
    assert result.validation_report.errors


def test_warning_requires_confirmation() -> None:
    report = ValidationReport(world_id="mist_valley")
    report.add(ValidationSeverity.WARNING, "quests.yaml.q1", "Unreachable stage.", code="quest_unreachable_stage")
    gate = AuthoringValidationGate()

    result = gate.evaluate(
        AuthoringValidationGateRequest(
            world_id="mist_valley",
            operation_type=AuthoringOperationType.SAVE,
            validation_report=report,
        )
    )

    assert result.allowed_to_save is False
    assert result.confirmation_required is True


def test_hidden_leak_risk_blocks_save(tmp_path: Path) -> None:
    worlds_root = _worlds(tmp_path)
    service = ContentAuthoringService(worlds_root)
    leaky = service.read_file("mist_valley", "rumors.yaml") + (
        "\n  - id: leak_test\n"
        "    fact_id: sealed_letter_under_stone\n"
        "    text_for_player: A sealed letter is hidden beneath a loose paving stone.\n"
    )

    result = service.validation_gate.evaluate(
        AuthoringValidationGateRequest(
            world_id="mist_valley",
            operation_type=AuthoringOperationType.SAVE,
            draft_content={"rumors.yaml": leaky},
            affected_files=["rumors.yaml"],
            confirm_warnings=True,
        )
    )

    assert result.allowed_to_save is False
    assert result.hidden_leak_risks
    assert any(issue.code == "authoring_gate_hidden_leak_blocked" for issue in result.validation_report.errors)


class CountingGate:
    def __init__(self) -> None:
        self.calls: list[AuthoringOperationType] = []

    def evaluate(self, request: AuthoringValidationGateRequest) -> AuthoringValidationGateResult:
        self.calls.append(request.operation_type)
        report = request.validation_report or ValidationReport(world_id=request.world_id)
        return AuthoringValidationGateResult(validation_report=report, allowed_to_save=True)


def test_visual_map_save_calls_gate(tmp_path: Path) -> None:
    service = ContentAuthoringService(_worlds(tmp_path))
    gate = CountingGate()
    service.validation_gate = gate  # type: ignore[assignment]

    graph = service.get_map_graph("mist_valley")
    report = service.write_map_graph("mist_valley", graph, confirm_warnings=True)

    assert report.ok
    assert AuthoringOperationType.SAVE in gate.calls


def test_quest_graph_save_calls_gate(tmp_path: Path) -> None:
    service = ContentAuthoringService(_worlds(tmp_path))
    gate = CountingGate()
    service.validation_gate = gate  # type: ignore[assignment]

    graph = parse_quest_graph("mist_valley", service)
    report = save_quest_graph("mist_valley", graph, service, confirm_warnings=True)

    assert report.ok
    assert AuthoringOperationType.SAVE in gate.calls


def test_rp_character_save_calls_gate(tmp_path: Path) -> None:
    service = ContentAuthoringService(_worlds(tmp_path))
    gate = CountingGate()
    service.validation_gate = gate  # type: ignore[assignment]

    graph = parse_rp_character_authoring("mist_valley", service)
    response = save_rp_character_authoring("mist_valley", graph, service, confirm_warnings=True)

    assert response.saved is True
    assert AuthoringOperationType.SAVE in gate.calls


def test_import_apply_calls_gate(tmp_path: Path, monkeypatch: Any) -> None:
    client = _client(tmp_path)
    archive = client.get("/authoring/export/worlds/mist_valley").json()["archive_base64"]
    calls: list[AuthoringOperationType] = []
    original = AuthoringValidationGate.evaluate

    def wrapped(self: AuthoringValidationGate, request: AuthoringValidationGateRequest) -> AuthoringValidationGateResult:
        calls.append(request.operation_type)
        return original(self, request)

    monkeypatch.setattr(AuthoringValidationGate, "evaluate", wrapped)

    response = client.post(
        "/authoring/import/packages/apply",
        json={"archive_base64": archive, "overwrite": True, "confirm_apply": True},
    )

    assert response.status_code == 200
    assert AuthoringOperationType.APPLY_PACK in calls
