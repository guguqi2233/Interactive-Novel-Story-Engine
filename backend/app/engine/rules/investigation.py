from enum import StrEnum
from random import Random

from pydantic import BaseModel, Field

from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    EvidenceState,
    FactVisibility,
    GameState,
    HypothesisState,
    HypothesisStatus,
    SocialConsequenceState,
    TestimonyState,
)
from app.engine.actions.base import ActionHandler
from app.engine.actions.declarative import (
    DeclarativeActionCategory,
    DeclarativeActionDefinition,
    DeclarativeOutcome,
    DeclarativeVisibilityPolicy,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.llm.schemas import PlayerActionType, PlayerIntent


class InvestigationActionType(StrEnum):
    EXAMINE_EVIDENCE = "examine_evidence"
    COMPARE_TESTIMONY = "compare_testimony"
    FORM_HYPOTHESIS = "form_hypothesis"
    ACCUSE_SUSPECT = "accuse_suspect"
    RECONSTRUCT_TIMELINE = "reconstruct_timeline"


class DeductionAttemptResult(BaseModel):
    action_type: InvestigationActionType
    target_id: str | None
    action_result: ActionResult
    event: Event


class InvestigationActionRule(BaseModel):
    action_type: InvestigationActionType
    label: str
    aliases: list[str] = Field(default_factory=list)


class InvestigationModuleConfig(BaseModel):
    module_id: str = "investigation"
    actions: dict[InvestigationActionType, InvestigationActionRule] = Field(default_factory=dict)


def default_investigation_module_config() -> InvestigationModuleConfig:
    return InvestigationModuleConfig(
        actions={
            InvestigationActionType.EXAMINE_EVIDENCE: InvestigationActionRule(
                action_type=InvestigationActionType.EXAMINE_EVIDENCE,
                label="Examine Evidence",
                aliases=["examine evidence", "inspect evidence"],
            ),
            InvestigationActionType.COMPARE_TESTIMONY: InvestigationActionRule(
                action_type=InvestigationActionType.COMPARE_TESTIMONY,
                label="Compare Testimony",
                aliases=["compare testimony"],
            ),
            InvestigationActionType.FORM_HYPOTHESIS: InvestigationActionRule(
                action_type=InvestigationActionType.FORM_HYPOTHESIS,
                label="Form Hypothesis",
                aliases=["form hypothesis"],
            ),
            InvestigationActionType.ACCUSE_SUSPECT: InvestigationActionRule(
                action_type=InvestigationActionType.ACCUSE_SUSPECT,
                label="Accuse Suspect",
                aliases=["accuse suspect", "accuse"],
            ),
            InvestigationActionType.RECONSTRUCT_TIMELINE: InvestigationActionRule(
                action_type=InvestigationActionType.RECONSTRUCT_TIMELINE,
                label="Reconstruct Timeline",
                aliases=["reconstruct timeline"],
            ),
        }
    )


class InvestigationActionHandler(ActionHandler):
    action_type = PlayerActionType.UNKNOWN

    def __init__(self, config: InvestigationModuleConfig | None = None) -> None:
        self.config = config or default_investigation_module_config()

    def can_handle(self, intent: PlayerIntent, state: GameState) -> bool:
        return self._rule_for_intent(intent) is not None

    def resolve(self, intent: PlayerIntent, state: GameState, rng: Random) -> ActionResult:
        return self.resolve_with_event(intent, state, rng).action_result

    def resolve_with_event(self, intent: PlayerIntent, state: GameState, rng: Random | None = None) -> DeductionAttemptResult:
        rule = self._rule_for_intent(intent)
        if rule is None:
            return self._invalid(intent, state, "Unknown investigation action.")
        event_id = f"event-{rule.action_type.value}-{intent.target_id or 'none'}-{state.turn}"
        if rule.action_type == InvestigationActionType.EXAMINE_EVIDENCE:
            return self._examine_evidence(rule, event_id, intent, state)
        if rule.action_type == InvestigationActionType.COMPARE_TESTIMONY:
            return self._compare_testimony(rule, event_id, intent, state)
        if rule.action_type == InvestigationActionType.FORM_HYPOTHESIS:
            return self._form_hypothesis(rule, event_id, intent, state)
        if rule.action_type == InvestigationActionType.ACCUSE_SUSPECT:
            return self._accuse_suspect(rule, event_id, intent, state)
        if rule.action_type == InvestigationActionType.RECONSTRUCT_TIMELINE:
            return self._reconstruct_timeline(rule, event_id, intent, state)
        return self._invalid(intent, state, "Unsupported investigation action.")

    def _rule_for_intent(self, intent: PlayerIntent) -> InvestigationActionRule | None:
        normalized = _normalized(intent.raw_text)
        for rule in self.config.actions.values():
            aliases = {rule.action_type.value, rule.action_type.value.replace("_", " "), rule.label.lower(), *[_normalized(alias) for alias in rule.aliases]}
            if normalized in aliases or any(normalized.startswith(alias) for alias in aliases):
                return rule
        return None

    def _examine_evidence(
        self,
        rule: InvestigationActionRule,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
    ) -> DeductionAttemptResult:
        evidence = state.evidence.get(intent.target_id or "")
        if evidence is None or not _evidence_visible(evidence, state):
            return self._result(rule, event_id, intent, state, SuccessLevel.INVALID, "Evidence is not visible or does not exist.", [], visible_to_player=False)
        deltas = [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"evidence.{evidence.id}.discovered",
                value=True,
                caused_by_event_id=event_id,
                reason="Player examined evidence.",
            ),
        ]
        visible_facts: list[str] = []
        hidden_facts: list[str] = []
        if evidence.fact_id and _fact_can_be_revealed(evidence.fact_id, state):
            deltas.append(
                StateDelta(
                    operation=StateDeltaOperation.ADD,
                    path="player_visible_facts",
                    value=evidence.fact_id,
                    caused_by_event_id=event_id,
                    reason="Evidence revealed a player-visible fact.",
                )
            )
            visible_facts.append(evidence.fact_id)
        elif evidence.fact_id:
            hidden_facts.append(evidence.fact_id)
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS, "Evidence examined by local rules.", deltas, visible_to_player=True, visible_facts=visible_facts, hidden_facts=hidden_facts)

    def _compare_testimony(
        self,
        rule: InvestigationActionRule,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
    ) -> DeductionAttemptResult:
        testimony = state.testimonies.get(intent.target_id or "")
        if testimony is None or testimony.hidden or not testimony.known_to_player:
            return self._result(rule, event_id, intent, state, SuccessLevel.INVALID, "Testimony is unknown.", [], visible_to_player=False)
        known_contradictions = [
            contradiction_id
            for contradiction_id in testimony.contradiction_ids
            if contradiction_id in state.player_visible_facts or state.evidence.get(contradiction_id, EvidenceState(id=contradiction_id)).discovered
        ]
        deltas = [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"flags.contradiction_{testimony.id}",
                value=True,
                caused_by_event_id=event_id,
                reason="Testimony comparison found a contradiction.",
            )
        ] if known_contradictions else []
        level = SuccessLevel.SUCCESS if known_contradictions else SuccessLevel.FAILURE
        reason = "Contradiction found." if known_contradictions else "No known contradiction can be established."
        return self._result(rule, event_id, intent, state, level, reason, deltas, visible_to_player=True, visible_facts=known_contradictions)

    def _form_hypothesis(
        self,
        rule: InvestigationActionRule,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
    ) -> DeductionAttemptResult:
        hypothesis = state.hypotheses.get(intent.target_id or "")
        if hypothesis is None:
            return self._result(rule, event_id, intent, state, SuccessLevel.INVALID, "Hypothesis does not exist.", [], visible_to_player=False)
        valid = _hypothesis_evidence_known(hypothesis, state)
        new_status = HypothesisStatus.VALID if valid else HypothesisStatus.WEAK
        deltas = [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"hypotheses.{hypothesis.id}.status",
                value=new_status.value,
                caused_by_event_id=event_id,
                reason="Hypothesis was evaluated from known evidence.",
            ),
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"hypotheses.{hypothesis.id}.known_to_player",
                value=True,
                caused_by_event_id=event_id,
                reason="Hypothesis became player-known.",
            ),
        ]
        level = SuccessLevel.SUCCESS if valid else SuccessLevel.FAILURE
        reason = "Hypothesis is supported by known evidence." if valid else "Hypothesis is weak because required evidence is missing."
        return self._result(rule, event_id, intent, state, level, reason, deltas, visible_to_player=True)

    def _accuse_suspect(
        self,
        rule: InvestigationActionRule,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
    ) -> DeductionAttemptResult:
        hypothesis = state.hypotheses.get(intent.target_id or "")
        if hypothesis is None:
            return self._result(rule, event_id, intent, state, SuccessLevel.INVALID, "Accusation requires a hypothesis.", [], visible_to_player=False)
        if not _hypothesis_evidence_known(hypothesis, state):
            return self._result(rule, event_id, intent, state, SuccessLevel.FAILURE, "Accusation is unsupported by known evidence.", [], visible_to_player=True)
        correct = bool(hypothesis.suspect_id and hypothesis.suspect_id == hypothesis.correct_suspect_id)
        if correct:
            deltas = [
                StateDelta(
                    operation=StateDeltaOperation.SET,
                    path=f"hypotheses.{hypothesis.id}.status",
                    value=HypothesisStatus.CORRECT.value,
                    caused_by_event_id=event_id,
                    reason="Correct accusation resolved by rules.",
                )
            ]
            if hypothesis.quest_id and hypothesis.quest_id in state.quests and hypothesis.quest_objective_id:
                deltas.append(
                    StateDelta(
                        operation=StateDeltaOperation.ADD,
                        path=f"quests.{hypothesis.quest_id}.completed_objectives",
                        value=hypothesis.quest_objective_id,
                        caused_by_event_id=event_id,
                        reason="Correct accusation advanced quest objective.",
                    )
                )
            return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS, "Correct accusation.", deltas, visible_to_player=True)
        consequence_id = f"wrong_accusation_{hypothesis.id}_{state.turn}"
        consequence = SocialConsequenceState(
            id=consequence_id,
            consequence_type="wrong_accusation",
            source_event_id=event_id,
            tags=["investigation", "reputation"],
            known_to_player=True,
        )
        deltas = [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"hypotheses.{hypothesis.id}.status",
                value=HypothesisStatus.WRONG.value,
                caused_by_event_id=event_id,
                reason="Wrong accusation resolved by rules.",
            ),
            StateDelta(
                operation=StateDeltaOperation.SET,
                path=f"social_consequences.{consequence_id}",
                value=consequence.model_dump(mode="json"),
                caused_by_event_id=event_id,
                reason="Wrong accusation created a social consequence.",
            ),
        ]
        return self._result(rule, event_id, intent, state, SuccessLevel.FAILURE, "Wrong accusation created a social consequence.", deltas, visible_to_player=True)

    def _reconstruct_timeline(
        self,
        rule: InvestigationActionRule,
        event_id: str,
        intent: PlayerIntent,
        state: GameState,
    ) -> DeductionAttemptResult:
        known_evidence = sorted(evidence.id for evidence in state.evidence.values() if evidence.discovered)
        deltas = [
            StateDelta(
                operation=StateDeltaOperation.SET,
                path="flags.investigation_timeline_reconstructed",
                value=bool(known_evidence),
                caused_by_event_id=event_id,
                reason="Timeline reconstruction used known evidence only.",
            )
        ]
        return self._result(rule, event_id, intent, state, SuccessLevel.SUCCESS, "Timeline reconstructed from known evidence.", deltas, visible_to_player=True, visible_facts=known_evidence)

    def _result(
        self,
        rule: InvestigationActionRule,
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
    ) -> DeductionAttemptResult:
        result = ActionResult(
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
            action_type=rule.action_type.value,
            result=level.value,
            visible_to_player=visible_to_player,
            target_id=intent.target_id,
            input_text=intent.raw_text,
            state_deltas=deltas,
            allow_empty_delta=not deltas,
        )
        return DeductionAttemptResult(action_type=rule.action_type, target_id=intent.target_id, action_result=result, event=event)

    def _invalid(self, intent: PlayerIntent, state: GameState, reason: str) -> DeductionAttemptResult:
        rule = InvestigationActionRule(action_type=InvestigationActionType.EXAMINE_EVIDENCE, label="Investigation")
        return self._result(rule, f"event-investigation-invalid-{state.turn}", intent, state, SuccessLevel.INVALID, reason, [], visible_to_player=False)


