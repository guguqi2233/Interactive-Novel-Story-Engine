from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    CrimeState,
    CrimeStatus,
    GameState,
    WitnessRecord,
    WitnessReportIntent,
)
from app.engine.rules.factions import change_reputation
from app.engine.rules.life_state import can_act
from app.engine.rules.rumors import create_rumor


class CrimeRuleError(ValueError):
    """Raised when crime rules cannot resolve cleanly."""


class CrimeDraft(BaseModel):
    crime_type: str
    actor_id: str
    location_id: str
    victim_id: str | None = None
    target_id: str | None = None
    severity: int = 1
    tags: list[str] = Field(default_factory=list)


class VisibleCrime(BaseModel):
    id: str
    crime_type: str
    location_id: str
    severity: int
    status: CrimeStatus
    created_turn: int


CRIME_TYPES = {
    "trespass",
    "theft",
    "assault",
    "murder",
    "lockpicking",
    "vandalism",
    "forbidden_magic",
}


def classify_crime(event: Event, state: GameState) -> CrimeDraft | None:
    if event.actor_id != state.player.id:
        return None
    location_id = state.player.location_id

    if event.action_type == "lockpick" and event.result in {"failure", "partial_success"}:
        return CrimeDraft(
            crime_type="lockpicking",
            actor_id=event.actor_id,
            target_id=event.target_id,
            location_id=location_id,
            severity=2 if event.result == "failure" else 1,
            tags=["lockpick"],
        )

    if event.action_type in {"attack", "assault"}:
        crime_type = "murder" if _event_marks_target_dead(event) else "assault"
        return CrimeDraft(
            crime_type=crime_type,
            actor_id=event.actor_id,
            victim_id=event.target_id,
            target_id=event.target_id,
            location_id=location_id,
            severity=5 if crime_type == "murder" else 3,
            tags=["violence"],
        )

    if event.action_type == "murder":
        return CrimeDraft(
            crime_type="murder",
            actor_id=event.actor_id,
            victim_id=event.target_id,
            target_id=event.target_id,
            location_id=location_id,
            severity=5,
            tags=["violence"],
        )

    if _event_transfers_non_player_item_to_player(event):
        return CrimeDraft(
            crime_type="theft",
            actor_id=event.actor_id,
            target_id=_transferred_item_id(event),
            location_id=location_id,
            severity=2,
            tags=["theft"],
        )

    return None


def detect_witnesses(event: Event, state: GameState) -> list[WitnessRecord]:
    draft = classify_crime(event, state)
    if draft is None:
        return []
    saw_actor = not _event_has_metadata(event, "sneak_result", "success")
    witnesses: list[WitnessRecord] = []
    location = state.locations.get(draft.location_id)
    cover_level = location.cover_level if location is not None else 0
    light_level = location.light_level if location is not None else 5

    for npc in sorted(state.npcs.values(), key=lambda item: item.id):
        if npc.location_id != draft.location_id:
            continue
        if not npc.visible:
            continue
        if not can_act(state, npc.id):
            continue
        certainty = max(0, 5 + light_level - cover_level + npc.alertness + npc.suspicion)
        if certainty <= 0:
            continue
        report_intent = (
            WitnessReportIntent.IMMEDIATE
            if certainty >= 8 or draft.severity >= 3
            else WitnessReportIntent.LATER
        )
        witnesses.append(
            WitnessRecord(
                id=f"pending:{npc.id}",
                npc_id=npc.id,
                certainty=certainty,
                confidence=certainty,
                saw_actor=saw_actor,
                saw_target=draft.target_id is not None,
                report_intent=report_intent,
            )
        )
    return witnesses


