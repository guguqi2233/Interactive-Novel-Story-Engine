from enum import StrEnum
from random import Random
import re
from string import Formatter
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    CombatStatus,
    FactVisibility,
    GameState,
    NPCState,
    PlayerState,
    RelationshipState,
)
from app.engine.rules.inventory import has_item
from app.engine.rules.time import make_time_delta
from app.engine.rules.visibility import get_visible_facts


class ActionDSLValidationError(ValueError):
    """Raised when a declarative action DSL entry is outside the safe subset."""


class ActionPreconditionType(StrEnum):
    ACTOR_AT_LOCATION = "actor_at_location"
    TARGET_EXISTS = "target_exists"
    TARGET_VISIBLE = "target_visible"
    ACTOR_HAS_ITEM = "actor_has_item"
    ACTOR_HAS_STATUS = "actor_has_status"
    TARGET_HAS_TAG = "target_has_tag"
    ACTOR_NOT_IN_COMBAT = "actor_not_in_combat"
    NPC_KNOWS_FACT = "npc_knows_fact"
    FACT_VISIBLE_TO_ACTOR = "fact_visible_to_actor"


class ActionCheckType(StrEnum):
    SKILL_CHECK = "skill_check"
    REPUTATION_CHECK = "reputation_check"
    RELATIONSHIP_CHECK = "relationship_check"
    ITEM_CHECK = "item_check"
    RANDOM_THRESHOLD = "random_threshold"
    FIXED_SUCCESS = "fixed_success"


class ActionEffectType(StrEnum):
    STATE_DELTA_TEMPLATE = "state_delta_template"
    ADD_FACT_DISCOVERY = "add_fact_discovery"
    ADD_STATUS = "add_status"
    CONSUME_ITEM = "consume_item"
    ADVANCE_TIME = "advance_time"
    CREATE_EVENT_MARKER = "create_event_marker"


class ActionDSLTargetType(StrEnum):
    ANY = "any"
    LOCATION = "location"
    OBJECT = "object"
    NPC = "npc"
    FACT = "fact"
    ITEM = "item"
    FACTION = "faction"
    RELATIONSHIP = "relationship"


class ActionDSLResult(BaseModel):
    passed: bool
    reason: str
    details: dict[str, str | int | float | bool] = Field(default_factory=dict)


class ActionStateDeltaTemplate(BaseModel):
    operation: StateDeltaOperation
    path: str
    value: Any = None
    reason: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("path")
    @classmethod
    def validate_template_path(cls, value: str) -> str:
        validate_action_dsl_path_template(value)
        return value

    def to_delta(
        self,
        *,
        event_id: str,
        actor_id: str,
        target_id: str | None = None,
    ) -> StateDelta:
        rendered_path = render_action_dsl_template(self.path, actor_id=actor_id, target_id=target_id)
        rendered_value = render_action_dsl_value(self.value, actor_id=actor_id, target_id=target_id)
        rendered_metadata = {
            key: str(render_action_dsl_value(value, actor_id=actor_id, target_id=target_id))
            for key, value in self.metadata.items()
        }
        return StateDelta(
            operation=self.operation,
            path=rendered_path,
            value=rendered_value,
            caused_by_event_id=event_id,
            reason=self.reason,
            metadata=rendered_metadata,
        )


class ActionPrecondition(BaseModel):
    precondition_type: ActionPreconditionType
    actor_id: str = "player"
    target_id: str | None = None
    target_type: ActionDSLTargetType = ActionDSLTargetType.ANY
    location_id: str | None = None
    item_id: str | None = None
    status: str | None = None
    tag: str | None = None
    npc_id: str | None = None
    fact_id: str | None = None
    expected: bool = True


class ActionCheck(BaseModel):
    check_type: ActionCheckType
    actor_id: str = "player"
    target_id: str | None = None
    skill: str | None = None
    difficulty: int = 0
    bonus: int = 0
    faction_id: str | None = None
    relationship_id: str | None = None
    relationship_field: str = "trust"
    item_id: str | None = None
    threshold: int = 0
    seed: int | None = None

    @field_validator("relationship_field")
    @classmethod
    def validate_relationship_field(cls, value: str) -> str:
        allowed = {"trust", "fear", "affinity", "obligation"}
        if value not in allowed:
            raise ValueError(f"relationship_field must be one of {sorted(allowed)}")
        return value


