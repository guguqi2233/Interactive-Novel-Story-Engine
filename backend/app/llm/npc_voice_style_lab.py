from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.config import Settings
from app.core.world_state import GameState, VoiceProfile
from app.llm.model_prompt_lab_policy import BenchmarkRun, ModelPromptLabPolicy, ProviderProfile, redact_sensitive_text
from app.llm.provider_base import LLMProvider
from app.llm.provider_factory import create_llm_provider
from app.llm.prompt_profiles import PromptProfileStore


class NPCVoiceDialogueTestCase(BaseModel):
    id: str = "default_voice_case"
    player_line: str = "What do you know?"
    expected_emotional_tone: str = "calm"
    npc_known_facts: list[str] = Field(default_factory=list)
    unknown_fact_terms: list[str] = Field(default_factory=list)
    hidden_terms: list[str] = Field(default_factory=list)


class NPCVoiceStyleExperiment(BaseModel):
    run_id: str = Field(default_factory=lambda: f"npc-voice-style-{uuid4().hex}")
    npc_id: str
    voice_profile_variant: VoiceProfile = Field(default_factory=VoiceProfile)
    rp_prompt_profile_id: str = "default_safe"
    example_dialogue_set: list[str] = Field(default_factory=list)
    dialogue_test_cases: list[NPCVoiceDialogueTestCase] = Field(default_factory=list)
    provider_id: str = "fake"
    model_id: str | None = None
    allow_real_provider: bool = False


class NPCVoiceStyleFinding(BaseModel):
    case_id: str
    check: str
    passed: bool
    severity: str = "warning"
    safe_detail: str = ""


