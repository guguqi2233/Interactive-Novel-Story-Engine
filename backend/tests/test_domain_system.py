from random import Random

from app.core.event_log import Event
from app.core.state_delta import apply_delta
from app.core.world_state import (
    ActorCondition,
    DomainUpgradeDefinition,
    FacilityState,
    GameState,
    LocationState,
    NPCState,
    PlayerState,
    WorldObjectState,
)
from app.engine.rules.domain import (
    assign_staff,
    build_facility,
    claim_base,
    collect_income,
    domain_tick,
    store_item,
    upgrade_facility,
    withdraw_item,
)


def make_state() -> GameState:
    return GameState(
        world_id="domain-test",
        turn=3,
        player=PlayerState(location_id="hall", currency=50),
        locations={"hall": LocationState(id="hall", name="Hall")},
        npcs={"mira": NPCState(id="mira", location_id="hall")},
        objects={"relic": WorldObjectState(id="relic", owner_id="player", portable=True)},
    )


def apply_all(state: GameState, deltas) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def claimed_state() -> GameState:
    state = make_state()
    return apply_all(state, claim_base(state, "base_1", "hall", name="Old Hall").state_deltas)


def test_claim_base_success() -> None:
    state = make_state()

    result = claim_base(state, "base_1", "hall", name="Old Hall")
    next_state = apply_all(state, result.state_deltas)

    assert result.rejected_reason is None
    assert isinstance(result.event, Event)
    assert next_state.domains["base_1"].claimed is True
    assert "base_1" in next_state.base_inventories


def test_build_facility_consumes_resources() -> None:
    state = claimed_state()

    result = build_facility(state, "base_1", "workshop", "workshop", cost=15, income=4, upkeep=1, staff_slots=1)
    next_state = apply_all(state, result.state_deltas)

    assert result.rejected_reason is None
    assert next_state.player.currency == state.player.currency - 15
    assert next_state.facilities["workshop"].income == 4
    assert "workshop" in next_state.domains["base_1"].facility_ids


def test_assign_staff_requires_valid_npc() -> None:
    state = claimed_state()
    state = apply_all(state, build_facility(state, "base_1", "workshop", "workshop", staff_slots=1).state_deltas)
    missing = assign_staff(state, "base_1", "missing", "workshop")
    state.npcs["mira"].condition = ActorCondition.INCAPACITATED
    inactive = assign_staff(state, "base_1", "mira", "workshop")
    state.npcs["mira"].condition = ActorCondition.HEALTHY
    active = assign_staff(state, "base_1", "mira", "workshop")
    next_state = apply_all(state, active.state_deltas)

    assert missing.rejected_reason == "npc_unavailable"
    assert inactive.rejected_reason == "npc_unavailable"
    assert active.rejected_reason is None
    assert next_state.staff_assignments["base_1_workshop_mira"].npc_id == "mira"


def test_collect_income_uses_state_delta() -> None:
    state = claimed_state()
    state = apply_all(state, build_facility(state, "base_1", "market", "market", income=6).state_deltas)

    result = collect_income(state, "base_1")
    next_state = apply_all(state, result.state_deltas)

    assert result.rejected_reason is None
    assert next_state.player.currency == state.player.currency + 6
    assert result.event.state_deltas == result.state_deltas


def test_upkeep_applies_in_domain_tick() -> None:
    state = claimed_state()
    state = apply_all(state, build_facility(state, "base_1", "market", "market", income=6, upkeep=2).state_deltas)

    tick = domain_tick(state, "base_1", Random(99))
    next_state = apply_all(state, tick.state_deltas)

    assert tick.income == 6
    assert tick.upkeep == 2
    assert next_state.domains["base_1"].treasury == 4


def test_invalid_facility_rejected() -> None:
    state = claimed_state()

    result = assign_staff(state, "base_1", "mira", "missing_facility")

    assert result.rejected_reason == "facility_missing"
    assert result.state_deltas == []


def test_store_and_withdraw_item_respects_inventory() -> None:
    state = claimed_state()

    stored = store_item(state, "base_1", "relic")
    state = apply_all(state, stored.state_deltas)
    withdrawn = withdraw_item(state, "base_1", "relic")
    next_state = apply_all(state, withdrawn.state_deltas)

    assert "relic" in state.base_inventories["base_1"].item_ids
    assert state.objects["relic"].owner_id is None
    assert "relic" not in next_state.base_inventories["base_1"].item_ids
    assert next_state.objects["relic"].owner_id == "player"


def test_upgrade_facility_updates_income_and_upkeep() -> None:
    state = claimed_state()
    state = apply_all(state, build_facility(state, "base_1", "workshop", "workshop", cost=0, income=1, upkeep=1, tags=["tools"]).state_deltas)
    state.domain_upgrades["workshop_2"] = DomainUpgradeDefinition(id="workshop_2", facility_type="workshop", target_level=2, cost=10, income_delta=3, upkeep_delta=1, required_tags=["tools"])

    result = upgrade_facility(state, "base_1", "workshop", "workshop_2")
    next_state = apply_all(state, result.state_deltas)

    assert result.rejected_reason is None
    assert next_state.facilities["workshop"].level == 2
    assert next_state.facilities["workshop"].income == 4
    assert next_state.facilities["workshop"].upkeep == 2


def test_domain_tick_can_deactivate_unavailable_staff_and_mark_risk() -> None:
    state = claimed_state()
    state.domains["base_1"].risk_level = 100
    state.facilities["workshop"] = FacilityState(id="workshop", domain_id="base_1", facility_type="workshop", staff_slots=1)
    state.domains["base_1"].facility_ids.append("workshop")
    state = apply_all(state, assign_staff(state, "base_1", "mira", "workshop").state_deltas)
    state.npcs["mira"].condition = ActorCondition.INCAPACITATED

    tick = domain_tick(state, "base_1", Random(1))
    next_state = apply_all(state, tick.state_deltas)

    assert tick.risk_triggered is True
    assert next_state.social_flags["domain_risk_base_1_3"] is True
    assert next_state.staff_assignments["base_1_workshop_mira"].active is False


def test_save_load_preserves_domain_state() -> None:
    state = claimed_state()
    state = apply_all(state, build_facility(state, "base_1", "market", "market", income=3).state_deltas)

    loaded = GameState.model_validate_json(state.model_dump_json())

    assert loaded.domains["base_1"].claimed is True
    assert loaded.facilities["market"].income == 3
    assert loaded.base_inventories["base_1"].domain_id == "base_1"
