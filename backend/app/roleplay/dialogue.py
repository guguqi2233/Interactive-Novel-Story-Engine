from __future__ import annotations

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.event_log import Event, EventLog
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import GameState, RelationshipState
from app.engine.actions.schemas import ActionResult
from app.engine.rules.knowledge import get_npc_context_for_dialogue
from app.engine.rules.life_state import can_talk
from app.engine.rules.emotions import emotion_from_event
from app.engine.rules.relationship_tone import get_tone_for_dialogue, tone_summary_for_prompt
from app.engine.rules.relationships import change_affinity, change_trust, get_relationship, relationship_id
from app.llm.context_builder import RPMemoryContext, RPMemoryContextBuilder, build_npc_dialogue_profile_context
from app.llm.memory_store import MemoryStore
from app.llm.prompt_profiles import PromptProfile
from app.roleplay.boundary import (
    RoleplayContextPolicy,
    RoleplayContextScope,
    RoleplayOutputCandidate,
    RoleplayOutputCheckResult,
)
from app.roleplay.output_consistency import RPConsistencyReport, RPOutputConsistencyChecker
from app.roleplay.scene_moods import scene_mood_summary_for_prompt


class DialogueMode(StrEnum):
    FOCUSED = "focused"
    CASUAL = "casual"
    INTERROGATION = "interrogation"
    NEGOTIATION = "negotiation"
    INTIMATE = "intimate"
    CONFLICT = "conflict"


class DialogueSessionStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class DialogueSession(BaseModel):
    session_id: str
    save_id: str | None = None
    game_session_id: str | None = None
    participant_ids: list[str] = Field(default_factory=list)
    focus_npc_id: str
    started_turn: int
    last_turn: int
    dialogue_mode: DialogueMode = DialogueMode.FOCUSED
    active_topics: list[str] = Field(default_factory=list)
    scene_mood_preset_id: str | None = None
    safe_context_summary: str = ""
    status: DialogueSessionStatus = DialogueSessionStatus.ACTIVE


class DialogueContext(BaseModel):
    session: DialogueSession
    npc_known_facts: list[str] = Field(default_factory=list)
    emotional_summary: str = ""
    relationship_tone_summary: str = ""
    scene_mood_summary: str = ""
    example_dialogue_summaries: list[str] = Field(default_factory=list)
    rp_memory_summaries: list[str] = Field(default_factory=list)
    rp_prompt_style_summary: str = ""
    safe_context_summary: str = ""


class DialogueIntent(BaseModel):
    raw_text: str
    intent_type: str = "continue_dialogue"
    target_id: str | None = None
    requested_end: bool = False


class DialogueModeResult(BaseModel):
    session: DialogueSession
    context: DialogueContext
    event: Event | None = None
    state: GameState
    output_check: RoleplayOutputCheckResult


class GroupDialogueSceneStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class GroupDialogueScene(BaseModel):
    scene_id: str
    game_session_id: str | None = None
    participant_ids: list[str] = Field(default_factory=list)
    location_id: str
    active_speaker_id: str
    turn_order: list[str] = Field(default_factory=list)
    scene_topic: str = ""
    scene_mood: str = "neutral"
    scene_mood_preset_id: str | None = None
    visibility_scope: str = "player_visible"
    status: GroupDialogueSceneStatus = GroupDialogueSceneStatus.ACTIVE


class GroupParticipantContext(BaseModel):
    npc_id: str
    npc_known_facts: list[str] = Field(default_factory=list)
    emotional_summary: str = ""
    relationship_tone_summary: str = ""
    scene_mood_summary: str = ""
    example_dialogue_summaries: list[str] = Field(default_factory=list)
    rp_prompt_style_summary: str = ""
    safe_context_summary: str = ""


