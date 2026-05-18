from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.playtesting.runner import PlaytestReport, PlaytestScenarioReport
from app.quality.reports import (
    QualityIssue,
    QualityIssueSeverity,
    QualityMetric,
    QualityMetricStatus,
    WorldQualityReport,
)


class SocialConsequenceCoverageRequest(BaseModel):
    events: list[Event] = Field(default_factory=list)
    playtest_reports: list[PlaytestReport] = Field(default_factory=list)
    scenario_reports: list[PlaytestScenarioReport] = Field(default_factory=list)


class SocialConsequenceCoverageReport(BaseModel):
    world_id: str
    crimes_configured: int = 0
    crimes_triggered: int = 0
    witness_records_generated: int = 0
    rumors_configured: int = 0
    rumors_created: int = 0
    rumors_propagated: int = 0
    faction_reputation_changes: int = 0
    npc_reactions_triggered: int = 0
    duplicate_consequences_prevented: int = 0
    orphan_consequence_rules: int = 0
    missing_rumor_fact_issues: list[QualityIssue] = Field(default_factory=list)
    missing_faction_effect_issues: list[QualityIssue] = Field(default_factory=list)
    hidden_fact_leakage_risks: list[QualityIssue] = Field(default_factory=list)
    untriggerable_consequence_issues: list[QualityIssue] = Field(default_factory=list)
    duplicate_consequence_risks: list[QualityIssue] = Field(default_factory=list)
    quality_report: WorldQualityReport

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", exclude_none=True)
        for field_name in _ISSUE_FIELDS:
            payload[field_name] = [
                issue.normal_copy().model_dump(mode="json", exclude_none=True)
                for issue in getattr(self, field_name)
            ]
        payload["quality_report"] = self.quality_report.model_dump_normal()
        return payload


