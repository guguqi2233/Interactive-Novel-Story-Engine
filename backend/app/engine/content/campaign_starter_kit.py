from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.engine.content.faction_templates import (
    FactionTemplateGeneratedContent,
    FactionTemplatePreview,
    get_faction_template,
)
from app.engine.content.mystery_templates import (
    MysteryTemplateGeneratedContent,
    MysteryTemplatePreview,
    get_mystery_template,
)
from app.engine.content.npc_pack_generator import NPCPackGeneratorDraft
from app.engine.content.quest_pack_generator import QuestPackGeneratorDraft
from app.engine.content.script_package_builder import (
    ScriptPackageBuildRequest,
    ScriptPackageBuildReport,
    ScriptPackageFile,
    ScriptPackageManifest,
    build_script_package_dry_run,
    export_script_package,
)
from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.engine.content.world_pack_wizard import WorldPackWizard, WorldPackWizardDraft, WorldPackWizardPreview


class CampaignStarterKitError(ValueError):
    """Raised when a campaign starter kit draft is invalid or unsafe."""


class CampaignStarterKitDraft(BaseModel):
    campaign_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1)
    genre: str = "fantasy"
    tone: str = "grounded"
    starting_region: str = Field(default="start", pattern=r"^[A-Za-z0-9_-]+$")
    core_conflict: str = "local mystery"
    npc_count: int = Field(default=3, ge=1, le=20)
    questline_count: int = Field(default=1, ge=1, le=10)
    faction_count: int = Field(default=2, ge=0, le=10)
    mystery_enabled: bool = True
    RP_focus_level: str = "medium"
    target_playtime_hours: int = Field(default=2, ge=1, le=40)
    llm_assisted: bool = False


class CampaignStarterQualityDryRun(BaseModel):
    passed: bool
    validation_ok: bool
    quality_gate_dry_run: bool = True
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class CampaignStarterKitPreview(BaseModel):
    draft: CampaignStarterKitDraft
    world_pack_draft: WorldPackWizardDraft
    world_pack_preview: WorldPackWizardPreview
    npc_pack_draft: NPCPackGeneratorDraft
    quest_pack_draft: QuestPackGeneratorDraft
    faction_draft: FactionTemplatePreview | None = None
    mystery_draft: MysteryTemplatePreview | None = None
    scenario_regression_suite: list[dict[str, Any]] = Field(default_factory=list)
    quality_gate_config: dict[str, Any] = Field(default_factory=dict)
    quality_gate_dry_run: CampaignStarterQualityDryRun
    script_package_draft: ScriptPackageBuildReport
    validation: ValidationReport
    writes_to_disk: bool = False
    active_game_state_modified: bool = False
    built: bool = False


class CampaignStarterKitBuildRequest(BaseModel):
    draft: CampaignStarterKitDraft
    confirm_build: bool = False


def preview_campaign_starter_kit(
    draft: CampaignStarterKitDraft,
    *,
    worlds_root: str = "worlds",
) -> CampaignStarterKitPreview:
    report = ValidationReport(world_id=draft.campaign_id)
    _validate_draft(draft, report)
    world_draft = _world_pack_draft(draft)
    world_preview = WorldPackWizard(worlds_root).preview_files(world_draft)
    if world_preview.validation:
        report.errors.extend(world_preview.validation.errors)
        report.warnings.extend(world_preview.validation.warnings)
        report.suggestions.extend(world_preview.validation.suggestions)
    npc_draft = _npc_pack_draft(draft)
    quest_draft = _quest_pack_draft(draft)
    faction_preview = _faction_preview(draft) if draft.faction_count > 0 else None
    mystery_preview = _mystery_preview(draft) if draft.mystery_enabled else None
    scenarios = _scenario_suite(draft)
    quality = _quality_dry_run(draft, report)
    script_report = _script_package_report(draft, scenarios)
    report.errors.extend(script_report.validation.errors)
    report.warnings.extend(script_report.validation.warnings)
    return CampaignStarterKitPreview(
        draft=draft,
        world_pack_draft=world_draft,
        world_pack_preview=world_preview,
        npc_pack_draft=npc_draft,
        quest_pack_draft=quest_draft,
        faction_draft=faction_preview,
        mystery_draft=mystery_preview,
        scenario_regression_suite=scenarios,
        quality_gate_config=_quality_gate_config(draft),
        quality_gate_dry_run=quality,
        script_package_draft=script_report,
        validation=report,
    )


