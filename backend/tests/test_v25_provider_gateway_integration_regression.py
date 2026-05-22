import base64
import json
import re
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import EventLog
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactState, FactVisibility, GameState, LocationState, PlayerState
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.llm.provider_base import LLMProvider, LLMProviderError, Message, SchemaT
from app.llm.provider_benchmark import ProviderBenchmarkRun, ProviderBenchmarkType, run_provider_benchmark
from app.llm.provider_capabilities import ModelCapability, ProviderCapability, ProviderCapabilityRegistry, ProviderType
from app.llm.provider_gateway import ProviderGateway
from app.llm.provider_profiles import (
    FakeProviderSecretResolver,
    ModelProfile,
    ProviderMode,
    ProviderProfileRepository,
    ProviderProfileV2,
    ProviderSafetyPolicy,
    ProviderSimulationBehavior,
    ProviderSimulationProfile,
    SimulatedProvider,
)
from app.llm.provider_router import ProviderRouter, ProviderRoutingConfig, ProviderRoutingContext, ProviderRoutingRule, ProviderRoutingUseCase
from app.llm.schemas import MemorySummary, NarrativeResult, PlayerIntent
from app.llm.structured_output_reliability import StructuredOutputReliabilityRun, StructuredOutputSchemaName, StructuredOutputTestCase, run_structured_output_reliability
from app.llm.usage_tracker import ModelUsageRecord, get_model_usage_store, wrap_provider_for_usage_tracking
from app.main import app
from app.platform.cross_mode import CrossModeDirection, CrossModeProposal, CrossModeRepository, TavernToWorldApplyService
from app.platform.narrative_project import NarrativeProject
from app.platform.novel_studio import GeneratedNovelDraft, NovelDraftGenerationService, NovelPromptContext
from app.platform.project_packages import export_project
from app.platform.project_repository import ProjectRepository
from app.platform.tavern_studio import GeneratedTavernReply, TavernPromptContext, TavernResponseGenerationService


HIDDEN_SENTINEL = "the hidden regent keeps the black ledger"
SECRET_SENTINEL = "sk-test-hidden-sentinel"


def setup_function() -> None:
    store = get_model_usage_store()
    store.clear()
    store.enabled = False


class RecordingProvider(LLMProvider):
    def __init__(self) -> None:
        self.messages: list[list[Message]] = []
        self.schemas: list[str] = []

    def generate_text(self, messages: list[Message], temperature: float = 0.7) -> str:
        self.messages.append(messages)
        return "safe routed text"

    def generate_json(self, messages: list[Message], schema: type[SchemaT], temperature: float = 0.2) -> SchemaT:
        self.messages.append(messages)
        self.schemas.append(schema.__name__)
        payload = _sample_payload(schema.__name__)
        return schema.model_validate(payload)


def _sample_payload(schema_name: str) -> dict[str, object]:
    if schema_name == "PlayerIntent":
        return {"action_type": "observe", "raw_text": "look", "confidence": 0.9, "requires_clarification": False}
    if schema_name == "NarrativeResult":
        return {"text": "You see a safe square.", "suggested_actions": ["observe"], "short_summary": "safe"}
    if schema_name == "MemorySummary":
        return {"summary": "Safe memory.", "important_facts": [], "open_threads": []}
    if schema_name == "GeneratedNovelDraft":
        return {"text": "Safe novel draft.", "summary": "safe"}
    if schema_name == "GeneratedTavernReply":
        return {"content": "Safe tavern reply.", "speaker_id": "mira"}
    raise AssertionError(f"Unexpected schema {schema_name}")


def _project_repo(tmp_path: Path) -> ProjectRepository:
    root = tmp_path / "projects"
    project_root = root / "demo"
    repo = ProjectRepository(root)
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    return repo


def _router_config(use_case: ProviderRoutingUseCase, *, primary: str = "local_http", primary_model: str = "local-model", fallback: str | None = "mock", fallback_model: str | None = "mock") -> ProviderRouter:
    return ProviderRouter(
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case=use_case,
                    primary_provider_id=primary,
                    primary_model_id=primary_model,
                    fallback_provider_id=fallback,
                    fallback_model_id=fallback_model,
                    require_json_support=use_case
                    in {
                        ProviderRoutingUseCase.WORLD_INTENT_PARSE,
                        ProviderRoutingUseCase.CROSS_MODE_DRAFT,
                        ProviderRoutingUseCase.STRUCTURED_JSON,
                        ProviderRoutingUseCase.QUALITY_EVAL,
                    },
                )
            ]
        )
    )


