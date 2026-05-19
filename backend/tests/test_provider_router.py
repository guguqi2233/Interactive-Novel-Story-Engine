import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.provider_capabilities import (
    ModelCapability,
    ProviderCapability,
    ProviderCapabilityRegistry,
    ProviderType,
)
from app.llm.provider_router import (
    ProviderRouter,
    ProviderRoutingConfig,
    ProviderRoutingRule,
    ProviderRoutingUseCase,
)
from app.main import app


def test_valid_routing_rule_can_be_saved() -> None:
    router = ProviderRouter()
    rule = ProviderRoutingRule(
        use_case=ProviderRoutingUseCase.NARRATOR,
        primary_provider_id="local_stub",
        primary_model_id="local_stub",
        fallback_provider_id="mock",
        fallback_model_id="mock",
        require_local_only=True,
    )

    summary = router.apply_routing_config(ProviderRoutingConfig(rules=[rule]))
    decision = router.select_model_for_use_case(ProviderRoutingUseCase.NARRATOR)

    assert summary.validation_reports[0].ok
    assert router.config.rules == [rule]
    assert decision.provider_id == "local_stub"
    assert decision.model_id == "local_stub"


def test_invalid_provider_or_model_is_rejected() -> None:
    router = ProviderRouter()
    rule = ProviderRoutingRule(
        use_case=ProviderRoutingUseCase.NARRATOR,
        primary_provider_id="missing",
        primary_model_id="missing",
    )

    report = router.validate_routing_rule(rule)

    assert not report.ok
    assert any("Unknown provider capability" in error for error in report.errors)


def test_json_use_case_with_non_json_primary_uses_warning_or_error() -> None:
    registry = ProviderCapabilityRegistry(
        providers=[
            ProviderCapability(provider_id="text_only", provider_type=ProviderType.MOCK),
            ProviderCapability(provider_id="json_ok", provider_type=ProviderType.MOCK),
        ],
        models=[
            ModelCapability(
                provider_id="text_only",
                provider_type=ProviderType.MOCK,
                model_id="text-model",
                supports_json=False,
            ),
            ModelCapability(
                provider_id="json_ok",
                provider_type=ProviderType.MOCK,
                model_id="json-model",
                supports_json=True,
            ),
        ],
    )
    router = ProviderRouter(registry=registry)
    blocked = ProviderRoutingRule(
        use_case=ProviderRoutingUseCase.STRUCTURED_JSON,
        primary_provider_id="text_only",
        primary_model_id="text-model",
    )
    with_fallback = blocked.model_copy(
        update={"fallback_provider_id": "json_ok", "fallback_model_id": "json-model"}
    )

    blocked_report = router.validate_routing_rule(blocked)
    fallback_report = router.validate_routing_rule(with_fallback)

    assert not blocked_report.ok
    assert "json_use_case_requires_json_support_or_json_fallback" in blocked_report.errors
    assert fallback_report.ok
    assert "primary_model_lacks_json_support_fallback_will_be_used" in fallback_report.warnings


def test_fallback_selection_when_primary_invalid_for_json() -> None:
    registry = ProviderCapabilityRegistry(
        providers=[
            ProviderCapability(provider_id="text_only", provider_type=ProviderType.MOCK),
            ProviderCapability(provider_id="json_ok", provider_type=ProviderType.MOCK),
        ],
        models=[
            ModelCapability(
                provider_id="text_only",
                provider_type=ProviderType.MOCK,
                model_id="text-model",
                supports_json=False,
            ),
            ModelCapability(
                provider_id="json_ok",
                provider_type=ProviderType.MOCK,
                model_id="json-model",
                supports_json=True,
            ),
        ],
    )
    router = ProviderRouter(
        registry=registry,
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case=ProviderRoutingUseCase.INTENT_PARSER,
                    primary_provider_id="text_only",
                    primary_model_id="text-model",
                    fallback_provider_id="json_ok",
                    fallback_model_id="json-model",
                )
            ]
        ),
    )

    decision = router.select_model_for_use_case(ProviderRoutingUseCase.INTENT_PARSER)

    assert decision.used_fallback
    assert decision.provider_id == "json_ok"
    assert decision.model_id == "json-model"


def test_rule_rejects_api_key_or_secret_text() -> None:
    router = ProviderRouter()
    rule = ProviderRoutingRule(
        use_case=ProviderRoutingUseCase.NARRATOR,
        primary_provider_id="local_stub",
        primary_model_id="sk-real-looking-secret",
    )

    report = router.validate_routing_rule(rule)
    payload = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert not report.ok
    assert "routing_rule_must_not_contain_api_key_or_secret" in report.errors
    assert "sk-real-looking-secret" not in payload


def test_provider_routing_api_respects_gate_and_saves_safe_rule() -> None:
    client = TestClient(app)
    previous_settings = getattr(app.state, "settings", None)
    previous_router = getattr(app.state, "provider_router", None)
    rule = {
        "use_case": "narrator",
        "primary_provider_id": "local_stub",
        "primary_model_id": "local_stub",
        "fallback_provider_id": "mock",
        "fallback_model_id": "mock",
        "require_json_support": False,
        "require_local_only": True,
        "enabled": True,
    }
    try:
        app.state.provider_router = ProviderRouter()
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=False, llm_provider="mock")
        disabled = client.get("/prompt-lab/provider-routing")
        app.state.settings = Settings(enable_debug_api=True, enable_perf_logging=False, llm_provider="mock")
        preview = client.post("/prompt-lab/provider-routing/preview", json=rule)
        saved = client.post("/prompt-lab/provider-routing/save", json={"rules": [rule]})
        fetched = client.get("/prompt-lab/provider-routing")
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        if previous_router is None:
            if hasattr(app.state, "provider_router"):
                delattr(app.state, "provider_router")
        else:
            app.state.provider_router = previous_router

    assert disabled.status_code == 403
    assert preview.status_code == 200
    assert saved.status_code == 200
    assert fetched.status_code == 200
    assert saved.json()["rules"][0]["primary_provider_id"] == "local_stub"
    assert "sk-" not in fetched.text
    assert "api_key" not in fetched.text.lower()


def test_invalid_config_is_not_applied() -> None:
    router = ProviderRouter()
    valid = ProviderRoutingRule(
        use_case=ProviderRoutingUseCase.NARRATOR,
        primary_provider_id="local_stub",
        primary_model_id="local_stub",
    )
    router.apply_routing_config(ProviderRoutingConfig(rules=[valid]))

    invalid = ProviderRoutingRule(
        use_case=ProviderRoutingUseCase.NARRATOR,
        primary_provider_id="missing",
        primary_model_id="missing",
    )
    summary = router.apply_routing_config(ProviderRoutingConfig(rules=[invalid]))

    assert "routing_config_not_applied_due_to_errors" in summary.warnings
    assert router.config.rules == [valid]