class DialogueManager:
    """Read-only/session-layer manager for continuous RP dialogue.

    Dialogue mode is intentionally not a world judge. It validates NPC
    availability, builds filtered context, and applies only deterministic
    rule-produced deltas for tiny social effects.
    """

    def __init__(
        self,
        policy: RoleplayContextPolicy | None = None,
        memory_store: MemoryStore | None = None,
        prompt_profile: PromptProfile | None = None,
    ) -> None:
        self._sessions: dict[str, DialogueSession] = {}
        self._policy = policy or RoleplayContextPolicy()
        self._memory_store = memory_store
        self._prompt_profile = prompt_profile
        self._output_checker = RPOutputConsistencyChecker()

    def set_prompt_profile(self, prompt_profile: PromptProfile | None) -> None:
        self._prompt_profile = prompt_profile

    def start_dialogue(
        self,
        state: GameState,
        *,
        game_session_id: str | None,
        focus_npc_id: str,
        dialogue_mode: DialogueMode = DialogueMode.FOCUSED,
        active_topics: list[str] | None = None,
        scene_mood_preset_id: str | None = None,
        save_id: str | None = None,
        event_log: EventLog | None = None,
    ) -> DialogueSession:
        self._validate_npc_available(state, focus_npc_id)
        context = self.build_dialogue_context(
            state,
            focus_npc_id=focus_npc_id,
            session=None,
            dialogue_mode=dialogue_mode,
            active_topics=active_topics or [],
            scene_mood_preset_id=scene_mood_preset_id,
        )
        session = DialogueSession(
            session_id=str(uuid4()),
            save_id=save_id,
            game_session_id=game_session_id,
            participant_ids=["player", focus_npc_id],
            focus_npc_id=focus_npc_id,
            started_turn=state.turn,
            last_turn=state.turn,
            dialogue_mode=dialogue_mode,
            active_topics=list(active_topics or []),
            scene_mood_preset_id=scene_mood_preset_id,
            safe_context_summary=context.safe_context_summary,
        )
        self._sessions[session.session_id] = session
        if event_log is not None:
            event_log.append(
                Event(
                    event_id=str(uuid4()),
                    turn=state.turn,
                    actor_id="player",
                    action_type="dialogue_start",
                    target_id=focus_npc_id,
                    result="success",
                    state_deltas=[],
                    allow_empty_delta=True,
                    visible_to_player=True,
                    narrative_text="Dialogue started.",
                )
            )
        return session

    def continue_dialogue(
        self,
        state: GameState,
        event_log: EventLog,
        *,
        dialogue_session_id: str,
        player_input: str,
    ) -> DialogueModeResult:
        session = self._require_active_session(dialogue_session_id)
        self._validate_npc_available(state, session.focus_npc_id)
        intent = self._parse_dialogue_intent(player_input, session.focus_npc_id)
        if intent.requested_end:
            ended = self.end_dialogue(dialogue_session_id, state.turn)
            context = self.build_dialogue_context(state, focus_npc_id=ended.focus_npc_id, session=ended)
            event = Event(
                event_id=str(uuid4()),
                turn=state.turn,
                actor_id="player",
                action_type="dialogue_end",
                target_id=ended.focus_npc_id,
                input_text=player_input,
                result="success",
                state_deltas=[],
                allow_empty_delta=True,
                visible_to_player=True,
                narrative_text="Dialogue ended.",
            )
            event_log.append(event)
            return DialogueModeResult(
                session=ended,
                context=context,
                event=event,
                state=state,
                output_check=self.validate_dialogue_output(RoleplayOutputCandidate(text="")),
            )

        deltas = self._rule_deltas_from_dialogue_input(state, session, intent)
        next_state = state
        for delta in deltas:
            next_state = apply_delta(next_state, delta)
        session.last_turn = next_state.turn
        session.safe_context_summary = self.build_dialogue_context(next_state, focus_npc_id=session.focus_npc_id, session=session).safe_context_summary
        self._sessions[session.session_id] = session
        event = Event(
            event_id=str(uuid4()),
            turn=next_state.turn,
            actor_id="player",
            action_type="dialogue",
            target_id=session.focus_npc_id,
            input_text=player_input,
            result="success",
            state_deltas=deltas,
            allow_empty_delta=not deltas,
            visible_to_player=True,
            narrative_text=None,
        )
        event_log.append(event)
        return DialogueModeResult(
            session=session,
            context=self.build_dialogue_context(next_state, focus_npc_id=session.focus_npc_id, session=session),
            event=event,
            state=next_state,
            output_check=self.validate_dialogue_output(RoleplayOutputCandidate(text=player_input)),
        )

    def end_dialogue(self, dialogue_session_id: str, turn: int) -> DialogueSession:
        session = self._sessions.get(dialogue_session_id)
        if session is None:
            raise ValueError(f"Unknown dialogue session: {dialogue_session_id}")
        session.status = DialogueSessionStatus.ENDED
        session.last_turn = turn
        self._sessions[dialogue_session_id] = session
        return session

    def get_session(self, dialogue_session_id: str) -> DialogueSession | None:
        return self._sessions.get(dialogue_session_id)

    def build_dialogue_context(
        self,
        state: GameState,
        *,
        focus_npc_id: str,
        session: DialogueSession | None = None,
        dialogue_mode: DialogueMode | None = None,
        active_topics: list[str] | None = None,
        scene_mood_preset_id: str | None = None,
    ) -> DialogueContext:
        knowledge_context = get_npc_context_for_dialogue(state, focus_npc_id)
        profile_context = build_npc_dialogue_profile_context(state, focus_npc_id)
        rp_context = self._policy.build_context(
            state,
            scope=RoleplayContextScope.NPC_DIALOGUE,
            actor_id=focus_npc_id,
            npc_id=focus_npc_id,
            fact_ids=knowledge_context.knowledge,
            rp_flavor=[profile_context.public_persona] if profile_context.public_persona else [],
            emotional_expression=[profile_context.emotional_tone],
        )
        allowed_fact_ids = [entry.id for entry in rp_context.entries if entry.source == "fact"]
        mode_value = (dialogue_mode or (session.dialogue_mode if session else DialogueMode.FOCUSED)).value
        topics = active_topics if active_topics is not None else (session.active_topics if session else [])
        mood_preset_id = scene_mood_preset_id if scene_mood_preset_id is not None else (session.scene_mood_preset_id if session else None)
        mood_summary = scene_mood_summary_for_prompt(state, mood_preset_id)
        relationship_tone = get_tone_for_dialogue(state, focus_npc_id, "player")
        rp_memory_context = self._build_rp_memory_context(
            state=state,
            session=session,
            focus_npc_id=focus_npc_id,
            allowed_fact_ids=allowed_fact_ids,
            relationship_tone=relationship_tone,
        )
        rp_memory_summaries = _rp_memory_summaries(rp_memory_context)
        rp_style_summary = _rp_prompt_style_summary(self._prompt_profile)
        safe_summary = (
            f"npc={focus_npc_id}; mode={mode_value}; topics={','.join(sorted(set(topics)))}; "
            f"emotion={profile_context.emotional_tone}/{profile_context.emotion_intensity_band}; "
            f"tone={profile_context.relationship_tone_summary}; mood={mood_summary or 'default'}; "
            f"known_fact_count={len(allowed_fact_ids)}; "
            f"example_dialogue_count={len(profile_context.example_dialogue_summaries)}; "
            f"rp_memory_count={len(rp_memory_summaries)}; "
            f"rp_style={self._prompt_profile.rp_profile.id if self._prompt_profile else 'default'}"
        )
        context_session = session or DialogueSession(
            session_id="preview",
            participant_ids=["player", focus_npc_id],
            focus_npc_id=focus_npc_id,
            started_turn=state.turn,
            last_turn=state.turn,
            dialogue_mode=dialogue_mode or DialogueMode.FOCUSED,
            active_topics=list(active_topics or []),
            scene_mood_preset_id=mood_preset_id,
            safe_context_summary=safe_summary,
        )
        return DialogueContext(
            session=context_session,
            npc_known_facts=allowed_fact_ids,
            emotional_summary=f"{profile_context.emotional_tone}:{profile_context.emotion_intensity_band}",
            relationship_tone_summary=tone_summary_for_prompt(relationship_tone),
            scene_mood_summary=mood_summary,
            example_dialogue_summaries=profile_context.example_dialogue_summaries,
            rp_memory_summaries=rp_memory_summaries,
            rp_prompt_style_summary=rp_style_summary,
            safe_context_summary=safe_summary,
        )

    def validate_dialogue_output(self, candidate: RoleplayOutputCandidate) -> RoleplayOutputCheckResult:
        return self._policy.check_output(candidate)

    def check_dialogue_output_consistency(
        self,
        *,
        generated_text: str,
        state: GameState,
        context: DialogueContext,
        action_result: ActionResult | None = None,
        forbidden_hidden_terms: list[str] | None = None,
        forbidden_hidden_ids: list[str] | None = None,
        allowed_flavor_terms: list[str] | None = None,
        candidate: RoleplayOutputCandidate | None = None,
    ) -> RPConsistencyReport:
        return self._output_checker.check(
            generated_text=generated_text,
            state=state,
            dialogue_context=context,
            action_result=action_result,
            visible_facts=state.player_visible_facts,
            npc_known_facts=context.npc_known_facts,
            forbidden_hidden_terms=forbidden_hidden_terms or [],
            forbidden_hidden_ids=forbidden_hidden_ids or [],
            allowed_flavor_terms=allowed_flavor_terms or [],
            speaker_npc_id=context.session.focus_npc_id,
            candidate=candidate,
        )

    def _parse_dialogue_intent(self, player_input: str, target_id: str) -> DialogueIntent:
        lowered = player_input.strip().lower()
        return DialogueIntent(
            raw_text=player_input,
            target_id=target_id,
            requested_end=lowered in {"bye", "goodbye", "end dialogue", "exit dialogue", "leave"},
        )

    def _rule_deltas_from_dialogue_input(
        self,
        state: GameState,
        session: DialogueSession,
        intent: DialogueIntent,
    ) -> list[StateDelta]:
        relationship = get_relationship(state, session.focus_npc_id, "player")
        if relationship is None:
            return [
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"relationships.{relationship_id(session.focus_npc_id, 'player')}",
                    value=RelationshipState(
                        id=relationship_id(session.focus_npc_id, "player"),
                        source_id=session.focus_npc_id,
                        target_id="player",
                        relation_type="general",
                        trust=1 if _sounds_kind(intent.raw_text) else 0,
                        affinity=1 if _sounds_kind(intent.raw_text) else 0,
                        fear=1 if _sounds_threatening(intent.raw_text) else 0,
                        known_by_player=True,
                    ),
                    reason="Dialogue rule initialized a visible relationship track.",
                    metadata={"source": "dialogue_mode", "visible_to_player": "true"},
                )
            ]
        if _sounds_kind(intent.raw_text):
            return [
                *change_trust(state, session.focus_npc_id, "player", 1, "Kind dialogue improved trust."),
                *change_affinity(state, session.focus_npc_id, "player", 1, "Kind dialogue improved affinity."),
                *emotion_from_event(state, session.focus_npc_id, "friendly_interaction"),
            ]
        if _sounds_threatening(intent.raw_text):
            return [
                StateDelta(
                    operation=StateDeltaOperation.INC,
                    path=f"relationships.{relationship.id}.fear",
                    value=1,
                    reason="Threatening dialogue increased fear.",
                    metadata={"source": "dialogue_mode", "relationship_id": relationship.id},
                ),
                StateDelta(
                    operation=StateDeltaOperation.INC,
                    path=f"relationships.{relationship.id}.trust",
                    value=-1,
                    reason="Threatening dialogue reduced trust.",
                    metadata={"source": "dialogue_mode", "relationship_id": relationship.id},
                ),
                *emotion_from_event(state, session.focus_npc_id, "threat"),
            ]
        return []

    def _require_active_session(self, dialogue_session_id: str) -> DialogueSession:
        session = self._sessions.get(dialogue_session_id)
        if session is None:
            raise ValueError(f"Unknown dialogue session: {dialogue_session_id}")
        if session.status != DialogueSessionStatus.ACTIVE:
            raise ValueError(f"Dialogue session is not active: {dialogue_session_id}")
        return session

    def _validate_npc_available(self, state: GameState, npc_id: str) -> None:
        npc = state.npcs.get(npc_id)
        if npc is None:
            raise ValueError(f"Dialogue target does not exist: {npc_id}")
        if npc.location_id != state.player.location_id:
            raise ValueError(f"Dialogue target is not present: {npc_id}")
        if not _npc_visible_to_player(state, npc_id):
            raise ValueError(f"Dialogue target is not visible: {npc_id}")
        if not can_talk(state, npc_id):
            raise ValueError(f"Dialogue target cannot talk: {npc_id}")

    def _build_rp_memory_context(
        self,
        *,
        state: GameState,
        session: DialogueSession | None,
        focus_npc_id: str,
        allowed_fact_ids: list[str],
        relationship_tone: object,
    ) -> RPMemoryContext | None:
        if self._memory_store is None:
            return None
        context_session = session or DialogueSession(
            session_id="preview",
            participant_ids=["player", focus_npc_id],
            focus_npc_id=focus_npc_id,
            started_turn=state.turn,
            last_turn=state.turn,
        )
        return RPMemoryContextBuilder(self._memory_store).build(
            state=state,
            dialogue_session=context_session,
            speaker_npc_id=focus_npc_id,
            player_id=state.player.id,
            location_id=state.player.location_id,
            visible_facts=list(state.player_visible_facts),
            npc_known_facts=allowed_fact_ids,
            relationship_tone=relationship_tone,
            emotional_state=state.npcs[focus_npc_id].emotional_state,
        )


