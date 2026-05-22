from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from app.core.world_state import GameState, LocationState
from app.engine.action_mod_schema import ActionMod, ModActionDefinition
from app.engine.action_mod_test_harness import ActionModTestCase, ActionModTestHarness
from app.engine.action_registry import ActionRegistry
from app.engine.mod_action_evaluator import ModActionEvaluator
from app.engine.actions.declarative import DeclarativeOutcome, DeclarativeStateDeltaTemplate
from app.engine.actions.schemas import SuccessLevel
from app.engine.rule_module_contract import RuleModuleManifest
from app.platform.character_pack import CharacterPack, validate_character_pack
from app.platform.extension_certification import CertificationService
from app.platform.mod_audit import ModAuditRepository, ModAuditResult
from app.platform.mod_compatibility_matrix import ModCompatibilityService
from app.platform.mod_import_export import ModImportExportService
from app.platform.module_browser import ModuleBrowserService
from app.platform.module_permissions import ModulePermissionSet, validate_module_permissions
from app.platform.narrative_style_mod import NarrativeStyleMod, validate_narrative_style_mod
from app.platform.package_manifest_v2 import PackageFileEntry, PackageManifestV2, PackageTypeV2
from app.platform.prompt_profile_pack import PromptProfilePack, validate_prompt_profile_pack
from app.platform.provider_profile_pack import ProviderProfilePack, validate_provider_profile_pack
from app.platform.rp_profile_mod import RPProfileMod, RPProfilePatch, validate_rp_profile_mod
from app.platform.script_pack_v2 import ScriptPackV2, validate_script_pack
from app.platform.world_extension_pack import WorldExtensionPack, WorldExtensionPatch, validate_world_extension_pack
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


def test_manifest_v2_and_permission_defaults_block_dangerous_permissions() -> None:
    manifest = _manifest("safe_pack", PackageTypeV2.SCRIPT_PACK)
    assert manifest.safe_summary()["package_type"] == "script_pack"
    with pytest.raises(ValueError):
        PackageManifestV2(
            package_id="bad",
            name="Bad",
            version="1.0",
            package_type="unknown",
        )
    with pytest.raises(ValueError):
        _manifest("bad_entry", PackageTypeV2.SCRIPT_PACK, entry_points=[{"entry_id": "run", "path": "run.py"}])

    permissions = ModulePermissionSet(file_permissions={"execute_code": True}, content_permissions={"add_content": True})
    report = validate_module_permissions(permissions)
    assert not report.ok
    assert "execute_code" in report.dangerous_permissions


def test_pack_validators_redact_and_block_unsafe_content() -> None:
    script = ScriptPackV2(manifest=_manifest("script", PackageTypeV2.SCRIPT_PACK), scenarios=[{"id": "s1"}])
    assert validate_script_pack(script).ok
    hidden = ScriptPackV2(manifest=_manifest("hidden_script", PackageTypeV2.SCRIPT_PACK), scenarios=[{"text": "hidden fact: x"}])
    assert not validate_script_pack(hidden).ok

    world = WorldExtensionPack(manifest=_manifest("world_ext", PackageTypeV2.WORLD_EXTENSION_PACK), locations_add=[{"id": "loc"}])
    assert validate_world_extension_pack(world).ok
    conflict = validate_world_extension_pack(world, existing_ids={"loc"})
    assert not conflict.ok

    character = CharacterPack(
        manifest=_manifest("characters", PackageTypeV2.CHARACTER_PACK),
        character_profiles=[{"character_id": "c1", "private_notes": "kept authoring-only"}],
    )
    assert validate_character_pack(character).ok
    assert "private_notes" not in character.safe_summary()["public_preview"]

    prompt = PromptProfilePack(manifest=_manifest("prompts", PackageTypeV2.PROMPT_PROFILE_PACK), prompt_profiles=[{"prompt_profile_id": "p1"}])
    assert validate_prompt_profile_pack(prompt).ok
    forbidden_prompt = PromptProfilePack(manifest=_manifest("bad_prompts", PackageTypeV2.PROMPT_PROFILE_PACK), prompt_profiles=[{"prompt_profile_id": "p1", "can_access_hidden_facts": True}])
    assert not validate_prompt_profile_pack(forbidden_prompt).ok

    provider = ProviderProfilePack(manifest=_manifest("providers", PackageTypeV2.PROVIDER_PROFILE_PACK), provider_profiles=[{"provider_profile_id": "p", "api_key_env": "OPENAI_API_KEY"}])
    assert validate_provider_profile_pack(provider).ok
    with_key = ProviderProfilePack(manifest=_manifest("bad_providers", PackageTypeV2.PROVIDER_PROFILE_PACK), provider_profiles=[{"provider_profile_id": "p", "api_key": "sk-real-not-allowed"}])
    assert not validate_provider_profile_pack(with_key).ok


