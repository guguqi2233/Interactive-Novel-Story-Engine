from app.core.world_state import GameState


def get_visible_facts(state: GameState, actor_id: str, location_id: str) -> list[str]:
    location = state.locations.get(location_id)
    if location is None:
        return []

    visible_facts = [location.id]

    for object_id in location.visible_objects:
        world_object = state.objects.get(object_id)
        if world_object is None:
            visible_facts.append(object_id)
            continue
        if _object_visible_to_actor(world_object.location_id, location_id, world_object.visible):
            if not world_object.hidden or actor_id in world_object.discovered_by:
                visible_facts.append(world_object.id)

    for world_object in state.objects.values():
        if world_object.id in location.visible_objects:
            continue
        if not _object_visible_to_actor(world_object.location_id, location_id, world_object.visible):
            continue
        if world_object.hidden and actor_id not in world_object.discovered_by:
            continue
        visible_facts.append(world_object.id)

    for npc in state.npcs.values():
        if npc.location_id == location_id:
            visible_facts.append(npc.id)

    for fact_id in sorted(state.player_visible_facts):
        if fact_id not in visible_facts:
            visible_facts.append(fact_id)

    return visible_facts


def _object_visible_to_actor(object_location_id: str, actor_location_id: str, visible: bool) -> bool:
    return visible and object_location_id == actor_location_id

