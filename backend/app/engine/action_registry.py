from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.world_state import GameState
from app.engine.actions.base import ActionHandler
from app.engine.actions.basic import default_action_handlers
from app.engine.actions.declarative import DeclarativeActionDefinition, DeclarativeActionHandler
from app.llm.schemas import PlayerActionType, PlayerIntent


class ActionRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionRegistrySource(StrEnum):
    CORE = "core"
    MODULE = "module"
    MOD = "mod"


class ActionMetadata(BaseModel):
    id: str
    label: str
    category: str = "general"
    aliases: list[str] = Field(default_factory=list)
    module_id: str | None = None
    enabled: bool = True
    risk_level: ActionRiskLevel = ActionRiskLevel.LOW
    target_types: list[str] = Field(default_factory=list)
    source: ActionRegistrySource = ActionRegistrySource.CORE


class RegisteredAction(BaseModel):
    metadata: ActionMetadata
    handler: ActionHandler
    model_config = {"arbitrary_types_allowed": True}


class AliasConflict(BaseModel):
    alias: str
    action_ids: list[str]
    severity: str = "warning"


class ActionRegistry:
    def __init__(self, *, include_core: bool = True) -> None:
        self._actions: dict[str, RegisteredAction] = {}
        if include_core:
            for handler in default_action_handlers():
                self.register_core_action(_core_action_metadata(handler.action_type), handler)

    def register_core_action(self, metadata: ActionMetadata, handler: ActionHandler) -> None:
        self._actions[metadata.id] = RegisteredAction(
            metadata=metadata.model_copy(update={"source": ActionRegistrySource.CORE, "module_id": None}),
            handler=handler,
        )

    def register_module_action(
        self,
        definition: DeclarativeActionDefinition,
        *,
        module_id: str,
        enabled: bool = True,
        risk_level: ActionRiskLevel = ActionRiskLevel.LOW,
        handler: ActionHandler | None = None,
    ) -> None:
        metadata = ActionMetadata(
            id=definition.id,
            label=definition.label,
            category=definition.category.value,
            aliases=definition.aliases,
            module_id=module_id,
            enabled=enabled,
            risk_level=risk_level,
            target_types=[spec.kind.value for spec in definition.target_specs],
            source=ActionRegistrySource.MODULE,
        )
        self._actions[definition.id] = RegisteredAction(
            metadata=metadata,
            handler=handler or DeclarativeActionHandler(definition),
        )

    def unregister_module_action(self, action_id: str) -> None:
        registered = self._actions.get(action_id)
        if registered and registered.metadata.source == ActionRegistrySource.MODULE:
            del self._actions[action_id]

    def register_mod_action(
        self,
        definition: DeclarativeActionDefinition,
        *,
        package_id: str,
        enabled: bool = True,
        risk_level: ActionRiskLevel = ActionRiskLevel.LOW,
        handler: ActionHandler | None = None,
    ) -> None:
        if definition.id in self._actions and self._actions[definition.id].metadata.source == ActionRegistrySource.CORE:
            raise ValueError(f"mod action conflicts with core action: {definition.id}")
        metadata = ActionMetadata(
            id=definition.id,
            label=definition.label,
            category=definition.category.value,
            aliases=definition.aliases,
            module_id=package_id,
            enabled=enabled,
            risk_level=risk_level,
            target_types=[spec.kind.value for spec in definition.target_specs],
            source=ActionRegistrySource.MOD,
        )
        proposed_aliases = set(_aliases_for_metadata(metadata))
        for registered in self._actions.values():
            if registered.metadata.source == ActionRegistrySource.MOD:
                overlap = proposed_aliases.intersection(_aliases_for_metadata(registered.metadata))
                if overlap:
                    raise ValueError(f"mod action alias conflict: {', '.join(sorted(overlap))}")
        self._actions[definition.id] = RegisteredAction(
            metadata=metadata,
            handler=handler or DeclarativeActionHandler(definition),
        )

    def unregister_mod_action(self, action_id: str) -> None:
        registered = self._actions.get(action_id)
        if registered and registered.metadata.source == ActionRegistrySource.MOD:
            del self._actions[action_id]

    def list_mod_actions(self) -> list[ActionMetadata]:
        return sorted(
            [registered.metadata for registered in self._actions.values() if registered.metadata.source == ActionRegistrySource.MOD],
            key=lambda metadata: metadata.id,
        )

    def list_available_actions(
        self,
        *,
        include_disabled: bool = False,
        state: GameState | None = None,
    ) -> list[ActionMetadata]:
        actions = [
            registered.metadata
            for registered in self._actions.values()
            if include_disabled or registered.metadata.enabled
        ]
        if state is not None:
            actions = [metadata for metadata in actions if self._is_visible_affordance(metadata, state)]
        return sorted(actions, key=lambda metadata: (metadata.source.value, metadata.id))

    def get_action_definition(self, action_id: str) -> ActionMetadata | None:
        registered = self._actions.get(action_id)
        return registered.metadata if registered else None

    def get_handler_for_intent(self, intent: PlayerIntent, state: GameState) -> ActionHandler | None:
        for registered in self._actions.values():
            if not registered.metadata.enabled:
                continue
            if registered.handler.can_handle(intent, state):
                return registered.handler
        return None

    def detect_alias_conflicts(self) -> list[AliasConflict]:
        alias_map: dict[str, list[str]] = {}
        for registered in self._actions.values():
            if not registered.metadata.enabled:
                continue
            for alias in _aliases_for_metadata(registered.metadata):
                alias_map.setdefault(alias, []).append(registered.metadata.id)
        return [
            AliasConflict(alias=alias, action_ids=sorted(set(action_ids)))
            for alias, action_ids in sorted(alias_map.items())
            if len(set(action_ids)) > 1
        ]

    def available_action_aliases(self) -> list[str]:
        aliases: set[str] = set()
        for metadata in self.list_available_actions():
            aliases.update(_aliases_for_metadata(metadata))
        return sorted(aliases)

    def suggested_actions_for_visible_affordances(self, state: GameState) -> list[str]:
        suggestions: list[str] = []
        for metadata in self.list_available_actions(state=state):
            alias = metadata.aliases[0] if metadata.aliases else metadata.id
            suggestions.append(alias)
        return suggestions

    def _is_visible_affordance(self, metadata: ActionMetadata, state: GameState) -> bool:
        if metadata.source == ActionRegistrySource.CORE:
            return True
        if "npc" in metadata.target_types:
            return any(npc.location_id == state.player.location_id and npc.visible and not npc.hidden for npc in state.npcs.values())
        if "object" in metadata.target_types:
            return any(obj.location_id == state.player.location_id and obj.visible and not obj.hidden for obj in state.objects.values())
        if "location" in metadata.target_types:
            return bool(state.locations)
        return True


def _aliases_for_metadata(metadata: ActionMetadata) -> list[str]:
    return sorted({metadata.id.lower(), metadata.label.lower(), *[alias.lower() for alias in metadata.aliases]})


def _core_action_metadata(action_type: PlayerActionType) -> ActionMetadata:
    label = action_type.value.replace("_", " ").title()
    return ActionMetadata(
        id=action_type.value,
        label=label,
        aliases=[action_type.value],
        category="core",
        target_types=[],
        source=ActionRegistrySource.CORE,
    )
