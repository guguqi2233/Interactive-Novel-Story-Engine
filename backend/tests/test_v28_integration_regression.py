from __future__ import annotations

import base64
import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import (
    ActorCondition,
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    NPCState,
    PlayerState,
    QuestState,
    WorldObjectState,
)
from app.llm.provider_capabilities import ModelCapability, ProviderCapability, ProviderCapabilityRegistry, ProviderType
from app.llm.provider_profiles import ProviderSafetyPolicy
from app.llm.provider_router import ProviderRouter, ProviderRoutingConfig, ProviderRoutingContext, ProviderRoutingRule, ProviderRoutingUseCase
from app.main import app
from app.platform.cross_mode import CrossModeDirection, CrossModeProposal, CrossModeRepository, TavernToNovelPipeline, validate_cross_mode_project
from app.platform.mod_import_export import ModImportExportService
from app.platform.narrative_project import NarrativeProject
from app.platform.package_manifest_v2 import PackageManifestV2, PackageTypeV2
from app.platform.project_packages import export_project
from app.platform.project_repository import ProjectRepository
from app.platform.rp_mature import (
    AdvancedRPMemoryRecord,
    BoundaryCheckService,
    CharacterVoiceLabProfile,
    ConsentState,
    ConsentStatus,
    ContentRating,
    EmotionArc,
    EmotionState,
    FadeToBlackRenderer,
    MatureContentPolicy,
    MatureMemoryPartitionService,
    MatureMemoryRecord,
    RPStyleQualityChecker,
    RPSafetyEvalCase,
    RPSafetyEvalRule,
    RPWorldConsistencyChecker,
    RelationshipToneProService,
    RoleplayBoundaryProfile,
    SceneMoodPresetPro,
    VoiceLabService,
    evaluate_rp_safety_case,
    run_rp_mature_quality_gate,
)
from app.platform.tavern_studio import TavernMessage, TavernSpeakerType, TavernToWorldProposalService, TavernWorldProposalType


def _project_repo(tmp_path: Path) -> ProjectRepository:
    repo = ProjectRepository(tmp_path / "projects")
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(tmp_path / "projects" / "demo")))
    return repo


def _state() -> GameState:
    return GameState(
        world_id="v28",
        player=PlayerState(location_id="square", inventory=[]),
        locations={"square": LocationState(id="square", name="Square")},
        objects={"coin": WorldObjectState(id="coin", name="Coin", owner_id="mira")},
        facts={
            "public": FactState(id="public", text="the square is open", visibility=FactVisibility.PUBLIC, public=True),
            "hidden": FactState(id="hidden", text="the hidden archive is below the inn", visibility=FactVisibility.HIDDEN, secret=True),
        },
        player_visible_facts={"public"},
        npcs={
            "mira": NPCState(id="mira", location_id="square", knowledge=["public"]),
            "oren": NPCState(id="oren", location_id="square", knowledge=[]),
            "dead": NPCState(id="dead", location_id="square", alive=False, condition=ActorCondition.DEAD),
        },
        quests={"q1": QuestState(id="q1", title="Quest", initial_stage="start", current_stage="start")},
    )


def _provider_router(policy: ProviderSafetyPolicy) -> ProviderRouter:
    registry = ProviderCapabilityRegistry(
        providers=[
            ProviderCapability(provider_id="cloud", provider_type=ProviderType.OPENAI, local_only=False),
            ProviderCapability(provider_id="local", provider_type=ProviderType.LOCAL_STUB, local_only=True),
        ],
        models=[
            ModelCapability(provider_id="cloud", provider_type=ProviderType.OPENAI, model_id="cloud", local_only=False),
            ModelCapability(provider_id="local", provider_type=ProviderType.LOCAL_STUB, model_id="local", local_only=True),
        ],
    )
    return ProviderRouter(
        registry=registry,
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case=ProviderRoutingUseCase.TAVERN_REPLY,
                    primary_provider_id="cloud",
                    primary_model_id="cloud",
                    fallback_provider_id="local",
                    fallback_model_id="local",
                    safety_policy=policy,
                )
            ]
        ),
    )


