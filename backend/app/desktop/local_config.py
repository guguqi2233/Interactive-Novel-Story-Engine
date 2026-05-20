from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.config import Settings


LocalConfigSeverity = Literal["info", "warning", "error"]


class LocalConfigIssue(BaseModel):
    code: str
    severity: LocalConfigSeverity
    message: str
    safe_field: str


class LocalConfigSummary(BaseModel):
    local_only: bool = True
    provider_type: str
    model_id: str
    debug_api_enabled: bool
    authoring_api_enabled: bool
    eval_api_enabled: bool
    playtest_api_enabled: bool
    usage_tracking_enabled: bool
    database_configured: bool
    database_path_hint: str
    api_key_configured: bool
    local_paths_redacted: dict[str, str] = Field(default_factory=dict)
    issues: list[LocalConfigIssue] = Field(default_factory=list)


class LocalEnvTemplateResponse(BaseModel):
    local_only: bool = True
    file_name: str = ".env.example"
    template: str
    contains_real_secret: bool = False
    writes_to_disk: bool = False


class LocalConfigManager:
    """Safe local config summaries for Desktop Studio.

    This manager never returns raw env, API key values, database passwords, or
    full sensitive paths. It does not write `.env` and does not call providers.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_safe_summary(self) -> LocalConfigSummary:
        issues = self.validate_config()
        return LocalConfigSummary(
            provider_type=self.settings.llm_provider,
            model_id=self._model_id(),
            debug_api_enabled=self.settings.enable_debug_api,
            authoring_api_enabled=self.settings.enable_authoring_api,
            eval_api_enabled=self.settings.enable_eval_api,
            playtest_api_enabled=self.settings.enable_playtest_api,
            usage_tracking_enabled=self.settings.enable_usage_tracking,
            database_configured=bool(self.settings.database_url),
            database_path_hint=_database_hint(self.settings.database_url),
            api_key_configured=bool(self.settings.llm_api_key),
            local_paths_redacted={
                "database": _database_hint(self.settings.database_url),
            },
            issues=issues,
        )

    def check_missing_required_config(self) -> list[LocalConfigIssue]:
        issues: list[LocalConfigIssue] = []
        if not self.settings.database_url:
            issues.append(
                LocalConfigIssue(
                    code="database_url_missing",
                    severity="error",
                    message="DATABASE_URL is not configured.",
                    safe_field="database_config",
                )
            )
        return issues

    def check_provider_config(self) -> list[LocalConfigIssue]:
        provider = self.settings.llm_provider.strip().lower()
        issues: list[LocalConfigIssue] = []
        if provider == "openai" and not self.settings.llm_api_key:
            issues.append(
                LocalConfigIssue(
                    code="openai_api_key_missing",
                    severity="warning",
                    message="OpenAI provider is selected, but API key is not configured.",
                    safe_field="provider_config",
                )
            )
        if provider == "local_http" and not self.settings.local_llm_base_url:
            issues.append(
                LocalConfigIssue(
                    code="local_http_base_url_missing",
                    severity="warning",
                    message="local_http provider is selected, but LOCAL_LLM_BASE_URL is not configured.",
                    safe_field="provider_config",
                )
            )
        if provider not in {"mock", "local_stub", "local_http", "openai"}:
            issues.append(
                LocalConfigIssue(
                    code="provider_unknown",
                    severity="error",
                    message=f"Unsupported provider: {provider}",
                    safe_field="provider_config",
                )
            )
        return issues

    def validate_config(self) -> list[LocalConfigIssue]:
        return [*self.check_missing_required_config(), *self.check_provider_config()]

    def generate_env_template(self) -> LocalEnvTemplateResponse:
        template = "\n".join(
            [
                'APP_ENV="local"',
                'DATABASE_URL="sqlite:///./world_engine.db"',
                'LLM_PROVIDER="mock"',
                f'LLM_MODEL="{_safe_template_value(self.settings.llm_model, default="gpt-4.1-mini")}"',
                'LLM_API_KEY=""',
                'LOCAL_LLM_BASE_URL=""',
                f'LOCAL_LLM_MODEL="{_safe_template_value(self.settings.local_llm_model, default="local-model")}"',
                f'LOCAL_LLM_TIMEOUT_SECONDS="{self.settings.local_llm_timeout_seconds:g}"',
                f'LOCAL_LLM_JSON_MODE="{str(self.settings.local_llm_json_mode).lower()}"',
                f'ENABLE_DEBUG_API="{str(self.settings.enable_debug_api).lower()}"',
                f'ENABLE_AUTHORING_API="{str(self.settings.enable_authoring_api).lower()}"',
                f'ENABLE_EVAL_API="{str(self.settings.enable_eval_api).lower()}"',
                f'ENABLE_PLAYTEST_API="{str(self.settings.enable_playtest_api).lower()}"',
                f'ENABLE_USAGE_TRACKING="{str(self.settings.enable_usage_tracking).lower()}"',
                'VITE_API_BASE_URL="http://127.0.0.1:8000"',
                "",
            ]
        )
        return LocalEnvTemplateResponse(template=template)

    def _model_id(self) -> str:
        provider = self.settings.llm_provider.strip().lower()
        if provider in {"local_http", "local_stub"}:
            return self.settings.local_llm_model
        return self.settings.llm_model


def _database_hint(database_url: str) -> str:
    if not database_url:
        return "not configured"
    if database_url.startswith("sqlite:///") or database_url.startswith("sqlite://"):
        path = Path(database_url.removeprefix("sqlite:///").removeprefix("sqlite://"))
        return f"sqlite local file: {path.name or '[configured]'}"
    return "database configured (redacted)"


def _safe_template_value(value: str, *, default: str) -> str:
    lowered = value.lower()
    if "sk-" in lowered or "api_key" in lowered or "secret" in lowered:
        return default
    return value
