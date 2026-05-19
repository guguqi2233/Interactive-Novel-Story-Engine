from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.engine.content.content_batch_validator import (
    BatchPackageType,
    ContentBatchValidationRequest,
    ContentBatchValidationTarget,
    validate_content_batch,
)
from app.engine.content.import_export_profiles import get_import_export_profile_catalog
from app.engine.content.local_content_library import LocalContentLibraryService, LocalContentType
from app.quality.content_coverage_planner import ContentCoveragePlan, ContentCoveragePlanRequest, build_content_coverage_plan


class ProductionPipelineStatus(BaseModel):
    status: str = "unknown"
    count: int = 0
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    summary: str = ""


class ProductionPipelineTask(BaseModel):
    tool_id: str
    label: str
    status: str
    summary: str
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


class ProductionPipelineSummary(BaseModel):
    local_only: bool = True
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    active_world: str | None = None
    active_production_drafts: list[ProductionPipelineTask] = Field(default_factory=list)
    recent_generated_packages: list[ProductionPipelineTask] = Field(default_factory=list)
    batch_validation_status: ProductionPipelineStatus = Field(default_factory=ProductionPipelineStatus)
    content_coverage_plan: ContentCoveragePlan | None = None
    quality_gate_summary: ProductionPipelineStatus = Field(default_factory=ProductionPipelineStatus)
    import_export_profile_status: ProductionPipelineStatus = Field(default_factory=ProductionPipelineStatus)
    script_package_build_status: ProductionPipelineStatus = Field(default_factory=ProductionPipelineStatus)
    campaign_starter_status: ProductionPipelineStatus = Field(default_factory=ProductionPipelineStatus)
    quick_entries: list[ProductionPipelineTask] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    hidden_details_redacted: bool = True
    sensitive_details_redacted: bool = True


def build_production_pipeline_summary(
    *,
    worlds_root: str | Path,
    library_service: LocalContentLibraryService,
    quality_gate_results: list[Any],
    active_world: str | None = None,
) -> ProductionPipelineSummary:
    worlds_root_path = Path(worlds_root)
    library = library_service.list_items()
    world_id = active_world or _first_world_id(library.items)
    batch_status = _batch_validation_status(worlds_root_path, library)
    coverage_plan = _coverage_plan(world_id, worlds_root_path)
    packages = _recent_packages(library.items)
    script_status = _package_type_status(packages, "script_package", "Script packages")
    campaign_status = _package_type_status(packages, "campaign_starter", "Campaign starters")
    quality_status = _quality_status(quality_gate_results, world_id)
    profile_status = _profile_status()
    drafts = _draft_tasks(world_id)
    quick_entries = _quick_entries()
    warnings = [*batch_status.warnings, *quality_status.warnings, *script_status.warnings, *campaign_status.warnings]
    blockers = [*batch_status.blockers, *quality_status.blockers]
    return ProductionPipelineSummary(
        active_world=world_id,
        active_production_drafts=drafts,
        recent_generated_packages=packages,
        batch_validation_status=batch_status,
        content_coverage_plan=coverage_plan,
        quality_gate_summary=quality_status,
        import_export_profile_status=profile_status,
        script_package_build_status=script_status,
        campaign_starter_status=campaign_status,
        quick_entries=quick_entries,
        warnings=_redact_list(warnings),
        blockers=_redact_list(blockers),
    )


def _first_world_id(items: list[Any]) -> str | None:
    for item in items:
        if getattr(getattr(item, "content_type", None), "value", None) == LocalContentType.WORLD.value:
            return str(getattr(item, "id", ""))
    return None


def _batch_validation_status(worlds_root: Path, library: Any) -> ProductionPipelineStatus:
    world_targets = [
        ContentBatchValidationTarget(package_type=BatchPackageType.WORLD, id=str(item.id))
        for item in library.items
        if getattr(getattr(item, "content_type", None), "value", None) == LocalContentType.WORLD.value
    ][:3]
    if not world_targets:
        return ProductionPipelineStatus(status="not_run", summary="No world packages discovered for batch validation.")
    report = validate_content_batch(
        ContentBatchValidationRequest(
            targets=world_targets,
            worlds_root=str(worlds_root),
            normal_report=True,
        )
    )
    status = "blocked" if report.failed else "warning" if report.warning else "passed"
    return ProductionPipelineStatus(
        status=status,
        count=report.total,
        warnings=[f"{report.warning} packages with warnings"] if report.warning else [],
        blockers=report.blockers[:8],
        summary=f"{report.passed} passed, {report.warning} warning, {report.failed} failed",
    )


