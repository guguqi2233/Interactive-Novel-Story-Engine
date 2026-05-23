from __future__ import annotations

import base64
from io import BytesIO
import json
from pathlib import Path
from shutil import copytree
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.world_state import GameState, LocationState
from app.db.repository import SQLiteSaveRepository
from app.engine.action_mod_schema import ModActionDefinition
from app.engine.action_registry import ActionRegistry
from app.engine.actions.declarative import DeclarativeOutcome, DeclarativeStateDeltaTemplate
from app.engine.actions.schemas import SuccessLevel
from app.engine.content.script_package_builder import ScriptPackageBuildRequest, ScriptPackageFile, ScriptPackageManifest
from app.engine.rule_module_contract import RuleModuleManifest
from app.main import app
from app.platform.character_pack import CharacterPack as PlatformCharacterPack
from app.platform.character_pack import validate_character_pack as validate_platform_character_pack
from app.platform.module_permissions import ModulePermissionSet
from app.platform.narrative_project import NarrativeProject
from app.platform.package_manifest_v2 import PackageManifestV2, PackageTypeV2
from app.platform.provider_profile_pack import ProviderProfilePack, validate_provider_profile_pack
from app.platform.script_pack_v2 import ScriptPackV2, validate_script_pack
from app.platform.world_extension_pack import WorldExtensionPack, validate_world_extension_pack
from app.platform.project_repository import ProjectRepository
from app.session_store import InMemorySessionStore


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"


def _client(tmp_path: Path) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(REPO_ROOT / "worlds" / "mist_valley", worlds_root / "mist_valley")
    project_root = tmp_path / "projects" / "demo"
    project_root.mkdir(parents=True)
    _write_project_modules(project_root)
    project_repo = ProjectRepository(tmp_path / "projects")
    project_repo.save_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    app.state.project_repository = project_repo
    app.state.session_store = InMemorySessionStore(worlds_root=worlds_root)
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v34.sqlite")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'v34.sqlite'}",
        enable_authoring_api=True,
        enable_module_api=True,
        enable_debug_api=False,
        llm_provider="mock",
        llm_api_key="sk-test-v34-secret-must-not-appear",
    )
    return TestClient(app)


def _manifest(package_id: str, package_type: PackageTypeV2, **updates: object) -> PackageManifestV2:
    values: dict[str, object] = {
        "package_id": package_id,
        "name": package_id,
        "version": "1.0.0",
        "package_type": package_type,
        "target_project_modes": ["world"],
        "permissions": ModulePermissionSet(content_permissions={"add_content": True}),
    }
    values.update(updates)
    return PackageManifestV2(**values)


def _write_project_modules(project_root: Path) -> None:
    modules_root = project_root / "modules"
    modules_root.mkdir()
    safe = modules_root / "safe_content"
    safe.mkdir()
    safe.joinpath("package_manifest_v2.json").write_text(
        _manifest("safe_content", PackageTypeV2.SCRIPT_PACK).model_dump_json(),
        encoding="utf-8",
    )
    action = modules_root / "action_pack"
    action.mkdir()
    action.joinpath("package_manifest_v2.json").write_text(
        _manifest(
            "action_pack",
            PackageTypeV2.ACTION_MOD,
            permissions=ModulePermissionSet(action_permissions={"add_declarative_action": True}),
        ).model_dump_json(),
        encoding="utf-8",
    )
    needs_dep = modules_root / "needs_dep"
    needs_dep.mkdir()
    needs_dep.joinpath("package_manifest_v2.json").write_text(
        _manifest("needs_dep", PackageTypeV2.SCRIPT_PACK, dependencies=[{"package_id": "missing_pack"}]).model_dump_json(),
        encoding="utf-8",
    )
    unsafe = modules_root / "unsafe_code"
    unsafe.mkdir()
    unsafe.joinpath("package_manifest_v2.json").write_text(
        json.dumps(
            {
                "package_id": "unsafe_code",
                "name": "unsafe_code",
                "version": "1.0.0",
                "package_type": "script_pack",
                "target_project_modes": ["world"],
                "permissions": {"file_permissions": {"execute_code": True}},
            }
        ),
        encoding="utf-8",
    )
    unsafe.joinpath("run.py").write_text("print('must not execute')\n", encoding="utf-8")


