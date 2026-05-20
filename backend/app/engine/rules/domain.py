from random import Random

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    BaseInventoryState,
    DomainState,
    DomainUpgradeDefinition,
    FacilityState,
    GameState,
    StaffAssignmentState,
)
from app.engine.rules.inventory import has_item
from app.engine.rules.life_state import can_act


class DomainRuleError(ValueError):
    """Raised when domain/base management rules cannot resolve cleanly."""


class DomainOperationResult(BaseModel):
    domain_id: str
    state_deltas: list[StateDelta] = Field(default_factory=list)
    event: Event
    rejected_reason: str | None = None


class DomainTickResult(BaseModel):
    domain_id: str
    income: int = 0
    upkeep: int = 0
    risk_triggered: bool = False
    state_deltas: list[StateDelta] = Field(default_factory=list)
    event: Event


def claim_base(state: GameState, domain_id: str, location_id: str, *, name: str = "") -> DomainOperationResult:
    event_id = f"domain-claim-{domain_id}-{state.turn}"
    if location_id not in state.locations:
        return _operation_result(state, domain_id, [], "claim_base", rejected_reason="location_missing", event_id=event_id)
    if domain_id in state.domains and state.domains[domain_id].claimed:
        return _operation_result(state, domain_id, [], "claim_base", rejected_reason="domain_already_claimed", event_id=event_id)
    domain = DomainState(id=domain_id, name=name or domain_id, location_id=location_id, owner_id=state.player.id, claimed=True)
    inventory = BaseInventoryState(domain_id=domain_id)
    deltas = [
        StateDelta(operation=StateDeltaOperation.SET, path=f"domains.{domain_id}", value=domain.model_dump(mode="json"), caused_by_event_id=event_id, reason="Player claimed a base."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"base_inventories.{domain_id}", value=inventory.model_dump(mode="json"), caused_by_event_id=event_id, reason="Base inventory initialized."),
    ]
    return _operation_result(state, domain_id, deltas, "claim_base", event_id=event_id)


def build_facility(
    state: GameState,
    domain_id: str,
    facility_id: str,
    facility_type: str,
    *,
    cost: int = 0,
    income: int = 0,
    upkeep: int = 0,
    staff_slots: int = 0,
    tags: list[str] | None = None,
) -> DomainOperationResult:
    event_id = f"domain-build-{facility_id}-{state.turn}"
    domain = state.domains.get(domain_id)
    if domain is None or not domain.claimed:
        return _operation_result(state, domain_id, [], "build_facility", rejected_reason="domain_not_claimed", event_id=event_id)
    if facility_id in state.facilities:
        return _operation_result(state, domain_id, [], "build_facility", rejected_reason="facility_exists", event_id=event_id)
    if state.player.currency < cost:
        return _operation_result(state, domain_id, [], "build_facility", rejected_reason="insufficient_currency", event_id=event_id)
    facility = FacilityState(id=facility_id, domain_id=domain_id, facility_type=facility_type, income=income, upkeep=upkeep, staff_slots=staff_slots, tags=tags or [])
    next_facility_ids = sorted({*domain.facility_ids, facility_id})
    deltas = [
        StateDelta(operation=StateDeltaOperation.INC, path="player.currency", value=-cost, caused_by_event_id=event_id, reason="Facility build consumed currency.", metadata={"source": "domain"}),
        StateDelta(operation=StateDeltaOperation.SET, path=f"facilities.{facility_id}", value=facility.model_dump(mode="json"), caused_by_event_id=event_id, reason="Facility built."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"domains.{domain_id}.facility_ids", value=next_facility_ids, caused_by_event_id=event_id, reason="Domain facility list updated."),
    ]
    return _operation_result(state, domain_id, deltas, "build_facility", event_id=event_id)