def test_provider_profile_secrets_api_and_export_are_safe(tmp_path: Path) -> None:
    repo = _project_repo(tmp_path)
    app.state.project_repository = repo
    previous_settings = getattr(app.state, "settings", None)
    profile = {
        "provider_profile_id": "relay_safe",
        "display_name": "Relay Safe",
        "provider_type": "relay",
        "base_url_env": "RELAY_BASE_URL",
        "api_key_env": "RELAY_API_KEY",
        "model_profiles": [{"model_id": "relay-chat", "supports_json": True}],
        "allowed_modes": ["novel", "tavern", "world", "cross_mode", "quality"],
    }

    try:
        app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
        client = TestClient(app)
        created = client.post("/projects/demo/providers", json=profile)
        listed = client.get("/projects/demo/providers")
        updated = client.patch("/projects/demo/providers/relay_safe", json={"display_name": "Relay Updated"})
        validated = client.post("/projects/demo/providers/relay_safe/validate")
        status = client.get("/projects/demo/providers/relay_safe/status")
        matrix = client.get("/projects/demo/providers/capability-matrix")
        rejected = client.post("/projects/demo/providers", json={**profile, "provider_profile_id": "bad", "api_key": "sk-not-allowed-realistic-secret"})
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")

    assert created.status_code == 200
    assert created.json()["provider"]["provider_profile_id"] == "relay_safe"
    assert listed.json()["providers"][0]["display_name"] == "Relay Safe"
    assert updated.json()["provider"]["display_name"] == "Relay Updated"
    assert validated.json()["ok"] is True
    assert status.json()["status"] == "configured"
    assert matrix.json()["matrix"]["rows"]
    assert rejected.status_code == 422
    rendered = created.text + listed.text + updated.text + validated.text + status.text + matrix.text
    assert SECRET_SENTINEL not in rendered
    assert "sk-not-allowed" not in rendered

    archive = export_project("demo", repo, sections=["providers/profiles"])
    raw = base64.b64decode(archive.archive_base64)
    with ZipFile(BytesIO(raw)) as bundle:
        exported_text = "\n".join(bundle.read(name).decode("utf-8", errors="ignore") for name in bundle.namelist() if name.endswith((".yaml", ".json")))
    assert SECRET_SENTINEL not in exported_text
    assert "api_key: " not in exported_text


def test_provider_profile_rejects_raw_key_and_fake_resolver_supports_refs() -> None:
    with pytest.raises(ValueError):
        ProviderProfileV2(provider_profile_id="bad", display_name="Bad", provider_type="mock", api_key="sk-real-looking-secret")  # type: ignore[call-arg]

    profile = ProviderProfileV2(provider_profile_id="ok", display_name="OK", provider_type="relay", base_url_env="RELAY_BASE_URL", api_key_env="RELAY_API_KEY")
    resolver = FakeProviderSecretResolver({"RELAY_API_KEY": SECRET_SENTINEL}, {"RELAY_BASE_URL": "http://relay.invalid/v1"})

    assert resolver.resolve_api_key(profile) == SECRET_SENTINEL
    assert SECRET_SENTINEL not in json.dumps(profile.safe_summary())


def test_frontend_provider_ui_has_no_plaintext_api_key_field() -> None:
    app_source = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    api_source = Path("frontend/src/api.ts").read_text(encoding="utf-8")

    assert 'name="api_key"' not in app_source
    assert re.search(r"\bapi_key\s*:", api_source) is None
    assert "api_key_env" in app_source
    assert "secret_ref" in app_source


