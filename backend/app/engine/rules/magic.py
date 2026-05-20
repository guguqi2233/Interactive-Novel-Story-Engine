from enum import StrEnum
from random import Random
from pydantic import BaseModel, Field, field_validator

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import CrimeState, CrimeStatus, GameState, MagicResourceState, WitnessRecord
from app.engine.actions.base import ActionHandler
from app.engine.actions.declarative import (
    DeclarativeActionCategory,
    DeclarativeActionDefinition,
    DeclarativeActionTargetSpec,
    DeclarativeOutcome,
    DeclarativeTargetKind,
    DeclarativeVisibilityPolicy,
)
from app.engine.actions.dsl import (
    ActionCheck,
    ActionEffect,
    ActionPrecondition,
    compile_effect,
    evaluate_check,
    evaluate_precondition,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.rules.visibility import get_visible_facts
from app.llm.schemas import PlayerActionType, PlayerIntent


class SpellSchool(StrEnum):
    ARCANE = "arcane"
    HEALING = "healing"
    ILLUSION = "illusion"
    WARDING = "warding"
    FIRE = "fire"
    SHADOW = "shadow"


class SpellTargetType(StrEnum):
    SELF = "self"
    LOCATION = "location"
    OBJECT = "object"
    NPC = "npc"


class SpellVisibilityPolicy(BaseModel):
    public_cast_visible: bool = True
    hidden_effect_player_visible: bool = False
    reveal_target_on_success: bool = True


class SpellCrimePolicy(BaseModel):
    illegal_public_cast: bool = False
    crime_type: str = "illegal_magic"
    severity: int = Field(default=1, ge=0)
    report_to_faction_id: str | None = None


class SpellDefinition(BaseModel):
    id: str
    name: str
    school: SpellSchool = SpellSchool.ARCANE
    cost: int = Field(default=0, ge=0)
    target_types: list[SpellTargetType] = Field(default_factory=lambda: [SpellTargetType.SELF])
    preconditions: list[ActionPrecondition] = Field(default_factory=list)
    checks: list[ActionCheck] = Field(default_factory=list)
    effects: list[ActionEffect] = Field(default_factory=list)
    failure_effects: list[ActionEffect] = Field(default_factory=list)
    visibility_policy: SpellVisibilityPolicy = Field(default_factory=SpellVisibilityPolicy)
    crime_policy: SpellCrimePolicy = Field(default_factory=SpellCrimePolicy)
    aliases: list[str] = Field(default_factory=list)
    hidden_effect: bool = False

    @field_validator("id")
    @classmethod
    def validate_spell_id(cls, value: str) -> str:
        if not value or any(token in value for token in ("/", "\\", "..", "`", "$")):
            raise ValueError("Spell id must be a safe local identifier")
        return value


class MagicModuleConfig(BaseModel):
    module_id: str = "magic"
    default_resource: MagicResourceState = Field(default_factory=MagicResourceState)
    spells: dict[str, SpellDefinition] = Field(default_factory=dict)


class SpellCastResult(BaseModel):
    spell_id: str
    action_result: ActionResult
    event: Event


class CastSpellActionHandler(ActionHandler):
    action_type = PlayerActionType.UNKNOWN

    def __init__(self, config: MagicModuleConfig) -> None:
        self.config = config

    def can_handle(self, intent: PlayerIntent, state: GameState) -> bool:
        return self._spell_for_intent(intent) is not None

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        return self.resolve_with_event(intent, state, rng).action_result

    def resolve_with_event(self, intent: PlayerIntent, state: GameState, rng: Random | None = None) -> SpellCastResult:
        active_rng = rng or Random(0)
        spell = self._spell_for_intent(intent)
        if spell is None:
            return self._invalid_result("unknown_spell", intent, state, "No known spell matches this action.")

        event_id = f"event-cast-spell-{spell.id}-{state.turn}"
        target_issue = self._validate_target(spell, intent, state)
        if target_issue is not None:
            return self._result(spell, event_id, intent, state, SuccessLevel.INVALID, target_issue, [], visible_to_player=False)

        resources = state.magic_resources.get(state.player.id)
        if resources is None or resources.mana < spell.cost:
            return self._result(spell, event_id, intent, state, SuccessLevel.FAILURE, "Insufficient mana.", [], visible_to_player=True)

        precondition_issue = self._check_preconditions(spell, intent, state)
        if precondition_issue is not None:
            return self._result(spell, event_id, intent, state, SuccessLevel.FAILURE, precondition_issue, [], visible_to_player=True)

        check_issue = self._run_checks(spell, intent, state, active_rng)
        success = check_issue is None
        effect_source = spell.effects if success else spell.failure_effects
        deltas = self._resource_deltas(event_id, spell)
        deltas.extend(self._effect_deltas(effect_source, event_id, intent, state))
        deltas.extend(self._crime_deltas(spell, event_id, intent, state) if success else [])

        hidden_facts: list[str] = []
        visible_facts: list[str] = []
        visible_to_player = True
        if spell.hidden_effect and not spell.visibility_policy.hidden_effect_player_visible:
            hidden_facts.append(f"magic_effect:{spell.id}")
            visible_to_player = False
        else:
            visible_facts.append(f"spell_cast:{spell.id}")
            if intent.target_id and spell.visibility_policy.reveal_target_on_success:
                visible_facts.append(intent.target_id)

        reason = "Spell resolved by deterministic magic rules." if success else check_issue or "Spell failed."
        return self._result(
            spell,
            event_id,
            intent,
            state,
            SuccessLevel.SUCCESS if success else SuccessLevel.FAILURE,
            reason,
            deltas,
            visible_to_player=visible_to_player,
            visible_facts=visible_facts,
            hidden_facts=hidden_facts,
        )

    def _spell_for_intent(self, intent: PlayerIntent) -> SpellDefinition | None:
        normalized = intent.raw_text.strip().lower()
        for spell in self.config.spells.values():
            aliases = {spell.id.lower(), spell.name.lower(), *[alias.lower() for alias in spell.aliases]}
            if normalized in aliases or any(normalized.startswith(f"cast {alias}") for alias in aliases):
                return spell
        return None

    def _validate_target(self, spell: SpellDefinition, intent: PlayerIntent, state: GameState) -> str | None:
        if SpellTargetType.SELF in spell.target_types and not intent.target_id:
            return None
        if not intent.target_id:
            return "Spell requires a target."
        visible = set(get_visible_facts(state, state.player.id, state.player.location_id))
        if SpellTargetType.LOCATION in spell.target_types and intent.target_id in state.locations:
            return None
        if SpellTargetType.OBJECT in spell.target_types and intent.target_id in state.objects and intent.target_id in visible:
            return None
        if SpellTargetType.NPC in spell.target_types and intent.target_id in state.npcs and intent.target_id in visible:
            return None
        if SpellTargetType.SELF in spell.target_types and intent.target_id == state.player.id:
            return None
        return "Invalid or invisible spell target."

    def _check_preconditions(self, spell: SpellDefinition, intent: PlayerIntent, state: GameState) -> str | None:
        for precondition in spell.preconditions:
            result = evaluate_precondition(precondition, state, actor_id=state.player.id, target_id=intent.target_id)
            if not result.passed:
                return result.reason
        return None

    def _run_checks(self, spell: SpellDefinition, intent: PlayerIntent, state: GameState, rng: Random) -> str | None:
        for index, check in enumerate(spell.checks):
            result = evaluate_check(
                check,
                state,
                actor_id=state.player.id,
                target_id=intent.target_id,
                seed=rng.randint(0, 999_999) + index,
            )
            if not result.passed:
                return result.reason
        return None

    def _resource_deltas(self, event_id: str, spell: SpellDefinition) -> list[StateDelta]:
        if spell.cost <= 0:
            return []
        return [
            StateDelta(
                operation=StateDeltaOperation.INC,
                path=f"magic_resources.{self._safe_actor_id('player')}.mana",
                value=-spell.cost,
                caused_by_event_id=event_id,
                reason=f"Mana cost for spell {spell.id}.",
            )
        ]

    def _effect_deltas(
        self,
        effects: list[ActionEffect],
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
    ) -> list[StateDelta]:
        deltas: list[StateDelta] = []
        for effect in effects:
            deltas.extend(
                compile_effect(
                    effect,
                    state,
                    event_id=event_id,
                    actor_id=state.player.id,
                    target_id=intent.target_id,
                )
            )
        return deltas

    def _crime_deltas(self, spell: SpellDefinition, event_id: str, intent: PlayerIntent, state: GameState) -> list[StateDelta]:
        if not spell.crime_policy.illegal_public_cast or not spell.visibility_policy.public_cast_visible:
            return []
        witness_ids = sorted(
            npc.id
            for npc in state.npcs.values()
            if npc.location_id == state.player.location_id and npc.visible and not npc.hidden
        )
        if not witness_ids:
            return []
        crime_id = f"magic_crime_{spell.id}_{state.turn}"
        crime = CrimeState(
            id=crime_id,
            crime_type=spell.crime_policy.crime_type,
            actor_id=state.player.id,
            target_id=intent.target_id,
            location_id=state.player.location_id,
            turn=state.turn,
            created_turn=state.turn,
            witness_ids=witness_ids,
            witnessed_by=witness_ids,
            reported_to_factions=[spell.crime_policy.report_to_faction_id] if spell.crime_policy.report_to_faction_id else [],
            severity=spell.crime_policy.severity,
            known_to_player=True,
            status=CrimeStatus.WITNESSED,
            tags=["magic", spell.school.value],
        )
        deltas: list[StateDelta] = [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"crimes.{crime_id}",
                value=crime.model_dump(mode="json"),
                caused_by_event_id=event_id,
                reason="Public illegal spell created a crime record.",
            )
        ]
        for witness_id in witness_ids:
            witness = WitnessRecord(
                id=f"{crime_id}:{witness_id}",
                npc_id=witness_id,
                crime_id=crime_id,
                certainty=80,
                confidence=80,
                saw_actor=True,
                saw_target=bool(intent.target_id),
                known_to_player=True,
            )
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"witnesses.{witness.id}",
                    value=witness.model_dump(mode="json"),
                    caused_by_event_id=event_id,
                    reason="Public illegal spell created a witness record.",
                )
            )
        return deltas

    def _result(
        self,
        spell: SpellDefinition,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
        level: SuccessLevel,
        reason: str,
        deltas: list[StateDelta],
        *,
        visible_to_player: bool,
        visible_facts: list[str] | None = None,
        hidden_facts: list[str] | None = None,
    ) -> SpellCastResult:
        action_result = ActionResult(
            success_level=level,
            reason=reason,
            state_deltas=deltas,
            visible_facts=sorted(set(visible_facts or [])),
            hidden_facts=sorted(set(hidden_facts or [])),
        )
        event = Event(
            event_id=event_id,
            turn=state.turn,
            actor_id=state.player.id,
            action_type="cast_spell",
            result=level.value,
            visible_to_player=visible_to_player,
            target_id=intent.target_id,
            input_text=intent.raw_text,
            state_deltas=deltas,
            allow_empty_delta=not deltas,
        )
        return SpellCastResult(spell_id=spell.id, action_result=action_result, event=event)

    def _invalid_result(self, spell_id: str, intent: PlayerIntent, state: GameState, reason: str) -> SpellCastResult:
        placeholder = SpellDefinition(id=spell_id, name=spell_id)
        return self._result(
            placeholder,
            f"event-cast-spell-{spell_id}-{state.turn}",
            intent,
            state,
            SuccessLevel.INVALID,
            reason,
            [],
            visible_to_player=False,
        )

    def _safe_actor_id(self, actor_id: str) -> str:
        return actor_id


