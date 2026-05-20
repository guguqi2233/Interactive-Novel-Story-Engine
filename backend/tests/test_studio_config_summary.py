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


def test_local_config_summary_redacts_secrets(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/studio/config/summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider_type"] == "openai"
    assert payload["api_key_configured"] is True
    assert payload["database_path_hint"] == "sqlite local file: studio_settings.db"
    assert "test-secret-placeholder" not in response.text
    assert str(tmp_path) not in response.text
    assert "raw_env" not in response.text


def test_local_config_missing_provider_issue(tmp_path: Path) -> None:
    client = make_client(tmp_path, provider="openai")

    app.state.settings = app.state.settings.model_copy(update={"llm_api_key": None})
    response = client.get("/studio/config/issues")

    assert response.status_code == 200
    payload = response.json()
    assert any(issue["code"] == "openai_api_key_missing" for issue in payload)
    assert all(issue["safe_field"] != "LLM_API_KEY" for issue in payload)
    assert any(issue["safe_field"] == "provider_config" for issue in payload)
    assert "test-secret-placeholder" not in response.text
    assert "LLM_API_KEY" not in response.text


def test_generated_env_template_contains_no_real_secret(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post("/studio/config/generate-template")

    assert response.status_code == 200
    payload = response.json()
    assert payload["contains_real_secret"] is False
    assert payload["writes_to_disk"] is False
    assert 'LLM_API_KEY=""' in payload["template"]
    assert "test-secret-placeholder" not in payload["template"]
    assert str(tmp_path) not in payload["template"]