def test_routing_covers_modes_and_missing_capability_fallback() -> None:
    router = ProviderRouter(
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(use_case="novel_draft", primary_provider_id="local_stub", primary_model_id="local_stub"),
                ProviderRoutingRule(use_case="tavern_reply", primary_provider_id="local_http", primary_model_id="local-model"),
                ProviderRoutingRule(use_case="world_intent_parse", primary_provider_id="local_stub", primary_model_id="local_stub", require_json_support=True),
                ProviderRoutingRule(use_case="cross_mode_draft", primary_provider_id="local_stub", primary_model_id="local_stub", require_json_support=True),
                ProviderRoutingRule(use_case="structured_json", primary_provider_id="text_only", primary_model_id="text", fallback_provider_id="mock", fallback_model_id="mock", require_json_support=True),
            ]
        ),
        registry=ProviderCapabilityRegistry(
            providers=[
                ProviderCapability(provider_id="local_stub", provider_type=ProviderType.LOCAL_STUB, local_only=True),
                ProviderCapability(provider_id="local_http", provider_type=ProviderType.LOCAL_HTTP, local_only=True),
                ProviderCapability(provider_id="mock", provider_type=ProviderType.MOCK, local_only=True),
                ProviderCapability(provider_id="text_only", provider_type=ProviderType.LOCAL_STUB, local_only=True),
            ],
            models=[
                ModelCapability(provider_id="local_stub", provider_type=ProviderType.LOCAL_STUB, model_id="local_stub", supports_json=True, recommended_use_cases=["narration", "structured_output"]),
                ModelCapability(provider_id="local_http", provider_type=ProviderType.LOCAL_HTTP, model_id="local-model", supports_json=True, recommended_use_cases=["rp_expression", "structured_output"]),
                ModelCapability(provider_id="mock", provider_type=ProviderType.MOCK, model_id="mock", supports_json=True, recommended_use_cases=["structured_output"]),
                ModelCapability(provider_id="text_only", provider_type=ProviderType.LOCAL_STUB, model_id="text", supports_json=False, recommended_use_cases=["narration"]),
            ],
        ),
    )

    assert router.select_model_for_use_case("novel_draft").provider_id == "local_stub"
    assert router.select_model_for_use_case("tavern_reply").provider_id == "local_http"
    assert router.select_model_for_use_case("world_intent_parse").provider_id == "local_stub"
    assert router.select_model_for_use_case("cross_mode_draft").provider_id == "local_stub"
    fallback = router.select_model_for_use_case("structured_json")
    assert fallback.used_fallback
    assert fallback.provider_id == "mock"


def test_gateway_runtime_fallback_timeout_schema_failure_skip_and_all_failed() -> None:
    timeout = SimulatedProvider(ProviderSimulationProfile(default_behavior=ProviderSimulationBehavior.TIMEOUT), provider_profile_id="local_http", model_id="local-model")
    mismatch = SimulatedProvider(ProviderSimulationProfile(default_behavior=ProviderSimulationBehavior.SCHEMA_MISMATCH), provider_profile_id="local_http", model_id="local-model")
    success = SimulatedProvider(ProviderSimulationProfile(default_behavior=ProviderSimulationBehavior.SUCCESS_JSON), provider_profile_id="mock", model_id="mock")
    error = SimulatedProvider(ProviderSimulationProfile(default_behavior=ProviderSimulationBehavior.PROVIDER_ERROR), provider_profile_id="mock", model_id="mock")

    context = ProviderRoutingContext(mode="world", use_case="world_intent_parse")
    gateway = ProviderGateway({"local_http": timeout, "mock": success}, router=_router_config(ProviderRoutingUseCase.WORLD_INTENT_PARSE))
    assert gateway.generate_json(context, [{"role": "user", "content": "look"}], PlayerIntent).raw_text == "observe"
    assert [trace.provider_profile_id for trace in gateway.traces] == ["local_http", "mock"]

    gateway = ProviderGateway({"local_http": mismatch, "mock": success}, router=_router_config(ProviderRoutingUseCase.WORLD_INTENT_PARSE))
    assert gateway.generate_json(context, [{"role": "user", "content": "look"}], PlayerIntent).action_type.value == "observe"
    assert gateway.traces[0].error_type == "schema_validation_failed"

    text_only_registry = ProviderCapabilityRegistry(
        providers=[
            ProviderCapability(provider_id="local_http", provider_type=ProviderType.LOCAL_HTTP),
            ProviderCapability(provider_id="text_only", provider_type=ProviderType.LOCAL_STUB),
        ],
        models=[
            ModelCapability(provider_id="local_http", provider_type=ProviderType.LOCAL_HTTP, model_id="local-model", supports_json=True),
            ModelCapability(provider_id="text_only", provider_type=ProviderType.LOCAL_STUB, model_id="text", supports_json=False),
        ],
    )
    skip_router = ProviderRouter(
        registry=text_only_registry,
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case="world_intent_parse",
                    primary_provider_id="local_http",
                    primary_model_id="local-model",
                    fallback_provider_id="text_only",
                    fallback_model_id="text",
                    require_json_support=True,
                )
            ]
        ),
    )
    gateway = ProviderGateway({"local_http": timeout, "text_only": success}, router=skip_router)
    with pytest.raises(LLMProviderError, match="timeout"):
        gateway.generate_json(context, [{"role": "user", "content": "look"}], PlayerIntent)
    assert [trace.provider_profile_id for trace in gateway.traces] == ["local_http"]

    gateway = ProviderGateway({"local_http": timeout, "mock": error}, router=_router_config(ProviderRoutingUseCase.WORLD_INTENT_PARSE))
    with pytest.raises(LLMProviderError, match="timeout"):
        gateway.generate_json(context, [{"role": "user", "content": "look"}], PlayerIntent)


