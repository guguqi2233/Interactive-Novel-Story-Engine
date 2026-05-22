from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.llm.model_compatibility import ModelCompatibilityUseCase
from app.llm.model_prompt_lab_policy import redact_sensitive_text
from app.llm.provider_capabilities import ModelCapability, ProviderCapabilityRegistry
from app.llm.provider_profiles import ProviderMode, ProviderSafetyPolicy


class ProviderRoutingUseCase(StrEnum):
    INTENT_PARSER = "intent_parser"
    NARRATOR = "narrator"
    RP_DIALOGUE = "RP_dialogue"
    MEMORY_SUMMARY = "memory_summary"
    CHARACTER_IMPORT = "character_import"
    LOREBOOK_CLASSIFICATION = "lorebook_classification"
    QUEST_DRAFT = "quest_draft"
    STRUCTURED_JSON = "structured_json"
    NOVEL_DRAFT = "novel_draft"
    NOVEL_REWRITE = "novel_rewrite"
    TAVERN_REPLY = "tavern_reply"
    WORLD_INTENT_PARSE = "world_intent_parse"
    WORLD_NARRATION = "world_narration"
    CROSS_MODE_DRAFT = "cross_mode_draft"
    QUALITY_EVAL = "quality_eval"
    CHEAP_SUMMARY = "cheap_summary"


JSON_ROUTING_USE_CASES = {
    ProviderRoutingUseCase.INTENT_PARSER,
    ProviderRoutingUseCase.MEMORY_SUMMARY,
    ProviderRoutingUseCase.CHARACTER_IMPORT,
    ProviderRoutingUseCase.LOREBOOK_CLASSIFICATION,
    ProviderRoutingUseCase.QUEST_DRAFT,
    ProviderRoutingUseCase.STRUCTURED_JSON,
    ProviderRoutingUseCase.WORLD_INTENT_PARSE,
    ProviderRoutingUseCase.CROSS_MODE_DRAFT,
    ProviderRoutingUseCase.QUALITY_EVAL,
}


class ProviderRoutingRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    use_case: ProviderRoutingUseCase
    primary_provider_id: str
    primary_model_id: str
    fallback_provider_id: str | None = None
    fallback_model_id: str | None = None
    max_latency_ms: float | None = Field(default=None, gt=0)
    max_cost_per_call: float | None = Field(default=None, ge=0)
    require_json_support: bool = False
    require_local_only: bool | None = None
    safety_policy: ProviderSafetyPolicy = Field(default_factory=ProviderSafetyPolicy)
    enabled: bool = True


class ProviderRoutingContext(BaseModel):
    mode: ProviderMode | str = ProviderMode.AUTHORING
    use_case: ProviderRoutingUseCase | str
    prompt_is_sensitive: bool = False
    prompt_is_debug: bool = False
    project_local_only: bool = False
    explicit_external_override: bool = False


class ProviderRoutingConfig(BaseModel):
    rules: list[ProviderRoutingRule] = Field(default_factory=list)


class ProviderRoutingValidationReport(BaseModel):
    ok: bool
    rule: ProviderRoutingRule
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


class ProviderRoutingDecision(BaseModel):
    use_case: ProviderRoutingUseCase
    provider_id: str
    model_id: str
    used_fallback: bool = False
    reason: str
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


class ProviderRoutingSummary(BaseModel):
    local_only: bool = True
    rules: list[ProviderRoutingRule] = Field(default_factory=list)
    validation_reports: list[ProviderRoutingValidationReport] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


