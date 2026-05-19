from app.llm.model_prompt_lab_policy import (
    BenchmarkRun,
    ContextSegment,
    ModelPromptLabPolicy,
    PromptLabPrivacyClass,
    ProviderProfile,
)


def test_prompt_profile_cannot_enable_hidden_facts() -> None:
    policy = ModelPromptLabPolicy()

    try:
        policy.validate_prompt_profile(
            {
                "id": "unsafe_lab_profile",
                "name": "Unsafe Lab Profile",
                "rp_profile": {
                    "id": "unsafe_rp",
                    "name": "Unsafe RP",
                    "hidden_fact_policy": "allow",
                },
            }
        )
    except ValueError as exc:
        assert "hidden_fact_policy" in str(exc) or "hidden facts" in str(exc)
    else:
        raise AssertionError("Expected hidden fact prompt profile override to be rejected")


def test_context_snapshot_defaults_redacted() -> None:
    policy = ModelPromptLabPolicy()
    snapshot = policy.build_context_snapshot(
        "snap-1",
        [
            ContextSegment(label="visible", content="visible square fact"),
            ContextSegment(
                label="hidden",
                content="hidden truth: the mayor forged the charter",
                privacy_class=PromptLabPrivacyClass.HIDDEN,
                safe_summary="hidden fact id=fact_mayor_secret",
            ),
            ContextSegment(
                label="debug",
                content="raw state_delta path=npcs.mira.knowledge",
                privacy_class=PromptLabPrivacyClass.DEBUG,
                safe_summary="debug delta summary",
            ),
            ContextSegment(label="secret", content="LLM_API_KEY=sk-real-looking-secret"),
        ],
    )

    normal_view = snapshot.normal_view()
    rendered = str(normal_view)

    assert normal_view["default_view"] == "normal"
    assert "visible square fact" in rendered
    assert "mayor forged the charter" not in rendered
    assert "raw state_delta path" not in rendered
    assert "sk-real-looking-secret" not in rendered
    assert "hidden fact id=fact_mayor_secret" in rendered
    assert "[redacted-secret]" in rendered


def test_benchmark_defaults_do_not_call_real_api() -> None:
    policy = ModelPromptLabPolicy()
    default_run = BenchmarkRun(id="bench-local")

    decision = policy.evaluate_benchmark_run(default_run)

    assert decision.allowed
    assert not default_run.provider_profile.uses_real_external_api


def test_real_provider_benchmark_requires_explicit_opt_in() -> None:
    policy = ModelPromptLabPolicy()
    run = BenchmarkRun(
        id="bench-real",
        provider_profile=ProviderProfile(
            provider_id="openai",
            provider_type="openai",
            model_id="gpt-test",
            api_key_configured=True,
        ),
    )

    decision = policy.evaluate_benchmark_run(run)

    assert not decision.allowed
    assert "real_external_provider_requires_explicit_opt_in" in decision.blockers


def test_provider_config_not_in_frontend_summary() -> None:
    policy = ModelPromptLabPolicy()
    profile = ProviderProfile(
        provider_id="openai",
        provider_type="openai",
        model_id="gpt-test",
        api_key_configured=True,
        base_url="https://api.example.invalid/v1?token=sk-secret",
    )

    summary = policy.frontend_provider_summary(profile)
    rendered = str(summary)

    assert summary["api_key_configured"] is True
    assert summary["base_url"] == "[redacted]"
    assert "sk-secret" not in rendered
    assert "api.example.invalid" not in rendered