class ActionEffect(BaseModel):
    effect_type: ActionEffectType
    state_delta_template: ActionStateDeltaTemplate | None = None
    actor_id: str = "player"
    target_id: str | None = None
    fact_id: str | None = None
    status: str | None = None
    item_id: str | None = None
    minutes: int = Field(default=0, ge=0)
    marker_key: str | None = None
    marker_value: bool | int | float | str = True
    reason: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_effect_payload(self) -> "ActionEffect":
        if self.effect_type == ActionEffectType.STATE_DELTA_TEMPLATE and self.state_delta_template is None:
            raise ValueError("state_delta_template effect requires a StateDelta template")
        if self.effect_type == ActionEffectType.ADD_FACT_DISCOVERY and not self.fact_id:
            raise ValueError("add_fact_discovery effect requires fact_id")
        if self.effect_type == ActionEffectType.ADD_STATUS and not self.status:
            raise ValueError("add_status effect requires status")
        if self.effect_type == ActionEffectType.CONSUME_ITEM and not self.item_id:
            raise ValueError("consume_item effect requires item_id")
        if self.effect_type == ActionEffectType.ADVANCE_TIME and self.minutes <= 0:
            raise ValueError("advance_time effect requires minutes > 0")
        if self.effect_type == ActionEffectType.CREATE_EVENT_MARKER and not self.marker_key:
            raise ValueError("create_event_marker effect requires marker_key")
        return self


_ALLOWED_TEMPLATE_FIELDS = {"actor_id", "target_id"}
_ALLOWED_STATE_DELTA_PREFIXES = (
    "flags.",
    "social_flags.",
    "player.location_id",
    "player.inventory",
    "player.status_effects",
    "player.currency",
    "player.stamina",
    "player.combat_stance",
    "npcs.{target_id}.",
    "npcs.{actor_id}.",
    "objects.{target_id}.",
    "quests.{target_id}.",
    "relationships.{target_id}.",
    "social_moves.{target_id}.",
    "leverages.{target_id}.",
    "factions.{target_id}.",
    "faction_mission_definitions.{target_id}.",
    "faction_missions.{target_id}.",
    "rumors.{target_id}.",
    "crimes.{target_id}.",
    "combats.{target_id}.",
    "weapon_profiles.{target_id}.",
    "combat_status_effects.{target_id}.",
    "combat_encounters.{target_id}.",
    "magic_resources.{actor_id}.",
    "magic_resources.{target_id}.",
    "hackables.{target_id}.",
    "hacking_tools.{target_id}.",
    "network_nodes.{target_id}.",
    "crafting_stations.{target_id}.",
    "evidence.{target_id}.",
    "testimonies.{target_id}.",
    "hypotheses.{target_id}.",
    "survival.{actor_id}.",
    "survival.{target_id}.",
    "travel_routes.{target_id}.",
    "weather.{target_id}.",
    "camps.{target_id}.",
    "domains.{target_id}.",
    "facilities.{target_id}.",
    "base_inventories.{target_id}.",
    "staff_assignments.{target_id}.",
    "domain_upgrades.{target_id}.",
    "stealth.{actor_id}.",
    "stealth.{target_id}.",
    "noise_events.{target_id}.",
    "cover_states.{target_id}.",
    "current_time",
)


def validate_action_dsl_path_template(path: str) -> None:
    if not path:
        raise ActionDSLValidationError("Action DSL path must be non-empty")
    if any(token in path for token in ("..", "/", "\\", "[", "]", "$", "`")):
        raise ActionDSLValidationError("Action DSL path contains a forbidden path token")
    if any(part == "" for part in path.split(".")):
        raise ActionDSLValidationError("Action DSL path cannot contain empty segments")
    for _, field_name, _, _ in Formatter().parse(path):
        if field_name and field_name not in _ALLOWED_TEMPLATE_FIELDS:
            raise ActionDSLValidationError(f"Unsupported Action DSL path placeholder: {field_name}")
    if "{" in path or "}" in path:
        _ = path.format(actor_id="actor", target_id="target")
    if not any(path == prefix or path.startswith(prefix) for prefix in _ALLOWED_STATE_DELTA_PREFIXES):
        raise ActionDSLValidationError(f"Action DSL path is outside the allowed StateDelta surface: {path}")


