from __future__ import annotations

from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.engine.content.validator import ValidationReport, ValidationSeverity
from app.llm.prompt_ab_test import PromptABTestCase
from app.llm.prompt_profiles import PromptProfile, PromptProfileStore, RPPromptProfile
from app.llm.prompt_regression import PromptRegressionCase
from app.llm.provider_benchmark import ProviderBenchmarkCase, ProviderBenchmarkType


SECRET_TOKENS = ("api_key", "apikey", "secret_key", "private_key", "bearer ", "sk-", "BEGIN PRIVATE KEY")
SENSITIVE_PROMPT_TOKENS = (
    "hidden fact",
    "hidden_facts",
    "npc secret",
    "raw gamestate",
    "raw game_state",
    "raw state_delta",
    "sensitive prompt snapshot",
)
EXECUTABLE_SUFFIXES = {".bat", ".cmd", ".com", ".dll", ".exe", ".js", ".mjs", ".ps1", ".py", ".sh", ".vbs"}


class PromptExperimentPackageManifest(BaseModel):
    package_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    name: str
    version: str = "1.0"
    prompt_profiles: list[PromptProfile] = Field(default_factory=list)
    rp_prompt_profiles: list[RPPromptProfile] = Field(default_factory=list)
    test_cases: list[PromptABTestCase] = Field(default_factory=list)
    benchmark_configs: list[ProviderBenchmarkCase] = Field(default_factory=list)
    regression_configs: list[PromptRegressionCase] = Field(default_factory=list)
    provider_requirements: list[str] = Field(default_factory=list)
    redaction_policy: Literal["safe_redacted", "ids_only"] = "safe_redacted"
    exported_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class PromptExperimentPackageFile(BaseModel):
    path: str
    content: str = ""


class PromptExperimentPackage(BaseModel):
    manifest: PromptExperimentPackageManifest
    files: list[PromptExperimentPackageFile] = Field(default_factory=list)


class PromptExperimentPackageExportRequest(BaseModel):
    package_id: str = Field(default="prompt_experiment", pattern=r"^[A-Za-z0-9_-]+$")
    name: str = "Prompt Experiment Package"
    prompt_profile_ids: list[str] = Field(default_factory=list)
    test_cases: list[PromptABTestCase] = Field(default_factory=list)
    benchmark_configs: list[ProviderBenchmarkCase] = Field(default_factory=list)
    regression_configs: list[PromptRegressionCase] = Field(default_factory=list)
    provider_requirements: list[str] = Field(default_factory=lambda: ["mock", "local_stub"])
    redaction_policy: Literal["safe_redacted", "ids_only"] = "safe_redacted"


class PromptExperimentPackageImportRequest(BaseModel):
    package: PromptExperimentPackage
    confirm_apply: bool = False


class PromptExperimentPackageImportReport(BaseModel):
    package_id: str
    validation: ValidationReport
    dry_run: bool = True
    applied: bool = False
    imported_profile_ids: list[str] = Field(default_factory=list)
    selected_profile_id_before: str | None = None
    selected_profile_id_after: str | None = None


def export_prompt_experiment_package(
    request: PromptExperimentPackageExportRequest,
    *,
    prompt_store: PromptProfileStore,
) -> PromptExperimentPackage:
    available_profiles = {profile.id: profile for profile in prompt_store.list_profiles()}
    selected_ids = request.prompt_profile_ids or sorted(available_profiles)
    profiles = [available_profiles[profile_id] for profile_id in selected_ids if profile_id in available_profiles]
    rp_profiles = [profile.rp_profile for profile in profiles]
    manifest = PromptExperimentPackageManifest(
        package_id=request.package_id,
        name=request.name,
        prompt_profiles=profiles,
        rp_prompt_profiles=rp_profiles,
        test_cases=[_safe_test_case(case) for case in request.test_cases],
        benchmark_configs=request.benchmark_configs or _default_benchmark_configs(),
        regression_configs=request.regression_configs,
        provider_requirements=[_safe_requirement(item) for item in request.provider_requirements],
        redaction_policy=request.redaction_policy,
    )
    package = PromptExperimentPackage(manifest=manifest)
    report = validate_prompt_experiment_package(package)
    if report.errors:
        raise ValueError("Prompt experiment package export contains unsafe data.")
    return package


def import_prompt_experiment_package_dry_run(
    request: PromptExperimentPackageImportRequest,
    *,
    prompt_store: PromptProfileStore,
) -> PromptExperimentPackageImportReport:
    validation = validate_prompt_experiment_package(request.package)
    selected = prompt_store.selected_profile_id()
    return PromptExperimentPackageImportReport(
        package_id=request.package.manifest.package_id,
        validation=validation,
        dry_run=True,
        applied=False,
        imported_profile_ids=[profile.id for profile in request.package.manifest.prompt_profiles],
        selected_profile_id_before=selected,
        selected_profile_id_after=selected,
    )


