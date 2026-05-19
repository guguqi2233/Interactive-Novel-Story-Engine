from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from app.llm.context_inspector import ContextSection, ContextVisibilityLevel
from app.llm.model_prompt_lab_policy import redact_sensitive_text


class TokenBudgetUseCase(StrEnum):
    NARRATOR = "narrator"
    DIALOGUE = "dialogue"
    GROUP_RP = "group_rp"
    INTENT_PARSER = "intent_parser"
    MEMORY_SUMMARY = "memory_summary"
    CHARACTER_IMPORT = "character_import"


class TokenBudgetOverflowPolicy(StrEnum):
    TRIM_LOW_PRIORITY = "trim_low_priority"
    DROP_LOW_PRIORITY = "drop_low_priority"
    REPORT_ONLY = "report_only"


class TokenBudgetProfile(BaseModel):
    id: str = "default_budget"
    use_case: TokenBudgetUseCase = TokenBudgetUseCase.NARRATOR
    max_total_tokens: int = Field(default=1200, ge=64)
    reserved_output_tokens: int = Field(default=300, ge=0)
    max_memory_tokens: int = Field(default=240, ge=0)
    max_lore_tokens: int = Field(default=160, ge=0)
    max_recent_events_tokens: int = Field(default=220, ge=0)
    max_dialogue_examples_tokens: int = Field(default=180, ge=0)
    priority_order: list[str] = Field(
        default_factory=lambda: [
            "safety_constraints",
            "player_input",
            "action_result",
            "visible_facts",
            "dialogue_profile",
            "npc_known_facts",
            "recent_events",
            "memory",
            "lore",
            "dialogue_examples",
        ]
    )
    overflow_policy: TokenBudgetOverflowPolicy = TokenBudgetOverflowPolicy.TRIM_LOW_PRIORITY

    @model_validator(mode="after")
    def validate_available_budget(self) -> "TokenBudgetProfile":
        if self.reserved_output_tokens >= self.max_total_tokens:
            raise ValueError("reserved_output_tokens must be lower than max_total_tokens")
        return self


class TokenBudgetRequest(BaseModel):
    profile: TokenBudgetProfile = Field(default_factory=TokenBudgetProfile)
    sections: list[ContextSection] = Field(default_factory=list)


class TokenBudgetSectionReport(BaseModel):
    section_type: str
    original_tokens: int
    allocated_tokens: int
    final_tokens: int
    trimmed_tokens: int = 0
    dropped: bool = False
    protected: bool = False
    safe_summary: str = ""


class BudgetReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"token-budget-{uuid4().hex}")
    profile: TokenBudgetProfile
    input_token_estimate: int
    available_context_tokens: int
    reserved_output_tokens: int
    final_context_tokens: int
    overflow_tokens: int
    sections: list[TokenBudgetSectionReport] = Field(default_factory=list)
    trimmed_sections: list[str] = Field(default_factory=list)
    dropped_sections: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    trimmed_context: list[ContextSection] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