def _world_pack_draft() -> dict[str, object]:
    return {
        "world_id": "v34_draft_world",
        "name": "V34 Draft World",
        "genre": "mystery",
        "tone": "grounded",
        "description": "Local authoring draft only.",
        "starting_location": "arrival_square",
        "location_seed_count": 1,
        "npc_seed_count": 1,
        "quest_seed_count": 1,
        "enabled_systems": ["quests", "factions", "rumors"],
        "default_prompt_profile": "default_safe",
        "default_quality_profile": "standard",
    }


def _script_package_request(tmp_path: Path) -> dict[str, object]:
    return ScriptPackageBuildRequest(
        manifest=ScriptPackageManifest(
            package_id="v34_script_pack",
            name="V34 Script Pack",
            included_worlds=["mist_valley"],
            dependencies=["mist_valley"],
        ),
        files=[ScriptPackageFile(path="beats/opening.yaml", content="beats:\n  - id: opening\n    summary: Safe beat.\n")],
        available_dependency_ids=["mist_valley"],
        packages_root=str(tmp_path / "packages"),
    ).model_dump(mode="json")


def _character_pack_payload() -> dict[str, object]:
    return {
        "world_id": "mist_valley",
        "pack": {
            "manifest": {
                "pack_id": "v34_character_pack",
                "name": "V34 Character Pack",
                "exported_at": "2026-05-24T00:00:00+00:00",
                "character_ids": ["v34_mira"],
            },
            "characters": [{"id": "v34_mira", "name": "Mira", "location_id": "village_square"}],
            "rp_profiles": {"v34_mira": {"public_persona": "A careful guide.", "private_notes": "authoring-only secret"}},
            "voice_profiles": {"v34_mira": {"tone": "warm"}},
            "files": [],
        },
    }


def test_v34_authoring_safe_apis_and_dry_runs_do_not_modify_active_game_state(tmp_path: Path) -> None:
    client = _client(tmp_path)
    start = client.post("/game/start", json={"world_id": "mist_valley"})
    assert start.status_code == 200, start.text
    session_id = start.json()["session_id"]
    before = client.get(f"/game/state/{session_id}").json()["visible_state"]

    world_preview = client.post("/authoring/production/world-pack/preview", json=_world_pack_draft())
    assert world_preview.status_code == 200, world_preview.text
    assert world_preview.json()["writes_to_disk"] is False
    assert world_preview.json()["applied"] is False
    assert not (tmp_path / "worlds" / "v34_draft_world").exists()

    script_dry_run = client.post("/production/script-packages/build-dry-run", json=_script_package_request(tmp_path))
    assert script_dry_run.status_code == 200, script_dry_run.text
    assert script_dry_run.json()["dry_run"] is True
    assert script_dry_run.json()["applied"] is False
    assert not (tmp_path / "packages").exists()

    character_dry_run = client.post("/authoring/character-packs/import-dry-run", json=_character_pack_payload())
    assert character_dry_run.status_code == 200, character_dry_run.text
    assert character_dry_run.json()["applied"] is False
    character_payload = json.dumps(character_dry_run.json(), ensure_ascii=False).lower()
    assert "authoring-only secret" not in character_payload

    graph = client.get("/authoring/worlds/mist_valley/quests/graph")
    assert graph.status_code == 200, graph.text
    graph_payload = graph.json()
    graph_payload["quests"][0]["stages"][0]["title"] = "Draft Only Title"
    quest_preview = client.post("/authoring/worlds/mist_valley/quests/graph/preview", json={"graph": graph_payload})
    assert quest_preview.status_code == 200, quest_preview.text
    assert "Draft Only Title" in quest_preview.json()["yaml_content"]

    files = client.get("/authoring/worlds/mist_valley/files")
    validation_graph = client.get("/authoring/worlds/mist_valley/validation-graph")
    map_graph = client.get("/authoring/worlds/mist_valley/map")
    assert files.status_code == 200
    assert validation_graph.status_code == 200
    assert map_graph.status_code == 200
    file_names = {item["file_name"] if isinstance(item, dict) else str(item) for item in files.json()["files"]}
    assert {"locations.yaml", "npcs.yaml", "items.yaml", "quests.yaml"} <= file_names

    after = client.get(f"/game/state/{session_id}").json()["visible_state"]
    assert after == before
    combined = "\n".join([world_preview.text, script_dry_run.text, character_dry_run.text, validation_graph.text]).lower()
    assert "sk-test-v34-secret-must-not-appear" not in combined
    assert "api_key" not in combined
    assert "state_deltas" not in combined


