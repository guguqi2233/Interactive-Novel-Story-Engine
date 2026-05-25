from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.provider_connection_test import HTTPProviderConnectionTestClient
from app.llm.provider_model_assignment import MODEL_ASSIGNMENT_USE_CASES
from app.llm.provider_model_discovery import HTTPProviderModelDiscoveryClient
from app.llm.provider_router import JSON_ROUTING_USE_CASES
from app.main import app
from app.platform.project_repository import ProjectRepository


SECRET_LIKE_RE = re.compile(
    r"sk-(?!test-|fake-|redacted-|placeholder-)[A-Za-z0-9_-]{12,}|authorization\s*[:=]\s*bearer\s+(?!\[?redacted\]?\b)\S+|BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY",
    re.IGNORECASE,
)


def _client(tmp_path: Path) -> tuple[TestClient, object, object]:
    previous_repo = getattr(app.state, "project_repository", None)
    previous_settings = getattr(app.state, "settings", None)
    app.state.project_repository = ProjectRepository(tmp_path / "projects_index")
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock")
    return TestClient(app), previous_repo, previous_settings


def _restore(previous_repo: object, previous_settings: object) -> None:
    if previous_repo is None:
        if hasattr(app.state, "project_repository"):
            delattr(app.state, "project_repository")
    else:
        app.state.project_repository = previous_repo
    app.state.settings = previous_settings or Settings(llm_provider="mock")


def _assert_safe_response(*payloads: str) -> None:
    joined = "\n".join(payloads)
    assert not SECRET_LIKE_RE.search(joined)
    lowered = joined.lower()
    for token in (
        "transient_api_key",
        "authorization: bearer",
        "raw_provider_response",
        "raw_prompt",
        "raw_output",
        "raw_state_delta",
        "hidden_fact_text",
        "npc_secret",
    ):
        assert token not in lowered


def _rules_for_all_core_product_modes(provider_id: str, model_id: str) -> list[dict[str, Any]]:
    return [
        {
            "use_case": str(use_case),
            "primary_provider_id": provider_id,
            "primary_model_id": model_id,
            "require_json_support": use_case in JSON_ROUTING_USE_CASES,
            "require_local_only": False,
            "enabled": True,
        }
        for use_case in MODEL_ASSIGNMENT_USE_CASES
    ]


def test_v37_chinese_local_product_e2e_path_uses_fake_provider_and_safe_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def blocked_real_connection(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("v3.7 product E2E tests must not open a real provider connection")

    def blocked_real_model_fetch(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("v3.7 product E2E tests must not fetch models from a real provider")

    monkeypatch.setattr(HTTPProviderConnectionTestClient, "test_connection", blocked_real_connection)
    monkeypatch.setattr(HTTPProviderModelDiscoveryClient, "fetch_models", blocked_real_model_fetch)

    client, previous_repo, previous_settings = _client(tmp_path)
    responses: list[str] = []
    project_root = tmp_path / "projects_index" / "demo_product_project"
    try:
        created = client.post(
            "/projects",
            json={
                "project_id": "demo_product",
                "name": "中文本地体验项目",
                "project_root": str(project_root),
                "default_world_id": "mist_valley",
            },
        )
        responses.append(created.text)
        assert created.status_code == 200
        assert created.json()["project"]["project_id"] == "demo_product"

        listed = client.get("/projects")
        responses.append(listed.text)
        assert listed.status_code == 200
        assert any(item["project_id"] == "demo_product" for item in listed.json()["projects"])

        provider_payload = {
            "provider_profile_id": "fake_playable_provider",
            "display_name": "Fake Playable Provider",
            "provider_type": "openai_compatible",
            "base_url": "http://fake-provider.local/v1",
            "requires_api_key": False,
            "model_profiles": [],
        }
        provider_created = client.post("/projects/demo_product/providers", json=provider_payload)
        responses.append(provider_created.text)
        assert provider_created.status_code == 200
        provider_summary = provider_created.json()["provider"]
        assert provider_summary["provider_profile_id"] == "fake_playable_provider"
        assert provider_summary["api_key_env"] is None
        assert provider_summary["secret_ref"] is None

        connection = client.post(
            "/projects/demo_product/providers/test-connection",
            json={
                "provider_profile_id": "fake_playable_provider",
                "provider_type": "openai_compatible",
                "base_url": "http://fake-provider.local/v1",
                "allow_real_connection": False,
            },
        )
        responses.append(connection.text)
        assert connection.status_code == 200
        assert connection.json()["status"] == "connected"

        fetched = client.post(
            "/projects/demo_product/providers/fetch-models",
            json={
                "provider_profile_id": "fake_playable_provider",
                "provider_type": "openai_compatible",
                "base_url": "http://fake-provider.local/v1",
                "allow_real_provider": False,
            },
        )
        responses.append(fetched.text)
        assert fetched.status_code == 200
        fetched_models = fetched.json()["report"]["models"]
        assert {model["model_id"] for model in fetched_models} == {"fake-chat-small", "fake-json-pro"}

        synced = client.post(
            "/projects/demo_product/providers/sync-models",
            json={
                "provider_profile_id": "fake_playable_provider",
                "provider_type": "openai_compatible",
                "base_url": "http://fake-provider.local/v1",
                "allow_real_provider": False,
            },
        )
        responses.append(synced.text)
        assert synced.status_code == 200
        assert synced.json()["report"]["status"] == "ok"

        saved_assignment = client.post(
            "/projects/demo_product/providers/model-assignments/save",
            json={"rules": _rules_for_all_core_product_modes("fake_playable_provider", "fake-json-pro")},
        )
        responses.append(saved_assignment.text)
        assert saved_assignment.status_code == 200
        assignment_payload = saved_assignment.json()
        assert not assignment_payload["warnings"]
        assert {rule["use_case"] for rule in assignment_payload["rules"]} >= {
            "novel_draft",
            "tavern_reply",
            "world_intent_parse",
            "world_narration",
            "cross_mode_draft",
            "quality_eval",
        }

        setup_checklist = client.get("/projects/demo_product/providers/setup-checklist")
        responses.append(setup_checklist.text)
        assert setup_checklist.status_code == 200
        assert setup_checklist.json()["overall_status"] in {"pass", "warning"}

        modes = client.get("/projects/demo_product/modes")
        responses.append(modes.text)
        assert modes.status_code == 200
        mode_ids = {item["mode"] for item in modes.json()["modes"]}
        assert {"novel", "tavern", "world"} <= mode_ids

        world_start = client.post("/projects/demo_product/world/start", json={"world_id": "mist_valley"})
        responses.append(world_start.text)
        assert world_start.status_code == 200
        world_payload = world_start.json()
        assert world_payload["world_id"] == "mist_valley"
        assert "visible_state" in world_payload
        assert "state_deltas" not in world_payload

        workflow = client.get("/projects/demo_product/workflow-check")
        responses.append(workflow.text)
        assert workflow.status_code == 200
        assert workflow.json()["privacy_boundaries_pass"] is True
    finally:
        _restore(previous_repo, previous_settings)

    assert (project_root / "providers" / "profiles" / "fake_playable_provider.yaml").exists()
    _assert_safe_response(*responses)
    saved_profile_text = (project_root / "providers" / "profiles" / "fake_playable_provider.yaml").read_text(encoding="utf-8")
    assert not re.search(r"(?m)^api_key\s*:", saved_profile_text)
    assert "transient_api_key" not in saved_profile_text
