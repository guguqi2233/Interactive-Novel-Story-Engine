from __future__ import annotations

import json
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.desktop.diagnostics_bundle import DiagnosticsBundleCreateRequest, DiagnosticsBundleService
from app.desktop.local_logs import LocalLogService
from app.llm.provider_redaction import ProviderRedactionService
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository


TRANSIENT_KEY = "sk-test-v35-transient-provider-secret"


def _project_repo(tmp_path: Path) -> ProjectRepository:
    root = tmp_path / "projects"
    project_root = root / "demo"
    repo = ProjectRepository(root)
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    return repo


def _client(tmp_path: Path) -> tuple[TestClient, object, object]:
    repo = _project_repo(tmp_path)
    previous_repo = getattr(app.state, "project_repository", None)
    previous_settings = getattr(app.state, "settings", None)
    app.state.project_repository = repo
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    return TestClient(app), previous_repo, previous_settings


def _restore(previous_repo: object, previous_settings: object) -> None:
    if previous_repo is None:
        if hasattr(app.state, "project_repository"):
            delattr(app.state, "project_repository")
    else:
        app.state.project_repository = previous_repo
    app.state.settings = previous_settings or Settings(llm_provider="mock")


def test_provider_redaction_service_covers_provider_secret_shapes() -> None:
    redactor = ProviderRedactionService()
    raw = (
        "Authorization: Bearer sk-test-authorization-provider-secret "
        "transient_api_key=sk-test-transient-inline-secret "
        "secret_ref=local/provider/secret-ref-value "
        "relay_token=relay-token-super-secret "
        "raw_provider_error={token:'sk-test-provider-raw-secret'} "
        "https://relay.local/v1/token/path-secret-value?api_key=sk-test-query-secret&signature=abc123secret"
    )

    result = redactor.redact_text(raw, extra_secrets=["path-secret-value"])

    assert result.redaction_count >= 6
    assert "sk-test-authorization-provider-secret" not in result.text
    assert "sk-test-transient-inline-secret" not in result.text
    assert "secret-ref-value" not in result.text
    assert "relay-token-super-secret" not in result.text
    assert "sk-test-provider-raw-secret" not in result.text
    assert "sk-test-query-secret" not in result.text
    assert "path-secret-value" not in result.text


def test_provider_connection_raw_provider_error_is_redacted(tmp_path: Path) -> None:
    client, previous_repo, previous_settings = _client(tmp_path)
    try:
        response = client.post(
            "/projects/demo/providers/test-connection",
            json={
                "provider_type": "openai_compatible",
                "base_url": "http://raw-secret-error.local/v1",
                "transient_api_key": TRANSIENT_KEY,
                "timeout_seconds": 1,
            },
        )
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "auth_failed"
    assert TRANSIENT_KEY not in response.text
    assert "Authorization" not in response.text
    assert "sk-test-raw-provider-secret" not in response.text
    assert "provider-secret" not in response.text
    assert "sk-test-query-secret" not in response.text


def test_provider_model_discovery_error_is_redacted(tmp_path: Path) -> None:
    client, previous_repo, previous_settings = _client(tmp_path)
    try:
        response = client.post(
            "/projects/demo/providers/fetch-models",
            json={
                "provider_type": "custom",
                "base_url": "http://custom.local/v1",
                "model_list_endpoint": "/raw-secret-error?token=sk-test-model-query-secret",
                "transient_api_key": TRANSIENT_KEY,
            },
        )
    finally:
        _restore(previous_repo, previous_settings)

    assert response.status_code == 200
    assert response.json()["report"]["status"] == "model_list_failed"
    assert TRANSIENT_KEY not in response.text
    assert "Authorization" not in response.text
    assert "sk-test-model-raw-secret" not in response.text
    assert "sk-test-model-query-secret" not in response.text
    assert "local/model-secret" not in response.text


def test_provider_logs_are_redacted(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "provider.log").write_text(
        (
            f"provider failed transient_api_key={TRANSIENT_KEY} "
            "Authorization: Bearer sk-test-log-bearer-secret "
            "secret_ref=local/provider/log-secret "
            "raw_provider_response={api_key:'sk-test-raw-log-secret'}"
        ),
        encoding="utf-8",
    )

    response = LocalLogService(tmp_path).list_safe_logs(limit=10)
    payload = json.dumps([entry.model_dump(mode="json") for entry in response.logs])

    assert response.logs
    assert any(entry.redacted for entry in response.logs)
    assert TRANSIENT_KEY not in payload
    assert "Authorization" not in payload
    assert "sk-test-log-bearer-secret" not in payload
    assert "log-secret" not in payload
    assert "sk-test-raw-log-secret" not in payload


def test_diagnostics_bundle_excludes_provider_raw_response(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "provider.log").write_text(
        "raw_provider_response={Authorization:'Bearer sk-test-diagnostics-provider-secret'}",
        encoding="utf-8",
    )
    service = DiagnosticsBundleService(tmp_path)
    request = DiagnosticsBundleCreateRequest(project_id="demo")

    preview = service.preview_bundle(request)
    created = service.create_bundle(request)
    bundle = next((tmp_path / "exports" / "diagnostics").glob("*.zip"))
    with zipfile.ZipFile(bundle, "r") as archive:
        payload = "\n".join(archive.read(name).decode("utf-8") for name in archive.namelist())

    assert created.created is True
    assert preview.safe_payload["provider"] == {"configured": "safe_summary_only", "credential_status": "redacted"}
    assert "provider_raw_response" not in payload
    assert "raw_provider_response" not in payload
    assert "sk-test-diagnostics-provider-secret" not in payload
    assert "Authorization" not in payload
    assert service.validate_bundle(str(bundle)).valid is True
