import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.prompt_ab_test import PromptABTestCase
from app.llm.prompt_experiment_packages import (
    PromptExperimentPackage,
    PromptExperimentPackageFile,
    PromptExperimentPackageImportRequest,
    PromptExperimentPackageManifest,
    export_prompt_experiment_package,
    import_prompt_experiment_package_dry_run,
)
from app.llm.prompt_profiles import PromptProfileStore
from app.main import app


def test_export_package_success() -> None:
    package = export_prompt_experiment_package(
        request=_export_request(),
        prompt_store=PromptProfileStore(),
    )

    assert package.manifest.package_id == "prompt_pack"
    assert package.manifest.prompt_profiles
    assert package.manifest.benchmark_configs


def test_export_does_not_contain_api_key_or_hidden_text() -> None:
    package = export_prompt_experiment_package(
        request=_export_request(
            test_cases=[
                PromptABTestCase(
                    id="redacted_case",
                    input_text="LLM_API_KEY=sk-real-looking-secret",
                    hidden_terms=["the mayor forged the charter"],
                )
            ]
        ),
        prompt_store=PromptProfileStore(),
    )
    payload = json.dumps(package.model_dump(mode="json"), ensure_ascii=False)

    assert "sk-real-looking-secret" not in payload
    assert "the mayor forged the charter" not in payload
    assert "[redacted]" in payload


def test_import_dry_run_does_not_write_or_enable_profile() -> None:
    store = PromptProfileStore()
    selected_before = store.selected_profile_id()
    package = export_prompt_experiment_package(request=_export_request(), prompt_store=store)
    report = import_prompt_experiment_package_dry_run(
        PromptExperimentPackageImportRequest(package=package),
        prompt_store=store,
    )

    assert report.validation.ok
    assert report.dry_run is True
    assert report.applied is False
    assert report.selected_profile_id_before == selected_before
    assert report.selected_profile_id_after == selected_before
    assert store.selected_profile_id() == selected_before


def test_invalid_manifest_is_rejected() -> None:
    package = PromptExperimentPackage(
        manifest=PromptExperimentPackageManifest(
            package_id="bad_pack",
            name="Bad Pack",
            provider_requirements=["../../openai"],
        )
    )
    report = import_prompt_experiment_package_dry_run(
        PromptExperimentPackageImportRequest(package=package),
        prompt_store=PromptProfileStore(),
    )

    assert not report.validation.ok
    assert any(issue.code == "prompt_experiment_package_unsafe_id" for issue in report.validation.errors)


def test_executable_and_path_traversal_are_rejected() -> None:
    package = PromptExperimentPackage(
        manifest=PromptExperimentPackageManifest(package_id="unsafe_pack", name="Unsafe Pack"),
        files=[
            PromptExperimentPackageFile(path="../escape.yaml", content="safe"),
            PromptExperimentPackageFile(path="scripts/run.py", content="print('no')"),
        ],
    )
    report = import_prompt_experiment_package_dry_run(
        PromptExperimentPackageImportRequest(package=package),
        prompt_store=PromptProfileStore(),
    )
    codes = {issue.code for issue in report.validation.errors}

    assert "prompt_experiment_package_path_traversal_rejected" in codes
    assert "prompt_experiment_package_executable_rejected" in codes


def test_imported_profile_not_auto_enabled_via_api() -> None:
    client = TestClient(app)
    previous_settings = getattr(app.state, "settings", None)
    previous_store = getattr(app.state, "prompt_profile_store", None)
    try:
        app.state.settings = Settings(enable_debug_api=True, llm_provider="mock")
        app.state.prompt_profile_store = PromptProfileStore()
        exported = client.post(
            "/prompt-lab/experiment-packages/export",
            json={"package_id": "api_pack", "name": "API Pack"},
        )
        applied = client.post(
            "/prompt-lab/experiment-packages/import-apply",
            json={"package": exported.json(), "confirm_apply": True},
        )
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
        if previous_store is not None:
            app.state.prompt_profile_store = previous_store

    assert exported.status_code == 200
    assert applied.status_code == 200
    payload = applied.json()
    assert payload["applied"] is True
    assert payload["selected_profile_id_before"] == payload["selected_profile_id_after"]


def _export_request(**updates: object):
    data = {
        "package_id": "prompt_pack",
        "name": "Prompt Pack",
    }
    data.update(updates)
    from app.llm.prompt_experiment_packages import PromptExperimentPackageExportRequest

    return PromptExperimentPackageExportRequest.model_validate(data)
