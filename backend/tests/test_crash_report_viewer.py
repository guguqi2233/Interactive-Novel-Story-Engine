from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.desktop.crash_reports import CrashReportService
from app.main import app
from app.session_store import InMemorySessionStore


def _make_client(tmp_path: Path, *, debug_enabled: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "crash_reports.db")
    app.state.settings = Settings(
        enable_debug_api=debug_enabled,
        llm_api_key="sk-test-secret-that-must-not-appear",
    )
    app.state.crash_report_service = CrashReportService()
    return TestClient(app)


def test_crash_report_record_and_read(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    report = app.state.crash_report_service.record_backend_exception(
        RuntimeError("Backend failed safely."),
        context={"route": "/studio/status"},
    )

    listed = client.get("/debug/crash-reports")
    detail = client.get(f"/debug/crash-reports/{report.id}")

    assert listed.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["reports"][0]["id"] == report.id
    assert detail.json()["safe_message"] == "Backend failed safely."


def test_crash_report_redacts_api_key_raw_prompt_and_hidden_fact(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    report = app.state.crash_report_service.record_backend_exception(
        RuntimeError(
            'boom sk-live-secret123456 Authorization: Bearer abc123 '
            'raw_prompt="tell hidden fact text: The shrine key is under the well"'
        ),
        context={
            "route": "/debug",
            "prompt": "raw prompt should be dropped",
            "hidden_fact_text": "The shrine key is under the well",
        },
    )

    response = client.get(f"/debug/crash-reports/{report.id}")

    assert response.status_code == 200
    text = response.text
    assert "sk-live-secret" not in text
    assert "abc123" not in text
    assert "raw prompt should be dropped" not in text
    assert "The shrine key" not in text
    assert "[REDACTED" in text


def test_crash_report_debug_disabled_forbidden(tmp_path: Path) -> None:
    client = _make_client(tmp_path, debug_enabled=False)

    response = client.get("/debug/crash-reports")

    assert response.status_code == 403


def test_crash_report_delete(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    report = app.state.crash_report_service.record_backend_exception(ValueError("delete me"))

    deleted = client.delete(f"/debug/crash-reports/{report.id}")
    missing = client.get(f"/debug/crash-reports/{report.id}")

    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert missing.status_code == 404
