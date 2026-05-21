import subprocess
from pathlib import Path
from typing import Sequence

from app.tools import release_checklist
from app.tools.release_checklist import (
    ReleaseChecklistConfig,
    ReleaseChecklistStatus,
    run_release_checklist,
)
from app.tools.v2_release_candidate_checklist import run_rc_checklist


def _write_release_tree(root: Path) -> None:
    (root / "docs").mkdir()
    (root / "frontend").mkdir()
    (root / ".env.example").write_text('LLM_API_KEY=""\n', encoding="utf-8")
    (root / "README.md").write_text(
        "v1.9 Release Candidate Hardening release checklist v2.0 RC checklist\n",
        encoding="utf-8",
    )
    for doc in release_checklist.REQUIRED_V19_DOCS:
        path = root / doc
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# doc\nNo high-risk blockers.\n", encoding="utf-8")
    (root / "docs" / "V2_0_COMPATIBILITY_CHECKLIST.md").write_text("# compatibility\n", encoding="utf-8")
    for doc in (
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
    ):
        (root / "docs" / doc).write_text("# contract\n", encoding="utf-8")


def _runner(command: Sequence[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
    _ = cwd
    if list(command[:2]) == ["git", "ls-files"]:
        return subprocess.CompletedProcess(list(command), 0, stdout="README.md\ndocs/V1_9_ROADMAP.md\n", stderr="")
    if list(command[:3]) == ["git", "status", "--short"]:
        return subprocess.CompletedProcess(list(command), 0, stdout="", stderr="")
    return subprocess.CompletedProcess(list(command), 0, stdout="", stderr="")


def test_release_checklist_passes_with_required_docs(monkeypatch, tmp_path: Path) -> None:
    _write_release_tree(tmp_path)

    monkeypatch.setattr(
        release_checklist,
        "run_quality_gate",
        lambda *args, **kwargs: type(
            "Gate",
            (),
            {"passed": True, "health_score": 100, "report_links": [], "blockers": [], "errors": [], "warnings": []},
        )(),
    )

    result = run_release_checklist(root=tmp_path, command_runner=_runner)

    assert result.passed is True
    assert not result.blockers
    assert next(item for item in result.items if item.name == "required_v19_docs").status == ReleaseChecklistStatus.PASS


def test_release_checklist_missing_doc_fails(tmp_path: Path) -> None:
    _write_release_tree(tmp_path)
    (tmp_path / "docs" / "V1_9_SECURITY_AUDIT.md").unlink()

    result = run_release_checklist(
        root=tmp_path,
        command_runner=_runner,
        config=ReleaseChecklistConfig(run_quality_gate=False),
    )

    docs = next(item for item in result.items if item.name == "required_v19_docs")
    assert result.passed is False
    assert docs.status == ReleaseChecklistStatus.BLOCKER
    assert "docs/V1_9_SECURITY_AUDIT.md" in docs.safe_details["missing"]


def test_release_checklist_real_secret_fails_but_fake_secret_passes(tmp_path: Path) -> None:
    _write_release_tree(tmp_path)
    (tmp_path / "fake.txt").write_text("sk-test-fake-not-real-1234567890\n", encoding="utf-8")
    fake = run_release_checklist(root=tmp_path, command_runner=_runner, config=ReleaseChecklistConfig(run_quality_gate=False))
    assert next(item for item in fake.items if item.name == "secret_scan").status == ReleaseChecklistStatus.PASS

    real_looking = "sk-" + "ABCDEFGHIJKLMNOPQRSTUVWX1234567890"
    (tmp_path / "real.txt").write_text(f"{real_looking}\n", encoding="utf-8")
    real = run_release_checklist(root=tmp_path, command_runner=_runner, config=ReleaseChecklistConfig(run_quality_gate=False))
    assert next(item for item in real.items if item.name == "secret_scan").status == ReleaseChecklistStatus.BLOCKER


def test_release_checklist_tracked_artifact_fails(tmp_path: Path) -> None:
    _write_release_tree(tmp_path)

    def runner(command: Sequence[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
        _ = cwd
        if list(command[:2]) == ["git", "ls-files"]:
            return subprocess.CompletedProcess(list(command), 0, stdout="frontend/dist/app.js\n", stderr="")
        if list(command[:3]) == ["git", "status", "--short"]:
            return subprocess.CompletedProcess(list(command), 0, stdout="", stderr="")
        return subprocess.CompletedProcess(list(command), 0, stdout="", stderr="")

    result = run_release_checklist(root=tmp_path, command_runner=runner, config=ReleaseChecklistConfig(run_quality_gate=False))

    tracked = next(item for item in result.items if item.name == "tracked_forbidden_files")
    assert result.passed is False
    assert tracked.status == ReleaseChecklistStatus.BLOCKER


def test_release_checklist_cli_json(monkeypatch, tmp_path: Path, capsys) -> None:
    _write_release_tree(tmp_path)
    monkeypatch.setattr(release_checklist, "_run_command", _runner)
    monkeypatch.setattr(
        release_checklist,
        "run_quality_gate",
        lambda *args, **kwargs: type(
            "Gate",
            (),
            {"passed": True, "health_score": 100, "report_links": [], "blockers": [], "errors": [], "warnings": []},
        )(),
    )

    exit_code = release_checklist.main(["--root", str(tmp_path), "--json"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert '"version": "v1.9"' in out


def test_v2_release_candidate_checklist_passes_and_fails(tmp_path: Path) -> None:
    _write_release_tree(tmp_path)
    result = run_rc_checklist(tmp_path / "docs")
    assert result.passed is True

    (tmp_path / "docs" / "V2_0_RELEASE_CANDIDATE_CHECKLIST.md").unlink()
    missing = run_rc_checklist(tmp_path / "docs")
    assert missing.passed is False
    assert "Missing RC doc: V2_0_RELEASE_CANDIDATE_CHECKLIST.md" in missing.blockers
