from abc import ABC, abstractmethod
from random import Random

from app.core.world_state import GameState
from app.engine.actions.schemas import ActionResult
from app.llm.schemas import PlayerActionType, PlayerIntent


class ActionHandler(ABC):
    action_type: PlayerActionType

    def can_handle(self, intent: PlayerIntent, state: GameState) -> bool:
        return intent.action_type == self.action_type

    @abstractmethod
    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        """Resolve intent into a structured result without mutating GameState."""

