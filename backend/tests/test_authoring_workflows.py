from app.engine.content.authoring_workflows import (
    AuthoringWorkflowError,
    AuthoringWorkflowPreset,
    AuthoringWorkflowPresetType,
    AuthoringWorkflowStep,
    list_authoring_workflow_presets,
    validate_authoring_workflow_preset,
)


def test_workflow_presets_can_load() -> None:
    presets = list_authoring_workflow_presets().presets
    assert {preset.id for preset in presets} >= {"new_world", "new_character_pack", "pre_release_check"}


def test_invalid_tool_ref_is_caught() -> None:
    preset = AuthoringWorkflowPreset(
        id="bad",
        preset_type=AuthoringWorkflowPresetType.NEW_WORLD,
        name="Bad",
        steps=[AuthoringWorkflowStep(id="bad_step", label="Bad", tool_ref="unknown_tool", action="Nope")],
        required_tools=["unknown_tool"],
    )
    try:
        validate_authoring_workflow_preset(preset)
    except AuthoringWorkflowError as exc:
        assert "unknown_tool" in str(exc)
    else:
        raise AssertionError("Expected invalid workflow tool ref to be caught")


def test_pre_release_check_contains_quality_gate() -> None:
    presets = {preset.id: preset for preset in list_authoring_workflow_presets().presets}
    pre_release = presets["pre_release_check"]
    assert "quality_gate" in pre_release.required_tools
    assert "quality_gate" in pre_release.validation_gates
    assert "scenario_regression" in pre_release.quality_checks


def test_workflow_step_cannot_bypass_validation() -> None:
    preset = AuthoringWorkflowPreset(
        id="unsafe",
        preset_type=AuthoringWorkflowPresetType.NEW_QUESTLINE,
        name="Unsafe",
        steps=[
            AuthoringWorkflowStep(
                id="write",
                label="Write",
                tool_ref="quests",
                action="Write content",
                requires_validation=False,
                writes_content=True,
            )
        ],
        required_tools=["quests"],
    )
    try:
        validate_authoring_workflow_preset(preset)
    except AuthoringWorkflowError as exc:
        assert "bypasses validation" in str(exc)
    else:
        raise AssertionError("Expected validation bypass to be rejected")
