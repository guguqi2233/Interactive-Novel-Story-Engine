import pytest

from app.core.event_log import EventLog
from app.core.world_state import (
    ActorCondition,
    EmotionalState,
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    NPCState,
    PlayerState,
    PrimaryEmotion,
    RelationshipState,
)
from app.roleplay.boundary import RoleplayOutputCandidate
from app.roleplay.dialogue import GroupDialogueManager, GroupDialogueSceneStatus


def make_group_state() -> GameState:
    return GameState(
        world_id="group-dialogue-test",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Square")},
        player_visible_facts={"public_market"},
        facts={
            "public_market": FactState(id="public_market", visibility=FactVisibility.PUBLIC, public=True),
            "hidden_debt": FactState(id="hidden_debt", visibility=FactVisibility.HIDDEN),
        },
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                visible=True,
                knowledge=["public_market"],
                emotional_state=EmotionalState(primary_emotion=PrimaryEmotion.CALM, intensity=10),
            ),
            "mira": NPCState(
                id="mira",
                location_id="square",
                visible=True,
                knowledge=["public_market", "hidden_debt"],
                emotional_state=EmotionalState(primary_emotion=PrimaryEmotion.ANGRY, intensity=80),
            ),
            "tomas": NPCState(
                id="tomas",
                location_id="square",
                visible=True,
                condition=ActorCondition.INCAPACITATED,
                alive=True,
            ),
        },
        relationships={
            "harlan_player": RelationshipState(
                id="harlan_player",
                source_id="harlan",
                target_id="player",
                relation_type="general",
                trust=25,
                known_by_player=True,
            ),
            "mira_player": RelationshipState(
                id="mira_player",
                source_id="mira",
                target_id="player",
                relation_type="general",
                trust=-20,
                fear=10,
                known_by_player=True,
            ),
        },
    )


def test_group_scene_can_be_created_and_records_event() -> None:
    state = make_group_state()
    events = EventLog()
    manager = GroupDialogueManager()

    scene = manager.start_group_scene(
        state,
        participant_ids=["harlan", "mira"],
        scene_topic="market",
        scene_mood="tense",
        event_log=events,
    )

    assert scene.status == GroupDialogueSceneStatus.ACTIVE
    assert scene.location_id == "square"
    assert scene.participant_ids == ["harlan", "mira"]
    assert events.list_events()[0].action_type == "group_dialogue_start"


def test_each_npc_context_is_independent() -> None:
    state = make_group_state()
    manager = GroupDialogueManager()
    scene = manager.start_group_scene(state, participant_ids=["harlan", "mira"])

    harlan = manager.build_participant_context(state, scene.scene_id, "harlan")
    mira = manager.build_participant_context(state, scene.scene_id, "mira")

    assert "hidden_debt" not in harlan.npc_known_facts
    assert "hidden_debt" in mira.npc_known_facts
    assert harlan.relationship_tone_summary != mira.relationship_tone_summary


def test_hidden_fact_not_in_player_safe_group_summary() -> None:
    state = make_group_state()
    manager = GroupDialogueManager()
    scene = manager.start_group_scene(state, participant_ids=["harlan", "mira"])

    mira = manager.build_participant_context(state, scene.scene_id, "mira")

    assert "hidden_debt" in mira.npc_known_facts
    assert "hidden_debt" not in mira.safe_context_summary


def test_next_speaker_selection_is_deterministic() -> None:
    state = make_group_state()
    manager = GroupDialogueManager()
    scene = manager.start_group_scene(state, participant_ids=["harlan", "mira"], active_speaker_id="harlan")

    first = manager.select_next_speaker(state, scene.scene_id)
    second = manager.select_next_speaker(state, scene.scene_id)

    assert first == "mira"
    assert second == "mira"


def test_dead_or_incapacitated_npc_cannot_join_group_scene() -> None:
    state = make_group_state()
    manager = GroupDialogueManager()

    with pytest.raises(ValueError, match="cannot talk"):
        manager.start_group_scene(state, participant_ids=["harlan", "tomas"])


def test_group_participant_output_cannot_modify_state() -> None:
    state = make_group_state()
    before = state.model_copy(deep=True)
    manager = GroupDialogueManager()

    check = manager.validate_participant_output(
        RoleplayOutputCandidate(
            text="Mira declares the mystery solved.",
            proposed_fact_creations=["invented_confession"],
            proposed_state_changes=["relationships.mira_player.trust=100"],
        )
    )

    assert check.ok is False
    assert state == before
