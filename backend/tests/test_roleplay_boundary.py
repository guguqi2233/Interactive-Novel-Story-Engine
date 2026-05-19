from app.core.world_state import FactState, FactVisibility, GameState, NPCState
from app.llm.memory_store import MemoryRecord, MemoryVisibility
from app.roleplay.boundary import (
    RoleplayBoundaryConcept,
    RoleplayContextPolicy,
    RoleplayContextScope,
    RoleplayOutputCandidate,
)


def _state() -> GameState:
    return GameState(
        world_id="rp-test",
        facts={
            "public_square": FactState(
                id="public_square",
                text="The square is public.",
                visibility=FactVisibility.PUBLIC,
                public=True,
            ),
            "hidden_heir": FactState(
                id="hidden_heir",
                text="Mira is the hidden heir.",
                visibility=FactVisibility.HIDDEN,
            ),
            "known_secret": FactState(
                id="known_secret",
                text="Harlan knows the bell code.",
                visibility=FactVisibility.HIDDEN,
            ),
        },
        player_visible_facts={"public_square"},
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                knowledge=["known_secret"],
                secrets=["hidden_heir"],
            )
        },
    )


def test_hidden_fact_not_allowed_in_player_rp_context() -> None:
    context = RoleplayContextPolicy().build_context(
        _state(),
        scope=RoleplayContextScope.PLAYER,
        fact_ids=["public_square", "hidden_heir"],
    )

    assert [entry.id for entry in context.entries] == ["public_square"]
    assert context.excluded[0].id == "hidden_heir"
    assert context.excluded[0].reason == "hidden_fact_not_allowed"


def test_debug_memory_not_allowed_in_rp_context() -> None:
    context = RoleplayContextPolicy().build_context(
        _state(),
        scope=RoleplayContextScope.NARRATOR,
        memories=[
            MemoryRecord(
                id="debug-memory",
                content="debug-only delta trail",
                visibility=MemoryVisibility.DEBUG_ONLY,
            )
        ],
    )

    assert context.entries == []
    assert context.excluded[0].id == "debug-memory"
    assert context.excluded[0].reason == "debug_memory_not_allowed"


def test_rp_flavor_can_enter_rp_context() -> None:
    context = RoleplayContextPolicy().build_context(
        _state(),
        scope=RoleplayContextScope.NARRATOR,
        rp_flavor=["Use clipped, nervous phrasing."],
    )

    assert context.entries[0].concept == RoleplayBoundaryConcept.RP_FLAVOR
    assert context.entries[0].content == "Use clipped, nervous phrasing."
    assert context.excluded == []


def test_emotional_expression_does_not_modify_game_state() -> None:
    state = _state()
    before = state.model_dump(mode="json")

    context = RoleplayContextPolicy().build_context(
        state,
        scope=RoleplayContextScope.NPC_DIALOGUE,
        npc_id="harlan",
        emotional_expression=["Harlan sounds guarded but not hostile."],
    )

    assert context.entries[0].concept == RoleplayBoundaryConcept.EMOTIONAL_EXPRESSION
    assert state.model_dump(mode="json") == before


def test_prohibited_fact_creation_is_marked_by_consistency_checker() -> None:
    result = RoleplayContextPolicy().check_output(
        RoleplayOutputCandidate(
            text="Mira hands you the royal key and the quest is now complete.",
            proposed_fact_creations=["royal_key_created", "quest_completed"],
        )
    )

    assert result.ok is False
    assert [issue.code for issue in result.issues] == [
        "prohibited_fact_creation",
        "prohibited_fact_creation",
    ]


def test_npc_known_fact_allowed_only_for_that_npc() -> None:
    context = RoleplayContextPolicy().build_context(
        _state(),
        scope=RoleplayContextScope.NPC_DIALOGUE,
        npc_id="harlan",
        fact_ids=["known_secret", "hidden_heir"],
    )

    assert [entry.id for entry in context.entries] == ["known_secret"]
    assert context.entries[0].concept == RoleplayBoundaryConcept.NPC_KNOWN_FACT
    assert context.excluded[0].id == "hidden_heir"
    assert context.excluded[0].reason == "npc_unknown_fact"