def test_v34_pack_validators_filter_hidden_and_secret_content() -> None:
    world_pack = WorldExtensionPack(
        manifest=_manifest("world_ext", PackageTypeV2.WORLD_EXTENSION_PACK),
        facts_add=[{"id": "public", "text": "Public fact", "visibility": "public"}],
    )
    assert validate_world_extension_pack(world_pack).ok
    hidden_world_pack = WorldExtensionPack(
        manifest=_manifest("hidden_world_ext", PackageTypeV2.WORLD_EXTENSION_PACK),
        facts_add=[{"id": "hidden", "text": "hidden fact full text", "visibility": "hidden"}],
    )
    assert not validate_world_extension_pack(hidden_world_pack).ok

    script_pack = ScriptPackV2(manifest=_manifest("script", PackageTypeV2.SCRIPT_PACK), scenarios=[{"id": "safe"}])
    assert validate_script_pack(script_pack).ok
    unsafe_script = ScriptPackV2(manifest=_manifest("unsafe_script", PackageTypeV2.SCRIPT_PACK), scenarios=[{"text": "hidden fact full text"}])
    assert not validate_script_pack(unsafe_script).ok

    character_pack = PlatformCharacterPack(
        manifest=_manifest("characters", PackageTypeV2.CHARACTER_PACK),
        character_profiles=[{"character_id": "c1", "private_notes": "npc secret authoring-only"}],
    )
    character_summary = character_pack.safe_summary()
    assert validate_platform_character_pack(character_pack).ok
    assert "npc secret authoring-only" not in json.dumps(character_summary, ensure_ascii=False).lower()

    provider_pack = ProviderProfilePack(
        manifest=_manifest("providers", PackageTypeV2.PROVIDER_PROFILE_PACK),
        provider_profiles=[{"provider_profile_id": "mock", "api_key_env": "OPENAI_API_KEY", "secret_ref": "local/mock"}],
    )
    assert validate_provider_profile_pack(provider_pack).ok
    bad_provider_pack = ProviderProfilePack(
        manifest=_manifest("bad_providers", PackageTypeV2.PROVIDER_PROFILE_PACK),
        provider_profiles=[{"provider_profile_id": "bad", "api_key": "sk-real-not-allowed"}],
    )
    assert not validate_provider_profile_pack(bad_provider_pack).ok