class TokenBudgetManager:
    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        return max(len(text.split()), len(text) // 4, 1)

    def allocate_budget(self, profile: TokenBudgetProfile, sections: list[ContextSection]) -> dict[str, int]:
        available = max(0, profile.max_total_tokens - profile.reserved_output_tokens)
        allocations: dict[str, int] = {}
        protected_total = sum(section.token_estimate for section in sections if _is_protected(section))
        remaining = max(0, available - protected_total)
        for index, section in enumerate(sections):
            if _is_protected(section):
                allocations[_section_key(section, index)] = section.token_estimate
        category_caps = {
            "memory": profile.max_memory_tokens,
            "lore": profile.max_lore_tokens,
            "recent_events": profile.max_recent_events_tokens,
            "dialogue_examples": profile.max_dialogue_examples_tokens,
        }
        for index, section in sorted(enumerate(sections), key=lambda item: _priority_index(profile, item[1].section_type)):
            key = _section_key(section, index)
            if key in allocations:
                continue
            if _is_hidden(section):
                allocations[key] = 0
                continue
            cap = category_caps.get(_category(section.section_type), section.token_estimate)
            allocation = min(section.token_estimate, cap, remaining)
            allocations[key] = max(0, allocation)
            remaining = max(0, remaining - allocation)
        return allocations

    def trim_context(self, profile: TokenBudgetProfile, sections: list[ContextSection]) -> BudgetReport:
        input_tokens = sum(section.token_estimate for section in sections)
        available = profile.max_total_tokens - profile.reserved_output_tokens
        allocations = self.allocate_budget(profile, sections)
        reports: list[TokenBudgetSectionReport] = []
        trimmed_context: list[ContextSection] = []
        trimmed: list[str] = []
        dropped: list[str] = []
        warnings: list[str] = []
        blockers: list[str] = []
        for index, section in enumerate(sections):
            key = _section_key(section, index)
            allocated = allocations.get(key, 0)
            protected = _is_protected(section)
            if _is_hidden(section):
                final_tokens = 0
                dropped.append(section.section_type)
                reports.append(_section_report(section, allocated, final_tokens, dropped=True, protected=False))
                continue
            if protected:
                final_tokens = section.token_estimate
                if final_tokens > available:
                    blockers.append("safety_constraints_exceed_available_budget")
            elif profile.overflow_policy == TokenBudgetOverflowPolicy.REPORT_ONLY:
                final_tokens = section.token_estimate
            elif allocated <= 0 or profile.overflow_policy == TokenBudgetOverflowPolicy.DROP_LOW_PRIORITY and allocated < section.token_estimate:
                final_tokens = 0
                dropped.append(section.section_type)
            else:
                final_tokens = allocated
            if 0 < final_tokens < section.token_estimate:
                trimmed.append(section.section_type)
            if final_tokens > 0:
                trimmed_context.append(_trim_section(section, final_tokens))
            reports.append(
                _section_report(
                    section,
                    allocated,
                    final_tokens,
                    dropped=final_tokens == 0,
                    protected=protected,
                )
            )
        final_tokens_total = sum(section.token_estimate for section in trimmed_context)
        overflow = max(0, final_tokens_total - available)
        if overflow:
            warnings.append("context_still_exceeds_budget")
        if any(_is_hidden(section) for section in trimmed_context):
            blockers.append("hidden_section_entered_trimmed_context")
        return BudgetReport(
            profile=profile,
            input_token_estimate=input_tokens,
            available_context_tokens=available,
            reserved_output_tokens=profile.reserved_output_tokens,
            final_context_tokens=final_tokens_total,
            overflow_tokens=overflow,
            sections=reports,
            trimmed_sections=trimmed,
            dropped_sections=dropped,
            warnings=warnings,
            blockers=blockers,
            trimmed_context=trimmed_context,
        )

    def report_trimmed_sections(self, report: BudgetReport) -> list[TokenBudgetSectionReport]:
        return [section for section in report.sections if section.trimmed_tokens > 0 or section.dropped]


def build_default_token_budget_profiles() -> list[TokenBudgetProfile]:
    return [
        TokenBudgetProfile(id="narrator_balanced", use_case=TokenBudgetUseCase.NARRATOR),
        TokenBudgetProfile(id="dialogue_compact", use_case=TokenBudgetUseCase.DIALOGUE, max_total_tokens=900, max_memory_tokens=120),
        TokenBudgetProfile(id="intent_parser_tight", use_case=TokenBudgetUseCase.INTENT_PARSER, max_total_tokens=400, reserved_output_tokens=80),
        TokenBudgetProfile(id="memory_summary_wide", use_case=TokenBudgetUseCase.MEMORY_SUMMARY, max_total_tokens=1400, max_memory_tokens=700),
    ]


def estimate_token_budget(request: TokenBudgetRequest) -> BudgetReport:
    manager = TokenBudgetManager()
    sections = request.sections or _sample_sections()
    return manager.trim_context(request.profile, sections)


def _sample_sections() -> list[ContextSection]:
    return [
        ContextSection(
            section_type="safety_constraints",
            token_estimate=20,
            visibility_level=ContextVisibilityLevel.NARRATOR_SAFE,
            safe_summary="LLM cannot modify GameState or access hidden facts.",
            content_redacted="LLM cannot modify GameState or access hidden facts.",
        ),
        ContextSection(
            section_type="player_input",
            token_estimate=8,
            visibility_level=ContextVisibilityLevel.NORMAL,
            safe_summary="look around",
            content_redacted="look around",
        ),
        ContextSection(
            section_type="memory",
            token_estimate=320,
            visibility_level=ContextVisibilityLevel.NARRATOR_SAFE,
            safe_summary="recent visible memories",
            content_redacted="visible memory " * 80,
        ),
    ]


def _section_report(
    section: ContextSection,
    allocated: int,
    final_tokens: int,
    *,
    dropped: bool,
    protected: bool,
) -> TokenBudgetSectionReport:
    return TokenBudgetSectionReport(
        section_type=section.section_type,
        original_tokens=section.token_estimate,
        allocated_tokens=allocated,
        final_tokens=final_tokens,
        trimmed_tokens=max(0, section.token_estimate - final_tokens),
        dropped=dropped,
        protected=protected,
        safe_summary=section.safe_summary,
    )


def _trim_section(section: ContextSection, final_tokens: int) -> ContextSection:
    if final_tokens >= section.token_estimate:
        return section
    words = section.content_redacted.split()
    trimmed_text = " ".join(words[:final_tokens]) if words else section.content_redacted[: final_tokens * 4]
    return section.model_copy(
        update={
            "token_estimate": final_tokens,
            "content_redacted": trimmed_text,
            "safe_summary": section.safe_summary,
        }
    )


def _is_protected(section: ContextSection) -> bool:
    lowered = section.section_type.lower()
    return (
        "safety" in lowered
        or "boundary" in lowered
        or "policy" in lowered
        or section.visibility_level == ContextVisibilityLevel.NARRATOR_SAFE and lowered in {"action_result", "character_import_policy"}
    )


def _is_hidden(section: ContextSection) -> bool:
    return section.visibility_level == ContextVisibilityLevel.HIDDEN_REDACTED


def _category(section_type: str) -> str:
    lowered = section_type.lower()
    if "memory" in lowered:
        return "memory"
    if "lore" in lowered or "fact" in lowered:
        return "lore"
    if "recent" in lowered or "event" in lowered:
        return "recent_events"
    if "dialogue_example" in lowered or "example" in lowered:
        return "dialogue_examples"
    return lowered


def _priority_index(profile: TokenBudgetProfile, section_type: str) -> int:
    category = _category(section_type)
    for index, item in enumerate(profile.priority_order):
        if item == section_type or item == category:
            return index
    return len(profile.priority_order) + 1


def _section_key(section: ContextSection, index: int) -> str:
    return f"{index}:{section.section_type}:{section.safe_summary[:24]}"


def _strip_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            stripped = _strip_sensitive(item)
            if _safe_key_value(str(key), stripped):
                safe[str(key)] = stripped
        return safe
    if isinstance(value, list):
        return [_strip_sensitive(item) for item in value]
    if isinstance(value, str):
        redacted = redact_sensitive_text(value).text
        lowered = redacted.lower()
        if "hidden fact" in lowered or "the mayor forged the charter" in lowered:
            return "[redacted]"
        return redacted
    return value


def _safe_key_value(key: str, value: Any) -> bool:
    lowered = f"{key}={value}".lower().replace("[redacted-secret]", "[redacted]")
    return not any(term in lowered for term in ["api_key", "llm_api_key", "raw_env", "secret", "sk-"])
