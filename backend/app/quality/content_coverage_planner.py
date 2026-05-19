from __future__ import annotations

from pydantic import BaseModel, Field

from app.quality.content_coverage import ContentCoverageReport, analyze_content_coverage


class ContentCoveragePlanRequest(BaseModel):
    target_world: str
    genre: str = "general"
    desired_playtime: str = "short"
    desired_complexity: str = "medium"
    current_content_coverage_report: ContentCoverageReport | None = None


class ContentCoverageSuggestion(BaseModel):
    category: str
    summary: str
    recommended_tool: str
    priority: str = "medium"
    safe_refs: list[str] = Field(default_factory=list)


class ContentCoveragePlan(BaseModel):
    world_id: str
    genre: str
    desired_playtime: str
    desired_complexity: str
    missing_location_types: list[ContentCoverageSuggestion] = Field(default_factory=list)
    missing_npc_archetypes: list[ContentCoverageSuggestion] = Field(default_factory=list)
    missing_quest_types: list[ContentCoverageSuggestion] = Field(default_factory=list)
    missing_clue_paths: list[ContentCoverageSuggestion] = Field(default_factory=list)
    missing_faction_hooks: list[ContentCoverageSuggestion] = Field(default_factory=list)
    missing_rp_scenes: list[ContentCoverageSuggestion] = Field(default_factory=list)
    missing_scenario_regressions: list[ContentCoverageSuggestion] = Field(default_factory=list)
    missing_playtest_paths: list[ContentCoverageSuggestion] = Field(default_factory=list)
    normal_report: bool = True


def build_content_coverage_plan(
    request: ContentCoveragePlanRequest,
    *,
    worlds_root: str = "worlds",
) -> ContentCoveragePlan:
    report = request.current_content_coverage_report or analyze_content_coverage(
        request.target_world,
        worlds_root=worlds_root,
    )
    plan = ContentCoveragePlan(
        world_id=request.target_world,
        genre=request.genre,
        desired_playtime=request.desired_playtime,
        desired_complexity=request.desired_complexity,
    )
    _add_coverage_suggestions(plan, report)
    _add_shape_suggestions(plan, report, request)
    return plan


def _add_coverage_suggestions(plan: ContentCoveragePlan, report: ContentCoverageReport) -> None:
    if report.locations.coverage_percent < 60:
        plan.missing_location_types.append(
            _suggestion("locations", "Add or test a hub, connector, and one optional side area.", "location_clusters", "high", report.locations.uncovered_ids[:3])
        )
    if report.npcs.coverage_percent < 60:
        plan.missing_npc_archetypes.append(
            _suggestion("npcs", "Add or cover guide, witness, merchant, and antagonist archetypes.", "npc_pack_generator", "high", report.npcs.uncovered_ids[:3])
        )
    if report.quests.coverage_percent < 70:
        plan.missing_quest_types.append(
            _suggestion("quests", "Add a starter quest, branch/failure path, and completion regression.", "quest_pack_generator", "high", report.quests.uncovered_ids[:3])
        )
    if report.facts.coverage_percent < 70 or report.hidden_entities_redacted.get("facts", 0) > 0:
        plan.missing_clue_paths.append(
            _suggestion("clues", "Add safe clue discovery paths and hidden leak regression coverage.", "mystery_templates", "high")
        )
    if report.factions.total == 0 or report.factions.coverage_percent < 50:
        plan.missing_faction_hooks.append(
            _suggestion("factions", "Add visible faction hooks or validate hidden faction boundaries.", "faction_templates", "medium", report.factions.uncovered_ids[:3])
        )
    if report.npcs.total > 0 and report.quests.total > 0:
        plan.missing_rp_scenes.append(
            _suggestion("rp_scenes", "Create dialogue and group RP scene templates for key NPCs.", "dialogue_scenes", "medium", report.npcs.uncovered_ids[:3])
        )
    if report.hidden_entities_redacted:
        plan.missing_scenario_regressions.append(
            _suggestion("scenario_regression", "Add hidden leak and boundary regression cases for redacted content.", "scenarios", "high")
        )
    if report.combat_encounters.total == 0 or report.shops_trade.coverage_percent < 50:
        plan.missing_playtest_paths.append(
            _suggestion("playtests", "Add playtest paths for combat avoidance, shop/trade, search, and quest progression.", "playtests", "medium")
        )


def _add_shape_suggestions(
    plan: ContentCoveragePlan,
    report: ContentCoverageReport,
    request: ContentCoveragePlanRequest,
) -> None:
    complexity_targets = {"low": 2, "medium": 4, "high": 7}
    desired = complexity_targets.get(request.desired_complexity, 4)
    if report.locations.total < desired:
        plan.missing_location_types.append(
            _suggestion("locations", f"Desired complexity suggests at least {desired} player-safe locations.", "location_clusters", "medium")
        )
    if request.genre.lower() in {"mystery", "detective", "推理"} and not plan.missing_clue_paths:
        plan.missing_clue_paths.append(
            _suggestion("clues", "Mystery genre benefits from clue, red herring, witness, and reveal path coverage.", "mystery_templates", "high")
        )


def _suggestion(
    category: str,
    summary: str,
    recommended_tool: str,
    priority: str,
    refs: list[str] | None = None,
) -> ContentCoverageSuggestion:
    return ContentCoverageSuggestion(
        category=category,
        summary=_redact(summary),
        recommended_tool=recommended_tool,
        priority=priority,
        safe_refs=[_safe_ref(ref) for ref in refs or []],
    )


def _safe_ref(ref: str) -> str:
    lowered = ref.lower()
    if any(token in lowered for token in ("hidden", "secret", "private", "sealed_letter_under_stone")):
        return "[redacted]"
    return ref


def _redact(value: str) -> str:
    text = value
    for token in ("hidden fact", "secret", "private_self_summary", "sealed_letter_under_stone"):
        text = text.replace(token, "[redacted]")
    return text