def _coverage_plan(world_id: str | None, worlds_root: Path) -> ContentCoveragePlan | None:
    if not world_id:
        return None
    try:
        return build_content_coverage_plan(
            ContentCoveragePlanRequest(target_world=world_id, genre="general", desired_playtime="short", desired_complexity="medium"),
            worlds_root=str(worlds_root),
        )
    except Exception:
        return None


def _recent_packages(items: list[Any]) -> list[ProductionPipelineTask]:
    tasks: list[ProductionPipelineTask] = []
    for item in items:
        content_type = getattr(getattr(item, "content_type", None), "value", str(getattr(item, "content_type", "unknown")))
        if content_type not in {"character_pack", "quest_pack", "NPC_pack", "template_pack", "scenario_suite", "script_package", "campaign_starter"}:
            continue
        tasks.append(
            ProductionPipelineTask(
                tool_id=_tool_for_type(content_type),
                label=str(getattr(item, "name", getattr(item, "id", content_type))),
                status="available",
                summary=f"{content_type} package is indexed locally.",
                warnings=[],
                blockers=[],
            )
        )
    return tasks[:12]


def _package_type_status(packages: list[ProductionPipelineTask], content_type: str, label: str) -> ProductionPipelineStatus:
    count = sum(1 for item in packages if item.tool_id == _tool_for_type(content_type))
    return ProductionPipelineStatus(
        status="ready" if count else "not_run",
        count=count,
        warnings=[] if count else [f"No {label.lower()} generated yet."],
        summary=f"{count} {label.lower()} indexed.",
    )


def _quality_status(results: list[Any], world_id: str | None) -> ProductionPipelineStatus:
    latest = None
    for result in reversed(results):
        if world_id is None or getattr(result, "world_id", None) == world_id:
            latest = result
            break
    if latest is None:
        return ProductionPipelineStatus(status="not_run", summary="No quality gate result recorded.")
    blockers = _redact_list([str(item) for item in (getattr(latest, "blockers", []) or [])][:8])
    warnings = _redact_list([str(item) for item in (getattr(latest, "warnings", []) or [])][:8])
    return ProductionPipelineStatus(
        status="passed" if bool(getattr(latest, "passed", False)) else "blocked",
        count=1,
        warnings=warnings,
        blockers=blockers,
        summary=f"{len(blockers)} blockers, {len(warnings)} warnings",
    )


def _profile_status() -> ProductionPipelineStatus:
    catalog = get_import_export_profile_catalog()
    count = len(catalog.export_profiles) + len(catalog.import_profiles)
    return ProductionPipelineStatus(status="ready", count=count, summary=f"{count} local import/export profiles available.")


def _draft_tasks(world_id: str | None) -> list[ProductionPipelineTask]:
    suffix = f" for {world_id}" if world_id else ""
    return [
        ProductionPipelineTask(tool_id="world_pack_wizard", label="World Wizard", status="ready", summary=f"Create or preview a world draft{suffix}."),
        ProductionPipelineTask(tool_id="npc_pack_generator", label="NPC Pack Generator", status="ready", summary="Generate NPC candidates and character packages."),
        ProductionPipelineTask(tool_id="quest_pack_generator", label="Quest Pack Generator", status="ready", summary="Generate questline drafts and scenario candidates."),
        ProductionPipelineTask(tool_id="batch_validator", label="Batch Validator", status="ready", summary="Run package/world batch validation."),
        ProductionPipelineTask(tool_id="script_package_builder", label="Script Package Builder", status="ready", summary="Build local non-executable script packages."),
        ProductionPipelineTask(tool_id="campaign_starter", label="Campaign Starter Builder", status="ready", summary="Assemble a starter kit through validation and quality dry-run."),
    ]


def _quick_entries() -> list[ProductionPipelineTask]:
    return _draft_tasks(None)


def _tool_for_type(content_type: str) -> str:
    return {
        "script_package": "script_package_builder",
        "campaign_starter": "campaign_starter",
        "NPC_pack": "npc_pack_generator",
        "quest_pack": "quest_pack_generator",
        "character_pack": "npc_pack_generator",
        "template_pack": "template_wizard",
        "scenario_suite": "scenarios",
    }.get(content_type, "local_content_library")


def _redact_list(values: list[str]) -> list[str]:
    return [_redact(value) for value in values]


def _redact(value: str) -> str:
    result = value
    for token in ("sk-", "api_key", "apikey", "secret", "hidden", "private_self_summary", ".env"):
        result = result.replace(token, "[redacted]")
        result = result.replace(token.upper(), "[redacted]")
    return result
