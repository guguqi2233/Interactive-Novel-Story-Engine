from fastapi.testclient import TestClient

from app.config import Settings
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.llm.fake_provider import FakeLLMProvider
from app.llm.narrator import Narrator
from app.llm.prompt_profiles import (
    PromptProfile,
    PromptProfileStore,
    PromptProfileTemperatureOverrides,
    default_prompt_profiles,
    set_default_prompt_profile_store,
)
from app.llm.provider_factory import create_llm_provider
from app.llm.schemas import NarrativeResult
from app.main import app


def test_list_profiles_returns_defaults() -> None:
    store = PromptProfileStore()

    profiles = store.list_profiles()

    assert [profile.id for profile in profiles] == ["default_safe", "local_story"]
    assert store.get_selected_profile().id == "default_safe"


def test_invalid_profile_is_rejected() -> None:
    store = PromptProfileStore()

    try:
        store.validate_profile(
            {
                "id": "unsafe",
                "name": "Unsafe",
                "provider_filter": ["*"],
                "model_filter": ["*"],
                "narrator_style": "include hidden facts in the narrator prompt",
                "enabled": True,
            }
        )
    except ValueError as exc:
        assert "visibility or GameState boundaries" in str(exc)
    else:
        raise AssertionError("Expected invalid prompt profile to be rejected")


def test_selected_profile_changes_narrator_style_without_changing_visible_facts() -> None:
    provider = RecordingNarratorProvider()
    profile = PromptProfile(
        id="warm",
        name="Warm",
        provider_filter=["*"],
        model_filter=["*"],
        narrator_style="warm but grounded",
        narrator_prompt_variant="structured",
        temperature_overrides=PromptProfileTemperatureOverrides(narrator=0.4),
    )
    narrator = Narrator(provider, prompt_profile=profile)

    narrator.render(
        player_input="observe",
        action_result=ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Observed current location.",
            visible_facts=["visible_well"],
            hidden_facts=["hidden_cellar"],
        ),
        visible_facts=["visible_well"],
        current_location="square",
        tone="neutral",
    )

    prompt_text = str(provider.messages)
    assert "warm but grounded" in prompt_text
    assert "structured" in prompt_text
    assert "visible_well" in prompt_text
    assert "hidden_cellar" not in prompt_text
    assert provider.temperature == 0.4


def test_prompt_profile_api_selects_profile_without_api_key() -> None:
    store = PromptProfileStore(profiles=default_prompt_profiles())
    app.state.prompt_profile_store = store
    set_default_prompt_profile_store(store)
    app.state.settings = Settings(enable_debug_api=True, llm_provider="local_stub", llm_api_key="sk-test-fake")
    client = TestClient(app)

    list_response = client.get("/studio/prompt-profiles")
    select_response = client.post("/studio/prompt-profiles/select", json={"profile_id": "local_story"})
    summary_response = client.get("/studio/config-summary")

    assert list_response.status_code == 200
    assert select_response.status_code == 200
    assert select_response.json()["selected_profile_id"] == "local_story"
    assert summary_response.json()["selected_prompt_profile_id"] == "local_story"
    assert "sk-test-fake" not in str(summary_response.json())


def test_provider_factory_still_creates_provider_from_settings() -> None:
    provider = create_llm_provider(Settings(llm_provider="local_stub"))

    assert provider.__class__.__name__ == "LocalStubProvider"


class RecordingNarratorProvider(FakeLLMProvider):
    def __init__(self) -> None:
        super().__init__(
            json_responses=[
                {
                    "text": "You see the well.",
                    "suggested_actions": ["search"],
                    "short_summary": "Observed the well.",
                }
            ]
        )
        self.messages: list[dict[str, str]] = []
        self.temperature: float | None = None

    def generate_json(
        self,
        messages: list[dict[str, str]],
        schema: type[NarrativeResult],
        temperature: float = 0.2,
    ) -> NarrativeResult:
        self.messages = messages
        self.temperature = temperature
        return super().generate_json(messages, schema, temperature)