def cast_spell_action_definition(config: MagicModuleConfig | None = None) -> DeclarativeActionDefinition:
    spell_ids = sorted((config or MagicModuleConfig()).spells.keys())
    return DeclarativeActionDefinition(
        id="magic.cast_spell",
        label="Cast Spell",
        aliases=["cast spell", "cast"],
        category=DeclarativeActionCategory.MAGIC,
        target_specs=[
            DeclarativeActionTargetSpec(kind=DeclarativeTargetKind.SELF, required=False),
            DeclarativeActionTargetSpec(kind=DeclarativeTargetKind.NPC, required=False),
            DeclarativeActionTargetSpec(kind=DeclarativeTargetKind.OBJECT, required=False),
            DeclarativeActionTargetSpec(kind=DeclarativeTargetKind.LOCATION, required=False),
        ],
        outcomes={
            SuccessLevel.SUCCESS: DeclarativeOutcome(
                success_level=SuccessLevel.SUCCESS,
                reason="Spell casting is resolved by deterministic magic rules.",
            )
        },
        event_type="magic.cast_spell.resolved",
        visibility_policy=DeclarativeVisibilityPolicy(hidden_outcome_player_visible=False),
        narrator_hints={"safe_summary": f"Available spells: {', '.join(spell_ids)}"},
    )


def default_magic_registry_config() -> MagicModuleConfig:
    return MagicModuleConfig()
