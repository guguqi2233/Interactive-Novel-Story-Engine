from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
import yaml

from app.platform.authoring_extensions import AuthoringExtensionManifest, AuthoringExtensionRegistry
from app.platform.campaigns import CampaignMetadata, CampaignService
from app.platform.character_transfer import CharacterTransferPackage, CharacterTransferService
from app.platform.content_pack_v2 import validate_content_pack_v2_manifest
from app.platform.long_campaign import LongCampaignService
from app.platform.module_api import ModuleLifecycleState, ModuleRegistry
from app.platform.package_v2 import PackageV2Exporter, PackageV2Importer
from app.platform.plugin_api import PluginManifest
from app.platform.provider_gateway_v2 import ProviderGatewayV2Config, validate_provider_gateway_v2
from app.platform.save_migration_v2 import plan_save_migration_v2
from app.platform.timeline_branching import TimelineBranch, TimelineBranchService
from app.platform.workspace_project import WorkspaceProjectManifest, WorkspaceProjectService


def test_plugin_manifest_validates_and_rejects_unsafe_permissions() -> None:
    manifest = PluginManifest(plugin_id="demo_plugin", name="Demo", version="2.0.0")
    assert manifest.permissions.execute_code is False
    with pytest.raises(ValueError):
        PluginManifest(
            plugin_id="bad_plugin",
            name="Bad",
            version="2.0.0",
            permissions={"execute_code": True},
        )


def test_package_v2_export_import_dry_run_and_security() -> None:
    exporter = PackageV2Exporter()
    package = exporter.export_files(
        package_id="demo_pkg",
        package_type="world",
        files={"payload/world.json": b'{"world_id":"demo"}'},
        schema_versions={"content_pack": "2"},
    )
    dry_run = PackageV2Importer().dry_run(package.archive_base64)
    assert dry_run.report.ok
    assert dry_run.dry_run is True
    assert dry_run.imported is False

    with pytest.raises(ValueError):
        exporter.export_files(package_id="secret_pkg", package_type="world", files={"payload/.env": b"LLM_API_KEY=sk-test-secret"})


def test_package_v2_rejects_zip_slip_executable_and_checksum_mismatch() -> None:
    manifest = {
        "package_id": "bad_pkg",
        "package_type": "world",
        "contract_version": "2",
        "included_files": ["payload/world.json"],
        "checksums": {"payload/world.json": "not-a-real-checksum"},
    }
    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as archive:
        archive.writestr("package_v2_manifest.json", json.dumps(manifest))
        archive.writestr("payload/world.json", "{}")
    report = PackageV2Importer().dry_run(base64.b64encode(buf.getvalue()).decode("ascii")).report
    assert not report.ok
    assert any("Checksum mismatch" in error for error in report.errors)

    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as archive:
        archive.writestr("../escape.txt", "bad")
    report = PackageV2Importer().dry_run(base64.b64encode(buf.getvalue()).decode("ascii")).report
    assert not report.ok

    with pytest.raises(ValueError):
        PackageV2Exporter().export_files(package_id="exe_pkg", package_type="world", files={"payload/run.exe": b"binary"})


def test_content_pack_v2_and_save_migration_v2_legacy_paths() -> None:
    legacy_report = validate_content_pack_v2_manifest({"world_id": "legacy_world", "name": "Legacy"})
    assert legacy_report.ok
    assert legacy_report.legacy_v1_compatible
    assert legacy_report.warnings

    plan = plan_save_migration_v2("1.8")
    assert plan.can_migrate
    assert plan.target_version == "2"
    assert plan.warnings


def test_authoring_extension_requires_validation_gate() -> None:
    registry = AuthoringExtensionRegistry()
    manifest = AuthoringExtensionManifest(extension_id="quest_panel", name="Quest Panel", version="2.0.0")
    assert registry.register(manifest).ok
    assert not registry.validate_save_policy("quest_panel", validation_gate_used=False).ok
    assert registry.validate_save_policy("quest_panel", validation_gate_used=True).ok


def test_provider_gateway_v2_safe_summary_has_no_secrets() -> None:
    config = ProviderGatewayV2Config(provider_id="mock", env_var_refs=["LLM_API_KEY"])
    assert validate_provider_gateway_v2(config).ok
    summary = config.safe_summary()
    assert "LLM_API_KEY" not in json.dumps(summary)
    assert "api_key" not in json.dumps(summary).lower()


def test_workspace_campaign_timeline_transfer_and_chronicle() -> None:
    workspace_report = WorkspaceProjectService(Path("workspace")).validate_project(
        WorkspaceProjectManifest(workspace_id="demo_workspace", name="Demo")
    )
    assert workspace_report.ok
    bad_workspace = WorkspaceProjectManifest(workspace_id="bad_workspace", name="Bad", worlds_dir="../outside")
    assert not WorkspaceProjectService(Path("workspace")).validate_project(bad_workspace).ok

    campaigns = CampaignService()
    campaign = campaigns.create(CampaignMetadata(campaign_id="camp", name="Campaign", world_id="world"))
    assert campaigns.select("camp").campaign_id == campaign.campaign_id

    timeline = TimelineBranchService()
    parent = timeline.create_branch(
        TimelineBranch(branch_id="main", campaign_id="camp", source_save_id="save_a", name="Main", current_save_id="save_a")
    )
    child = timeline.create_branch(
        TimelineBranch(branch_id="branch_b", campaign_id="camp", parent_branch_id=parent.branch_id, source_save_id="save_a", name="Branch", current_save_id="save_b")
    )
    assert timeline.switch(child.branch_id).branch_id == "branch_b"
    assert timeline.diff("branch_b", "main").hidden_redacted

    transfer = CharacterTransferService().export_character("hero", "world", public_identity={"name": "Hero"})
    assert "hidden" not in transfer.model_dump_json().lower()
    assert not CharacterTransferService().import_apply(transfer, "target", confirm_apply=False).ok
    assert CharacterTransferService().import_apply(transfer, "target", confirm_apply=True).applied

    chronicle = LongCampaignService().chronicle("camp", ["public victory", "hidden betrayal"])
    assert chronicle.major_events == ["public victory"]


def test_module_registry_lifecycle(tmp_path: Path) -> None:
    module_dir = tmp_path / "demo_module"
    module_dir.mkdir()
    (module_dir / "gameplay_module.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "demo_module",
                "name": "Demo Module",
                "version": "2.0.0",
                "module_type": "action_pack",
                "engine_version_min": "0.0.0",
                "provided_actions": [{"id": "pray", "action_type": "pray"}],
            }
        ),
        encoding="utf-8",
    )
    registry = ModuleRegistry(tmp_path)
    report = registry.enable("demo_module", confirm_enable=True)
    assert report.ok
    assert report.state == ModuleLifecycleState.ENABLED