def render_action_dsl_template(path: str, *, actor_id: str, target_id: str | None) -> str:
    validate_action_dsl_path_template(path)
    rendered = path.format(actor_id=actor_id, target_id=target_id or "")
    if any(part == "" for part in rendered.split(".")):
        raise ActionDSLValidationError("Rendered Action DSL path cannot contain empty segments")
    return rendered


def render_action_dsl_value(value: Any, *, actor_id: str, target_id: str | None) -> Any:
    if isinstance(value, str):
        return value.format(actor_id=actor_id, target_id=target_id or "")
    if isinstance(value, list):
        return [render_action_dsl_value(item, actor_id=actor_id, target_id=target_id) for item in value]
    if isinstance(value, dict):
        return {
            str(render_action_dsl_value(key, actor_id=actor_id, target_id=target_id)): render_action_dsl_value(
                item,
                actor_id=actor_id,
                target_id=target_id,
            )
            for key, item in value.items()
        }
    return value


def evaluate_precondition(
    precondition: ActionPrecondition,
    state: GameState,
    *,
    actor_id: str | None = None,
    target_id: str | None = None,
) -> ActionDSLResult:
    resolved_actor_id = actor_id or precondition.actor_id
    resolved_target_id = target_id or precondition.target_id
    passed = _evaluate_precondition_boolean(precondition, state, resolved_actor_id, resolved_target_id)
    if not precondition.expected:
        passed = not passed
    return ActionDSLResult(
        passed=passed,
        reason=(
            f"Precondition {precondition.precondition_type.value} "
            f"{'passed' if passed else 'failed'} for actor {resolved_actor_id}."
        ),
    )


def evaluate_check(
    check: ActionCheck,
    state: GameState,
    *,
    actor_id: str | None = None,
    target_id: str | None = None,
    seed: int | None = None,
) -> ActionDSLResult:
    resolved_actor_id = actor_id or check.actor_id
    resolved_target_id = target_id or check.target_id
    rng = Random(seed if seed is not None else check.seed if check.seed is not None else 0)

    if check.check_type == ActionCheckType.FIXED_SUCCESS:
        return ActionDSLResult(passed=True, reason="Fixed success check passed.")
    if check.check_type == ActionCheckType.ITEM_CHECK:
        passed = bool(check.item_id) and has_item(state, resolved_actor_id, check.item_id)
        return ActionDSLResult(passed=passed, reason="Item check evaluated.")
    if check.check_type == ActionCheckType.RANDOM_THRESHOLD:
        roll = rng.randint(1, 100)
        passed = roll <= check.threshold
        return ActionDSLResult(passed=passed, reason="Random threshold check evaluated.", details={"roll": roll})
    if check.check_type == ActionCheckType.SKILL_CHECK:
        roll = rng.randint(1, 20)
        modifier = _skill_modifier(state, resolved_actor_id, check.skill)
        total = roll + modifier + check.bonus
        passed = total >= check.difficulty
        return ActionDSLResult(
            passed=passed,
            reason="Skill check evaluated.",
            details={"roll": roll, "modifier": modifier, "total": total},
        )
    if check.check_type == ActionCheckType.REPUTATION_CHECK:
        reputation = state.factions.get(check.faction_id).reputation.value if check.faction_id in state.factions else 0
        passed = reputation + check.bonus >= check.threshold
        return ActionDSLResult(
            passed=passed,
            reason="Reputation check evaluated.",
            details={"reputation": reputation},
        )
    if check.check_type == ActionCheckType.RELATIONSHIP_CHECK:
        relationship = _relationship_for_check(state, check.relationship_id, resolved_actor_id, resolved_target_id)
        value = getattr(relationship, check.relationship_field, 0) if relationship else 0
        passed = value + check.bonus >= check.threshold
        return ActionDSLResult(
            passed=passed,
            reason="Relationship check evaluated.",
            details={check.relationship_field: value},
        )
    return ActionDSLResult(passed=False, reason=f"Unsupported check: {check.check_type.value}")


