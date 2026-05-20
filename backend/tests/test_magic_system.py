from random import Random

from app.core.state_delta import StateDeltaOperation, apply_delta
from app.core.world_state import (
    GameState,
    LocationState,
    MagicResourceState,
    NPCState,
    PlayerState,
)
from app.engine.action_registry import ActionRegistry
from app.engine.actions.dsl import (
    ActionCheck,
    ActionCheckType,
    ActionEffect,
    ActionEffectType,
    ActionStateDeltaTemplate,
)
from app.engine.actions.schemas import SuccessLevel
from app.engine.rules.magic import (
    CastSpellActionHandler,
    MagicModuleConfig,
    SpellCrimePolicy,
    SpellDefinition,
    SpellTargetType,
    SpellVisibilityPolicy,
    cast_spell_action_definition,
)
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.session_store import build_visible_state


def _state(*, mana: int = 5) -> GameState:
    return GameState(
        world_id="magic-test",
        turn=3,
        player=PlayerState(location_id="square"),
        locations={"square": LocationState(id="square", name="Town Square")},
        npcs={
            "guard": NPCState(id="guard", location_id="square", visible=True),
            "hidden_mage": NPCState(id="hidden_mage", location_id="square", visible=True, hidden=True),
        },
        magic_resources={"player": MagicResourceState(mana=mana, max_mana=10, focus=2, max_focus=2)},
    )


def _intent(raw_text: str = "cast spark", target_id: str | None = "guard") -> PlayerIntent:
    return PlayerIntent(
        action_type=PlayerActionType.UNKNOWN,
        raw_text=raw_text,
        confidence=1.0,
        requires_clarification=False,
        target_id=target_id,
    )


def _damage_effect(amount: int = -2) -> ActionEffect:
    return ActionEffect(
        effect_type=ActionEffectType.STATE_DELTA_TEMPLATE,
        state_delta_template=ActionStateDeltaTemplate(
            operation=StateDeltaOperation.INC,
            path="npcs.{target_id}.hp",
            value=amount,
            reason="Spell damage.",
        ),
    )


def _spell(**updates: object) -> SpellDefinition:
    payload = {
        "id": "spark",
        "name": "Spark",
        "school": "fire",
        "cost": 2,
        "target_types": [SpellTargetType.NPC],
        "checks": [ActionCheck(check_type=ActionCheckType.FIXED_SUCCESS)],
        "effects": [_damage_effect()],
        "aliases": ["cast spark", "spark"],
    }
    payload.update(updates)
    return SpellDefinition.model_validate(payload)


def _handler(spell: SpellDefinition | None = None) -> CastSpellActionHandler:
    active_spell = spell or _spell()
    return CastSpellActionHandler(MagicModuleConfig(spells={active_spell.id: active_spell}))


def _apply_all(state: GameState, deltas: list) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def test_cast_spell_success_consumes_mana() -> None:
    state = _state(mana=5)

    execution = _handler().resolve_with_event(_intent(), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert execution.action_result.success_level == SuccessLevel.SUCCESS
    assert next_state.magic_resources["player"].mana == 3
    assert state.magic_resources["player"].mana == 5


def test_spell_effect_uses_state_delta() -> None:
    execution = _handler().resolve_with_event(_intent(), _state(), Random(1))

    assert any(delta.path == "npcs.guard.hp" and delta.operation == StateDeltaOperation.INC for delta in execution.action_result.state_deltas)
    assert execution.event.state_deltas == execution.action_result.state_deltas


def test_insufficient_mana_fails_without_deltas() -> None:
    execution = _handler().resolve_with_event(_intent(), _state(mana=1), Random(1))

    assert execution.action_result.success_level == SuccessLevel.FAILURE
    assert execution.action_result.reason == "Insufficient mana."
    assert execution.action_result.state_deltas == []


def test_invalid_spell_target_returns_invalid() -> None:
    execution = _handler().resolve_with_event(_intent(target_id="missing_npc"), _state(), Random(1))

    assert execution.action_result.success_level == SuccessLevel.INVALID
    assert execution.event.allow_empty_delta is True


def test_public_illegal_spell_triggers_crime_and_witness() -> None:
    spell = _spell(
        crime_policy=SpellCrimePolicy(illegal_public_cast=True, crime_type="illegal_fire_magic", severity=3),
        visibility_policy=SpellVisibilityPolicy(public_cast_visible=True),
    )
    state = _state()

    execution = _handler(spell).resolve_with_event(_intent(), state, Random(1))
    next_state = _apply_all(state, execution.action_result.state_deltas)

    assert "magic_crime_spark_3" in next_state.crimes
    assert next_state.crimes["magic_crime_spark_3"].crime_type == "illegal_fire_magic"
    assert "magic_crime_spark_3:guard" in next_state.witnesses
    assert "magic_crime_spark_3:hidden_mage" not in next_state.witnesses


def test_hidden_magic_effect_does_not_leak_to_player_visible_state() -> None:
    spell = _spell(hidden_effect=True, visibility_policy=SpellVisibilityPolicy(hidden_effect_player_visible=False))
    state = _state()

    execution = _handler(spell).resolve_with_event(_intent(), state, Random(1))
    visible_payload = build_visible_state(state).model_dump_json()

    assert execution.event.visible_to_player is False
    assert execution.action_result.visible_facts == []
    assert "magic_effect:spark" in execution.action_result.hidden_facts
    assert "magic_effect:spark" not in visible_payload


def test_save_load_preserves_magic_state() -> None:
    state = _state(mana=7)
    restored = GameState.model_validate_json(state.model_dump_json())

    assert restored.magic_resources["player"].mana == 7
    assert restored.magic_resources["player"].max_mana == 10


def test_cast_spell_action_can_register_with_action_registry() -> None:
    spell = _spell()
    registry = ActionRegistry(include_core=False)
    definition = cast_spell_action_definition(MagicModuleConfig(spells={spell.id: spell}))
    registry.register_module_action(definition, module_id="magic", handler=_handler(spell))

    handler = registry.get_handler_for_intent(_intent(), _state())

    assert handler is not None
    assert registry.get_action_definition("magic.cast_spell") is not None
