from __future__ import annotations

from pathlib import Path
from random import Random
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.core.state_delta import StateDelta
from app.core.timeline_replay import state_checksum
from app.core.world_state import GameState, LocationState, PlayerState, WorldObjectState
from app.engine.actions.declarative import DeclarativeActionDefinition, DeclarativeActionHandler
from app.engine.gameplay_module_loader import GameplayModuleLoader, GameplayModuleLoaderError, GameplayModuleManifest
from app.llm.schemas import PlayerActionType, PlayerIntent


class ModuleDebugActionSummary(BaseModel):
    id: str
    label: str
    category: str
    aliases: list[str] = Field(default_factory=list)
    event_type: str
    target_types: list[str] = Field(default_factory=list)
    precondition_count: int = 0
    check_count: int = 0
    effect_count: int = 0
    state_delta_templates: list[str] = Field(default_factory=list)


class ModuleDebugSummary(BaseModel):
    local_only: bool = True
    module_id: str
    name: str
    version: str
    module_type: str
    permissions: dict[str, bool] = Field(default_factory=dict)
    state_schema_extensions: list[dict[str, Any]] = Field(default_factory=list)
    event_types: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[ModuleDebugActionSummary] = Field(default_factory=list)
    hidden_details_redacted: bool = True
    contains_api_key: bool = False
    calls_llm: bool = False


class ModuleDebugListResponse(BaseModel):
    local_only: bool = True
    modules: list[ModuleDebugSummary] = Field(default_factory=list)


class ModuleActionDryRunRequest(BaseModel):
    input_text: str = ""
    target_id: str | None = None
    seed: int = 1


class ModuleActionDryRunResponse(BaseModel):
    local_only: bool = True
    dry_run: bool = True
    state_unchanged: bool
    module_id: str
    action_id: str
    preconditions_result: list[dict[str, Any]] = Field(default_factory=list)
    checks_result: list[dict[str, Any]] = Field(default_factory=list)
    selected_outcome: str
    state_delta_preview: list[StateDelta] = Field(default_factory=list)
    event_preview: dict[str, Any] = Field(default_factory=dict)
    visibility_summary: dict[str, Any] = Field(default_factory=dict)
    hidden_facts_redacted: bool = True
    contains_api_key: bool = False
    calls_llm: bool = False


def list_module_debug_summaries(modules_root: str | Path = "gameplay_modules") -> ModuleDebugListResponse:
    loader = GameplayModuleLoader(modules_root)
    summaries = [_summary_for_manifest(module.manifest, module.path) for module in loader.discover_modules()]
    return ModuleDebugListResponse(modules=summaries)


def get_module_debug_summary(module_id: str, modules_root: str | Path = "gameplay_modules") -> ModuleDebugSummary:
    loader = GameplayModuleLoader(modules_root)
    manifest = loader.load_manifest_only(module_id)
    module_path = _module_path(loader.modules_root, module_id)
    return _summary_for_manifest(manifest, module_path)