def investigation_action_definitions(config: InvestigationModuleConfig | None = None) -> list[DeclarativeActionDefinition]:
    active = config or default_investigation_module_config()
    return [
        DeclarativeActionDefinition(
            id=f"investigation.{rule.action_type.value}",
            label=rule.label,
            aliases=rule.aliases,
            category=DeclarativeActionCategory.INVESTIGATION,
            outcomes={SuccessLevel.SUCCESS: DeclarativeOutcome(success_level=SuccessLevel.SUCCESS, reason=f"{rule.label} is resolved by deterministic investigation rules.")},
            event_type=f"investigation.{rule.action_type.value}.resolved",
            visibility_policy=DeclarativeVisibilityPolicy(hidden_outcome_player_visible=False),
        )
        for rule in active.actions.values()
    ]


def _evidence_visible(evidence: EvidenceState, state: GameState) -> bool:
    if evidence.hidden and state.player.id not in evidence.discovered_by:
        return False
    if evidence.location_id and evidence.location_id != state.player.location_id:
        return False
    return evidence.visible


def _fact_can_be_revealed(fact_id: str, state: GameState) -> bool:
    fact = state.facts.get(fact_id)
    if fact is None:
        return False
    return fact.public or fact.visibility in {FactVisibility.PUBLIC, FactVisibility.DISCOVERABLE}


def _hypothesis_evidence_known(hypothesis: HypothesisState, state: GameState) -> bool:
    for evidence_id in hypothesis.required_evidence_ids:
        evidence = state.evidence.get(evidence_id)
        if evidence is None or not evidence.discovered:
            return False
    for fact_id in hypothesis.supporting_fact_ids:
        if fact_id not in state.player_visible_facts:
            return False
    return True


def _normalized(value: str) -> str:
    return value.strip().lower().replace("_", " ")