def assign_staff(state: GameState, domain_id: str, npc_id: str, facility_id: str, *, role: str = "worker") -> DomainOperationResult:
    event_id = f"domain-assign-{npc_id}-{facility_id}-{state.turn}"
    domain = state.domains.get(domain_id)
    facility = state.facilities.get(facility_id)
    npc = state.npcs.get(npc_id)
    if domain is None or not domain.claimed:
        return _operation_result(state, domain_id, [], "assign_staff", rejected_reason="domain_not_claimed", event_id=event_id)
    if facility is None or facility.domain_id != domain_id:
        return _operation_result(state, domain_id, [], "assign_staff", rejected_reason="facility_missing", event_id=event_id)
    if npc is None or not can_act(state, npc_id):
        return _operation_result(state, domain_id, [], "assign_staff", rejected_reason="npc_unavailable", event_id=event_id)
    current_staff = [assignment for assignment in state.staff_assignments.values() if assignment.facility_id == facility_id and assignment.active]
    if len(current_staff) >= facility.staff_slots:
        return _operation_result(state, domain_id, [], "assign_staff", rejected_reason="facility_staff_full", event_id=event_id)
    assignment_id = f"{domain_id}_{facility_id}_{npc_id}"
    assignment = StaffAssignmentState(id=assignment_id, domain_id=domain_id, npc_id=npc_id, facility_id=facility_id, role=role)
    next_assignments = sorted({*domain.staff_assignment_ids, assignment_id})
    deltas = [
        StateDelta(operation=StateDeltaOperation.SET, path=f"staff_assignments.{assignment_id}", value=assignment.model_dump(mode="json"), caused_by_event_id=event_id, reason="Staff assigned to facility."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"domains.{domain_id}.staff_assignment_ids", value=next_assignments, caused_by_event_id=event_id, reason="Domain staff list updated."),
    ]
    return _operation_result(state, domain_id, deltas, "assign_staff", event_id=event_id)


def upgrade_facility(state: GameState, domain_id: str, facility_id: str, upgrade_id: str) -> DomainOperationResult:
    event_id = f"domain-upgrade-{facility_id}-{upgrade_id}-{state.turn}"
    facility = state.facilities.get(facility_id)
    upgrade = state.domain_upgrades.get(upgrade_id)
    if facility is None or facility.domain_id != domain_id:
        return _operation_result(state, domain_id, [], "upgrade_facility", rejected_reason="facility_missing", event_id=event_id)
    if upgrade is None or upgrade.facility_type != facility.facility_type:
        return _operation_result(state, domain_id, [], "upgrade_facility", rejected_reason="upgrade_missing", event_id=event_id)
    if facility.level >= upgrade.target_level:
        return _operation_result(state, domain_id, [], "upgrade_facility", rejected_reason="facility_already_upgraded", event_id=event_id)
    if not set(upgrade.required_tags).issubset(set(facility.tags)):
        return _operation_result(state, domain_id, [], "upgrade_facility", rejected_reason="missing_required_tags", event_id=event_id)
    if state.player.currency < upgrade.cost:
        return _operation_result(state, domain_id, [], "upgrade_facility", rejected_reason="insufficient_currency", event_id=event_id)
    deltas = [
        StateDelta(operation=StateDeltaOperation.INC, path="player.currency", value=-upgrade.cost, caused_by_event_id=event_id, reason="Facility upgrade consumed currency.", metadata={"source": "domain"}),
        StateDelta(operation=StateDeltaOperation.SET, path=f"facilities.{facility_id}.level", value=upgrade.target_level, caused_by_event_id=event_id, reason="Facility level upgraded."),
        StateDelta(operation=StateDeltaOperation.INC, path=f"facilities.{facility_id}.income", value=upgrade.income_delta, caused_by_event_id=event_id, reason="Facility upgrade changed income."),
        StateDelta(operation=StateDeltaOperation.INC, path=f"facilities.{facility_id}.upkeep", value=upgrade.upkeep_delta, caused_by_event_id=event_id, reason="Facility upgrade changed upkeep."),
    ]
    return _operation_result(state, domain_id, deltas, "upgrade_facility", event_id=event_id)


def store_item(state: GameState, domain_id: str, item_id: str) -> DomainOperationResult:
    event_id = f"domain-store-{domain_id}-{item_id}-{state.turn}"
    if domain_id not in state.domains or domain_id not in state.base_inventories:
        return _operation_result(state, domain_id, [], "store_item", rejected_reason="domain_not_claimed", event_id=event_id)
    if not has_item(state, state.player.id, item_id):
        return _operation_result(state, domain_id, [], "store_item", rejected_reason="item_not_owned", event_id=event_id)
    inventory = state.base_inventories[domain_id]
    deltas = [
        StateDelta(operation=StateDeltaOperation.SET, path=f"objects.{item_id}.owner_id", value=None, caused_by_event_id=event_id, reason="Stored item left player inventory."),
        StateDelta(operation=StateDeltaOperation.ADD, path=f"base_inventories.{domain_id}.item_ids", value=item_id, caused_by_event_id=event_id, reason="Stored item entered base inventory."),
    ]
    if item_id in inventory.item_ids:
        deltas = []
    return _operation_result(state, domain_id, deltas, "store_item", event_id=event_id)


