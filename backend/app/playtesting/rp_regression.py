from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import StrEnum
from random import Random
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.event_log import EventLog
from app.core.world_state import GameState
from app.engine.content.world_loader import WorldLoader
from app.quality import QualityIssue, QualityIssueSeverity, QualityMetric, QualityMetricStatus, WorldQualityReport
from app.roleplay.dialogue import DialogueManager, DialogueMode, GroupDialogueManager


class RPRegressionScenarioType(StrEnum):
    FRIENDLY_TALK = "friendly_talk"
    INTERROGATION = "interrogation"
    NEGOTIATION = "negotiation"
    CONFLICT_ARGUMENT = "conflict_argument"
    INTIMATE_TRUST_BUILDING = "intimate_trust_building"
    GROUP_MEETING = "group_meeting"
    SECRET_PROBING = "secret_probing"
    RUMOR_DISCUSSION = "rumor_discussion"


class RPRegressionScenario(BaseModel):
    id: str
    world_id: str = "mist_valley"
    scenario_type: RPRegressionScenarioType = RPRegressionScenarioType.FRIENDLY_TALK
    participant_ids: list[str] = Field(default_factory=list)
    input_sequence: list[str] = Field(default_factory=list)
    expected_safe_topics: list[str] = Field(default_factory=list)
    forbidden_facts: list[str] = Field(default_factory=list)
    expected_emotional_shifts: list[str] = Field(default_factory=list)
    expected_relationship_tone_changes: list[str] = Field(default_factory=list)
    max_turns: int = Field(default=5, ge=0)
    seed: int = 123


class RPRegressionStepRecord(BaseModel):
    step: int
    input_text: str
    speaker_id: str | None = None
    event_action_type: str | None = None
    delta_paths: list[str] = Field(default_factory=list)
    safe_topics_seen: list[str] = Field(default_factory=list)
    consistency_issue_codes: list[str] = Field(default_factory=list)


class RPRegressionReport(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scenario_id: str
    scenario_type: RPRegressionScenarioType
    world_id: str
    seed: int
    passed: bool
    steps_run: int
    step_records: list[RPRegressionStepRecord] = Field(default_factory=list)
    failure_reasons: list[str] = Field(default_factory=list)
    hidden_leak_summary: list[str] = Field(default_factory=list)
    emotional_shift_summary: list[str] = Field(default_factory=list)
    relationship_tone_summary: list[str] = Field(default_factory=list)
    group_context_summary: list[str] = Field(default_factory=list)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, object]:
        payload = self.model_dump(mode="json", exclude_none=True)
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return _strip_hidden_text(payload)


def run_rp_regression_scenario(
    scenario: RPRegressionScenario,
    *,
    worlds_root: str = "worlds",
) -> RPRegressionReport:
    rng = Random(scenario.seed)
    state = WorldLoader(worlds_root).load(scenario.world_id).to_game_state()
    event_log = EventLog()
    step_records: list[RPRegressionStepRecord] = []
    failure_reasons: list[str] = []
    hidden_leaks: list[str] = []
    emotional_shifts: list[str] = []
    relationship_changes: list[str] = []
    group_context_summary: list[str] = []

    if _is_group_scenario(scenario):
        state, group_records, group_failures, group_leaks, group_summary = _run_group_regression(
            scenario,
            state,
            event_log,
            rng,
        )
        step_records.extend(group_records)
        failure_reasons.extend(group_failures)
        hidden_leaks.extend(group_leaks)
        group_context_summary.extend(group_summary)
    else:
        state, records, failures, leaks, emotions, relationships = _run_dialogue_regression(
            scenario,
            state,
            event_log,
            rng,
        )
        step_records.extend(records)
        failure_reasons.extend(failures)
        hidden_leaks.extend(leaks)
        emotional_shifts.extend(emotions)
        relationship_changes.extend(relationships)

    failure_reasons.extend(_check_expectations(scenario, emotional_shifts, relationship_changes, hidden_leaks))
    if _contains_hidden_text(json.dumps(failure_reasons + hidden_leaks, ensure_ascii=False), state):
        failure_reasons.append("normal_report_hidden_text_leak")
    quality = _quality_report(scenario, failure_reasons, hidden_leaks, len(step_records))
    return RPRegressionReport(
        scenario_id=scenario.id,
        scenario_type=scenario.scenario_type,
        world_id=scenario.world_id,
        seed=scenario.seed,
        passed=not failure_reasons and not hidden_leaks,
        steps_run=len(step_records),
        step_records=step_records,
        failure_reasons=_redact_hidden_text(_dedupe(failure_reasons), state),
        hidden_leak_summary=_redact_hidden_text(_dedupe(hidden_leaks), state),
        emotional_shift_summary=_dedupe(emotional_shifts),
        relationship_tone_summary=_dedupe(relationship_changes),
        group_context_summary=_dedupe(group_context_summary),
        quality_report=quality,
    )