class GroupDialogueManager:
    """Deterministic group RP scene manager.

    This manager never lets an LLM coordinate multiple agents or modify facts.
    It only selects speakers, builds per-NPC safe contexts, and records local
    scene events.
    """

    def __init__(self, policy: RoleplayContextPolicy | None = None, prompt_profile: PromptProfile | None = None) -> None:
        self._scenes: dict[str, GroupDialogueScene] = {}
        self._policy = policy or RoleplayContextPolicy()
        self._prompt_profile = prompt_profile
        self._output_checker = RPOutputConsistencyChecker()

    def set_prompt_profile(self, prompt_profile: PromptProfile | None) -> None:
        self._prompt_profile = prompt_profile

    def start_group_scene(
        self,
        state: GameState,
        *,
        participant_ids: list[str],
        game_session_id: str | None = None,
        scene_topic: str = "",
        scene_mood: str = "neutral",
        scene_mood_preset_id: str | None = None,
        active_speaker_id: str | None = None,
        event_log: EventLog | None = None,
    ) -> GroupDialogueScene:
        participants = sorted(dict.fromkeys(participant_ids))
        if len(participants) < 2:
            raise ValueError("Group dialogue requires at least two NPC participants")
        for npc_id in participants:
            _validate_group_participant(state, npc_id)
        speaker = active_speaker_id or self._select_initial_speaker(state, participants)
        if speaker not in participants:
            raise ValueError(f"Active speaker must be a participant: {speaker}")
        scene = GroupDialogueScene(
            scene_id=str(uuid4()),
            game_session_id=game_session_id,
            participant_ids=participants,
            location_id=state.player.location_id,
            active_speaker_id=speaker,
            turn_order=participants,
            scene_topic=scene_topic,
            scene_mood=scene_mood,
            scene_mood_preset_id=scene_mood_preset_id,
        )
        self._scenes[scene.scene_id] = scene
        if event_log is not None:
            event_log.append(_group_scene_event(state, scene, "group_dialogue_start"))
        return scene

    def select_next_speaker(
        self,
        state: GameState,
        scene_id: str,
        *,
        manual_focus_id: str | None = None,
        event_log: EventLog | None = None,
    ) -> str:
        scene = self._require_active_scene(scene_id)
        candidates = [npc_id for npc_id in scene.participant_ids if _participant_can_continue(state, scene, npc_id)]
        if not candidates:
            raise ValueError("No eligible group dialogue speaker")
        if manual_focus_id and manual_focus_id in candidates:
            next_speaker = manual_focus_id
        else:
            ranked = sorted(
                candidates,
                key=lambda npc_id: (-_speaker_priority(state, scene, npc_id), scene.turn_order.index(npc_id), npc_id),
            )
            next_speaker = ranked[0]
        scene.active_speaker_id = next_speaker
        self._scenes[scene.scene_id] = scene
        if event_log is not None:
            event_log.append(_group_scene_event(state, scene, "group_dialogue_next_speaker"))
        return next_speaker

    def build_participant_context(
        self,
        state: GameState,
        scene_id: str,
        npc_id: str,
    ) -> GroupParticipantContext:
        scene = self._scenes.get(scene_id)
        if scene is None:
            raise ValueError(f"Unknown group dialogue scene: {scene_id}")
        if npc_id not in scene.participant_ids:
            raise ValueError(f"NPC is not in group scene: {npc_id}")
        knowledge_context = get_npc_context_for_dialogue(state, npc_id)
        npc = state.npcs[npc_id]
        candidate_fact_ids = sorted(set(knowledge_context.knowledge) | set(npc.knowledge) | state.npc_knowledge.get(npc_id, set()))
        profile_context = build_npc_dialogue_profile_context(state, npc_id)
        rp_context = self._policy.build_context(
            state,
            scope=RoleplayContextScope.NPC_DIALOGUE,
            actor_id=npc_id,
            npc_id=npc_id,
            fact_ids=candidate_fact_ids,
            rp_flavor=[profile_context.public_persona] if profile_context.public_persona else [],
            emotional_expression=[profile_context.emotional_tone],
        )
        fact_ids = [entry.id for entry in rp_context.entries if entry.source == "fact"]
        tone = tone_summary_for_prompt(get_tone_for_dialogue(state, npc_id, "player"))
        mood_summary = scene_mood_summary_for_prompt(state, scene.scene_mood_preset_id)
        rp_style_summary = _rp_prompt_style_summary(self._prompt_profile)
        summary = (
            f"npc={npc_id}; scene={scene.scene_id}; topic={scene.scene_topic}; mood={scene.scene_mood}; "
            f"emotion={profile_context.emotional_tone}/{profile_context.emotion_intensity_band}; "
            f"tone={tone}; scene_mood={mood_summary or 'default'}; known_fact_count={len(fact_ids)}; "
            f"example_dialogue_count={len(profile_context.example_dialogue_summaries)}; "
            f"rp_style={self._prompt_profile.rp_profile.id if self._prompt_profile else 'default'}"
        )
        return GroupParticipantContext(
            npc_id=npc_id,
            npc_known_facts=fact_ids,
            emotional_summary=f"{profile_context.emotional_tone}:{profile_context.emotion_intensity_band}",
            relationship_tone_summary=tone,
            scene_mood_summary=mood_summary,
            example_dialogue_summaries=profile_context.example_dialogue_summaries,
            rp_prompt_style_summary=rp_style_summary,
            safe_context_summary=summary,
        )

    def validate_participant_output(self, candidate: RoleplayOutputCandidate) -> RoleplayOutputCheckResult:
        return self._policy.check_output(candidate)

    def check_participant_output_consistency(
        self,
        *,
        generated_text: str,
        state: GameState,
        context: GroupParticipantContext,
        action_result: ActionResult | None = None,
        forbidden_hidden_terms: list[str] | None = None,
        forbidden_hidden_ids: list[str] | None = None,
        allowed_flavor_terms: list[str] | None = None,
        candidate: RoleplayOutputCandidate | None = None,
    ) -> RPConsistencyReport:
        return self._output_checker.check(
            generated_text=generated_text,
            state=state,
            dialogue_context=context,
            action_result=action_result,
            visible_facts=state.player_visible_facts,
            npc_known_facts=context.npc_known_facts,
            forbidden_hidden_terms=forbidden_hidden_terms or [],
            forbidden_hidden_ids=forbidden_hidden_ids or [],
            allowed_flavor_terms=allowed_flavor_terms or [],
            speaker_npc_id=context.npc_id,
            candidate=candidate,
        )

    def end_group_scene(self, scene_id: str, event_log: EventLog | None = None, state: GameState | None = None) -> GroupDialogueScene:
        scene = self._scenes.get(scene_id)
        if scene is None:
            raise ValueError(f"Unknown group dialogue scene: {scene_id}")
        scene.status = GroupDialogueSceneStatus.ENDED
        self._scenes[scene_id] = scene
        if event_log is not None and state is not None:
            event_log.append(_group_scene_event(state, scene, "group_dialogue_end"))
        return scene

    def get_scene(self, scene_id: str) -> GroupDialogueScene | None:
        return self._scenes.get(scene_id)

    def _require_active_scene(self, scene_id: str) -> GroupDialogueScene:
        scene = self._scenes.get(scene_id)
        if scene is None:
            raise ValueError(f"Unknown group dialogue scene: {scene_id}")
        if scene.status != GroupDialogueSceneStatus.ACTIVE:
            raise ValueError(f"Group dialogue scene is not active: {scene_id}")
        return scene

    def _select_initial_speaker(self, state: GameState, participant_ids: list[str]) -> str:
        return sorted(participant_ids, key=lambda npc_id: (-_speaker_priority(state, None, npc_id), npc_id))[0]


