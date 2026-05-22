from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.event_log import EventLog
from app.core.world_state import GameState, LocationState
from app.engine.action_mod_schema import ActionMod, ModActionDefinition
from app.engine.action_mod_test_harness import ActionModTestCase, ActionModTestHarness
from app.engine.action_registry import ActionRegistry
from app.engine.actions.declarative import DeclarativeCheck, DeclarativeCondition, DeclarativeOutcome, DeclarativeStateDeltaTemplate
from app.engine.actions.schemas import SuccessLevel
from app.engine.mod_action_evaluator import ModActionEvaluator
from app.engine.rule_module_contract import RuleModuleManifest, validate_rule_module_manifest
from app.llm.schemas import PlayerActionType, PlayerIntent
from app.main import app
from app.config import Settings
from app.platform.character_pack import CharacterPack, validate_character_pack
from app.platform.extension_certification import CertificationService
from app.platform.mod_audit import ModAuditRepository, ModAuditResult
from app.platform.mod_compatibility_matrix import ModCompatibilityService
from app.platform.mod_import_export import ModImportExportService
from app.platform.module_browser import ModuleBrowserService
from app.platform.module_permissions import ModulePermissionSet, validate_module_permissions
from app.platform.narrative_project import NarrativeProject
from app.platform.narrative_style_mod import NarrativeStyleMod, validate_narrative_style_mod
from app.platform.package_manifest_v2 import PackageFileEntry, PackageManifestV2, PackageTypeV2
from app.platform.project_repository import ProjectRepository
from app.platform.prompt_profile_pack import PromptProfilePack, validate_prompt_profile_pack
from app.platform.provider_profile_pack import ProviderProfilePack, validate_provider_profile_pack
from app.platform.rp_profile_mod import RPProfileMod, RPProfilePatch, validate_rp_profile_mod
from app.platform.script_pack_v2 import ScriptPackV2, validate_script_pack
from app.platform.world_extension_pack import WorldExtensionPack, validate_world_extension_pack
from app.quality.mod_quality_gate import run_mod_quality_gate


def _manifest(package_id: str, package_type: PackageTypeV2, **kwargs: object) -> PackageManifestV2:
    return PackageManifestV2(
        package_id=package_id,
        name=package_id,
        version="1.0.0",
        package_type=package_type,
        target_project_modes=["world"],
        permissions=kwargs.pop("permissions", ModulePermissionSet(content_permissions={"add_content": True})),
        **kwargs,
    )


def _state() -> GameState:
    return GameState(
        world_id="v26",
        locations={"shrine": LocationState(id="shrine", name="Shrine")},
        player={"location_id": "shrine"},
        player_visible_facts=["shrine"],
    )


def _action_definition(action_id: str = "mod.pray", *, leak: bool = False) -> ModActionDefinition:
    return ModActionDefinition(
        id=action_id,
        label="Pray",
        aliases=["pray"],
        category="general",
        preconditions=[DeclarativeCondition(condition_type="at_location", value="shrine")],
        checks=[DeclarativeCheck(check_type="always")],
        outcomes={
            SuccessLevel.SUCCESS: DeclarativeOutcome(
                success_level=SuccessLevel.SUCCESS,
                reason="hidden fact should not be visible" if leak else "Prayer resolved.",
                state_delta_templates=[DeclarativeStateDeltaTemplate(operation="set", path="flags.prayed", value=True)],
            ),
            SuccessLevel.FAILURE: DeclarativeOutcome(success_level=SuccessLevel.FAILURE, reason="Prayer failed."),
        },
        event_type="mod.pray",
    )


def _action_mod(action_id: str = "mod.pray", *, leak: bool = False) -> ActionMod:
    return ActionMod(
        manifest=_manifest(
            "action_pack",
            PackageTypeV2.ACTION_MOD,
            permissions=ModulePermissionSet(action_permissions={"add_declarative_action": True}),
        ),
        actions=[_action_definition(action_id, leak=leak)],
    )