def withdraw_item(state: GameState, domain_id: str, item_id: str) -> DomainOperationResult:
    event_id = f"domain-withdraw-{domain_id}-{item_id}-{state.turn}"
    inventory = state.base_inventories.get(domain_id)
    if inventory is None:
        return _operation_result(state, domain_id, [], "withdraw_item", rejected_reason="domain_not_claimed", event_id=event_id)
    if item_id not in inventory.item_ids:
        return _operation_result(state, domain_id, [], "withdraw_item", rejected_reason="item_not_stored", event_id=event_id)
    deltas = [
        StateDelta(operation=StateDeltaOperation.REMOVE, path=f"base_inventories.{domain_id}.item_ids", value=item_id, caused_by_event_id=event_id, reason="Withdrawn item left base inventory."),
        StateDelta(operation=StateDeltaOperation.SET, path=f"objects.{item_id}.owner_id", value=state.player.id, caused_by_event_id=event_id, reason="Withdrawn item entered player inventory."),
    ]
    return _operation_result(state, domain_id, deltas, "withdraw_item", event_id=event_id)


def collect_income(state: GameState, domain_id: str) -> DomainOperationResult:
    event_id = f"domain-income-{domain_id}-{state.turn}"
    if domain_id not in state.domains:
        return _operation_result(state, domain_id, [], "collect_income", rejected_reason="domain_not_claimed", event_id=event_id)
    income = _domain_income(state, domain_id)
    if income <= 0:
        return _operation_result(state, domain_id, [], "collect_income", rejected_reason="no_income", event_id=event_id)
    deltas = [
        StateDelta(operation=StateDeltaOperation.INC, path="player.currency", value=income, caused_by_event_id=event_id, reason="Collected base income.", metadata={"source": "domain"}),
        StateDelta(operation=StateDeltaOperation.SET, path=f"social_flags.domain_income_collected_{domain_id}_{state.turn}", value=True, caused_by_event_id=event_id, reason="Domain income collection marked."),
    ]
    return _operation_result(state, domain_id, deltas, "collect_income", event_id=event_id)


def domain_tick(state: GameState, domain_id: str, rng: Random | None = None) -> DomainTickResult:
    active_rng = rng or Random(0)
    event_id = f"domain-tick-{domain_id}-{state.turn}"
    domain = state.domains.get(domain_id)
    if domain is None:
        event = Event(event_id=event_id, turn=state.turn, actor_id="system", action_type="domain_tick", result="missing_domain", visible_to_player=False, state_deltas=[], allow_empty_delta=True)
        return DomainTickResult(domain_id=domain_id, state_deltas=[], event=event)
    income = _domain_income(state, domain_id)
    upkeep = _domain_upkeep(state, domain_id)
    risk_triggered = active_rng.randint(1, 100) <= domain.risk_level
    deltas = [
        StateDelta(operation=StateDeltaOperation.INC, path=f"domains.{domain_id}.treasury", value=income - upkeep, caused_by_event_id=event_id, reason="Domain tick applied income and upkeep.", metadata={"source": "domain_tick"}),
    ]
    if risk_triggered:
        deltas.append(StateDelta(operation=StateDeltaOperation.SET, path=f"social_flags.domain_risk_{domain_id}_{state.turn}", value=True, caused_by_event_id=event_id, reason="Domain tick triggered a bounded risk marker.", metadata={"source": "domain_tick"}))
    for assignment in sorted(state.staff_assignments.values(), key=lambda item: item.id):
        if assignment.domain_id == domain_id and assignment.active and not can_act(state, assignment.npc_id):
            deltas.append(StateDelta(operation=StateDeltaOperation.SET, path=f"staff_assignments.{assignment.id}.active", value=False, caused_by_event_id=event_id, reason="Domain tick deactivated unavailable staff.", metadata={"source": "domain_tick"}))
    event = Event(event_id=event_id, turn=state.turn, actor_id="system", action_type="domain_tick", result="success", visible_to_player=False, state_deltas=deltas)
    return DomainTickResult(domain_id=domain_id, income=income, upkeep=upkeep, risk_triggered=risk_triggered, state_deltas=deltas, event=event)


def _domain_income(state: GameState, domain_id: str) -> int:
    return sum(facility.income for facility in state.facilities.values() if facility.domain_id == domain_id)


def _domain_upkeep(state: GameState, domain_id: str) -> int:
    return sum(facility.upkeep for facility in state.facilities.values() if facility.domain_id == domain_id)


def _operation_result(
    state: GameState,
    domain_id: str,
    deltas: list[StateDelta],
    action_type: str,
    *,
    rejected_reason: str | None = None,
    event_id: str,
) -> DomainOperationResult:
    event = Event(
        event_id=event_id,
        turn=state.turn,
        actor_id=state.player.id,
        action_type=action_type,
        result="rejected" if rejected_reason else "success",
        target_id=domain_id,
        visible_to_player=True,
        state_deltas=deltas,
        allow_empty_delta=not deltas,
    )
    return DomainOperationResult(domain_id=domain_id, state_deltas=deltas, event=event, rejected_reason=rejected_reason)