def test_gateway_fallback_must_satisfy_same_safety_policy() -> None:
    timeout = SimulatedProvider(ProviderSimulationProfile(default_behavior=ProviderSimulationBehavior.TIMEOUT), provider_profile_id="local_http", model_id="local-model")
    cloud_success = SimulatedProvider(ProviderSimulationProfile(default_behavior=ProviderSimulationBehavior.SUCCESS_JSON), provider_profile_id="openai", model_id="gpt-4.1-mini")
    router = ProviderRouter(
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case="world_intent_parse",
                    primary_provider_id="local_http",
                    primary_model_id="local-model",
                    fallback_provider_id="openai",
                    fallback_model_id="gpt-4.1-mini",
                    require_json_support=True,
                    safety_policy=ProviderSafetyPolicy(require_local_only=True),
                )
            ]
        )
    )
    gateway = ProviderGateway({"local_http": timeout, "openai": cloud_success}, router=router)

    with pytest.raises(LLMProviderError, match="timeout"):
        gateway.generate_json(
            ProviderRoutingContext(mode="world", use_case="world_intent_parse", project_local_only=True),
            [{"role": "user", "content": "look"}],
            PlayerIntent,
        )

    assert [trace.provider_profile_id for trace in gateway.traces] == ["local_http"]


def test_default_json_routing_never_selects_text_only_model() -> None:
    router = ProviderRouter(
        registry=ProviderCapabilityRegistry(
            providers=[
                ProviderCapability(provider_id="text_only", provider_type=ProviderType.LOCAL_STUB, local_only=True),
                ProviderCapability(provider_id="json_ok", provider_type=ProviderType.LOCAL_STUB, local_only=True),
            ],
            models=[
                ModelCapability(provider_id="text_only", provider_type=ProviderType.LOCAL_STUB, model_id="text", supports_json=False, recommended_use_cases=["structured_output"]),
                ModelCapability(provider_id="json_ok", provider_type=ProviderType.LOCAL_STUB, model_id="json", supports_json=True, recommended_use_cases=[]),
            ],
        )
    )

    decision = router.resolve_provider_for_use_case(ProviderRoutingContext(mode="world", use_case="world_intent_parse"))

    assert decision.provider_id == "json_ok"
    assert decision.model_id == "json"