def create_crime_record(
    state: GameState,
    draft: CrimeDraft,
    witnesses: list[WitnessRecord] | None = None,
    crime_id: str | None = None,
) -> list[StateDelta]:
    if draft.crime_type not in CRIME_TYPES:
        raise CrimeRuleError(f"Unsupported crime_type: {draft.crime_type}")
    resolved_crime_id = crime_id or f"crime_{uuid4().hex}"
    witness_ids = [witness.npc_id for witness in witnesses or [] if witness.saw_actor]
    status = CrimeStatus.WITNESSED if witness_ids else CrimeStatus.HIDDEN
    crime = CrimeState(
        id=resolved_crime_id,
        crime_type=draft.crime_type,
        location_id=draft.location_id,
        actor_id=draft.actor_id,
        victim_id=draft.victim_id,
        target_id=draft.target_id,
        witnessed_by=witness_ids,
        witness_ids=witness_ids,
        severity=draft.severity,
        status=status,
        turn=state.turn,
        created_turn=state.turn,
        tags=draft.tags,
    )
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"crimes.{resolved_crime_id}",
            value=crime,
            reason="Crime record created.",
            metadata={"source": "crime", "crime_id": resolved_crime_id, "crime_type": draft.crime_type},
        )
    ]


def add_witness_record(
    state: GameState,
    crime_id: str,
    witness: WitnessRecord,
) -> list[StateDelta]:
    if crime_id not in state.crimes:
        raise CrimeRuleError(f"Unknown crime_id: {crime_id}")
    if witness.npc_id not in state.npcs:
        raise CrimeRuleError(f"Unknown witness npc_id: {witness.npc_id}")
    record = witness.model_copy(
        update={
            "id": f"{crime_id}:{witness.npc_id}",
            "crime_id": crime_id,
            "confidence": witness.certainty,
        }
    )
    deltas = [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"witnesses.{record.id}",
            value=record,
            reason="Witness record created.",
            metadata={"source": "crime_witness", "crime_id": crime_id, "npc_id": witness.npc_id},
        ),
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"npcs.{witness.npc_id}.knowledge",
            value=f"crime:{crime_id}",
            reason="Witness learned about a crime.",
            metadata={"source": "crime_witness", "crime_id": crime_id, "npc_id": witness.npc_id},
        ),
    ]
    if record.saw_actor:
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path=f"crimes.{crime_id}.witnessed_by",
                value=witness.npc_id,
                reason="Crime gained a witness.",
                metadata={"source": "crime_witness", "crime_id": crime_id, "npc_id": witness.npc_id},
            )
        )
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path=f"crimes.{crime_id}.witness_ids",
                value=witness.npc_id,
                reason="Crime gained a witness.",
                metadata={"source": "crime_witness", "crime_id": crime_id, "npc_id": witness.npc_id},
            )
        )
    return deltas


def apply_crime_consequences(state: GameState, crime_id: str) -> list[StateDelta]:
    crime = state.crimes.get(crime_id)
    if crime is None:
        raise CrimeRuleError(f"Unknown crime_id: {crime_id}")

    deltas: list[StateDelta] = []
    if crime.witnessed_by and crime.status == CrimeStatus.HIDDEN:
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"crimes.{crime_id}.status",
                value=CrimeStatus.WITNESSED,
                reason="Crime was witnessed.",
                metadata={"source": "crime", "crime_id": crime_id},
            )
        )

    for witness_id in crime.witnessed_by:
        npc = state.npcs.get(witness_id)
        if npc is None:
            continue
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.INC,
                path=f"npcs.{witness_id}.suspicion",
                value=max(1, crime.severity),
                reason="Witness became more suspicious after a crime.",
                metadata={"source": "crime", "crime_id": crime_id, "npc_id": witness_id},
            )
        )
        if npc.faction_id and npc.faction_id in state.factions:
            deltas.extend(
                change_reputation(
                    state,
                    npc.faction_id,
                    -max(1, crime.severity),
                    f"Reported {crime.crime_type}.",
                )
            )
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.ADD,
                    path=f"crimes.{crime_id}.reported_to",
                    value=npc.faction_id,
                    reason="Crime was reported to faction.",
                    metadata={"source": "crime", "crime_id": crime_id, "faction_id": npc.faction_id},
                )
            )
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.ADD,
                    path=f"crimes.{crime_id}.reported_to_factions",
                    value=npc.faction_id,
                    reason="Crime was reported to faction.",
                    metadata={"source": "crime", "crime_id": crime_id, "faction_id": npc.faction_id},
                )
            )
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"crimes.{crime_id}.status",
                    value=CrimeStatus.REPORTED,
                    reason="Crime was reported.",
                    metadata={"source": "crime", "crime_id": crime_id},
                )
            )
        if _rumor_id(crime_id) not in state.rumors:
            deltas.extend(
                create_rumor(
                    state,
                    rumor_id=_rumor_id(crime_id),
                    text_for_player=f"People are whispering about a {crime.crime_type} incident.",
                    source_event_id=crime_id,
                    truth_status="unknown",
                    known_by_npcs=[witness_id],
                    known_by_factions=[npc.faction_id] if npc.faction_id else [],
                    spread_level=1,
                    tags=["crime", crime.crime_type],
                )
            )
    return deltas


