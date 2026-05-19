from app.core.event_log import EventLog
from app.core.world_state import (
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
from app.roleplay.dialogue import DialogueManager, DialogueMode, DialogueSessionStatus


def make_dialogue_state() -> GameState:
    return GameState(
        world_id="dialogue-test",
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Square")},
        player_visible_facts={"public_square"},
        facts={
            "public_square": FactState(id="public_square", visibility=FactVisibility.PUBLIC, public=True),
            "hidden_blackmail": FactState(id="hidden_blackmail", visibility=FactVisibility.HIDDEN),
            "unknown_hidden": FactState(id="unknown_hidden", visibility=FactVisibility.HIDDEN),
        },
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                visible=True,
                knowledge=["public_square", "hidden_blackmail"],
            )
        },
        relationships={
            "harlan_player_friend": RelationshipState(
                id="harlan_player_friend",
                source_id="harlan",
                target_id="player",
                relation_type="friend",
                trust=40,
                affinity=30,
                known_by_player=True,
            )
        },
    )


def test_start_dialogue_creates_session_and_event() -> None:
    state = make_dialogue_state()
    events = EventLog()
    manager = DialogueManager()

    session = manager.start_dialogue(
        state,
        game_session_id="game-1",
        focus_npc_id="harlan",
        dialogue_mode=DialogueMode.CASUAL,
        active_topics=["tools"],
        event_log=events,
    )

    assert session.focus_npc_id == "harlan"
    assert session.status == DialogueSessionStatus.ACTIVE
    assert session.dialogue_mode == DialogueMode.CASUAL
    assert events.list_events()[0].action_type == "dialogue_start"


def test_npc_unknown_and_hidden_facts_do_not_enter_dialogue_context() -> None:
    state = make_dialogue_state()
    manager = DialogueManager()
    session = manager.start_dialogue(state, game_session_id="game-1", focus_npc_id="harlan")

    context = manager.build_dialogue_context(state, focus_npc_id="harlan", session=session)

    assert "public_square" in context.npc_known_facts
    assert "hidden_blackmail" not in context.npc_known_facts
    assert "unknown_hidden" not in context.npc_known_facts
    assert "hidden_blackmail" not in context.safe_context_summary


def test_friendly_tone_and_emotion_enter_safe_dialogue_context() -> None:
    state = make_dialogue_state()
    state.npcs["harlan"].emotional_state = EmotionalState(
        primary_emotion=PrimaryEmotion.AFFECTIONATE,
        intensity=75,
        stress=5,
    )
    manager = DialogueManager()

    session = manager.start_dialogue(state, game_session_id="game-1", focus_npc_id="harlan")
    context = manager.build_dialogue_context(state, focus_npc_id="harlan", session=session)

    assert "warmth=high" in context.relationship_tone_summary
    assert context.emotional_summary.endswith(":high")
    assert "affectionate" in context.emotional_summary
    assert "hidden" not in context.safe_context_summary


def test_dialogue_can_apply_rule_based_relationship_delta() -> None:
    state = make_dialogue_state()
    events = EventLog()
    manager = DialogueManager()
    session = manager.start_dialogue(state, game_session_id="game-1", focus_npc_id="harlan")

    result = manager.continue_dialogue(
        state,
        events,
        dialogue_session_id=session.session_id,
        player_input="thank you, please let me help",
    )

    assert result.state.relationships["harlan_player_friend"].trust == 41
    assert result.state.relationships["harlan_player_friend"].affinity == 31
    assert result.event is not None
    assert result.event.action_type == "dialogue"
    assert [delta.path for delta in result.event.state_deltas] == [
        "relationships.harlan_player_friend.trust",
        "relationships.harlan_player_friend.affinity",
        "npcs.harlan.emotional_state",
    ]


def test_dialogue_output_cannot_directly_modify_game_state() -> None:
    state = make_dialogue_state()
    before = state.model_copy(deep=True)
    manager = DialogueManager()

    check = manager.validate_dialogue_output(
        RoleplayOutputCandidate(
            text="Harlan declares the quest complete.",
            proposed_fact_creations=["invented_key_item"],
            proposed_state_changes=["quests.main.status=completed"],
        )
    )

    assert check.ok is False
    assert state == before
    assert {issue.code for issue in check.issues} == {"prohibited_fact_creation", "prohibited_state_change"}


def test_end_dialogue_sets_ended_status() -> None:
    state = make_dialogue_state()
    manager = DialogueManager()
    session = manager.start_dialogue(state, game_session_id="game-1", focus_npc_id="harlan")

    ended = manager.end_dialogue(session.session_id, turn=3)

    assert ended.status == DialogueSessionStatus.ENDED
    assert ended.last_turn == 3


def test_dialogue_end_requested_from_input_records_event() -> None:
    state = make_dialogue_state()
    events = EventLog()
    manager = DialogueManager()
    session = manager.start_dialogue(state, game_session_id="game-1", focus_npc_id="harlan")

    result = manager.continue_dialogue(
        state,
        events,
        dialogue_session_id=session.session_id,
        player_input="bye",
    )

    assert result.session.status == DialogueSessionStatus.ENDED
    assert result.event is not None
    assert result.event.action_type == "dialogue_end"
    assert result.event.allow_empty_delta is True
    assert events.list_events()[-1].action_type == "dialogue_end"
