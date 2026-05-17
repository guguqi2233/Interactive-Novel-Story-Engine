from enum import StrEnum
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator

from app.engine.content.authoring_service import ALLOWED_AUTHORING_FILES
from app.engine.content.validator import ValidationReport, validate_world_pack


class ScenarioTemplateError(ValueError):
    """Raised when a scenario template is invalid or unsafe."""


class ScenarioTemplateType(StrEnum):
    WORLD = "world"
    QUEST = "quest"
    LOCATION_CLUSTER = "location_cluster"
    NPC_SET = "npc_set"
    FACTION_SET = "faction_set"
    MYSTERY = "mystery"
    COMBAT_ENCOUNTER = "combat_encounter"


class ScenarioTemplateOutputFile(BaseModel):
    file_name: str
    content: str

    @model_validator(mode="after")
    def validate_file_name(self) -> "ScenarioTemplateOutputFile":
        if self.file_name not in ALLOWED_AUTHORING_FILES or Path(self.file_name).name != self.file_name:
            raise ValueError(f"Template output file is not allowed: {self.file_name}")
        return self


class ScenarioTemplate(BaseModel):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    description: str = ""
    template_type: ScenarioTemplateType
    required_variables: list[str] = Field(default_factory=list)
    optional_variables: dict[str, str] = Field(default_factory=dict)
    output_files: list[ScenarioTemplateOutputFile]
    validation_rules: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_variables(self) -> "ScenarioTemplate":
        variable_names = set(self.required_variables) | set(self.optional_variables)
        for variable_name in variable_names:
            if not _is_safe_variable_name(variable_name):
                raise ValueError(f"Unsafe template variable name: {variable_name}")
        return self


class RenderedTemplateFile(BaseModel):
    file_name: str
    content: str


class RenderedTemplate(BaseModel):
    template_id: str
    template_type: ScenarioTemplateType
    files: list[RenderedTemplateFile]


class ScenarioTemplatePreview(BaseModel):
    template: ScenarioTemplate
    rendered: RenderedTemplate
    validation_report: ValidationReport | None = None
    writes_to_disk: bool = False


