from enum import StrEnum

from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import ActorCondition, CrimeStatus, GameState
from app.engine.rules.factions import ReputationBand, reputation_band
from app.engine.rules.life_state import can_act


class NPCReactionType(StrEnum):
    INCREASE_SUSPICION = "increase_suspicion"
    DECREASE_TRUST = "decrease_trust"
    REFUSE_TALK = "refuse_talk"
    FLEE = "flee"
    CALL_FOR_HELP = "call_for_help"
    SPREAD_RUMOR = "spread_rumor"
    BECOME_HOSTILE = "become_hostile"
    BECOME_FRIENDLY = "become_friendly"


def resolve_npc_reactions(state: GameState) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    working_state = state

    for npc in sorted(state.npcs.values(), key=lambda item: item.id):
        if not can_act(working_state, npc.id):
            continue

        for delta in _crime_reaction_deltas(working_state, npc.id):
            deltas.append(delta)
            working_state = apply_delta(working_state, delta)

        for delta in _reputation_reaction_deltas(working_state, npc.id):
            deltas.append(delta)
            working_state = apply_delta(working_state, delta)

        for delta in _rumor_reaction_deltas(working_state, npc.id):
            deltas.append(delta)
            working_state = apply_delta(working_state, delta)

        for delta in _injury_reaction_deltas(working_state, npc.id):
            deltas.append(delta)
            working_state = apply_delta(working_state, delta)

    return deltas


def _crime_reaction_deltas(state: GameState, npc_id: str) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    npc = state.npcs[npc_id]
    for crime in sorted(state.crimes.values(), key=lambda item: item.id):
        if npc_id not in crime.witnessed_by and f"crime:{crime.id}" not in npc.knowledge:
            continue
        source_id = f"crime:{crime.id}"
        if not _already_reacted(state, npc_id, NPCReactionType.INCREASE_SUSPICION, source_id):
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.INC,
                    path=f"npcs.{npc_id}.suspicion",
                    value=max(1, crime.severity),
                    reason="NPC reacts suspiciously to a known crime.",
                    metadata={"source": "npc_reaction", "npc_id": npc_id, "reaction": NPCReactionType.INCREASE_SUSPICION, "source_id": source_id},
                )
            )
            deltas.append(_reaction_marker(npc_id, NPCReactionType.INCREASE_SUSPICION, source_id))
        if crime.status in {CrimeStatus.WITNESSED, CrimeStatus.REPORTED} and not _already_reacted(
            state, npc_id, NPCReactionType.DECREASE_TRUST, source_id
        ):
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.INC,
                    path=f"npcs.{npc_id}.relationship_to_player",
                    value=-max(1, crime.severity),
                    reason="NPC trusts the player less after a known crime.",
                    metadata={"source": "npc_reaction", "npc_id": npc_id, "reaction": NPCReactionType.DECREASE_TRUST, "source_id": source_id},
                )
            )
            deltas.append(_reaction_marker(npc_id, NPCReactionType.DECREASE_TRUST, source_id))
    return deltas


