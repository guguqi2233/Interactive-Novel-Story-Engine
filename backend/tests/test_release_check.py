import subprocess
from pathlib import Path
from typing import Sequence

from app.tools import release_check
from app.tools.release_check import ReleaseCheckStatus, run_release_check


def _write_minimal_release_tree(root: Path) -> None:
    docs = root / "docs"
    docs.mkdir()
    (root / "frontend").mkdir()
    for doc in release_check.REQUIRED_DOCS:
        path = root / doc
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.name}\nLocal v1.0 quality gate LLM notes.\n", encoding="utf-8")
    (root / "README.md").write_text("v1.0 local quality gate LLM release notes\n", encoding="utf-8")
    (root / ".env.example").write_text(
        "\n".join(f'{key}=""' for key in release_check.REQUIRED_ENV_KEYS),
        encoding="utf-8",
    )
    (docs / "V1_0_SECURITY_AUDIT.md").write_text("High-risk blockers: none found.\n", encoding="utf-8")


def _clean_runner(command: Sequence[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
    _ = cwd
    if list(command[:2]) == ["git", "ls-files"]:
        stdout = "README.md\ndocs/SPEC.md\n"
    elif list(command[:3]) == ["git", "status", "--short"]:
        stdout = ""
    elif list(command[:3]) == ["git", "tag", "--list"]:
        stdout = ""
    else:
        stdout = ""
    return subprocess.CompletedProcess(list(command), 0, stdout=stdout, stderr="")


def test_release_check_clean_project_passes(monkeypatch, tmp_path: Path) -> None:
    _write_minimal_release_tree(tmp_path)

    def fake_quality_gate(*args, **kwargs):
        _ = (args, kwargs)
        return type(
            "FakeQualityGate",
            (),
            {
                "passed": True,
                "health_score": 100,
                "report_links": [object()],
                "blockers": [],
                "errors": [],
                "warnings": [],
            },
        )()

    monkeypatch.setattr(release_check, "run_quality_gate", fake_quality_gate)

    report = run_release_check(root=tmp_path, command_runner=_clean_runner)

    assert report.passed is True
    assert not report.blockers
    assert any(item.name == "quality_gate_standard" and item.status == ReleaseCheckStatus.PASS for item in report.items)


def test_release_check_missing_doc_is_blocker(tmp_path: Path) -> None:
    _write_minimal_release_tree(tmp_path)
    (tmp_path / "docs" / "V1_0_RELEASE_NOTES.md").unlink()

    report = run_release_check(
        root=tmp_path,
        run_pytest=False,
        run_frontend_build=False,
        run_quality=False,
        command_runner=_clean_runner,
    )

    required_docs = next(item for item in report.items if item.name == "required_docs")
    assert report.passed is False
    assert required_docs.status == ReleaseCheckStatus.BLOCKER
    assert "docs/V1_0_RELEASE_NOTES.md" in required_docs.safe_details["missing"]


def test_release_check_fake_key_is_allowed_but_real_key_is_blocker(tmp_path: Path) -> None:
    _write_minimal_release_tree(tmp_path)
    (tmp_path / "fake_key.txt").write_text("sk-test-fake-not-real-1234567890\n", encoding="utf-8")
    fake_only = run_release_check(
        root=tmp_path,
        run_pytest=False,
        run_frontend_build=False,
        run_quality=False,
        command_runner=_clean_runner,
    )
    assert next(item for item in fake_only.items if item.name == "secret_scan").status == ReleaseCheckStatus.PASS

    real_looking_key = "sk-" + "ABCDEFGHIJKLMNOPQRSTUVWX1234567890"
    (tmp_path / "real_key.txt").write_text(f"{real_looking_key}\n", encoding="utf-8")
    with_real = run_release_check(
        root=tmp_path,
        run_pytest=False,
        run_frontend_build=False,
        run_quality=False,
        command_runner=_clean_runner,
    )

    secret_scan = next(item for item in with_real.items if item.name == "secret_scan")
    assert with_real.passed is False
    assert secret_scan.status == ReleaseCheckStatus.BLOCKER
    assert secret_scan.safe_details["locations"] == ["real_key.txt:1"]


def test_release_check_tracked_env_is_blocker(tmp_path: Path) -> None:
    _write_minimal_release_tree(tmp_path)

    def runner(command: Sequence[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
        _ = cwd
        if list(command[:2]) == ["git", "ls-files"]:
            return subprocess.CompletedProcess(list(command), 0, stdout=".env\nREADME.md\n", stderr="")
        if list(command[:3]) == ["git", "status", "--short"]:
            return subprocess.CompletedProcess(list(command), 0, stdout="", stderr="")
        if list(command[:3]) == ["git", "tag", "--list"]:
            return subprocess.CompletedProcess(list(command), 0, stdout="", stderr="")
        return subprocess.CompletedProcess(list(command), 0, stdout="", stderr="")

    report = run_release_check(
        root=tmp_path,
        run_pytest=False,
        run_frontend_build=False,
        run_quality=False,
        command_runner=runner,
    )

    tracked = next(item for item in report.items if item.name == "tracked_forbidden_files")
    assert report.passed is False
    assert tracked.status == ReleaseCheckStatus.BLOCKER
    assert tracked.safe_details["paths"] == [".env"]


def test_release_check_cli_runs_with_skipped_expensive_checks(tmp_path: Path, monkeypatch, capsys) -> None:
    _write_minimal_release_tree(tmp_path)
    monkeypatch.setattr(release_check, "_run_command", _clean_runner)

    exit_code = release_check.main(
        [
            "--version",
            "v1.0",
            "--root",
            str(tmp_path),
            "--skip-pytest",
            "--skip-frontend-build",
            "--skip-quality-gate",
            "--json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"version": "v1.0"' in captured.out
