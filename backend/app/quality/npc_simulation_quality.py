from __future__ import annotations

from collections import Counter
from typing import Any

from pydantic import BaseModel, Field

from app.core.event_log import Event, EventLog
from app.core.world_state import FactVisibility, GameState, NPCIntentStatus, NPCPlanStatus
from app.engine.rules.life_state import can_act
from app.engine.rules.npc_simulation_tick import NPCSimulationTickBudget, NPCSimulationTickResult
from app.quality.npc_behavior_coverage import NPCBehaviorCoverageReport, analyze_npc_behavior_coverage
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)


class NPCSimulationQualityReport(BaseModel):
    world_id: str
    npc_unknown_fact_used: list[QualityIssue] = Field(default_factory=list)
    hidden_fact_leaks: list[QualityIssue] = Field(default_factory=list)
    repeated_intent_loops: list[QualityIssue] = Field(default_factory=list)
    blocked_plan_loops: list[QualityIssue] = Field(default_factory=list)
    dead_npc_actions: list[QualityIssue] = Field(default_factory=list)
    invalid_targets: list[QualityIssue] = Field(default_factory=list)
    no_event_recorded: list[QualityIssue] = Field(default_factory=list)
    too_many_intents: list[QualityIssue] = Field(default_factory=list)
    plan_budget_exceeded: list[QualityIssue] = Field(default_factory=list)
    behavior_coverage_low: list[QualityIssue] = Field(default_factory=list)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        for key in (
            "npc_unknown_fact_used",
            "hidden_fact_leaks",
            "repeated_intent_loops",
            "blocked_plan_loops",
            "dead_npc_actions",
            "invalid_targets",
            "no_event_recorded",
            "too_many_intents",
            "plan_budget_exceeded",
            "behavior_coverage_low",
        ):
            payload[key] = [
                issue.normal_copy().model_dump(mode="json", exclude_none=True)
                for issue in getattr(self, key)
            ]
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return payload


def analyze_npc_simulation_quality(
    state: GameState,
    *,
    event_log: EventLog | None = None,
    events: list[Event] | None = None,
    tick_results: list[NPCSimulationTickResult] | None = None,
    budget: NPCSimulationTickBudget | None = None,
    coverage_report: NPCBehaviorCoverageReport | None = None,
    repeated_intent_threshold: int = 3,
    blocked_plan_threshold: int = 2,
) -> NPCSimulationQualityReport:
    all_events = list(events or [])
    if event_log is not None:
        all_events.extend(event_log.list_events())
    all_tick_results = list(tick_results or [])
    active_budget = budget or NPCSimulationTickBudget()

    unknown_fact_used = _unknown_fact_usage(state, all_events)
    hidden_leaks = _hidden_fact_leaks(state, all_events, all_tick_results)
    repeated_intents = _repeated_intent_loops(state, all_events, repeated_intent_threshold)
    blocked_plans = _blocked_plan_loops(state, all_events, blocked_plan_threshold)
    dead_actions = _dead_npc_actions(state, all_events, all_tick_results)
    invalid_targets = _invalid_targets(state, all_events)
    no_events = _no_event_recorded(all_tick_results)
    too_many = _too_many_intents(state, active_budget)
    budget_exceeded = _plan_budget_exceeded(all_tick_results)
    coverage_low = _behavior_coverage_low(state, coverage_report)

    report = NPCSimulationQualityReport(
        world_id=state.world_id,
        npc_unknown_fact_used=unknown_fact_used,
        hidden_fact_leaks=hidden_leaks,
        repeated_intent_loops=repeated_intents,
        blocked_plan_loops=blocked_plans,
        dead_npc_actions=dead_actions,
        invalid_targets=invalid_targets,
        no_event_recorded=no_events,
        too_many_intents=too_many,
        plan_budget_exceeded=budget_exceeded,
        behavior_coverage_low=coverage_low,
        quality_report=WorldQualityReport(world_id=state.world_id),
    )
    report.quality_report = _to_quality_report(report)
    return report


