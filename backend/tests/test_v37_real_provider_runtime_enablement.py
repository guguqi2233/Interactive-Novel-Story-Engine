from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.desktop.backup_restore import BackupCreateRequest, BackupService
from app.desktop.diagnostics_bundle import DiagnosticsBundleCreateRequest, DiagnosticsBundleService
from app.desktop.local_logs import LocalLogService
from app.llm.local_provider import LocalStubProvider
from app.llm.openai_compatible_provider import OpenAICompatibleProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.provider_base import LLMProviderError
from app.llm.provider_connection_test import HTTPProviderConnectionTestClient, ProviderConnectionTestRequest, test_provider_connection_safe as run_provider_connection_safe
from app.llm.provider_factory import create_llm_provider
from app.llm.provider_gateway import project_provider_gateway_from_project
from app.llm.provider_model_assignment import (
    ProviderModelAssignmentRepository,
    validate_provider_model_assignments,
)
from app.llm.provider_model_discovery import HTTPProviderModelDiscoveryClient, ProviderModelFetchRequest, ProviderModelSyncRequest, fetch_provider_models_safe, sync_provider_models_safe
from app.llm.provider_profiles import (
    FakeProviderSecretResolver,
    ModelProfile,
    ProviderProfileRepository,
    ProviderProfileV2,
    ProviderSecretResolver,
)
from app.llm.provider_router import ProviderRoutingConfig, ProviderRoutingContext, ProviderRoutingRule
from app.llm.schemas import PlayerIntent
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.novel_studio import NovelDraftGenerationService, NovelPromptContext
from app.platform.project_repository import ProjectRepository
from app.platform.tavern_studio import TavernPromptContext, TavernResponseGenerationService


LOCAL_SECRET = "sk-test-v37-local-secret-runtime"
TRANSIENT_KEY = "sk-test-v37-transient-runtime"
PRODUCTION_LIKE_SECRET_PLACEHOLDER = "sk-live-placeholder-not-real-do-not-use-1234567890"


def _write_local_secret(base_dir: Path, ref: str, value: str = LOCAL_SECRET) -> None:
    target = base_dir.joinpath(*ref.split("/")).with_suffix(".secret")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def _profile(**updates: Any) -> ProviderProfileV2:
    payload: dict[str, Any] = {
        "provider_profile_id": "compat",
        "display_name": "Compatible",
        "provider_type": "openai_compatible",
        "base_url": "http://compatible.local/v1",
        "local_secret_ref": "providers/compat",
        "model_profiles": [ModelProfile(model_id="compat-model", supports_json=True)],
    }
    payload.update(updates)
    return ProviderProfileV2.model_validate(payload)


def _project_repo(tmp_path: Path) -> ProjectRepository:
    root = tmp_path / "projects"
    project_root = root / "demo"
    repo = ProjectRepository(root)
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    return repo


def test_fake_provider_generation_still_works_without_network() -> None:
    provider = create_llm_provider(Settings(llm_provider="local_stub"))

    assert isinstance(provider, LocalStubProvider)
    assert provider.generate_text([{"role": "user", "content": "hello"}]) == "local stub text"


def test_local_secret_ref_resolves_outside_project_and_safe_outputs_exclude_value(tmp_path: Path) -> None:
    secret_dir = tmp_path / "outside_project_secrets"
    _write_local_secret(secret_dir, "providers/compat")
    resolver = ProviderSecretResolver(local_secret_dir=secret_dir)
    project_root = tmp_path / "projects" / "demo"
    project_root.mkdir(parents=True)
    profile = _profile()

    saved = ProviderProfileRepository(project_root).save_provider_profile(profile)
    backup_plan = BackupService(project_root).create_backup_plan(BackupCreateRequest(project_id="demo"))
    diagnostics = DiagnosticsBundleService(project_root).preview_bundle(DiagnosticsBundleCreateRequest(project_id="demo"))
    profile_text = (project_root / "providers" / "profiles" / "compat.yaml").read_text(encoding="utf-8")
    rendered = json.dumps(
        {
            "summary": saved.safe_summary(),
            "backup": backup_plan.model_dump(mode="json"),
            "diagnostics": diagnostics.model_dump(mode="json"),
        },
        ensure_ascii=False,
    )

    assert resolver.resolve_api_key(profile) == LOCAL_SECRET
    assert LOCAL_SECRET not in profile_text
    assert LOCAL_SECRET not in rendered
    assert "local provider secret store" in rendered
    assert saved.safe_summary()["local_secret_ref"] == "[configured]"
    assert saved.safe_summary()["local_secret_ref_configured"] is True


