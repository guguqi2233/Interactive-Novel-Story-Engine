from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

from app.core.world_state import NPCFactionDuty, NPCGoalState, NPCSocialDisposition
from app.engine.content.authoring_service import AuthoringError, ContentAuthoringService
from app.engine.content.npc_goal_authoring import (
    NPCGoalAuthoringError,
    NPCGoalAuthoringGraph,
    npc_yaml_to_goal_graph,
)
from app.engine.content.validation_gate import (
    AuthoringOperationType,
    AuthoringValidationGateRequest,
    AuthoringValidationGateResult,
)
from app.engine.content.validator import ValidationReport, ValidationSeverity


class NPCSimulationPresetError(ValueError):
    """Raised when an NPC simulation preset cannot be previewed or applied."""


class NPCSimulationPreset(BaseModel):
    id: str
    name: str
    description: str = ""
    goals: list[NPCGoalState] = Field(default_factory=list)
    intent_priorities: dict[str, int] = Field(default_factory=dict)
    faction_duties: list[NPCFactionDuty] = Field(default_factory=list)
    relationship_behavior_rules: list[dict[str, Any]] = Field(default_factory=list)
    rumor_decision_tendencies: dict[str, Any] = Field(default_factory=dict)
    social_disposition_defaults: NPCSocialDisposition = Field(default_factory=NPCSocialDisposition)
    conflict_avoidance_defaults: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_no_executable_content(self) -> "NPCSimulationPreset":
        payload = self.model_dump(mode="json")
        if _contains_forbidden_key(payload):
            raise ValueError("NPC simulation presets cannot contain scripts, commands, or remote URLs")
        return self


class NPCSimulationPresetApplyRequest(BaseModel):
    preset_id: str | None = None
    preset: NPCSimulationPreset | None = None
    confirm_warnings: bool = False


class NPCSimulationPresetPreview(BaseModel):
    world_id: str
    npc_id: str
    preset: NPCSimulationPreset
    graph: NPCGoalAuthoringGraph
    yaml_content: str
    validation: ValidationReport
    validation_gate: AuthoringValidationGateResult
    applied_fields: list[str] = Field(default_factory=list)

    @property
    def confirmation_required(self) -> bool:
        return self.validation_gate.confirmation_required


def list_npc_simulation_presets() -> list[NPCSimulationPreset]:
    return [NPCSimulationPreset.model_validate(item) for item in _BUILT_IN_PRESETS]


def get_npc_simulation_preset(preset_id: str) -> NPCSimulationPreset:
    for preset in list_npc_simulation_presets():
        if preset.id == preset_id:
            return preset
    raise NPCSimulationPresetError(f"Unknown NPC simulation preset: {preset_id}")


def preview_npc_simulation_preset(
    world_id: str,
    npc_id: str,
    request: NPCSimulationPresetApplyRequest,
    authoring_service: ContentAuthoringService,
) -> NPCSimulationPresetPreview:
    preset = _resolve_preset(request)
    draft_yaml = _apply_preset_to_yaml(world_id, npc_id, preset, authoring_service)
    graph = npc_yaml_to_goal_graph(world_id, draft_yaml)
    validation = authoring_service.validate_draft(world_id, "npcs.yaml", draft_yaml)
    _validate_preset_against_world(world_id, npc_id, preset, authoring_service, validation)
    gate = authoring_service.validation_gate.evaluate(
        AuthoringValidationGateRequest(
            world_id=world_id,
            operation_type=AuthoringOperationType.SAVE,
            draft_content={"npcs.yaml": draft_yaml},
            affected_files=["npcs.yaml"],
            confirm_warnings=request.confirm_warnings,
            validation_report=validation,
        )
    )
    return NPCSimulationPresetPreview(
        world_id=world_id,
        npc_id=npc_id,
        preset=preset,
        graph=graph,
        yaml_content=draft_yaml,
        validation=gate.validation_report,
        validation_gate=gate,
        applied_fields=[
            "goals",
            "priorities",
            "faction_duties",
            "social_disposition",
            "plan_state.simulation_preset",
        ],
    )