def test_v28_rp_memory_emotion_tone_boundaries() -> None:
    memory = AdvancedRPMemoryRecord(
        memory_id="m1",
        project_id="demo",
        session_id="s1",
        character_ids=["mira"],
        memory_type="relationship_shift",
        content="Mira prefers quiet honesty.",
    )
    mature_memory = MatureMemoryRecord(memory_id="mm1", project_id="demo", session_id="s1", character_ids=["mira"], content="mature_only private memory")
    assert memory.authoritative is False
    assert MatureMemoryPartitionService([mature_memory]).filter_for_normal_context([mature_memory]) == []

    emotion = EmotionState(character_id="mira", session_id="s1", primary_emotion="wary", intensity=55, triggers=["public apology"])
    arc = EmotionArc(arc_id="arc1", character_id="mira", session_id="s1", start_state=emotion, current_state=emotion).add_turning_point({"event": "apology accepted"})
    assert arc.turning_points[0]["event"] == "apology accepted"

    tone = RelationshipToneProService().derive_from_tavern_memory([memory])
    assert 0 <= tone.trust <= 100
    safe_world_tone = RelationshipToneProService().derive_from_world_relationship_safe({"relationship_id": "r1", "source_id": "mira", "target_id": "player", "trust": 15, "hidden_secret": "never expose"})
    assert "hidden_secret" not in json.dumps(RelationshipToneProService().build_tone_prompt_context(safe_world_tone)).lower()


