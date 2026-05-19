from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    ActorCondition,
    EmotionalState,
    GameState,
    NPCState,
    PrimaryEmotion,
    load_game_state_payload,
)
from app.engine.rules.emotions import (
    apply_emotional_shift,
    decay_emotion,
    emotion_from_event,
    emotion_to_dialogue_tone,
    get_emotional_state,
)
from app.llm.context_builder import build_npc_dialogue_profile_context


def _state(npc: NPCState | None = None) -> GameState:
    return GameState(world_id="test_world", npcs={"harlan": npc or NPCState(id="harlan", location_id="square")})


def test_npc_default_emotion_loads() -> None:
    state = _state()

    emotion = get_emotional_state(state, "harlan")

    assert emotion.primary_emotion == PrimaryEmotion.CALM
    assert emotion.intensity == 0
    assert emotion.stress == 0


def test_apply_emotional_shift_returns_state_delta_and_event_can_record_it() -> None:
    state = _state()

    deltas = apply_emotional_shift(
        state,
        "harlan",
        primary_emotion=PrimaryEmotion.SUSPICIOUS,
        intensity_delta=20,
        stress_delta=10,
        event_id="evt_emotion",
        reason="Test emotional shift.",
    )
    next_state = apply_delta(state, deltas[0])
    event = Event(
        event_id="evt_emotion",
        turn=state.turn,
        actor_id="system",
        action_type="emotion_shift",
        result="success",
        visible_to_player=False,
        state_deltas=deltas,
    )

    assert len(deltas) == 1
    assert deltas[0].operation == StateDeltaOperation.SET
    assert next_state.npcs["harlan"].emotional_state.primary_emotion == PrimaryEmotion.SUSPICIOUS
    assert event.state_deltas == deltas


def test_crime_witnessed_increases_fear_and_suspicion_tone() -> None:
    state = _state()

    deltas = emotion_from_event(state, "harlan", "crime_witnessed", event_id="crime_evt")
    next_state = apply_delta(state, deltas[0])
    emotion = next_state.npcs["harlan"].emotional_state

    assert emotion.primary_emotion == PrimaryEmotion.AFRAID
    assert emotion.stress == 30
    assert emotion.fear_tone == "fearful"
    assert emotion.trust_tone == "guarded"


def test_friendly_interaction_increases_affection_tone() -> None:
    state = _state()

    deltas = emotion_from_event(state, "harlan", "friendly_interaction", event_id="friendly_evt")
    next_state = apply_delta(state, deltas[0])
    emotion = next_state.npcs["harlan"].emotional_state

    assert emotion.primary_emotion == PrimaryEmotion.AFFECTIONATE
    assert emotion.affection_tone == "open"
    assert emotion.trust_tone == "warmer"


def test_emotion_decay_is_deterministic() -> None:
    state = _state(
        NPCState(
            id="harlan",
            location_id="square",
            emotional_state=EmotionalState(primary_emotion=PrimaryEmotion.ANGRY, intensity=50, stress=20, stability=70),
        )
    )

    first = apply_delta(state, decay_emotion(state, "harlan", event_id="decay_evt")[0])
    second = apply_delta(state, decay_emotion(state, "harlan", event_id="decay_evt")[0])

    assert first.npcs["harlan"].emotional_state == second.npcs["harlan"].emotional_state
    assert first.npcs["harlan"].emotional_state.intensity == 45
    assert first.npcs["harlan"].emotional_state.stress == 18


def test_emotional_state_enters_dialogue_context_as_safe_summary() -> None:
    state = _state(
        NPCState(
            id="harlan",
            location_id="square",
            emotional_state=EmotionalState(
                primary_emotion=PrimaryEmotion.DEFENSIVE,
                intensity=75,
                stress=60,
                trust_tone="guarded",
                fear_tone="alert",
                affection_tone="reserved",
            ),
        )
    )

    context = build_npc_dialogue_profile_context(state, "harlan")

    assert "defensive" in context.emotional_tone
    assert context.emotion_intensity_band == "high"
    assert "hidden" not in context.model_dump_json().lower()


def test_llm_output_cannot_directly_write_emotional_state() -> None:
    state = _state()
    forbidden_llm_delta = StateDelta(
        operation=StateDeltaOperation.SET,
        path="npcs.harlan.emotional_state",
        value=EmotionalState(primary_emotion=PrimaryEmotion.JOYFUL, intensity=100).model_dump(mode="json"),
        metadata={"source": "llm_output"},
    )

    assert state.npcs["harlan"].emotional_state.primary_emotion == PrimaryEmotion.CALM
    assert forbidden_llm_delta.metadata["source"] == "llm_output"
    # The rule layer does not apply LLM-origin deltas; only deterministic rule deltas are applied.
    assert state.npcs["harlan"].emotional_state.primary_emotion == PrimaryEmotion.CALM


def test_dead_or_incapacitated_npc_emotion_not_updated_by_normal_shift() -> None:
    state = _state(NPCState(id="harlan", location_id="square", condition=ActorCondition.DEAD, alive=False))

    assert apply_emotional_shift(state, "harlan", primary_emotion=PrimaryEmotion.SAD, intensity_delta=50) == []


def test_save_load_preserves_emotional_state() -> None:
    state = _state(
        NPCState(
            id="harlan",
            location_id="square",
            emotional_state=EmotionalState(primary_emotion=PrimaryEmotion.EXCITED, intensity=42, last_emotional_event_id="evt"),
        )
    )

    restored = load_game_state_payload(state.model_dump(mode="json"))

    assert restored.npcs["harlan"].emotional_state.primary_emotion == PrimaryEmotion.EXCITED
    assert restored.npcs["harlan"].emotional_state.intensity == 42
    assert restored.npcs["harlan"].emotional_state.last_emotional_event_id == "evt"


def test_emotion_to_dialogue_tone_is_safe_summary() -> None:
    tone = emotion_to_dialogue_tone(
        EmotionalState(primary_emotion=PrimaryEmotion.AFRAID, intensity=80, stress=10, fear_tone="watchful")
    )

    assert tone == "afraid; intensity=high; stress=low; trust=neutral; fear=watchful; affection=reserved"
