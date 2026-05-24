from __future__ import annotations

import subprocess
from pathlib import Path
from collections.abc import Sequence

from app.tools.v2_release_checklist import run_v2_release_checklist, ReleaseChecklistV2Config


def test_v2_release_checklist_missing_doc_fails(tmp_path: Path) -> None:
    result = run_v2_release_checklist(root=tmp_path, command_runner=_runner(""))
    assert not result.passed
    assert any("documents" in blocker for blocker in result.blockers)


def test_v2_release_checklist_json_model_stable(tmp_path: Path) -> None:
    _write_required_docs(tmp_path)
    (tmp_path / "README.md").write_text("v2.0 Modular Narrative RPG Platform Plugin API Package v2 release checklist\n", encoding="utf-8")
    result = run_v2_release_checklist(config=ReleaseChecklistV2Config(run_pytest=False, run_frontend_build=False), root=tmp_path, command_runner=_runner(""))
    payload = result.model_dump_safe()
    assert payload["version"] == "v2.0"
    assert isinstance(payload["items"], list)


def test_v2_release_checklist_allows_fake_key_only_in_test_redaction_fixture(tmp_path: Path) -> None:
    _write_required_docs(tmp_path)
    (tmp_path / "README.md").write_text("v2.0 Modular Narrative RPG Platform Plugin API Package v2 release checklist\n", encoding="utf-8")
    test_file = tmp_path / "backend" / "tests" / "test_redaction_fixture.py"
    test_file.parent.mkdir(parents=True)
    fake_key = "sk-" + "real-not-allowed-12345678901234567890"
    test_file.write_text(f'assert "{fake_key}" not in payload\n', encoding="utf-8")

    result = run_v2_release_checklist(config=ReleaseChecklistV2Config(run_pytest=False, run_frontend_build=False), root=tmp_path, command_runner=_runner(""))
    assert result.passed

    production_file = tmp_path / "backend" / "app" / "unsafe_config.py"
    production_file.parent.mkdir(parents=True)
    production_file.write_text(f'API_KEY = "{fake_key}"\n', encoding="utf-8")

    result = run_v2_release_checklist(config=ReleaseChecklistV2Config(run_pytest=False, run_frontend_build=False), root=tmp_path, command_runner=_runner(""))
    assert not result.passed
    assert any(item.id == "secret_scan" and item.status == "blocker" for item in result.items)


def test_v2_release_checklist_blocks_env_key_even_when_key_looks_fake(tmp_path: Path) -> None:
    _write_required_docs(tmp_path)
    (tmp_path / "README.md").write_text("v2.0 Modular Narrative RPG Platform Plugin API Package v2 release checklist\n", encoding="utf-8")
    fake_env_key = "sk-" + "test-env-key-must-still-block"
    (tmp_path / ".env").write_text(f"OPENAI_API_KEY={fake_env_key}\n", encoding="utf-8")

    result = run_v2_release_checklist(config=ReleaseChecklistV2Config(run_pytest=False, run_frontend_build=False), root=tmp_path, command_runner=_runner(""))

    assert not result.passed
    secret_item = next(item for item in result.items if item.id == "secret_scan")
    assert secret_item.status == "blocker"
    assert ".env" in secret_item.safe_details["files"]


def test_v2_release_checklist_allows_marked_doc_fake_key_but_blocks_unmarked_doc_key(tmp_path: Path) -> None:
    _write_required_docs(tmp_path)
    (tmp_path / "README.md").write_text("v2.0 Modular Narrative RPG Platform Plugin API Package v2 release checklist\n", encoding="utf-8")
    marked_doc_key = "sk-" + "test-doc-fixture-not-real"
    (tmp_path / "docs" / "FAKE_KEY_FIXTURE.md").write_text(f"Fake redaction fixture: {marked_doc_key}\n", encoding="utf-8")

    result = run_v2_release_checklist(config=ReleaseChecklistV2Config(run_pytest=False, run_frontend_build=False), root=tmp_path, command_runner=_runner(""))
    assert result.passed

    unmarked_doc_key = "sk-" + "abcdefghijklmnopqrstuvwx"
    (tmp_path / "docs" / "UNMARKED_KEY.md").write_text(f"Production key: {unmarked_doc_key}\n", encoding="utf-8")

    result = run_v2_release_checklist(config=ReleaseChecklistV2Config(run_pytest=False, run_frontend_build=False), root=tmp_path, command_runner=_runner(""))
    assert not result.passed
    secret_item = next(item for item in result.items if item.id == "secret_scan")
    assert "docs\\UNMARKED_KEY.md" in secret_item.safe_details["files"] or "docs/UNMARKED_KEY.md" in secret_item.safe_details["files"]


def _write_required_docs(root: Path) -> None:
    docs = root / "docs"
    docs.mkdir()
    for name in [
        "V2_0_ROADMAP.md",
        "PLATFORM_BOUNDARY.md",
        "PLUGIN_API_CONTRACT.md",
        "MODULE_API_CONTRACT.md",
        "CONTENT_PACK_SCHEMA_V2.md",
        "SAVE_MIGRATION_V2_CONTRACT.md",
        "AUTHORING_EXTENSION_API_CONTRACT.md",
        "PROVIDER_GATEWAY_V2_CONTRACT.md",
        "PACKAGE_CONTRACT_V2.md",
        "V2_0_LLM_BOUNDARY_AUDIT.md",
        "V2_0_VISIBILITY_PRIVACY_AUDIT.md",
        "V2_0_COMPATIBILITY_MIGRATION_AUDIT.md",
        "V2_0_SECURITY_AUDIT.md",
        "V2_0_PLATFORM_CONTRACT_AUDIT.md",
        "V2_0_ACCEPTANCE_REPORT.md",
        "V2_0_RELEASE_NOTES.md",
        "V2_0_RELEASE_CHECKLIST.md",
        "V2_0_COMPATIBILITY_CHECKLIST.md",
        "V2_0_RELEASE_CANDIDATE_CHECKLIST.md",
        "V1_9_ACCEPTANCE_REPORT.md",
        "V1_9_RELEASE_NOTES.md",
        "V1_9_SECURITY_AUDIT.md",
        "RELEASE_CANDIDATE_BOUNDARY.md",
        "COMPATIBILITY_BOUNDARY.md",
        "GAMESTATE_CONTRACT.md",
        "STATEDELTA_CONTRACT.md",
        "EVENTLOG_CONTRACT.md",
        "CONTENT_PACK_SCHEMA_CONTRACT.md",
        "SAVE_MIGRATION_CONTRACT.md",
        "MODULE_MANIFEST_CONTRACT.md",
        "ACTION_MOD_CONTRACT.md",
        "PROMPT_PROFILE_CONTRACT.md",
        "PROVIDER_GATEWAY_CONTRACT.md",
        "PACKAGE_CONTRACT.md",
        "AUTHORING_API_CONTRACT.md",
        "DEBUG_API_CONTRACT.md",
        "QUALITY_GATE_CONTRACT.md",
    ]:
        (docs / name).write_text("# doc\n", encoding="utf-8")


def _runner(stdout: str):
    def run(command: Sequence[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
        if command[:2] == ["git", "ls-files"]:
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    return run