def test_v28_multi_npc_scene_api_is_safe_and_does_not_modify_world_state(tmp_path: Path) -> None:
    app.state.project_repository = _project_repo(tmp_path)
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    app.state.v28_multi_scenes = {}
    client = TestClient(app)
    before = _state().model_copy(deep=True)

    assert client.post("/projects/demo/tavern/characters", json={"tavern_character_id": "mira", "display_name": "Mira"}).status_code == 200
    assert client.post("/projects/demo/tavern/characters", json={"tavern_character_id": "oren", "display_name": "Oren"}).status_code == 200
    created = client.post(
        "/projects/demo/tavern/multi-scenes",
        json={"scene_id": "scene1", "title": "Two Voices", "participant_ids": ["mira", "oren"], "turn_order": ["mira", "oren"]},
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["participant_ids"] == ["mira", "oren"]
    assert payload["turn_order"] == ["mira", "oren"]

    reply = client.post("/projects/demo/tavern/multi-scenes/scene1/next-reply")
    assert reply.status_code == 200
    body = json.dumps(reply.json(), ensure_ascii=False).lower()
    assert "tavern" in body
    assert "hidden archive" not in body
    assert "state_delta" not in body
    assert before == _state()


def test_v28_mood_voice_boundary_and_mature_policy_defaults() -> None:
    mood = SceneMoodPresetPro(preset_id="quiet", name="Quiet", mood_tags=["quiet"], target_modes=["tavern"])
    assert mood.can_access_hidden_facts is False
    assert "hidden" not in json.dumps(mood.safe_prompt_context()).lower()

    voice = CharacterVoiceLabProfile(voice_id="v1", character_id="mira", private_notes_authoring_only="do not export")
    assert "private_notes" not in json.dumps(VoiceLabService([voice]).build_voice_context("v1")).lower()

    boundary = RoleplayBoundaryProfile(boundary_profile_id="safe")
    assert boundary.mature_allowed is False
    assert not MatureContentPolicy().enabled
    assert MatureContentPolicy().allow_explicit_adult is False

    service = BoundaryCheckService()
    disabled = MatureContentPolicy()
    assert not service.check_scene_allowed(policy=disabled, consent=ConsentState(character_ids=["mira"]), rating=ContentRating.MATURE_FADE_TO_BLACK, age_categories=["adult"]).allowed
    enabled = MatureContentPolicy(enabled=True, max_rating=ContentRating.MATURE_FADE_TO_BLACK)
    assert not service.check_scene_allowed(policy=enabled, consent=ConsentState(character_ids=["mira"], consent_status=ConsentStatus.WILLING), rating=ContentRating.MATURE_FADE_TO_BLACK, age_categories=["unknown"]).allowed
    assert not service.check_scene_allowed(policy=enabled, consent=ConsentState(character_ids=["mira"], all_adult_verified=True, consent_status=ConsentStatus.UNWILLING), rating=ContentRating.MATURE_FADE_TO_BLACK, age_categories=["adult"]).allowed
    fade = FadeToBlackRenderer().render(reason="boundary_refusal")
    assert "explicit" not in fade.lower()


def test_v28_provider_safety_routing_rejects_disallowed_and_cloud_local_only() -> None:
    context = ProviderRoutingContext(
        use_case=ProviderRoutingUseCase.TAVERN_REPLY,
        content_rating=ContentRating.MATURE_FADE_TO_BLACK,
        mature_policy=MatureContentPolicy(enabled=True, max_rating=ContentRating.MATURE_FADE_TO_BLACK),
    )
    with pytest.raises(ValueError, match="provider_safety_policy_rejects_mature_content"):
        _provider_router(ProviderSafetyPolicy(allow_mature_content=False)).resolve_provider_for_content_rating(context)

    local_only_decision = _provider_router(
        ProviderSafetyPolicy(
            allow_mature_content=True,
            allowed_content_ratings=["safe", "mature_fade_to_black"],
            require_local_only_for_mature=True,
        )
    ).resolve_provider_for_content_rating(context)
    assert local_only_decision.provider_id == "local"
    assert local_only_decision.used_fallback
    assert any("provider_safety_policy_requires_local_only_for_mature" in warning for warning in local_only_decision.warnings)

    error_text = _provider_router(ProviderSafetyPolicy(allow_mature_content=False)).reject_or_downgrade_by_policy(context)
    assert "hidden archive" not in json.dumps(error_text).lower()


def test_v28_cross_mode_export_and_mature_mod_policy(tmp_path: Path) -> None:
    message = TavernMessage(message_id="m1", session_id="s1", speaker_type=TavernSpeakerType.USER, content="safe promise")
    proposal = TavernToWorldProposalService().create_proposal_from_message(
        project_id="demo",
        session_id="s1",
        message=message,
        proposal_type=TavernWorldProposalType.PROMISE_OR_DEAL,
        proposed_content={"summary": "safe promise"},
    )
    assert proposal.rp_safety_metadata is not None
    assert TavernToWorldProposalService().validate_proposal(proposal).ok
    normal = json.dumps(proposal.normal_summary(), ensure_ascii=False).lower()
    assert "mature_only" not in normal

    cross_repo = CrossModeRepository(tmp_path / "cross")
    cross_repo.create_proposal(CrossModeProposal(proposal_id="bad", project_id="demo", draft_id="d", direction=CrossModeDirection.TAVERN_TO_WORLD, validation_status="valid"))
    validation = validate_cross_mode_project(tmp_path / "cross")
    assert any(issue.code == "tavern_world_missing_rp_safety_metadata" for issue in validation.errors)
    draft = TavernToNovelPipeline(cross_repo).preview(project_id="demo", session_id="s1", safe_messages=["hello", "mature_only private memory"])
    assert "mature_only" not in json.dumps(draft.safe_summary(), ensure_ascii=False).lower()

    project_repo = _project_repo(tmp_path / "export")
    project = project_repo.load_project("demo")
    root = Path(project.project_root)
    (root / "tavern" / "memory").mkdir(parents=True, exist_ok=True)
    (root / "tavern" / "memory" / "mature.yaml").write_text("visibility: mature_only\ncontent: mature scene detail\n", encoding="utf-8")
    archive = export_project("demo", project_repo, sections=["tavern"])
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(archive.archive_base64))) as zf:
        assert not any("mature.yaml" in name for name in zf.namelist())

    package_root = root / "modules" / "mature_style"
    package_root.mkdir(parents=True)
    manifest = PackageManifestV2(package_id="mature_style", name="Mature Style", version="1", package_type=PackageTypeV2.NARRATIVE_STYLE_MOD, mature_policy={"contains_mature_content": True, "requires_mature_module": True})
    (package_root / "package_manifest_v2.json").write_text(manifest.model_dump_json(), encoding="utf-8")
    (package_root / "style.json").write_text('{"visibility":"mature_only","content":"mature scene detail"}', encoding="utf-8")
    assert ModImportExportService(root).export_package("mature_style").file_count == 0


def test_v28_quality_consistency_evals_detect_blockers() -> None:
    hidden = "the hidden archive is below the inn"
    eval_result = evaluate_rp_safety_case(
        RPSafetyEvalCase(
            case_id="leak",
            rule=RPSafetyEvalRule.HIDDEN_FACT_NOT_IN_RP_PROMPT,
            payload={"prompt": hidden},
            forbidden_terms=[hidden],
            expected_issue_codes=["forbidden_term_0"],
            should_pass=False,
        )
    )
    assert eval_result.passed

    style = RPStyleQualityChecker().check(text="private note leaked", speaker_id="mira", private_terms=["private note"])
    assert style.status == "fail"
    assert "private note" not in json.dumps(style.model_dump_normal()).lower()

    world = RPWorldConsistencyChecker().check(messages=[{"speaker_id": "dead", "content": "I am here."}], state=_state())
    assert world.status == "fail"
    assert "dead_or_incapacitated_npc_speaking" in {issue.code for issue in world.issues}

    gate = run_rp_mature_quality_gate("mature_enabled_by_default_project")
    assert not gate.passed
    assert "mature_enabled_by_default" in gate.blockers