def apply_npc_simulation_preset_to_draft(
    world_id: str,
    npc_id: str,
    request: NPCSimulationPresetApplyRequest,
    authoring_service: ContentAuthoringService,
) -> NPCSimulationPresetPreview:
    # This intentionally returns a draft preview only. Persisting still uses the
    # existing NPC goal save endpoint, which writes only after the validation gate.
    return preview_npc_simulation_preset(world_id, npc_id, request, authoring_service)


def _resolve_preset(request: NPCSimulationPresetApplyRequest) -> NPCSimulationPreset:
    if request.preset is not None:
        return request.preset
    if request.preset_id:
        return get_npc_simulation_preset(request.preset_id)
    raise NPCSimulationPresetError("preset_id or preset is required")


def _apply_preset_to_yaml(
    world_id: str,
    npc_id: str,
    preset: NPCSimulationPreset,
    authoring_service: ContentAuthoringService,
) -> str:
    try:
        data = yaml.safe_load(authoring_service.read_file(world_id, "npcs.yaml")) or {}
    except (AuthoringError, yaml.YAMLError) as exc:
        raise NPCSimulationPresetError(f"Cannot read npcs.yaml: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("npcs"), list):
        raise NPCSimulationPresetError("Expected npcs.yaml to contain an 'npcs' list")

    found = False
    updated_npcs: list[Any] = []
    for raw_npc in data["npcs"]:
        if not isinstance(raw_npc, dict) or str(raw_npc.get("id", "")) != npc_id:
            updated_npcs.append(raw_npc)
            continue
        found = True
        updated = dict(raw_npc)
        updated["goals"] = _merge_goals(updated.get("goals", []), preset.goals)
        updated["priorities"] = {
            **_dict_or_empty(updated.get("priorities")),
            **preset.intent_priorities,
        }
        updated["faction_duties"] = _merge_by_id(
            updated.get("faction_duties", []),
            [duty.model_dump(mode="json") for duty in preset.faction_duties],
        )
        updated["social_disposition"] = preset.social_disposition_defaults.model_dump(mode="json")
        plan_state = _dict_or_empty(updated.get("plan_state"))
        plan_state["simulation_preset"] = {
            "preset_id": preset.id,
            "relationship_behavior_rules": preset.relationship_behavior_rules,
            "rumor_decision_tendencies": preset.rumor_decision_tendencies,
            "conflict_avoidance_defaults": preset.conflict_avoidance_defaults,
        }
        updated["plan_state"] = plan_state
        updated_npcs.append(updated)
    if not found:
        raise NPCSimulationPresetError(f"NPC not found: {npc_id}")

    data["npcs"] = updated_npcs
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def _validate_preset_against_world(
    world_id: str,
    npc_id: str,
    preset: NPCSimulationPreset,
    authoring_service: ContentAuthoringService,
    report: ValidationReport,
) -> None:
    known_ids = _load_world_ids(world_id, authoring_service)
    if npc_id not in known_ids["npcs"]:
        report.add(
            ValidationSeverity.ERROR,
            f"npcs.{npc_id}",
            f"NPC not found: {npc_id}",
            code="npc_simulation_preset_missing_npc",
            ref_id=npc_id,
        )
    allowed_intents = {
        "report_crime",
        "spread_rumor",
        "visit_location",
        "avoid_actor",
        "talk_to_npc",
        "guard_location",
        "rest",
        "seek_item",
        "help_actor",
        "warn_actor",
        "refuse_hostile_actor",
        "seek_information",
        "enforce_curfew",
        "call_for_help",
    }
    for intent_type in preset.intent_priorities:
        if intent_type not in allowed_intents:
            report.add(
                ValidationSeverity.ERROR,
                f"npc_simulation_presets.{preset.id}.intent_priorities.{intent_type}",
                f"Invalid NPC simulation intent type: {intent_type}",
                code="npc_simulation_preset_invalid_intent",
                ref_id=preset.id,
            )
    for goal in preset.goals:
        _validate_fact_conditions(goal.conditions, known_ids["facts"], report, preset.id)
    for duty in preset.faction_duties:
        if duty.faction_id is not None and duty.faction_id not in known_ids["factions"]:
            report.add(
                ValidationSeverity.ERROR,
                f"npc_simulation_presets.{preset.id}.faction_duties.{duty.id}.faction_id",
                f"Faction duty references unknown faction: {duty.faction_id}",
                code="npc_simulation_preset_missing_faction",
                ref_id=duty.faction_id,
            )
        for fact_id in duty.required_fact_ids:
            if fact_id not in known_ids["facts"]:
                report.add(
                    ValidationSeverity.ERROR,
                    f"npc_simulation_presets.{preset.id}.faction_duties.{duty.id}.required_fact_ids",
                    f"Faction duty references unknown fact: {fact_id}",
                    code="npc_simulation_preset_unknown_fact",
                    ref_id=fact_id,
                )
        if duty.target_type == "location" and duty.target_id and duty.target_id not in known_ids["locations"]:
            report.add(
                ValidationSeverity.ERROR,
                f"npc_simulation_presets.{preset.id}.faction_duties.{duty.id}.target_id",
                f"Faction duty references unknown location: {duty.target_id}",
                code="npc_simulation_preset_missing_location",
                ref_id=duty.target_id,
            )


def _load_world_ids(world_id: str, authoring_service: ContentAuthoringService) -> dict[str, set[str]]:
    files = {
        "npcs": "npcs.yaml",
        "facts": "facts.yaml",
        "factions": "factions.yaml",
        "locations": "locations.yaml",
    }
    result: dict[str, set[str]] = {key: set() for key in files}
    for key, file_name in files.items():
        try:
            data = yaml.safe_load(authoring_service.read_file(world_id, file_name)) or {}
        except (AuthoringError, yaml.YAMLError):
            continue
        entries = data.get(key, []) if isinstance(data, dict) else []
        if isinstance(entries, list):
            result[key] = {str(item.get("id")) for item in entries if isinstance(item, dict) and item.get("id")}
    return result


def _validate_fact_conditions(
    conditions: list[str],
    fact_ids: set[str],
    report: ValidationReport,
    preset_id: str,
) -> None:
    for condition in conditions:
        if condition.startswith("fact:"):
            fact_id = condition.split(":", 1)[1]
            if fact_id not in fact_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"npc_simulation_presets.{preset_id}.goals.conditions",
                    f"Preset goal references unknown fact: {fact_id}",
                    code="npc_simulation_preset_unknown_fact",
                    ref_id=fact_id,
                )