def analyze_npc_simulation_quality_for_world(
    world_id: str,
    *,
    worlds_root: str = "worlds",
) -> NPCSimulationQualityReport:
    from app.engine.content.world_loader import WorldLoader

    state = WorldLoader(worlds_root).load(world_id).to_game_state()
    coverage = analyze_npc_behavior_coverage(world_id, worlds_root=worlds_root)
    return analyze_npc_simulation_quality(state, coverage_report=coverage)


def _unknown_fact_usage(state: GameState, events: list[Event]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for event in events:
        npc_id = _event_npc_id(event)
        if npc_id not in state.npcs:
            continue
        known = set(state.npcs[npc_id].knowledge) | set(state.npc_knowledge.get(npc_id, set()))
        for fact_id in _event_fact_ids(event):
            if fact_id in state.facts and fact_id not in known:
                issues.append(
                    _issue(
                        state.world_id,
                        "npc_unknown_fact_used",
                        QualityIssueSeverity.ERROR,
                        f"NPC simulation used a fact outside the NPC knowledge set.",
                        entity_id=npc_id,
                        safe_details={"npc_id": npc_id, "fact_id": fact_id, "event_id": event.event_id},
                    )
                )
    return _dedupe_issues(issues)


def _hidden_fact_leaks(
    state: GameState,
    events: list[Event],
    tick_results: list[NPCSimulationTickResult],
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    hidden_facts = {
        fact_id: fact
        for fact_id, fact in state.facts.items()
        if fact.visibility == FactVisibility.HIDDEN or fact.secret
    }
    for event in events:
        if not event.visible_to_player:
            continue
        payload = event.model_dump(mode="json")
        for fact_id, fact in hidden_facts.items():
            if _contains_text(payload, fact.text):
                issues.append(
                    _issue(
                        state.world_id,
                        "hidden_fact_leak",
                        QualityIssueSeverity.BLOCKER,
                        "Player-visible NPC simulation event exposed hidden fact text.",
                        entity_id=_event_npc_id(event),
                        safe_details={"fact_id": fact_id, "event_id": event.event_id},
                        hidden_details_debug_only={"hidden_fact_text": fact.text},
                    )
                )
    for result in tick_results:
        for entry in result.debug_output:
            for fact_id, fact in hidden_facts.items():
                if fact.text and fact.text in entry.detail:
                    issues.append(
                        _issue(
                            state.world_id,
                            "hidden_fact_leak",
                            QualityIssueSeverity.ERROR,
                            "NPC simulation debug output contains hidden fact text.",
                            entity_id=entry.npc_id,
                            safe_details={"fact_id": fact_id, "phase": entry.phase},
                            hidden_details_debug_only={"hidden_fact_text": fact.text},
                        )
                    )
    return _dedupe_issues(issues)


def _repeated_intent_loops(
    state: GameState,
    events: list[Event],
    threshold: int,
) -> list[QualityIssue]:
    counts: Counter[tuple[str, str, str | None]] = Counter()
    for npc in state.npcs.values():
        for intent in npc.intent_queue:
            if intent.status in {NPCIntentStatus.QUEUED, NPCIntentStatus.ACTIVE, NPCIntentStatus.BLOCKED}:
                counts[(npc.id, intent.intent_type, intent.target_id)] += 1
    for event in events:
        npc_id = _event_npc_id(event)
        intent_type = _event_intent_type(event)
        if npc_id and intent_type:
            counts[(npc_id, intent_type, _event_target(event))] += 1
    return [
        _issue(
            state.world_id,
            "repeated_intent_loop",
            QualityIssueSeverity.WARNING,
            "NPC simulation produced the same unresolved intent repeatedly.",
            entity_id=npc_id,
            safe_details={"npc_id": npc_id, "intent_type": intent_type, "target_id": target_id, "count": count},
        )
        for (npc_id, intent_type, target_id), count in sorted(counts.items())
        if count > threshold
    ]


def _blocked_plan_loops(
    state: GameState,
    events: list[Event],
    threshold: int,
) -> list[QualityIssue]:
    counts: Counter[tuple[str, str]] = Counter()
    for npc in state.npcs.values():
        for plan in npc.plans:
            if plan.status == NPCPlanStatus.BLOCKED:
                counts[(npc.id, plan.id)] += 1
    for event in events:
        npc_id = _event_npc_id(event)
        plan_id = _event_plan_id(event)
        status = _event_status(event)
        if npc_id and plan_id and status == "blocked":
            counts[(npc_id, plan_id)] += 1
    return [
        _issue(
            state.world_id,
            "blocked_plan_loop",
            QualityIssueSeverity.ERROR,
            "NPC simulation repeatedly blocked the same plan.",
            entity_id=npc_id,
            safe_details={"npc_id": npc_id, "plan_id": plan_id, "count": count},
        )
        for (npc_id, plan_id), count in sorted(counts.items())
        if count > threshold
    ]


def _dead_npc_actions(
    state: GameState,
    events: list[Event],
    tick_results: list[NPCSimulationTickResult],
) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    inactive = {npc_id for npc_id in state.npcs if not can_act(state, npc_id)}
    for event in events:
        npc_id = _event_npc_id(event)
        if npc_id in inactive and _is_simulation_action(event):
            issues.append(
                _issue(
                    state.world_id,
                    "dead_npc_acted",
                    QualityIssueSeverity.BLOCKER,
                    "Dead or incapacitated NPC produced a simulation action.",
                    entity_id=npc_id,
                    safe_details={"npc_id": npc_id, "event_id": event.event_id, "action_type": event.action_type},
                )
            )
    for result in tick_results:
        for npc_id in result.processed_npc_ids:
            if npc_id in inactive:
                issues.append(
                    _issue(
                        state.world_id,
                        "dead_npc_acted",
                        QualityIssueSeverity.BLOCKER,
                        "Simulation tick processed a dead or incapacitated NPC.",
                        entity_id=npc_id,
                        safe_details={"npc_id": npc_id},
                    )
                )
    return _dedupe_issues(issues)


def _invalid_targets(state: GameState, events: list[Event]) -> list[QualityIssue]:
    valid_ids = (
        set(state.npcs)
        | set(state.locations)
        | set(state.objects)
        | set(state.facts)
        | set(state.rumors)
        | set(state.quests)
        | set(state.factions)
        | set(state.crimes)
        | {"player"}
    )
    issues: list[QualityIssue] = []
    for npc in state.npcs.values():
        for intent in npc.intent_queue:
            if intent.target_id and intent.target_id not in valid_ids:
                issues.append(
                    _issue(
                        state.world_id,
                        "invalid_target",
                        QualityIssueSeverity.ERROR,
                        "NPC intent references an invalid target.",
                        entity_id=npc.id,
                        safe_details={"npc_id": npc.id, "target_id": intent.target_id, "intent_id": intent.id},
                    )
                )
        for plan in npc.plans:
            for index, step in enumerate(plan.steps):
                if step.target_id and step.target_id not in valid_ids:
                    issues.append(
                        _issue(
                            state.world_id,
                            "invalid_target",
                            QualityIssueSeverity.ERROR,
                            "NPC plan step references an invalid target.",
                            entity_id=npc.id,
                            safe_details={"npc_id": npc.id, "target_id": step.target_id, "plan_id": plan.id, "step_index": index},
                        )
                    )
    for event in events:
        target = _event_target(event)
        if target and target not in valid_ids:
            issues.append(
                _issue(
                    state.world_id,
                    "invalid_target",
                    QualityIssueSeverity.ERROR,
                    "NPC simulation event references an invalid target.",
                    entity_id=_event_npc_id(event),
                    safe_details={"target_id": target, "event_id": event.event_id},
                )
            )
    return _dedupe_issues(issues)


def _no_event_recorded(tick_results: list[NPCSimulationTickResult]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for index, result in enumerate(tick_results):
        if result.state_deltas and not result.events:
            issues.append(
                QualityIssue(
                    id=f"npc_simulation_quality:no_event_recorded:{index}",
                    severity=QualityIssueSeverity.ERROR,
                    category="no_event_recorded",
                    message="NPC simulation produced StateDelta entries without Event records.",
                    safe_details={"tick_index": index, "state_deltas": len(result.state_deltas)},
                )
            )
    return issues


def _too_many_intents(state: GameState, budget: NPCSimulationTickBudget) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for npc in sorted(state.npcs.values(), key=lambda item: item.id):
        open_count = sum(
            1
            for intent in npc.intent_queue
            if intent.status in {NPCIntentStatus.QUEUED, NPCIntentStatus.ACTIVE, NPCIntentStatus.BLOCKED}
        )
        if open_count > budget.max_intents_per_npc:
            issues.append(
                _issue(
                    state.world_id,
                    "too_many_intents",
                    QualityIssueSeverity.WARNING,
                    "NPC has more unresolved intents than the simulation tick budget allows.",
                    entity_id=npc.id,
                    safe_details={"npc_id": npc.id, "intent_count": open_count, "budget": budget.max_intents_per_npc},
                )
            )
    return issues


def _plan_budget_exceeded(tick_results: list[NPCSimulationTickResult]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    for index, result in enumerate(tick_results):
        if result.budget_exhausted or any(entry.phase == "budget" or "max_plan_steps" in entry.detail for entry in result.debug_output):
            issues.append(
                QualityIssue(
                    id=f"npc_simulation_quality:plan_budget_exceeded:{index}",
                    severity=QualityIssueSeverity.WARNING,
                    category="plan_budget_exceeded",
                    message="NPC simulation tick exhausted its action or plan budget.",
                    safe_details={"tick_index": index, "events": len(result.events), "state_deltas": len(result.state_deltas)},
                )
            )
    return issues


def _behavior_coverage_low(
    state: GameState,
    coverage_report: NPCBehaviorCoverageReport | None,
) -> list[QualityIssue]:
    if coverage_report is None:
        return []
    goal_count = coverage_report.goals_total
    covered = (
        coverage_report.goals_activated
        + coverage_report.goals_completed
        + coverage_report.goals_failed
        + coverage_report.goals_blocked
        + sum(coverage_report.planning_actions_executed.values())
    )
    if goal_count == 0 or covered >= max(1, goal_count // 2):
        return []
    return [
        _issue(
            state.world_id,
            "behavior_coverage_low",
            QualityIssueSeverity.WARNING,
            "NPC simulation behavior coverage is low for defined NPC goals.",
            safe_details={"goals_total": goal_count, "covered_signals": covered},
        )
    ]


def _to_quality_report(report: NPCSimulationQualityReport) -> WorldQualityReport:
    issues = [
        *report.npc_unknown_fact_used,
        *report.hidden_fact_leaks,
        *report.repeated_intent_loops,
        *report.blocked_plan_loops,
        *report.dead_npc_actions,
        *report.invalid_targets,
        *report.no_event_recorded,
        *report.too_many_intents,
        *report.plan_budget_exceeded,
        *report.behavior_coverage_low,
    ]
    return WorldQualityReport(
        world_id=report.world_id,
        categories=["npc_simulation_quality"],
        issues=issues,
        metrics=[
            QualityMetric(
                name="npc_simulation_quality_issues",
                value=len(issues),
                category="npc_simulation_quality",
                threshold=0,
                status=QualityMetricStatus.OK if not issues else QualityMetricStatus.ERROR,
            )
        ],
        summary={
            "issue_counts": {
                "npc_unknown_fact_used": len(report.npc_unknown_fact_used),
                "hidden_fact_leak": len(report.hidden_fact_leaks),
                "repeated_intent_loop": len(report.repeated_intent_loops),
                "blocked_plan_loop": len(report.blocked_plan_loops),
                "dead_npc_acted": len(report.dead_npc_actions),
                "invalid_target": len(report.invalid_targets),
                "no_event_recorded": len(report.no_event_recorded),
                "too_many_intents": len(report.too_many_intents),
                "plan_budget_exceeded": len(report.plan_budget_exceeded),
                "behavior_coverage_low": len(report.behavior_coverage_low),
            }
        },
        recommended_actions=[
            "Review NPC simulation rules and playtests for deterministic knowledge, lifecycle, and budget violations."
        ] if issues else [],
    ).normal_copy()


def _event_fact_ids(event: Event) -> set[str]:
    fact_ids: set[str] = set()
    for delta in event.state_deltas:
        for key in ("fact_id", "required_fact_id"):
            if delta.metadata.get(key):
                fact_ids.add(str(delta.metadata[key]))
        for condition in _metadata_list(delta.metadata.get("preconditions")):
            if condition.startswith("fact:"):
                fact_ids.add(condition.split(":", 1)[1])
    return fact_ids


def _event_npc_id(event: Event) -> str | None:
    if event.target_id and event.target_id.startswith("npc:"):
        return event.target_id.split(":", 1)[1]
    if event.target_id in {"player", None}:
        pass
    elif event.target_id:
        return event.target_id
    if event.actor_id and event.actor_id not in {"system", "player"}:
        return event.actor_id
    for delta in event.state_deltas:
        npc_id = delta.metadata.get("npc_id") or _npc_id_from_path(delta.path)
        if npc_id:
            return str(npc_id)
    return None


def _event_intent_type(event: Event) -> str | None:
    for delta in event.state_deltas:
        intent_type = delta.metadata.get("intent_type") or delta.metadata.get("plan_type")
        if intent_type:
            return str(intent_type)
    if event.action_type in {"npc_intent", "npc_planning", "npc_simulation"} and event.result:
        return event.result
    return None


def _event_plan_id(event: Event) -> str | None:
    for delta in event.state_deltas:
        if delta.metadata.get("plan_id"):
            return str(delta.metadata["plan_id"])
    return None


def _event_status(event: Event) -> str | None:
    for delta in event.state_deltas:
        if delta.metadata.get("status"):
            return str(delta.metadata["status"])
    return event.result if event.result in {"blocked", "failed", "completed"} else None


def _event_target(event: Event) -> str | None:
    for delta in event.state_deltas:
        target = delta.metadata.get("target_id")
        if target:
            return str(target)
    return event.target_id


def _is_simulation_action(event: Event) -> bool:
    if event.action_type.startswith("npc_"):
        return True
    for delta in event.state_deltas:
        source = delta.metadata.get("source", "")
        if str(source).startswith("npc_"):
            return True
    return False


def _npc_id_from_path(path: str) -> str | None:
    parts = path.split(".")
    if len(parts) >= 2 and parts[0] == "npcs":
        return parts[1]
    return None


def _metadata_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _contains_text(payload: Any, text: str) -> bool:
    if not text:
        return False
    if isinstance(payload, dict):
        return any(_contains_text(item, text) for item in payload.values())
    if isinstance(payload, list):
        return any(_contains_text(item, text) for item in payload)
    return isinstance(payload, str) and text in payload


def _issue(
    world_id: str,
    category: str,
    severity: QualityIssueSeverity,
    message: str,
    *,
    entity_id: str | None = None,
    safe_details: dict[str, Any] | None = None,
    hidden_details_debug_only: dict[str, Any] | None = None,
) -> QualityIssue:
    safe = safe_details or {}
    issue_id = ":".join(
        [
            "npc_simulation_quality",
            world_id,
            category,
            str(entity_id or safe.get("npc_id") or "world"),
            str(safe.get("event_id") or safe.get("intent_id") or safe.get("plan_id") or safe.get("target_id") or safe.get("fact_id") or "issue"),
        ]
    )
    return QualityIssue(
        id=issue_id,
        severity=severity,
        category=category,
        entity_id=entity_id,
        message=message,
        safe_details={"code": category, **safe},
        hidden_details_debug_only=hidden_details_debug_only,
    )


def _dedupe_issues(issues: list[QualityIssue]) -> list[QualityIssue]:
    by_id = {issue.id: issue for issue in issues}
    return [by_id[key] for key in sorted(by_id)]
