from __future__ import annotations

import base64
import io
import json
import zipfile
from pathlib import Path

import pytest

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
from app.llm.provider_profiles import ProviderMode, ProviderSafetyPolicy
from app.llm.provider_router import ProviderRouter, ProviderRoutingConfig, ProviderRoutingContext, ProviderRoutingRule, ProviderRoutingUseCase
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
    MatureExportFilter,
    MatureExportPolicy,
    MatureMemoryPartitionService,
    MatureMemoryRecord,
    RPStyleQualityChecker,
    RPSafetyEvalCase,
    RPSafetyEvalRule,
    RPWorldConsistencyChecker,
    RelationshipToneProfile,
    RelationshipToneProService,
    RoleplayBoundaryProfile,
    SceneMoodPresetPro,
    VoiceLabService,
    VoiceSample,
    evaluate_rp_safety_case,
    run_rp_mature_quality_gate,
)
from app.platform.tavern_studio import TavernMemoryRecord, TavernSpeakerType, TavernVisibility, TavernMessage, TavernToWorldProposalService, TavernWorldProposalType


def _state() -> GameState:
    return GameState(
        world_id="v28",
        player=PlayerState(location_id="square", inventory=[]),
        locations={"square": LocationState(id="square", name="Square")},
        objects={"coin": WorldObjectState(id="coin", name="Coin", owner_id="mira")},
        facts={
            "public_fact": FactState(id="public_fact", text="the square is open", visibility=FactVisibility.PUBLIC, public=True),
            "hidden_fact": FactState(id="hidden_fact", text="the secret door is below the well", visibility=FactVisibility.HIDDEN, secret=True),
        },
        player_visible_facts={"public_fact"},
        npcs={
            "mira": NPCState(id="mira", location_id="square", knowledge=["public_fact"]),
            "dead": NPCState(id="dead", location_id="square", alive=False, condition=ActorCondition.DEAD),
        },
        quests={"q1": QuestState(id="q1", title="Quest", initial_stage="start", current_stage="start")},
    )


def test_mature_policy_boundary_fade_and_memory_are_default_safe() -> None:
    policy = MatureContentPolicy()
    assert policy.enabled is False
    result = BoundaryCheckService().check_scene_allowed(
        policy=policy,
        consent=ConsentState(character_ids=["mira"], all_adult_verified=False, consent_status=ConsentStatus.UNKNOWN),
        rating=ContentRating.MATURE_FADE_TO_BLACK,
        age_categories=["unknown"],
    )
    assert not result.allowed
    assert "mature_policy_disabled" in result.blocker_codes
    assert "age_unknown_blocks_mature" in result.blocker_codes
    assert "consent_unknown_blocks_mature" in result.blocker_codes
    fade = FadeToBlackRenderer().render(reason="mature")
    assert "state_delta" not in fade.lower()

    memory = MatureMemoryRecord(memory_id="m1", project_id="p", session_id="s", character_ids=["mira"], content="mature_only private text")
    partition = MatureMemoryPartitionService([memory])
    assert partition.filter_for_normal_context(partition.records) == []
    with pytest.raises(ValueError):
        partition.build_mature_context(policy)
    assert partition.list_mature_memory()[0].authoritative is False


def test_boundary_check_age_is_fail_closed_and_normalized() -> None:
    service = BoundaryCheckService()
    policy = MatureContentPolicy(enabled=True, max_rating=ContentRating.MATURE_FADE_TO_BLACK)
    consent = ConsentState(character_ids=["mira"], all_adult_verified=True, consent_status=ConsentStatus.WILLING)

    missing_age = service.check_scene_allowed(policy=policy, consent=consent, rating=ContentRating.MATURE_FADE_TO_BLACK)
    assert not missing_age.allowed
    assert "age_unknown_blocks_mature" in missing_age.blocker_codes

    mixed_case_age = service.check_scene_allowed(policy=policy, consent=consent, rating=ContentRating.MATURE_FADE_TO_BLACK, age_categories=[" Minor "])
    assert not mixed_case_age.allowed
    assert "age_minor_blocks_mature" in mixed_case_age.blocker_codes