class _SocialContent(BaseModel):
    world_path: Path
    facts: list[dict[str, Any]] = Field(default_factory=list)
    factions: list[dict[str, Any]] = Field(default_factory=list)
    rumors: list[dict[str, Any]] = Field(default_factory=list)
    npcs: list[dict[str, Any]] = Field(default_factory=list)
    quests: list[dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def load(cls, world_path: Path) -> "_SocialContent":
        return cls(
            world_path=world_path,
            facts=_read_yaml_list(world_path / "facts.yaml", "facts"),
            factions=_read_yaml_list(world_path / "factions.yaml", "factions"),
            rumors=_read_yaml_list(world_path / "rumors.yaml", "rumors"),
            npcs=_read_yaml_list(world_path / "npcs.yaml", "npcs"),
            quests=_read_yaml_list(world_path / "quests.yaml", "quests"),
        )

    @property
    def fact_by_id(self) -> dict[str, dict[str, Any]]:
        return {str(fact.get("id")): fact for fact in self.facts if fact.get("id")}

    @property
    def faction_ids(self) -> set[str]:
        return {str(faction.get("id")) for faction in self.factions if faction.get("id")}

    @property
    def npc_ids(self) -> set[str]:
        return {str(npc.get("id")) for npc in self.npcs if npc.get("id")}


_ISSUE_FIELDS = [
    "missing_rumor_fact_issues",
    "missing_faction_effect_issues",
    "hidden_fact_leakage_risks",
    "untriggerable_consequence_issues",
    "duplicate_consequence_risks",
]

CRIME_TAGS = {"crime", "theft", "assault", "murder", "lockpicking", "vandalism", "forbidden_magic"}
SOCIAL_ACTION_TYPES = {
    "crime_consequence",
    "rumor_spread",
    "faction_reputation_changed",
    "faction_conflict",
    "npc_reaction",
}


def analyze_social_consequence_coverage(
    world_id: str,
    *,
    worlds_root: str | Path = "worlds",
    events: list[Event] | None = None,
    playtest_reports: list[PlaytestReport] | None = None,
    scenario_reports: list[PlaytestScenarioReport] | None = None,
) -> SocialConsequenceCoverageReport:
    world_path = Path(worlds_root) / world_id
    if not world_path.exists():
        raise FileNotFoundError(world_path)

    content = _SocialContent.load(world_path)
    all_events = list(events or [])
    all_events.extend(_events_from_playtests(playtest_reports or []))
    all_events.extend(_events_from_scenarios(scenario_reports or []))

    report = SocialConsequenceCoverageReport(
        world_id=world_id,
        crimes_configured=_configured_crime_count(content.rumors),
        rumors_configured=len([rumor for rumor in content.rumors if rumor.get("id")]),
        quality_report=WorldQualityReport(world_id=world_id),
    )

    _detect_rumor_reference_issues(report, content)
    _detect_untriggerable_consequences(report, content)
    _detect_duplicate_consequence_risks(report, content)
    _observe_event_coverage(report, all_events)

    report.orphan_consequence_rules = len(report.untriggerable_consequence_issues)
    report.quality_report = social_consequence_coverage_to_quality_report(report)
    return report


def social_consequence_coverage_to_quality_report(
    report: SocialConsequenceCoverageReport,
) -> WorldQualityReport:
    issues = [issue for field_name in _ISSUE_FIELDS for issue in getattr(report, field_name)]
    blocker_count = sum(1 for issue in issues if issue.severity == QualityIssueSeverity.BLOCKER)
    error_count = sum(1 for issue in issues if issue.severity == QualityIssueSeverity.ERROR)
    warning_count = sum(1 for issue in issues if issue.severity == QualityIssueSeverity.WARNING)
    status = QualityMetricStatus.OK
    if blocker_count:
        status = QualityMetricStatus.BLOCKER
    elif error_count:
        status = QualityMetricStatus.ERROR
    elif warning_count:
        status = QualityMetricStatus.WARNING
    return WorldQualityReport(
        world_id=report.world_id,
        categories=["social_consequence_coverage"],
        metrics=[
            QualityMetric(name="crimes_configured", value=report.crimes_configured, category="social_consequence_coverage", status=QualityMetricStatus.OK),
            QualityMetric(name="crimes_triggered", value=report.crimes_triggered, category="social_consequence_coverage", status=QualityMetricStatus.OK),
            QualityMetric(name="witness_records_generated", value=report.witness_records_generated, category="social_consequence_coverage", status=QualityMetricStatus.OK),
            QualityMetric(name="rumors_configured", value=report.rumors_configured, category="social_consequence_coverage", status=QualityMetricStatus.OK),
            QualityMetric(name="rumors_created", value=report.rumors_created, category="social_consequence_coverage", status=QualityMetricStatus.OK),
            QualityMetric(name="rumors_propagated", value=report.rumors_propagated, category="social_consequence_coverage", status=QualityMetricStatus.OK),
            QualityMetric(name="faction_reputation_changes", value=report.faction_reputation_changes, category="social_consequence_coverage", status=QualityMetricStatus.OK),
            QualityMetric(name="npc_reactions_triggered", value=report.npc_reactions_triggered, category="social_consequence_coverage", status=QualityMetricStatus.OK),
            QualityMetric(name="duplicate_consequences_prevented", value=report.duplicate_consequences_prevented, category="social_consequence_coverage", status=QualityMetricStatus.OK),
            QualityMetric(name="orphan_consequence_rules", value=report.orphan_consequence_rules, category="social_consequence_coverage", status=QualityMetricStatus.WARNING if report.orphan_consequence_rules else QualityMetricStatus.OK),
            QualityMetric(name="social_consequence_issues", value=len(issues), category="social_consequence_coverage", threshold=0, status=status),
        ],
        issues=issues,
        summary={
            "crimes_configured": report.crimes_configured,
            "crimes_triggered": report.crimes_triggered,
            "witness_records_generated": report.witness_records_generated,
            "rumors_configured": report.rumors_configured,
            "rumors_created": report.rumors_created,
            "rumors_propagated": report.rumors_propagated,
            "faction_reputation_changes": report.faction_reputation_changes,
            "npc_reactions_triggered": report.npc_reactions_triggered,
            "duplicate_consequences_prevented": report.duplicate_consequences_prevented,
            "orphan_consequence_rules": report.orphan_consequence_rules,
            "issue_count": len(issues),
            "blockers": blocker_count,
            "errors": error_count,
            "warnings": warning_count,
        },
        recommended_actions=_recommended_actions(error_count, warning_count),
    )


def _detect_rumor_reference_issues(report: SocialConsequenceCoverageReport, content: _SocialContent) -> None:
    facts = content.fact_by_id
    faction_ids = content.faction_ids
    for rumor in sorted(content.rumors, key=lambda item: str(item.get("id", ""))):
        rumor_id = str(rumor.get("id", ""))
        fact_id = rumor.get("fact_id")
        if fact_id and str(fact_id) not in facts:
            report.missing_rumor_fact_issues.append(
                _rumor_issue(
                    rumor=rumor,
                    code="rumor_missing_fact",
                    severity=QualityIssueSeverity.ERROR,
                    message="Rumor references a missing fact id.",
                    safe_details={"fact_id": str(fact_id)},
                    path=f"rumors.{rumor_id}.fact_id",
                )
            )
        elif fact_id:
            fact = facts[str(fact_id)]
            if _is_hidden_fact(fact) and _rumor_reveals_fact_text(rumor, fact):
                report.hidden_fact_leakage_risks.append(
                    _hidden_fact_issue(
                        rumor=rumor,
                        fact=fact,
                        code="rumor_hidden_fact_text_leakage",
                        severity=QualityIssueSeverity.WARNING,
                        message="Rumor player-facing text appears to contain hidden fact text.",
                        path=f"rumors.{rumor_id}.text_for_player",
                    )
                )

        for faction_id in _string_list(rumor.get("known_by_factions")):
            if faction_id not in faction_ids:
                report.missing_faction_effect_issues.append(
                    _rumor_issue(
                        rumor=rumor,
                        code="rumor_missing_faction_effect",
                        severity=QualityIssueSeverity.ERROR,
                        message="Rumor or reputation consequence references a missing faction.",
                        safe_details={"faction_id": faction_id},
                        path=f"rumors.{rumor_id}.known_by_factions",
                    )
                )


def _detect_untriggerable_consequences(report: SocialConsequenceCoverageReport, content: _SocialContent) -> None:
    npc_ids = content.npc_ids
    faction_ids = content.faction_ids
    for rumor in sorted(content.rumors, key=lambda item: str(item.get("id", ""))):
        rumor_id = str(rumor.get("id", ""))
        known_npcs = [npc_id for npc_id in _string_list(rumor.get("known_by_npcs")) if npc_id in npc_ids]
        known_factions = [faction_id for faction_id in _string_list(rumor.get("known_by_factions")) if faction_id in faction_ids]
        if not known_npcs and not known_factions and not bool(rumor.get("known_by_player")) and not rumor.get("source_event_id"):
            report.untriggerable_consequence_issues.append(
                _rumor_issue(
                    rumor=rumor,
                    code="rumor_consequence_never_triggerable",
                    severity=QualityIssueSeverity.WARNING,
                    message="Rumor has no valid initial knower, faction, player visibility, or source event.",
                    safe_details={},
                    path=f"rumors.{rumor_id}",
                )
            )


def _detect_duplicate_consequence_risks(report: SocialConsequenceCoverageReport, content: _SocialContent) -> None:
    seen_ids: dict[str, int] = {}
    seen_signatures: dict[tuple[str, str, tuple[str, ...]], int] = {}
    for rumor in content.rumors:
        rumor_id = str(rumor.get("id", ""))
        seen_ids[rumor_id] = seen_ids.get(rumor_id, 0) + 1
        signature = (
            str(rumor.get("fact_id", "")),
            str(rumor.get("text_for_player") or rumor.get("text") or ""),
            tuple(sorted(_string_list(rumor.get("tags")))),
        )
        seen_signatures[signature] = seen_signatures.get(signature, 0) + 1

    for rumor in sorted(content.rumors, key=lambda item: str(item.get("id", ""))):
        rumor_id = str(rumor.get("id", ""))
        signature = (
            str(rumor.get("fact_id", "")),
            str(rumor.get("text_for_player") or rumor.get("text") or ""),
            tuple(sorted(_string_list(rumor.get("tags")))),
        )
        if seen_ids.get(rumor_id, 0) > 1:
            report.duplicate_consequence_risks.append(
                _rumor_issue(
                    rumor=rumor,
                    code="duplicate_consequence_id",
                    severity=QualityIssueSeverity.WARNING,
                    message="Duplicate rumor/consequence id may cause repeated or overwritten social consequences.",
                    safe_details={},
                    path=f"rumors.{rumor_id}.id",
                )
            )
        elif seen_signatures.get(signature, 0) > 1 and "dedupe_key" not in _string_list(rumor.get("tags")):
            report.duplicate_consequence_risks.append(
                _rumor_issue(
                    rumor=rumor,
                    code="repeated_consequence_without_dedupe_key",
                    severity=QualityIssueSeverity.WARNING,
                    message="Multiple social consequences share the same signature without a dedupe_key tag.",
                    safe_details={},
                    path=f"rumors.{rumor_id}.tags",
                )
            )


def _observe_event_coverage(report: SocialConsequenceCoverageReport, events: list[Event]) -> None:
    for event in events:
        if event.action_type in {"crime_consequence", "crime", "theft", "assault", "murder"}:
            report.crimes_triggered += 1
        if event.action_type == "rumor_spread":
            report.rumors_propagated += 1
        if event.action_type == "npc_reaction":
            report.npc_reactions_triggered += 1
        if event.action_type == "faction_reputation_changed":
            report.faction_reputation_changes += 1
        for delta in event.state_deltas:
            path = delta.path
            source = delta.metadata.get("source", "")
            event_type = delta.metadata.get("event_type", "")
            if path.startswith("witnesses."):
                report.witness_records_generated += 1
            if path.startswith("rumors.") and (delta.operation == "set" or source == "rumor"):
                report.rumors_created += 1
            if source == "rumor_propagation":
                report.rumors_propagated += 1
            if path.startswith("factions.") and ("reputation" in path or event_type == "faction_reputation_changed"):
                report.faction_reputation_changes += 1
            if source in {"npc_reaction", "reaction"}:
                report.npc_reactions_triggered += 1
            if path.startswith("social_flags.") and ("processed" in path or source in {"social_consequence_tick", "faction_conflict"}):
                report.duplicate_consequences_prevented += 1


def _events_from_playtests(playtest_reports: list[PlaytestReport]) -> list[Event]:
    events: list[Event] = []
    for report in playtest_reports:
        for action in report.actions_taken:
            if action.action_type not in SOCIAL_ACTION_TYPES:
                continue
            events.append(
                Event(
                    event_id=action.event_id or f"playtest:{report.seed}:{action.step}",
                    turn=action.turn_after,
                    actor_id="playtest",
                    action_type=action.action_type,
                    result=action.result,
                    visible_to_player=False,
                    allow_empty_delta=True,
                )
            )
    return events


def _events_from_scenarios(scenario_reports: list[PlaytestScenarioReport]) -> list[Event]:
    return _events_from_playtests([scenario.playtest_report for scenario in scenario_reports])


def _configured_crime_count(rumors: list[dict[str, Any]]) -> int:
    return sum(1 for rumor in rumors if set(_string_list(rumor.get("tags"))).intersection(CRIME_TAGS))


def _hidden_fact_issue(
    *,
    rumor: dict[str, Any],
    fact: dict[str, Any],
    code: str,
    severity: QualityIssueSeverity,
    message: str,
    path: str,
) -> QualityIssue:
    rumor_id = str(rumor.get("id", ""))
    fact_id = str(fact.get("id", ""))
    return QualityIssue(
        id=f"social_consequence_coverage:{rumor_id}:{code}",
        severity=severity,
        category="social_consequence_coverage",
        file="rumors.yaml",
        path=path,
        entity_id=rumor_id,
        message=message,
        safe_details={"code": code, "fact_id": fact_id},
        hidden_details_debug_only={"fact_id": fact_id, "fact_text": fact.get("text"), "path": path},
    )


def _rumor_issue(
    *,
    rumor: dict[str, Any],
    code: str,
    severity: QualityIssueSeverity,
    message: str,
    safe_details: dict[str, Any],
    path: str,
) -> QualityIssue:
    rumor_id = str(rumor.get("id", ""))
    return QualityIssue(
        id=f"social_consequence_coverage:{rumor_id}:{code}",
        severity=severity,
        category="social_consequence_coverage",
        file="rumors.yaml",
        path=path,
        entity_id=rumor_id,
        message=message,
        safe_details={"code": code, **safe_details},
    )


def _is_hidden_fact(fact: dict[str, Any]) -> bool:
    return str(fact.get("visibility", "hidden")).lower() in {"hidden", "discoverable"} and "player" not in _string_list(fact.get("known_by"))


def _rumor_reveals_fact_text(rumor: dict[str, Any], fact: dict[str, Any]) -> bool:
    fact_text = str(fact.get("text", "")).strip().lower()
    rumor_text = str(rumor.get("text_for_player") or rumor.get("text") or "").strip().lower()
    return bool(fact_text and rumor_text and fact_text in rumor_text)


def _read_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _read_yaml_list(path: Path, key: str) -> list[dict[str, Any]]:
    data = _read_yaml_file(path)
    values = data.get(key, []) if isinstance(data, dict) else []
    return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _recommended_actions(errors: int, warnings: int) -> list[str]:
    actions: list[str] = []
    if errors:
        actions.append("Fix missing fact and faction references before relying on social consequence coverage.")
    if warnings:
        actions.append("Review hidden fact rumor text, untriggerable consequences, and duplicate social consequence signatures.")
    return actions
