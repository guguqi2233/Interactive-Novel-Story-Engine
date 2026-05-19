from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pydantic import ValidationError

from app.config import Settings
from app.core.world_state import FactState, FactVisibility, GameState, LocationState, NPCState
from app.llm.context_inspector import ContextInspectRequest, ContextInspectType, inspect_context
from app.llm.fake_provider import FakeLLMProvider
from app.llm.local_model_diagnostics import LocalModelDiagnosticRequest, run_local_model_diagnostics
from app.llm.model_compatibility import build_model_compatibility_matrix
from app.llm.prompt_ab_test import PromptABTestCase, PromptABTestRun, PromptABUseCase, run_prompt_ab_test
from app.llm.prompt_diff import PromptDiffRequest, review_prompt_diff
from app.llm.prompt_experiment_packages import (
    PromptExperimentPackageImportRequest,
    export_prompt_experiment_package,
    import_prompt_experiment_package_dry_run,
)
from app.llm.prompt_profiles import PromptProfile, PromptProfileStore, RPPromptProfile
from app.llm.prompt_regression import PromptRegressionRun, run_prompt_regression
from app.llm.provider_benchmark import ProviderBenchmarkRun, ProviderBenchmarkType, run_provider_benchmark
from app.llm.provider_capabilities import ProviderCapabilityRegistry
from app.llm.provider_factory import create_llm_provider
from app.llm.provider_router import ProviderRouter, ProviderRoutingRule, ProviderRoutingUseCase
from app.llm.schemas import NarrativeResult
from app.llm.structured_output_reliability import (
    StructuredOutputReliabilityRun,
    StructuredOutputSchemaName,
    StructuredOutputTestCase,
    run_structured_output_reliability,
)
from app.llm.token_budget import TokenBudgetRequest, build_default_token_budget_profiles, estimate_token_budget
from app.llm.usage_tracker import get_model_usage_store, wrap_provider_for_usage_tracking
from app.llm.narrator_style_lab import NarratorStyleExperiment, run_narrator_style_experiment
from app.llm.npc_voice_style_lab import NPCVoiceStyleExperiment, run_npc_voice_style_experiment


SECRET_TEXT = "the mayor forged the charter"


def setup_function() -> None:
    store = get_model_usage_store()
    store.clear()
    store.enabled = False


def teardown_function() -> None:
    store = get_model_usage_store()
    store.clear()
    store.enabled = False


def test_v15_provider_capability_and_benchmark_boundary() -> None:
    registry = ProviderCapabilityRegistry()
    summary = registry.safe_summary_for_frontend(Settings(llm_provider="openai", llm_api_key="sk-real-looking-secret"))
    validation = registry.validate_model_for_use_case("local_stub", "local_stub", "structured_output")
    benchmark = run_provider_benchmark(
        ProviderBenchmarkRun(provider_id="fake", benchmark_types=[ProviderBenchmarkType.GENERATE_TEXT_SMOKE])
    )
    real_blocked = run_provider_benchmark(
        ProviderBenchmarkRun(provider_id="openai", benchmark_types=[ProviderBenchmarkType.GENERATE_TEXT_SMOKE])
    )
    rendered = json.dumps({"summary": summary, "benchmark": benchmark.model_dump_safe()}, ensure_ascii=False)

    assert registry.list_providers()
    assert registry.list_models()
    assert validation.allowed
    assert benchmark.total_cases == 1
    assert real_blocked.real_provider_blocked
    assert "sk-real-looking-secret" not in rendered
    assert SECRET_TEXT not in rendered


def test_v15_structured_output_and_prompt_style_labs_are_safe() -> None:
    structured = run_structured_output_reliability(
        StructuredOutputReliabilityRun(
            provider_id="fake",
            cases=[StructuredOutputTestCase(id="invalid_json", schema_name=StructuredOutputSchemaName.PLAYER_INTENT)],
        )
    )
    ab = run_prompt_ab_test(
        PromptABTestRun(
            profile_a_id="default_safe",
            profile_b_id="local_story",
            use_case=PromptABUseCase.NARRATOR,
            test_cases=[PromptABTestCase(id="leak_case", hidden_terms=[SECRET_TEXT])],
        )
    )
    action_reason = "You look around and see a public bell."
    style = run_narrator_style_experiment(
        NarratorStyleExperiment(prompt_profile_id="default_safe", action_reason=action_reason, hidden_terms=[SECRET_TEXT])
    )
    voice = run_npc_voice_style_experiment(
        NPCVoiceStyleExperiment(
            npc_id="mira",
            dialogue_test_cases=[{"id": "voice_leak", "hidden_terms": [SECRET_TEXT], "unknown_fact_terms": ["unknown crime"]}],
        )
    )
    rendered = json.dumps(
        [structured.model_dump_safe(), ab.model_dump_safe(), style.model_dump_safe(), voice.model_dump_safe()],
        ensure_ascii=False,
    )

    assert structured.total_cases == 1
    assert ab.cases
    assert style.blockers == []
    assert style.output_summary_safe
    assert action_reason == "You look around and see a public bell."
    assert voice.findings
    assert "unknown_fact" in rendered or "hidden" in rendered
    assert SECRET_TEXT not in rendered
    assert "sk-" not in rendered


