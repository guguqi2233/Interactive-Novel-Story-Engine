from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.core.world_state import FactState, FactVisibility, GameState, LocationState, NPCState
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.knowledge import get_npc_context_for_dialogue
from app.engine.rules.visibility import get_visible_facts
from app.llm.context_builder import MemoryContextBuilder, build_npc_dialogue_profile_context
from app.llm.memory_store import InMemoryMemoryStore, MemoryRecord, MemoryVisibility
from app.llm.model_prompt_lab_policy import redact_sensitive_text


class ContextInspectType(StrEnum):
    NARRATOR = "narrator"
    DIALOGUE = "dialogue"
    GROUP_RP = "group_rp"
    INTENT_PARSER = "intent_parser"
    MEMORY_SUMMARY = "memory_summary"
    CHARACTER_IMPORT = "character_import"


class ContextVisibilityLevel(StrEnum):
    NORMAL = "normal"
    NARRATOR_SAFE = "narrator_safe"
    NPC_KNOWN = "npc_known"
    DEBUG_ONLY = "debug_only"
    HIDDEN_REDACTED = "hidden_redacted"


class ContextSection(BaseModel):
    section_type: str
    token_estimate: int
    visibility_level: ContextVisibilityLevel
    safe_summary: str
    content_redacted: str
    excluded_reasons: list[str] = Field(default_factory=list)


class ContextSnapshot(BaseModel):
    snapshot_id: str = Field(default_factory=lambda: f"context-snapshot-{uuid4().hex}")
    context_type: ContextInspectType
    total_token_estimate: int = 0
    sections: list[ContextSection] = Field(default_factory=list)
    raw_prompt_redacted: str | None = None
    raw_prompt_included: bool = False

    def model_dump_safe(self) -> dict[str, Any]:
        return _strip_sensitive(self.model_dump(mode="json", exclude_none=True))


class ContextInspectRequest(BaseModel):
    context_type: ContextInspectType = ContextInspectType.NARRATOR
    state: GameState | None = None
    memories: list[MemoryRecord] = Field(default_factory=list)
    actor_id: str = "player"
    location_id: str = "start"
    npc_id: str | None = None
    player_input: str = "look around"
    include_debug_raw: bool = False
    max_raw_chars: int = Field(default=500, ge=80, le=2000)


def inspect_context(request: ContextInspectRequest) -> ContextSnapshot:
    state = request.state or _default_state(request.location_id, request.npc_id)
    sections: list[ContextSection] = []
    if request.context_type == ContextInspectType.NARRATOR:
        sections.extend(_narrator_sections(request, state))
    elif request.context_type == ContextInspectType.DIALOGUE:
        sections.extend(_dialogue_sections(request, state))
    elif request.context_type == ContextInspectType.GROUP_RP:
        sections.extend(_group_rp_sections(request, state))
    elif request.context_type == ContextInspectType.INTENT_PARSER:
        sections.extend(_intent_sections(request, state))
    elif request.context_type == ContextInspectType.MEMORY_SUMMARY:
        sections.extend(_memory_summary_sections(request, state))
    elif request.context_type == ContextInspectType.CHARACTER_IMPORT:
        sections.extend(_character_import_sections(request, state))
    raw_prompt = _raw_prompt(sections) if request.include_debug_raw else None
    snapshot = ContextSnapshot(
        context_type=request.context_type,
        sections=sections,
        total_token_estimate=sum(section.token_estimate for section in sections),
        raw_prompt_redacted=_redact(raw_prompt)[: request.max_raw_chars] if raw_prompt else None,
        raw_prompt_included=bool(raw_prompt),
    )
    return snapshot