def _merge_goals(existing: Any, additions: list[NPCGoalState]) -> list[dict[str, Any]]:
    existing_list = existing if isinstance(existing, list) else []
    addition_payloads = [goal.model_dump(mode="json") for goal in additions]
    return _merge_by_id(existing_list, addition_payloads)


def _merge_by_id(existing: Any, additions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing_items = [dict(item) for item in existing if isinstance(item, dict)] if isinstance(existing, list) else []
    by_id = {str(item.get("id", "")): item for item in existing_items if item.get("id")}
    for addition in additions:
        by_id[str(addition["id"])] = addition
    ordered_ids = [str(item.get("id", "")) for item in existing_items if item.get("id")]
    for addition in additions:
        addition_id = str(addition["id"])
        if addition_id not in ordered_ids:
            ordered_ids.append(addition_id)
    return [by_id[item_id] for item_id in ordered_ids]


def _dict_or_empty(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _contains_forbidden_key(value: Any) -> bool:
    forbidden = {"script", "scripts", "command", "commands", "url", "remote_url", "executable"}
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in forbidden:
                return True
            if isinstance(child, str) and child.lower().startswith(("http://", "https://", "file://")):
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


_BUILT_IN_PRESETS: list[dict[str, Any]] = [
    {
        "id": "guard",
        "name": "Guard",
        "description": "Protect a location, report crimes, and avoid unnecessary risks.",
        "goals": [
            {
                "id": "guard_assigned_location",
                "description": "Keep watch over the assigned area.",
                "priority": 70,
                "status": "inactive",
                "allowed_actions": ["guard_location", "report_crime"],
                "forbidden_actions": ["spread_rumor"],
            }
        ],
        "intent_priorities": {"guard_location": 80, "report_crime": 70, "call_for_help": 65},
        "faction_duties": [
            {"id": "guard_assigned_location", "duty_type": "guard_location", "priority": 70, "target_type": "location"}
        ],
        "relationship_behavior_rules": [{"behavior": "report_actor", "when": "hostile_or_criminal"}],
        "rumor_decision_tendencies": {"share_with_faction": 60, "keep_secret": 45},
        "social_disposition_defaults": {"loyalty_to_faction": 70, "risk_tolerance": 45, "conflict_tolerance": 65},
        "conflict_avoidance_defaults": {"call_for_help": 70, "flee_from_actor": 25},
    },
    {
        "id": "merchant",
        "name": "Merchant",
        "description": "Prefer trade, self-preservation, and cautious information sharing.",
        "goals": [
            {
                "id": "maintain_shop",
                "description": "Keep the shop safe and stocked.",
                "priority": 60,
                "status": "inactive",
                "allowed_actions": ["talk_to_npc", "flee"],
            }
        ],
        "intent_priorities": {"talk_to_npc": 55, "avoid_actor": 65, "seek_item": 50},
        "relationship_behavior_rules": [{"behavior": "withhold_information", "when": "low_trust"}],
        "rumor_decision_tendencies": {"keep_secret": 65, "share_with_actor": 30},
        "social_disposition_defaults": {"trust_player": 5, "risk_tolerance": 35, "secrecy_preference": 65},
        "conflict_avoidance_defaults": {"avoid_actor": 70, "call_for_help": 45},
    },
    {
        "id": "informant",
        "name": "Informant",
        "description": "Collect information and share known rumors with trusted actors.",
        "goals": [
            {
                "id": "trade_information",
                "description": "Trade known information without revealing unknown facts.",
                "priority": 65,
                "status": "inactive",
                "allowed_actions": ["talk_to_npc", "spread_rumor"],
            }
        ],
        "intent_priorities": {"spread_rumor": 70, "talk_to_npc": 60, "seek_information": 55},
        "relationship_behavior_rules": [{"behavior": "share_known_rumor", "when": "trusted_actor"}],
        "rumor_decision_tendencies": {"share_with_actor": 65, "distort_rumor": 20, "keep_secret": 55},
        "social_disposition_defaults": {"trust_player": 10, "risk_tolerance": 45, "secrecy_preference": 75},
        "conflict_avoidance_defaults": {"avoid_actor": 60},
    },
    {
        "id": "hostile",
        "name": "Hostile Actor",
        "description": "Report, refuse, or avoid actors with hostile relationships.",
        "goals": [
            {
                "id": "oppose_hostile_actor",
                "description": "Oppose hostile actors through bounded rules.",
                "priority": 75,
                "status": "inactive",
                "allowed_actions": ["report_crime", "avoid_actor"],
            }
        ],
        "intent_priorities": {"report_crime": 75, "avoid_actor": 55, "refuse_hostile_actor": 65},
        "relationship_behavior_rules": [{"behavior": "report_actor", "when": "hostile"}],
        "rumor_decision_tendencies": {"share_with_faction": 50, "keep_secret": 60},
        "social_disposition_defaults": {"trust_player": -40, "fear_player": 10, "conflict_tolerance": 70},
        "conflict_avoidance_defaults": {"refuse_confrontation": 50},
    },
    {
        "id": "timid_villager",
        "name": "Timid Villager",
        "description": "Avoid danger, seek guards, and share only safe known rumors.",
        "goals": [
            {
                "id": "stay_safe",
                "description": "Avoid danger and seek help when frightened.",
                "priority": 80,
                "status": "inactive",
                "allowed_actions": ["flee", "rest_if_injured"],
            }
        ],
        "intent_priorities": {"avoid_actor": 80, "rest": 55, "talk_to_npc": 30},
        "relationship_behavior_rules": [{"behavior": "avoid_actor", "when": "high_fear"}],
        "rumor_decision_tendencies": {"keep_secret": 80, "share_with_actor": 15},
        "social_disposition_defaults": {"fear_player": 35, "risk_tolerance": 20, "conflict_tolerance": 15},
        "conflict_avoidance_defaults": {"flee_from_actor": 80, "hide": 60},
    },
    {
        "id": "loyal_subordinate",
        "name": "Loyal Subordinate",
        "description": "Prioritize faction and superior duties.",
        "goals": [
            {
                "id": "serve_faction",
                "description": "Serve faction goals through bounded duties.",
                "priority": 75,
                "status": "inactive",
                "allowed_actions": ["guard_location", "report_crime", "spread_rumor"],
            }
        ],
        "intent_priorities": {"guard_location": 65, "report_crime": 80, "spread_rumor": 55},
        "relationship_behavior_rules": [{"behavior": "warn_actor", "when": "ally_in_danger"}],
        "rumor_decision_tendencies": {"share_with_faction": 75, "keep_secret": 70},
        "social_disposition_defaults": {"loyalty_to_faction": 90, "secrecy_preference": 70},
        "conflict_avoidance_defaults": {"call_for_help": 65},
    },
    {
        "id": "rumor_spreader",
        "name": "Rumor Spreader",
        "description": "Spread known, safe rumors without inventing facts.",
        "goals": [
            {
                "id": "spread_known_news",
                "description": "Share rumors already known to this NPC.",
                "priority": 60,
                "status": "inactive",
                "allowed_actions": ["spread_rumor", "talk_to_npc"],
            }
        ],
        "intent_priorities": {"spread_rumor": 85, "talk_to_npc": 50},
        "relationship_behavior_rules": [{"behavior": "share_known_rumor", "when": "low_secrecy"}],
        "rumor_decision_tendencies": {"share_with_actor": 75, "distort_rumor": 15, "keep_secret": 25},
        "social_disposition_defaults": {"secrecy_preference": 20, "risk_tolerance": 55},
        "conflict_avoidance_defaults": {"avoid_actor": 35},
    },
    {
        "id": "investigator",
        "name": "Investigator",
        "description": "Seek information, report crimes, and avoid contaminating knowledge boundaries.",
        "goals": [
            {
                "id": "investigate_known_crime",
                "description": "Investigate only known crimes or visible clues.",
                "priority": 80,
                "status": "inactive",
                "allowed_actions": ["investigate", "report_crime", "talk_to_npc"],
            }
        ],
        "intent_priorities": {"seek_information": 80, "report_crime": 70, "talk_to_npc": 60},
        "relationship_behavior_rules": [{"behavior": "withhold_information", "when": "investigation_sensitive"}],
        "rumor_decision_tendencies": {"keep_secret": 70, "report_rumor": 60},
        "social_disposition_defaults": {"risk_tolerance": 55, "secrecy_preference": 70, "moral_flexibility": 25},
        "conflict_avoidance_defaults": {"seek_guard": 50, "avoid_actor": 40},
    },
]


def validate_npc_simulation_preset_payload(payload: dict[str, Any]) -> NPCSimulationPreset:
    try:
        return NPCSimulationPreset.model_validate(payload)
    except ValidationError as exc:
        raise NPCSimulationPresetError(str(exc)) from exc
