from pathlib import Path

import pytest
import yaml

from app.core.world_state import (
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    NPCState,
    PlayerState,
    SceneMoodPreset,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.content.world_loader import WorldLoader, WorldLoaderError
from app.llm.fake_provider import FakeLLMProvider
from app.llm.narrator import Narrator
from app.llm.prompt_profiles import PromptProfile
from app.llm.schemas import NarrativeResult
from app.roleplay.dialogue import DialogueManager, GroupDialogueManager
from app.roleplay.scene_moods import scene_mood_summary_for_prompt


def make_mood_state() -> GameState:
    return GameState(
        world_id="mood-test",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Square")},
        player_visible_facts={"public_square"},
        facts={
            "public_square": FactState(id="public_square", visibility=FactVisibility.PUBLIC, public=True),
            "hidden_debt": FactState(id="hidden_debt", text="Mira owes the smuggler", visibility=FactVisibility.HIDDEN),
        },
        npcs={
            "harlan": NPCState(id="harlan", location_id="square", visible=True, knowledge=["public_square"]),
            "mira": NPCState(id="mira", location_id="square", visible=True, knowledge=["public_square", "hidden_debt"]),
        },
        scene_mood_presets={
            "noir_tension": SceneMoodPreset(
                id="noir_tension",
                name="Noir Tension",
                tone="tense",
                pacing="clipped",
                sensory_focus=["rain", "neon"],
                metaphor_style="noir",
                dialogue_pressure="high",
                allowed_intensity_range=[20, 70],
                forbidden_content_rules=["Do not reveal Mira owes the smuggler."],
                compatible_genres=["mystery"],
            )
        },
    )


def test_scene_mood_preset_loads_from_content_pack() -> None:
    pack = WorldLoader("worlds").load("mist_valley")
    state = pack.to_game_state()

    assert "mist_tension" in state.scene_mood_presets
    assert state.scene_mood_presets["mist_tension"].dialogue_pressure == "high"


def test_invalid_scene_mood_preset_is_rejected(tmp_path: Path) -> None:
    world = tmp_path / "bad_world"
    world.mkdir()
    _write_yaml(world / "manifest.yaml", {"world_id": "bad_world", "name": "Bad", "start_location_id": "square"})
    _write_yaml(world / "locations.yaml", {"locations": [{"id": "square", "name": "Square", "description": ""}]})
    _write_yaml(world / "npcs.yaml", {"npcs": [{"id": "harlan", "name": "Harlan", "location_id": "square", "personality": ""}]})
    _write_yaml(
        world / "scene_moods.yaml",
        {
            "scene_mood_presets": [
                {
                    "id": "bad_mood",
                    "name": "Bad Mood",
                    "dialogue_pressure": "omniscient",
                    "allowed_intensity_range": [80, 20],
                }
            ]
        },
    )

    with pytest.raises(WorldLoaderError, match="World pack schema validation failed"):
        WorldLoader(tmp_path).load("bad_world")


def test_selected_mood_enters_dialogue_safe_context_without_hidden_text() -> None:
    state = make_mood_state()
    manager = DialogueManager()

    session = manager.start_dialogue(
        state,
        game_session_id="game-1",
        focus_npc_id="harlan",
        scene_mood_preset_id="noir_tension",
    )
    context = manager.build_dialogue_context(state, focus_npc_id="harlan", session=session)

    assert "scene_mood=noir_tension" in context.scene_mood_summary
    assert "tone=tense" in context.safe_context_summary
    assert "Mira owes the smuggler" not in context.safe_context_summary
    assert "hidden_debt" not in context.safe_context_summary


def test_selected_mood_enters_group_safe_context_without_cross_npc_fact_leak() -> None:
    state = make_mood_state()
    manager = GroupDialogueManager()
    scene = manager.start_group_scene(
        state,
        participant_ids=["harlan", "mira"],
        scene_topic="market",
        scene_mood="tense",
        scene_mood_preset_id="noir_tension",
    )

    harlan = manager.build_participant_context(state, scene.scene_id, "harlan")
    mira = manager.build_participant_context(state, scene.scene_id, "mira")

    assert "scene_mood=noir_tension" in harlan.scene_mood_summary
    assert "hidden_debt" not in harlan.safe_context_summary
    assert "hidden_debt" not in mira.safe_context_summary


def test_mood_summary_does_not_modify_game_state() -> None:
    state = make_mood_state()
    before = state.model_copy(deep=True)

    summary = scene_mood_summary_for_prompt(state, "noir_tension")

    assert "scene_mood=noir_tension" in summary
    assert state == before


def test_prompt_profile_mood_does_not_override_action_result() -> None:
    provider = RecordingNarratorProvider(
        {
            "text": "You still fail to open the lock.",
            "suggested_actions": ["try again"],
            "short_summary": "Failed lock attempt.",
        }
    )
    narrator = Narrator(
        provider,
        prompt_profile=PromptProfile(
            id="moody",
            name="Moody",
            scene_mood_preset_id="noir_tension",
        ),
    )
    action_result = ActionResult(
        success_level=SuccessLevel.FAILURE,
        reason="The lock does not budge.",
        visible_facts=["locked_door"],
        hidden_facts=["hidden_debt"],
    )

    result = narrator.render(
        player_input="open the lock",
        action_result=action_result,
        visible_facts=["locked_door"],
        current_location="square",
        tone="quiet",
        scene_mood_summary="scene_mood=noir_tension; tone=tense",
    )

    prompt_text = str(provider.messages)
    assert result == NarrativeResult(
        text="You still fail to open the lock.",
        suggested_actions=["try again"],
        short_summary="Failed lock attempt.",
    )
    assert "failure" in prompt_text
    assert "scene_mood=noir_tension" in prompt_text
    assert "hidden_debt" not in prompt_text


class RecordingNarratorProvider(FakeLLMProvider):
    def __init__(self, response: dict[str, object]) -> None:
        super().__init__(json_responses=[response])
        self.messages: list[dict[str, str]] = []

    def generate_json(
        self,
        messages: list[dict[str, str]],
        schema: type[NarrativeResult],
        temperature: float = 0.2,
    ) -> NarrativeResult:
        self.messages = messages
        return super().generate_json(messages, schema, temperature)


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