def compile_effect(
    effect: ActionEffect,
    state: GameState,
    *,
    event_id: str,
    actor_id: str | None = None,
    target_id: str | None = None,
) -> list[StateDelta]:
    resolved_actor_id = actor_id or effect.actor_id
    resolved_target_id = target_id or effect.target_id

    if effect.effect_type == ActionEffectType.STATE_DELTA_TEMPLATE:
        if effect.state_delta_template is None:
            raise ActionDSLValidationError("state_delta_template effect is missing a template")
        return [
            effect.state_delta_template.to_delta(
                event_id=event_id,
                actor_id=resolved_actor_id,
                target_id=resolved_target_id,
            )
        ]
    if effect.effect_type == ActionEffectType.ADD_FACT_DISCOVERY:
        if not _fact_can_be_discovered_by_player(state, str(effect.fact_id or "")):
            raise ActionDSLValidationError("Action DSL cannot discover hidden or unknown facts for the player.")
        return [
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path="player_visible_facts",
                value=effect.fact_id,
                caused_by_event_id=event_id,
                reason=effect.reason or "Action DSL discovered a fact for the player.",
                metadata=effect.metadata,
            )
        ]
    if effect.effect_type == ActionEffectType.ADD_STATUS:
        _validate_safe_state_id(resolved_actor_id)
        path = "player.status_effects" if resolved_actor_id == state.player.id else f"npcs.{resolved_actor_id}.status_effects"
        return [
            StateDelta(
                operation=StateDeltaOperation.ADD,
                path=path,
                value=effect.status,
                caused_by_event_id=event_id,
                reason=effect.reason or "Action DSL added a status.",
                metadata=effect.metadata,
            )
        ]
    if effect.effect_type == ActionEffectType.CONSUME_ITEM:
        _validate_safe_state_id(effect.item_id or "")
        path = "player.inventory" if resolved_actor_id == state.player.id else f"objects.{effect.item_id}.owner_id"
        operation = StateDeltaOperation.REMOVE if resolved_actor_id == state.player.id else StateDeltaOperation.SET
        value: Any = effect.item_id if resolved_actor_id == state.player.id else None
        return [
            StateDelta(
                operation=operation,
                path=path,
                value=value,
                caused_by_event_id=event_id,
                reason=effect.reason or "Action DSL consumed an item.",
                metadata=effect.metadata,
            )
        ]
    if effect.effect_type == ActionEffectType.ADVANCE_TIME:
        return [make_time_delta(state, effect.minutes).model_copy(update={"caused_by_event_id": event_id})]
    if effect.effect_type == ActionEffectType.CREATE_EVENT_MARKER:
        _validate_safe_state_id(effect.marker_key or "")
        marker_path = f"flags.{effect.marker_key}"
        validate_action_dsl_path_template(marker_path)
        return [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=marker_path,
                value=effect.marker_value,
                caused_by_event_id=event_id,
                reason=effect.reason or "Action DSL created an event marker.",
                metadata=effect.metadata,
            )
        ]
    raise ActionDSLValidationError(f"Unsupported effect: {effect.effect_type.value}")


def _fact_can_be_discovered_by_player(state: GameState, fact_id: str) -> bool:
    if fact_id in state.player_visible_facts:
        return True
    fact = state.facts.get(fact_id)
    if fact is None:
        return False
    return fact.public or fact.visibility in {FactVisibility.PUBLIC, FactVisibility.DISCOVERABLE}


def _evaluate_precondition_boolean(
    precondition: ActionPrecondition,
    state: GameState,
    actor_id: str,
    target_id: str | None,
) -> bool:
    if precondition.precondition_type == ActionPreconditionType.ACTOR_AT_LOCATION:
        return _actor_location(state, actor_id) == precondition.location_id
    if precondition.precondition_type == ActionPreconditionType.TARGET_EXISTS:
        return _target_exists(state, target_id, precondition.target_type)
    if precondition.precondition_type == ActionPreconditionType.TARGET_VISIBLE:
        return bool(target_id) and target_id in _visible_for_actor(state, actor_id)
    if precondition.precondition_type == ActionPreconditionType.ACTOR_HAS_ITEM:
        return bool(precondition.item_id) and has_item(state, actor_id, precondition.item_id)
    if precondition.precondition_type == ActionPreconditionType.ACTOR_HAS_STATUS:
        return bool(precondition.status) and precondition.status in _actor_status_effects(state, actor_id)
    if precondition.precondition_type == ActionPreconditionType.TARGET_HAS_TAG:
        return bool(target_id and precondition.tag) and precondition.tag in _target_tags(state, target_id)
    if precondition.precondition_type == ActionPreconditionType.ACTOR_NOT_IN_COMBAT:
        return not _actor_in_active_combat(state, actor_id)
    if precondition.precondition_type == ActionPreconditionType.NPC_KNOWS_FACT:
        npc_id = precondition.npc_id or actor_id
        return bool(precondition.fact_id) and _npc_knows_fact(state, npc_id, precondition.fact_id)
    if precondition.precondition_type == ActionPreconditionType.FACT_VISIBLE_TO_ACTOR:
        return bool(precondition.fact_id) and _fact_visible_to_actor(state, actor_id, precondition.fact_id)
    return False


