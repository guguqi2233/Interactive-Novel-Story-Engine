from random import Random

from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import FactVisibility, GameState
from app.engine.actions.base import ActionHandler
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.inventory import has_item
from app.engine.rules.time import make_time_delta
from app.engine.rules.visibility import get_visible_facts
from app.llm.schemas import PlayerActionType, PlayerIntent


class SearchActionHandler(ActionHandler):
    action_type = PlayerActionType.SEARCH

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        scope = _resolve_search_scope(intent, state)
        if scope is None:
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason="Search target is not present or reachable.",
            )

        object_deltas = _discoverable_object_deltas(state, scope)
        fact_deltas = _discoverable_fact_deltas(state, scope)
        discovery_deltas = [*object_deltas, *fact_deltas]
        time_delta = make_time_delta(state, 10)

        if discovery_deltas:
            discovered_ids = _discovered_ids(discovery_deltas)
            visible_facts = [
                *_currently_visible_facts(state),
                *discovered_ids,
            ]
            return ActionResult(
                success_level=SuccessLevel.SUCCESS,
                reason="Search revealed something previously unnoticed.",
                state_deltas=[time_delta, *discovery_deltas],
                visible_facts=_dedupe(visible_facts),
            )

        return ActionResult(
            success_level=SuccessLevel.FAILURE,
            reason="Search found no obvious new clues.",
            state_deltas=[time_delta],
            visible_facts=get_visible_facts(state, state.player.id, state.player.location_id),
        )


def _resolve_search_scope(intent: PlayerIntent, state: GameState) -> dict[str, str] | None:
    location_id = state.player.location_id
    target_id = intent.target_id
    if target_id is None or target_id == location_id:
        if location_id not in state.locations:
            return None
        return {"kind": "location", "id": location_id}

    target_object = state.objects.get(target_id)
    if target_object is not None:
        if target_object.location_id != location_id and not has_item(state, state.player.id, target_id):
            return None
        if target_object.hidden and state.player.id not in target_object.discovered_by:
            return None
        return {"kind": "object", "id": target_id}

    target_npc = state.npcs.get(target_id)
    if target_npc is not None:
        if target_npc.location_id != location_id:
            return None
        if target_npc.hidden and state.player.id not in target_npc.discovered_by:
            return None
        return {"kind": "npc", "id": target_id}

    return None


def _discoverable_object_deltas(state: GameState, scope: dict[str, str]) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    for world_object in state.objects.values():
        if state.player.id in world_object.discovered_by:
            continue
        if not world_object.discoverable:
            continue
        if not _object_in_scope(world_object.location_id, scope, state):
            continue
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path=f"objects.{world_object.id}.discovered_by",
                value=state.player.id,
                reason="Player discovered object by searching.",
                metadata={"source": "search", "discovered_object_id": world_object.id},
            )
        )
    return deltas


def _discoverable_fact_deltas(state: GameState, scope: dict[str, str]) -> list[StateDelta]:
    deltas: list[StateDelta] = []
    for fact in state.facts.values():
        if fact.id in state.player_visible_facts:
            continue
        if fact.visibility != FactVisibility.DISCOVERABLE:
            continue
        if not _fact_in_scope(fact.tags, scope):
            continue
        deltas.append(
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path="player_visible_facts",
                value=fact.id,
                reason="Player discovered fact by searching.",
                metadata={"source": "search", "discovered_fact_id": fact.id},
            )
        )
    return deltas


def _object_in_scope(object_location_id: str, scope: dict[str, str], state: GameState) -> bool:
    if scope["kind"] == "location":
        return object_location_id == scope["id"]
    if scope["kind"] == "object":
        return object_location_id == scope["id"]
    if scope["kind"] == "npc":
        npc = state.npcs.get(scope["id"])
        return npc is not None and object_location_id == npc.location_id
    return False


def _fact_in_scope(tags: list[str], scope: dict[str, str]) -> bool:
    return f"{scope['kind']}:{scope['id']}" in tags


def _currently_visible_facts(state: GameState) -> list[str]:
    return get_visible_facts(state, state.player.id, state.player.location_id)


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _discovered_ids(deltas: list[StateDelta]) -> list[str]:
    discovered: list[str] = []
    for delta in deltas:
        object_id = delta.metadata.get("discovered_object_id")
        fact_id = delta.metadata.get("discovered_fact_id")
        if object_id:
            discovered.append(object_id)
        if fact_id:
            discovered.append(fact_id)
    return discovered