def test_v34_mod_browser_permissions_compatibility_certification_quality_and_audit(tmp_path: Path) -> None:
    client = _client(tmp_path)

    scan = client.post("/projects/demo/modules/scan")
    assert scan.status_code == 200, scan.text
    modules = client.get("/projects/demo/modules")
    assert modules.status_code == 200
    module_ids = {module["package_id"] for module in modules.json()["modules"]}
    assert {"safe_content", "action_pack", "needs_dep", "unsafe_code"} <= module_ids

    permission_summary = client.get("/projects/demo/modules/permissions-summary")
    unsafe_permissions = client.get("/projects/demo/modules/unsafe_code/permissions")
    assert permission_summary.status_code == 200
    assert unsafe_permissions.status_code == 200
    assert "execute_code" in unsafe_permissions.json()["permissions"]["dangerous_permissions"]
    assert unsafe_permissions.json()["permissions"]["risk_level"] == "blocked"

    compatibility = client.post("/projects/demo/modules/compatibility-matrix", json={"package_ids": ["safe_content", "needs_dep"]})
    selection = client.post("/projects/demo/modules/check-selection", json={"package_ids": ["needs_dep"]})
    assert compatibility.status_code == 200
    assert selection.status_code == 200
    assert compatibility.json()["matrix"]["ok"] is False
    assert any("missing dependency" in " ".join(entry["errors"]) for entry in compatibility.json()["matrix"]["entries"])

    certification = client.post("/projects/demo/modules/safe_content/certify")
    unsafe_certification = client.post("/projects/demo/modules/unsafe_code/certify")
    quality_gate = client.post("/projects/demo/modules/safe_content/quality-gate", json={"require_action_tests": False})
    unsafe_quality_gate = client.post("/projects/demo/modules/unsafe_code/quality-gate", json={"require_action_tests": False})
    audit = client.get("/projects/demo/modules/audit")
    assert certification.status_code == 200
    assert unsafe_certification.status_code == 200
    assert quality_gate.status_code == 200
    assert unsafe_quality_gate.status_code == 200
    assert certification.json()["certification"]["ok"] is True
    assert unsafe_certification.json()["certification"]["level"] == "unsafe_blocked"
    assert quality_gate.json()["quality_gate"]["ok"] is True
    assert unsafe_quality_gate.json()["quality_gate"]["ok"] is False
    assert audit.status_code == 200
    assert {record["action_type"] for record in audit.json()["records"]} >= {"scan", "certify", "quality_gate"}

    combined = "\n".join([scan.text, modules.text, permission_summary.text, compatibility.text, certification.text, quality_gate.text, audit.text]).lower()
    assert "sk-test-v34-secret-must-not-appear" not in combined
    assert "provider_secret" not in combined
    assert "raw_env" not in combined


def test_v34_import_export_safe_apply_boundaries_and_active_state(tmp_path: Path) -> None:
    client = _client(tmp_path)
    start = client.post("/game/start", json={"world_id": "mist_valley"})
    session_id = start.json()["session_id"]
    before = client.get(f"/game/state/{session_id}").json()["visible_state"]

    exported = client.get("/authoring/export/worlds/mist_valley")
    assert exported.status_code == 200, exported.text
    exported_payload = exported.text.lower()
    assert "sk-test-v34-secret-must-not-appear" not in exported_payload
    assert "api_key" not in exported_payload

    app.state.worlds_root = tmp_path / "imported_worlds"
    dry_run = client.post("/authoring/import/packages/dry-run", json={"archive_base64": exported.json()["archive_base64"]})
    blocked_apply = client.post("/authoring/import/packages/apply", json={"archive_base64": exported.json()["archive_base64"]})
    assert dry_run.status_code == 200
    assert dry_run.json()["ok"] is True
    assert not (tmp_path / "imported_worlds" / "mist_valley").exists()
    assert blocked_apply.status_code == 400
    assert "explicit confirmation" in blocked_apply.json()["detail"]

    secret_archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "leaky_world"},
            "worlds/leaky_world/manifest.yaml": "world_id: leaky_world\nname: Leaky\n",
            "worlds/leaky_world/.env": "OPENAI_API_KEY=sk-real-looking-secret\n",
        }
    )
    secret_import = client.post("/authoring/import/packages/dry-run", json={"archive_base64": secret_archive})
    assert secret_import.status_code == 200
    assert secret_import.json()["ok"] is False
    assert "sk-real-looking-secret" not in secret_import.text

    after = client.get(f"/game/state/{session_id}").json()["visible_state"]
    assert after == before


