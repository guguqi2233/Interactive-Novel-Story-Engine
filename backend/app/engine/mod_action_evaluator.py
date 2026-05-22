from __future__ import annotations

from random import Random

from pydantic import BaseModel, Field

from app.core.world_state import GameState
from app.engine.action_mod_schema import ModActionDefinition
from app.engine.actions.declarative import DeclarativeActionExecution, DeclarativeActionHandler
from app.llm.schemas import PlayerIntent


SUPPORTED_PRECONDITIONS = [
    "actor_at_location",
    "target_exists",
    "target_visible",
    "target_has_tag",
    "actor_has_item",
    "actor_not_in_combat",
    "actor_has_skill",
    "location_has_tag",
    "fact_known_by_actor",
]

SUPPORTED_CHECKS = [
    "static_success",
    "skill_check",
    "reputation_check",
    "item_check",
    "visibility_check",
]

SUPPORTED_OUTCOME_EFFECTS = ["set", "inc", "add", "remove"]


class ModActionEvaluationReport(BaseModel):
    ok: bool
    action_id: str
    supported_preconditions: list[str] = Field(default_factory=lambda: list(SUPPORTED_PRECONDITIONS))
    supported_checks: list[str] = Field(default_factory=lambda: list(SUPPORTED_CHECKS))
    supported_outcome_effects: list[str] = Field(default_factory=lambda: list(SUPPORTED_OUTCOME_EFFECTS))


class ModActionEvaluator:
    """Safe wrapper for declarative mod actions.

    This evaluator intentionally delegates to the existing declarative handler.
    It does not use eval/exec, filesystem, network, database, or LLM calls.
    """

    def validate_definition(self, definition: ModActionDefinition) -> ModActionEvaluationReport:
        for outcome in definition.outcomes.values():
            for template in outcome.state_delta_templates:
                if template.operation.value not in SUPPORTED_OUTCOME_EFFECTS:
                    return ModActionEvaluationReport(ok=False, action_id=definition.id)
        return ModActionEvaluationReport(ok=True, action_id=definition.id)

    def evaluate(
        self,
        definition: ModActionDefinition,
        intent: PlayerIntent,
        state: GameState,
        rng: Random | None = None,
    ) -> DeclarativeActionExecution:
        report = self.validate_definition(definition)
        if not report.ok:
            raise ValueError("mod action definition uses unsupported outcome effects")
        return DeclarativeActionHandler(definition).resolve_with_event(intent, state, rng or Random(0))