def test_missing_local_secret_returns_missing_secret_without_ref_or_value(tmp_path: Path) -> None:
    profile = _profile(provider_profile_id="missing")
    status = run_provider_connection_safe(
        profile,
        ProviderConnectionTestRequest(provider_type="openai_compatible", base_url=profile.base_url),
        secret_resolver=ProviderSecretResolver(local_secret_dir=tmp_path / "secrets"),
    )

    assert status.status == "missing_secret"
    assert status.error_type == "missing_secret"
    assert "providers/compat" not in status.safe_message
    assert "sk-" not in status.safe_message


def test_openai_compatible_real_runtime_path_is_injectable_without_network(tmp_path: Path) -> None:
    secret_dir = tmp_path / "secrets"
    _write_local_secret(secret_dir, "providers/compat")
    seen: dict[str, object] = {}

    def transport(url: str, payload: dict[str, object], timeout: float, headers: dict[str, str]) -> dict[str, object]:
        seen.update({"url": url, "payload": payload, "timeout": timeout, "headers": headers})
        return {"choices": [{"message": {"content": "real path via injected transport"}}]}

    provider = OpenAICompatibleProvider(_profile(), secret_resolver=ProviderSecretResolver(local_secret_dir=secret_dir), transport=transport)
    text = provider.generate_text([{"role": "user", "content": "hello"}])

    assert text == "real path via injected transport"
    assert seen["url"] == "http://compatible.local/v1/chat/completions"
    assert seen["headers"]["Authorization"] == f"Bearer {LOCAL_SECRET}"  # type: ignore[index]
    assert LOCAL_SECRET not in json.dumps(provider.safe_summary(), ensure_ascii=False)


def test_openai_profile_runtime_uses_resolver_and_injected_client() -> None:
    profile = ProviderProfileV2(
        provider_profile_id="openai_profile",
        display_name="OpenAI Profile",
        provider_type="openai",
        api_key_env="OPENAI_API_KEY",
        model_profiles=[ModelProfile(model_id="gpt-test")],
    )
    seen: dict[str, object] = {}

    class _Responses:
        def create(self, **kwargs: object) -> object:
            seen.update(kwargs)
            return type("Response", (), {"output_text": "hello from injected openai"})()

    def client_factory(**kwargs: object) -> object:
        seen["client_kwargs"] = kwargs
        return type("Client", (), {"responses": _Responses()})()

    provider = OpenAIProvider(profile=profile, secret_resolver=FakeProviderSecretResolver({"OPENAI_API_KEY": LOCAL_SECRET}), client_factory=client_factory)

    assert provider.generate_text([{"role": "user", "content": "hi"}]) == "hello from injected openai"
    assert seen["client_kwargs"] == {"api_key": LOCAL_SECRET}
    assert seen["model"] == "gpt-test"