def test_style_and_rp_mods_do_not_expand_facts_or_knowledge() -> None:
    style = NarrativeStyleMod(
        manifest=_manifest("style", PackageTypeV2.NARRATIVE_STYLE_MOD),
        style_id="quiet",
        name="Quiet",
        target_modes=["novel"],
        tone="quiet",
    )
    assert validate_narrative_style_mod(style).ok
    assert style.to_prompt_profile_preset()["can_modify_state"] is False
    forbidden = style.model_copy(update={"forbidden_behaviors": ["access_hidden_facts"]})
    assert not validate_narrative_style_mod(forbidden).ok

    rp = RPProfileMod(
        manifest=_manifest("rp", PackageTypeV2.RP_PROFILE_MOD),
        patch_voice_profile=[RPProfilePatch(target_profile_id="voice1", path="voice.catchphrases", operation="set", value=["hm"])],
    )
    assert validate_rp_profile_mod(rp, existing_profile_ids={"voice1"}).ok
    bad = RPProfileMod(
        manifest=_manifest("bad_rp", PackageTypeV2.RP_PROFILE_MOD),
        patch_rp_profile=[RPProfilePatch(target_profile_id="rp1", path="world_npc.knowledge.secret", operation="set", value=True)],
    )
    assert not validate_rp_profile_mod(bad, existing_profile_ids={"rp1"}).ok


def _action_definition() -> ModActionDefinition:
    return ModActionDefinition(
        id="mod.pray",
        label="Pray",
        aliases=["pray"],
        category="general",
        outcomes={
            SuccessLevel.SUCCESS: DeclarativeOutcome(
                success_level=SuccessLevel.SUCCESS,
                reason="Prayer resolved.",
                state_delta_templates=[
                    DeclarativeStateDeltaTemplate(operation="set", path="flags.prayed", value=True)
                ],
            ),
            SuccessLevel.FAILURE: DeclarativeOutcome(success_level=SuccessLevel.FAILURE, reason="Prayer failed."),
        },
        event_type="mod.pray",
    )


def test_action_mod_registry_and_test_harness() -> None:
    action_mod = ActionMod(manifest=_manifest("action_pack", PackageTypeV2.ACTION_MOD, permissions=ModulePermissionSet(action_permissions={"add_declarative_action": True})), actions=[_action_definition()])
    registry = ActionRegistry(include_core=False)
    registry.register_mod_action(action_mod.actions[0], package_id=action_mod.manifest.package_id)
    assert registry.list_mod_actions()[0].id == "mod.pray"
    assert ModActionEvaluator().validate_definition(action_mod.actions[0]).ok
    with pytest.raises(ValueError):
        registry.register_mod_action(action_mod.actions[0].model_copy(update={"id": "mod.kneel"}), package_id="other")

    state = GameState(world_id="test", locations={"shrine": LocationState(id="shrine", name="Shrine")}, player={"location_id": "shrine"})
    test_case = ActionModTestCase(
        test_id="success",
        action_id="mod.pray",
        input_intent={"raw_text": "pray"},
        initial_state_fixture=state.model_dump(mode="json"),
        expected_result_type=SuccessLevel.SUCCESS,
        expected_state_deltas=[{"operation": "set", "path": "flags.prayed", "value": True}],
        expected_event_tags=["mod.pray"],
    )
    report = ActionModTestHarness(action_mod).run_all_for_mod([test_case])
    assert report.ok


