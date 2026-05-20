from random import Random

from app.core.world_state import GameState
from app.engine.action_registry import ActionRegistry
from app.engine.actions.base import ActionHandler
from app.engine.actions.basic import default_action_handlers
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.llm.schemas import PlayerIntent


class ActionDispatcher:
    def __init__(self, handlers: list[ActionHandler] | None = None, action_registry: ActionRegistry | None = None) -> None:
        self._handlers = handlers or default_action_handlers()
        self._action_registry = action_registry

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random | None = None) -> ActionResult:
        active_rng = rng or Random()
        if self._action_registry is not None:
            handler = self._action_registry.get_handler_for_intent(intent, state)
            if handler is not None:
                return handler.resolve(intent, state, active_rng)
            return ActionResult(
                success_level=SuccessLevel.INVALID,
                reason=f"No enabled registered action can handle: {intent.raw_text}",
            )
        for handler in self._handlers:
            if handler.can_handle(intent, state):
                return handler.resolve(intent, state, active_rng)

        return ActionResult(
            success_level=SuccessLevel.INVALID,
            reason=f"No handler registered for action_type: {intent.action_type}",
        )

