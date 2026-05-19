from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


PromptDiffKind = Literal["prompt_profile_diff", "rp_prompt_profile_diff", "context_snapshot_diff", "prompt_template_diff"]


class PromptDiffRequest(BaseModel):
    diff_type: PromptDiffKind = "prompt_profile_diff"
    left: dict[str, Any] = Field(default_factory=dict)
    right: dict[str, Any] = Field(default_factory=dict)


class PromptDiffReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"prompt-diff-{uuid4().hex}")
    diff_type: PromptDiffKind
    added_sections: list[str] = Field(default_factory=list)
    removed_sections: list[str] = Field(default_factory=list)
    changed_sections: list[str] = Field(default_factory=list)
    safety_policy_changes: list[str] = Field(default_factory=list)
    token_delta: int = 0
    hidden_access_policy_changes: list[str] = Field(default_factory=list)
    state_modification_policy_changes: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json"))


def review_prompt_diff(request: PromptDiffRequest) -> PromptDiffReport:
    left = _strip_sensitive(request.left)
    right = _strip_sensitive(request.right)
    left_keys = set(left)
    right_keys = set(right)
    changed = sorted(key for key in left_keys & right_keys if left.get(key) != right.get(key))
    report = PromptDiffReport(
        diff_type=request.diff_type,
        added_sections=sorted(right_keys - left_keys),
        removed_sections=sorted(left_keys - right_keys),
        changed_sections=changed,
        token_delta=_estimate_tokens(right) - _estimate_tokens(left),
    )
    for key in changed:
        lowered = key.lower()
        if "hidden_fact_policy" in lowered:
            report.hidden_access_policy_changes.append(key)
            if _policy_relaxed(left.get(key), right.get(key)):
                report.blockers.append("hidden_fact_policy_relaxed")
        if "state_modification_policy" in lowered:
            report.state_modification_policy_changes.append(key)
            if _policy_relaxed(left.get(key), right.get(key)):
                report.blockers.append("state_modification_policy_relaxed")
        if "policy" in lowered or "safety" in lowered:
            report.safety_policy_changes.append(key)
    if not report.blockers and not (report.added_sections or report.removed_sections or report.changed_sections):
        report.warnings.append("no_prompt_diff_changes_detected")
    return report


def _policy_relaxed(left: Any, right: Any) -> bool:
    return str(left).lower() == "deny" and str(right).lower() != "deny"


def _estimate_tokens(value: Any) -> int:
    text = str(_strip_sensitive(value))
    return max(0, len(text) // 4)


def _strip_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _strip_sensitive(child) for key, child in value.items() if _safe_key(str(key))}
    if isinstance(value, list):
        return [_strip_sensitive(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if "sk-" in lowered or "api_key" in lowered or "hidden fact" in lowered or "npc secret" in lowered:
            return "[redacted]"
        return value
    return value


def _safe_key(key: str) -> bool:
    lowered = key.lower()
    return "api_key" not in lowered and "secret" not in lowered and "raw_env" not in lowered
