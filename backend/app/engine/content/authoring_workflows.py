from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AuthoringWorkflowError(ValueError):
    """Raised when an authoring workflow preset is invalid."""


class AuthoringWorkflowPresetType(StrEnum):
    NEW_WORLD = "new_world"
    NEW_QUESTLINE = "new_questline"
    NEW_CHARACTER_PACK = "new_character_pack"
    NEW_RP_SCENE = "new_rp_scene"
    NEW_MYSTERY_CASE = "new_mystery_case"
    PRE_RELEASE_CHECK = "pre_release_check"
    IMPORT_REVIEW = "import_review"
    BRANCH_MERGE_REVIEW = "branch_merge_review"


class AuthoringWorkflowStep(BaseModel):
    id: str
    label: str
    tool_ref: str
    action: str
    requires_validation: bool = True
    writes_content: bool = False


class AuthoringWorkflowPreset(BaseModel):
    id: str
    preset_type: AuthoringWorkflowPresetType
    name: str
    description: str = ""
    steps: list[AuthoringWorkflowStep] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    validation_gates: list[str] = Field(default_factory=list)
    suggested_templates: list[str] = Field(default_factory=list)
    quality_checks: list[str] = Field(default_factory=list)


class AuthoringWorkflowPresetList(BaseModel):
    local_only: bool = True
    presets: list[AuthoringWorkflowPreset] = Field(default_factory=list)


ALLOWED_AUTHORING_TOOL_REFS = {
    "map",
    "quests",
    "npc_goals",
    "social",
    "economy",
    "rumor_crime",
    "rp_characters",
    "dialogue_scenes",
    "group_rp_scenes",
    "example_dialogue",
    "scenarios",
    "templates",
    "template_wizard",
    "merge_assistant",
    "diff_review",
    "validation",
    "quality_gate",
    "import_export",
}


def list_authoring_workflow_presets() -> AuthoringWorkflowPresetList:
    presets = _default_presets()
    for preset in presets:
        validate_authoring_workflow_preset(preset)
    return AuthoringWorkflowPresetList(presets=presets)


def validate_authoring_workflow_preset(preset: AuthoringWorkflowPreset) -> AuthoringWorkflowPreset:
    unknown = sorted(set(preset.required_tools) - ALLOWED_AUTHORING_TOOL_REFS)
    unknown.extend(sorted({step.tool_ref for step in preset.steps} - ALLOWED_AUTHORING_TOOL_REFS))
    if unknown:
        raise AuthoringWorkflowError(f"Invalid workflow tool reference: {', '.join(sorted(set(unknown)))}")
    for step in preset.steps:
        if step.writes_content and not step.requires_validation:
            raise AuthoringWorkflowError(f"Workflow step bypasses validation: {step.id}")
    return preset


def _step(step_id: str, label: str, tool_ref: str, action: str, *, writes: bool = False) -> AuthoringWorkflowStep:
    return AuthoringWorkflowStep(id=step_id, label=label, tool_ref=tool_ref, action=action, writes_content=writes)


