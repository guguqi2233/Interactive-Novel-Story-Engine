from pydantic import BaseModel, Field

from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import GameState, NPCGoalState, NPCState


class KnowledgeRuleError(ValueError):
    """Raised when NPC knowledge rules cannot resolve a request."""


class NPCDialogueContext(BaseModel):
    npc_id: str
    location_id: str
    mood: str
    relationship_to_player: int
    knowledge: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)


def npc_knows(state: GameState, npc_id: str, fact_id: str) -> bool:
    npc = _get_npc(state, npc_id)
    return fact_id in npc.knowledge or fact_id in state.npc_knowledge.get(npc_id, set())


def add_npc_knowledge(state: GameState, npc_id: str, fact_id: str) -> GameState:
    _get_npc(state, npc_id)
    if npc_knows(state, npc_id, fact_id):
        return state
    return apply_delta(
        state,
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"npcs.{npc_id}.knowledge",
            value=fact_id,
            reason="NPC learned a new fact.",
        ),
    )


def get_npc_context_for_dialogue(state: GameState, npc_id: str) -> NPCDialogueContext:
    npc = _get_npc(state, npc_id)
    merged_knowledge = sorted(set(npc.knowledge) | state.npc_knowledge.get(npc_id, set()))
    public_or_known_facts = [
        fact_id
        for fact_id in merged_knowledge
        if _fact_allowed_for_dialogue(state, npc, fact_id)
    ]
    return NPCDialogueContext(
        npc_id=npc.id,
        location_id=npc.location_id,
        mood=npc.mood,
        relationship_to_player=npc.relationship_to_player,
        knowledge=public_or_known_facts,
        goals=_dialogue_goal_ids(npc),
    )


def _get_npc(state: GameState, npc_id: str) -> NPCState:
    npc = state.npcs.get(npc_id)
    if npc is None:
        raise KnowledgeRuleError(f"NPC not found: {npc_id}")
    return npc


def _fact_allowed_for_dialogue(state: GameState, npc: NPCState, fact_id: str) -> bool:
    if fact_id in state.player_visible_facts:
        return True

    fact = state.facts.get(fact_id)
    if fact is not None:
        if fact.public:
            return True
        return False

    return fact_id not in npc.secrets


def _dialogue_goal_ids(npc: NPCState) -> list[str]:
    return [
        goal.id if isinstance(goal, NPCGoalState) else goal
        for goal in npc.goals
    ]