def _reputation_reaction_deltas(state: GameState, npc_id: str) -> list[StateDelta]:
    npc = state.npcs[npc_id]
    if npc.faction_id is None or npc.faction_id not in state.factions:
        return []
    faction = state.factions[npc.faction_id]
    band = reputation_band(faction.reputation.value)
    source_id = f"faction:{npc.faction_id}:{band.value}"
    if band == ReputationBand.HOSTILE and not _already_reacted(state, npc_id, NPCReactionType.BECOME_HOSTILE, source_id):
        deltas = [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"npcs.{npc_id}.mood",
                value="hostile",
                reason="NPC became hostile because faction reputation is hostile.",
                metadata={"source": "npc_reaction", "npc_id": npc_id, "reaction": NPCReactionType.BECOME_HOSTILE, "source_id": source_id},
            ),
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path=f"npcs.{npc_id}.hostile_to",
                value=state.player.id,
                reason="NPC became hostile to the player.",
                metadata={"source": "npc_reaction", "npc_id": npc_id, "reaction": NPCReactionType.BECOME_HOSTILE, "source_id": source_id},
            ),
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path=f"npcs.{npc_id}.status_effects",
                value="refuse_talk",
                reason="NPC refuses to talk while hostile.",
                metadata={"source": "npc_reaction", "npc_id": npc_id, "reaction": NPCReactionType.REFUSE_TALK, "source_id": source_id},
            ),
            _reaction_marker(npc_id, NPCReactionType.BECOME_HOSTILE, source_id),
            _reaction_marker(npc_id, NPCReactionType.REFUSE_TALK, source_id),
        ]
        return deltas
    if band == ReputationBand.TRUSTED and not _already_reacted(state, npc_id, NPCReactionType.BECOME_FRIENDLY, source_id):
        return [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"npcs.{npc_id}.mood",
                value="friendly",
                reason="NPC became friendly because faction reputation is trusted.",
                metadata={"source": "npc_reaction", "npc_id": npc_id, "reaction": NPCReactionType.BECOME_FRIENDLY, "source_id": source_id},
            ),
            _reaction_marker(npc_id, NPCReactionType.BECOME_FRIENDLY, source_id),
        ]
    return []


def _rumor_reaction_deltas(state: GameState, npc_id: str) -> list[StateDelta]:
    for rumor in sorted(state.rumors.values(), key=lambda item: item.id):
        if npc_id not in rumor.known_by_npcs:
            continue
        source_id = f"rumor:{rumor.id}"
        if _already_reacted(state, npc_id, NPCReactionType.SPREAD_RUMOR, source_id):
            continue
        if "spread_rumor" in state.npcs[npc_id].goals:
            return [_reaction_marker(npc_id, NPCReactionType.SPREAD_RUMOR, source_id)]
        return [
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path=f"npcs.{npc_id}.goals",
                value="spread_rumor",
                reason="NPC wants to spread a known rumor.",
                metadata={"source": "npc_reaction", "npc_id": npc_id, "reaction": NPCReactionType.SPREAD_RUMOR, "source_id": source_id},
            ),
            _reaction_marker(npc_id, NPCReactionType.SPREAD_RUMOR, source_id),
        ]
    return []


def _injury_reaction_deltas(state: GameState, npc_id: str) -> list[StateDelta]:
    npc = state.npcs[npc_id]
    if npc.condition not in {ActorCondition.WOUNDED, ActorCondition.CRITICAL}:
        return []
    source_id = f"injury:{npc.condition.value}"
    if _already_reacted(state, npc_id, NPCReactionType.FLEE, source_id):
        return []
    location = state.locations.get(npc.location_id)
    if location is None or not location.exits:
        return []
    destination = next(iter(location.exits.values()))
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"npcs.{npc_id}.location_id",
            value=destination,
            reason="Injured NPC fled to a reachable location.",
            metadata={"source": "npc_reaction", "npc_id": npc_id, "reaction": NPCReactionType.FLEE, "source_id": source_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"npcs.{npc_id}.combat_stance",
            value="fleeing",
            reason="Injured NPC is fleeing.",
            metadata={"source": "npc_reaction", "npc_id": npc_id, "reaction": NPCReactionType.FLEE, "source_id": source_id},
        ),
        _reaction_marker(npc_id, NPCReactionType.FLEE, source_id),
    ]


def _already_reacted(state: GameState, npc_id: str, reaction: NPCReactionType, source_id: str) -> bool:
    return state.social_flags.get(_reaction_key(npc_id, reaction, source_id)) is True


def _reaction_marker(npc_id: str, reaction: NPCReactionType, source_id: str) -> StateDelta:
    return StateDelta(
        operation=StateDeltaOperation.SET,
        path=f"social_flags.{_reaction_key(npc_id, reaction, source_id)}",
        value=True,
        reason="NPC reaction processed.",
        metadata={"source": "npc_reaction", "npc_id": npc_id, "reaction": reaction.value, "source_id": source_id},
    )


def _reaction_key(npc_id: str, reaction: NPCReactionType, source_id: str) -> str:
    safe_source = source_id.replace(":", "_")
    return f"npc_reaction_{npc_id}_{reaction.value}_{safe_source}"
