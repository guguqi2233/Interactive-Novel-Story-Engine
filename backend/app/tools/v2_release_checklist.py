from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.tools.v2_compatibility_checklist import run_checklist as run_v2_compatibility_checklist  # noqa: E402
from app.tools.v2_release_candidate_checklist import run_rc_checklist  # noqa: E402


CommandRunner = Callable[[Sequence[str], Path | None], subprocess.CompletedProcess[str]]


class ReleaseChecklistV2Config(BaseModel):
    version: str = "v2.0"
    phase: str = "freeze"
    run_pytest: bool = False
    run_frontend_build: bool = False
    allow_expected_dirty_files: bool = True


class ReleaseChecklistV2Item(BaseModel):
    id: str
    status: str
    message: str
    safe_details: dict[str, Any] = Field(default_factory=dict)


class ReleaseChecklistV2Result(BaseModel):
    version: str = "v2.0"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    passed: bool
    local_only: bool = True
    items: list[ReleaseChecklistV2Item] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def model_dump_safe(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


REQUIRED_V2_DOCS = [
    "docs/V2_0_ROADMAP.md",
    "docs/PLATFORM_BOUNDARY.md",
    "docs/PLUGIN_API_CONTRACT.md",
    "docs/MODULE_API_CONTRACT.md",
    "docs/CONTENT_PACK_SCHEMA_V2.md",
    "docs/SAVE_MIGRATION_V2_CONTRACT.md",
    "docs/AUTHORING_EXTENSION_API_CONTRACT.md",
    "docs/PROVIDER_GATEWAY_V2_CONTRACT.md",
    "docs/PACKAGE_CONTRACT_V2.md",
    "docs/V2_0_LLM_BOUNDARY_AUDIT.md",
    "docs/V2_0_VISIBILITY_PRIVACY_AUDIT.md",
    "docs/V2_0_COMPATIBILITY_MIGRATION_AUDIT.md",
    "docs/V2_0_SECURITY_AUDIT.md",
    "docs/V2_0_PLATFORM_CONTRACT_AUDIT.md",
    "docs/V2_0_ACCEPTANCE_REPORT.md",
    "docs/V2_0_RELEASE_NOTES.md",
    "docs/V2_0_RELEASE_CHECKLIST.md",
]

FORBIDDEN_TRACKED = re.compile(
    r"(^|/)(\.env($|\.)|.*\.(db|sqlite|sqlite3|log)$|logs?/|cache/|caches/|node_modules/|frontend/dist/|desktop-dist/|desktop_build/|backups/|crash-reports/)",
    re.IGNORECASE,
)
SK_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
FAKE_MARKERS = (
    "test",
    "fake",
    "example",
    "placeholder",
    "redacted",
    "not-real",
    "local",
    "real-looking",
    "live-secret",
)


def run_v2_release_checklist(
    *,
    config: ReleaseChecklistV2Config | None = None,
    root: Path | str = Path("."),
    command_runner: CommandRunner | None = None,
) -> ReleaseChecklistV2Result:
    config = config or ReleaseChecklistV2Config()
    repo_root = Path(root).resolve()
    runner = command_runner or _run_command
    items = [
        _docs_check(repo_root),
        _readme_check(repo_root),
        _tracked_artifacts_check(repo_root, runner),
        _secret_scan_check(repo_root),
        _v2_compatibility_check(repo_root),
        _v2_rc_check(repo_root),
    ]
    items.append(_command_check("python_pytest", ["python", "-m", "pytest"], repo_root, runner) if config.run_pytest else _warning("python_pytest", "pytest not run by this invocation."))
    items.append(_command_check("frontend_build", ["npm.cmd", "run", "build"], repo_root / "frontend", runner) if config.run_frontend_build else _warning("frontend_build", "frontend build not run by this invocation."))
    blockers = [item.message for item in items if item.status == "blocker"]
    warnings = [item.message for item in items if item.status == "warning"]
    return ReleaseChecklistV2Result(version=config.version, passed=not blockers, items=items, blockers=blockers, warnings=warnings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local v2.0 release checklist.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--version", default="v2.0")
    parser.add_argument("--run-pytest", action="store_true")
    parser.add_argument("--run-frontend-build", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = run_v2_release_checklist(
        config=ReleaseChecklistV2Config(version=args.version, run_pytest=args.run_pytest, run_frontend_build=args.run_frontend_build),
        root=Path(args.root),
    )
    if args.json:
        print(json.dumps(result.model_dump_safe(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"v2.0 release checklist: {'PASS' if result.passed else 'FAIL'}")
        for item in result.items:
            print(f"- [{item.status}] {item.id}: {item.message}")
    return 0 if result.passed else 1


def _docs_check(repo_root: Path) -> ReleaseChecklistV2Item:
    missing = [path for path in REQUIRED_V2_DOCS if not (repo_root / path).exists()]
    if missing:
        return _blocker("required_v2_docs", "Required v2.0 documents are missing.", {"missing": missing})
    return _pass("required_v2_docs", "Required v2.0 documents exist.")


def _readme_check(repo_root: Path) -> ReleaseChecklistV2Item:
    readme = repo_root / "README.md"
    text = readme.read_text(encoding="utf-8", errors="ignore").lower() if readme.exists() else ""
    required = ["v2.0", "modular narrative rpg platform", "plugin api", "package v2", "release checklist"]
    missing = [term for term in required if term not in text]
    if missing:
        return _blocker("readme_v2", "README is missing v2.0 platform guidance.", {"missing": missing})
    return _pass("readme_v2", "README contains v2.0 platform guidance.")


def _tracked_artifacts_check(repo_root: Path, runner: CommandRunner) -> ReleaseChecklistV2Item:
    result = runner(["git", "ls-files"], repo_root)
    if result.returncode != 0:
        return _blocker("tracked_artifacts", "Unable to inspect tracked files.")
    offenders = [line for line in result.stdout.splitlines() if FORBIDDEN_TRACKED.search(line) and not line.endswith(".env.example")]
    if offenders:
        return _blocker("tracked_artifacts", "Forbidden local artifacts are tracked.", {"files": offenders})
    return _pass("tracked_artifacts", "No forbidden local artifacts tracked.")


def _secret_scan_check(repo_root: Path) -> ReleaseChecklistV2Item:
    offenders: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file() or any(part in {"node_modules", ".git", "__pycache__", "dist"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel_path = path.relative_to(repo_root)
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in SK_KEY_PATTERN.findall(line):
                if _is_allowed_fake_key_fixture(rel_path, line, match):
                    continue
                offenders.append(str(path.relative_to(repo_root)))
                break
            if str(path.relative_to(repo_root)) in offenders:
                break
    if offenders:
        return _blocker("secret_scan", "Potential real API keys found.", {"files": sorted(set(offenders))})
    return _pass("secret_scan", "No real API key pattern found.")


def _is_allowed_fake_key_fixture(relative_path: Path, line: str, match: str) -> bool:
    normalized_path = relative_path.as_posix().lower()
    if normalized_path == ".env" or normalized_path.endswith("/.env"):
        return False
    lowered_key = match.lower()
    lowered_line = line.lower()
    if _is_test_fixture_path(normalized_path):
        return _has_fake_marker(lowered_key) or _has_fixture_context(lowered_line)
    if _is_documentation_path(normalized_path):
        return _has_fake_marker(lowered_key) and _has_doc_fixture_context(lowered_line)
    if normalized_path == ".env.example":
        return _has_fake_marker(lowered_key) and _has_doc_fixture_context(lowered_line)
    return False


def _is_test_fixture_path(normalized_path: str) -> bool:
    return normalized_path.startswith(("backend/tests/", "tests/", "fixtures/"))


def _is_documentation_path(normalized_path: str) -> bool:
    return normalized_path.startswith("docs/") or normalized_path in {"readme.md", "agents.md"}


def _has_fake_marker(text: str) -> bool:
    return any(marker in text for marker in FAKE_MARKERS)


def _has_fixture_context(lowered_line: str) -> bool:
    fixture_context = (
        "assert",
        "redact",
        "reject",
        "forbidden",
        "not-allowed",
        "secret_like",
        "hidden leak",
        "auth_failed",
        "raises",
        "api_key",
        "openai_api_key",
        "secret",
        "token",
        "fake",
        "fixture",
        "test",
    )
    return any(marker in lowered_line for marker in fixture_context)


def _has_doc_fixture_context(lowered_line: str) -> bool:
    doc_context = (
        "fake",
        "example",
        "placeholder",
        "redacted",
        "redaction",
        "fixture",
        "test",
        "not real",
        "not-real",
        "local",
        "forbidden",
        "blocked",
        "reject",
        "never store",
        "must not",
        "no real",
    )
    return any(marker in lowered_line for marker in doc_context)


def _v2_compatibility_check(repo_root: Path) -> ReleaseChecklistV2Item:
    result = run_v2_compatibility_checklist(repo_root / "docs")
    if result.passed:
        return _pass("v2_compatibility", "v2 compatibility checklist passed.")
    return _blocker("v2_compatibility", "v2 compatibility checklist failed.", {"blockers": result.blockers})


def _v2_rc_check(repo_root: Path) -> ReleaseChecklistV2Item:
    result = run_rc_checklist(repo_root / "docs")
    if result.passed:
        return _pass("v2_rc", "v2 release candidate checklist passed.")
    return _blocker("v2_rc", "v2 release candidate checklist failed.", {"blockers": result.blockers})


def _command_check(check_id: str, command: list[str], cwd: Path, runner: CommandRunner) -> ReleaseChecklistV2Item:
    result = runner(command, cwd)
    if result.returncode == 0:
        return _pass(check_id, "Command passed.")
    return _blocker(check_id, "Command failed.", {"returncode": result.returncode})


def _run_command(command: Sequence[str], cwd: Path | None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(command), cwd=cwd, text=True, capture_output=True, check=False)


def _pass(check_id: str, message: str, details: dict[str, Any] | None = None) -> ReleaseChecklistV2Item:
    return ReleaseChecklistV2Item(id=check_id, status="pass", message=message, safe_details=details or {})


def _warning(check_id: str, message: str, details: dict[str, Any] | None = None) -> ReleaseChecklistV2Item:
    return ReleaseChecklistV2Item(id=check_id, status="warning", message=message, safe_details=details or {})


def _blocker(check_id: str, message: str, details: dict[str, Any] | None = None) -> ReleaseChecklistV2Item:
    return ReleaseChecklistV2Item(id=check_id, status="blocker", message=message, safe_details=details or {})


if __name__ == "__main__":
    raise SystemExit(main())