def test_real_connection_and_model_fetch_clients_are_injectable_and_redacted() -> None:
    calls: list[tuple[str, dict[str, str]]] = []

    def transport(url: str, timeout: float, headers: dict[str, str]) -> tuple[int, str]:
        calls.append((url, dict(headers)))
        return 200, json.dumps({"data": [{"id": "remote-model", "supports_json": True}]})

    profile = _profile(api_key_env="OPENAI_API_KEY", local_secret_ref=None)
    resolver = FakeProviderSecretResolver({"OPENAI_API_KEY": LOCAL_SECRET})
    connection = HTTPProviderConnectionTestClient(transport=transport)
    discovery = HTTPProviderModelDiscoveryClient(secret_resolver=resolver, transport=transport)
    request = ProviderModelFetchRequest(
        provider_profile_id="compat",
        provider_type="openai_compatible",
        api_key_env="OPENAI_API_KEY",
        base_url="http://compatible.local/v1",
        allow_real_provider=True,
    )
    report = fetch_provider_models_safe(profile, request, client=discovery, secret_resolver=resolver, connection_client=connection)

    assert report.status == "ok"
    assert [model.model_id for model in report.models] == ["remote-model"]
    assert all(headers.get("Authorization") == f"Bearer {LOCAL_SECRET}" for _url, headers in calls)
    assert LOCAL_SECRET not in report.model_dump_json()


