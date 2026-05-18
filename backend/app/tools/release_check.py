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


ReleaseCommandRunner = Callable[[Sequence[str], Path | None], subprocess.CompletedProcess[str]]


class ReleaseCheckStatus(str):
    PASS = "pass"
    WARNING = "warning"
    BLOCKER = "blocker"
    SKIPPED = "skipped"


class ReleaseCheckItem(BaseModel):
    name: str
    status: str
    message: str
    safe_details: dict[str, Any] = Field(default_factory=dict)


class ReleaseCheckReport(BaseModel):
    version: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    local_only: bool = True
    passed: bool
    items: list[ReleaseCheckItem]
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)

    def model_dump_safe(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


REQUIRED_DOCS = [
    "docs/SPEC.md",
    "docs/WORLD_ENGINE.md",
    "docs/LLM_PROTOCOL.md",
    "docs/CONTENT_PACKS.md",
    "docs/DESKTOP_PACKAGING.md",
    "README.md",
    "docs/UPGRADE_GUIDE_V0_TO_V1.md",
    "docs/END_TO_END_LOCAL_WORKFLOW.md",
    "docs/V1_0_ROADMAP.md",
    "docs/V1_0_ACCEPTANCE_REPORT.md",
    "docs/V1_0_RELEASE_NOTES.md",
    "docs/V1_0_RELEASE_CRITERIA.md",
]

REQUIRED_ENV_KEYS = [
    "DATABASE_URL",
    "LLM_PROVIDER",
    "LLM_API_KEY",
    "LOCAL_LLM_BASE_URL",
    "LOCAL_LLM_MODEL",
    "ENABLE_AUTHORING_API",
    "ENABLE_DEBUG_API",
    "ENABLE_PERF_LOGGING",
    "ENABLE_EVAL_API",
    "ENABLE_PLAYTEST_API",
    "VITE_API_BASE_URL",
]

PROHIBITED_TRACKED_PATTERNS = [
    re.compile(r"(^|/)\.env($|[./])", re.IGNORECASE),
    re.compile(r"\.(db|sqlite|sqlite3)$", re.IGNORECASE),
    re.compile(r"(^|/)(logs?|cache|caches|__pycache__|node_modules)(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)frontend/dist(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)(dist|build|out|target/release|src-tauri/target)(/|$)", re.IGNORECASE),
]

EXPECTED_DIRTY_PREFIXES = (
    "backend/app/",
    "backend/tests/",
    "docs/",
    "worlds/",
    "frontend/src/",
    "frontend/package",
    "scripts/",
    "templates/",
    ".env.example",
    ".gitignore",
    "README.md",
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
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local v1.0 release checklist.")
    parser.add_argument("--version", default="v1.0", help="Release version, for example v1.0.")
    parser.add_argument("--world", default="mist_valley", help="World id for quality gate.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--skip-pytest", action="store_true", help="Skip pytest and report it as skipped.")
    parser.add_argument("--skip-frontend-build", action="store_true", help="Skip frontend build and report it as skipped.")
    parser.add_argument("--skip-quality-gate", action="store_true", help="Skip quality gate and report it as skipped.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    report = run_release_check(
        version=args.version,
        root=Path(args.root),
        world_id=args.world,
        run_pytest=not args.skip_pytest,
        run_frontend_build=not args.skip_frontend_build,
        run_quality=not args.skip_quality_gate,
    )
    if args.json:
        print(json.dumps(report.model_dump_safe(), ensure_ascii=False, indent=2))
    else:
        print(f"Release check {report.version}: {'PASS' if report.passed else 'FAIL'}")
        print(f"Blockers: {len(report.blockers)}")
        print(f"Warnings: {len(report.warnings)}")
        for item in report.items:
            print(f"- [{item.status}] {item.name}: {item.message}")
    return 0 if report.passed else 1


def run_release_check(
    *,
    version: str = "v1.0",
    root: Path | str = Path("."),
    world_id: str = "mist_valley",
    run_pytest: bool = True,
    run_frontend_build: bool = True,
    run_quality: bool = True,
    command_runner: ReleaseCommandRunner | None = None,
) -> ReleaseCheckReport:
    repo_root = Path(root).resolve()
    runner = command_runner or _run_command
    items: list[ReleaseCheckItem] = []

    if run_pytest:
        items.append(_command_check("python_pytest", ["python", "-m", "pytest"], repo_root, runner))
    else:
        items.append(_item("python_pytest", ReleaseCheckStatus.SKIPPED, "pytest was skipped by CLI option."))

    if run_frontend_build:
        items.append(_command_check("frontend_build", ["npm.cmd", "run", "build"], repo_root / "frontend", runner))
    else:
        items.append(_item("frontend_build", ReleaseCheckStatus.SKIPPED, "frontend build was skipped by CLI option."))

    if run_quality:
        items.append(_quality_gate_check(world_id, repo_root))
    else:
        items.append(_item("quality_gate_standard", ReleaseCheckStatus.SKIPPED, "quality gate was skipped by CLI option."))

    items.extend(
        [
            _required_docs_check(repo_root),
            _env_example_check(repo_root),
            _readme_check(repo_root),
            _tracked_forbidden_files_check(repo_root, runner),
            _secret_scan_check(repo_root),
            _git_status_check(repo_root, runner),
            _audit_blocker_check(repo_root),
            _tag_exists_check(version, repo_root, runner),
        ]
    )

    blockers = [item.message for item in items if item.status == ReleaseCheckStatus.BLOCKER]
    warnings = [item.message for item in items if item.status == ReleaseCheckStatus.WARNING]
    return ReleaseCheckReport(
        version=version,
        passed=not blockers,
        items=items,
        blockers=blockers,
        warnings=warnings,
        summary={
            "total_checks": len(items),
            "blockers": len(blockers),
            "warnings": len(warnings),
            "skipped": sum(1 for item in items if item.status == ReleaseCheckStatus.SKIPPED),
            "local_only": True,
            "auto_commit": False,
            "auto_tag": False,
        },
    )


def _command_check(
    name: str,
    command: list[str],
    cwd: Path,
    runner: ReleaseCommandRunner,
) -> ReleaseCheckItem:
    if not cwd.exists():
        return _item(name, ReleaseCheckStatus.BLOCKER, f"Working directory does not exist: {_safe_path(cwd)}")
    try:
        completed = runner(command, cwd)
    except FileNotFoundError as exc:
        return _item(name, ReleaseCheckStatus.BLOCKER, f"Command not found: {command[0]}", {"error": str(exc)})
    except Exception as exc:  # pragma: no cover - defensive report shaping
        return _item(name, ReleaseCheckStatus.BLOCKER, f"Command failed before completion: {command[0]}", {"error": str(exc)})
    if completed.returncode == 0:
        return _item(name, ReleaseCheckStatus.PASS, "Command passed.")
    return _item(
        name,
        ReleaseCheckStatus.BLOCKER,
        "Command failed.",
        {"command": " ".join(command), "returncode": completed.returncode, "stderr_tail": _safe_tail(completed.stderr)},
    )


def _quality_gate_check(world_id: str, repo_root: Path) -> ReleaseCheckItem:
    try:
        result = run_quality_gate(
            world_id,
            QualityGateConfig(profile=QualityGateProfile.STANDARD),
            worlds_root=str(repo_root / "worlds"),
            mods_root=str(repo_root / "mods"),
        )
    except Exception as exc:
        return _item("quality_gate_standard", ReleaseCheckStatus.BLOCKER, "Quality gate failed to run.", {"error": str(exc)})
    if result.passed:
        return _item(
            "quality_gate_standard",
            ReleaseCheckStatus.PASS,
            "Quality gate standard profile passed.",
            {"health_score": result.health_score, "reports": len(result.report_links)},
        )
    return _item(
        "quality_gate_standard",
        ReleaseCheckStatus.BLOCKER,
        "Quality gate standard profile failed.",
        {
            "blockers": len(result.blockers),
            "errors": len(result.errors),
            "warnings": len(result.warnings),
            "health_score": result.health_score,
        },
    )


def _required_docs_check(repo_root: Path) -> ReleaseCheckItem:
    missing = [path for path in REQUIRED_DOCS if not (repo_root / path).exists()]
    if missing:
        return _item("required_docs", ReleaseCheckStatus.BLOCKER, "Required v1.0 documents are missing.", {"missing": missing})
    return _item("required_docs", ReleaseCheckStatus.PASS, "Required v1.0 documents exist.")


def _env_example_check(repo_root: Path) -> ReleaseCheckItem:
    env_example = repo_root / ".env.example"
    if not env_example.exists():
        return _item("env_example", ReleaseCheckStatus.BLOCKER, ".env.example is missing.")
    content = env_example.read_text(encoding="utf-8", errors="ignore")
    missing = [key for key in REQUIRED_ENV_KEYS if key not in content]
    if missing:
        return _item("env_example", ReleaseCheckStatus.BLOCKER, ".env.example is missing required v1.0 config keys.", {"missing": missing})
    return _item("env_example", ReleaseCheckStatus.PASS, ".env.example contains required v1.0 config keys.")


def _readme_check(repo_root: Path) -> ReleaseCheckItem:
    readme = repo_root / "README.md"
    if not readme.exists():
        return _item("readme_v1", ReleaseCheckStatus.BLOCKER, "README.md is missing.")
    text = readme.read_text(encoding="utf-8", errors="ignore").lower()
    required_terms = ["v1.0", "quality gate", "local", "llm"]
    missing = [term for term in required_terms if term not in text]
    if missing:
        return _item("readme_v1", ReleaseCheckStatus.BLOCKER, "README.md is missing required v1.0 release terms.", {"missing": missing})
    return _item("readme_v1", ReleaseCheckStatus.PASS, "README.md contains v1.0 release guidance.")


def _tracked_forbidden_files_check(repo_root: Path, runner: ReleaseCommandRunner) -> ReleaseCheckItem:
    tracked = _git_lines(["git", "ls-files"], repo_root, runner)
    if tracked is None:
        return _item("tracked_forbidden_files", ReleaseCheckStatus.WARNING, "Could not inspect git tracked files.")
    forbidden = [path for path in tracked if _is_forbidden_tracked_path(path)]
    if forbidden:
        return _item("tracked_forbidden_files", ReleaseCheckStatus.BLOCKER, "Forbidden local/generated files are tracked.", {"paths": forbidden})
    return _item("tracked_forbidden_files", ReleaseCheckStatus.PASS, "No forbidden local/generated files are tracked.")


def _secret_scan_check(repo_root: Path) -> ReleaseCheckItem:
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
        return _item("secret_scan", ReleaseCheckStatus.BLOCKER, "Potential real sk-... secret pattern found.", {"locations": findings})
    return _item("secret_scan", ReleaseCheckStatus.PASS, "No real-looking sk-... API keys found.")


def _git_status_check(repo_root: Path, runner: ReleaseCommandRunner) -> ReleaseCheckItem:
    status_lines = _git_lines(["git", "status", "--short"], repo_root, runner)
    if status_lines is None:
        return _item("git_status", ReleaseCheckStatus.WARNING, "Could not inspect git status.")
    if not status_lines:
        return _item("git_status", ReleaseCheckStatus.PASS, "Git status is clean.")
    unexpected = [line for line in status_lines if not _is_expected_dirty_status(line)]
    if unexpected:
        return _item("git_status", ReleaseCheckStatus.BLOCKER, "Git status contains unexpected files.", {"unexpected": unexpected})
    return _item("git_status", ReleaseCheckStatus.WARNING, "Git status is not clean but only contains expected release files.", {"files": status_lines})


def _audit_blocker_check(repo_root: Path) -> ReleaseCheckItem:
    audit_paths = sorted((repo_root / "docs").glob("*AUDIT*.md")) if (repo_root / "docs").exists() else []
    risky: list[str] = []
    for path in audit_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            if ("high-risk" in lowered or "高风险" in line) and ("blocker" in lowered or "阻塞" in line):
                if any(marker in lowered for marker in ("no ", "none", "not found", "未发现", "无高风险", "不阻塞")):
                    continue
                risky.append(f"{_safe_relpath(path, repo_root)}:{line_number}")
    if risky:
        return _item("audit_blockers", ReleaseCheckStatus.BLOCKER, "Audit docs mention high-risk blockers.", {"locations": risky})
    if not audit_paths:
        return _item("audit_blockers", ReleaseCheckStatus.WARNING, "No audit docs found to scan.")
    return _item("audit_blockers", ReleaseCheckStatus.PASS, "No high-risk blockers found in audit docs.")


def _tag_exists_check(version: str, repo_root: Path, runner: ReleaseCommandRunner) -> ReleaseCheckItem:
    completed = runner(["git", "tag", "--list", version], repo_root)
    if completed.returncode != 0:
        return _item("git_tag", ReleaseCheckStatus.WARNING, "Could not inspect git tags.")
    if completed.stdout.strip():
        return _item("git_tag", ReleaseCheckStatus.BLOCKER, f"Tag {version} already exists.")
    return _item("git_tag", ReleaseCheckStatus.PASS, f"Tag {version} does not exist yet.")


def _git_lines(command: list[str], repo_root: Path, runner: ReleaseCommandRunner) -> list[str] | None:
    try:
        completed = runner(command, repo_root)
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _is_forbidden_tracked_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
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
    return subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )


def _item(name: str, status: str, message: str, safe_details: dict[str, Any] | None = None) -> ReleaseCheckItem:
    return ReleaseCheckItem(name=name, status=status, message=message, safe_details=safe_details or {})


def _safe_tail(value: str | None, limit: int = 600) -> str:
    if not value:
        return ""
    return value[-limit:].replace("sk-", "sk-[redacted]-")


def _safe_path(path: Path) -> str:
    return path.name if path.is_absolute() else str(path)


def _safe_relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


if __name__ == "__main__":
    raise SystemExit(main())
