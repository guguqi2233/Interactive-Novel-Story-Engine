from collections.abc import Callable
from random import Random
from uuid import uuid4

from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.core.world_state import GameState
from app.api import VisibleStateResponse
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.visibility import get_visible_facts
from app.llm.intent_parser import IntentParser
from app.llm.mock_provider import MockLLMProvider
from app.llm.narrator import Narrator
from app.llm.provider_base import LLMProvider

ProviderFactory = Callable[[], LLMProvider]


class InMemorySessionStore:
    def __init__(
        self,
        provider_factory: ProviderFactory | None = None,
        worlds_root: str = "worlds",
        default_world_id: str = "mist_valley",
    ) -> None:
        self._sessions: dict[str, GameLoop] = {}
        self._provider_factory = provider_factory or MockLLMProvider
        self._world_loader = WorldLoader(worlds_root)
        self._default_world_id = default_world_id

    def create_session(self) -> tuple[str, GameLoop]:
        session_id = str(uuid4())
        provider = self._provider_factory()
        game_loop = GameLoop(
            state=create_initial_state(self._world_loader, self._default_world_id),
            event_log=EventLog(),
            intent_parser=IntentParser(provider),
            action_dispatcher=ActionDispatcher(),
            narrator=Narrator(provider),
            rng=Random(),
        )
        self._sessions[session_id] = game_loop
        return session_id, game_loop

    def get_session(self, session_id: str) -> GameLoop | None:
        return self._sessions.get(session_id)


def create_initial_state(world_loader: WorldLoader | None = None, world_id: str = "mist_valley") -> GameState:
    loader = world_loader or WorldLoader("worlds")
    return loader.load(world_id).to_game_state()


def build_visible_state(state: GameState) -> VisibleStateResponse:
    location = state.locations.get(state.player.location_id)
    return VisibleStateResponse(
        world_id=state.world_id,
        location_id=state.player.location_id,
        location_name=location.name if location else state.player.location_id,
        visible_facts=get_visible_facts(state, state.player.id, state.player.location_id),
    )