def test_v15_usage_tracking_context_diff_and_budget_boundaries() -> None:
    provider = wrap_provider_for_usage_tracking(
        FakeLLMProvider(text_responses=["safe output"]),
        provider_id="fake",
        model_id="fake",
        enabled=True,
    )
    provider.generate_text([{"role": "user", "content": "LLM_API_KEY=sk-real-looking-secret hidden fact text"}])
    usage_payload = json.dumps(get_model_usage_store().summary().model_dump(mode="json"), ensure_ascii=False)
    snapshot = inspect_context(
        ContextInspectRequest(context_type=ContextInspectType.NARRATOR, state=_state(), location_id="square", npc_id="mira")
    )
    diff = review_prompt_diff(
        PromptDiffRequest(
            left={"hidden_fact_policy": "deny", "state_modification_policy": "deny"},
            right={"hidden_fact_policy": "allow", "state_modification_policy": "deny"},
        )
    )
    budget = estimate_token_budget(TokenBudgetRequest(profile=build_default_token_budget_profiles()[0], sections=snapshot.sections))
    budget_sections = {section.section_type: section for section in budget.sections}

    assert get_model_usage_store().summary().total_calls == 1
    assert "sk-real-looking-secret" not in usage_payload
    assert "hidden fact text" not in usage_payload
    assert SECRET_TEXT not in json.dumps(snapshot.model_dump_safe(), ensure_ascii=False)
    assert "hidden_fact_policy_relaxed" in diff.blockers
    assert budget.final_context_tokens <= budget.available_context_tokens
    assert any(section.protected for section in budget.sections)
    assert budget_sections.get("safety_constraints") is None or budget_sections["safety_constraints"].dropped is False


def test_v15_compatibility_routing_diagnostics_and_factory_boundary() -> None:
    matrix = build_model_compatibility_matrix()
    router = ProviderRouter()
    invalid_rule = ProviderRoutingRule(
        use_case=ProviderRoutingUseCase.NARRATOR,
        primary_provider_id="missing",
        primary_model_id="missing",
    )
    json_rule = ProviderRoutingRule(
        use_case=ProviderRoutingUseCase.STRUCTURED_JSON,
        primary_provider_id="mock",
        primary_model_id="mock",
    )
    diagnostic = run_local_model_diagnostics(LocalModelDiagnosticRequest(provider_id="local_stub", fake_mode="ok"))
    missing_base = run_local_model_diagnostics(LocalModelDiagnosticRequest(provider_id="local_http"), settings=Settings(local_llm_base_url=""))
    provider = create_llm_provider(Settings(llm_provider="local_stub"))

    assert matrix.rows
    assert not router.validate_routing_rule(invalid_rule).ok
    assert router.validate_routing_rule(json_rule).ok
    assert diagnostic.pass_fail == "pass"
    assert "local_http_base_url_missing" in missing_base.blockers
    assert provider.__class__.__name__ in {"LocalStubProvider", "UsageTrackingProvider"}


def test_v15_prompt_experiment_package_and_profile_boundaries() -> None:
    store = PromptProfileStore()
    selected = store.selected_profile_id()
    package = export_prompt_experiment_package(
        request=_export_request_with_secret_case(),
        prompt_store=store,
    )
    dry_run = import_prompt_experiment_package_dry_run(
        PromptExperimentPackageImportRequest(package=package),
        prompt_store=store,
    )
    payload = json.dumps(package.model_dump(mode="json"), ensure_ascii=False)

    assert "sk-real-looking-secret" not in payload
    assert SECRET_TEXT not in payload
    assert dry_run.applied is False
    assert dry_run.selected_profile_id_after == selected
    assert store.selected_profile_id() == selected
    try:
        RPPromptProfile(hidden_fact_policy="allow")  # type: ignore[arg-type]
    except ValidationError:
        pass
    else:
        raise AssertionError("Prompt profile hidden fact policy must not be relaxed")


def test_v15_prompt_lab_cli_defaults_do_not_call_real_provider() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "app.tools.prompt_lab", "--json", "benchmark-provider", "--provider", "openai"],
        cwd=Path.cwd() / "backend",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["real_provider_blocked"] is True
    assert "sk-" not in result.stdout
    assert SECRET_TEXT not in result.stdout


def test_v15_benchmark_and_eval_do_not_modify_game_state_or_save() -> None:
    state = _state()
    before = state.model_dump_json()

    run_provider_benchmark(ProviderBenchmarkRun(provider_id="fake"))
    run_prompt_regression(PromptRegressionRun())
    run_structured_output_reliability(StructuredOutputReliabilityRun(provider_id="fake"))

    assert state.model_dump_json() == before


def _state() -> GameState:
    return GameState(
        world_id="v15_world",
        locations={"square": LocationState(id="square", name="Square")},
        npcs={"mira": NPCState(id="mira", location_id="square", knowledge=["public_fact"])},
        facts={
            "public_fact": FactState(id="public_fact", text="A public bell rings.", visibility=FactVisibility.PUBLIC, public=True),
            "hidden_fact": FactState(id="hidden_fact", text=SECRET_TEXT, visibility=FactVisibility.HIDDEN),
        },
        player_visible_facts={"public_fact"},
    )


def _export_request_with_secret_case():
    from app.llm.prompt_experiment_packages import PromptExperimentPackageExportRequest

    return PromptExperimentPackageExportRequest(
        package_id="v15_prompt_pack",
        name="V15 Prompt Pack",
        test_cases=[
            PromptABTestCase(
                id="secret_case",
                input_text="LLM_API_KEY=sk-real-looking-secret",
                hidden_terms=[SECRET_TEXT],
            )
        ],
    )
