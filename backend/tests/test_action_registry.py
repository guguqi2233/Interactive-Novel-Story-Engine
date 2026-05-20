from random import Random
from typing import Any

from app.core.world_state import GameState, LocationState, NPCState
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.action_registry import ActionRegistry
from app.engine.actions.declarative import (
    DeclarativeActionDefinition,
    DeclarativeActionHandler,
    DeclarativeActionTargetSpec,
    DeclarativeOutcome,
    DeclarativeTargetKind,
)
from app.engine.actions.schemas import SuccessLevel
from app.llm.intent_parser import IntentParser
from app.llm.provider_base import LLMProvider
from app.llm.schemas import PlayerActionType, PlayerIntent


class CapturingProvider(LLMProvider):
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    def generate_text(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        self.messages = messages
        return "ok"

    def generate_json(self, messages: list[dict[str, str]], schema: type[Any], temperature: float = 0.2) -> Any:
        self.messages = messages
        return schema.model_validate(
            {
                "action_type": "unknown",
                "raw_text": "pray",
                "confidence": 0.6,
                "requires_clarification": False,
            }
        )


def _state(*, npc_hidden: bool = False) -> GameState:
    return GameState(
        world_id="action-registry-test",
        locations={"shrine": LocationState(id="shrine", name="Shrine")},
        player={"location_id": "shrine"},
        npcs={
            "oracle": NPCState(
                id="oracle",
                name="Oracle",
                location_id="shrine",
                hidden=npc_hidden,
                visible=True,
            )
        },
    )


def _pray_definition(alias: str = "pray", *, target_kind: DeclarativeTargetKind = DeclarativeTargetKind.CURRENT_LOCATION) -> DeclarativeActionDefinition:
    return DeclarativeActionDefinition(
        id="module.pray",
        label="Pray",
        aliases=[alias],
        category="general",
        target_specs=[DeclarativeActionTargetSpec(kind=target_kind, required=False)],
        outcomes={
            SuccessLevel.SUCCESS: DeclarativeOutcome(
                success_level=SuccessLevel.SUCCESS,
                reason="Prayer resolved.",
            )
        },
        event_type="module.pray",
    )


def _intent(raw_text: str = "pray") -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.UNKNOWN,
        raw_text=raw_text,
        confidence=1.0,
        requires_clarification=False,
    )


def test_core_and_module_actions_can_register() -> None:
    registry = ActionRegistry()
    registry.register_module_action(_pray_definition(), module_id="faith")

    actions = registry.list_available_actions()
    ids = {action.id for action in actions}

    assert "observe" in ids
    assert "module.pray" in ids
    assert registry.get_action_definition("module.pray").module_id == "faith"


def test_alias_conflict_is_detected() -> None:
    registry = ActionRegistry(include_core=False)
    registry.register_module_action(_pray_definition("pray"), module_id="faith")
    registry.register_module_action(_pray_definition("pray").model_copy(update={"id": "module.kneel", "label": "Kneel"}), module_id="faith")

    conflicts = registry.detect_alias_conflicts()

    assert conflicts
    assert conflicts[0].alias == "pray"
    assert conflicts[0].severity == "warning"


def test_disabled_module_action_cannot_be_called() -> None:
    registry = ActionRegistry(include_core=False)
    registry.register_module_action(_pray_definition(), module_id="faith", enabled=False)
    dispatcher = ActionDispatcher(action_registry=registry)

    result = dispatcher.resolve(_intent(), _state(), Random(1))

    assert result.success_level == SuccessLevel.INVALID
    assert "No enabled registered action" in result.reason


def test_enabled_module_action_can_be_called_through_registry_dispatcher() -> None:
    registry = ActionRegistry(include_core=False)
    definition = _pray_definition()
    registry.register_module_action(definition, module_id="faith", handler=DeclarativeActionHandler(definition))
    dispatcher = ActionDispatcher(action_registry=registry)

    result = dispatcher.resolve(_intent(), _state(), Random(1))

    assert result.success_level == SuccessLevel.SUCCESS


def test_intent_parser_action_list_includes_enabled_module_action() -> None:
    registry = ActionRegistry(include_core=False)
    registry.register_module_action(_pray_definition(), module_id="faith")
    provider = CapturingProvider()

    _ = IntentParser(provider, available_action_aliases=registry.available_action_aliases()).parse("pray")

    system_prompt = provider.messages[0]["content"]
    assert "Enabled local action aliases" in system_prompt
    assert "pray" in system_prompt


def test_suggested_actions_only_show_visible_affordance() -> None:
    registry = ActionRegistry(include_core=False)
    registry.register_module_action(
        _pray_definition("consult oracle", target_kind=DeclarativeTargetKind.NPC),
        module_id="faith",
    )

    visible = registry.suggested_actions_for_visible_affordances(_state(npc_hidden=False))
    hidden = registry.suggested_actions_for_visible_affordances(_state(npc_hidden=True))

    assert "consult oracle" in visible
    assert "consult oracle" not in hidden
