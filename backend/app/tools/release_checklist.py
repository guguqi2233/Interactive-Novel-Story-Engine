from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.quality.gate import QualityGateConfig, QualityGateProfile, run_quality_gate  # noqa: E402
from app.tools.v2_compatibility_checklist import run_checklist as run_v2_compatibility_checklist  # noqa: E402


ReleaseCommandRunner = Callable[[Sequence[str], Path | None], subprocess.CompletedProcess[str]]


class ReleaseChecklistStatus(str):
    PASS = "pass"
    WARNING = "warning"
    BLOCKER = "blocker"
    SKIPPED = "skipped"


class ReleaseChecklistConfig(BaseModel):
    version: str = "v1.9"
    world_id: str = "mist_valley"
    run_pytest: bool = False
    run_frontend_build: bool = False
    run_quality_gate: bool = True
    run_v2_compatibility: bool = True
    allow_dirty_expected_files: bool = True


class ReleaseChecklistItem(BaseModel):
    name: str
    status: str
    message: str
    safe_details: dict[str, Any] = Field(default_factory=dict)


class ReleaseChecklistResult(BaseModel):
    version: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    local_only: bool = True
    passed: bool
    items: list[ReleaseChecklistItem] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)

    def model_dump_safe(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


REQUIRED_V19_DOCS = [
    "docs/V1_9_ROADMAP.md",
    "docs/RELEASE_CANDIDATE_BOUNDARY.md",
    "docs/V1_9_LLM_BOUNDARY_AUDIT.md",
    "docs/V1_9_VISIBILITY_PRIVACY_LEAK_AUDIT.md",
    "docs/V1_9_COMPATIBILITY_MIGRATION_AUDIT.md",
    "docs/V1_9_PERFORMANCE_STABILITY_AUDIT.md",
    "docs/V1_9_SECURITY_AUDIT.md",
    "docs/V1_9_ACCEPTANCE_REPORT.md",
    "docs/V1_9_RELEASE_NOTES.md",
    "docs/V2_0_RELEASE_CANDIDATE_CHECKLIST.md",
]

PROHIBITED_TRACKED_PATTERNS = [
    re.compile(r"(^|/)\.env($|\.[^.].*)", re.IGNORECASE),
    re.compile(r"\.(db|sqlite|sqlite3|log)$", re.IGNORECASE),
    re.compile(r"(^|/)(logs?|cache|caches|__pycache__|node_modules)(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)frontend/dist(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)(desktop-dist|desktop_build|release|backups|crash-reports)(/|$)", re.IGNORECASE),
]

EXPECTED_DIRTY_PREFIXES = (
    "backend/app/",
    "backend/tests/",
    "docs/",
    "worlds/",
    "templates/",
    "frontend/src/",
    "frontend/package",
    "scripts/",
    ".env.example",
    ".gitignore",
    "README.md",
    "AGENTS.md",
)

SK_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
FAKE_SECRET_MARKERS = (
    "fake",
    "test",
    "placeholder",
    "not-real",
    "not_real",
    "example",
    "redacted",
    "local",
    "dummy",
    "real-looking",
    "live-secret",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local v1.9 release candidate checklist.")
    parser.add_argument("--version", default="v1.9")
    parser.add_argument("--world", default="mist_valley")
    parser.add_argument("--root", default=".")
    parser.add_argument("--run-pytest", action="store_true", help="Run python -m pytest as part of the checklist.")
    parser.add_argument("--run-frontend-build", action="store_true", help="Run npm.cmd run build in frontend.")
    parser.add_argument("--skip-quality-gate", action="store_true")
    parser.add_argument("--skip-v2-compatibility", action="store_true")
    parser.add_argument("--strict-clean", action="store_true", help="Fail on any dirty git status, even expected release files.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = run_release_checklist(
        config=ReleaseChecklistConfig(
            version=args.version,
            world_id=args.world,
            run_pytest=args.run_pytest,
            run_frontend_build=args.run_frontend_build,
            run_quality_gate=not args.skip_quality_gate,
            run_v2_compatibility=not args.skip_v2_compatibility,
            allow_dirty_expected_files=not args.strict_clean,
        ),
        root=Path(args.root),
    )
    if args.json:
        print(json.dumps(result.model_dump_safe(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Release checklist {result.version}: {'PASS' if result.passed else 'FAIL'}")
        print(f"Blockers: {len(result.blockers)}")
        print(f"Warnings: {len(result.warnings)}")
        for item in result.items:
            print(f"- [{item.status}] {item.name}: {item.message}")
    return 0 if result.passed else 1


def run_release_checklist(
    *,
    config: ReleaseChecklistConfig | None = None,
    root: Path | str = Path("."),
    command_runner: ReleaseCommandRunner | None = None,
) -> ReleaseChecklistResult:
    config = config or ReleaseChecklistConfig()
    repo_root = Path(root).resolve()
    runner = command_runner or _run_command
    items: list[ReleaseChecklistItem] = []

    items.append(_required_docs_check(repo_root))
    items.append(_readme_v19_check(repo_root))
    items.append(_tracked_forbidden_files_check(repo_root, runner))
    items.append(_secret_scan_check(repo_root))
    items.append(_git_status_check(repo_root, runner, allow_expected=config.allow_dirty_expected_files))
    items.append(_audit_blocker_check(repo_root))

    if config.run_quality_gate:
        items.append(_quality_gate_check(config.world_id, repo_root))
    else:
        items.append(_item("quality_gate_standard", ReleaseChecklistStatus.SKIPPED, "Quality gate skipped by CLI option."))

    if config.run_v2_compatibility:
        items.append(_v2_compatibility_check(repo_root))
    else:
        items.append(_item("v2_compatibility_checklist", ReleaseChecklistStatus.SKIPPED, "v2 compatibility checklist skipped by CLI option."))

    if config.run_pytest:
        items.append(_command_check("python_pytest", ["python", "-m", "pytest"], repo_root, runner))
    else:
        items.append(_item("python_pytest", ReleaseChecklistStatus.WARNING, "pytest was not run by this checklist invocation."))

    if config.run_frontend_build:
        items.append(_command_check("frontend_build", ["npm.cmd", "run", "build"], repo_root / "frontend", runner))
    else:
        items.append(_item("frontend_build", ReleaseChecklistStatus.WARNING, "frontend build was not run by this checklist invocation."))

    blockers = [item.message for item in items if item.status == ReleaseChecklistStatus.BLOCKER]
    warnings = [item.message for item in items if item.status == ReleaseChecklistStatus.WARNING]
    return ReleaseChecklistResult(
        version=config.version,
        passed=not blockers,
        items=items,
        blockers=blockers,
        warnings=warnings,
        summary={
            "total_checks": len(items),
            "blockers": len(blockers),
            "warnings": len(warnings),
            "skipped": sum(1 for item in items if item.status == ReleaseChecklistStatus.SKIPPED),
            "local_only": True,
            "auto_fix": False,
            "auto_commit": False,
            "auto_tag": False,
        },
    )


def _required_docs_check(repo_root: Path) -> ReleaseChecklistItem:
    missing = [path for path in REQUIRED_V19_DOCS if not (repo_root / path).exists()]
    if missing:
        return _item("required_v19_docs", ReleaseChecklistStatus.BLOCKER, "Required v1.9 release documents are missing.", {"missing": missing})
    return _item("required_v19_docs", ReleaseChecklistStatus.PASS, "Required v1.9 release documents exist.")


def _readme_v19_check(repo_root: Path) -> ReleaseChecklistItem:
    readme = repo_root / "README.md"
    if not readme.exists():
        return _item("readme_v19", ReleaseChecklistStatus.BLOCKER, "README.md is missing.")
    text = readme.read_text(encoding="utf-8", errors="ignore").lower()
    required = ["v1.9", "release candidate hardening", "release checklist", "v2.0 rc checklist"]
    missing = [term for term in required if term not in text]
    if missing:
        return _item("readme_v19", ReleaseChecklistStatus.BLOCKER, "README.md is missing v1.9 release guidance.", {"missing": missing})
    return _item("readme_v19", ReleaseChecklistStatus.PASS, "README.md contains v1.9 release guidance.")


def _quality_gate_check(world_id: str, repo_root: Path) -> ReleaseChecklistItem:
    try:
        result = run_quality_gate(
            world_id,
            QualityGateConfig(profile=QualityGateProfile.STANDARD),
            worlds_root=str(repo_root / "worlds"),
            mods_root=str(repo_root / "mods"),
        )
    except Exception as exc:
        return _item("quality_gate_standard", ReleaseChecklistStatus.BLOCKER, "Quality gate failed to run.", {"error": _safe_text(str(exc))})
    if result.passed:
        return _item(
            "quality_gate_standard",
            ReleaseChecklistStatus.PASS,
            "Quality gate standard profile passed.",
            {"health_score": result.health_score, "reports": len(result.report_links)},
        )
    return _item(
        "quality_gate_standard",
        ReleaseChecklistStatus.BLOCKER,
        "Quality gate standard profile failed.",
        {"blockers": len(result.blockers), "errors": len(result.errors), "warnings": len(result.warnings), "health_score": result.health_score},
    )


def _v2_compatibility_check(repo_root: Path) -> ReleaseChecklistItem:
    result = run_v2_compatibility_checklist(repo_root / "docs")
    if result.passed:
        return _item("v2_compatibility_checklist", ReleaseChecklistStatus.PASS, "v2 compatibility checklist passed.")
    return _item(
        "v2_compatibility_checklist",
        ReleaseChecklistStatus.BLOCKER,
        "v2 compatibility checklist failed.",
        {"blockers": result.blockers},
    )


def _tracked_forbidden_files_check(repo_root: Path, runner: ReleaseCommandRunner) -> ReleaseChecklistItem:
    tracked = _git_lines(["git", "ls-files"], repo_root, runner)
    if tracked is None:
        return _item("tracked_forbidden_files", ReleaseChecklistStatus.WARNING, "Could not inspect git tracked files.")
    forbidden = [path for path in tracked if _is_forbidden_tracked_path(path)]
    if forbidden:
        return _item("tracked_forbidden_files", ReleaseChecklistStatus.BLOCKER, "Forbidden local/generated files are tracked.", {"paths": forbidden})
    return _item("tracked_forbidden_files", ReleaseChecklistStatus.PASS, "No forbidden local/generated files are tracked.")


def _secret_scan_check(repo_root: Path) -> ReleaseChecklistItem:
    findings: list[str] = []
    for path in _iter_scannable_files(repo_root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in SK_KEY_PATTERN.finditer(line):
                if _looks_fake_secret(match.group(0), line):
                    continue
                findings.append(f"{_safe_relpath(path, repo_root)}:{line_number}")
    if findings:
        return _item("secret_scan", ReleaseChecklistStatus.BLOCKER, "Potential real sk-... secret pattern found.", {"locations": findings})
    return _item("secret_scan", ReleaseChecklistStatus.PASS, "No real-looking sk-... API keys found.")


def _git_status_check(repo_root: Path, runner: ReleaseCommandRunner, *, allow_expected: bool) -> ReleaseChecklistItem:
    status_lines = _git_lines(["git", "status", "--short"], repo_root, runner)
    if status_lines is None:
        return _item("git_status", ReleaseChecklistStatus.WARNING, "Could not inspect git status.")
    if not status_lines:
        return _item("git_status", ReleaseChecklistStatus.PASS, "Git status is clean.")
    if not allow_expected:
        return _item("git_status", ReleaseChecklistStatus.BLOCKER, "Git status is not clean.", {"files": status_lines})
    unexpected = [line for line in status_lines if not _is_expected_dirty_status(line)]
    if unexpected:
        return _item("git_status", ReleaseChecklistStatus.BLOCKER, "Git status contains unexpected files.", {"unexpected": unexpected})
    return _item("git_status", ReleaseChecklistStatus.WARNING, "Git status is not clean but only contains expected release files.", {"files": status_lines})


def _audit_blocker_check(repo_root: Path) -> ReleaseChecklistItem:
    audit_paths = [
        repo_root / "docs/V1_9_LLM_BOUNDARY_AUDIT.md",
        repo_root / "docs/V1_9_VISIBILITY_PRIVACY_LEAK_AUDIT.md",
        repo_root / "docs/V1_9_COMPATIBILITY_MIGRATION_AUDIT.md",
        repo_root / "docs/V1_9_PERFORMANCE_STABILITY_AUDIT.md",
        repo_root / "docs/V1_9_SECURITY_AUDIT.md",
    ]
    missing = [str(path.relative_to(repo_root)) for path in audit_paths if not path.exists()]
    if missing:
        return _item("audit_blockers", ReleaseChecklistStatus.BLOCKER, "Required v1.9 audit docs are missing.", {"missing": missing})
    risky: list[str] = []
    for path in audit_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lowered = text.lower()
        if "high-risk" in lowered and "blocker" in lowered and "none" not in lowered and "no high-risk" not in lowered:
            risky.append(str(path.relative_to(repo_root)))
    if risky:
        return _item("audit_blockers", ReleaseChecklistStatus.BLOCKER, "Audit docs mention high-risk blockers.", {"paths": risky})
    return _item("audit_blockers", ReleaseChecklistStatus.PASS, "No high-risk blockers found in v1.9 audit docs.")


def _command_check(name: str, command: list[str], cwd: Path, runner: ReleaseCommandRunner) -> ReleaseChecklistItem:
    if not cwd.exists():
        return _item(name, ReleaseChecklistStatus.BLOCKER, f"Working directory does not exist: {_safe_path(cwd)}")
    try:
        completed = runner(command, cwd)
    except FileNotFoundError as exc:
        return _item(name, ReleaseChecklistStatus.BLOCKER, f"Command not found: {command[0]}", {"error": str(exc)})
    if completed.returncode == 0:
        return _item(name, ReleaseChecklistStatus.PASS, "Command passed.")
    return _item(
        name,
        ReleaseChecklistStatus.BLOCKER,
        "Command failed.",
        {"command": " ".join(command), "returncode": completed.returncode, "stderr_tail": _safe_text(completed.stderr[-2000:])},
    )


def _git_lines(command: list[str], repo_root: Path, runner: ReleaseCommandRunner) -> list[str] | None:
    try:
        completed = runner(command, repo_root)
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    return [line.rstrip() for line in completed.stdout.splitlines() if line.strip()]


def _is_forbidden_tracked_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.endswith(".env.example") or normalized == ".env.example":
        return False
    return any(pattern.search(normalized) for pattern in PROHIBITED_TRACKED_PATTERNS)


def _is_expected_dirty_status(status_line: str) -> bool:
    path = status_line[3:].replace("\\", "/") if len(status_line) > 3 else status_line.replace("\\", "/")
    return any(path.startswith(prefix) or path == prefix.rstrip("/") for prefix in EXPECTED_DIRTY_PREFIXES)


def _iter_scannable_files(repo_root: Path) -> list[Path]:
    skipped_parts = {
        ".git",
        "node_modules",
        "dist",
        "build",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "data",
        "logs",
        "backups",
        "crash-reports",
    }
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = set(path.relative_to(repo_root).parts)
        if rel_parts & skipped_parts:
            continue
        if path.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip"}:
            continue
        files.append(path)
    return files


def _looks_fake_secret(token: str, line: str) -> bool:
    haystack = f"{token} {line}".lower()
    return any(marker in haystack for marker in FAKE_SECRET_MARKERS)


def _run_command(command: Sequence[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=False)


def _safe_relpath(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.name


def _safe_path(path: Path) -> str:
    return path.name if path.is_absolute() else str(path)


def _safe_text(text: str) -> str:
    return SK_KEY_PATTERN.sub("[redacted-api-key]", text)


def _item(name: str, status: str, message: str, safe_details: dict[str, Any] | None = None) -> ReleaseChecklistItem:
    return ReleaseChecklistItem(name=name, status=status, message=message, safe_details=safe_details or {})


if __name__ == "__main__":
    raise SystemExit(main())