def test_rp_immersion_metadata_is_non_authoritative_and_safe() -> None:
    memory = AdvancedRPMemoryRecord(memory_id="addr", project_id="p", session_id="s", memory_type="address_preference", content="Call her Captain.", visibility="tavern_safe")
    assert memory.safe_summary()["authoritative"] is False
    emotion = EmotionState(character_id="mira", session_id="s", primary_emotion="relieved", intensity=40, triggers=["public apology"])
    arc = EmotionArc(arc_id="arc", character_id="mira", session_id="s", start_state=emotion, current_state=emotion).add_turning_point({"beat": "apology"})
    assert arc.current_state.safe_prompt_context()["primary_emotion"] == "relieved"
    tone = RelationshipToneProService().derive_from_tavern_memory([memory])
    assert isinstance(tone, RelationshipToneProfile)
    assert RelationshipToneProService().propose_world_relationship_change(tone)["proposal_type"] == "relationship_change"
    with pytest.raises(ValueError):
        RelationshipToneProfile(tone_profile_id="bad", character_a_id="a", character_b_id="b", intimacy_band="high")
    mood = SceneMoodPresetPro(preset_id="quiet", name="Quiet", mood_tags=["quiet"], target_modes=["tavern"])
    assert mood.safe_prompt_context()["fade_to_black_policy"] == "off"


def test_boundary_profile_voice_lab_and_style_quality() -> None:
    boundary = RoleplayBoundaryProfile(boundary_profile_id="safe", disallowed_topics=["forbidden"], fade_to_black_for=["fade"])
    assert boundary.mature_allowed is False
    assert boundary.matches_disallowed_topic("this is forbidden")
    assert boundary.requires_fade_to_black("please fade")

    voice = CharacterVoiceLabProfile(voice_id="v", character_id="mira", tone="dry", taboo_phrases=["never say"], example_dialogue=["Careful now."])
    service = VoiceLabService([voice])
    service.add_voice_sample("v", VoiceSample(sample_id="s", voice_id="v", text="Careful now."))
    assert "private_notes" not in json.dumps(service.build_voice_context("v")).lower()

    report = RPStyleQualityChecker().check(
        text="never say. the secret door is below the well",
        speaker_id="mira",
        forbidden_phrases=["never say"],
        hidden_terms=["the secret door is below the well"],
        mood_tags=["quiet"],
        content_rating=ContentRating.SUGGESTIVE,
        allowed_rating=ContentRating.SAFE,
    )
    assert report.status == "fail"
    assert {"forbidden_phrase_used", "hidden_fact_leak", "mature_rating_mismatch"} <= {issue.code for issue in report.issues}
    assert "secret door" not in json.dumps(report.model_dump_normal()).lower()


def test_rp_world_consistency_and_safety_evals_are_redacted() -> None:
    report = RPWorldConsistencyChecker().check(messages=[{"speaker_id": "dead", "content": "Quest completed. the secret door is below the well"}], state=_state())
    assert report.status == "fail"
    assert {"dead_or_incapacitated_npc_speaking", "hidden_fact_revealed", "quest_completion_contradiction"} <= {issue.code for issue in report.issues}
    assert "secret door" not in json.dumps(report.model_dump_normal()).lower()

    eval_result = evaluate_rp_safety_case(
        RPSafetyEvalCase(
            case_id="hidden",
            rule=RPSafetyEvalRule.HIDDEN_FACT_NOT_IN_RP_PROMPT,
            payload={"prompt": "the secret door is below the well"},
            forbidden_terms=["the secret door is below the well"],
            expected_issue_codes=["forbidden_term_0"],
            should_pass=False,
        )
    )
    assert eval_result.passed
    assert "secret door" not in json.dumps(eval_result.model_dump(mode="json")).lower()