class ProviderRouter:
    """Metadata-only provider routing rules for Prompt Lab.

    The router never instantiates providers or calls external APIs. Runtime
    provider construction remains the responsibility of the existing
    `create_llm_provider` factory.
    """

    def __init__(
        self,
        *,
        registry: ProviderCapabilityRegistry | None = None,
        config: ProviderRoutingConfig | None = None,
    ) -> None:
        self._registry = registry or ProviderCapabilityRegistry()
        self._config = config or ProviderRoutingConfig()

    @property
    def config(self) -> ProviderRoutingConfig:
        return self._config

    def validate_routing_rule(self, rule: ProviderRoutingRule) -> ProviderRoutingValidationReport:
        errors: list[str] = []
        warnings: list[str] = []
        if _contains_sensitive(rule.model_dump(mode="json")):
            errors.append("routing_rule_must_not_contain_api_key_or_secret")
        primary = self._get_model(rule.primary_provider_id, rule.primary_model_id, errors)
        fallback = self._get_fallback_model(rule, errors)
        needs_json = rule.require_json_support or rule.use_case in JSON_ROUTING_USE_CASES
        if primary is not None:
            errors.extend(_model_constraint_errors(rule, primary, is_fallback=False))
            if needs_json and not primary.supports_json:
                if fallback is not None and fallback.supports_json:
                    warnings.append("primary_model_lacks_json_support_fallback_will_be_used")
                else:
                    errors.append("json_use_case_requires_json_support_or_json_fallback")
        if fallback is not None:
            errors.extend(_model_constraint_errors(rule, fallback, is_fallback=True))
            if needs_json and not fallback.supports_json:
                warnings.append("fallback_model_lacks_json_support")
        if rule.fallback_provider_id and not rule.fallback_model_id:
            errors.append("fallback_model_id_required_when_fallback_provider_id_is_set")
        if rule.fallback_model_id and not rule.fallback_provider_id:
            errors.append("fallback_provider_id_required_when_fallback_model_id_is_set")
        if rule.max_cost_per_call is not None:
            warnings.append("max_cost_per_call_is_enforced_as_metadata_only")
        if rule.max_latency_ms is not None:
            warnings.append("max_latency_ms_is_enforced_as_metadata_only")
        if rule.safety_policy.log_prompts:
            warnings.append("prompt_logging_is_disabled_by_default_and_requires_explicit_debug_review")
        return ProviderRoutingValidationReport(ok=not errors, rule=rule, errors=errors, warnings=warnings)

    def select_model_for_use_case(self, use_case: ProviderRoutingUseCase | ModelCompatibilityUseCase | str) -> ProviderRoutingDecision:
        parsed = ProviderRoutingUseCase(str(use_case))
        rule = next((item for item in self._config.rules if item.enabled and item.use_case == parsed), None)
        if rule is None:
            default = self._default_model_for_use_case(parsed)
            return ProviderRoutingDecision(
                use_case=parsed,
                provider_id=default.provider_id,
                model_id=default.model_id,
                reason="default_declared_capability",
            )
        report = self.validate_routing_rule(rule)
        if "primary_model_lacks_json_support_fallback_will_be_used" in report.warnings:
            fallback = self._valid_fallback(rule)
            if fallback is not None:
                return ProviderRoutingDecision(
                    use_case=parsed,
                    provider_id=fallback.provider_id,
                    model_id=fallback.model_id,
                    used_fallback=True,
                    reason="routing_rule_primary_lacks_json_fallback_selected",
                    warnings=report.warnings,
                )
        if report.ok:
            return ProviderRoutingDecision(
                use_case=parsed,
                provider_id=rule.primary_provider_id,
                model_id=rule.primary_model_id,
                reason="routing_rule_primary_selected",
                warnings=report.warnings,
            )
        fallback = self._valid_fallback(rule)
        if fallback is not None:
            return ProviderRoutingDecision(
                use_case=parsed,
                provider_id=fallback.provider_id,
                model_id=fallback.model_id,
                used_fallback=True,
                reason="routing_rule_primary_blocked_fallback_selected",
                warnings=report.errors + report.warnings,
            )
        raise ValueError("; ".join(report.errors) or "Routing rule is invalid.")

    def resolve_provider_for_use_case(self, context: ProviderRoutingContext) -> ProviderRoutingDecision:
        parsed = ProviderRoutingUseCase(str(context.use_case))
        rule = next((item for item in self._config.rules if item.enabled and item.use_case == parsed), None)
        if rule is None:
            decision = self.select_model_for_use_case(parsed)
            model = self._registry.get_capability(decision.provider_id, decision.model_id)  # type: ignore[assignment]
            policy_errors = _policy_errors(context, ProviderSafetyPolicy(), model)  # type: ignore[arg-type]
            if policy_errors:
                raise ValueError("; ".join(policy_errors))
            return decision
        report = self.validate_routing_rule(rule)
        primary = self._get_model(rule.primary_provider_id, rule.primary_model_id, [])
        if primary is not None:
            report.errors.extend(_policy_errors(context, rule.safety_policy, primary))
        if report.ok and not report.errors:
            return self.select_model_for_use_case(parsed)
        fallback = self._valid_fallback(rule)
        if fallback is not None and not _policy_errors(context, rule.safety_policy, fallback):
            return ProviderRoutingDecision(
                use_case=parsed,
                provider_id=fallback.provider_id,
                model_id=fallback.model_id,
                used_fallback=True,
                reason="routing_policy_primary_blocked_fallback_selected",
                warnings=report.errors + report.warnings,
            )
        raise ValueError("; ".join(report.errors) or "Provider safety policy rejected routing decision")

    def fallback_for_use_case(self, context: ProviderRoutingContext) -> ProviderRoutingDecision | None:
        """Return a fallback decision that satisfies the same capability and policy checks."""
        parsed = ProviderRoutingUseCase(str(context.use_case))
        rule = next((item for item in self._config.rules if item.enabled and item.use_case == parsed), None)
        if rule is None:
            return None
        fallback = self._valid_fallback(rule)
        if fallback is None:
            return None
        policy_errors = _policy_errors(context, rule.safety_policy, fallback)
        if policy_errors:
            return None
        return ProviderRoutingDecision(
            use_case=parsed,
            provider_id=fallback.provider_id,
            model_id=fallback.model_id,
            used_fallback=True,
            reason="routing_rule_fallback_selected_after_primary_failure",
        )

    def apply_routing_config(self, config: ProviderRoutingConfig) -> ProviderRoutingSummary:
        reports = [self.validate_routing_rule(rule) for rule in config.rules]
        if any(not report.ok for report in reports):
            return ProviderRoutingSummary(
                rules=self._config.rules,
                validation_reports=reports,
                warnings=["routing_config_not_applied_due_to_errors"],
            )
        self._config = config
        return ProviderRoutingSummary(rules=self._config.rules, validation_reports=reports)

    def safe_summary(self) -> ProviderRoutingSummary:
        return ProviderRoutingSummary(
            rules=self._config.rules,
            validation_reports=[self.validate_routing_rule(rule) for rule in self._config.rules],
        )

    def _get_model(self, provider_id: str, model_id: str, errors: list[str]) -> ModelCapability | None:
        try:
            return self._registry.get_capability(provider_id, model_id)  # type: ignore[return-value]
        except ValueError as exc:
            errors.append(str(exc))
            return None

    def _get_fallback_model(self, rule: ProviderRoutingRule, errors: list[str]) -> ModelCapability | None:
        if not rule.fallback_provider_id or not rule.fallback_model_id:
            return None
        return self._get_model(rule.fallback_provider_id, rule.fallback_model_id, errors)

    def _valid_fallback(self, rule: ProviderRoutingRule) -> ModelCapability | None:
        if not rule.fallback_provider_id or not rule.fallback_model_id:
            return None
        local_errors: list[str] = []
        fallback = self._get_model(rule.fallback_provider_id, rule.fallback_model_id, local_errors)
        if fallback is None:
            return None
        needs_json = rule.require_json_support or rule.use_case in JSON_ROUTING_USE_CASES
        if needs_json and not fallback.supports_json:
            return None
        if _model_constraint_errors(rule, fallback, is_fallback=True):
            return None
        return fallback

    def _default_model_for_use_case(self, use_case: ProviderRoutingUseCase) -> ModelCapability:
        capability_key = _capability_use_case(use_case)
        needs_json = use_case in JSON_ROUTING_USE_CASES
        for model in self._registry.list_models():
            if needs_json and not model.supports_json:
                continue
            if capability_key in model.recommended_use_cases:
                return model
        models = [model for model in self._registry.list_models() if not needs_json or model.supports_json]
        if not models:
            if needs_json:
                raise ValueError("No JSON-capable provider models are registered.")
            raise ValueError("No provider models are registered.")
        return models[0]


