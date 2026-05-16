from pathlib import Path

from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    GameState,
    LocationState,
    PlayerState,
    QuestStage,
    QuestState,
    QuestStatus,
    QuestTrigger,
    QuestTriggerAction,
    QuestTriggerType,
    QuestVisibility,
    WorldObjectState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.quests import (
    activate_quest,
    complete_objective,
    get_visible_quests,
    resolve_quest_triggers,
)
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.session_store import build_visible_state


def make_state() -> GameState:
    return GameState(
        world_id="quest-test",
        player=PlayerState(location_id="square"),
        locations={
            "square": LocationState(id="square", name="Square", exits={"east": "smithy"}),
            "smithy": LocationState(id="smithy", name="Smithy"),
        },
        objects={
            "sealed_letter": WorldObjectState(
                id="sealed_letter",
                location_id="square",
                portable=True,
                discovered_by=["player"],
            )
        },
        quests={
            "missing_tools": QuestState(
                id="missing_tools",
                title="Missing Tools",
                description="Find the tools.",
                initial_stage="ask",
                current_stage="ask",
                visibility=QuestVisibility.PUBLIC,
                status=QuestStatus.ACTIVE,
                known_to_player=True,
                stages={
                    "ask": QuestStage(
                        id="ask",
                        title="Ask Harlan",
                        objectives=["talk_harlan"],
                        next_stages=["find"],
                    ),
                    "find": QuestStage(
                        id="find",
                        title="Find the clue",
                        objectives=["take_letter"],
                    ),
                },
                triggers=[
                    QuestTrigger(
                        type=QuestTriggerType.NPC_TALKED,
                        id="harlan",
                        action=QuestTriggerAction.COMPLETE_OBJECTIVE,
                        objective_id="talk_harlan",
                        next_stage="find",
                    ),
                    QuestTrigger(
                        type=QuestTriggerType.ITEM_ACQUIRED,
                        id="sealed_letter",
                        action=QuestTriggerAction.COMPLETE_OBJECTIVE,
                        objective_id="take_letter",
                    ),
                ],
            ),
            "hidden_letter": QuestState(
                id="hidden_letter",
                title="Hidden Letter",
                initial_stage="find",
                current_stage="find",
                visibility=QuestVisibility.HIDDEN,
                status=QuestStatus.INACTIVE,
                known_to_player=False,
                stages={
                    "find": QuestStage(
                        id="find",
                        title="Find the letter",
                        objectives=["discover_letter"],
                    )
                },
                triggers=[
                    QuestTrigger(
                        type=QuestTriggerType.FACT_DISCOVERED,
                        id="letter_fact",
                        action=QuestTriggerAction.COMPLETE_OBJECTIVE,
                        objective_id="discover_letter",
                    )
                ],
            ),
        },
    )


def test_initial_quests_load_from_content_pack() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()

    assert "missing_tools" in state.quests
    assert state.quests["missing_tools"].current_stage == "ask_harlan"
    assert state.quests["missing_tools"].status == QuestStatus.ACTIVE


def test_hidden_quest_does_not_enter_visible_state() -> None:
    visible_state = build_visible_state(make_state())

    assert [quest.id for quest in visible_state.quests] == ["missing_tools"]


def test_fact_discovery_activates_hidden_quest() -> None:
    before_state = make_state()
    after_state = apply_delta(
        before_state,
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path="player_visible_facts",
            value="letter_fact",
        ),
    )
    result = ActionResult(success_level=SuccessLevel.SUCCESS, reason="Fact discovered")

    deltas = resolve_quest_triggers(
        before_state,
        after_state,
        PlayerIntent(
            action_type=PlayerActionType.SEARCH,
            raw_text="search",
            confidence=1.0,
            requires_clarification=False,
        ),
        result,
    )
    next_state = after_state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)

    assert next_state.quests["hidden_letter"].status == QuestStatus.ACTIVE
    assert next_state.quests["hidden_letter"].known_to_player is True
    assert "discover_letter" in next_state.quests["hidden_letter"].completed_objectives


def test_item_acquired_completes_objective() -> None:
    before_state = make_state()
    after_state = apply_delta(
        before_state,
        StateDelta(
            operation=StateDeltaOperation.SET,
            path="objects.sealed_letter.owner_id",
            value="player",
        ),
    )
    result = ActionResult(success_level=SuccessLevel.SUCCESS, reason="Item acquired")

    deltas = resolve_quest_triggers(
        before_state,
        after_state,
        PlayerIntent(
            action_type=PlayerActionType.USE_ITEM,
            target_id="sealed_letter",
            raw_text="take letter",
            confidence=1.0,
            requires_clarification=False,
        ),
        result,
    )
    next_state = after_state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)

    assert "take_letter" in next_state.quests["missing_tools"].completed_objectives


def test_talk_trigger_advances_stage() -> None:
    state = make_state()
    result = ActionResult(success_level=SuccessLevel.SUCCESS, reason="Talked to Harlan")

    deltas = resolve_quest_triggers(
        state,
        state,
        PlayerIntent(
            action_type=PlayerActionType.TALK,
            target_id="harlan",
            raw_text="talk to Harlan",
            confidence=1.0,
            requires_clarification=False,
        ),
        result,
    )
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)

    assert next_state.quests["missing_tools"].current_stage == "find"
    assert "talk_harlan" in next_state.quests["missing_tools"].completed_objectives


def test_quest_stage_updates_via_state_delta() -> None:
    state = make_state()
    deltas = activate_quest(state, "hidden_letter")
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)

    assert all(delta.path.startswith("quests.hidden_letter.") for delta in deltas)
    assert next_state.quests["hidden_letter"].status == QuestStatus.ACTIVE


def test_visible_quests_filters_to_known_active_quests() -> None:
    visible_quests = get_visible_quests(make_state())

    assert [quest.id for quest in visible_quests] == ["missing_tools"]


def test_save_load_preserves_quest_state(tmp_path: Path) -> None:
    repository = SQLiteSaveRepository(tmp_path / "quest_save.db")
    state = make_state()
    next_state = state
    for delta in complete_objective(state, "missing_tools", "talk_harlan"):
        next_state = apply_delta(next_state, delta)

    repository.create_save("save-quest", next_state)
    loaded = repository.load_save("save-quest")

    assert loaded.quests["missing_tools"].completed_objectives == {"talk_harlan"}
    assert loaded.quests["hidden_letter"].status == QuestStatus.INACTIVE


def test_visible_state_quests_include_stage_and_objectives() -> None:
    visible_state = build_visible_state(make_state())
    quest = visible_state.quests[0]

    assert quest.id == "missing_tools"
    assert quest.title == "Missing Tools"
    assert quest.current_stage == "ask"
    assert quest.objectives[0].id == "talk_harlan"
    assert quest.objectives[0].completed is False