def test_usage_cost_tracking_aggregates_without_sensitive_text() -> None:
    store = get_model_usage_store()
    provider = wrap_provider_for_usage_tracking(
        RecordingProvider(),
        provider_id="local_stub",
        model_id="local_stub",
        enabled=True,
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.02,
        project_id="demo",
        mode="novel",
    )

    provider.generate_text([{"role": "user", "content": f"safe prompt without {HIDDEN_SENTINEL}"}])
    store.record(
        ModelUsageRecord(
            project_id="demo",
            provider_id="mock",
            model_id="mock",
            mode="tavern",
            use_case="tavern_reply",
            duration_ms=2,
            input_tokens_estimated=8,
            output_tokens_estimated=4,
            cost_estimated=0.0,
            success=False,
            error_type="timeout",
        )
    )

    summary = store.summary(project_id="demo")
    by_mode = store.by_mode(project_id="demo")
    by_provider = store.by_provider(project_id="demo")
    rendered = json.dumps(summary.model_dump(mode="json"), ensure_ascii=False) + json.dumps([item.model_dump(mode="json") for item in by_mode + by_provider], ensure_ascii=False)

    assert summary.total_calls == 2
    assert {item.key for item in by_mode} == {"novel", "tavern"}
    assert {item.key for item in by_provider} == {"local_stub", "mock"}
    assert "safe prompt" not in rendered
    assert HIDDEN_SENTINEL not in rendered
    assert "api_key" not in rendered.lower()


def test_benchmark_and_structured_reliability_mock_only_capture_failures() -> None:
    benchmark = run_provider_benchmark(
        ProviderBenchmarkRun(
            provider_id="fake",
            benchmark_types=[
                ProviderBenchmarkType.TEXT_GENERATION,
                ProviderBenchmarkType.JSON_GENERATION,
                ProviderBenchmarkType.SCHEMA_FAILURE_HANDLING,
                ProviderBenchmarkType.FALLBACK_HANDLING,
                ProviderBenchmarkType.ROUTING_RESOLUTION,
            ],
        ),
        settings=Settings(llm_provider="mock"),
    )
    reliability = run_structured_output_reliability(
        StructuredOutputReliabilityRun(
            provider_id="fake",
            cases=[
                StructuredOutputTestCase(id="valid", schema_name=StructuredOutputSchemaName.PLAYER_INTENT),
            ],
        ),
        settings=Settings(llm_provider="mock"),
    )
    invalid = run_structured_output_reliability(
        StructuredOutputReliabilityRun(provider_id="fake_invalid_json", cases=[StructuredOutputTestCase(id="invalid", schema_name=StructuredOutputSchemaName.PLAYER_INTENT, retry_once=False)]),
        settings=Settings(llm_provider="mock"),
    )
    mismatch = run_structured_output_reliability(
        StructuredOutputReliabilityRun(provider_id="fake_schema_violation", cases=[StructuredOutputTestCase(id="mismatch", schema_name=StructuredOutputSchemaName.PLAYER_INTENT, retry_once=False)]),
        settings=Settings(llm_provider="mock"),
    )

    assert benchmark.real_provider_blocked is False
    assert benchmark.total_cases >= 5
    assert any(case.benchmark_type == ProviderBenchmarkType.SCHEMA_FAILURE_HANDLING for case in benchmark.cases)
    assert reliability.total_cases == 1
    assert reliability.schema_valid_rate == 1.0
    assert invalid.valid_json_rate == 0.0
    assert mismatch.schema_valid_rate == 0.0
    rendered = json.dumps(benchmark.model_dump_safe(), ensure_ascii=False) + json.dumps(reliability.model_dump_safe(), ensure_ascii=False) + json.dumps(invalid.model_dump_safe(), ensure_ascii=False) + json.dumps(mismatch.model_dump_safe(), ensure_ascii=False)
    assert "sk-" not in rendered
    assert HIDDEN_SENTINEL not in rendered


def test_safety_policy_rejects_cloud_disallowed_mode_and_routes_sensitive_local() -> None:
    assert ProviderSafetyPolicy().log_prompts is False

    local_policy = ProviderSafetyPolicy(allow_sensitive_prompts=True)
    cloud_policy = ProviderSafetyPolicy(allowed_modes=[ProviderMode.NOVEL])
    router = ProviderRouter(
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case="novel_draft",
                    primary_provider_id="openai",
                    primary_model_id="gpt-4.1-mini",
                    fallback_provider_id="local_stub",
                    fallback_model_id="local_stub",
                    safety_policy=local_policy,
                )
            ]
        )
    )
    decision = router.resolve_provider_for_use_case(ProviderRoutingContext(mode="novel", use_case="novel_draft", prompt_is_sensitive=True, project_local_only=True))
    assert decision.used_fallback
    assert decision.provider_id == "local_stub"

    blocked = ProviderRouter(
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case="tavern_reply",
                    primary_provider_id="local_http",
                    primary_model_id="local-model",
                    safety_policy=cloud_policy,
                )
            ]
        )
    )
    with pytest.raises(ValueError, match="mode_not_allowed"):
        blocked.resolve_provider_for_use_case(ProviderRoutingContext(mode="tavern", use_case="tavern_reply"))