def test_provider_mature_routing_policy_blocks_and_allows() -> None:
    registry = ProviderCapabilityRegistry(
        providers=[
            ProviderCapability(provider_id="local", provider_type=ProviderType.LOCAL_STUB, local_only=True),
            ProviderCapability(provider_id="cloud", provider_type=ProviderType.OPENAI, local_only=False),
        ],
        models=[
            ModelCapability(provider_id="local", provider_type=ProviderType.LOCAL_STUB, model_id="local", local_only=True),
            ModelCapability(provider_id="cloud", provider_type=ProviderType.OPENAI, model_id="cloud", local_only=False),
        ],
    )
    router = ProviderRouter(
        registry=registry,
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case=ProviderRoutingUseCase.TAVERN_REPLY,
                    primary_provider_id="cloud",
                    primary_model_id="cloud",
                    fallback_provider_id="local",
                    fallback_model_id="local",
                    safety_policy=ProviderSafetyPolicy(allow_mature_content=False),
                )
            ]
        ),
    )
    context = ProviderRoutingContext(
        use_case=ProviderRoutingUseCase.TAVERN_REPLY,
        content_rating=ContentRating.MATURE_FADE_TO_BLACK,
        mature_policy=MatureContentPolicy(enabled=True, max_rating=ContentRating.MATURE_FADE_TO_BLACK),
    )
    with pytest.raises(ValueError, match="provider_safety_policy_rejects_mature_content"):
        router.resolve_provider_for_content_rating(context)
    with pytest.raises(ValueError, match="provider_safety_policy_rejects_mature_content"):
        router.resolve_provider_for_use_case(context)

    router = ProviderRouter(
        registry=registry,
        config=ProviderRoutingConfig(
            rules=[
                ProviderRoutingRule(
                    use_case=ProviderRoutingUseCase.TAVERN_REPLY,
                    primary_provider_id="local",
                    primary_model_id="local",
                    safety_policy=ProviderSafetyPolicy(allow_mature_content=True, allowed_content_ratings=["safe", "mature_fade_to_black"]),
                )
            ]
        ),
    )
    decision = router.resolve_provider_for_content_rating(context)
    assert decision.provider_id == "local"


def test_mature_export_filter_project_export_and_mod_policy(tmp_path: Path) -> None:
    filtered = MatureExportFilter().filter_payload({"memory": [{"visibility": "mature_only", "content": "mature_only detail"}], "api_key": "sk-real-looking-secret"})
    assert filtered == {"memory": []}

    repo = ProjectRepository(tmp_path / "projects")
    project = repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(tmp_path / "projects" / "demo")))
    root = Path(project.project_root)
    (root / "tavern" / "memory").mkdir(parents=True, exist_ok=True)
    (root / "tavern" / "memory" / "m.yaml").write_text("visibility: mature_only\ncontent: mature scene detail\n", encoding="utf-8")
    archive = export_project(project.project_id, repo, sections=["tavern"])
    raw = base64.b64decode(archive.archive_base64)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        assert not any("memory/m.yaml" in name for name in zf.namelist())

    package_root = root / "modules" / "mature_pkg"
    package_root.mkdir(parents=True)
    manifest = PackageManifestV2(package_id="mature_pkg", name="Mature", version="1", package_type=PackageTypeV2.NARRATIVE_STYLE_MOD, mature_policy={"contains_mature_content": True, "requires_mature_module": True})
    (package_root / "package_manifest_v2.json").write_text(manifest.model_dump_json(), encoding="utf-8")
    (package_root / "style.json").write_text('{"visibility":"mature_only","content":"mature scene detail"}', encoding="utf-8")
    export = ModImportExportService(root).export_package("mature_pkg")
    assert export.file_count == 0