def apply_prompt_experiment_package_import(
    request: PromptExperimentPackageImportRequest,
    *,
    prompt_store: PromptProfileStore,
) -> PromptExperimentPackageImportReport:
    report = import_prompt_experiment_package_dry_run(request, prompt_store=prompt_store)
    if not request.confirm_apply:
        report.validation.add(
            ValidationSeverity.ERROR,
            "prompt_experiment_package.import_apply",
            "Prompt experiment package import requires explicit confirmation.",
            code="prompt_experiment_package_apply_requires_confirmation",
        )
        return report
    if not report.validation.ok:
        return report
    return report.model_copy(update={"dry_run": False, "applied": True})


def validate_prompt_experiment_package(package: PromptExperimentPackage) -> ValidationReport:
    report = ValidationReport(world_id=package.manifest.package_id)
    _validate_manifest(report, package.manifest)
    for file in package.files:
        _validate_package_path(report, file.path)
        _validate_no_sensitive_text(report, file.content, f"prompt_experiment_package.files.{file.path}")
    _validate_no_sensitive_text(report, package.model_dump(mode="json"), "prompt_experiment_package")
    return report


def _validate_manifest(report: ValidationReport, manifest: PromptExperimentPackageManifest) -> None:
    ids = {manifest.package_id}
    ids.update(manifest.provider_requirements)
    ids.update(profile.id for profile in manifest.prompt_profiles)
    ids.update(profile.id for profile in manifest.rp_prompt_profiles)
    for value in ids:
        if not _is_safe_id(value):
            report.add(
                ValidationSeverity.ERROR,
                "prompt_experiment_package.manifest",
                f"Unsafe manifest id: {value}",
                code="prompt_experiment_package_unsafe_id",
                ref_id=value,
            )
    for profile in manifest.prompt_profiles:
        try:
            profile.validate_security_boundary()
        except ValueError as exc:
            report.add(
                ValidationSeverity.ERROR,
                f"prompt_experiment_package.prompt_profiles.{profile.id}",
                str(exc),
                code="prompt_experiment_package_prompt_profile_rejected",
                ref_id=profile.id,
            )
        if profile.enabled:
            report.add(
                ValidationSeverity.WARNING,
                f"prompt_experiment_package.prompt_profiles.{profile.id}",
                "Imported prompt profiles are not automatically enabled or selected.",
                code="prompt_experiment_package_profile_not_auto_enabled",
                ref_id=profile.id,
            )


def _safe_test_case(case: PromptABTestCase) -> PromptABTestCase:
    return case.model_copy(
        update={
            "input_text": _redact_sensitive(case.input_text),
            "visible_facts": [_redact_sensitive(item) for item in case.visible_facts],
            "hidden_terms": ["[redacted-hidden]" for _ in case.hidden_terms],
        }
    )


def _default_benchmark_configs() -> list[ProviderBenchmarkCase]:
    return [
        ProviderBenchmarkCase(
            id="prompt_package_text_smoke",
            benchmark_type=ProviderBenchmarkType.GENERATE_TEXT_SMOKE,
            prompt="Say ok for a local prompt experiment package smoke test.",
        )
    ]


def _safe_requirement(value: str) -> str:
    return "".join(character for character in value if character.isalnum() or character in {"_", "-", ".", ":"}) or "unknown"


def _validate_package_path(report: ValidationReport, path: str) -> None:
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if not normalized or normalized.startswith("/") or normalized.startswith("~") or ".." in pure.parts:
        report.add(
            ValidationSeverity.ERROR,
            f"prompt_experiment_package.files.{path}",
            "Prompt experiment package file path escapes the package root.",
            code="prompt_experiment_package_path_traversal_rejected",
            ref_id=path,
        )
    if pure.suffix.lower() in EXECUTABLE_SUFFIXES:
        report.add(
            ValidationSeverity.ERROR,
            f"prompt_experiment_package.files.{path}",
            "Prompt experiment packages cannot contain executable files.",
            code="prompt_experiment_package_executable_rejected",
            ref_id=path,
        )


def _validate_no_sensitive_text(report: ValidationReport, value: Any, path: str) -> None:
    for text in _iter_strings(value):
        lowered = text.lower()
        if any(token.lower() in lowered for token in SECRET_TOKENS):
            report.add(
                ValidationSeverity.ERROR,
                path,
                "Prompt experiment package contains API key or sensitive configuration text.",
                code="prompt_experiment_package_secret_rejected",
            )
            return
        if any(token in lowered for token in SENSITIVE_PROMPT_TOKENS):
            report.add(
                ValidationSeverity.ERROR,
                path,
                "Prompt experiment package contains hidden, raw state, or sensitive prompt content.",
                code="prompt_experiment_package_sensitive_prompt_rejected",
            )
            return


def _redact_sensitive(value: str) -> str:
    lowered = value.lower()
    if any(token.lower() in lowered for token in SECRET_TOKENS) or any(token in lowered for token in SENSITIVE_PROMPT_TOKENS):
        return "[redacted]"
    return value


def _is_safe_id(value: str) -> bool:
    return bool(value) and all(character.isalnum() or character in {"_", "-", ".", ":"} for character in value)


def _iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for key, child in value.items() for item in _iter_strings(key) + _iter_strings(child)]
    if isinstance(value, list):
        return [item for child in value for item in _iter_strings(child)]
    return []