def build_campaign_starter_kit(
    request: CampaignStarterKitBuildRequest,
    *,
    worlds_root: str = "worlds",
) -> CampaignStarterKitPreview:
    preview = preview_campaign_starter_kit(request.draft, worlds_root=worlds_root)
    if not request.confirm_build:
        preview.validation.add(
            ValidationSeverity.ERROR,
            "campaign_starter.build",
            "Campaign starter build requires explicit confirmation.",
            code="campaign_starter_build_requires_confirmation",
        )
        preview.quality_gate_dry_run.passed = False
        preview.quality_gate_dry_run.blockers.append("explicit confirmation required")
        return preview
    if not preview.validation.ok or not preview.quality_gate_dry_run.passed:
        return preview
    preview.built = True
    return preview


def export_campaign_starter_script_package(
    draft: CampaignStarterKitDraft,
) -> ScriptPackageBuildReport:
    scenarios = _scenario_suite(draft)
    request = _script_package_request(draft, scenarios)
    return export_script_package(request)


def _validate_draft(draft: CampaignStarterKitDraft, report: ValidationReport) -> None:
    unsafe = "\n".join([draft.name, draft.genre, draft.tone, draft.core_conflict, draft.RP_focus_level]).lower()
    if any(token in unsafe for token in ("sk-", "api_key", "apikey", ".env", "http://", "https://", "script")):
        report.add(
            ValidationSeverity.ERROR,
            "campaign_starter.safety",
            "Campaign starter drafts cannot contain API keys, scripts, environment references, or remote URLs.",
            code="campaign_starter_unsafe_reference",
        )
    if draft.llm_assisted:
        report.add(
            ValidationSeverity.WARNING,
            "campaign_starter.llm_assisted",
            "LLM-assisted mode is reserved and remains draft-only.",
            code="campaign_starter_llm_assisted_reserved",
        )


def _world_pack_draft(draft: CampaignStarterKitDraft) -> WorldPackWizardDraft:
    return WorldPackWizardDraft(
        world_id=draft.campaign_id,
        name=draft.name,
        genre=draft.genre,
        tone=draft.tone,
        description=f"{draft.name}: a {draft.tone} {draft.genre} starter centered on {draft.core_conflict}.",
        starting_location=draft.starting_region,
        location_seed_count=max(3, min(8, draft.target_playtime_hours + 1)),
        npc_seed_count=draft.npc_count,
        quest_seed_count=draft.questline_count,
        enabled_systems=["quests", "roleplay", "npc_simulation", "factions", "rumors"],
        default_prompt_profile="default_safe",
        default_quality_profile="standard",
    )


def _npc_pack_draft(draft: CampaignStarterKitDraft) -> NPCPackGeneratorDraft:
    return NPCPackGeneratorDraft(
        target_world_id=draft.campaign_id,
        pack_id=f"{draft.campaign_id}_npcs",
        theme=draft.core_conflict,
        faction_ids=[f"{draft.campaign_id}_faction_{index + 1}" for index in range(draft.faction_count)],
        location_ids=[draft.starting_region],
        npc_count=draft.npc_count,
        archetypes=["guide", "witness", "antagonist", "merchant"][: max(1, min(4, draft.npc_count))],
        rp_style=draft.RP_focus_level,
        simulation_preset_ids=["guard", "rumor_spreader"] if draft.faction_count else ["witness"],
        relationship_density=0.35,
        hidden_secret_ratio=0.2 if draft.mystery_enabled else 0.0,
    )


def _quest_pack_draft(draft: CampaignStarterKitDraft) -> QuestPackGeneratorDraft:
    return QuestPackGeneratorDraft(
        target_world_id=draft.campaign_id,
        pack_id=f"{draft.campaign_id}_quests",
        theme=draft.core_conflict,
        quest_count=draft.questline_count,
        involved_npcs=["guide"],
        involved_locations=[draft.starting_region],
        involved_factions=[f"{draft.campaign_id}_faction_1"] if draft.faction_count else [],
        required_facts=["world_pack_started"],
        mystery_mode=draft.mystery_enabled,
        failure_paths_enabled=True,
        reward_policy="story",
    )


def _faction_preview(draft: CampaignStarterKitDraft) -> FactionTemplatePreview:
    template = get_faction_template("city_watch")
    return FactionTemplatePreview(
        template=template,
        target_world_id=draft.campaign_id,
        generated=FactionTemplateGeneratedContent(
            factions_draft=[
                {
                    "id": f"{draft.campaign_id}_faction_{index + 1}",
                    "name": f"{template.name} {index + 1}",
                    "type": template.faction_type,
                    "reputation": template.default_reputation,
                    "visibility": "public",
                }
                for index in range(draft.faction_count)
            ],
            npc_faction_duty_candidates=[duty.model_dump(mode="json") for duty in template.duties],
            relationship_candidates=[],
            quest_hook_candidates=[hook.model_dump(mode="json") for hook in template.quest_hooks],
        ),
        validation=ValidationReport(world_id=draft.campaign_id),
        writes_to_disk=False,
    )


