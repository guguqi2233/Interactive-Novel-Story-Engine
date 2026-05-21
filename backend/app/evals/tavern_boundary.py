from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.core.world_state import GameState
from app.platform.security import redact_text


class TavernBoundaryRule(StrEnum):
    NO_HIDDEN_FACT_PROMPT_LEAK = "no_hidden_fact_prompt_leak"
    NO_NPC_SECRET_LEAK = "no_npc_secret_leak"
    NO_PRIVATE_PERSONA_LEAK = "no_private_persona_leak"
    NO_DEBUG_MEMORY_LEAK = "no_debug_memory_leak"
    NO_RAW_STATE_DELTAS = "no_raw_state_deltas"
    NO_GAMESTATE_MUTATION = "no_gamestate_mutation"
    NO_WORLD_EVENT_FROM_RP = "no_world_event_from_rp"
    NO_PROPOSAL_APPLY = "no_proposal_apply"
    SAFE_TAVERN_CONTEXT = "safe_tavern_context"


class TavernBoundaryEvalCase(BaseModel):
    id: str
    rule: TavernBoundaryRule
    payload: dict[str, Any] = Field(default_factory=dict)
    forbidden_terms: list[str] = Field(default_factory=list)
    state_before: GameState | None = None
    state_after: GameState | None = None
    event_count_before: int = 0
    event_count_after: int = 0
    proposal_applied: bool = False
    should_pass: bool = False
    expected_issue_codes: list[str] = Field(default_factory=list)


class TavernBoundaryEvalResult(BaseModel):
    case_id: str
    passed: bool
    issue_codes: list[str] = Field(default_factory=list)
    safe_details: dict[str, str] = Field(default_factory=dict)


class TavernBoundaryEvalReport(BaseModel):
    total_cases: int
    failed: int
    results: list[TavernBoundaryEvalResult] = Field(default_factory=list)

    def model_dump_normal(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json")
        text = json.dumps(payload, ensure_ascii=False)
        return json.loads(redact_text(text))


def evaluate_tavern_boundary_case(case: TavernBoundaryEvalCase) -> TavernBoundaryEvalResult:
    serialized = json.dumps(case.payload, ensure_ascii=False, sort_keys=True).lower()
    issue_codes: list[str] = []
    if case.rule != TavernBoundaryRule.SAFE_TAVERN_CONTEXT:
        for term in case.forbidden_terms:
            if term and term.lower() in serialized:
                issue_codes.append(_issue_for_rule(case.rule))
                break
    if "state_delta" in serialized or "state_deltas" in serialized:
        issue_codes.append("raw_state_delta_leak")
    if case.state_before is not None and case.state_after is not None and case.state_before != case.state_after:
        issue_codes.append("direct_gamestate_mutation")
    if case.event_count_after > case.event_count_before:
        issue_codes.append("rp_message_became_world_event")
    if case.proposal_applied:
        issue_codes.append("proposal_applied_to_world")
    issue_codes = sorted(set(issue_codes))
    if case.should_pass:
        passed = not issue_codes
    else:
        passed = all(code in issue_codes for code in case.expected_issue_codes)
    return TavernBoundaryEvalResult(case_id=case.id, passed=passed, issue_codes=issue_codes, safe_details={"rule": case.rule.value})


def run_tavern_boundary_evals(cases: list[TavernBoundaryEvalCase]) -> TavernBoundaryEvalReport:
    results = [evaluate_tavern_boundary_case(case) for case in cases]
    return TavernBoundaryEvalReport(total_cases=len(cases), failed=sum(1 for result in results if not result.passed), results=results)


def run_default_tavern_boundary_evals() -> TavernBoundaryEvalReport:
    hidden = "hidden tavern boundary marker"
    cases = [
        TavernBoundaryEvalCase(
            id="safe_tavern_context",
            rule=TavernBoundaryRule.SAFE_TAVERN_CONTEXT,
            payload={"prompt": "A safe local RP context."},
            should_pass=True,
        ),
        TavernBoundaryEvalCase(
            id="hidden_fact_prompt_leak",
            rule=TavernBoundaryRule.NO_HIDDEN_FACT_PROMPT_LEAK,
            payload={"prompt": hidden},
            forbidden_terms=[hidden],
            expected_issue_codes=["hidden_fact_prompt_leak"],
        ),
    ]
    return run_tavern_boundary_evals(cases)


def _issue_for_rule(rule: TavernBoundaryRule) -> str:
    return {
        TavernBoundaryRule.NO_HIDDEN_FACT_PROMPT_LEAK: "hidden_fact_prompt_leak",
        TavernBoundaryRule.NO_NPC_SECRET_LEAK: "npc_secret_leak",
        TavernBoundaryRule.NO_PRIVATE_PERSONA_LEAK: "private_persona_leak",
        TavernBoundaryRule.NO_DEBUG_MEMORY_LEAK: "debug_memory_leak",
        TavernBoundaryRule.NO_RAW_STATE_DELTAS: "raw_state_delta_leak",
        TavernBoundaryRule.NO_GAMESTATE_MUTATION: "direct_gamestate_mutation",
        TavernBoundaryRule.NO_WORLD_EVENT_FROM_RP: "rp_message_became_world_event",
        TavernBoundaryRule.NO_PROPOSAL_APPLY: "proposal_applied_to_world",
        TavernBoundaryRule.SAFE_TAVERN_CONTEXT: "unexpected_tavern_boundary_issue",
    }[rule]
