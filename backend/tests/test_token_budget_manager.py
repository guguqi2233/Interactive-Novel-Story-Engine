import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.context_inspector import ContextSection, ContextVisibilityLevel
from app.llm.token_budget import (
    TokenBudgetManager,
    TokenBudgetOverflowPolicy,
    TokenBudgetProfile,
    TokenBudgetRequest,
    TokenBudgetUseCase,
    estimate_token_budget,
)
from app.main import app


def test_budget_allocation_is_correct() -> None:
    manager = TokenBudgetManager()
    profile = TokenBudgetProfile(max_total_tokens=120, reserved_output_tokens=20, max_memory_tokens=30)
    sections = [
        _section("safety_constraints", 15, ContextVisibilityLevel.NARRATOR_SAFE),
        _section("player_input", 10, ContextVisibilityLevel.NORMAL),
        _section("memory", 80, ContextVisibilityLevel.NARRATOR_SAFE),
    ]

    report = manager.trim_context(profile, sections)

    assert report.available_context_tokens == 100
    assert report.final_context_tokens <= 100
    assert report.sections[0].protected is True
    assert report.sections[2].allocated_tokens == 30


def test_memory_section_over_limit_is_trimmed() -> None:
    profile = TokenBudgetProfile(max_total_tokens=100, reserved_output_tokens=20, max_memory_tokens=25)
    report = estimate_token_budget(TokenBudgetRequest(profile=profile, sections=[_section("memory", 90, ContextVisibilityLevel.NARRATOR_SAFE)]))

    assert "memory" in report.trimmed_sections
    assert report.sections[0].final_tokens == 25
    assert report.sections[0].trimmed_tokens == 65


def test_safety_constraints_are_not_trimmed() -> None:
    profile = TokenBudgetProfile(max_total_tokens=80, reserved_output_tokens=20, max_memory_tokens=5)
    report = estimate_token_budget(
        TokenBudgetRequest(
            profile=profile,
            sections=[
                _section("safety_constraints", 30, ContextVisibilityLevel.NARRATOR_SAFE),
                _section("memory", 40, ContextVisibilityLevel.NARRATOR_SAFE),
            ],
        )
    )

    safety = report.sections[0]
    assert safety.protected is True
    assert safety.final_tokens == 30
    assert "safety_constraints" not in report.trimmed_sections


def test_hidden_facts_do_not_enter_trimmed_context() -> None:
    profile = TokenBudgetProfile()
    report = estimate_token_budget(
        TokenBudgetRequest(
            profile=profile,
            sections=[
                _section("fact_excluded", 40, ContextVisibilityLevel.HIDDEN_REDACTED, "hidden fact: the mayor forged the charter"),
                _section("visible_facts", 10, ContextVisibilityLevel.NORMAL),
            ],
        )
    )
    payload = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert "fact_excluded" in report.dropped_sections
    assert all(section.visibility_level != ContextVisibilityLevel.HIDDEN_REDACTED for section in report.trimmed_context)
    assert "the mayor forged the charter" not in payload


def test_drop_low_priority_policy_drops_overflow_sections() -> None:
    profile = TokenBudgetProfile(
        max_total_tokens=70,
        reserved_output_tokens=20,
        max_memory_tokens=10,
        overflow_policy=TokenBudgetOverflowPolicy.DROP_LOW_PRIORITY,
    )
    report = estimate_token_budget(TokenBudgetRequest(profile=profile, sections=[_section("memory", 40, ContextVisibilityLevel.NARRATOR_SAFE)]))

    assert report.dropped_sections == ["memory"]
    assert report.final_context_tokens == 0


def test_token_budget_api_respects_gate_and_returns_report() -> None:
    client = TestClient(app)
    previous_settings = getattr(app.state, "settings", None)
    previous_reports = getattr(app.state, "token_budget_reports", None)
    try:
        app.state.token_budget_reports = []
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=False, llm_provider="mock")
        disabled = client.post("/prompt-lab/token-budget/estimate", json={})
        app.state.settings = Settings(enable_debug_api=True, enable_perf_logging=False, llm_provider="mock")
        profiles = client.get("/prompt-lab/token-budget/profiles")
        enabled = client.post(
            "/prompt-lab/token-budget/estimate",
            json={
                "profile": {
                    "id": "api_budget",
                    "use_case": "narrator",
                    "max_total_tokens": 120,
                    "reserved_output_tokens": 20,
                    "max_memory_tokens": 20,
                    "max_lore_tokens": 20,
                    "max_recent_events_tokens": 20,
                    "max_dialogue_examples_tokens": 20,
                    "priority_order": ["safety_constraints", "memory"],
                    "overflow_policy": "trim_low_priority",
                },
                "sections": [{"section_type": "memory", "token_estimate": 80, "visibility_level": "narrator_safe", "safe_summary": "memory", "content_redacted": "memory content"}],
            },
        )
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        app.state.token_budget_reports = previous_reports or []

    assert disabled.status_code == 403
    assert profiles.status_code == 200
    assert enabled.status_code == 200
    assert enabled.json()["local_only"] is True
    assert enabled.json()["trimmed_sections"] == ["memory"]


def _section(
    section_type: str,
    tokens: int,
    visibility: ContextVisibilityLevel,
    content: str | None = None,
) -> ContextSection:
    return ContextSection(
        section_type=section_type,
        token_estimate=tokens,
        visibility_level=visibility,
        safe_summary=content or section_type,
        content_redacted=content or (f"{section_type} " * max(tokens, 1)),
    )