def test_default_connection_and_model_fetch_paths_use_fake_clients_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked_http_connection(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("real HTTP connection client must not be used in tests")

    def blocked_http_model_fetch(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("real HTTP model discovery client must not be used in tests")

    monkeypatch.setattr(HTTPProviderConnectionTestClient, "test_connection", blocked_http_connection)
    monkeypatch.setattr(HTTPProviderModelDiscoveryClient, "fetch_models", blocked_http_model_fetch)
    profile = _profile(api_key_env="OPENAI_API_KEY", local_secret_ref=None)
    resolver = FakeProviderSecretResolver({"OPENAI_API_KEY": LOCAL_SECRET})

    status = run_provider_connection_safe(
        profile,
        ProviderConnectionTestRequest(
            provider_profile_id=profile.provider_profile_id,
            provider_type="openai_compatible",
            base_url=profile.base_url,
            api_key_env="OPENAI_API_KEY",
            allow_real_connection=False,
        ),
        secret_resolver=resolver,
    )
    report = fetch_provider_models_safe(
        profile,
        ProviderModelFetchRequest(
            provider_profile_id=profile.provider_profile_id,
            provider_type="openai_compatible",
            base_url=profile.base_url,
            api_key_env="OPENAI_API_KEY",
            allow_real_provider=False,
        ),
        secret_resolver=resolver,
    )

    assert status.status == "connected"
    assert report.status == "ok"
    assert [model.model_id for model in report.models] == ["fake-chat-small", "fake-json-pro"]
    assert LOCAL_SECRET not in status.model_dump_json()
    assert LOCAL_SECRET not in report.model_dump_json()


def test_auth_failed_and_raw_provider_errors_are_redacted() -> None:
    profile = _profile(provider_profile_id="raw-secret-error", base_url="http://raw-secret-error.local/v1", local_secret_ref=None, requires_api_key=True)
    status = run_provider_connection_safe(
        profile,
        ProviderConnectionTestRequest(
            provider_profile_id=profile.provider_profile_id,
            provider_type="openai_compatible",
            base_url=profile.base_url,
            transient_api_key=TRANSIENT_KEY,
        ),
    )

    assert status.status == "auth_failed"
    assert status.error_type == "auth_failed"
    rendered = status.model_dump_json()
    assert TRANSIENT_KEY not in rendered
    assert "sk-test-raw-provider-secret" not in rendered
    assert "sk-test-query-secret" not in rendered
    assert "relay-token-secret-value" not in rendered
    assert "Bearer sk-" not in rendered
    assert status.redaction_applied is True


def test_provider_profile_rejects_raw_api_key_fields_and_secret_values() -> None:
    with pytest.raises(ValueError):
        ProviderProfileV2.model_validate(
            {
                "provider_profile_id": "bad_key",
                "display_name": "Bad Key",
                "provider_type": "openai",
                "api_key": PRODUCTION_LIKE_SECRET_PLACEHOLDER,
            }
        )
    with pytest.raises(ValueError):
        ProviderProfileV2.model_validate(
            {
                "provider_profile_id": "bad_notes",
                "display_name": "Bad Notes",
                "provider_type": "openai_compatible",
                "base_url": "http://compatible.local/v1",
                "provider_notes": f"debug note {PRODUCTION_LIKE_SECRET_PLACEHOLDER}",
            }
        )


def test_api_logs_diagnostics_backup_and_export_surfaces_do_not_include_provider_keys(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    profile = _profile(provider_profile_id="safe_export", local_secret_ref="providers/compat")
    saved = ProviderProfileRepository(project_root).save_provider_profile(profile)
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "backend.log").write_text(
        f"ERROR Authorization: Bearer {LOCAL_SECRET} transient_api_key={TRANSIENT_KEY} api_key={LOCAL_SECRET}",
        encoding="utf-8",
    )

    logs = LocalLogService(tmp_path).list_safe_logs()
    diagnostics = DiagnosticsBundleService(tmp_path).preview_bundle(DiagnosticsBundleCreateRequest(project_id="demo"))
    backup = BackupService(project_root).create_backup_plan(BackupCreateRequest(project_id="demo"))
    frontend_response = {"local_only": True, "provider": saved.safe_summary(), "models": [model.safe_summary() for model in saved.model_profiles]}
    export_preview = {"local_only": True, "provider_safe_summary": saved.safe_summary(), "excluded": ["API key", "provider secrets", "transient_api_key"]}
    rendered = json.dumps(
        {
            "profile_file": (project_root / "providers" / "profiles" / "safe_export.yaml").read_text(encoding="utf-8"),
            "frontend_response": frontend_response,
            "logs": logs.model_dump(mode="json"),
            "diagnostics": diagnostics.model_dump(mode="json"),
            "backup": backup.model_dump(mode="json"),
            "export_preview": export_preview,
        },
        ensure_ascii=False,
    )

    assert saved.safe_summary()["local_secret_ref"] == "[configured]"
    assert LOCAL_SECRET not in rendered
    assert TRANSIENT_KEY not in rendered
    assert "Authorization: Bearer" not in rendered
    assert "local_secret_ref: providers/compat" in rendered  # stored metadata may keep the safe ref, never the key value
    assert any(entry.redacted for entry in logs.logs)
    assert diagnostics.local_only is True
    assert backup.local_only is True


def test_fake_model_sync_and_assignment_work_without_secrets(tmp_path: Path) -> None:
    profile = _profile(provider_profile_id="assignable", api_key_env="OPENAI_API_KEY", local_secret_ref=None, model_profiles=[])
    resolver = FakeProviderSecretResolver({"OPENAI_API_KEY": LOCAL_SECRET})
    synced_profile, report = sync_provider_models_safe(
        profile,
        ProviderModelSyncRequest(
            provider_profile_id="assignable",
            provider_type="openai_compatible",
            base_url=profile.base_url,
            api_key_env="OPENAI_API_KEY",
            allow_real_provider=False,
        ),
        secret_resolver=resolver,
    )
    config = ProviderRoutingConfig(
        rules=[
            ProviderRoutingRule(use_case="novel_draft", primary_provider_id="assignable", primary_model_id="fake-chat-small"),
            ProviderRoutingRule(use_case="tavern_reply", primary_provider_id="assignable", primary_model_id="fake-chat-small"),
            ProviderRoutingRule(use_case="world_intent_parse", primary_provider_id="assignable", primary_model_id="fake-json-pro", require_json_support=True),
            ProviderRoutingRule(use_case="world_narration", primary_provider_id="assignable", primary_model_id="fake-chat-small"),
        ]
    )
    ProviderProfileRepository(tmp_path).save_provider_profile(synced_profile)
    saved = ProviderModelAssignmentRepository(tmp_path).save(config)
    validation = validate_provider_model_assignments(saved, [synced_profile])

    assert report.status == "ok"
    assert {model.model_id for model in synced_profile.model_profiles} == {"fake-chat-small", "fake-json-pro"}
    assert len(saved.rules) == 4
    assert not validation.warnings
    assert all(item["ok"] is True for item in validation.validation_reports)
    assert LOCAL_SECRET not in report.model_dump_json()
    assert LOCAL_SECRET not in validation.model_dump_json()
    assert LOCAL_SECRET not in (tmp_path / "providers" / "model_assignments.yaml").read_text(encoding="utf-8")


def test_world_novel_and_tavern_use_assigned_provider_gateway_routes_without_game_state_mutation(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    profile = _profile(provider_profile_id="compat_gateway", model_profiles=[ModelProfile(model_id="compat-model", supports_json=True, recommended_use_cases=["novel", "tavern", "world"])])
    ProviderProfileRepository(project_root).save_provider_profile(profile)
    ProviderModelAssignmentRepository(project_root).save(
        ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(use_case="world_intent_parse", primary_provider_id="compat_gateway", primary_model_id="compat-model", require_json_support=True),
                ProviderRoutingRule(use_case="world_narration", primary_provider_id="compat_gateway", primary_model_id="compat-model"),
                ProviderRoutingRule(use_case="novel_draft", primary_provider_id="compat_gateway", primary_model_id="compat-model"),
                ProviderRoutingRule(use_case="tavern_reply", primary_provider_id="compat_gateway", primary_model_id="compat-model"),
            ]
        )
    )
    calls: list[dict[str, object]] = []

    def transport(url: str, payload: dict[str, object], timeout: float, headers: dict[str, str]) -> dict[str, object]:
        calls.append({"url": url, "payload": payload, "headers": dict(headers)})
        messages = json.dumps(payload.get("messages", []), ensure_ascii=False).lower()
        if payload.get("response_format"):
            if "tavern rp" in messages:
                content = {"content": "Safe routed Tavern reply.", "speaker_id": "mira"}
            elif "novel" in messages:
                content = {"text": "Safe routed novel draft.", "summary": "safe"}
            else:
                content = {"action_type": "observe", "raw_text": "look", "confidence": 0.9, "requires_clarification": False}
        else:
            content = "Safe routed world narration."
        return {"choices": [{"message": {"content": json.dumps(content) if isinstance(content, dict) else content}}]}

    gateway = project_provider_gateway_from_project(
        str(project_root),
        secret_resolver=FakeProviderSecretResolver({"providers/compat": LOCAL_SECRET}),
        openai_compatible_transport=transport,
    )

    intent = gateway.generate_json(
        context=ProviderRoutingContext(mode="world", use_case="world_intent_parse"),
        messages=[{"role": "user", "content": "look"}],
        schema=PlayerIntent,
    )
    narration = gateway.generate_text(
        context=ProviderRoutingContext(mode="world", use_case="world_narration"),
        messages=[{"role": "user", "content": "visible result only"}],
    )
    novel = NovelDraftGenerationService(gateway.provider_for(ProviderRoutingContext(mode="novel", use_case="novel_draft"))).generate_scene_draft(
        NovelPromptContext(project_id="demo", manuscript_id="manuscript", scene_summary="visible scene only")
    )
    tavern = TavernResponseGenerationService(gateway.provider_for(ProviderRoutingContext(mode="tavern", use_case="tavern_reply"))).generate_character_reply(
        TavernPromptContext(project_id="demo", session_id="session", character_id="mira", current_speaker_safe_profile={"name": "Mira"})
    )
    rendered = json.dumps({"calls": calls, "traces": [trace.safe_summary() for trace in gateway.traces]}, ensure_ascii=False)

    assert intent.action_type.value == "observe"
    assert narration == "Safe routed world narration."
    assert novel.text == "Safe routed novel draft."
    assert tavern.content == "Safe routed Tavern reply."
    assert [trace.use_case for trace in gateway.traces] == ["world_intent_parse", "world_narration", "novel_draft", "tavern_reply"]
    assert all(call["payload"]["model"] == "compat-model" for call in calls)  # type: ignore[index]
    assert "state_delta" not in rendered.lower()
    assert LOCAL_SECRET not in json.dumps([trace.safe_summary() for trace in gateway.traces], ensure_ascii=False)


def test_transient_key_and_local_secret_ref_are_not_persisted_or_cached(tmp_path: Path) -> None:
    repo = _project_repo(tmp_path)
    previous_repo = getattr(app.state, "project_repository", None)
    previous_settings = getattr(app.state, "settings", None)
    app.state.project_repository = repo
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)
    try:
        created = client.post(
            "/projects/demo/providers",
            json=_profile(provider_profile_id="relay_safe", display_name="Relay Safe", provider_type="relay", base_url="http://relay.local/v1").model_dump(mode="json"),
        )
        tested = client.post(
            "/projects/demo/providers/test-connection",
            json={"provider_profile_id": "relay_safe", "transient_api_key": TRANSIENT_KEY, "timeout_seconds": 1},
        )
        health = client.get("/projects/demo/providers/health")
        project_root = Path(repo.load_project("demo").project_root)
        profile_text = (project_root / "providers" / "profiles" / "relay_safe.yaml").read_text(encoding="utf-8")
        cache_text = (project_root / "providers" / "connection_status_cache.json").read_text(encoding="utf-8")
    finally:
        if previous_repo is None:
            if hasattr(app.state, "project_repository"):
                delattr(app.state, "project_repository")
        else:
            app.state.project_repository = previous_repo
        app.state.settings = previous_settings or Settings(llm_provider="mock")

    assert created.status_code == 200
    assert tested.status_code == 200
    assert health.status_code == 200
    combined = created.text + tested.text + health.text + profile_text + cache_text
    assert TRANSIENT_KEY not in combined
    assert LOCAL_SECRET not in combined
    assert "transient_api_key" not in profile_text
    assert "Authorization" not in combined
    assert '"local_secret_ref":"[configured]"' in health.text