def test_v34_action_mod_and_rule_module_boundaries(tmp_path: Path) -> None:
    definition = ModActionDefinition(
        id="v34.pray",
        label="Pray",
        aliases=["pray"],
        category="general",
        outcomes={
            SuccessLevel.SUCCESS: DeclarativeOutcome(
                success_level=SuccessLevel.SUCCESS,
                reason="Prayer resolved locally.",
                state_delta_templates=[DeclarativeStateDeltaTemplate(operation="set", path="flags.v34_prayed", value=True)],
            )
        },
        event_type="v34.pray.resolved",
    )
    registry = ActionRegistry(include_core=False)
    registry.register_mod_action(definition, package_id="action_pack")
    registered = registry.list_mod_actions()[0]
    assert registered.id == "v34.pray"
    assert registered.module_id == "action_pack"
    assert registered.source == "mod"
    assert definition.event_type == "v34.pray.resolved"
    assert definition.outcomes[SuccessLevel.SUCCESS].state_delta_templates[0].path == "flags.v34_prayed"

    client = _client(tmp_path)
    invalid_delta = {
        "module_id": "bad",
        "name": "Bad",
        "version": "1.0.0",
        "actions": [
            {
                "id": "bad.write",
                "label": "Unsafe Write",
                "aliases": ["unsafe_write"],
                "category": "general",
                "target_specs": [{"kind": "current_location"}],
                "outcomes": {
                    "success": {
                        "success_level": "success",
                        "reason": "bad",
                        "state_delta_templates": [{"operation": "set", "path": "player.hp", "value": 1}],
                    }
                },
                "event_type": "bad.write",
            }
        ],
    }
    response = client.post("/authoring/action-mods/validate", json=invalid_delta)
    assert response.status_code == 200
    assert response.json()["validation"]["ok"] is False
    assert "forbidden_state_delta_path" in response.text.lower()

    safe_rule = RuleModuleManifest(module_id="safe_rule", name="Safe Rule", version="1.0.0", permissions={"can_add_actions": True})
    assert safe_rule.safe_summary()["experimental"] is True
    try:
        RuleModuleManifest(module_id="bad_rule", name="Bad Rule", version="1.0.0", permissions={"can_execute_code": True})
    except ValueError as exc:
        assert "execute_code" in str(exc)
    else:
        raise AssertionError("Rule Module contract allowed execute_code")


def test_v34_frontend_authoring_mod_ui_static_regression() -> None:
    app_source = (FRONTEND / "src" / "App.tsx").read_text(encoding="utf-8")
    api_source = (FRONTEND / "src" / "api.ts").read_text(encoding="utf-8")
    check_source = (FRONTEND / "scripts" / "check-v34-authoring-ui.mjs").read_text(encoding="utf-8")
    package_json = (FRONTEND / "package.json").read_text(encoding="utf-8")
    combined = "\n".join([app_source, api_source, check_source, package_json])

    for token in [
        "AuthoringWorkspaceShell",
        "WorldPackWizardPanel",
        "Script Package Builder",
        "Character Pack",
        "Quest Graph",
        "ActionModEditorPanel",
        "ActionModTestHarnessPanel",
        "RuleModuleContractPanel",
        "ModuleBrowserProPanel",
        "ModPermissionDashboardProPanel",
        "CompatibilityMatrixProPanel",
        "ExtensionCertificationProPanel",
        "ImportExportWizardProPanel",
        "ModQualityGateProPanel",
        "AuthoringValidationDashboardPanel",
        "AuthoringDiffPreview",
        "AuthoringOnlyPreviewDetails",
        "redactAuthoringPreviewText",
        "redactReportText",
        "SafeApplyWorkflowPanel",
        "check:v34-authoring-ui",
    ]:
        assert token in combined

    for safety_copy in [
        "local-only",
        "No online marketplace",
        "No remote download",
        "No arbitrary code execution",
        "does not modify active GameState",
        "validation, dry-run, and explicit confirm",
    ]:
        assert safety_copy in combined

    lowered = combined.lower()
    assert 'name="api_key"' not in lowered
    assert "sk-test-v34-secret-must-not-appear" not in combined
    app_lowered = app_source.lower()
    assert "enable dangerous permission" not in app_lowered
    assert "override dangerous permission" not in app_lowered
    assert "<pre>{previewContent}</pre>" not in app_source
    assert "redactReportText(issue.message)" in app_source
    assert "Authoring-only preview" in app_source
    assert "<button>online marketplace</button>" not in lowered
    assert "<button>remote download</button>" not in lowered


def _archive_b64(files: dict[str, str | dict[str, object]]) -> str:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, json.dumps(content) if isinstance(content, dict) else content)
    return base64.b64encode(buffer.getvalue()).decode("ascii")
