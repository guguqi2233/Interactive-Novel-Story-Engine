import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import GameState, NPCState, VoiceProfile
from app.llm.npc_voice_style_lab import (
    NPCVoiceDialogueTestCase,
    NPCVoiceStyleExperiment,
    run_npc_voice_style_experiment,
)
from app.llm.prompt_profiles import PromptProfileStore
from app.main import app


def _voice() -> VoiceProfile:
    return VoiceProfile(
        tone="calm",
        vocabulary_style="plain",
        catchphrases=["steady now"],
        speech_habits=["measured"],
        emotional_tells=["soft pause"],
    )


def test_npc_voice_style_experiment_can_run() -> None:
    report = run_npc_voice_style_experiment(
        NPCVoiceStyleExperiment(
            npc_id="harlan",
            voice_profile_variant=_voice(),
            dialogue_test_cases=[NPCVoiceDialogueTestCase(id="tone", expected_emotional_tone="calm")],
        )
    )

    assert report.pass_fail == "pass"
    assert report.voice_consistency_score > 0
    assert report.findings


def test_unknown_fact_mention_is_flagged() -> None:
    report = run_npc_voice_style_experiment(
        NPCVoiceStyleExperiment(
            npc_id="harlan",
            provider_id="fake_unknown_fact",
            voice_profile_variant=_voice(),
            dialogue_test_cases=[
                NPCVoiceDialogueTestCase(
                    id="unknown",
                    unknown_fact_terms=["unknown forbidden fact"],
                )
            ],
        )
    )

    assert report.pass_fail == "fail"
    assert any(finding.safe_detail == "unknown_fact_mention" for finding in report.findings)


def test_hidden_fact_leak_is_flagged_and_redacted() -> None:
    report = run_npc_voice_style_experiment(
        NPCVoiceStyleExperiment(
            npc_id="harlan",
            provider_id="fake_hidden_leak",
            voice_profile_variant=_voice(),
            dialogue_test_cases=[
                NPCVoiceDialogueTestCase(
                    id="hidden",
                    hidden_terms=["the mayor forged the charter"],
                )
            ],
        )
    )
    payload = json.dumps(report.model_dump_safe(), ensure_ascii=False)

    assert report.pass_fail == "fail"
    assert any(finding.safe_detail == "hidden_leak_detected" for finding in report.findings)
    assert "the mayor forged the charter" not in payload


def test_example_dialogue_does_not_become_fact() -> None:
    report = run_npc_voice_style_experiment(
        NPCVoiceStyleExperiment(
            npc_id="harlan",
            voice_profile_variant=_voice(),
            example_dialogue_set=["Harlan: The hidden seal is under the shrine."],
            dialogue_test_cases=[
                NPCVoiceDialogueTestCase(
                    id="example_style_only",
                    unknown_fact_terms=["hidden seal is under the shrine"],
                )
            ],
        )
    )

    assert report.pass_fail == "pass"
    assert not any(finding.safe_detail == "unknown_fact_mention" for finding in report.findings)


def test_voice_profile_lab_does_not_change_game_state() -> None:
    state = GameState(world_id="test_world", npcs={"harlan": NPCState(id="harlan", location_id="square")})
    before = state.model_dump(mode="json")

    report = run_npc_voice_style_experiment(
        NPCVoiceStyleExperiment(npc_id="harlan", voice_profile_variant=_voice()),
        state=state,
    )

    assert report.pass_fail == "pass"
    assert state.model_dump(mode="json") == before


def test_npc_voice_style_api_respects_gate() -> None:
    previous_settings = getattr(app.state, "settings", None)
    previous_reports = getattr(app.state, "npc_voice_style_reports", None)
    previous_store = getattr(app.state, "prompt_profile_store", None)
    client = TestClient(app)
    try:
        app.state.npc_voice_style_reports = []
        app.state.prompt_profile_store = PromptProfileStore()
        app.state.settings = Settings(enable_debug_api=False, enable_perf_logging=False, llm_provider="mock")
        disabled = client.post("/prompt-lab/npc-voice-style/run", json={"npc_id": "harlan"})
        app.state.settings = Settings(enable_debug_api=True, enable_perf_logging=False, llm_provider="mock")
        enabled = client.post(
            "/prompt-lab/npc-voice-style/run",
            json={"run_id": "npc-voice-api-test", "npc_id": "harlan", "voice_profile_variant": _voice().model_dump()},
        )
        fetched = client.get("/prompt-lab/npc-voice-style/npc-voice-api-test")
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        app.state.npc_voice_style_reports = previous_reports or []
        if previous_store is not None:
            app.state.prompt_profile_store = previous_store

    assert disabled.status_code == 403
    assert enabled.status_code == 200
    assert enabled.json()["pass_fail"] == "pass"
    assert fetched.status_code == 200
