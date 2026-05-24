from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.llm.provider_capabilities import ModelCapability, ProviderCapability, ProviderCapabilityRegistry, ProviderType
from app.llm.provider_profiles import ModelProfile, ProviderProfileV2
from app.llm.provider_router import (
    JSON_ROUTING_USE_CASES,
    ProviderRouter,
    ProviderRoutingConfig,
    ProviderRoutingRule,
    ProviderRoutingSummary,
    ProviderRoutingUseCase,
)
from app.platform.narrative_project import validate_project_relative_path


MODEL_ASSIGNMENT_USE_CASES = [
    ProviderRoutingUseCase.NOVEL_DRAFT,
    ProviderRoutingUseCase.NOVEL_REWRITE,
    ProviderRoutingUseCase.TAVERN_REPLY,
    ProviderRoutingUseCase.MULTI_NPC_REPLY,
    ProviderRoutingUseCase.WORLD_INTENT_PARSE,
    ProviderRoutingUseCase.WORLD_NARRATION,
    ProviderRoutingUseCase.MEMORY_SUMMARY,
    ProviderRoutingUseCase.CROSS_MODE_DRAFT,
    ProviderRoutingUseCase.STRUCTURED_JSON,
    ProviderRoutingUseCase.QUALITY_EVAL,
    ProviderRoutingUseCase.CHEAP_SUMMARY,
]


class ProviderModelAssignmentRepository:
    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root).resolve()
        safe = validate_project_relative_path("providers/model_assignments.yaml")
        self.path = (self.project_root / safe).resolve()
        if self.project_root not in self.path.parents:
            raise ValueError("Provider assignment path escaped project root")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> ProviderRoutingConfig:
        if not self.path.exists():
            return ProviderRoutingConfig()
        return ProviderRoutingConfig.model_validate(yaml.safe_load(self.path.read_text(encoding="utf-8")) or {})

    def save(self, config: ProviderRoutingConfig) -> ProviderRoutingConfig:
        self.path.write_text(yaml.safe_dump(config.model_dump(mode="json"), sort_keys=True, allow_unicode=True), encoding="utf-8")
        return config


class ProviderModelAssignmentSummary(BaseModel):
    local_only: bool = True
    supported_use_cases: list[str] = Field(default_factory=lambda: [str(item) for item in MODEL_ASSIGNMENT_USE_CASES])
    rules: list[ProviderRoutingRule] = Field(default_factory=list)
    validation_reports: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    fallback_chains: dict[str, list[str]] = Field(default_factory=dict)


def build_project_provider_registry(profiles: list[ProviderProfileV2]) -> ProviderCapabilityRegistry:
    providers: list[ProviderCapability] = []
    models: list[ModelCapability] = []
    for profile in profiles:
        provider_type = _provider_type_for_registry(str(profile.provider_type))
        local_only = str(profile.provider_type) in {"mock", "local_stub", "local_http"}
        providers.append(
            ProviderCapability(
                provider_id=profile.provider_profile_id,
                provider_type=provider_type,
                supports_text=True,
                supports_json=any(model.supports_json for model in profile.model_profiles) if profile.model_profiles else True,
                supports_streaming=any(model.supports_streaming for model in profile.model_profiles),
                supports_tools=any(model.supports_tools for model in profile.model_profiles),
                recommended_use_cases=_profile_use_cases(profile),
                requires_api_key=profile.key_required(),
                local_only=local_only,
                notes="Project-local provider profile metadata only.",
            )
        )
        source_models = profile.model_profiles or [
            ModelProfile(model_id=profile.primary_model_id(), display_name=profile.primary_model_id(), provider_profile_id=profile.provider_profile_id)
        ]
        for model in source_models:
            models.append(
                ModelCapability(
                    provider_id=profile.provider_profile_id,
                    provider_type=provider_type,
                    model_id=model.model_id,
                    supports_text=model.supports_text,
                    supports_json=model.supports_json,
                    supports_streaming=model.supports_streaming,
                    supports_tools=model.supports_tools,
                    supports_embeddings=model.supports_embeddings,
                    context_window=model.context_window,
                    max_output_tokens=model.max_output_tokens,
                    recommended_use_cases=model.recommended_use_cases,
                    requires_api_key=profile.key_required(),
                    local_only=local_only,
                    notes="Project-local ModelProfile metadata.",
                )
            )
    return ProviderCapabilityRegistry(providers=providers, models=models)


def validate_provider_model_assignments(config: ProviderRoutingConfig, profiles: list[ProviderProfileV2]) -> ProviderModelAssignmentSummary:
    router = ProviderRouter(registry=build_project_provider_registry(profiles), config=config)
    reports = [router.validate_routing_rule(rule) for rule in config.rules]
    warnings: list[str] = []
    for report in reports:
        if report.rule.use_case in JSON_ROUTING_USE_CASES and not report.rule.require_json_support:
            warnings.append(f"{report.rule.use_case}: structured output use case should require JSON support")
    return ProviderModelAssignmentSummary(
        rules=config.rules,
        validation_reports=[report.model_dump_safe() for report in reports],
        warnings=warnings,
        fallback_chains={str(rule.use_case): _fallback_chain(rule) for rule in config.rules},
    )


def apply_provider_model_assignments(config: ProviderRoutingConfig, profiles: list[ProviderProfileV2]) -> ProviderRoutingSummary:
    router = ProviderRouter(registry=build_project_provider_registry(profiles))
    return router.apply_routing_config(config)


def _provider_type_for_registry(provider_type: str) -> ProviderType:
    if provider_type == "custom":
        return ProviderType.CUSTOM
    return ProviderType(provider_type)


def _profile_use_cases(profile: ProviderProfileV2) -> list[str]:
    use_cases: set[str] = set(profile.capabilities)
    for model in profile.model_profiles:
        use_cases.update(model.recommended_use_cases)
    return sorted(use_cases)


def _fallback_chain(rule: ProviderRoutingRule) -> list[str]:
    chain = [f"{rule.primary_provider_id}/{rule.primary_model_id}"]
    if rule.fallback_provider_id and rule.fallback_model_id:
        chain.append(f"{rule.fallback_provider_id}/{rule.fallback_model_id}")
    return chain
