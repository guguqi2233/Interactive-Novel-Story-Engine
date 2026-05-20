from pathlib import Path
from typing import Any
from base64 import b64encode
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.core.state_delta import StateDeltaOperation
from app.engine.actions.declarative import (
    DeclarativeActionDefinition,
    DeclarativeStateDeltaTemplate,
    DeclarativeTargetKind,
)
from app.engine.actions.dsl import ActionDSLValidationError, validate_action_dsl_path_template
from app.engine.content.validator import ValidationIssue, ValidationSeverity


class ActionModValidationReport(BaseModel):
    module_id: str = "standalone"
    ok: bool = True
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)

    def add(
        self,
        severity: ValidationSeverity,
        path: str,
        message: str,
        *,
        code: str,
        ref_id: str | None = None,
        file: str = "action_mods",
        suggestion: str | None = None,
    ) -> None:
        issue = ValidationIssue(
            severity=severity,
            file=file,
            path=path,
            code=code,
            message=message,
            ref_id=ref_id,
            suggestion=suggestion,
        )
        if severity == ValidationSeverity.ERROR:
            self.errors.append(issue)
        else:
            self.warnings.append(issue)
        self.ok = not self.errors


class ActionModDraft(BaseModel):
    module_id: str = "local_action_mod"
    name: str = "Local Action Mod"
    version: str = "0.1.0"
    actions: list[DeclarativeActionDefinition] = Field(default_factory=list)


class ActionModPreviewResponse(BaseModel):
    local_only: bool = True
    draft: ActionModDraft
    validation: ActionModValidationReport
    writes_to_disk: bool = False
    executes_code: bool = False
    active_game_state_modified: bool = False
    normalized_yaml: str


class ActionModExportResponse(BaseModel):
    local_only: bool = True
    exported: bool
    file_name: str
    archive_base64: str
    validation: ActionModValidationReport
    contains_api_key: bool = False
    writes_to_disk: bool = False
    executes_code: bool = False


def validate_action_mods(
    action_definitions: list[DeclarativeActionDefinition],
    *,
    module_id: str = "standalone",
    manifest: Any | None = None,
) -> ActionModValidationReport:
    report = ActionModValidationReport(module_id=module_id)
    _validate_manifest_permissions(manifest, report)
    _validate_save_compatibility(manifest.save_compatibility if manifest else None, report)
    _validate_unique_action_ids(action_definitions, report)
    _validate_alias_conflicts(action_definitions, report)
    for index, definition in enumerate(action_definitions):
        _validate_action_definition(definition, report, index=index)
    report.ok = not report.errors
    return report


def preview_action_mod_draft(draft: ActionModDraft) -> ActionModPreviewResponse:
    validation = validate_action_mods(draft.actions, module_id=draft.module_id)
    return ActionModPreviewResponse(
        draft=draft,
        validation=validation,
        normalized_yaml=_action_mod_yaml(draft),
    )


