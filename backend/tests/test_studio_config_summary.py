from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def make_client(tmp_path: Path, *, provider: str = "openai") -> TestClient:
    database_path = tmp_path / "private" / "studio_settings.db"
    database_path.parent.mkdir()
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(database_path)
    app.state.settings = Settings(
        database_url=f"sqlite:///{database_path}",
        llm_provider=provider,
        llm_api_key="test-secret-placeholder",
        enable_authoring_api=True,
        enable_debug_api=False,
        enable_perf_logging=True,
        enable_playtest_api=True,
        enable_eval_api=True,
    )
    return TestClient(app)


def test_config_summary_redacts_sensitive_values(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/studio/config-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    assert payload["llm_provider"] == "openai"
    assert payload["api_key_configured"] is True
    assert payload["authoring_api_enabled"] is True
    assert payload["playtest_api_enabled"] is True
    assert payload["eval_api_enabled"] is True
    assert payload["database_path_hint"] == "sqlite local file: studio_settings.db"
    assert "test-secret-placeholder" not in response.text
    assert str(tmp_path) not in response.text
    assert "DATABASE_URL" not in response.text
    assert "LLM_API_KEY" not in response.text


def test_config_summary_reports_local_stub_without_external_prompt_warning(tmp_path: Path) -> None:
    client = make_client(tmp_path, provider="local_stub")

    response = client.get("/studio/config-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["llm_provider"] == "local_stub"
    assert payload["provider_sends_prompts_off_machine"] is False
    assert "no network calls" in payload["provider_status"]
