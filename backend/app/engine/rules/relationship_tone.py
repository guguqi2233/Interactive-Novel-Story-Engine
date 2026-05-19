from pydantic import BaseModel, Field

from app.core.world_state import EmotionalState, GameState, PrimaryEmotion, RelationshipState
from app.engine.rules.factions import reputation_band
from app.engine.rules.relationships import get_relationship


class RelationshipTone(BaseModel):
    address_style: str = "neutral"
    formality: str = "medium"
    warmth: int = Field(default=0, ge=0, le=100)
    tension: int = Field(default=0, ge=0, le=100)
    intimacy: int = Field(default=0, ge=0, le=100)
    respect: int = Field(default=50, ge=0, le=100)
    resentment: int = Field(default=0, ge=0, le=100)
    fear: int = Field(default=0, ge=0, le=100)
    avoidance: int = Field(default=0, ge=0, le=100)
    trust_expression: str = "reserved"


def derive_tone_from_relationship(
    relationship: RelationshipState | None,
    *,
    faction_reputation: int | None = None,
    emotional_state: EmotionalState | None = None,
    recent_event_tags: list[str] | None = None,
) -> RelationshipTone:
    trust = relationship.trust if relationship is not None else 0
    affinity = relationship.affinity if relationship is not None else 0
    obligation = relationship.obligation if relationship is not None else 0
    fear_value = relationship.fear if relationship is not None else 0
    warmth = _clamp(45 + trust + affinity // 2)
    tension = _clamp(20 - trust + fear_value)
    intimacy = _clamp(affinity + max(0, trust // 2))
    respect = _clamp(50 + obligation + trust // 2)
    resentment = _clamp(max(0, -trust) + fear_value // 2)
    avoidance = _clamp(fear_value + max(0, -affinity // 2))
    if faction_reputation is not None:
        band = reputation_band(faction_reputation)
        if band.value in {"friendly", "trusted"}:
            warmth = _clamp(warmth + 10)
            respect = _clamp(respect + 5)
        elif band.value == "hostile":
            tension = _clamp(tension + 20)
            resentment = _clamp(resentment + 10)

    if emotional_state is not None:
        if emotional_state.primary_emotion in {PrimaryEmotion.AFRAID, PrimaryEmotion.DEFENSIVE}:
            tension = _clamp(tension + emotional_state.intensity // 4)
            avoidance = _clamp(avoidance + emotional_state.stress // 4)
        if emotional_state.primary_emotion == PrimaryEmotion.AFFECTIONATE:
            warmth = _clamp(warmth + emotional_state.intensity // 4)
            intimacy = _clamp(intimacy + emotional_state.intensity // 5)
        if emotional_state.primary_emotion == PrimaryEmotion.ANGRY:
            resentment = _clamp(resentment + emotional_state.intensity // 3)
            tension = _clamp(tension + emotional_state.intensity // 4)

    tone = RelationshipTone(
        address_style=_address_style(warmth, tension, intimacy, fear_value),
        formality=_formality(warmth, tension, intimacy, respect),
        warmth=warmth,
        tension=tension,
        intimacy=intimacy,
        respect=respect,
        resentment=resentment,
        fear=_clamp(fear_value),
        avoidance=avoidance,
        trust_expression=_trust_expression(trust, warmth, tension),
    )
    for tag in recent_event_tags or []:
        tone = apply_tone_modifier(tone, tag)
    return tone


def apply_tone_modifier(tone: RelationshipTone, modifier: str) -> RelationshipTone:
    if modifier == "recent_kindness":
        return tone.model_copy(update={"warmth": _clamp(tone.warmth + 10), "trust_expression": "warmer"})
    if modifier == "recent_betrayal":
        return tone.model_copy(
            update={
                "warmth": _clamp(tone.warmth - 15),
                "tension": _clamp(tone.tension + 20),
                "resentment": _clamp(tone.resentment + 20),
                "trust_expression": "guarded",
            }
        )
    if modifier == "recent_threat":
        return tone.model_copy(update={"tension": _clamp(tone.tension + 15), "avoidance": _clamp(tone.avoidance + 10)})
    return tone


def get_tone_for_dialogue(
    state: GameState,
    source_id: str,
    target_id: str = "player",
    *,
    relation_type: str | None = None,
    recent_event_tags: list[str] | None = None,
) -> RelationshipTone:
    relationship = get_relationship(state, source_id, target_id, relation_type)
    faction_reputation = None
    emotional_state = None
    npc = state.npcs.get(source_id)
    if npc is not None:
        emotional_state = npc.emotional_state
        if npc.faction_id and npc.faction_id in state.factions:
            faction_reputation = state.factions[npc.faction_id].reputation.value
    return derive_tone_from_relationship(
        relationship,
        faction_reputation=faction_reputation,
        emotional_state=emotional_state,
        recent_event_tags=recent_event_tags,
    )


def tone_summary_for_prompt(tone: RelationshipTone) -> str:
    return (
        f"address={tone.address_style}; formality={tone.formality}; "
        f"warmth={_band(tone.warmth)}; tension={_band(tone.tension)}; "
        f"intimacy={_band(tone.intimacy)}; respect={_band(tone.respect)}; "
        f"resentment={_band(tone.resentment)}; fear={_band(tone.fear)}; "
        f"avoidance={_band(tone.avoidance)}; trust_expression={tone.trust_expression}"
    )


def _address_style(warmth: int, tension: int, intimacy: int, fear_value: int) -> str:
    if fear_value >= 60:
        return "cautious formal address"
    if tension >= 70:
        return "cold distant address"
    if intimacy >= 60:
        return "familiar address"
    if warmth >= 65:
        return "friendly address"
    return "neutral address"


def _formality(warmth: int, tension: int, intimacy: int, respect: int) -> str:
    if tension >= 70 or respect >= 75:
        return "high"
    if intimacy >= 60 or warmth >= 70:
        return "low"
    return "medium"


def _trust_expression(trust: int, warmth: int, tension: int) -> str:
    if trust >= 50 and warmth >= 60:
        return "open"
    if trust < -20 or tension >= 65:
        return "guarded"
    if trust > 10:
        return "warmer"
    return "reserved"


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
