from random import Random
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.event_log import Event, EventLog
from app.core.instrumentation import PerformanceSpan, get_performance_recorder, performance_logging_enabled
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import GameState
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.crime import build_crime_event, resolve_crime_from_event
from app.engine.rules.quests import resolve_quest_triggers
from app.engine.rules.world_tick import run_world_tick
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.llm.schemas import NarrativeResult, PlayerActionType, PlayerIntent
from app.roleplay.scene_moods import scene_mood_summary_for_prompt


class GameLoopResult(BaseModel):
    state: GameState
    intent: PlayerIntent
    action_result: ActionResult | None
    narrative: NarrativeResult
    event: Event | None = None
    system_events: list[Event] = Field(default_factory=list)


class GameLoop:
    def __init__(
        self,
        state: GameState,
        event_log: EventLog,
        intent_parser: IntentParser,
        action_dispatcher: ActionDispatcher,
        narrator: Narrator,
        rng: Random | None = None,
    ) -> None:
        self.state = state
        self.event_log = event_log
        self.intent_parser = intent_parser
        self.action_dispatcher = action_dispatcher
        self.narrator = narrator
        self.rng = rng or Random()

    def step(self, player_input: str, tone: str = "quiet") -> GameLoopResult:
        perf_span = PerformanceSpan("game_loop.step", tags={"world_id": self.state.world_id})
        with perf_span.stage("intent_parse"):
            intent = self.intent_parser.parse(player_input)

        if intent.requires_clarification:
            narrative = NarrativeResult(
                text=intent.clarification_question or "Please clarify your action.",
                suggested_actions=[],
                short_summary="Clarification requested.",
            )
            event = self._record_noop_event(
                intent=intent,
                player_input=player_input,
                result="clarification",
                narrative=narrative,
            )
            return GameLoopResult(
                state=self.state,
                intent=intent,
                action_result=None,
                narrative=narrative,
                event=event,
            )

        if intent.action_type == PlayerActionType.UNKNOWN:
            narrative = NarrativeResult(
                text="I could not understand that action.",
                suggested_actions=[],
                short_summary="Unknown action.",
            )
            event = self._record_noop_event(
                intent=intent,
                player_input=player_input,
                result="unknown",
                narrative=narrative,
            )
            return GameLoopResult(
                state=self.state,
                intent=intent,
                action_result=None,
                narrative=narrative,
                event=event,
            )

        original_state = self.state
        with perf_span.stage("action_resolve"):
            action_result = self.action_dispatcher.resolve(intent, original_state, self.rng)
        next_state = self.state
        action_deltas = action_result.state_deltas
        event_deltas = list(action_deltas)

        with perf_span.stage("apply_delta"):
            for delta in action_deltas:
                next_state = apply_delta(next_state, delta)

        if action_result.success_level in {SuccessLevel.SUCCESS, SuccessLevel.PARTIAL_SUCCESS}:
            with perf_span.stage("apply_delta"):
                quest_deltas = resolve_quest_triggers(
                    original_state,
                    next_state,
                    intent,
                    action_result,
                )
                for delta in quest_deltas:
                    next_state = apply_delta(next_state, delta)
            event_deltas.extend(quest_deltas)

            turn_delta = StateDelta(
                operation=StateDeltaOperation.INC,
                path="turn",
                value=1,
                reason="Successful player action advances the game turn.",
            )
            with perf_span.stage("apply_delta"):
                next_state = apply_delta(next_state, turn_delta)
            event_deltas.append(turn_delta)

        system_events: list[Event] = []
        if action_result.success_level in {SuccessLevel.SUCCESS, SuccessLevel.PARTIAL_SUCCESS}:
            with perf_span.stage("world_tick"):
                tick_result = run_world_tick(next_state, self.rng)
                if tick_result.state_deltas:
                    for delta in tick_result.state_deltas:
                        next_state = apply_delta(next_state, delta)
                if tick_result.event is not None:
                    system_events.append(tick_result.event)

        with perf_span.stage("narrator"):
            scene_mood_summary = scene_mood_summary_for_prompt(next_state, self.narrator.scene_mood_preset_id())
            if scene_mood_summary:
                narrative = self.narrator.render(
                    player_input=player_input,
                    action_result=action_result,
                    visible_facts=action_result.visible_facts,
                    current_location=next_state.player.location_id,
                    tone=tone,
                    scene_mood_summary=scene_mood_summary,
                )
            else:
                narrative = self.narrator.render(
                    player_input=player_input,
                    action_result=action_result,
                    visible_facts=action_result.visible_facts,
                    current_location=next_state.player.location_id,
                    tone=tone,
                )
        event = Event(
            event_id=str(uuid4()),
            turn=next_state.turn,
            actor_id=next_state.player.id,
            action_type=intent.action_type.value,
            target_id=intent.target_id,
            input_text=player_input,
            result=action_result.success_level.value,
            state_deltas=event_deltas,
            allow_empty_delta=not event_deltas,
            visible_to_player=True,
            narrative_text=narrative.text,
        )
        crime_deltas = resolve_crime_from_event(event, next_state)
        if crime_deltas:
            with perf_span.stage("apply_delta"):
                for delta in crime_deltas:
                    next_state = apply_delta(next_state, delta)
            system_events.append(
                build_crime_event(
                    event_id=str(uuid4()),
                    turn=next_state.turn,
                    state_deltas=crime_deltas,
                )
            )
        self.state = next_state
        self.event_log.append(event)
        for system_event in system_events:
            self.event_log.append(system_event)
        if performance_logging_enabled():
            get_performance_recorder().record(
                perf_span.finish(
                    tags={
                        "action_type": intent.action_type.value,
                        "result": action_result.success_level.value,
                    }
                )
            )

        return GameLoopResult(
            state=self.state,
            intent=intent,
            action_result=action_result,
            narrative=narrative,
            event=event,
            system_events=system_events,
        )

    def _record_noop_event(
        self,
        intent: PlayerIntent,
        player_input: str,
        result: str,
        narrative: NarrativeResult,
    ) -> Event:
        event = Event(
            event_id=str(uuid4()),
            turn=self.state.turn,
            actor_id=self.state.player.id,
            action_type=intent.action_type.value,
            target_id=intent.target_id,
            input_text=player_input,
            result=result,
            state_deltas=[],
            allow_empty_delta=True,
            visible_to_player=True,
            narrative_text=narrative.text,
        )
        self.event_log.append(event)
        return event
