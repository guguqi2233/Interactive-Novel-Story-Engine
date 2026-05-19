from __future__ import annotations

import re
from enum import StrEnum
from hashlib import sha256
from typing import Iterable

from pydantic import BaseModel, Field

from app.core.world_state import ActorCondition, FactVisibility, GameState
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.roleplay.boundary import RoleplayOutputCandidate


class RPConsistencySeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class RPConsistencyDecision(StrEnum):
    ACCEPT = "accept"
    REQUEST_RETRY = "request_retry"
    REJECT = "reject"
    FALLBACK_SAFE_SUMMARY = "fallback_safe_summary"


class RPConsistencyIssue(BaseModel):
    code: str
    severity: RPConsistencySeverity = RPConsistencySeverity.ERROR
    message: str
    safe_details: dict[str, str] = Field(default_factory=dict)


class RPConsistencyReport(BaseModel):
    ok: bool
    decision: RPConsistencyDecision = RPConsistencyDecision.ACCEPT
    issues: list[RPConsistencyIssue] = Field(default_factory=list)
    fallback_text: str = ""


class RPOutputConsistencyChecker:
    """Deterministic RP output guard.

    The checker is deliberately conservative and read-only. It does not judge
    world outcomes. It flags text that claims facts or state changes that the
    rule engine did not authorize, or that mentions information outside the
    current visibility/NPC knowledge boundary.
    """

    _debug_markers = (
        "state_delta",
        "state_deltas",
        "raw gamestate",
        "debug_only",
        "debug memory",
        "api key",
        "sk-",
    )
    _success_words = ("succeeded", "successfully", "worked", "opened", "unlocked", "completed")
    _failure_words = ("failed", "could not", "cannot", "blocked", "stuck", "impossible")
    _relationship_change_markers = (
        "trust increased",
        "trust decreased",
        "affinity increased",
        "affinity decreased",
        "relationship increased",
        "relationship decreased",
        "relationship score",
        "romance increased",
        "friendship level",
    )
    _quest_completion_markers = (
        "quest complete",
        "quest completed",
        "completed the quest",
        "objective complete",
        "objective completed",
        "quest status: completed",
    )

    def check(
        self,
        *,
        generated_text: str,
        state: GameState | None = None,
        dialogue_context: object | None = None,
        action_result: ActionResult | None = None,
        visible_facts: Iterable[str] | None = None,
        npc_known_facts: Iterable[str] | None = None,
        forbidden_hidden_terms: Iterable[str] | None = None,
        forbidden_hidden_ids: Iterable[str] | None = None,
        allowed_flavor_terms: Iterable[str] | None = None,
        speaker_npc_id: str | None = None,
        candidate: RoleplayOutputCandidate | None = None,
    ) -> RPConsistencyReport:
        text = generated_text or ""
        lower_text = text.lower()
        visible_fact_ids = set(visible_facts or [])
        npc_known_fact_ids = set(npc_known_facts or _context_known_facts(dialogue_context))
        allowed_flavor = {term.lower() for term in allowed_flavor_terms or [] if term}
        issues: list[RPConsistencyIssue] = []

        self._check_raw_debug_text(lower_text, issues)
        self._check_candidate_declarations(candidate, issues)
        self._check_forbidden_hidden_terms(
            lower_text,
            forbidden_hidden_terms or [],
            forbidden_hidden_ids or [],
            issues,
        )
        if state is not None:
            self._check_state_fact_mentions(
                state,
                lower_text,
                visible_fact_ids,
                npc_known_fact_ids,
                allowed_flavor,
                issues,
            )
            self._check_invented_entities(state, text, lower_text, allowed_flavor, issues)
            self._check_dead_speaker(state, speaker_npc_id or _context_focus_npc_id(dialogue_context), text, issues)
        self._check_action_result(action_result, lower_text, issues)
        self._check_unauthorized_relationship_change(action_result, lower_text, issues)
        self._check_unauthorized_quest_completion(action_result, lower_text, issues)
        return _report_from_issues(issues)

    def fallback_safe_summary(self, report: RPConsistencyReport) -> str:
        if report.fallback_text:
            return report.fallback_text
        if not report.issues:
            return ""
        return _safe_fallback_text(report.issues)

    def _check_raw_debug_text(self, lower_text: str, issues: list[RPConsistencyIssue]) -> None:
        for marker in self._debug_markers:
            if marker in lower_text:
                issues.append(
                    RPConsistencyIssue(
                        code="raw_debug_or_state_delta_leakage",
                        severity=RPConsistencySeverity.BLOCKER,
                        message="RP output included raw debug/state-delta or sensitive configuration markers.",
                        safe_details={"marker": _redacted_term_marker(marker)},
                    )
                )

    def _check_candidate_declarations(
        self,
        candidate: RoleplayOutputCandidate | None,
        issues: list[RPConsistencyIssue],
    ) -> None:
        if candidate is None:
            return
        for fact_id in candidate.proposed_fact_creations:
            issues.append(
                RPConsistencyIssue(
                    code="prohibited_fact_creation",
                    severity=RPConsistencySeverity.ERROR,
                    message="RP output attempted to create an authoritative fact.",
                    safe_details={"candidate_id": fact_id},
                )
            )
        for change in candidate.proposed_state_changes:
            issues.append(
                RPConsistencyIssue(
                    code="prohibited_state_change",
                    severity=RPConsistencySeverity.ERROR,
                    message="RP output attempted to declare a canonical state change.",
                    safe_details={"candidate_change": change},
                )
            )

    def _check_forbidden_hidden_terms(
        self,
        lower_text: str,
        forbidden_hidden_terms: Iterable[str],
        forbidden_hidden_ids: Iterable[str],
        issues: list[RPConsistencyIssue],
    ) -> None:
        for term in forbidden_hidden_terms:
            normalized = term.lower()
            if normalized and normalized in lower_text:
                issues.append(
                    RPConsistencyIssue(
                        code="hidden_fact_leakage",
                        severity=RPConsistencySeverity.BLOCKER,
                        message="RP output mentioned a forbidden hidden term.",
                        safe_details={"term": _redacted_term_marker(term)},
                    )
                )
        for term in forbidden_hidden_ids:
            normalized = term.lower()
            if normalized and normalized in lower_text:
                issues.append(
                    RPConsistencyIssue(
                        code="hidden_fact_leakage",
                        severity=RPConsistencySeverity.BLOCKER,
                        message="RP output mentioned a forbidden hidden id.",
                        safe_details={"id": _redacted_term_marker(term)},
                    )
                )

    def _check_state_fact_mentions(
        self,
        state: GameState,
        lower_text: str,
        visible_fact_ids: set[str],
        npc_known_fact_ids: set[str],
        allowed_flavor: set[str],
        issues: list[RPConsistencyIssue],
    ) -> None:
        visible_ids = set(state.player_visible_facts) | visible_fact_ids
        for fact_id, fact in sorted(state.facts.items()):
            terms = {fact_id}
            if fact.text:
                terms.add(fact.text)
            if not _contains_any_unallowed(lower_text, terms, allowed_flavor):
                continue
            player_allowed = (
                fact_id in visible_ids
                or fact.visibility == FactVisibility.PUBLIC
                or fact.public
            )
            npc_allowed = (
                not npc_known_fact_ids
                or fact_id in npc_known_fact_ids
                or fact.visibility == FactVisibility.PUBLIC
                or fact.public
            )
            if not player_allowed:
                issues.append(
                    RPConsistencyIssue(
                        code="hidden_fact_leakage",
                        severity=RPConsistencySeverity.BLOCKER,
                        message="RP output referenced a fact outside player visibility.",
                        safe_details={"fact_id": fact_id},
                    )
                )
            if not npc_allowed:
                issues.append(
                    RPConsistencyIssue(
                        code="npc_unknown_fact_mention",
                        severity=RPConsistencySeverity.ERROR,
                        message="RP output made an NPC mention a fact outside NPC knowledge.",
                        safe_details={"fact_id": fact_id},
                    )
                )

    def _check_invented_entities(
        self,
        state: GameState,
        text: str,
        lower_text: str,
        allowed_flavor: set[str],
        issues: list[RPConsistencyIssue],
    ) -> None:
        known_items = set(state.objects)
        known_npcs = set(state.npcs)
        known_locations = set(state.locations)
        for entity_type, known, code in (
            ("item", known_items, "invented_key_item"),
            ("npc", known_npcs, "invented_key_npc"),
            ("location", known_locations, "invented_location"),
        ):
            for value in _explicit_entity_mentions(text, entity_type):
                if value not in known and value.lower() not in allowed_flavor:
                    issues.append(
                        RPConsistencyIssue(
                            code=code,
                            severity=RPConsistencySeverity.ERROR,
                            message=f"RP output referenced an unknown {entity_type} id.",
                            safe_details={f"{entity_type}_id": value},
                        )
                    )
        if _claims_unknown_key_item(lower_text, known_items, allowed_flavor):
            issues.append(
                RPConsistencyIssue(
                    code="invented_key_item",
                    severity=RPConsistencySeverity.ERROR,
                    message="RP output appeared to grant or reveal an unknown key item.",
                    safe_details={"pattern": "unknown_key_item_claim"},
                )
            )

    def _check_dead_speaker(
        self,
        state: GameState,
        speaker_npc_id: str | None,
        text: str,
        issues: list[RPConsistencyIssue],
    ) -> None:
        if not speaker_npc_id or not text.strip():
            return
        npc = state.npcs.get(speaker_npc_id)
        if npc is None:
            return
        if not npc.alive or npc.condition in {ActorCondition.DEAD, ActorCondition.INCAPACITATED}:
            issues.append(
                RPConsistencyIssue(
                    code="dead_or_incapacitated_npc_speaking",
                    severity=RPConsistencySeverity.ERROR,
                    message="RP output gave speech to a dead or incapacitated NPC.",
                    safe_details={"npc_id": speaker_npc_id},
                )
            )

    def _check_action_result(
        self,
        action_result: ActionResult | None,
        lower_text: str,
        issues: list[RPConsistencyIssue],
    ) -> None:
        if action_result is None:
            return
        if action_result.success_level in {SuccessLevel.FAILURE, SuccessLevel.INVALID}:
            if any(word in lower_text for word in self._success_words):
                issues.append(
                    RPConsistencyIssue(
                        code="contradiction_with_action_result",
                        severity=RPConsistencySeverity.ERROR,
                        message="RP output described a failed action as successful.",
                        safe_details={"action_result": action_result.success_level.value},
                    )
                )
        if action_result.success_level == SuccessLevel.SUCCESS:
            if any(word in lower_text for word in self._failure_words):
                issues.append(
                    RPConsistencyIssue(
                        code="contradiction_with_action_result",
                        severity=RPConsistencySeverity.WARNING,
                        message="RP output described a successful action as failed.",
                        safe_details={"action_result": action_result.success_level.value},
                    )
                )

    def _check_unauthorized_relationship_change(
        self,
        action_result: ActionResult | None,
        lower_text: str,
        issues: list[RPConsistencyIssue],
    ) -> None:
        if not any(marker in lower_text for marker in self._relationship_change_markers):
            return
        if _has_authorized_delta(action_result, "relationships."):
            return
        issues.append(
            RPConsistencyIssue(
                code="unauthorized_relationship_change",
                severity=RPConsistencySeverity.ERROR,
                message="RP output described a relationship value change without a matching StateDelta.",
                safe_details={"requires": "relationship_state_delta"},
            )
        )

    def _check_unauthorized_quest_completion(
        self,
        action_result: ActionResult | None,
        lower_text: str,
        issues: list[RPConsistencyIssue],
    ) -> None:
        if not any(marker in lower_text for marker in self._quest_completion_markers):
            return
        if _has_authorized_delta(action_result, "quests."):
            return
        issues.append(
            RPConsistencyIssue(
                code="unauthorized_quest_completion",
                severity=RPConsistencySeverity.ERROR,
                message="RP output declared quest progress without a matching StateDelta.",
                safe_details={"requires": "quest_state_delta"},
            )
        )


