import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.narrator_style_lab import NarratorStyleExperiment, run_narrator_style_experiment
from app.llm.prompt_profiles import PromptProfileStore
from app.main import app


def test_style_experiment_can_run() -> None:
    report = run_narrator_style_experiment(
        NarratorStyleExperiment(
            prompt_profile_id="default_safe",
            genre_tone="noir",
            sensory_focus="rain",
            prose_density="lean",
            response_length="short",
        )
    )

    assert report.pass_fail == "pass"
    assert report.style_score > 0
    assert report.findings
    assert report.suggested_actions == ["observe", "search"]


def test_hidden_leak_is_flagged_and_redacted() -> None:
    report = run_narrator_style_experiment(
        NarratorStyleExperiment(
            provider_id="fake_hidden_leak",
            hidden_terms=["the mayor forged the charter"],
        )
    )
    payload = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert report.pass_fail == "fail"
    assert "hidden_leak_detected" in report.blockers
    assert "the mayor forged the charter" not in payload


def test_invented_item_is_flagged() -> None:
    report = run_narrator_style_experiment(
        NarratorStyleExperiment(provider_id="fake_invented_item")
    )

    assert report.pass_fail == "fail"
    assert "invented_key_item_detected" in report.blockers


def test_style_params_do_not_change_action_result() -> None:
    experiment = NarratorStyleExperiment(action_reason="Safe visible observation.", genre_tone="wuxia")

    report = run_narrator_style_experiment(experiment)

    assert experiment.action_reason == "Safe visible observation."
    assert not any(finding.check == "no_contradiction_with_action_result" and not finding.passed for finding in report.findings)


def test_report_does_not_contain_api_key() -> None:
    report = run_narrator_style_experiment(
        NarratorStyleExperiment(player_input="observe LLM_API_KEY=sk-real-looking-secret"),
        settings=Settings(llm_api_key="sk-real-looking-settings-secret"),
    )
    payload = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert "sk-real-looking-secret" not in payload
    assert "sk-real-looking-settings-secret" not in payload
    assert "LLM_API_KEY" not in payload


def test_narrator_style_api_respects_gate() -> None:
    previous_settings = getattr(app.state, "settings", None)
    previous_reports = getattr(app.state, "narrator_style_reports", None)
    previous_store = getattr(app.state, "prompt_profile_store", None)
    client = TestClient(app)
    try:
        app.state.narrator_style_reports = []
        app.state.prompt_profile_store = PromptProfileStore()
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=False, llm_provider="mock")
        disabled = client.post("/prompt-lab/narrator-style/run", json={"prompt_profile_id": "default_safe"})
        app.state.settings = Settings(enable_debug_api=True, enable_perf_logging=False, llm_provider="mock")
        enabled = client.post(
            "/prompt-lab/narrator-style/run",
            json={"run_id": "narrator-style-api-test", "prompt_profile_id": "default_safe"},
        )
        fetched = client.get("/prompt-lab/narrator-style/narrator-style-api-test")
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        app.state.narrator_style_reports = previous_reports or []
        if previous_store is not None:
            app.state.prompt_profile_store = previous_store

    assert disabled.status_code == 403
    assert enabled.status_code == 200
    assert enabled.json()["pass_fail"] == "pass"
    assert fetched.status_code == 200
