from __future__ import annotations

import json
import re
from pathlib import Path
from random import Random
from typing import Any

import yaml
from pydantic import BaseModel, Field

from app.core.event_log import EventLog
from app.core.state_delta import StateDelta
from app.core.world_state import GameState
from app.engine.action_mod_schema import ActionMod, ModActionDefinition
from app.engine.actions.declarative import DeclarativeActionHandler
from app.engine.actions.schemas import SuccessLevel
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.platform.security import contains_secret_text, redact_text, validate_relative_package_path


class ActionModTestCase(BaseModel):
    test_id: str
    action_id: str
    input_intent: dict[str, Any] = Field(default_factory=dict)
    initial_state_fixture: dict[str, Any]
    expected_result_type: SuccessLevel
    expected_state_deltas: list[dict[str, Any]] = Field(default_factory=list)
    forbidden_visible_text_patterns: list[str] = Field(default_factory=list)
    expected_event_tags: list[str] = Field(default_factory=list)


class ActionModTestResult(BaseModel):
    test_id: str
    action_id: str
    passed: bool
    errors: list[str] = Field(default_factory=list)
    result_type: str | None = None
    state_unchanged: bool = True


class ActionModTestReport(BaseModel):
    ok: bool
    package_id: str
    results: list[ActionModTestResult] = Field(default_factory=list)
    safe_summary: dict[str, Any] = Field(default_factory=dict)


class ActionModTestHarness:
    def __init__(self, action_mod: ActionMod) -> None:
        self.action_mod = action_mod

    @staticmethod
    def load_test_cases(path: Path) -> list[ActionModTestCase]:
        validate_relative_package_path(path.name)
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) if path.suffix.lower() in {".yaml", ".yml"} else json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            loaded = loaded.get("tests", [])
        if not isinstance(loaded, list):
            raise ValueError("action mod test file must contain a list of tests")
        return [ActionModTestCase.model_validate(item) for item in loaded]

    def run_test_case(self, test_case: ActionModTestCase) -> ActionModTestResult:
        errors: list[str] = []
        definition = self._definition(test_case.action_id)
        if definition is None:
            return ActionModTestResult(test_id=test_case.test_id, action_id=test_case.action_id, passed=False, errors=["action_id not found"])
        state = GameState.model_validate(test_case.initial_state_fixture)
        before = state.model_dump_json()
        raw_text = test_case.input_intent.get("raw_text") or (definition.aliases[0] if definition.aliases else definition.id)
        intent = PlayerIntent(
            action_type=PlayerActionType.UNKNOWN,
            raw_text=str(raw_text),
            target_id=test_case.input_intent.get("target_id"),
            confidence=float(test_case.input_intent.get("confidence", 1.0)),
            requires_clarification=bool(test_case.input_intent.get("requires_clarification", False)),
        )
        execution = DeclarativeActionHandler(definition).resolve_with_event(intent, state, Random(123))
        event_log = EventLog()
        event_log.append(execution.event)
        after = state.model_dump_json()
        if after != before:
            errors.append("action mod test mutated GameState directly")
        if execution.action_result.success_level != test_case.expected_result_type:
            errors.append(f"expected result {test_case.expected_result_type.value}, got {execution.action_result.success_level.value}")
        if not _expected_deltas_match(execution.action_result.state_deltas, test_case.expected_state_deltas):
            errors.append("expected StateDelta proposal mismatch")
        visible_text = json.dumps(
            {
                "reason": execution.action_result.reason,
                "visible_facts": execution.action_result.visible_facts,
                "event": execution.event.model_dump(mode="json", exclude={"state_deltas"}),
            },
            ensure_ascii=False,
            default=str,
        )
        for pattern in test_case.forbidden_visible_text_patterns:
            if re.search(pattern, visible_text, re.IGNORECASE):
                errors.append(f"forbidden visible text pattern matched: {pattern}")
        event_text = execution.event.model_dump_json()
        for tag in test_case.expected_event_tags:
            if tag not in event_text:
                errors.append(f"expected event tag missing: {tag}")
        if contains_secret_text(visible_text):
            errors.append("visible output contains secret-like text")
        return ActionModTestResult(
            test_id=test_case.test_id,
            action_id=test_case.action_id,
            passed=not errors,
            errors=[redact_text(error) for error in errors],
            result_type=execution.action_result.success_level.value,
            state_unchanged=after == before,
        )

    def run_all_for_mod(self, tests: list[ActionModTestCase]) -> ActionModTestReport:
        results = [self.run_test_case(test_case) for test_case in tests]
        return self.produce_report(results)

    def produce_report(self, results: list[ActionModTestResult]) -> ActionModTestReport:
        return ActionModTestReport(
            ok=all(result.passed for result in results),
            package_id=self.action_mod.manifest.package_id,
            results=results,
            safe_summary={"test_count": len(results), "passed": sum(1 for result in results if result.passed)},
        )

    def _definition(self, action_id: str) -> ModActionDefinition | None:
        return next((action for action in self.action_mod.actions if action.id == action_id), None)


def _expected_deltas_match(actual: list[StateDelta], expected: list[dict[str, Any]]) -> bool:
    if len(actual) != len(expected):
        return False
    for actual_delta, expected_delta in zip(actual, expected, strict=False):
        for key, value in expected_delta.items():
            if getattr(actual_delta, key) != value:
                return False
    return True