def _run_dialogue_regression(
    scenario: RPRegressionScenario,
    state: GameState,
    event_log: EventLog,
    rng: Random,
) -> tuple[GameState, list[RPRegressionStepRecord], list[str], list[str], list[str], list[str]]:
    manager = DialogueManager()
    focus_npc_id = scenario.participant_ids[0] if scenario.participant_ids else _first_visible_npc(state)
    mode = _dialogue_mode_for_scenario(scenario.scenario_type)
    session = manager.start_dialogue(
        state,
        game_session_id=f"rp-regression-{scenario.id}",
        focus_npc_id=focus_npc_id,
        dialogue_mode=mode,
        active_topics=scenario.expected_safe_topics,
        event_log=event_log,
    )
    records: list[RPRegressionStepRecord] = []
    failures: list[str] = []
    leaks: list[str] = []
    emotional_shifts: list[str] = []
    relationship_changes: list[str] = []
    for index, player_input in enumerate(scenario.input_sequence[: scenario.max_turns]):
        generated_text = _safe_fake_output(focus_npc_id, player_input, scenario, rng)
        context = manager.build_dialogue_context(state, focus_npc_id=focus_npc_id, session=session)
        output_check = manager.check_dialogue_output_consistency(
            generated_text=generated_text,
            state=state,
            context=context,
            forbidden_hidden_terms=_forbidden_fact_texts(state, scenario.forbidden_facts),
            forbidden_hidden_ids=scenario.forbidden_facts,
            allowed_flavor_terms=scenario.expected_safe_topics,
        )
        if not output_check.ok:
            codes = sorted({issue.code for issue in output_check.issues})
            failures.append(f"rp_output_consistency:{index}:{','.join(codes)}")
            if "hidden_fact_leakage" in codes:
                leaks.append(f"hidden_fact_leakage:step:{index}")
        result = manager.continue_dialogue(
            state,
            event_log,
            dialogue_session_id=session.session_id,
            player_input=player_input,
        )
        state = result.state
        session = result.session
        delta_paths = [delta.path for delta in result.event.state_deltas] if result.event else []
        emotional_shifts.extend(path for path in delta_paths if path.endswith(".emotional_state"))
        relationship_changes.extend(path for path in delta_paths if path.startswith("relationships."))
        records.append(
            RPRegressionStepRecord(
                step=index,
                input_text=player_input,
                speaker_id=focus_npc_id,
                event_action_type=result.event.action_type if result.event else None,
                delta_paths=delta_paths,
                safe_topics_seen=[topic for topic in scenario.expected_safe_topics if topic.lower() in generated_text.lower()],
                consistency_issue_codes=sorted({issue.code for issue in output_check.issues}),
            )
        )
    return state, records, failures, leaks, emotional_shifts, relationship_changes


def _run_group_regression(
    scenario: RPRegressionScenario,
    state: GameState,
    event_log: EventLog,
    rng: Random,
) -> tuple[GameState, list[RPRegressionStepRecord], list[str], list[str], list[str]]:
    manager = GroupDialogueManager()
    participants = scenario.participant_ids or _first_visible_npcs(state, 2)
    scene = manager.start_group_scene(
        state,
        participant_ids=participants,
        scene_topic=", ".join(scenario.expected_safe_topics),
        scene_mood="serious",
        event_log=event_log,
    )
    records: list[RPRegressionStepRecord] = []
    failures: list[str] = []
    leaks: list[str] = []
    summaries: list[str] = []
    context_by_npc = {npc_id: manager.build_participant_context(state, scene.scene_id, npc_id) for npc_id in scene.participant_ids}
    for npc_id, context in context_by_npc.items():
        summaries.append(f"{npc_id}:facts:{len(context.npc_known_facts)}")
        forbidden_for_npc = [fact_id for fact_id in scenario.forbidden_facts if fact_id not in context.npc_known_facts]
        text = _safe_fake_output(npc_id, "group scene", scenario, rng)
        check = manager.check_participant_output_consistency(
            generated_text=text,
            state=state,
            context=context,
            forbidden_hidden_terms=_forbidden_fact_texts(state, forbidden_for_npc),
            forbidden_hidden_ids=forbidden_for_npc,
        )
        if not check.ok:
            codes = sorted({issue.code for issue in check.issues})
            failures.append(f"group_output_consistency:{npc_id}:{','.join(codes)}")
            if "hidden_fact_leakage" in codes:
                leaks.append(f"group_hidden_fact_leakage:{npc_id}")
    for index, _ in enumerate(scenario.input_sequence[: scenario.max_turns]):
        speaker = manager.select_next_speaker(state, scene.scene_id, event_log=event_log)
        records.append(
            RPRegressionStepRecord(
                step=index,
                input_text="group_next_speaker",
                speaker_id=speaker,
                event_action_type=event_log.list_events()[-1].action_type if event_log.list_events() else None,
            )
        )
    return state, records, failures, leaks, summaries


