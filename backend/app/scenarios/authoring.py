import json
import re
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from app.engine.content.validator import ValidationIssue, ValidationReport, ValidationSeverity
from app.engine.content.world_loader import WorldLoader, WorldLoaderError
from app.scenarios.regression import ScenarioRegressionCase

_SAFE_SCENARIO_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


class ScenarioAuthoringError(ValueError):
    pass


class ScenarioAuthoringListResponse(BaseModel):
    local_only: bool = True
    scenarios: list[ScenarioRegressionCase] = Field(default_factory=list)


class ScenarioAuthoringPreviewRequest(BaseModel):
    scenario: ScenarioRegressionCase


class ScenarioAuthoringValidationResponse(BaseModel):
    world_id: str
    ok: bool
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    suggestions: list[ValidationIssue] = Field(default_factory=list)


class ScenarioAuthoringPreviewResponse(BaseModel):
    local_only: bool = True
    scenario: ScenarioRegressionCase
    validation: ScenarioAuthoringValidationResponse
    writes_to_disk: bool = False


class ScenarioAuthoringSaveResponse(ScenarioAuthoringPreviewResponse):
    writes_to_disk: bool = True


class ScenarioAuthoringService:
    def __init__(self, scenarios_root: str | Path = "scenarios", worlds_root: str | Path = "worlds") -> None:
        self.scenarios_root = Path(scenarios_root)
        self.worlds_root = Path(worlds_root)

    def list_scenarios(self) -> list[ScenarioRegressionCase]:
        if not self.scenarios_root.exists():
            return []
        scenarios: list[ScenarioRegressionCase] = []
        for path in sorted(self.scenarios_root.glob("*.json"), key=lambda item: item.name):
            try:
                scenarios.append(self._read_path(path))
            except (ScenarioAuthoringError, ValidationError, json.JSONDecodeError):
                continue
        return scenarios

    def get_scenario(self, scenario_id: str) -> ScenarioRegressionCase:
        path = self._safe_scenario_path(scenario_id)
        if not path.exists():
            raise ScenarioAuthoringError(f"Scenario not found: {scenario_id}")
        return self._read_path(path)

    def preview_scenario(self, scenario: ScenarioRegressionCase) -> ScenarioAuthoringPreviewResponse:
        return ScenarioAuthoringPreviewResponse(
            scenario=scenario,
            validation=_scenario_validation_response(self.validate_scenario(scenario)),
            writes_to_disk=False,
        )

    def validate_scenario(self, scenario: ScenarioRegressionCase) -> ValidationReport:
        report = ValidationReport(world_id=scenario.world_id)
        if not _SAFE_SCENARIO_ID.fullmatch(scenario.id):
            report.add(
                ValidationSeverity.ERROR,
                f"scenarios/{scenario.id}.json",
                "Scenario id must use only letters, numbers, dots, dashes, or underscores.",
                code="invalid_scenario_id",
                ref_id=scenario.id,
            )
            return report
        if scenario.max_turns < len(scenario.input_sequence):
            report.add(
                ValidationSeverity.WARNING,
                f"scenarios/{scenario.id}.json.max_turns",
                "Scenario max_turns is lower than input_sequence length.",
                code="scenario_max_turns_short",
                ref_id=scenario.id,
            )
        try:
            pack = WorldLoader(self.worlds_root).load(scenario.world_id)
        except WorldLoaderError as exc:
            report.add(
                ValidationSeverity.ERROR,
                f"scenarios/{scenario.id}.json.world_id",
                str(exc),
                code="scenario_world_not_found",
                ref_id=scenario.world_id,
            )
            return report
        fact_ids = {fact.id for fact in pack.facts}
        quest_ids = {quest.id for quest in pack.quests}
        for fact_id in [*scenario.expected_visible_facts, *scenario.forbidden_visible_facts]:
            if fact_id not in fact_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"scenarios/{scenario.id}.json.facts",
                    f"Scenario references unknown fact id: {fact_id}",
                    code="scenario_unknown_fact",
                    ref_id=fact_id,
                )
        for quest_id in scenario.expected_quest_states:
            if quest_id not in quest_ids:
                report.add(
                    ValidationSeverity.ERROR,
                    f"scenarios/{scenario.id}.json.expected_quest_states",
                    f"Scenario references unknown quest id: {quest_id}",
                    code="scenario_unknown_quest",
                    ref_id=quest_id,
                )
        return report

    def save_scenario(self, scenario_id: str, scenario: ScenarioRegressionCase) -> ScenarioAuthoringSaveResponse:
        if scenario_id != scenario.id:
            raise ScenarioAuthoringError("Path scenario_id must match scenario.id")
        validation = self.validate_scenario(scenario)
        if not validation.ok:
            return ScenarioAuthoringSaveResponse(
                scenario=scenario,
                validation=_scenario_validation_response(validation),
                writes_to_disk=False,
            )
        path = self._safe_scenario_path(scenario_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(scenario.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return ScenarioAuthoringSaveResponse(
            scenario=scenario,
            validation=_scenario_validation_response(validation),
            writes_to_disk=True,
        )

    def _safe_scenario_path(self, scenario_id: str) -> Path:
        if not _SAFE_SCENARIO_ID.fullmatch(scenario_id):
            raise ScenarioAuthoringError(f"Unsafe scenario id: {scenario_id}")
        root = self.scenarios_root.resolve()
        path = (root / f"{scenario_id}.json").resolve()
        if root != path.parent:
            raise ScenarioAuthoringError("Scenario path escapes scenarios root")
        return path

    def _read_path(self, path: Path) -> ScenarioRegressionCase:
        root = self.scenarios_root.resolve()
        resolved = path.resolve()
        if resolved.parent != root:
            raise ScenarioAuthoringError("Scenario path escapes scenarios root")
        return ScenarioRegressionCase.model_validate(json.loads(resolved.read_text(encoding="utf-8")))


def _scenario_validation_response(report: ValidationReport) -> ScenarioAuthoringValidationResponse:
    return ScenarioAuthoringValidationResponse(
        world_id=report.world_id,
        ok=report.ok,
        errors=report.errors,
        warnings=report.warnings,
        suggestions=report.suggestions,
    )
