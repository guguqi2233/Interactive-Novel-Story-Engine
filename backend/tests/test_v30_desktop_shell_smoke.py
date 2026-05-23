from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_startup_scripts_exist_and_have_safe_preflight_contract() -> None:
    ps1 = REPO_ROOT / "scripts" / "start_local_studio.ps1"
    sh = REPO_ROOT / "scripts" / "start_local_studio.sh"

    assert ps1.exists()
    assert sh.exists()
    for text in (_read(ps1), _read(sh)):
        assert "Preflight" in text or "preflight" in text
        assert "VITE_API_BASE_URL" in text
        assert "LLM_API_KEY is not read" in text
        assert "GameState" in text
        assert "no cloud sync" in text.lower()
        assert "no online marketplace" in text.lower()
        assert "sk-" not in text


def test_shell_script_syntax_when_bash_is_available() -> None:
    bash = shutil.which("bash")
    if bash is None:
        return
    result = subprocess.run([bash, "-n", str(REPO_ROOT / "scripts" / "start_local_studio.sh")], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_backend_health_endpoints_work_in_test_mode_without_secrets() -> None:
    client = TestClient(app)
    health = client.get("/health")
    studio_health = client.get("/studio/health")
    local_health = client.get("/local-studio/health")

    assert health.status_code == 200
    assert studio_health.status_code == 200
    assert local_health.status_code == 200
    combined = health.text + studio_health.text + local_health.text
    assert "sk-" not in combined
    assert "OPENAI_API_KEY" not in combined
    assert "Authorization" not in combined
    assert "raw_state_deltas" not in combined


def test_desktop_packaging_docs_exclude_sensitive_artifacts_and_online_requirements() -> None:
    doc = _read(REPO_ROOT / "docs" / "DESKTOP_PACKAGING.md")

    for token in [
        ".env",
        "API keys",
        "logs",
        "caches",
        "database",
        "node_modules",
        "frontend/dist",
        "desktop-dist",
        "desktop_build",
        "backups",
        "crash-reports",
        "No desktop workflow calls a real LLM provider",
        "cloud sync",
        "account",
        "marketplace",
    ]:
        assert token in doc


def test_gitignore_excludes_desktop_runtime_and_packaging_outputs() -> None:
    gitignore = _read(REPO_ROOT / ".gitignore")
    for token in [
        ".env",
        "*.db",
        "*.sqlite",
        "logs/",
        "cache/",
        "node_modules/",
        "frontend/dist/",
        "desktop-dist/",
        "desktop_build/",
        "release/",
        "backups/",
        "crash-reports/",
    ]:
        assert token in gitignore


def test_frontend_package_has_no_large_e2e_dependency() -> None:
    package = json.loads(_read(REPO_ROOT / "frontend" / "package.json"))
    deps = set(package.get("dependencies", {})) | set(package.get("devDependencies", {}))
    assert deps.isdisjoint({"playwright", "cypress", "selenium-webdriver", "electron", "@tauri-apps/api"})