def test_rule_module_contract_blocks_runtime_permissions() -> None:
    manifest = RuleModuleManifest(
        module_id="magic",
        name="Magic",
        version="1.0",
        permissions={"can_add_actions": True, "can_execute_code": False},
        required_state_schema_extensions=[{"path": "magic"}],
    )
    assert manifest.safe_summary()["experimental"] is True
    with pytest.raises(ValueError):
        RuleModuleManifest(module_id="bad", name="Bad", version="1.0", permissions={"can_execute_code": True})


def _write_package(root: Path, package_id: str, package_type: PackageTypeV2, **manifest_updates: object) -> Path:
    package_dir = root / "modules" / package_id
    package_dir.mkdir(parents=True)
    manifest = _manifest(package_id, package_type, **manifest_updates)
    (package_dir / "package_manifest_v2.json").write_text(manifest.model_dump_json(), encoding="utf-8")
    return package_dir


def test_module_browser_compatibility_certification_quality_and_audit(tmp_path: Path) -> None:
    _write_package(tmp_path, "safe_content", PackageTypeV2.SCRIPT_PACK)
    _write_package(tmp_path, "style_mod", PackageTypeV2.NARRATIVE_STYLE_MOD)
    _write_package(tmp_path, "needs_dep", PackageTypeV2.SCRIPT_PACK, dependencies=[{"package_id": "missing"}])
    unsafe = _write_package(tmp_path, "unsafe", PackageTypeV2.SCRIPT_PACK)
    (unsafe / "run.exe").write_text("binary", encoding="utf-8")

    browser = ModuleBrowserService(tmp_path)
    modules = browser.list_modules()
    assert {module.package_id for module in modules} >= {"safe_content", "style_mod", "unsafe"}
    assert browser.get_module("unsafe").summary.validation_status == "invalid"
    assert browser.permissions("safe_content").risk_level == "low"

    matrix = ModCompatibilityService(browser).build_matrix(["safe_content", "needs_dep"])
    assert not matrix.ok
    assert any("missing dependency" in " ".join(entry.errors) for entry in matrix.entries)

    assert CertificationService(browser).certify_package("safe_content").level == "safe_content"
    assert CertificationService(browser).certify_package("style_mod").level == "safe_style"
    assert run_mod_quality_gate(tmp_path, "safe_content").ok
    assert not run_mod_quality_gate(tmp_path, "unsafe").ok

    audit = ModAuditRepository(tmp_path, "project").append_action(package_id="safe_content", action_type="validate", result=ModAuditResult.SUCCESS, safe_summary="validated")
    assert ModAuditRepository(tmp_path, "project").get(audit.audit_id).safe_summary == "validated"


def _zip_package(manifest: PackageManifestV2, files: dict[str, bytes] | None = None) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("package_manifest_v2.json", manifest.model_dump_json())
        for path, data in (files or {}).items():
            archive.writestr(path, data)
    return stream.getvalue()


def test_mod_import_export_hardening(tmp_path: Path) -> None:
    service = ModImportExportService(tmp_path)
    manifest = _manifest("import_me", PackageTypeV2.SCRIPT_PACK)
    package = _zip_package(manifest, {"drafts/readme.txt": b"ok"})
    assert service.import_dry_run(package).ok
    with pytest.raises(ValueError):
        service.import_apply(package, confirm=False)
    applied = service.import_apply(package, confirm=True)
    assert applied.ok

    duplicate = service.import_dry_run(package)
    assert not duplicate.ok

    zip_slip = io.BytesIO()
    with zipfile.ZipFile(zip_slip, "w") as archive:
        archive.writestr("../evil.txt", b"bad")
    assert not service.import_dry_run(zip_slip.getvalue()).ok

    secret_manifest = _manifest("secret_pack", PackageTypeV2.SCRIPT_PACK, included_files=[PackageFileEntry(path="secret.txt")])
    secret_package = _zip_package(secret_manifest, {"secret.txt": b"sk-real-not-allowed-12345678901234567890"})
    assert not service.import_dry_run(secret_package).ok