def _default_presets() -> list[AuthoringWorkflowPreset]:
    return [
        AuthoringWorkflowPreset(
            id="new_world",
            preset_type=AuthoringWorkflowPresetType.NEW_WORLD,
            name="Create New World",
            description="Start with Template Wizard, then validate map, quests, NPCs, and release readiness.",
            steps=[
                _step("wizard", "Choose world template", "template_wizard", "Create a world draft."),
                _step("map", "Review map", "map", "Inspect locations and exits."),
                _step("validate", "Validate world pack", "validation", "Run validation graph."),
            ],
            required_tools=["template_wizard", "map", "validation"],
            validation_gates=["world_pack_validation"],
            suggested_templates=["basic_village_world"],
            quality_checks=["world_health"],
        ),
        AuthoringWorkflowPreset(
            id="new_questline",
            preset_type=AuthoringWorkflowPresetType.NEW_QUESTLINE,
            name="New Questline",
            steps=[_step("wizard", "Draft questline", "template_wizard", "Generate questline draft."), _step("graph", "Edit quest graph", "quests", "Review graph paths."), _step("scenario", "Generate scenario draft", "scenarios", "Add regression coverage.")],
            required_tools=["template_wizard", "quests", "scenarios"],
            validation_gates=["quest_validation", "scenario_validation"],
            suggested_templates=["village_notice_quest"],
            quality_checks=["quest_completion_analysis"],
        ),
        AuthoringWorkflowPreset(
            id="new_character_pack",
            preset_type=AuthoringWorkflowPresetType.NEW_CHARACTER_PACK,
            name="New Character Pack",
            steps=[_step("characters", "Author characters", "rp_characters", "Edit RP/voice profiles."), _step("examples", "Add examples", "example_dialogue", "Review safe dialogue samples."), _step("review", "Review package diff", "diff_review", "Inspect export candidates.")],
            required_tools=["rp_characters", "example_dialogue", "diff_review"],
            validation_gates=["rp_character_validation", "package_validation"],
            suggested_templates=[],
            quality_checks=["hidden_leak_review"],
        ),
        AuthoringWorkflowPreset(
            id="new_rp_scene",
            preset_type=AuthoringWorkflowPresetType.NEW_RP_SCENE,
            name="Make RP Scene",
            steps=[_step("dialogue", "Dialogue scene", "dialogue_scenes", "Create focused scene."), _step("group", "Group scene", "group_rp_scenes", "Create multi-NPC scene."), _step("validate", "Validate prompts", "validation", "Check visibility issues.")],
            required_tools=["dialogue_scenes", "group_rp_scenes", "validation"],
            validation_gates=["dialogue_scene_validation", "group_rp_scene_validation"],
            suggested_templates=["rp_intro_scene"],
            quality_checks=["rp_boundary_evals"],
        ),
        AuthoringWorkflowPreset(
            id="new_mystery_case",
            preset_type=AuthoringWorkflowPresetType.NEW_MYSTERY_CASE,
            name="Design Mystery Case",
            steps=[_step("wizard", "Mystery template", "template_wizard", "Draft clue/case structure."), _step("rumors", "Consequences", "rumor_crime", "Wire facts, witnesses, rumors."), _step("scenario", "Regression case", "scenarios", "Cover discovery path.")],
            required_tools=["template_wizard", "rumor_crime", "scenarios"],
            validation_gates=["fact_visibility_validation", "scenario_validation"],
            suggested_templates=["mystery_case"],
            quality_checks=["hidden_info_leak_eval"],
        ),
        AuthoringWorkflowPreset(
            id="pre_release_check",
            preset_type=AuthoringWorkflowPresetType.PRE_RELEASE_CHECK,
            name="Pre-release Check",
            steps=[_step("validation", "Validation graph", "validation", "Run schema/reference checks."), _step("diff", "Diff review", "diff_review", "Review final changes."), _step("quality", "Quality gate", "quality_gate", "Run quality gate and scenario regression.")],
            required_tools=["validation", "diff_review", "quality_gate"],
            validation_gates=["world_pack_validation", "quality_gate"],
            suggested_templates=[],
            quality_checks=["quality_gate", "scenario_regression", "world_health", "content_coverage"],
        ),
        AuthoringWorkflowPreset(
            id="import_review",
            preset_type=AuthoringWorkflowPresetType.IMPORT_REVIEW,
            name="Import Review",
            steps=[_step("import", "Dry-run import", "import_export", "Review local package dry-run."), _step("diff", "Diff review", "diff_review", "Inspect proposed content."), _step("validation", "Validation", "validation", "Block unsafe content.")],
            required_tools=["import_export", "diff_review", "validation"],
            validation_gates=["import_validation", "package_validation"],
            quality_checks=["hidden_leak_review"],
        ),
        AuthoringWorkflowPreset(
            id="branch_merge_review",
            preset_type=AuthoringWorkflowPresetType.BRANCH_MERGE_REVIEW,
            name="Branch Merge Review",
            steps=[_step("merge", "Resolve branch merge", "merge_assistant", "Preview and resolve conflicts."), _step("diff", "Review diff", "diff_review", "Inspect merge output."), _step("validation", "Validate", "validation", "Validate before saving.")],
            required_tools=["merge_assistant", "diff_review", "validation"],
            validation_gates=["merge_validation", "world_pack_validation"],
            quality_checks=["branch_regression"],
        ),
    ]