def _report_from_issues(issues: list[RPConsistencyIssue]) -> RPConsistencyReport:
    if not issues:
        return RPConsistencyReport(ok=True)
    severities = {issue.severity for issue in issues}
    if RPConsistencySeverity.BLOCKER in severities:
        decision = RPConsistencyDecision.FALLBACK_SAFE_SUMMARY
    elif RPConsistencySeverity.ERROR in severities:
        decision = RPConsistencyDecision.REQUEST_RETRY
    else:
        decision = RPConsistencyDecision.ACCEPT
    return RPConsistencyReport(
        ok=decision == RPConsistencyDecision.ACCEPT,
        decision=decision,
        issues=issues,
        fallback_text=_safe_fallback_text(issues),
    )


def _safe_fallback_text(issues: list[RPConsistencyIssue]) -> str:
    issue_codes = sorted({issue.code for issue in issues})
    return (
        "The roleplay response was withheld because it conflicted with the "
        f"world boundary ({', '.join(issue_codes)}). The scene remains unchanged."
    )


def _redacted_term_marker(term: str) -> str:
    digest = sha256(term.encode("utf-8")).hexdigest()[:12]
    return f"[redacted:{digest}]"


def _contains_any_unallowed(lower_text: str, terms: set[str], allowed_flavor: set[str]) -> bool:
    for term in terms:
        normalized = term.lower()
        if normalized and normalized not in allowed_flavor and normalized in lower_text:
            return True
    return False