def _sounds_kind(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("thank", "thanks", "please", "sorry", "help", "appreciate"))


def _sounds_threatening(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("threaten", "hurt", "kill", "hate", "insult", "liar"))


def _rp_memory_summaries(context: RPMemoryContext | None) -> list[str]:
    if context is None:
        return []
    summaries: list[str] = []
    for memory in context.speaker_safe_memories[:5]:
        summaries.append(
            f"memory_ref=speaker_safe; tag_count={len(memory.tags)}; turn={memory.created_turn}"
        )
    return summaries


def _rp_prompt_style_summary(prompt_profile: PromptProfile | None) -> str:
    if prompt_profile is None:
        return ""
    return prompt_profile.rp_profile.style_summary()


def _npc_visible_to_player(state: GameState, npc_id: str) -> bool:
    npc = state.npcs.get(npc_id)
    if npc is None or not npc.visible:
        return False
    return not npc.hidden or state.player.id in npc.discovered_by


def _validate_group_participant(state: GameState, npc_id: str) -> None:
    npc = state.npcs.get(npc_id)
    if npc is None:
        raise ValueError(f"Group participant does not exist: {npc_id}")
    if npc.location_id != state.player.location_id:
        raise ValueError(f"Group participant is not present: {npc_id}")
    if not _npc_visible_to_player(state, npc_id):
        raise ValueError(f"Group participant is not visible: {npc_id}")
    if not can_talk(state, npc_id):
        raise ValueError(f"Group participant cannot talk: {npc_id}")


