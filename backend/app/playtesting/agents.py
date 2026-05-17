from abc import ABC, abstractmethod
from random import Random

from app.api import VisibleStateResponse


class PlaytestingAgent(ABC):
    """Base class for agents that choose player input only from visible data."""

    strategy_name: str

    @abstractmethod
    def choose_action(self, visible_state: VisibleStateResponse, rng: Random) -> str:
        """Return player input text for the next GameLoop step."""


class RandomValidActionAgent(PlaytestingAgent):
    strategy_name = "random_valid_action_agent"

    def choose_action(self, visible_state: VisibleStateResponse, rng: Random) -> str:
        return rng.choice(_visible_action_pool(visible_state))


class ExploreAgent(PlaytestingAgent):
    strategy_name = "explore_agent"

    def choose_action(self, visible_state: VisibleStateResponse, rng: Random) -> str:
        exits = sorted(set(visible_state.location.exits.values()))
        if exits:
            return f"move {rng.choice(exits)}"
        return rng.choice(["observe", "search", "wait 30"])


class QuestFollowingAgent(PlaytestingAgent):
    strategy_name = "quest_following_agent"

    def choose_action(self, visible_state: VisibleStateResponse, rng: Random) -> str:
        for quest in visible_state.quests:
            text = " ".join([quest.id, quest.current_stage, quest.stage_title]).lower()
            if "talk" in text and visible_state.visible_npcs:
                return f"talk {visible_state.visible_npcs[0].id}"
            if "search" in text or "fact" in text:
                return "search"
        return RandomValidActionAgent().choose_action(visible_state, rng)


class StressAgent(PlaytestingAgent):
    strategy_name = "stress_agent"

    def choose_action(self, visible_state: VisibleStateResponse, rng: Random) -> str:
        pool = _visible_action_pool(visible_state)
        pool.extend(
            [
                "lockpick missing_target",
                "sneak missing_target",
                "attack missing_target",
                "buy missing_item",
                "sell missing_item",
                "use missing_item",
                "wait 0",
            ]
        )
        return rng.choice(pool)


def create_playtesting_agent(strategy_name: str) -> PlaytestingAgent:
    strategies: dict[str, type[PlaytestingAgent]] = {
        RandomValidActionAgent.strategy_name: RandomValidActionAgent,
        ExploreAgent.strategy_name: ExploreAgent,
        QuestFollowingAgent.strategy_name: QuestFollowingAgent,
        StressAgent.strategy_name: StressAgent,
    }
    try:
        return strategies[strategy_name]()
    except KeyError as exc:
        raise ValueError(f"Unknown playtesting strategy: {strategy_name}") from exc


def _visible_action_pool(visible_state: VisibleStateResponse) -> list[str]:
    actions = ["observe", "search", "wait 30"]
    for target_id in sorted(set(visible_state.location.exits.values())):
        actions.append(f"move {target_id}")
    for npc in visible_state.visible_npcs:
        actions.append(f"talk {npc.id}")
        actions.append(f"attack {npc.id}")
    for item in visible_state.visible_objects:
        actions.append(f"use {item.id}")
        actions.append(f"lockpick {item.id}")
    for item in visible_state.inventory:
        actions.append(f"use {item.id}")
        actions.append(f"sell {item.id}")
    return actions
