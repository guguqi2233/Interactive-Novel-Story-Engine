from __future__ import annotations

from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.import_export import ImportExportService
from app.engine.content.local_content_library import LocalContentLibraryService
from app.engine.content.production_pipeline_dashboard import build_production_pipeline_summary
from app.main import app
from app.session_store import InMemorySessionStore


def _roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    worlds_root = tmp_path / "worlds"
    mods_root = tmp_path / "mods"
    templates_root = tmp_path / "templates"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    mods_root.mkdir()
    templates_root.mkdir()
    return worlds_root, mods_root, templates_root


def _library(tmp_path: Path) -> tuple[LocalContentLibraryService, Path]:
    worlds_root, mods_root, templates_root = _roots(tmp_path)
    service = ImportExportService(
        worlds_root=worlds_root,
        mods_root=mods_root,
        templates_root=templates_root,
        repository=SQLiteSaveRepository(tmp_path / "pipeline.db"),
    )
    return LocalContentLibraryService(service), worlds_root


def _client(tmp_path: Path, *, authoring: bool = True) -> TestClient:
    worlds_root, mods_root, templates_root = _roots(tmp_path)
    app.state.settings = Settings(enable_authoring_api=authoring, llm_provider="mock")
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "pipeline_api.db")
    app.state.session_store = InMemorySessionStore(worlds_root=worlds_root)
    app.state.worlds_root = worlds_root
    app.state.mods_root = mods_root
    app.state.scenario_template_renderer = None
    app.state.quality_gate_results = []
    return TestClient(app)


def test_pipeline_summary_api_ok(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/production/pipeline-summary?world_id=mist_valley")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    assert payload["active_world"] == "mist_valley"
    assert payload["batch_validation_status"]["count"] >= 1
    assert payload["quick_entries"]


def test_pipeline_summary_does_not_return_api_key(tmp_path: Path) -> None:
    service, worlds_root = _library(tmp_path)

    summary = build_production_pipeline_summary(
        worlds_root=worlds_root,
        library_service=service,
        quality_gate_results=[],
        active_world="mist_valley",
    )

    payload = summary.model_dump_json()
    assert "sk-real" not in payload
    assert "api_key" not in payload.lower()


def test_pipeline_summary_redacts_hidden_details(tmp_path: Path) -> None:
    service, worlds_root = _library(tmp_path)

    summary = build_production_pipeline_summary(
        worlds_root=worlds_root,
        library_service=service,
        quality_gate_results=[],
        active_world="mist_valley",
    )

    payload = summary.model_dump_json().lower()
    assert "sealed_letter_under_stone" not in payload
    assert "hidden details" not in payload
    assert summary.hidden_details_redacted is True


def test_pipeline_summary_authoring_disabled(tmp_path: Path) -> None:
    client = _client(tmp_path, authoring=False)

    response = client.get("/production/pipeline-summary")

    assert response.status_code == 403
