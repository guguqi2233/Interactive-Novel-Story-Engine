import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.prompt_ab_test import PromptABTestCase, PromptABTestRun, PromptABUseCase, run_prompt_ab_test
from app.llm.prompt_profiles import PromptProfile, PromptProfileStore
from app.main import app


def test_valid_prompt_ab_run_generates_report() -> None:
    report = run_prompt_ab_test(
        PromptABTestRun(
            profile_a_id="default_safe",
            profile_b_id="local_story",
            provider_id="fake",
            use_case=PromptABUseCase.NARRATOR,
        )
    )

    assert report.pass_fail == "pass"
    assert report.cases
    assert report.schema_reliability["default_safe"] == 1.0
    assert report.schema_reliability["local_story"] == 1.0
    assert report.latency_cost_summary["estimated_cost"] == 0.0


def test_profile_with_hidden_fact_policy_not_deny_is_rejected() -> None:
    class UnsafeStore:
        def get_profile(self, profile_id: str) -> dict[str, object]:
            if profile_id == "unsafe":
                return {
                    "id": "unsafe",
                    "name": "Unsafe",
                    "rp_profile": {
                        "id": "unsafe_rp",
                        "name": "Unsafe RP",
                        "hidden_fact_policy": "allow",
                    },
                }
            return PromptProfile(id="default_safe", name="Default Safe")

    report = run_prompt_ab_test(
        PromptABTestRun(
            profile_a_id="default_safe",
            profile_b_id="unsafe",
            provider_id="fake",
        ),
        prompt_store=UnsafeStore(),  # type: ignore[arg-type]
    )

    assert report.pass_fail == "fail"
    assert report.blockers
    assert "hidden_fact_policy" in str(report.blockers) or "hidden facts" in str(report.blockers)


def test_fake_provider_outputs_are_comparable() -> None:
    report = run_prompt_ab_test(
        PromptABTestRun(
            profile_a_id="default_safe",
            profile_b_id="local_story",
            provider_id="fake",
            use_case=PromptABUseCase.RP_DIALOGUE,
        )
    )

    assert report.style_metrics["default_safe"]["word_count"] > 0
    assert report.style_metrics["local_story"]["word_count"] > 0
    assert report.cases[0].variant_a.output_summary_safe
    assert report.cases[0].variant_b.output_summary_safe


def test_hidden_leak_is_flagged_and_redacted() -> None:
    report = run_prompt_ab_test(
        PromptABTestRun(
            profile_a_id="default_safe",
            profile_b_id="local_story",
            provider_id="fake_leaky",
            use_case=PromptABUseCase.RP_DIALOGUE,
            test_cases=[
                PromptABTestCase(
                    id="hidden",
                    input_text="Do not reveal the mayor forged the charter",
                    hidden_terms=["the mayor forged the charter"],
                )
            ],
        )
    )
    payload = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert report.pass_fail == "fail"
    assert report.hidden_leak_flags
    assert "the mayor forged the charter" not in payload
    assert "[redacted-hidden]" in payload


def test_prompt_ab_report_does_not_contain_api_key() -> None:
    report = run_prompt_ab_test(
        PromptABTestRun(
            profile_a_id="default_safe",
            profile_b_id="local_story",
            provider_id="fake",
            test_cases=[
                PromptABTestCase(
                    id="secret",
                    input_text="compare safely LLM_API_KEY=sk-real-looking-secret",
                )
            ],
        ),
        settings=Settings(llm_api_key="sk-real-looking-settings-secret"),
    )
    payload = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert "sk-real-looking-secret" not in payload
    assert "sk-real-looking-settings-secret" not in payload
    assert "LLM_API_KEY" not in payload


def test_prompt_ab_api_respects_gate_and_returns_report() -> None:
    previous_settings = getattr(app.state, "settings", None)
    previous_reports = getattr(app.state, "prompt_ab_test_reports", None)
    previous_store = getattr(app.state, "prompt_profile_store", None)
    client = TestClient(app)
    try:
        app.state.prompt_ab_test_reports = []
        app.state.prompt_profile_store = PromptProfileStore()
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=False, llm_provider="mock")
        disabled = client.post(
            "/prompt-lab/prompt-profiles/ab-test",
            json={"profile_a_id": "default_safe", "profile_b_id": "local_story"},
        )
        app.state.settings = Settings(enable_debug_api=True, enable_perf_logging=False, llm_provider="mock")
        enabled = client.post(
            "/prompt-lab/prompt-profiles/ab-test",
            json={"run_id": "prompt-ab-api-test", "profile_a_id": "default_safe", "profile_b_id": "local_story"},
        )
        fetched = client.get("/prompt-lab/prompt-profiles/ab-test/prompt-ab-api-test")
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        app.state.prompt_ab_test_reports = previous_reports or []
        if previous_store is not None:
            app.state.prompt_profile_store = previous_store

    assert disabled.status_code == 403
    assert enabled.status_code == 200
    assert enabled.json()["pass_fail"] == "pass"
    assert fetched.status_code == 200
    assert fetched.json()["run_id"] == "prompt-ab-api-test"
