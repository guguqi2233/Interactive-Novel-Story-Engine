import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.openai_compatible_provider import OpenAICompatibleProvider
from app.llm.provider_base import LLMProviderError
from app.llm.provider_factory import create_llm_provider
from app.llm.provider_profiles import (
    CapabilityDetectionService,
    FakeProviderSecretResolver,
    ModelProfile,
    ProviderProfileRepository,
    ProviderProfileV2,
    ProviderProfileType,
    ProviderSimulationBehavior,
    ProviderSimulationProfile,
    SimulatedProvider,
    build_model_capability_matrix,
)
from app.llm.schemas import PlayerIntent
from app.llm.usage_tracker import ModelUsageRecord, get_model_usage_store
from app.main import app
from app.platform.narrative_project import NarrativeProject
from app.platform.project_repository import ProjectRepository


def setup_function() -> None:
    store = get_model_usage_store()
    store.clear()
    store.enabled = False


def test_provider_profile_v2_rejects_raw_api_key_and_summarizes_safely() -> None:
    profile = ProviderProfileV2(
        provider_profile_id="relay_demo",
        display_name="Relay Demo",
        provider_type=ProviderProfileType.RELAY,
        base_url_env="RELAY_BASE_URL",
        api_key_env="RELAY_API_KEY",
        model_profiles=[ModelProfile(model_id="relay-model", supports_json=True)],
    )

    rendered = json.dumps(profile.safe_summary(), ensure_ascii=False)

    assert "relay-model" in rendered
    assert "sk-" not in rendered
    with pytest.raises(ValueError):
        ProviderProfileV2(provider_profile_id="bad", display_name="Bad", provider_type="mock", api_key="sk-secret")  # type: ignore[call-arg]


def test_provider_profile_repository_roundtrip_and_path_traversal(tmp_path: Path) -> None:
    repo = ProviderProfileRepository(tmp_path)
    profile = ProviderProfileV2(provider_profile_id="local", display_name="Local", provider_type="local_stub", model_profiles=[ModelProfile(model_id="local_stub")])

    repo.create_provider_profile(profile)

    assert repo.load_provider_profile("local").display_name == "Local"
    assert repo.list_safe_summaries()[0]["provider_profile_id"] == "local"
    with pytest.raises(ValueError):
        repo.load_provider_profile("../.env")


def test_openai_compatible_provider_uses_fake_transport_and_validates_schema() -> None:
    seen: dict[str, object] = {}

    def transport(url: str, payload: dict[str, object], timeout: float, headers: dict[str, str]) -> dict[str, object]:
        seen.update({"url": url, "timeout": timeout, "headers": dict(headers)})
        return {"choices": [{"message": {"content": json.dumps({"action_type": "observe", "raw_text": "look", "confidence": 0.9, "requires_clarification": False})}}]}

    profile = ProviderProfileV2(
        provider_profile_id="compat",
        display_name="Compat",
        provider_type="openai_compatible",
        base_url="http://local-compatible.invalid/v1",
        api_key_env="FAKE_KEY",
        model_profiles=[ModelProfile(model_id="compat-model")],
    )
    provider = OpenAICompatibleProvider(profile, secret_resolver=FakeProviderSecretResolver({"FAKE_KEY": "sk-test-fake"}), transport=transport)
    result = provider.generate_json([{"role": "user", "content": "look"}], PlayerIntent)

    assert result.action_type.value == "observe"
    assert seen["url"] == "http://local-compatible.invalid/v1/chat/completions"
    assert "sk-test-fake" in seen["headers"]["Authorization"]  # type: ignore[index]
    assert "sk-test-fake" not in json.dumps(provider.safe_summary())


def test_openai_compatible_provider_missing_base_url_and_secret_are_clear() -> None:
    with pytest.raises(LLMProviderError, match="base_url"):
        OpenAICompatibleProvider(ProviderProfileV2(provider_profile_id="bad", display_name="Bad", provider_type="openai_compatible", api_key_env="FAKE_KEY"))
    with pytest.raises(LLMProviderError, match="Missing provider secret"):
        OpenAICompatibleProvider(ProviderProfileV2(provider_profile_id="bad2", display_name="Bad2", provider_type="relay", base_url="http://relay.invalid", api_key_env="MISSING_FAKE_KEY"))


def test_capability_detection_matrix_and_simulation_provider() -> None:
    profile = ProviderProfileV2(
        provider_profile_id="text_only",
        display_name="Text",
        provider_type="local_stub",
        model_profiles=[ModelProfile(model_id="text", supports_json=False, recommended_use_cases=["novel_draft"])],
    )
    report = CapabilityDetectionService().detect_from_profile(profile)[0]
    checked = CapabilityDetectionService().validate_model_capabilities(report, mode="world", use_case="world_intent_parse")
    matrix = build_model_capability_matrix("demo", [profile])

    assert "use_case_requires_json_support" in checked.errors
    assert matrix.rows[0].warnings

    provider = SimulatedProvider(ProviderSimulationProfile(default_behavior=ProviderSimulationBehavior.SUCCESS_JSON))
    parsed = provider.generate_json([{"role": "user", "content": "look"}], PlayerIntent)
    assert parsed.raw_text == "observe"
    assert provider.traces[0].safe_summary()["success"] is True


def test_simulation_invalid_json_and_safety_rejection_are_clear() -> None:
    invalid = SimulatedProvider(ProviderSimulationProfile(default_behavior=ProviderSimulationBehavior.INVALID_JSON))
    with pytest.raises(LLMProviderError, match="invalid_json"):
        invalid.generate_json([{"role": "user", "content": "x"}], PlayerIntent)
    rejected = SimulatedProvider(ProviderSimulationProfile(default_behavior=ProviderSimulationBehavior.SAFETY_REJECTION))
    with pytest.raises(LLMProviderError, match="safety_rejection"):
        rejected.generate_text([{"role": "user", "content": "x"}])


def test_usage_records_project_mode_and_safe_project_api(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    project_root = root / "demo"
    repo = ProjectRepository(root)
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    app.state.project_repository = repo
    previous_settings = getattr(app.state, "settings", None)
    store = get_model_usage_store()
    store.enabled = True
    store.record(
        ModelUsageRecord(
            project_id="demo",
            provider_id="fake",
            model_id="fake",
            mode="novel",
            use_case="novel_draft",
            duration_ms=1.0,
            input_tokens_estimated=10,
            output_tokens_estimated=5,
            cost_estimated=0.001,
        )
    )
    try:
        app.state.settings = Settings(enable_usage_tracking=True, enable_authoring_api=True, llm_provider="mock")
        client = TestClient(app)
        recent = client.get("/projects/demo/providers/usage/recent")
        summary = client.get("/projects/demo/providers/usage/summary")
        by_mode = client.get("/projects/demo/providers/usage/by-mode")
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")

    assert recent.status_code == 200
    assert summary.json()["total_calls"] == 1
    assert by_mode.json()["by_mode"][0]["key"] == "novel"
    rendered = recent.text + summary.text + by_mode.text
    assert "api_key" not in rendered.lower()
    assert "hidden fact text" not in rendered


def test_provider_factory_supports_openai_compatible_with_fake_transport() -> None:
    def transport(url: str, payload: dict[str, object], timeout: float, headers: dict[str, str]) -> dict[str, object]:
        return {"choices": [{"message": {"content": "compatible text"}}]}

    provider = create_llm_provider(
        Settings(llm_provider="openai_compatible", local_llm_base_url="http://compat.invalid/v1"),
        openai_compatible_transport=transport,
    )

    assert provider.generate_text([{"role": "user", "content": "hello"}]) == "compatible text"