def test_project_provider_gateway_uses_project_profiles_and_assignment_without_network(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    profile = _profile(provider_profile_id="compat_gateway")
    ProviderProfileRepository(project_root).save_provider_profile(profile)
    ProviderModelAssignmentRepository(project_root).save(
        ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case="world_intent_parse",
                    primary_provider_id="compat_gateway",
                    primary_model_id="compat-model",
                    require_json_support=True,
                )
            ]
        )
    )

    def transport(url: str, payload: dict[str, object], timeout: float, headers: dict[str, str]) -> dict[str, object]:
        return {"choices": [{"message": {"content": json.dumps({"action_type": "observe", "raw_text": "look", "confidence": 0.9, "requires_clarification": False})}}]}

    gateway = project_provider_gateway_from_project(
        str(project_root),
        secret_resolver=FakeProviderSecretResolver({"providers/compat": LOCAL_SECRET}),
        openai_compatible_transport=transport,
    )
    parsed = gateway.generate_json(
        context=ProviderRoutingContext(mode="world", use_case="world_intent_parse"),
        messages=[{"role": "user", "content": "look"}],
        schema=PlayerIntent,
    )

    assert parsed.action_type.value == "observe"
    assert LOCAL_SECRET not in json.dumps([trace.safe_summary() for trace in gateway.traces], ensure_ascii=False)


def test_provider_runtime_missing_secret_fails_closed_without_network() -> None:
    try:
        create_llm_provider(
            Settings(llm_provider="openai_compatible"),
            provider_profile=_profile(api_key_env="MISSING_RUNTIME_SECRET", local_secret_ref=None),
            openai_compatible_transport=lambda *_args: {"choices": [{"message": {"content": "should not run"}}]},
        )
    except LLMProviderError as exc:
        assert "Missing provider secret" in str(exc)
    else:
        raise AssertionError("missing secret should fail before transport is available")
