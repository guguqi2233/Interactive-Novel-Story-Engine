from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.quality.mod_compat_stress import (
    ModCompatibilityStressRequest,
    run_mod_compatibility_stress,
)
from app.session_store import InMemorySessionStore

from .test_mod_loader import write_mod


def make_client(tmp_path: Path) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "mod_compat.db")
    app.state.mods_root = tmp_path / "mods"
    app.state.mod_compat_stress_reports = []
    app.state.settings = Settings(llm_provider="mock")
    return TestClient(app)


def test_mod_compatibility_stress_passes_compatible_mods(tmp_path: Path) -> None:
    write_mod(tmp_path, "base_mod", load_order_hint=0)
    write_mod(tmp_path, "addon_mod", dependencies=["base_mod"], load_order_hint=1)

    report = run_mod_compatibility_stress(
        ModCompatibilityStressRequest(
            available_mods=["base_mod", "addon_mod"],
            selected_worlds=["mist_valley"],
            max_combinations=10,
            seed=1,
        ),
        mods_root=tmp_path / "mods",
    )

    combined = next(result for result in report.results if set(result.mod_ids) == {"base_mod", "addon_mod"})
    assert combined.ok is True
    assert combined.load_order == ["base_mod", "addon_mod"]
    assert combined.scenario_subset_ids


def test_mod_compatibility_stress_reports_missing_dependency(tmp_path: Path) -> None:
    write_mod(tmp_path, "addon_mod", dependencies=["missing_mod"])

    report = run_mod_compatibility_stress(
        ModCompatibilityStressRequest(available_mods=["addon_mod"], max_combinations=5),
        mods_root=tmp_path / "mods",
    )

    result = report.results[0]
    assert result.ok is False
    assert result.dependency_errors == {"addon_mod": ["missing_mod"]}
    assert report.failed_combinations == 1


def test_mod_compatibility_stress_reports_conflicts(tmp_path: Path) -> None:
    write_mod(tmp_path, "first_mod", conflicts=["second_mod"])
    write_mod(tmp_path, "second_mod")

    report = run_mod_compatibility_stress(
        ModCompatibilityStressRequest(
            available_mods=["first_mod", "second_mod"],
            max_combinations=10,
            seed=2,
        ),
        mods_root=tmp_path / "mods",
    )

    result = next(item for item in report.results if item.mod_ids == ["first_mod", "second_mod"])
    assert result.ok is False
    assert ["first_mod", "second_mod"] in result.conflicts


def test_mod_compatibility_stress_reports_broken_reference(tmp_path: Path) -> None:
    mod_path = write_mod(tmp_path, "broken_mod")
    locations_path = mod_path / "content" / "mist_valley" / "locations.yaml"
    locations_path.write_text(
        locations_path.read_text(encoding="utf-8").replace("north: old_bridge", "north: missing_bridge"),
        encoding="utf-8",
    )

    report = run_mod_compatibility_stress(
        ModCompatibilityStressRequest(available_mods=["broken_mod"], max_combinations=5),
        mods_root=tmp_path / "mods",
    )

    result = report.results[0]
    assert result.ok is False
    assert result.broken_references
    assert any("missing_bridge" in message for message in result.validation_errors)


def test_mod_compatibility_stress_rejects_path_traversal(tmp_path: Path) -> None:
    write_mod(tmp_path, "traversal_mod", content_paths=["../outside"], copy_world=False)

    report = run_mod_compatibility_stress(
        ModCompatibilityStressRequest(available_mods=["traversal_mod"], max_combinations=5),
        mods_root=tmp_path / "mods",
    )

    result = report.results[0]
    assert result.ok is False
    assert any("Unsafe mod content path" in message for message in result.validation_errors)


def test_mod_compatibility_stress_rejects_executable_content_and_redacts_paths(tmp_path: Path) -> None:
    mod_path = write_mod(tmp_path, "unsafe_mod")
    (mod_path / "content" / "mist_valley" / "payload.py").write_text("print('nope')\n", encoding="utf-8")

    report = run_mod_compatibility_stress(
        ModCompatibilityStressRequest(available_mods=["unsafe_mod"], max_combinations=5),
        mods_root=tmp_path / "mods",
    )

    result = report.results[0]
    assert result.ok is False
    assert any("executable code" in message.lower() for message in result.validation_errors)
    normal_payload = str(report.model_dump_normal())
    assert str(tmp_path) not in normal_payload


def test_mod_compatibility_stress_api_runs(tmp_path: Path) -> None:
    write_mod(tmp_path, "base_mod")
    client = make_client(tmp_path)

    response = client.post(
        "/quality/mods/compatibility-stress/run",
        json={"available_mods": ["base_mod"], "selected_worlds": ["mist_valley"], "max_combinations": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tested_combinations"] == 1
    assert payload["quality_report"]["categories"] == ["mod_compatibility_stress"]


def test_mod_compatibility_stress_api_redacts_manifest_error_path(tmp_path: Path) -> None:
    bad_mod = tmp_path / "mods" / "bad_mod"
    bad_mod.mkdir(parents=True)
    bad_mod.joinpath("mod.yaml").write_text("id: bad_mod\nname: Bad\n", encoding="utf-8")
    client = make_client(tmp_path)

    response = client.post("/quality/mods/compatibility-stress/run", json={"available_mods": ["bad_mod"]})

    assert response.status_code == 400
    assert str(tmp_path) not in response.text
    assert "mod.yaml" in response.text