def _explicit_entity_mentions(text: str, entity_type: str) -> list[str]:
    pattern = re.compile(rf"\b{re.escape(entity_type)}:([A-Za-z0-9_-]+)\b")
    return sorted(set(pattern.findall(text)))


def _claims_unknown_key_item(lower_text: str, known_items: set[str], allowed_flavor: set[str]) -> bool:
    if not any(phrase in lower_text for phrase in ("you receive", "you gain", "hands you", "gives you", "reveals the key")):
        return False
    if any(item_id.lower() in lower_text for item_id in known_items):
        return False
    if any(term in lower_text for term in allowed_flavor):
        return False
    return any(token in lower_text for token in (" key", "artifact", "amulet", "quest item", "seal"))


def _has_authorized_delta(action_result: ActionResult | None, path_prefix: str) -> bool:
    if action_result is None:
        return False
    return any(delta.path.startswith(path_prefix) for delta in action_result.state_deltas)


def _context_known_facts(dialogue_context: object | None) -> list[str]:
    if dialogue_context is None:
        return []
    value = getattr(dialogue_context, "npc_known_facts", [])
    return [str(item) for item in value]


def _context_focus_npc_id(dialogue_context: object | None) -> str | None:
    if dialogue_context is None:
        return None
    session = getattr(dialogue_context, "session", None)
    value = getattr(session, "focus_npc_id", None)
    return str(value) if value else None