def get_player_known_crimes(state: GameState) -> list[VisibleCrime]:
    return [
        VisibleCrime(
            id=crime.id,
            crime_type=crime.crime_type,
            location_id=crime.location_id,
            severity=crime.severity,
            status=crime.status,
            created_turn=crime.created_turn,
        )
        for crime in sorted(state.crimes.values(), key=lambda item: item.id)
        if crime.known_to_player or crime.status in {CrimeStatus.REPORTED, CrimeStatus.RESOLVED}
    ]


def resolve_crime_from_event(event: Event, state: GameState) -> list[StateDelta]:
    draft = classify_crime(event, state)
    if draft is None:
        return []
    witnesses = detect_witnesses(event, state)
    crime_id = f"crime_{event.event_id.replace('-', '_')}"
    deltas = create_crime_record(state, draft, witnesses=[], crime_id=crime_id)
    crime_state = state.model_copy(deep=True)
    from app.core.state_delta import apply_delta

    for delta in deltas:
        crime_state = apply_delta(crime_state, delta)
    for witness in witnesses:
        witness_deltas = add_witness_record(crime_state, crime_id, witness)
        for delta in witness_deltas:
            crime_state = apply_delta(crime_state, delta)
        deltas.extend(witness_deltas)
    consequence_deltas = apply_crime_consequences(crime_state, crime_id)
    deltas.extend(consequence_deltas)
    return deltas


def build_crime_event(event_id: str, turn: int, state_deltas: list[StateDelta]) -> Event:
    return Event(
        event_id=event_id,
        turn=turn,
        actor_id="system",
        action_type="crime_consequence",
        result="success",
        state_deltas=state_deltas,
        visible_to_player=any(delta.metadata.get("visible_to_player") == "true" for delta in state_deltas),
    )


def _event_transfers_non_player_item_to_player(event: Event) -> bool:
    return any(
        delta.operation == StateDeltaOperation.SET
        and delta.path.startswith("objects.")
        and delta.path.endswith(".owner_id")
        and delta.value == "player"
        for delta in event.state_deltas
    )


def _transferred_item_id(event: Event) -> str | None:
    for delta in event.state_deltas:
        if delta.path.startswith("objects.") and delta.path.endswith(".owner_id") and delta.value == "player":
            return delta.path.split(".")[1]
    return event.target_id


def _event_has_metadata(event: Event, key: str, value: str) -> bool:
    return any(delta.metadata.get(key) == value for delta in event.state_deltas)


def _event_marks_target_dead(event: Event) -> bool:
    if event.target_id is None:
        return False
    return any(
        delta.path == f"npcs.{event.target_id}.condition"
        and str(delta.value) == "dead"
        for delta in event.state_deltas
    )


def _rumor_id(crime_id: str) -> str:
    return f"rumor_{crime_id}"