class ScenarioTemplateRenderer:
    def __init__(
        self,
        templates_root: str | Path = "templates",
        worlds_root: str | Path = "worlds",
    ) -> None:
        self.templates_root = Path(templates_root)
        self.worlds_root = Path(worlds_root)

    def list_templates(self) -> list[ScenarioTemplate]:
        if not self.templates_root.exists():
            return []
        templates: list[ScenarioTemplate] = []
        for path in sorted(self.templates_root.glob("*.yaml"), key=lambda item: item.name):
            templates.append(self._load_template(path))
        return templates

    def get_template(self, template_id: str) -> ScenarioTemplate:
        if not _is_safe_id(template_id):
            raise ScenarioTemplateError(f"Invalid template id: {template_id}")
        path = (self.templates_root / f"{template_id}.yaml").resolve()
        root = self.templates_root.resolve()
        if root != path.parent:
            raise ScenarioTemplateError("Template path escapes templates root")
        if not path.exists():
            raise ScenarioTemplateError(f"Scenario template not found: {template_id}")
        return self._load_template(path)

    def preview_template(
        self,
        template_id: str,
        variables: dict[str, str],
        *,
        target_world_id: str | None = None,
    ) -> ScenarioTemplatePreview:
        template = self.get_template(template_id)
        rendered = self.render_template(template, variables)
        validation_report = self.validate_rendered_content(rendered, target_world_id=target_world_id)
        return ScenarioTemplatePreview(
            template=template,
            rendered=rendered,
            validation_report=validation_report,
            writes_to_disk=False,
        )

    def render_template(
        self,
        template: ScenarioTemplate,
        variables: dict[str, str],
    ) -> RenderedTemplate:
        resolved_variables = self._resolve_variables(template, variables)
        return RenderedTemplate(
            template_id=template.id,
            template_type=template.template_type,
            files=[
                RenderedTemplateFile(
                    file_name=output_file.file_name,
                    content=_render_text(output_file.content, resolved_variables),
                )
                for output_file in template.output_files
            ],
        )

    def validate_rendered_content(
        self,
        rendered: RenderedTemplate,
        *,
        target_world_id: str | None = None,
    ) -> ValidationReport | None:
        with TemporaryDirectory() as tmpdir:
            tmp_worlds_root = Path(tmpdir) / "worlds"
            if rendered.template_type != ScenarioTemplateType.WORLD:
                if target_world_id is None:
                    return None
                source_world = self._safe_world_path(target_world_id)
                copytree(source_world, tmp_worlds_root / target_world_id)
                validation_world_id = target_world_id
            else:
                manifest = _safe_load_mapping(_file_content(rendered, "manifest.yaml"))
                raw_world_id = manifest.get("world_id")
                if not isinstance(raw_world_id, str) or not _is_safe_id(raw_world_id):
                    raise ScenarioTemplateError("Rendered world template must include a safe manifest world_id")
                validation_world_id = raw_world_id
                (tmp_worlds_root / validation_world_id).mkdir(parents=True)

            world_path = tmp_worlds_root / validation_world_id
            for rendered_file in rendered.files:
                if rendered_file.file_name not in ALLOWED_AUTHORING_FILES or Path(rendered_file.file_name).name != rendered_file.file_name:
                    raise ScenarioTemplateError(f"Rendered file is not authoring-allowed: {rendered_file.file_name}")
                _safe_load_mapping(rendered_file.content)
                (world_path / rendered_file.file_name).write_text(rendered_file.content, encoding="utf-8")

            return validate_world_pack(validation_world_id, worlds_root=tmp_worlds_root)

    def _load_template(self, path: Path) -> ScenarioTemplate:
        root = self.templates_root.resolve()
        resolved = path.resolve()
        if root != resolved.parent:
            raise ScenarioTemplateError("Template path escapes templates root")
        try:
            data = yaml.safe_load(resolved.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ScenarioTemplateError(f"Invalid template YAML: {path.name}: {exc}") from exc
        if not isinstance(data, dict):
            raise ScenarioTemplateError(f"Expected template mapping: {path.name}")
        try:
            return ScenarioTemplate.model_validate(data)
        except ValidationError as exc:
            raise ScenarioTemplateError(f"Template schema validation failed: {path.name}: {exc}") from exc

    def _resolve_variables(self, template: ScenarioTemplate, variables: dict[str, str]) -> dict[str, str]:
        resolved = dict(template.optional_variables)
        for key, value in variables.items():
            if not _is_safe_variable_name(key):
                raise ScenarioTemplateError(f"Unsafe template variable name: {key}")
            if _looks_like_path_traversal(value):
                raise ScenarioTemplateError(f"Unsafe template variable value for {key}")
            resolved[key] = value
        missing = [key for key in template.required_variables if not resolved.get(key)]
        if missing:
            raise ScenarioTemplateError(f"Missing required template variables: {', '.join(missing)}")
        allowed = set(template.required_variables) | set(template.optional_variables)
        unexpected = sorted(set(variables) - allowed)
        if unexpected:
            raise ScenarioTemplateError(f"Unexpected template variables: {', '.join(unexpected)}")
        return resolved

    def _safe_world_path(self, world_id: str) -> Path:
        if not _is_safe_id(world_id):
            raise ScenarioTemplateError(f"Invalid target world id: {world_id}")
        root = self.worlds_root.resolve()
        path = (root / world_id).resolve()
        if root != path and root not in path.parents:
            raise ScenarioTemplateError("World path escapes worlds root")
        if not path.exists() or not path.is_dir():
            raise ScenarioTemplateError(f"World pack not found: {world_id}")
        return path


def _render_text(template: str, variables: dict[str, str]) -> str:
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    unresolved = _find_unresolved_placeholders(rendered)
    if unresolved:
        raise ScenarioTemplateError(f"Unresolved template variables: {', '.join(unresolved)}")
    return rendered


def _find_unresolved_placeholders(value: str) -> list[str]:
    unresolved: list[str] = []
    start = 0
    while True:
        open_index = value.find("{{", start)
        if open_index == -1:
            break
        close_index = value.find("}}", open_index + 2)
        if close_index == -1:
            break
        unresolved.append(value[open_index + 2 : close_index].strip())
        start = close_index + 2
    return unresolved


def _file_content(rendered: RenderedTemplate, file_name: str) -> str:
    for rendered_file in rendered.files:
        if rendered_file.file_name == file_name:
            return rendered_file.content
    raise ScenarioTemplateError(f"Rendered template missing required file: {file_name}")


def _safe_load_mapping(content: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        raise ScenarioTemplateError(f"Rendered template produced invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ScenarioTemplateError("Rendered template produced non-mapping YAML")
    return data


def _is_safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-"} for character in value)


def _is_safe_variable_name(value: str) -> bool:
    return _is_safe_id(value)


def _looks_like_path_traversal(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return "../" in normalized or normalized.startswith("/") or normalized.startswith("~")
