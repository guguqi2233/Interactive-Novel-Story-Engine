from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from time import perf_counter
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.config import Settings
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.llm.model_prompt_lab_policy import BenchmarkRun, ModelPromptLabPolicy, ProviderProfile, redact_sensitive_text
from app.llm.narrator import Narrator
from app.llm.provider_base import LLMProvider, LLMProviderError
from app.llm.provider_factory import create_llm_provider
from app.llm.prompt_profiles import PromptProfile, PromptProfileStore
from app.llm.schemas import NarrativeResult


class NarratorStylePerspective(StrEnum):
    SECOND_PERSON = "second_person"
    CLOSE_THIRD = "close_third"
    DISTANT_THIRD = "distant_third"


class NarratorStyleExperiment(BaseModel):
    run_id: str = Field(default_factory=lambda: f"narrator-style-{uuid4().hex}")
    prompt_profile_id: str = "default_safe"
    scene_mood_id: str | None = None
    perspective: str = NarratorStylePerspective.SECOND_PERSON.value
    prose_density: str = "balanced"
    response_length: str = "medium"
    sensory_focus: str = "balanced"
    genre_tone: str = "grounded"
    provider_id: str = "fake"
    model_id: str | None = None
    allow_real_provider: bool = False
    player_input: str = "observe the square"
    visible_facts: list[str] = Field(default_factory=lambda: ["visible_square"])
    hidden_terms: list[str] = Field(default_factory=list)
    action_reason: str = "Safe visible observation."
    expected_action: str = "observe"


class NarratorStyleFinding(BaseModel):
    check: str
    passed: bool
    severity: str = "warning"
    safe_detail: str = ""


