from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from app.config import Settings, get_settings

PromptVariant = Literal["default", "compact", "structured", "local_model"]


class PromptProfileTemperatureOverrides(BaseModel):
    narrator: float | None = Field(default=None, ge=0.0, le=2.0)
    intent_parser: float | None = Field(default=None, ge=0.0, le=2.0)
    memory: float | None = Field(default=None, ge=0.0, le=2.0)


class PromptProfile(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    description: str = ""
    provider_filter: list[str] = Field(default_factory=lambda: ["*"])
    model_filter: list[str] = Field(default_factory=lambda: ["*"])
    narrator_style: str = "clear, concise, grounded in visible facts"
    intent_parser_prompt_variant: PromptVariant = "default"
    narrator_prompt_variant: PromptVariant = "default"
    memory_prompt_variant: PromptVariant = "default"
    temperature_overrides: PromptProfileTemperatureOverrides = Field(
        default_factory=PromptProfileTemperatureOverrides
    )
    max_output_tokens: int | None = Field(default=None, ge=1, le=8192)
    enabled: bool = True

    @field_validator("provider_filter", "model_filter")
    @classmethod
    def validate_filters(cls, values: list[str]) -> list[str]:
        if not values:
            raise ValueError("filters must not be empty")
        for value in values:
            if value != "*" and not _is_safe_filter_value(value):
                raise ValueError(f"unsafe filter value: {value}")
        return values

    @model_validator(mode="after")
    def validate_security_boundary(self) -> "PromptProfile":
        forbidden_text = " ".join(
            [
                self.narrator_style,
                self.intent_parser_prompt_variant,
                self.narrator_prompt_variant,
                self.memory_prompt_variant,
            ]
        ).lower()
        forbidden_terms = [
            "hidden fact",
            "hidden_facts",
            "npc secret",
            "raw gamestate",
            "raw state_delta",
            "raw state_deltas",
            "modify gamestate",
            "write gamestate",
        ]
        for term in forbidden_terms:
            if term in forbidden_text:
                raise ValueError("Prompt profiles cannot weaken visibility or GameState boundaries")
        return self


class PromptProfileStore:
    def __init__(
        self,
        profiles: list[PromptProfile] | None = None,
        *,
        selected_profile_id: str | None = None,
    ) -> None:
        self._profiles: dict[str, PromptProfile] = {}
        for profile in profiles or default_prompt_profiles():
            self.validate_profile(profile)
            self._profiles[profile.id] = profile
        configured_profile = selected_profile_id or get_settings().prompt_profile_id
        self._selected_profile_id = configured_profile if configured_profile in self._profiles else "default_safe"

    def list_profiles(self) -> list[PromptProfile]:
        return sorted(self._profiles.values(), key=lambda profile: profile.id)

    def get_profile(self, profile_id: str) -> PromptProfile:
        if profile_id not in self._profiles:
            raise ValueError(f"Prompt profile not found: {profile_id}")
        return self._profiles[profile_id]

    def get_selected_profile(self) -> PromptProfile:
        return self.get_profile(self._selected_profile_id)

    def select_profile(self, profile_id: str) -> PromptProfile:
        profile = self.get_profile(profile_id)
        if not profile.enabled:
            raise ValueError(f"Prompt profile is disabled: {profile_id}")
        self._selected_profile_id = profile.id
        return profile

    def validate_profile(self, profile: PromptProfile | dict[str, object]) -> PromptProfile:
        try:
            candidate = profile if isinstance(profile, PromptProfile) else PromptProfile.model_validate(profile)
        except ValidationError as exc:
            raise ValueError(f"Invalid prompt profile: {exc}") from exc
        if not candidate.enabled:
            return candidate
        return candidate

    def selected_profile_id(self) -> str:
        return self._selected_profile_id


def default_prompt_profiles() -> list[PromptProfile]:
    return [
        PromptProfile(
            id="default_safe",
            name="Default Safe",
            description="Neutral local studio profile. Keeps prompts grounded in visible state.",
            provider_filter=["*"],
            model_filter=["*"],
            narrator_style="clear, concise, grounded in visible facts",
            temperature_overrides=PromptProfileTemperatureOverrides(
                narrator=0.7,
                intent_parser=0.0,
                memory=0.2,
            ),
        ),
        PromptProfile(
            id="local_story",
            name="Local Story",
            description="Slightly warmer prose for local_stub/local_http providers.",
            provider_filter=["local_stub", "local_http"],
            model_filter=["*"],
            narrator_style="warm, sensory, concise, never adding facts beyond visible inputs",
            narrator_prompt_variant="local_model",
            temperature_overrides=PromptProfileTemperatureOverrides(narrator=0.6),
        ),
    ]


def profile_matches_settings(profile: PromptProfile, settings: Settings) -> bool:
    provider = settings.llm_provider.strip().lower()
    model = (
        settings.local_llm_model
        if provider.startswith("local")
        else settings.llm_model
    ).strip().lower()
    return _matches_filter(provider, profile.provider_filter) and _matches_filter(model, profile.model_filter)


_DEFAULT_STORE: PromptProfileStore | None = None


def get_default_prompt_profile_store() -> PromptProfileStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = PromptProfileStore()
    return _DEFAULT_STORE


def set_default_prompt_profile_store(store: PromptProfileStore) -> None:
    global _DEFAULT_STORE
    _DEFAULT_STORE = store


def _matches_filter(value: str, filters: list[str]) -> bool:
    normalized = value.lower()
    return "*" in filters or normalized in {item.lower() for item in filters}


def _is_safe_filter_value(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-", ".", ":"} for character in value)