_DEFAULT_PROVIDER_ROUTER = ProviderRouter()


def get_default_provider_router() -> ProviderRouter:
    return _DEFAULT_PROVIDER_ROUTER


def _model_constraint_errors(rule: ProviderRoutingRule, model: ModelCapability, *, is_fallback: bool) -> list[str]:
    prefix = "fallback" if is_fallback else "primary"
    errors: list[str] = []
    if rule.require_local_only is True and not model.local_only:
        errors.append(f"{prefix}_model_must_be_local_only")
    if not model.supports_text:
        errors.append(f"{prefix}_model_must_support_text")
    return errors


def _capability_use_case(use_case: ProviderRoutingUseCase) -> str:
    if use_case in JSON_ROUTING_USE_CASES:
        return "structured_output"
    if use_case in {ProviderRoutingUseCase.NARRATOR, ProviderRoutingUseCase.WORLD_NARRATION, ProviderRoutingUseCase.NOVEL_DRAFT, ProviderRoutingUseCase.NOVEL_REWRITE}:
        return "narration"
    if use_case in {ProviderRoutingUseCase.RP_DIALOGUE, ProviderRoutingUseCase.TAVERN_REPLY}:
        return "rp_expression"
    if use_case in {ProviderRoutingUseCase.MEMORY_SUMMARY, ProviderRoutingUseCase.CHEAP_SUMMARY}:
        return "structured_output"
    return use_case.value


def _policy_errors(context: ProviderRoutingContext, policy: ProviderSafetyPolicy, model: ModelCapability) -> list[str]:
    errors: list[str] = []
    mode = str(context.mode)
    allowed = [str(item) for item in policy.allowed_modes]
    disallowed = [str(item) for item in policy.disallowed_modes]
    if allowed and mode not in allowed:
        errors.append("provider_safety_policy_mode_not_allowed")
    if mode in disallowed:
        errors.append("provider_safety_policy_mode_disallowed")
    if context.prompt_is_sensitive and not policy.allow_sensitive_prompts:
        errors.append("provider_safety_policy_rejects_sensitive_prompt")
    if context.prompt_is_debug and not policy.allow_debug_prompts:
        errors.append("provider_safety_policy_rejects_debug_prompt")
    if (context.project_local_only or policy.require_local_only) and not context.explicit_external_override and not model.local_only:
        errors.append("provider_safety_policy_requires_local_only")
    return errors


def _contains_sensitive(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_sensitive(key) or _contains_sensitive(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_sensitive(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return "api_key=" in lowered or "llm_api_key" in lowered or "sk-" in lowered or "raw_env" in lowered
    return False


def _strip_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            stripped = _strip_sensitive(item)
            if not _contains_sensitive(key) and not _contains_sensitive(stripped):
                safe[str(key)] = stripped
        return safe
    if isinstance(value, list):
        return [_strip_sensitive(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value).text
    return value