def test_novel_tavern_world_and_cross_mode_use_gateway_without_hidden_prompt_leak(tmp_path: Path) -> None:
    provider = RecordingProvider()
    router = ProviderRouter(
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(use_case="novel_draft", primary_provider_id="local_stub", primary_model_id="local_stub"),
                ProviderRoutingRule(use_case="tavern_reply", primary_provider_id="local_stub", primary_model_id="local_stub"),
                ProviderRoutingRule(use_case="world_intent_parse", primary_provider_id="local_stub", primary_model_id="local_stub", require_json_support=True),
                ProviderRoutingRule(use_case="world_narration", primary_provider_id="local_stub", primary_model_id="local_stub"),
                ProviderRoutingRule(use_case="cross_mode_draft", primary_provider_id="local_stub", primary_model_id="local_stub", require_json_support=True),
            ]
        )
    )
    gateway = ProviderGateway({"local_stub": provider}, router=router)

    novel_provider = gateway.provider_for(ProviderRoutingContext(mode="novel", use_case="novel_draft"))
    novel = NovelDraftGenerationService(novel_provider).generate_scene_draft(NovelPromptContext(project_id="demo", manuscript_id="m1", scene_summary="safe visible scene"))
    tavern_provider = gateway.provider_for(ProviderRoutingContext(mode="tavern", use_case="tavern_reply"))
    tavern = TavernResponseGenerationService(tavern_provider).generate_character_reply(TavernPromptContext(project_id="demo", session_id="s1", character_id="c1", recent_safe_messages=[{"content": "safe hello"}]))
    world_intent = IntentParser(gateway.provider_for(ProviderRoutingContext(mode="world", use_case="world_intent_parse"))).parse("look")
    narration = Narrator(gateway.provider_for(ProviderRoutingContext(mode="world", use_case="world_narration"))).render(
        "look",
        ActionResult(success_level=SuccessLevel.SUCCESS, reason="Visible result", visible_facts=["public bell rings"]),
        ["public bell rings"],
        "square",
        "calm",
    )
    cross_mode = gateway.generate_json(
        ProviderRoutingContext(mode="cross_mode", use_case="cross_mode_draft"),
        [{"role": "user", "content": "Create safe draft only."}],
        GeneratedNovelDraft,
    )

    assert novel.text
    assert tavern.content
    assert world_intent.action_type.value == "observe"
    assert isinstance(narration, NarrativeResult)
    assert cross_mode.text
    rendered_messages = json.dumps(provider.messages, ensure_ascii=False)
    assert HIDDEN_SENTINEL not in rendered_messages
    assert "state_delta" not in rendered_messages.lower()

    project_repo = _project_repo(tmp_path)
    project_root = Path(project_repo.load_project("demo").project_root)
    repo = CrossModeRepository(project_root)
    proposal = repo.create_proposal(CrossModeProposal(proposal_id="p1", project_id="demo", draft_id="d1", direction=CrossModeDirection.TAVERN_TO_WORLD, validation_status="valid"))
    plan = TavernToWorldApplyService(repo).build_apply_plan(proposal)
    before_trace_count = len(gateway.traces)
    state = GameState(world_id="demo", player=PlayerState(location_id="square"), locations={"square": LocationState(id="square", name="Square")})
    event_log = EventLog()
    delta = StateDelta(operation=StateDeltaOperation.SET, path="facts.public", value=FactState(id="public", text="Public safe fact", visibility=FactVisibility.PUBLIC).model_dump(mode="json"), source="cross_mode")
    TavernToWorldApplyService(repo).apply_confirmed(plan, explicit_confirm=True, state=state, event_log=event_log, state_deltas=[delta])

    assert len(gateway.traces) == before_trace_count
    assert event_log.list_events()