def export_action_mod_draft(draft: ActionModDraft) -> ActionModExportResponse:
    preview = preview_action_mod_draft(draft)
    if not preview.validation.ok:
        return ActionModExportResponse(
            exported=False,
            file_name="",
            archive_base64="",
            validation=preview.validation,
        )
    manifest_yaml = _manifest_yaml(draft)
    action_yaml = preview.normalized_yaml
    if _contains_secret_like_text(manifest_yaml) or _contains_secret_like_text(action_yaml):
        preview.validation.add(
            ValidationSeverity.ERROR,
            "export",
            "Action mod export contains secret-like text and was blocked.",
            code="action_mod_export_secret_forbidden",
        )
        return ActionModExportResponse(
            exported=False,
            file_name="",
            archive_base64="",
            validation=preview.validation,
            contains_api_key=True,
        )
    archive = BytesIO()
    with ZipFile(archive, mode="w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr("gameplay_module.yaml", manifest_yaml)
        zip_file.writestr("action_mods/actions.yaml", action_yaml)
    file_name = f"{draft.module_id}-{draft.version}.zip"
    return ActionModExportResponse(
        exported=True,
        file_name=file_name,
        archive_base64=b64encode(archive.getvalue()).decode("ascii"),
        validation=preview.validation,
    )


def validate_action_mod_files(
    module_path: Path,
    manifest: Any,
) -> ActionModValidationReport:
    report = ActionModValidationReport(module_id=manifest.id)
    action_files = _action_mod_files(module_path)
    if not action_files:
        return validate_action_mods([], module_id=manifest.id, manifest=manifest)

    definitions: list[DeclarativeActionDefinition] = []
    for action_file in action_files:
        try:
            for raw_definition in _read_action_definitions(action_file):
                definitions.append(DeclarativeActionDefinition.model_validate(raw_definition))
        except (ActionModValidationError, ValidationError, ValueError) as exc:
            report.add(
                ValidationSeverity.ERROR,
                str(action_file.relative_to(module_path)),
                f"Action mod schema validation failed: {exc}",
                code="action_mod_schema_invalid",
                file=str(action_file.relative_to(module_path)),
            )
    parsed_report = validate_action_mods(definitions, module_id=manifest.id, manifest=manifest)
    report.errors.extend(parsed_report.errors)
    report.warnings.extend(parsed_report.warnings)
    report.ok = not report.errors
    return report


def _validate_manifest_permissions(
    manifest: Any | None,
    report: ActionModValidationReport,
) -> None:
    if manifest is None:
        return
    if manifest.permissions.execute_code:
        report.add(
            ValidationSeverity.ERROR,
            "gameplay_module.yaml.permissions.execute_code",
            "Action mods are declarative and cannot request execute_code permission.",
            code="action_mod_execute_code_forbidden",
            ref_id=manifest.id,
            file="gameplay_module.yaml",
        )


def _validate_save_compatibility(
    compatibility: Any | None,
    report: ActionModValidationReport,
) -> None:
    if compatibility is None:
        return
    if compatibility.requires_new_game and compatibility.safe_to_add_mid_save:
        report.add(
            ValidationSeverity.ERROR,
            "gameplay_module.yaml.save_compatibility",
            "Action mod save compatibility cannot require a new game and be safe mid-save at the same time.",
            code="action_mod_invalid_save_compatibility",
            file="gameplay_module.yaml",
        )
    if compatibility.migration_required and not compatibility.migration_defaults:
        report.add(
            ValidationSeverity.ERROR,
            "gameplay_module.yaml.save_compatibility.migration_defaults",
            "Action mod migration_required requires migration_defaults.",
            code="action_mod_missing_migration_defaults",
            file="gameplay_module.yaml",
        )


def _validate_unique_action_ids(
    definitions: list[DeclarativeActionDefinition],
    report: ActionModValidationReport,
) -> None:
    seen: dict[str, int] = {}
    for index, definition in enumerate(definitions):
        if definition.id in seen:
            report.add(
                ValidationSeverity.ERROR,
                f"actions[{index}].id",
                f"Duplicate action id: {definition.id}",
                code="action_mod_duplicate_action_id",
                ref_id=definition.id,
            )
        seen[definition.id] = index


def _validate_alias_conflicts(
    definitions: list[DeclarativeActionDefinition],
    report: ActionModValidationReport,
) -> None:
    alias_owners: dict[str, str] = {}
    for definition in definitions:
        for alias in [definition.id, *definition.aliases]:
            normalized = alias.strip().lower()
            if not normalized:
                report.add(
                    ValidationSeverity.ERROR,
                    f"actions.{definition.id}.aliases",
                    "Action aliases cannot be blank.",
                    code="action_mod_blank_alias",
                    ref_id=definition.id,
                )
                continue
            owner = alias_owners.get(normalized)
            if owner and owner != definition.id:
                report.add(
                    ValidationSeverity.WARNING,
                    f"actions.{definition.id}.aliases",
                    f"Action alias conflicts with {owner}: {alias}",
                    code="action_mod_alias_conflict",
                    ref_id=alias,
                    suggestion="Rename one alias so the intent parser resolves deterministically.",
                )
            alias_owners[normalized] = definition.id


def _validate_action_definition(
    definition: DeclarativeActionDefinition,
    report: ActionModValidationReport,
    *,
    index: int,
) -> None:
    path = f"actions[{index}]"
    _validate_safe_dotted_identifier(definition.id, report, f"{path}.id", "action_mod_invalid_action_id")
    _validate_safe_dotted_identifier(definition.event_type, report, f"{path}.event_type", "action_mod_invalid_event_type")
    if not definition.outcomes:
        report.add(
            ValidationSeverity.ERROR,
            f"{path}.outcomes",
            "Action mod must define at least one outcome.",
            code="action_mod_missing_outcomes",
            ref_id=definition.id,
        )
    for target_index, target_spec in enumerate(definition.target_specs):
        _validate_target_spec(definition.id, target_spec, report, f"{path}.target_specs[{target_index}]")
    for template_index, template in enumerate(definition.state_delta_templates):
        _validate_delta_template(definition.id, template, report, f"{path}.state_delta_templates[{template_index}]")
    for outcome_key, outcome in definition.outcomes.items():
        outcome_path = f"{path}.outcomes.{outcome_key.value}"
        if outcome.hidden_outcome and definition.visibility_policy.hidden_outcome_player_visible:
            report.add(
                ValidationSeverity.ERROR,
                outcome_path,
                "Hidden outcomes cannot be marked player-visible by visibility_policy.",
                code="action_mod_hidden_outcome_visible_policy",
                ref_id=definition.id,
            )
        overlap = set(outcome.hidden_facts) & set(outcome.visible_facts)
        if overlap:
            report.add(
                ValidationSeverity.ERROR,
                outcome_path,
                f"Hidden output also appears in visible_facts: {', '.join(sorted(overlap))}",
                code="action_mod_hidden_output_visible",
                ref_id=definition.id,
            )
        for template_index, template in enumerate(outcome.state_delta_templates):
            _validate_delta_template(
                definition.id,
                template,
                report,
                f"{outcome_path}.state_delta_templates[{template_index}]",
            )


def _validate_target_spec(
    action_id: str,
    target_spec: Any,
    report: ActionModValidationReport,
    path: str,
) -> None:
    if target_spec.kind in {DeclarativeTargetKind.SELF, DeclarativeTargetKind.CURRENT_LOCATION} and target_spec.allowed_ids:
        report.add(
            ValidationSeverity.ERROR,
            f"{path}.allowed_ids",
            "self/current_location target specs cannot constrain arbitrary allowed_ids.",
            code="action_mod_invalid_target_spec",
            ref_id=action_id,
        )
    for allowed_id in target_spec.allowed_ids:
        if not _is_safe_dotted_identifier(allowed_id):
            report.add(
                ValidationSeverity.ERROR,
                f"{path}.allowed_ids",
                f"Target allowed_id is not a safe identifier: {allowed_id}",
                code="action_mod_invalid_target_id",
                ref_id=action_id,
            )


def _validate_delta_template(
    action_id: str,
    template: DeclarativeStateDeltaTemplate,
    report: ActionModValidationReport,
    path: str,
) -> None:
    try:
        validate_action_dsl_path_template(template.path)
    except ActionDSLValidationError as exc:
        report.add(
            ValidationSeverity.ERROR,
            f"{path}.path",
            f"StateDelta path is outside the Action DSL whitelist: {exc}",
            code="action_mod_forbidden_state_delta_path",
            ref_id=action_id,
        )
    if template.operation not in set(StateDeltaOperation):
        report.add(
            ValidationSeverity.ERROR,
            f"{path}.operation",
            f"Unsupported StateDelta operation: {template.operation}",
            code="action_mod_invalid_delta_operation",
            ref_id=action_id,
        )


def _validate_safe_dotted_identifier(
    value: str,
    report: ActionModValidationReport,
    path: str,
    code: str,
) -> None:
    if not _is_safe_dotted_identifier(value):
        report.add(
            ValidationSeverity.ERROR,
            path,
            f"Identifier must be dotted alphanumeric/underscore/dash only: {value}",
            code=code,
            ref_id=value,
        )


def _action_mod_files(module_path: Path) -> list[Path]:
    root = module_path.resolve()
    action_root = (root / "action_mods").resolve()
    if not action_root.exists():
        return []
    if root != action_root and root not in action_root.parents:
        raise ActionModValidationError("Action mod path escapes module root")
    return sorted(
        [
            path
            for path in action_root.rglob("*")
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml", ".json"}
        ],
        key=lambda item: str(item),
    )


def _read_action_definitions(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if isinstance(data, list):
        return [_ensure_mapping(item, path) for item in data]
    if not isinstance(data, dict):
        raise ActionModValidationError(f"Expected mapping or list in {path.name}")
    if "actions" in data:
        actions = data["actions"]
        if not isinstance(actions, list):
            raise ActionModValidationError(f"Expected actions list in {path.name}")
        return [_ensure_mapping(item, path) for item in actions]
    return [data]


def _ensure_mapping(value: Any, path: Path) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ActionModValidationError(f"Expected action mapping in {path.name}")
    return value


def _is_safe_dotted_identifier(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-", "."} for character in value)


def _action_mod_yaml(draft: ActionModDraft) -> str:
    return yaml.safe_dump(
        {"actions": [action.model_dump(mode="json", exclude_none=True) for action in draft.actions]},
        sort_keys=False,
        allow_unicode=True,
    )


def _manifest_yaml(draft: ActionModDraft) -> str:
    return yaml.safe_dump(
        {
            "id": draft.module_id,
            "name": draft.name,
            "version": draft.version,
            "module_type": "action_pack",
            "engine_version_min": "0.1.0",
            "schema_version": "0.6",
            "provided_actions": [
                {"id": action.id, "action_type": action.id}
                for action in draft.actions
            ],
            "permissions": {
                "execute_code": False,
                "access_network": False,
                "access_filesystem": False,
                "call_llm": False,
                "modify_game_state_directly": False,
            },
            "save_compatibility": {
                "safe_to_add_mid_save": True,
                "migration_required": False,
                "requires_new_game": False,
                "migration_defaults": {},
            },
            "quality_tests": ["action_mod_validation"],
        },
        sort_keys=False,
        allow_unicode=True,
    )


def _contains_secret_like_text(text: str) -> bool:
    lowered = text.lower()
    secret_markers = ("sk-", "api_key", "api key", "authorization:", "bearer ")
    return any(marker in lowered for marker in secret_markers)