def _write_package(root: Path, package_id: str, package_type: PackageTypeV2, **updates: object) -> Path:
    package_dir = root / "modules" / package_id
    package_dir.mkdir(parents=True)
    manifest = _manifest(package_id, package_type, **updates)
    (package_dir / "package_manifest_v2.json").write_text(manifest.model_dump_json(), encoding="utf-8")
    return package_dir


def _zip_package(manifest: PackageManifestV2, files: dict[str, bytes] | None = None) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("package_manifest_v2.json", manifest.model_dump_json())
        for path, data in (files or {}).items():
            archive.writestr(path, data)
    return stream.getvalue()


def test_v26_manifest_pack_types_and_secret_boundaries() -> None:
    assert _manifest("valid", PackageTypeV2.SCRIPT_PACK).package_type == PackageTypeV2.SCRIPT_PACK
    with pytest.raises(ValueError):
        PackageManifestV2(package_id="bad", name="Bad", version="1", package_type="unknown")
    with pytest.raises(ValueError):
        _manifest("exec", PackageTypeV2.SCRIPT_PACK, entry_points=[{"entry_id": "run", "path": "run.py"}])
    with pytest.raises(ValueError):
        PackageManifestV2(package_id="secret", name="Secret", version="1", package_type=PackageTypeV2.SCRIPT_PACK, description="sk-real-not-allowed-12345678901234567890")

    assert validate_script_pack(ScriptPackV2(manifest=_manifest("script", PackageTypeV2.SCRIPT_PACK), scenarios=[{"id": "s"}])).ok
    assert validate_world_extension_pack(WorldExtensionPack(manifest=_manifest("world", PackageTypeV2.WORLD_EXTENSION_PACK), locations_add=[{"id": "loc"}])).ok
    assert not validate_world_extension_pack(WorldExtensionPack(manifest=_manifest("world2", PackageTypeV2.WORLD_EXTENSION_PACK), locations_add=[{"id": "loc"}]), existing_ids={"loc"}).ok
    assert validate_character_pack(CharacterPack(manifest=_manifest("chars", PackageTypeV2.CHARACTER_PACK), character_profiles=[{"character_id": "c"}])).ok
    assert not validate_prompt_profile_pack(PromptProfilePack(manifest=_manifest("prompts", PackageTypeV2.PROMPT_PROFILE_PACK), prompt_profiles=[{"prompt_profile_id": "p", "can_access_hidden_facts": True}])).ok
    assert not validate_provider_profile_pack(ProviderProfilePack(manifest=_manifest("providers", PackageTypeV2.PROVIDER_PROFILE_PACK), provider_profiles=[{"provider_profile_id": "p", "api_key": "sk-real-not-allowed-12345678901234567890"}])).ok
    assert not validate_narrative_style_mod(NarrativeStyleMod(manifest=_manifest("style", PackageTypeV2.NARRATIVE_STYLE_MOD), style_id="s", name="S", forbidden_behaviors=["override_action_result"])).ok
    assert not validate_rp_profile_mod(RPProfileMod(manifest=_manifest("rp", PackageTypeV2.RP_PROFILE_MOD), patch_rp_profile=[RPProfilePatch(target_profile_id="rp", path="world_npc.knowledge.secret", operation="set", value=True)]), existing_profile_ids={"rp"}).ok


def test_v26_action_mod_state_delta_eventlog_and_no_eval_exec() -> None:
    mod = _action_mod()
    registry = ActionRegistry()
    registry.register_mod_action(mod.actions[0], package_id="action_pack")
    assert registry.get_action_definition("mod.pray") is not None
    with pytest.raises(ValueError):
        registry.register_mod_action(_action_definition("observe"), package_id="conflict")

    state = _state()
    before = state.model_dump_json()
    intent = PlayerIntent(action_type=PlayerActionType.UNKNOWN, raw_text="pray", confidence=1.0, requires_clarification=False)
    execution = ModActionEvaluator().evaluate(mod.actions[0], intent, state)
    assert state.model_dump_json() == before
    assert execution.action_result.state_deltas[0].path == "flags.prayed"
    event_log = EventLog()
    event_log.append(execution.event)
    assert event_log.list_events()[0].action_type == "mod.pray"

    source_root = Path("backend/app")
    checked = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in [source_root / "engine" / "mod_action_evaluator.py", source_root / "engine" / "action_mod_test_harness.py"])
    assert "exec(" not in checked
    assert "eval(" not in checked


