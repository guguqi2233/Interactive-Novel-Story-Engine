from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import ActorCondition, EmotionalState, GameState, PrimaryEmotion


class EmotionRuleError(ValueError):
    """Raised when an emotional rule cannot be applied safely."""


def get_emotional_state(state: GameState, npc_id: str) -> EmotionalState:
    if npc_id not in state.npcs:
        raise EmotionRuleError(f"Unknown NPC: {npc_id}")
    return state.npcs[npc_id].emotional_state


def apply_emotional_shift(
    state: GameState,
    npc_id: str,
    *,
    primary_emotion: PrimaryEmotion | str | None = None,
    intensity_delta: int = 0,
    stress_delta: int = 0,
    stability_delta: int = 0,
    trust_tone: str | None = None,
    fear_tone: str | None = None,
    affection_tone: str | None = None,
    event_id: str | None = None,
    expires_turn: int | None = None,
    reason: str = "NPC emotional state shifted by deterministic rule.",
    allow_incapacitated: bool = False,
) -> list[StateDelta]:
    npc = state.npcs.get(npc_id)
    if npc is None:
        raise EmotionRuleError(f"Unknown NPC: {npc_id}")
    if npc.condition in {ActorCondition.DEAD, ActorCondition.INCAPACITATED} and not allow_incapacitated:
        return []

    current = npc.emotional_state
    next_state = current.model_copy(
        update={
            "primary_emotion": PrimaryEmotion(primary_emotion) if primary_emotion is not None else current.primary_emotion,
            "intensity": _clamp(current.intensity + intensity_delta),
            "stress": _clamp(current.stress + stress_delta),
            "stability": _clamp(current.stability + stability_delta),
            "trust_tone": trust_tone if trust_tone is not None else current.trust_tone,
            "fear_tone": fear_tone if fear_tone is not None else current.fear_tone,
            "affection_tone": affection_tone if affection_tone is not None else current.affection_tone,
            "last_emotional_event_id": event_id if event_id is not None else current.last_emotional_event_id,
            "expires_turn": expires_turn if expires_turn is not None else current.expires_turn,
        }
    )
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"npcs.{npc_id}.emotional_state",
            value=next_state.model_dump(mode="json"),
            caused_by_event_id=event_id,
            reason=reason,
            metadata={"source": "emotion_rule", "npc_id": npc_id},
        )
    ]


def decay_emotion(state: GameState, npc_id: str, *, event_id: str | None = None) -> list[StateDelta]:
    current = get_emotional_state(state, npc_id)
    if state.npcs[npc_id].condition in {ActorCondition.DEAD, ActorCondition.INCAPACITATED}:
        return []
    if current.intensity == 0 and current.stress == 0 and current.primary_emotion == PrimaryEmotion.CALM:
        return []
    stability_factor = max(1, 12 - current.stability // 10)
    next_intensity = max(0, current.intensity - stability_factor)
    next_stress = max(0, current.stress - max(1, stability_factor // 2))
    next_emotion = PrimaryEmotion.CALM if next_intensity == 0 and next_stress == 0 else current.primary_emotion
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"npcs.{npc_id}.emotional_state",
            value=current.model_copy(
                update={
                    "primary_emotion": next_emotion,
                    "intensity": next_intensity,
                    "stress": next_stress,
                    "last_emotional_event_id": event_id or current.last_emotional_event_id,
                    "expires_turn": None if current.expires_turn is not None and state.turn >= current.expires_turn else current.expires_turn,
                }
            ).model_dump(mode="json"),
            caused_by_event_id=event_id,
            reason="NPC emotion decayed deterministically.",
            metadata={"source": "emotion_rule", "npc_id": npc_id, "decay": "true"},
        )
    ]


def emotion_from_event(state: GameState, npc_id: str, event_type: str, *, event_id: str | None = None) -> list[StateDelta]:
    event_key = event_type.lower()
    if event_key in {"crime_witnessed", "witnessed_crime", "crime"}:
        return apply_emotional_shift(
            state,
            npc_id,
            primary_emotion=PrimaryEmotion.AFRAID,
            intensity_delta=25,
            stress_delta=30,
            stability_delta=-10,
            trust_tone="guarded",
            fear_tone="fearful",
            event_id=event_id,
            reason="NPC witnessed or learned of a crime.",
        )
    if event_key in {"friendly_interaction", "kindness", "helped"}:
        return apply_emotional_shift(
            state,
            npc_id,
            primary_emotion=PrimaryEmotion.AFFECTIONATE,
            intensity_delta=12,
            stress_delta=-5,
            stability_delta=5,
            trust_tone="warmer",
            affection_tone="open",
            event_id=event_id,
            reason="NPC experienced a friendly interaction.",
        )
    if event_key in {"threat", "attack", "combat"}:
        return apply_emotional_shift(
            state,
            npc_id,
            primary_emotion=PrimaryEmotion.DEFENSIVE,
            intensity_delta=20,
            stress_delta=20,
            stability_delta=-5,
            fear_tone="alert",
            event_id=event_id,
            reason="NPC reacted to a threat.",
        )
    return []


def emotion_to_dialogue_tone(emotional_state: EmotionalState) -> str:
    if emotional_state.primary_emotion == PrimaryEmotion.CALM:
        return "calm"
    return (
        f"{emotional_state.primary_emotion.value}; "
        f"intensity={_band(emotional_state.intensity)}; "
        f"stress={_band(emotional_state.stress)}; "
        f"trust={emotional_state.trust_tone}; "
        f"fear={emotional_state.fear_tone}; "
        f"affection={emotional_state.affection_tone}"
    )


def _clamp(value: int) -> int:
    return min(100, max(0, value))


def _band(value: int) -> str:
    if value >= 70:
        return "high"
    if value >= 35:
        return "medium"
    if value > 0:
        return "low"
    return "none"