def _narrator_sections(request: ContextInspectRequest, state: GameState) -> list[ContextSection]:
    visible = get_visible_facts(state, request.actor_id, request.location_id)
    action_result = ActionResult(
        success_level=SuccessLevel.SUCCESS,
        reason="Inspector visible action result.",
        visible_facts=visible,
    )
    memory_context = MemoryContextBuilder(InMemoryMemoryStore(request.memories)).build(
        state,
        actor_id=request.actor_id,
        current_location=request.location_id,
        action_result=action_result,
        visible_facts=visible,
        current_npc_id=request.npc_id,
    )
    sections = [
        _section("player_input", request.player_input, ContextVisibilityLevel.NORMAL),
        _section("visible_facts", ", ".join(visible), ContextVisibilityLevel.NORMAL),
        _section("action_result", action_result.reason, ContextVisibilityLevel.NARRATOR_SAFE),
    ]
    sections.extend(
        _memory_section(memory, ContextVisibilityLevel.NARRATOR_SAFE)
        for memory in memory_context.narrator_safe_memories
    )
    sections.extend(_hidden_fact_sections(state, visible, npc_id=request.npc_id))
    sections.extend(
        _excluded_section("excluded_memory", reason.memory_id, reason.reason)
        for reason in memory_context.excluded_memory_reasons
    )
    return sections


def _dialogue_sections(request: ContextInspectRequest, state: GameState) -> list[ContextSection]:
    npc_id = request.npc_id or next(iter(state.npcs), "")
    if not npc_id or npc_id not in state.npcs:
        return [_excluded_section("dialogue_context", npc_id or "missing", "npc_missing")]
    context = get_npc_context_for_dialogue(state, npc_id)
    profile = build_npc_dialogue_profile_context(state, npc_id)
    sections = [
        _section("dialogue_profile", profile.model_dump_json(exclude_none=True), ContextVisibilityLevel.NPC_KNOWN),
        _section("npc_known_facts", ", ".join(context.knowledge), ContextVisibilityLevel.NPC_KNOWN),
        _section("npc_mood", context.mood, ContextVisibilityLevel.NPC_KNOWN),
    ]
    known = set(context.knowledge)
    for fact_id, fact in sorted(state.facts.items()):
        if fact_id not in known and fact.visibility != FactVisibility.PUBLIC:
            sections.append(_excluded_section("npc_unknown_fact", fact_id, f"npc_unknown_fact:{fact_id}"))
    return sections


def _group_rp_sections(request: ContextInspectRequest, state: GameState) -> list[ContextSection]:
    sections = [_section("group_rp_participants", ", ".join(sorted(state.npcs)), ContextVisibilityLevel.NPC_KNOWN)]
    for npc_id in sorted(state.npcs):
        sections.append(_section("participant_context", f"{npc_id}: {state.npcs[npc_id].mood}", ContextVisibilityLevel.NPC_KNOWN))
    sections.extend(_hidden_fact_sections(state, get_visible_facts(state, request.actor_id, request.location_id), npc_id=request.npc_id))
    return sections


def _intent_sections(request: ContextInspectRequest, state: GameState) -> list[ContextSection]:
    visible = get_visible_facts(state, request.actor_id, request.location_id)
    return [
        _section("intent_input", request.player_input, ContextVisibilityLevel.NORMAL),
        _section("intent_visible_refs", ", ".join(visible), ContextVisibilityLevel.NORMAL),
    ] + _hidden_fact_sections(state, visible, npc_id=request.npc_id)


def _memory_summary_sections(request: ContextInspectRequest, state: GameState) -> list[ContextSection]:
    sections: list[ContextSection] = []
    for memory in request.memories:
        if memory.visibility in {MemoryVisibility.HIDDEN, MemoryVisibility.DEBUG_ONLY}:
            sections.append(_excluded_section("memory_summary_excluded", memory.id, f"visibility:{memory.visibility}"))
        else:
            sections.append(_memory_section(memory, ContextVisibilityLevel.NARRATOR_SAFE))
    sections.extend(_hidden_fact_sections(state, get_visible_facts(state, request.actor_id, request.location_id), npc_id=request.npc_id))
    return sections


