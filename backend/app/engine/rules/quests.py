from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    GameState,
    QuestState,
    QuestStatus,
    QuestTrigger,
    QuestTriggerAction,
    QuestTriggerType,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.llm.schemas import PlayerActionType, PlayerIntent


class QuestRuleError(ValueError):
    """Raised when quest state cannot be resolved safely."""


def activate_quest(state: GameState, quest_id: str) -> list[StateDelta]:
    quest = _get_quest(state, quest_id)
    if quest.status in {QuestStatus.ACTIVE, QuestStatus.COMPLETED, QuestStatus.FAILED}:
        return []
    return [
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"quests.{quest_id}.status",
            value=QuestStatus.ACTIVE,
            reason=f"Activate quest {quest_id}.",
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"quests.{quest_id}.known_to_player",
            value=True,
            reason=f"Reveal quest {quest_id} to the player.",
        ),
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"quests.{quest_id}.current_stage",
            value=quest.initial_stage,
            reason=f"Set quest {quest_id} to its initial stage.",
        ),
    ]


def advance_quest(state: GameState, quest_id: str, next_stage: str) -> list[StateDelta]:
    quest = _get_quest(state, quest_id)
    if next_stage not in quest.stages:
        raise QuestRuleError(f"Quest {quest_id} has no stage: {next_stage}")
    if quest.current_stage == next_stage and quest.status == QuestStatus.ACTIVE:
        return []
    deltas = []
    if quest.status != QuestStatus.ACTIVE:
        deltas.extend(activate_quest(state, quest_id))
    deltas.append(
        StateDelta(
            operation=StateDeltaOperation.SET,
            path=f"quests.{quest_id}.current_stage",
            value=next_stage,
            reason=f"Advance quest {quest_id} to stage {next_stage}.",
        )
    )
    return deltas


def complete_objective(state: GameState, quest_id: str, objective_id: str) -> list[StateDelta]:
    quest = _get_quest(state, quest_id)
    known_objectives = {
        objective for stage in quest.stages.values() for objective in stage.objectives
    }
    if objective_id not in known_objectives:
        raise QuestRuleError(f"Quest {quest_id} has no objective: {objective_id}")
    if objective_id in quest.completed_objectives:
        return []
    deltas = []
    if quest.status != QuestStatus.ACTIVE:
        deltas.extend(activate_quest(state, quest_id))
    deltas.append(
        StateDelta(
            operation=StateDeltaOperation.ADD,
            path=f"quests.{quest_id}.completed_objectives",
            value=objective_id,
            reason=f"Complete quest objective {objective_id}.",
        )
    )
    return deltas


def get_visible_quests(state: GameState) -> list[QuestState]:
    return [
        quest
        for quest in state.quests.values()
        if quest.known_to_player and quest.status != QuestStatus.INACTIVE
    ]


def resolve_quest_triggers(
    before_state: GameState,
    after_state: GameState,
    intent: PlayerIntent,
    action_result: ActionResult,
) -> list[StateDelta]:
    if action_result.success_level not in {SuccessLevel.SUCCESS, SuccessLevel.PARTIAL_SUCCESS}:
        return []

    deltas: list[StateDelta] = []
    working_state = after_state
    for quest in working_state.quests.values():
        for trigger in quest.triggers:
            if not _trigger_matches(trigger, before_state, after_state, intent, action_result):
                continue
            for delta in _deltas_for_trigger(working_state, quest.id, trigger):
                deltas.append(delta)
                working_state = apply_delta(working_state, delta)
    return deltas


def _deltas_for_trigger(
    state: GameState,
    quest_id: str,
    trigger: QuestTrigger,
) -> list[StateDelta]:
    if trigger.action == QuestTriggerAction.ACTIVATE:
        return activate_quest(state, quest_id)
    if trigger.action == QuestTriggerAction.ADVANCE:
        if not trigger.next_stage:
            raise QuestRuleError(f"Quest {quest_id} advance trigger requires next_stage")
        return advance_quest(state, quest_id, trigger.next_stage)
    if trigger.action == QuestTriggerAction.COMPLETE_OBJECTIVE:
        if not trigger.objective_id:
            raise QuestRuleError(
                f"Quest {quest_id} complete_objective trigger requires objective_id"
            )
        deltas = complete_objective(state, quest_id, trigger.objective_id)
        if trigger.next_stage:
            next_state = state
            for delta in deltas:
                next_state = apply_delta(next_state, delta)
            deltas.extend(advance_quest(next_state, quest_id, trigger.next_stage))
        return deltas
    raise QuestRuleError(f"Unsupported quest trigger action: {trigger.action}")


def _trigger_matches(
    trigger: QuestTrigger,
    before_state: GameState,
    after_state: GameState,
    intent: PlayerIntent,
    action_result: ActionResult,
) -> bool:
    if trigger.type == QuestTriggerType.FACT_DISCOVERED:
        return (
            trigger.id not in before_state.player_visible_facts
            and trigger.id in after_state.player_visible_facts
        )
    if trigger.type == QuestTriggerType.ITEM_ACQUIRED:
        before_item = before_state.objects.get(trigger.id)
        after_item = after_state.objects.get(trigger.id)
        return (
            before_item is not None
            and after_item is not None
            and before_item.owner_id != "player"
            and after_item.owner_id == "player"
        )
    if trigger.type == QuestTriggerType.NPC_TALKED:
        return intent.action_type == PlayerActionType.TALK and intent.target_id == trigger.id
    if trigger.type == QuestTriggerType.LOCATION_VISITED:
        return (
            before_state.player.location_id != trigger.id
            and after_state.player.location_id == trigger.id
        )
    raise QuestRuleError(f"Unsupported quest trigger type: {trigger.type}")


def _get_quest(state: GameState, quest_id: str) -> QuestState:
    quest = state.quests.get(quest_id)
    if quest is None:
        raise QuestRuleError(f"Quest does not exist: {quest_id}")
    return quest