class NarratorStyleReport(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    prompt_profile_id: str
    scene_mood_id: str | None = None
    provider_id: str
    model_id: str | None = None
    pass_fail: str
    output_summary_safe: str = ""
    style_score: float = 0.0
    latency_ms: float = 0.0
    suggested_actions: list[str] = Field(default_factory=list)
    findings: list[NarratorStyleFinding] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


def run_narrator_style_experiment(
    experiment: NarratorStyleExperiment,
    *,
    prompt_store: PromptProfileStore | None = None,
    settings: Settings | None = None,
) -> NarratorStyleReport:
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
        profile = policy.validate_prompt_profile(store.get_profile(experiment.prompt_profile_id))
    except ValueError as exc:
        return _blocked_report(experiment, [str(exc)], decision.warnings)

    before_reason = experiment.action_reason
    provider = _create_provider(experiment)
    started = perf_counter()
    try:
        result = Narrator(provider, prompt_profile=profile).render(
            player_input=experiment.player_input,
            action_result=ActionResult(
                success_level=SuccessLevel.SUCCESS,
                reason=experiment.action_reason,
                visible_facts=experiment.visible_facts,
            ),
            visible_facts=experiment.visible_facts,
            current_location="square",
            tone=_style_tone(experiment),
            scene_mood_summary=experiment.scene_mood_id or "",
        )
        latency_ms = round((perf_counter() - started) * 1000, 3)
    except Exception as exc:
        latency_ms = round((perf_counter() - started) * 1000, 3)
        return NarratorStyleReport(
            run_id=experiment.run_id,
            prompt_profile_id=experiment.prompt_profile_id,
            scene_mood_id=experiment.scene_mood_id,
            provider_id=experiment.provider_id,
            model_id=experiment.model_id,
            pass_fail="fail",
            latency_ms=latency_ms,
            blockers=[_safe_error_message(str(exc))],
            warnings=decision.warnings,
        )

    findings = _evaluate_output(result, experiment, before_reason)
    blockers = [finding.safe_detail for finding in findings if not finding.passed and finding.severity == "blocker"]
    return NarratorStyleReport(
        run_id=experiment.run_id,
        prompt_profile_id=experiment.prompt_profile_id,
        scene_mood_id=experiment.scene_mood_id,
        provider_id=experiment.provider_id,
        model_id=experiment.model_id,
        pass_fail="fail" if blockers else "pass",
        output_summary_safe=redact_sensitive_text(result.short_summary or result.text).text[:160],
        style_score=_style_score(result.text, experiment),
        latency_ms=latency_ms,
        suggested_actions=result.suggested_actions,
        findings=findings,
        blockers=blockers,
        warnings=decision.warnings,
    )


def _style_tone(experiment: NarratorStyleExperiment) -> str:
    return (
        f"perspective={experiment.perspective}; prose_density={experiment.prose_density}; "
        f"response_length={experiment.response_length}; sensory_focus={experiment.sensory_focus}; "
        f"genre_tone={experiment.genre_tone}"
    )


def _evaluate_output(result: NarrativeResult, experiment: NarratorStyleExperiment, before_reason: str) -> list[NarratorStyleFinding]:
    text = result.text
    lowered = text.lower()
    hidden_leak = any(term.lower() in lowered for term in experiment.hidden_terms if term)
    invented_item = "item:" in lowered or "key item" in lowered or "silver key" in lowered
    contradiction = before_reason != experiment.action_reason or "failed" in lowered and experiment.expected_action == "observe"
    word_count = len([word for word in text.split() if word])
    concise_limit = {"short": 60, "medium": 140, "long": 260}.get(experiment.response_length, 140)
    style_match = _style_score(text, experiment) >= 0.5
    invalid_actions = [action for action in result.suggested_actions if action not in {"observe", "search", "wait", "talk", "move"}]
    return [
        NarratorStyleFinding(check="no_invented_key_item", passed=not invented_item, severity="blocker", safe_detail="invented_key_item_detected" if invented_item else "ok"),
        NarratorStyleFinding(check="no_hidden_fact_leak", passed=not hidden_leak, severity="blocker", safe_detail="hidden_leak_detected" if hidden_leak else "ok"),
        NarratorStyleFinding(check="no_contradiction_with_action_result", passed=not contradiction, severity="blocker", safe_detail="action_result_contradiction" if contradiction else "ok"),
        NarratorStyleFinding(check="concise_enough", passed=word_count <= concise_limit, safe_detail=f"word_count={word_count}"),
        NarratorStyleFinding(check="style_match", passed=style_match, safe_detail=f"score={_style_score(text, experiment)}"),
        NarratorStyleFinding(check="suggested_actions_validity", passed=not invalid_actions, severity="blocker", safe_detail="invalid_suggested_action" if invalid_actions else "ok"),
    ]


def _style_score(text: str, experiment: NarratorStyleExperiment) -> float:
    lowered = text.lower()
    hits = 0
    for token in [experiment.genre_tone, experiment.sensory_focus, experiment.prose_density]:
        if token and token.lower() in lowered:
            hits += 1
    if experiment.perspective == "second_person" and ("you " in lowered or lowered.startswith("you")):
        hits += 1
    return round(min(1.0, hits / 4), 3)


def _create_provider(experiment: NarratorStyleExperiment) -> LLMProvider:
    if experiment.provider_id == "fake":
        return _NarratorStyleFakeProvider(experiment)
    if experiment.provider_id == "fake_hidden_leak":
        return _NarratorStyleFakeProvider(experiment, leak_hidden=True)
    if experiment.provider_id == "fake_invented_item":
        return _NarratorStyleFakeProvider(experiment, invented_item=True)
    provider_name = "local_http" if experiment.provider_id == "openai_compatible" else experiment.provider_id
    return create_llm_provider(Settings(llm_provider=provider_name, llm_model=experiment.model_id or "gpt-4.1-mini"))


class _NarratorStyleFakeProvider(LLMProvider):
    def __init__(self, experiment: NarratorStyleExperiment, *, leak_hidden: bool = False, invented_item: bool = False) -> None:
        self._experiment = experiment
        self._leak_hidden = leak_hidden
        self._invented_item = invented_item

    def generate_text(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        _ = messages, temperature
        return "safe narrator style text"

    def generate_json(self, messages: list[dict[str, str]], schema: type[Any], temperature: float = 0.2) -> Any:
        _ = messages, temperature
        if schema is not NarrativeResult:
            raise LLMProviderError(f"NarratorStyleFakeProvider does not support schema: {schema.__name__}")
        text = f"You notice a {self._experiment.genre_tone} scene with {self._experiment.sensory_focus} details and {self._experiment.prose_density} prose."
        if self._leak_hidden and self._experiment.hidden_terms:
            text += f" {self._experiment.hidden_terms[0]}"
        if self._invented_item:
            text += " A silver key item appears."
        return schema.model_validate(
            {
                "text": text,
                "suggested_actions": ["observe", "search"],
                "short_summary": "Safe narrator style sample.",
            }
        )


def _provider_type(provider_id: str, settings: Settings) -> str:
    if provider_id in {"fake_hidden_leak", "fake_invented_item"}:
        return "fake"
    if provider_id == "openai_compatible":
        return "local_http"
    if provider_id in {"mock", "fake", "local_stub", "local_http", "openai"}:
        return provider_id
    return settings.llm_provider


def _blocked_report(experiment: NarratorStyleExperiment, blockers: list[str], warnings: list[str]) -> NarratorStyleReport:
    return NarratorStyleReport(
        run_id=experiment.run_id,
        prompt_profile_id=experiment.prompt_profile_id,
        scene_mood_id=experiment.scene_mood_id,
        provider_id=experiment.provider_id,
        model_id=experiment.model_id,
        pass_fail="fail",
        blockers=blockers,
        warnings=warnings,
    )


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
        if "the mayor forged the charter" in redacted.lower() or "hidden fact" in redacted.lower():
            return "[redacted]"
        return redacted
    return value


def _safe_key_value(key: str, value: Any) -> bool:
    lowered = f"{key}={value}".lower().replace("[redacted-secret]", "[redacted]")
    return not any(term in lowered for term in ["api_key", "llm_api_key", "raw_env", "base_url", "secret", "sk-"])