def _actor_location(state: GameState, actor_id: str) -> str | None:
    if actor_id == state.player.id:
        return state.player.location_id
    npc = state.npcs.get(actor_id)
    return npc.location_id if npc else None


def _actor_status_effects(state: GameState, actor_id: str) -> list[str]:
    actor = _actor(state, actor_id)
    return list(actor.status_effects) if actor else []


def _actor(state: GameState, actor_id: str) -> PlayerState | NPCState | None:
    if actor_id == state.player.id:
        return state.player
    return state.npcs.get(actor_id)


def _target_exists(state: GameState, target_id: str | None, target_type: ActionDSLTargetType) -> bool:
    if not target_id:
        return False
    if target_type == ActionDSLTargetType.ANY:
        return any(
            target_id in collection
            for collection in (
                state.locations,
                state.objects,
                state.npcs,
                state.facts,
                state.factions,
                state.relationships,
            )
        )
    if target_type == ActionDSLTargetType.LOCATION:
        return target_id in state.locations
    if target_type in {ActionDSLTargetType.OBJECT, ActionDSLTargetType.ITEM}:
        return target_id in state.objects
    if target_type == ActionDSLTargetType.NPC:
        return target_id in state.npcs
    if target_type == ActionDSLTargetType.FACT:
        return target_id in state.facts
    if target_type == ActionDSLTargetType.FACTION:
        return target_id in state.factions
    if target_type == ActionDSLTargetType.RELATIONSHIP:
        return target_id in state.relationships
    return False


def _visible_for_actor(state: GameState, actor_id: str) -> set[str]:
    location_id = _actor_location(state, actor_id)
    if location_id is None:
        return set()
    return set(get_visible_facts(state, actor_id, location_id))


def _target_tags(state: GameState, target_id: str) -> list[str]:
    if target_id in state.objects:
        return state.objects[target_id].tags
    if target_id in state.npcs:
        return list(getattr(state.npcs[target_id], "tags", []))
    if target_id in state.facts:
        return state.facts[target_id].tags
    if target_id in state.factions:
        return state.factions[target_id].tags
    return []


def _actor_in_active_combat(state: GameState, actor_id: str) -> bool:
    return any(
        actor_id in combat.combatant_ids and combat.status == CombatStatus.ACTIVE
        for combat in state.combats.values()
    )


def _npc_knows_fact(state: GameState, npc_id: str, fact_id: str) -> bool:
    npc = state.npcs.get(npc_id)
    if npc and fact_id in npc.knowledge:
        return True
    return fact_id in state.npc_knowledge.get(npc_id, set())


def _fact_visible_to_actor(state: GameState, actor_id: str, fact_id: str) -> bool:
    fact = state.facts.get(fact_id)
    if fact is None:
        return False
    if actor_id == state.player.id:
        return fact_id in state.player_visible_facts or fact.visibility == FactVisibility.PUBLIC or fact.public
    return fact.visibility == FactVisibility.PUBLIC or actor_id in fact.known_by or _npc_knows_fact(state, actor_id, fact_id)


def _skill_modifier(state: GameState, actor_id: str, skill: str | None) -> int:
    actor = _actor(state, actor_id)
    if actor is None or skill is None:
        return 0
    if skill == "stealth":
        return getattr(actor, "stealth_modifier", 0)
    if skill == "combat":
        return getattr(actor, "attack", 0)
    if skill == "defense":
        return getattr(actor, "defense", 0)
    return int(state.flags.get(f"skill_{skill}", 0) or 0)


def _relationship_for_check(
    state: GameState,
    relationship_id: str | None,
    actor_id: str,
    target_id: str | None,
) -> RelationshipState | None:
    if relationship_id:
        return state.relationships.get(relationship_id)
    if not target_id:
        return None
    for relationship in state.relationships.values():
        if relationship.source_id == actor_id and relationship.target_id == target_id:
            return relationship
    return None


def _validate_safe_state_id(value: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ActionDSLValidationError(f"Unsafe Action DSL state id: {value}")