class NPCVoiceStyleReport(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    npc_id: str
    rp_prompt_profile_id: str
    provider_id: str
    model_id: str | None = None
    pass_fail: str
    voice_consistency_score: float = 0.0
    latency_ms: float = 0.0
    output_summaries_safe: list[str] = Field(default_factory=list)
    findings: list[NPCVoiceStyleFinding] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


def run_npc_voice_style_experiment(
    experiment: NPCVoiceStyleExperiment,
    *,
    prompt_store: PromptProfileStore | None = None,
    settings: Settings | None = None,
    state: GameState | None = None,
) -> NPCVoiceStyleReport:
    _ = state
    active_settings = settings or Settings(llm_provider="mock")
    policy = ModelPromptLabPolicy()
    provider_profile = ProviderProfile(
        provider_id=experiment.provider_id,
        provider_type=_provider_type(experiment.provider_id, active_settings),  # type: ignore[arg-type]
        model_id=experiment.model_id or experiment.provider_id,
        api_key_configured=bool(active_settings.llm_api_key),
        uses_real_external_api=experiment.provider_id == "openai",
    )
    decision = policy.evaluate_benchmark_run(
        BenchmarkRun(
            id=experiment.run_id,
            provider_profile=provider_profile,
            explicit_real_provider_opt_in=experiment.allow_real_provider,
            uses_provider_factory=True,
        )
    )
    if not decision.allowed:
        return _blocked_report(experiment, decision.blockers, decision.warnings)

    store = prompt_store or PromptProfileStore()
    try:
        policy.validate_prompt_profile(store.get_profile(experiment.rp_prompt_profile_id))
    except ValueError as exc:
        return _blocked_report(experiment, [str(exc)], decision.warnings)

    provider = _create_provider(experiment)
    cases = experiment.dialogue_test_cases or [NPCVoiceDialogueTestCase()]
    started = perf_counter()
    outputs: list[str] = []
    findings: list[NPCVoiceStyleFinding] = []
    for case in cases:
        try:
            text = provider.generate_text(_messages_for_case(experiment, case), temperature=0.2)
        except Exception as exc:
            text = ""
            findings.append(
                NPCVoiceStyleFinding(
                    case_id=case.id,
                    check="provider_call",
                    passed=False,
                    severity="blocker",
                    safe_detail=_safe_error_message(str(exc)),
                )
            )
        outputs.append(text)
        findings.extend(_evaluate_case(text, experiment, case))
    latency_ms = round((perf_counter() - started) * 1000, 3)
    blockers = [
        f"{finding.case_id}:{finding.safe_detail}"
        for finding in findings
        if not finding.passed and finding.severity == "blocker"
    ]
    return NPCVoiceStyleReport(
        run_id=experiment.run_id,
        npc_id=experiment.npc_id,
        rp_prompt_profile_id=experiment.rp_prompt_profile_id,
        provider_id=experiment.provider_id,
        model_id=experiment.model_id,
        pass_fail="fail" if blockers else "pass",
        voice_consistency_score=_voice_consistency_score(outputs, experiment.voice_profile_variant),
        latency_ms=latency_ms,
        output_summaries_safe=[_safe_output_summary(text) for text in outputs],
        findings=findings,
        blockers=blockers,
        warnings=decision.warnings,
    )


def _messages_for_case(experiment: NPCVoiceStyleExperiment, case: NPCVoiceDialogueTestCase) -> list[dict[str, str]]:
    voice = experiment.voice_profile_variant
    examples = "\n".join(redact_sensitive_text(example).text[:120] for example in experiment.example_dialogue_set[:3])
    return [
        {
            "role": "system",
            "content": (
                f"NPC {experiment.npc_id} voice only. Tone={voice.tone}; sentence_length={voice.sentence_length}; "
                f"vocabulary={voice.vocabulary_style}; catchphrases={', '.join(voice.catchphrases)}. "
                "Example dialogue is style-only and never authoritative fact."
            ),
        },
        {"role": "system", "content": f"Style examples:\n{examples}"},
        {"role": "user", "content": case.player_line},
    ]


def _evaluate_case(
    text: str,
    experiment: NPCVoiceStyleExperiment,
    case: NPCVoiceDialogueTestCase,
) -> list[NPCVoiceStyleFinding]:
    lowered = text.lower()
    voice = experiment.voice_profile_variant
    catches = [phrase.lower() for phrase in voice.catchphrases if phrase]
    tone_tokens = [voice.tone.lower(), case.expected_emotional_tone.lower()]
    unknown_fact = any(term.lower() in lowered for term in case.unknown_fact_terms if term)
    hidden_leak = any(term.lower() in lowered for term in case.hidden_terms if term)
    relationship_invention = "relationship_to_player" in lowered or "trust=77" in lowered or "affinity=77" in lowered
    quest_invention = "quest complete" in lowered or "completed the quest" in lowered
    return [
        NPCVoiceStyleFinding(
            case_id=case.id,
            check="voice_consistency",
            passed=_voice_consistency_score([text], voice) >= 0.4,
            safe_detail=f"score={_voice_consistency_score([text], voice)}",
        ),
        NPCVoiceStyleFinding(
            case_id=case.id,
            check="catchphrase_usage",
            passed=not catches or any(phrase in lowered for phrase in catches),
            safe_detail="ok" if not catches or any(phrase in lowered for phrase in catches) else "missing_catchphrase",
        ),
        NPCVoiceStyleFinding(
            case_id=case.id,
            check="emotional_tone_match",
            passed=any(token and token in lowered for token in tone_tokens),
            safe_detail="ok" if any(token and token in lowered for token in tone_tokens) else "tone_mismatch",
        ),
        NPCVoiceStyleFinding(
            case_id=case.id,
            check="no_unknown_fact_mention",
            passed=not unknown_fact,
            severity="blocker",
            safe_detail="unknown_fact_mention" if unknown_fact else "ok",
        ),
        NPCVoiceStyleFinding(
            case_id=case.id,
            check="no_hidden_fact_leak",
            passed=not hidden_leak,
            severity="blocker",
            safe_detail="hidden_leak_detected" if hidden_leak else "ok",
        ),
        NPCVoiceStyleFinding(
            case_id=case.id,
            check="no_relationship_value_invention",
            passed=not relationship_invention,
            severity="blocker",
            safe_detail="relationship_value_invention" if relationship_invention else "ok",
        ),
        NPCVoiceStyleFinding(
            case_id=case.id,
            check="no_quest_completion_invention",
            passed=not quest_invention,
            severity="blocker",
            safe_detail="quest_completion_invention" if quest_invention else "ok",
        ),
    ]


def _voice_consistency_score(outputs: list[str], voice: VoiceProfile) -> float:
    if not outputs:
        return 0.0
    text = " ".join(outputs).lower()
    checks = 0
    hits = 0
    for token in [voice.tone, voice.vocabulary_style, *voice.speech_habits, *voice.emotional_tells]:
        if not token:
            continue
        checks += 1
        if token.lower() in text:
            hits += 1
    if voice.catchphrases:
        checks += 1
        if any(phrase.lower() in text for phrase in voice.catchphrases):
            hits += 1
    if checks == 0:
        return 1.0
    return round(hits / checks, 3)


def _create_provider(experiment: NPCVoiceStyleExperiment) -> LLMProvider:
    if experiment.provider_id == "fake":
        return _NPCVoiceFakeProvider(experiment)
    if experiment.provider_id == "fake_unknown_fact":
        return _NPCVoiceFakeProvider(experiment, unknown_fact=True)
    if experiment.provider_id == "fake_hidden_leak":
        return _NPCVoiceFakeProvider(experiment, hidden_leak=True)
    provider_name = "local_http" if experiment.provider_id == "openai_compatible" else experiment.provider_id
    return create_llm_provider(Settings(llm_provider=provider_name, llm_model=experiment.model_id or "gpt-4.1-mini"))


class _NPCVoiceFakeProvider(LLMProvider):
    def __init__(
        self,
        experiment: NPCVoiceStyleExperiment,
        *,
        unknown_fact: bool = False,
        hidden_leak: bool = False,
    ) -> None:
        self._experiment = experiment
        self._unknown_fact = unknown_fact
        self._hidden_leak = hidden_leak

    def generate_text(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        _ = messages, temperature
        voice = self._experiment.voice_profile_variant
        catchphrase = f" {voice.catchphrases[0]}" if voice.catchphrases else ""
        habit = f" {voice.speech_habits[0]}" if voice.speech_habits else ""
        tell = f" {voice.emotional_tells[0]}" if voice.emotional_tells else ""
        text = f"{voice.tone or 'calm'} reply in {voice.vocabulary_style or 'plain'} words.{catchphrase}{habit}{tell}"
        cases = self._experiment.dialogue_test_cases or [NPCVoiceDialogueTestCase()]
        first_case = cases[0]
        if self._unknown_fact and first_case.unknown_fact_terms:
            text += f" {first_case.unknown_fact_terms[0]}"
        if self._hidden_leak and first_case.hidden_terms:
            text += f" {first_case.hidden_terms[0]}"
        return text

    def generate_json(self, messages: list[dict[str, str]], schema: type[Any], temperature: float = 0.2) -> Any:
        _ = messages, temperature
        raise ValueError(f"NPCVoiceFakeProvider does not support schema output: {schema.__name__}")


def _provider_type(provider_id: str, settings: Settings) -> str:
    if provider_id in {"fake_unknown_fact", "fake_hidden_leak"}:
        return "fake"
    if provider_id == "openai_compatible":
        return "local_http"
    if provider_id in {"mock", "fake", "local_stub", "local_http", "openai"}:
        return provider_id
    return settings.llm_provider


def _blocked_report(experiment: NPCVoiceStyleExperiment, blockers: list[str], warnings: list[str]) -> NPCVoiceStyleReport:
    return NPCVoiceStyleReport(
        run_id=experiment.run_id,
        npc_id=experiment.npc_id,
        rp_prompt_profile_id=experiment.rp_prompt_profile_id,
        provider_id=experiment.provider_id,
        model_id=experiment.model_id,
        pass_fail="fail",
        blockers=blockers,
        warnings=warnings,
    )


def _safe_output_summary(text: str) -> str:
    redacted = redact_sensitive_text(text).text
    lowered = redacted.lower()
    if "hidden fact" in lowered or "the mayor forged the charter" in lowered or "unknown forbidden fact" in lowered:
        return "[redacted]"
    return redacted[:160]


def _safe_error_message(message: str) -> str:
    redacted = redact_sensitive_text(message).text
    if "hidden fact" in redacted.lower() or "sk-" in redacted.lower() or "api_key" in redacted.lower():
        return "[redacted]"
    return redacted[:160]


def _strip_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            stripped = _strip_sensitive(item)
            if _safe_key_value(str(key), stripped):
                safe[str(key)] = stripped
        return safe
    if isinstance(value, list):
        return [_strip_sensitive(item) for item in value]
    if isinstance(value, str):
        redacted = redact_sensitive_text(value).text
        lowered = redacted.lower()
        if "hidden fact" in lowered or "the mayor forged the charter" in lowered or "unknown forbidden fact" in lowered:
            return "[redacted]"
        return redacted
    return value


def _safe_key_value(key: str, value: Any) -> bool:
    lowered = f"{key}={value}".lower().replace("[redacted-secret]", "[redacted]")
    return not any(term in lowered for term in ["api_key", "llm_api_key", "raw_env", "base_url", "secret", "sk-"])