def _character_import_sections(request: ContextInspectRequest, state: GameState) -> list[ContextSection]:
    _ = state
    return [
        _section("character_import_input", request.player_input, ContextVisibilityLevel.NORMAL),
        _section("character_import_policy", "external card text is untrusted and style-only until validated", ContextVisibilityLevel.NARRATOR_SAFE),
    ]


def _hidden_fact_sections(state: GameState, visible_fact_ids: list[str], *, npc_id: str | None) -> list[ContextSection]:
    visible_set = set(visible_fact_ids)
    sections: list[ContextSection] = []
    for fact_id, fact in sorted(state.facts.items()):
        if fact.visibility == FactVisibility.PUBLIC or fact_id in visible_set:
            continue
        reason = f"hidden_fact:{fact_id}"
        if npc_id and npc_id in state.npcs and fact_id not in state.npcs[npc_id].knowledge and fact_id not in state.npc_knowledge.get(npc_id, set()):
            reason = f"npc_unknown_fact:{fact_id}"
        sections.append(
            ContextSection(
                section_type="fact_excluded",
                token_estimate=1,
                visibility_level=ContextVisibilityLevel.HIDDEN_REDACTED,
                safe_summary=f"{fact_id} redacted",
                content_redacted="[redacted:hidden]",
                excluded_reasons=[reason],
            )
        )
    return sections


def _memory_section(memory: MemoryRecord, visibility: ContextVisibilityLevel) -> ContextSection:
    return _section(
        "memory",
        memory.content,
        visibility,
        safe_summary=f"{memory.id}; tags={','.join(memory.tags[:4])}; facts={','.join(memory.fact_ids[:4])}",
    )


def _excluded_section(section_type: str, ref_id: str, reason: str) -> ContextSection:
    return ContextSection(
        section_type=section_type,
        token_estimate=1,
        visibility_level=ContextVisibilityLevel.HIDDEN_REDACTED if "hidden" in reason or "unknown" in reason else ContextVisibilityLevel.DEBUG_ONLY,
        safe_summary=f"{ref_id} excluded",
        content_redacted="[redacted]",
        excluded_reasons=[reason],
    )


def _section(
    section_type: str,
    content: str,
    visibility: ContextVisibilityLevel,
    *,
    safe_summary: str | None = None,
) -> ContextSection:
    redacted = _redact(content)
    return ContextSection(
        section_type=section_type,
        token_estimate=_estimate_tokens(redacted),
        visibility_level=visibility,
        safe_summary=safe_summary or redacted[:120],
        content_redacted=redacted[:500],
        excluded_reasons=[],
    )


def _raw_prompt(sections: list[ContextSection]) -> str:
    return "\n".join(f"[{section.visibility_level}] {section.section_type}: {section.content_redacted}" for section in sections)


def _redact(text: str | None) -> str:
    if not text:
        return ""
    redacted = redact_sensitive_text(text).text
    lowered = redacted.lower()
    if "hidden fact text" in lowered or "the mayor forged the charter" in lowered:
        return "[redacted]"
    return redacted


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
        return _redact(value)
    return value


def _safe_key_value(key: str, value: Any) -> bool:
    lowered = f"{key}={value}".lower().replace("[redacted-secret]", "[redacted]")
    return not any(term in lowered for term in ["api_key", "llm_api_key", "raw_env", "secret", "sk-", "raw gamestate"])


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(len(text.split()), len(text) // 4, 1)


def _default_state(location_id: str, npc_id: str | None) -> GameState:
    npc = npc_id or "npc_sample"
    return GameState(
        world_id="context_inspector_sample",
        locations={location_id: LocationState(id=location_id, name=location_id)},
        npcs={npc: NPCState(id=npc, location_id=location_id)},
        facts={
            "visible_square": FactState(id="visible_square", text="A visible square.", visibility=FactVisibility.PUBLIC, public=True),
            "hidden_sample": FactState(id="hidden_sample", text="hidden fact text", visibility=FactVisibility.HIDDEN),
        },
        player_visible_facts={"visible_square"},
    )
