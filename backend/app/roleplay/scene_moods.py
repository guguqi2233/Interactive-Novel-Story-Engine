from __future__ import annotations

from app.core.world_state import GameState, SceneMoodPreset


def get_scene_mood_preset(state: GameState, preset_id: str | None) -> SceneMoodPreset | None:
    if not preset_id:
        return None
    preset = state.scene_mood_presets.get(preset_id)
    if preset is None:
        raise ValueError(f"Scene mood preset not found: {preset_id}")
    return preset


def scene_mood_summary_for_prompt(state: GameState, preset_id: str | None) -> str:
    """Build a safe style-only summary for narrator/dialogue prompts.

    The summary intentionally omits free-form forbidden-content rule text. Those
    rules are useful for authoring validation and future checks, but prompt
    summaries should stay compact and avoid accidentally carrying spoiler text.
    """
    preset = get_scene_mood_preset(state, preset_id)
    if preset is None:
        return ""
    intensity_min, intensity_max = preset.allowed_intensity_range
    focus = ",".join(sorted(set(preset.sensory_focus)))
    genres = ",".join(sorted(set(preset.compatible_genres)))
    return (
        f"scene_mood={preset.id}; tone={preset.tone}; pacing={preset.pacing}; "
        f"sensory_focus={focus or 'none'}; metaphor_style={preset.metaphor_style or 'plain'}; "
        f"dialogue_pressure={preset.dialogue_pressure}; intensity={intensity_min}-{intensity_max}; "
        f"compatible_genres={genres or 'any'}; forbidden_rule_count={len(preset.forbidden_content_rules)}"
    )