def test_mature_mod_import_warns_and_blocks_hidden_access(tmp_path: Path) -> None:
    manifest = {
        "package_id": "mature_zip",
        "name": "Mature Zip",
        "version": "1",
        "package_type": "narrative_style_mod",
        "mature_policy": {"contains_mature_content": True, "requires_mature_module": True},
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("package_manifest_v2.json", json.dumps(manifest))
        archive.writestr("style.json", "{}")
    report = ModImportExportService(tmp_path).import_dry_run(buffer.getvalue())
    assert report.ok
    assert report.mature_package
    assert any("mature_package_detected" in warning for warning in report.warnings)

    bad_manifest = {**manifest, "package_id": "bad", "mature_policy": {"contains_mature_content": True, "can_access_hidden_facts": True}}
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("package_manifest_v2.json", json.dumps(bad_manifest))
    bad = ModImportExportService(tmp_path).import_dry_run(buffer.getvalue())
    assert not bad.ok


def test_cross_mode_rp_metadata_and_mature_filtering(tmp_path: Path) -> None:
    repo = CrossModeRepository(tmp_path)
    message = TavernMessage(message_id="m1", session_id="s1", speaker_type=TavernSpeakerType.USER, content="promise")
    proposal = TavernToWorldProposalService().create_proposal_from_message(project_id="p", session_id="s1", message=message, proposal_type=TavernWorldProposalType.PROMISE_OR_DEAL, proposed_content={"summary": "promise"})
    assert proposal.rp_safety_metadata is not None
    assert TavernToWorldProposalService().validate_proposal(proposal).ok

    repo.create_proposal(CrossModeProposal(proposal_id="p1", project_id="p", draft_id="d", direction=CrossModeDirection.TAVERN_TO_WORLD, validation_status="valid"))
    validation = validate_cross_mode_project(tmp_path)
    assert not validation.ok
    assert any(issue.code == "tavern_world_missing_rp_safety_metadata" for issue in validation.errors)

    draft = TavernToNovelPipeline(repo).preview(project_id="p", session_id="s1", safe_messages=["hello", "mature_only private scene"])
    payload = json.dumps(draft.safe_summary(), ensure_ascii=False).lower()
    assert "mature_only" not in payload
    assert "private scene" not in payload

    mature_memory = TavernMemoryRecord(memory_id="mm1", project_id="p", session_id="s1", content="mature_only private proposal text", visibility=TavernVisibility.MATURE_ONLY)
    memory_proposal = TavernToWorldProposalService().create_proposal_from_memory(project_id="p", memory=mature_memory)
    summary = json.dumps(memory_proposal.normal_summary(), ensure_ascii=False).lower()
    assert "private proposal text" not in summary
    assert "mature_only" not in summary
    assert "mature memory filtered" in summary
    assert not TavernToWorldProposalService().validate_proposal(memory_proposal).ok


def test_rp_mature_quality_gate_safe_summary() -> None:
    result = run_rp_mature_quality_gate("safe_project")
    assert result.passed
    assert "api_key" not in json.dumps(result.model_dump_normal()).lower()


def test_rp_mature_quality_gate_scans_project_artifacts(tmp_path: Path) -> None:
    (tmp_path / "settings").mkdir()
    (tmp_path / "settings" / "mature_policy.json").write_text('{"enabled": true}', encoding="utf-8")
    (tmp_path / "exports").mkdir()
    (tmp_path / "exports" / "tavern.json").write_text('{"visibility":"mature_only","content":"mature scene detail"}', encoding="utf-8")
    (tmp_path / "providers").mkdir()
    (tmp_path / "providers" / "profile.json").write_text('{"allowed_content_ratings":["mature_fade_to_black"],"log_prompts":true}', encoding="utf-8")
    (tmp_path / "cross_mode" / "proposals").mkdir(parents=True)
    (tmp_path / "cross_mode" / "proposals" / "p.yaml").write_text("direction: tavern_to_world\nproposed: state_delta", encoding="utf-8")
    (tmp_path / "mods" / "bad").mkdir(parents=True)
    (tmp_path / "mods" / "bad" / "package_manifest_v2.json").write_text('{"mature_policy":{"default_enabled": true}}', encoding="utf-8")

    result = run_rp_mature_quality_gate(tmp_path)
    assert not result.passed
    payload = json.dumps(result.model_dump_normal(), ensure_ascii=False).lower()
    assert "mature_enabled_by_default" in payload
    assert "normal_export_sensitive_leak" in payload
    assert "provider_mature" in payload
    assert "tavern_world_missing_rp_safety_metadata" in payload
    assert "unsafe_mature_mod_policy" in payload
    assert "mature scene detail" not in payload