def _mystery_preview(draft: CampaignStarterKitDraft) -> MysteryTemplatePreview:
    template = get_mystery_template("missing_heirloom_case")
    return MysteryTemplatePreview(
        template=template,
        target_world_id=draft.campaign_id,
        generated=MysteryTemplateGeneratedContent(
            facts_draft=[template.truth_fact.model_dump(mode="json")],
            npc_knowledge_draft={suspect.npc_id: [template.truth_fact.id] for suspect in template.suspects if suspect.knows_truth},
            questline_draft=[],
            rumor_draft=[],
            evidence_items_draft=[
                {"id": clue.evidence_item_id, "name": clue.id, "visibility": "discoverable"}
                for clue in template.clues
                if clue.evidence_item_id
            ],
            scenario_regression_draft=[],
        ),
        validation=ValidationReport(world_id=draft.campaign_id),
        writes_to_disk=False,
    )


def _scenario_suite(draft: CampaignStarterKitDraft) -> list[dict[str, Any]]:
    return [
        {
            "case_id": f"{draft.campaign_id}_starter_path",
            "world_id": draft.campaign_id,
            "description": "Starter path reaches the first visible quest without hidden leak.",
            "steps": ["look", "talk guide"],
            "expected_visible_facts": ["world_pack_started"],
            "forbidden_visible_facts": [f"{draft.campaign_id}_truth"] if draft.mystery_enabled else [],
            "seed": 14,
        }
    ]


def _quality_gate_config(draft: CampaignStarterKitDraft) -> dict[str, Any]:
    return {
        "profile": "fast",
        "min_health_score": 0,
        "scenario_count": 1,
        "hidden_leak_check": True,
        "target_playtime_hours": draft.target_playtime_hours,
    }


def _quality_dry_run(draft: CampaignStarterKitDraft, validation: ValidationReport) -> CampaignStarterQualityDryRun:
    warnings: list[str] = []
    if draft.npc_count < 2:
        warnings.append("Starter kits are stronger with at least two NPC roles.")
    if draft.questline_count < 1:
        warnings.append("Starter kit needs at least one questline.")
    if draft.mystery_enabled and draft.target_playtime_hours < 2:
        warnings.append("Mystery starters benefit from at least two hours of playtime.")
    blockers = [issue.message for issue in validation.errors]
    return CampaignStarterQualityDryRun(
        passed=not blockers,
        validation_ok=not blockers,
        blockers=blockers,
        warnings=warnings,
        summary={
            "world": draft.campaign_id,
            "npcs": draft.npc_count,
            "questlines": draft.questline_count,
            "factions": draft.faction_count,
            "mystery_enabled": draft.mystery_enabled,
        },
    )


def _script_package_report(draft: CampaignStarterKitDraft, scenarios: list[dict[str, Any]]) -> ScriptPackageBuildReport:
    return build_script_package_dry_run(_script_package_request(draft, scenarios))


def _script_package_request(draft: CampaignStarterKitDraft, scenarios: list[dict[str, Any]]) -> ScriptPackageBuildRequest:
    return ScriptPackageBuildRequest(
        manifest=ScriptPackageManifest(
            package_id=f"{draft.campaign_id}_starter_script",
            name=f"{draft.name} Starter Script",
            included_worlds=[draft.campaign_id],
            included_quests=[f"{draft.campaign_id}_quests"],
            included_characters=[f"{draft.campaign_id}_npcs"],
            included_templates=[f"{draft.campaign_id}_templates"],
            included_scenarios=[scenario["case_id"] for scenario in scenarios],
            included_quality_profile="fast",
            dependencies=[draft.campaign_id],
        ),
        files=[
            ScriptPackageFile(
                path="campaign_starter/manifest.json",
                content=_safe_json({"campaign_id": draft.campaign_id, "name": draft.name, "core_conflict": draft.core_conflict}),
            ),
            ScriptPackageFile(
                path="campaign_starter/scenarios.json",
                content=_safe_json({"cases": scenarios}),
            ),
        ],
        available_dependency_ids=[draft.campaign_id],
        confirm_apply=False,
    )


def _safe_json(value: Any) -> str:
    return __import__("json").dumps(value, ensure_ascii=False, sort_keys=True)