def _safe_fake_output(speaker_id: str, player_input: str, scenario: RPRegressionScenario, rng: Random) -> str:
    topic = scenario.expected_safe_topics[rng.randrange(len(scenario.expected_safe_topics))] if scenario.expected_safe_topics else "the scene"
    if scenario.scenario_type == RPRegressionScenarioType.SECRET_PROBING:
        return f"{speaker_id} refuses to discuss hidden matters and redirects to {topic}."
    return f"{speaker_id} responds to '{player_input}' while staying on {topic}."


def _check_expectations(
    scenario: RPRegressionScenario,
    emotional_shifts: list[str],
    relationship_changes: list[str],
    hidden_leaks: list[str],
) -> list[str]:
    failures: list[str] = []
    if scenario.expected_emotional_shifts and not emotional_shifts:
        failures.append("expected_emotional_shift_missing")
    if scenario.expected_relationship_tone_changes and not relationship_changes:
        failures.append("expected_relationship_tone_change_missing")
    if hidden_leaks:
        failures.append("hidden_leak_detected")
    return failures


def _dialogue_mode_for_scenario(scenario_type: RPRegressionScenarioType) -> DialogueMode:
    mapping = {
        RPRegressionScenarioType.INTERROGATION: DialogueMode.INTERROGATION,
        RPRegressionScenarioType.NEGOTIATION: DialogueMode.NEGOTIATION,
        RPRegressionScenarioType.CONFLICT_ARGUMENT: DialogueMode.CONFLICT,
        RPRegressionScenarioType.INTIMATE_TRUST_BUILDING: DialogueMode.INTIMATE,
        RPRegressionScenarioType.FRIENDLY_TALK: DialogueMode.CASUAL,
        RPRegressionScenarioType.SECRET_PROBING: DialogueMode.INTERROGATION,
        RPRegressionScenarioType.RUMOR_DISCUSSION: DialogueMode.CASUAL,
    }
    return mapping.get(scenario_type, DialogueMode.FOCUSED)


def _is_group_scenario(scenario: RPRegressionScenario) -> bool:
    return scenario.scenario_type == RPRegressionScenarioType.GROUP_MEETING or len(scenario.participant_ids) > 1


def _first_visible_npc(state: GameState) -> str:
    for npc_id, npc in sorted(state.npcs.items()):
        if npc.visible and not npc.hidden and npc.location_id == state.player.location_id:
            return npc_id
    raise ValueError("No visible NPC available for RP regression")


def _first_visible_npcs(state: GameState, count: int) -> list[str]:
    return [
        npc_id
        for npc_id, npc in sorted(state.npcs.items())
        if npc.visible and not npc.hidden and npc.location_id == state.player.location_id
    ][:count]


def _forbidden_fact_texts(state: GameState, fact_ids: list[str]) -> list[str]:
    return [state.facts[fact_id].text or "" for fact_id in fact_ids if fact_id in state.facts and state.facts[fact_id].text]


def _contains_hidden_text(value: str, state: GameState) -> bool:
    return any(fact.text and fact.secret and fact.text in value for fact in state.facts.values())


def _redact_hidden_text(values: list[str], state: GameState) -> list[str]:
    redacted = values
    for fact in state.facts.values():
        if fact.text and fact.secret:
            redacted = [value.replace(fact.text, "[hidden text redacted]") for value in redacted]
    return redacted


def _quality_report(
    scenario: RPRegressionScenario,
    failures: list[str],
    hidden_leaks: list[str],
    steps_run: int,
) -> WorldQualityReport:
    issues = [
        QualityIssue(
            id=f"rp_regression:{scenario.id}:{index}",
            severity=QualityIssueSeverity.BLOCKER if "hidden" in reason else QualityIssueSeverity.ERROR,
            category="rp_regression",
            entity_id=scenario.id,
            message=reason,
            safe_details={"scenario_type": scenario.scenario_type.value},
        )
        for index, reason in enumerate([*failures, *hidden_leaks])
    ]
    return WorldQualityReport(
        world_id=scenario.world_id,
        categories=["rp_regression"],
        metrics=[
            QualityMetric(name="rp_regression_steps", value=steps_run, category="rp_regression", status=QualityMetricStatus.OK),
            QualityMetric(
                name="rp_regression_failures",
                value=len(issues),
                category="rp_regression",
                threshold=0,
                status=QualityMetricStatus.OK if not issues else QualityMetricStatus.ERROR,
            ),
        ],
        issues=issues,
        summary={"scenario_id": scenario.id, "passed": not issues, "steps_run": steps_run},
        recommended_actions=[] if not issues else ["Review RP regression failures before changing prompt or dialogue rules."],
    )


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _strip_hidden_text(value: object) -> object:
    if isinstance(value, dict):
        return {key: _strip_hidden_text(item) for key, item in value.items() if key != "hidden_details_debug_only"}
    if isinstance(value, list):
        return [_strip_hidden_text(item) for item in value]
    return value