def dry_run_module_action(
    module_id: str,
    action_id: str,
    request: ModuleActionDryRunRequest,
    *,
    modules_root: str | Path = "gameplay_modules",
) -> ModuleActionDryRunResponse:
    module_path = _module_path(Path(modules_root), module_id)
    definitions = _read_action_definitions(module_path)
    definition = next((item for item in definitions if item.id == action_id), None)
    if definition is None:
        raise GameplayModuleLoaderError(f"Action not found in gameplay module: {action_id}")
    state = _debug_state()
    before_checksum = state_checksum(state)
    default_input = definition.aliases[0] if definition.aliases else definition.id
    input_text = request.input_text or default_input
    intent = PlayerIntent(
        action_type=PlayerActionType.UNKNOWN,
        raw_text=input_text,
        confidence=1.0,
        requires_clarification=False,
        target_id=request.target_id or _default_target(definition),
    )
    execution = DeclarativeActionHandler(definition).resolve_with_event(intent, state, Random(request.seed))
    after_checksum = state_checksum(state)
    action_result = execution.action_result
    return ModuleActionDryRunResponse(
        state_unchanged=before_checksum == after_checksum,
        module_id=module_id,
        action_id=action_id,
        preconditions_result=[
            {"index": index, "condition_type": condition.condition_type.value, "safe_summary": "evaluated by DeclarativeActionHandler"}
            for index, condition in enumerate(definition.preconditions)
        ],
        checks_result=[
            {"index": index, "check_type": check.check_type.value, "safe_summary": "evaluated by DeclarativeActionHandler"}
            for index, check in enumerate(definition.checks)
        ],
        selected_outcome=action_result.success_level.value,
        state_delta_preview=action_result.state_deltas,
        event_preview={
            "event_id": execution.event.event_id,
            "turn": execution.event.turn,
            "actor_id": execution.event.actor_id,
            "action_type": execution.event.action_type,
            "result": execution.event.result,
            "visible_to_player": execution.event.visible_to_player,
            "delta_count": len(execution.event.state_deltas),
        },
        visibility_summary={
            "visible_fact_count": len(action_result.visible_facts),
            "hidden_fact_count": len(action_result.hidden_facts),
            "hidden_fact_ids_redacted": bool(action_result.hidden_facts),
            "visible_to_player": execution.event.visible_to_player,
        },
    )


def _summary_for_manifest(manifest: GameplayModuleManifest, module_path: Path) -> ModuleDebugSummary:
    return ModuleDebugSummary(
        module_id=manifest.id,
        name=manifest.name,
        version=manifest.version,
        module_type=manifest.module_type,
        permissions=manifest.permissions.model_dump(),
        state_schema_extensions=[extension.model_dump(mode="json") for extension in manifest.state_schema_extensions],
        event_types=[event_type.model_dump(mode="json") for event_type in manifest.event_types],
        actions=[_action_summary(action) for action in _read_action_definitions(module_path)],
    )


def _action_summary(definition: DeclarativeActionDefinition) -> ModuleDebugActionSummary:
    templates = [
        template.path
        for template in definition.state_delta_templates
        for _ in [template]
    ]
    for outcome in definition.outcomes.values():
        templates.extend(template.path for template in outcome.state_delta_templates)
    return ModuleDebugActionSummary(
        id=definition.id,
        label=definition.label,
        category=definition.category.value,
        aliases=definition.aliases,
        event_type=definition.event_type,
        target_types=[spec.kind.value for spec in definition.target_specs],
        precondition_count=len(definition.preconditions),
        check_count=len(definition.checks),
        effect_count=len(templates),
        state_delta_templates=sorted(set(templates)),
    )


def _read_action_definitions(module_path: Path) -> list[DeclarativeActionDefinition]:
    action_root = module_path / "action_mods"
    if not action_root.exists():
        return []
    definitions: list[DeclarativeActionDefinition] = []
    for path in sorted(action_root.rglob("*"), key=lambda item: str(item)):
        if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml", ".json"}:
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if isinstance(data, list):
            raw_actions = data
        elif isinstance(data, dict):
            raw_actions = data.get("actions", [data])
        else:
            raw_actions = []
        for raw_action in raw_actions:
            definitions.append(DeclarativeActionDefinition.model_validate(raw_action))
    return definitions


def _module_path(modules_root: str | Path, module_id: str) -> Path:
    root = Path(modules_root).resolve()
    module_path = (root / module_id).resolve()
    if root != module_path and root not in module_path.parents:
        raise GameplayModuleLoaderError("Gameplay module path escapes module root")
    if not module_path.exists():
        raise GameplayModuleLoaderError(f"Gameplay module not found: {module_id}")
    return module_path


def _debug_state() -> GameState:
    return GameState(
        world_id="module-debug",
        turn=1,
        player=PlayerState(location_id="debug_room"),
        locations={"debug_room": LocationState(id="debug_room", name="Debug Room")},
        objects={"debug_object": WorldObjectState(id="debug_object", location_id="debug_room", visible=True)},
    )


def _default_target(definition: DeclarativeActionDefinition) -> str | None:
    target_types = {spec.kind.value for spec in definition.target_specs}
    if "object" in target_types:
        return "debug_object"
    if "current_location" in target_types:
        return None
    return None