def _participant_can_continue(state: GameState, scene: GroupDialogueScene, npc_id: str) -> bool:
    npc = state.npcs.get(npc_id)
    return npc is not None and npc.location_id == scene.location_id and _npc_visible_to_player(state, npc_id) and can_talk(state, npc_id)


def _speaker_priority(state: GameState, scene: GroupDialogueScene | None, npc_id: str) -> int:
    npc = state.npcs[npc_id]
    tone = get_tone_for_dialogue(state, npc_id, "player")
    topic_score = 5 if scene and scene.scene_topic and any(scene.scene_topic in goal for goal in _goal_labels(npc.goals)) else 0
    quest_score = 5 if any("quest" in goal for goal in _goal_labels(npc.goals)) else 0
    return npc.emotional_state.intensity + tone.tension + topic_score + quest_score


def _goal_labels(goals: list[object]) -> list[str]:
    return [getattr(goal, "id", str(goal)) for goal in goals]


def _group_scene_event(state: GameState, scene: GroupDialogueScene, action_type: str) -> Event:
    return Event(
        event_id=str(uuid4()),
        turn=state.turn,
        actor_id=scene.active_speaker_id,
        action_type=action_type,
        target_id="player",
        result="success",
        state_deltas=[],
        allow_empty_delta=True,
        visible_to_player=True,
        narrative_text=f"Group dialogue scene {scene.status.value}.",
    )