def test_v26_action_mod_test_harness_failures_and_cli(tmp_path: Path) -> None:
    mod = _action_mod()
    good_case = ActionModTestCase(
        test_id="good",
        action_id="mod.pray",
        input_intent={"raw_text": "pray"},
        initial_state_fixture=_state().model_dump(mode="json"),
        expected_result_type=SuccessLevel.SUCCESS,
        expected_state_deltas=[{"operation": "set", "path": "flags.prayed", "value": True}],
        expected_event_tags=["mod.pray"],
    )
    assert ActionModTestHarness(mod).run_all_for_mod([good_case]).ok

    mismatch = good_case.model_copy(update={"test_id": "mismatch", "expected_state_deltas": [{"operation": "set", "path": "flags.wrong", "value": True}]})
    assert not ActionModTestHarness(mod).run_all_for_mod([mismatch]).ok

    leaking_mod = _action_mod(leak=True)
    leak_case = good_case.model_copy(update={"test_id": "leak", "forbidden_visible_text_patterns": ["hidden fact"]})
    assert not ActionModTestHarness(leaking_mod).run_all_for_mod([leak_case]).ok

    mod_dir = tmp_path / "action_mod"
    mod_dir.mkdir()
    (mod_dir / "action_mod.json").write_text(mod.model_dump_json(), encoding="utf-8")
    (mod_dir / "action_mod_tests.json").write_text(json.dumps([good_case.model_dump(mode="json")]), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": "backend"}
    result = subprocess.run(
        [sys.executable, "-m", "backend.app.tools.test_action_mod", str(mod_dir), "--json"],
        cwd=Path.cwd(),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert '"ok": true' in result.stdout


def test_v26_rule_module_permissions_and_migration_warning() -> None:
    manifest = RuleModuleManifest(
        module_id="magic",
        name="Magic",
        version="1",
        permissions={"can_add_state_schema": True},
        required_state_schema_extensions=[{"path": "magic.mana"}],
    )
    report = validate_rule_module_manifest(manifest)
    assert report.ok
    assert report.warnings
    with pytest.raises(ValueError):
        RuleModuleManifest(module_id="bad", name="Bad", version="1", permissions={"can_execute_code": True})
    with pytest.raises(ValueError):
        RuleModuleManifest(module_id="bad_llm", name="Bad LLM", version="1", permissions={"can_call_llm": True})
    permission_report = validate_module_permissions(ModulePermissionSet())
    assert permission_report.ok
    assert not permission_report.dangerous_permissions


def test_v26_module_browser_api_matrix_certification_quality_and_audit(tmp_path: Path) -> None:
    project_root = tmp_path / "demo"
    repo = ProjectRepository(tmp_path)
    repo.create_project(NarrativeProject(project_id="demo", name="Demo", project_root=str(project_root)))
    _write_package(project_root, "safe_content", PackageTypeV2.SCRIPT_PACK)
    _write_package(project_root, "needs_dep", PackageTypeV2.SCRIPT_PACK, dependencies=[{"package_id": "missing"}])
    _write_package(project_root, "conflict_a", PackageTypeV2.SCRIPT_PACK, conflicts=["conflict_b"])
    _write_package(project_root, "conflict_b", PackageTypeV2.SCRIPT_PACK)
    unsafe = _write_package(project_root, "unsafe", PackageTypeV2.SCRIPT_PACK)
    (unsafe / "run.exe").write_text("blocked", encoding="utf-8")

    browser = ModuleBrowserService(project_root)
    assert browser.scan().ok
    matrix = ModCompatibilityService(browser).build_matrix(["needs_dep", "conflict_a", "conflict_b"])
    assert not matrix.ok
    assert matrix.load_order == sorted(matrix.load_order)
    assert CertificationService(browser).certify_package("safe_content").ok
    assert not CertificationService(browser).certify_package("unsafe").ok
    assert run_mod_quality_gate(project_root, "safe_content").ok
    assert not run_mod_quality_gate(project_root, "unsafe").ok

    app.state.project_repository = repo
    previous_settings = getattr(app.state, "settings", None)
    try:
        app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
        client = TestClient(app)
        assert client.get("/projects/demo/modules").status_code == 200
        scan = client.post("/projects/demo/modules/scan")
        assert scan.status_code == 200
        assert client.post("/projects/demo/modules/safe_content/validate").status_code == 200
        assert client.post("/projects/demo/modules/safe_content/certify").status_code == 200
        audit = client.get("/projects/demo/modules/audit").json()["records"]
    finally:
        app.state.settings = previous_settings or Settings(llm_provider="mock")
    assert {record["action_type"] for record in audit} >= {"scan", "validate", "certify"}
    assert "sk-" not in json.dumps(audit)


def test_v26_import_export_hardening_and_provider_pack_secret_boundary(tmp_path: Path) -> None:
    service = ModImportExportService(tmp_path)
    zip_slip = io.BytesIO()
    with zipfile.ZipFile(zip_slip, "w") as archive:
        archive.writestr("../evil.txt", b"bad")
    assert not service.import_dry_run(zip_slip.getvalue()).ok

    executable_package = _zip_package(_manifest("exe", PackageTypeV2.SCRIPT_PACK), {"run.exe": b"blocked"})
    assert not service.import_dry_run(executable_package).ok

    provider_manifest = _manifest(
        "provider_pack",
        PackageTypeV2.PROVIDER_PROFILE_PACK,
        included_files=[PackageFileEntry(path="provider.json")],
    )
    provider_package = _zip_package(provider_manifest, {"provider.json": b'{"provider_profile_id":"p","api_key_env":"OPENAI_API_KEY"}'})
    assert service.import_dry_run(provider_package).ok
    service.import_apply(provider_package, confirm=True)
    export = service.export_package("provider_pack")
    assert export.ok
    assert "sk-" not in json.dumps(export.model_dump(mode="json"))

    secret_dir = _write_package(tmp_path, "secret_export", PackageTypeV2.SCRIPT_PACK)
    (secret_dir / "secret.txt").write_text("sk-real-not-allowed-12345678901234567890", encoding="utf-8")
    with pytest.raises(ValueError):
        service.export_package("secret_export")


def test_v26_import_dry_run_does_not_read_forbidden_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    service = ModImportExportService(tmp_path)
    package = _zip_package(_manifest("blocked_env", PackageTypeV2.SCRIPT_PACK), {".env": b"OPENAI_API_KEY=sk-real-not-allowed-12345678901234567890"})
    original_read = zipfile.ZipFile.read
    forbidden_reads: list[str] = []

    def guarded_read(self: zipfile.ZipFile, name: str, *args: object, **kwargs: object) -> bytes:
        if str(name) == ".env":
            forbidden_reads.append(str(name))
        return original_read(self, name, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "read", guarded_read)
    report = service.import_dry_run(package)

    assert not report.ok
    assert forbidden_reads == []


def test_v26_module_browser_does_not_read_forbidden_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package_dir = _write_package(tmp_path, "blocked_env", PackageTypeV2.SCRIPT_PACK)
    (package_dir / ".env").write_text("OPENAI_API_KEY=sk-real-not-allowed-12345678901234567890", encoding="utf-8")
    original_read_text = Path.read_text

    def guarded_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if self.name == ".env":
            raise AssertionError(".env payload should not be read by Module Browser")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)
    detail = ModuleBrowserService(tmp_path).get_module("blocked_env")

    assert detail.summary.validation_status == "invalid"
    assert "secret-like content detected" in detail.summary.errors


def test_v26_no_real_api_and_no_arbitrary_code_execution_markers() -> None:
    platform_sources = [*Path("backend/app/platform").glob("*.py"), Path("backend/app/engine/mod_action_evaluator.py"), Path("backend/app/engine/action_mod_test_harness.py")]
    combined = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in platform_sources)
    assert "openai.OpenAI" not in combined
    assert "requests." not in combined
    assert "subprocess" not in combined
    assert "exec(" not in combined
    assert "eval(" not in combined
