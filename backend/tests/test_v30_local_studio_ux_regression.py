from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"
APP_TSX = FRONTEND / "src" / "App.tsx"
API_TS = FRONTEND / "src" / "api.ts"
PACKAGE_JSON = FRONTEND / "package.json"
V30_CHECK = FRONTEND / "scripts" / "check-v30-local-studio-ux.mjs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_v30_frontend_check_script_and_lightweight_dependencies_exist() -> None:
    package = json.loads(_read(PACKAGE_JSON))
    assert package["scripts"]["check:v30-ux"] == "node scripts/check-v30-local-studio-ux.mjs"
    assert V30_CHECK.exists()
    deps = set(package.get("dependencies", {})) | set(package.get("devDependencies", {}))
    assert deps.isdisjoint({"@mui/material", "antd", "chakra-ui", "bootstrap", "playwright", "cypress", "electron"})


def test_v30_local_studio_entry_surfaces_exist() -> None:
    app = _read(APP_TSX)
    for token in [
        "First-Run Onboarding",
        "Local Launcher / Startup Status",
        "Project Selector",
        "Recent Projects",
        "Local Config Wizard",
        "Provider Setup Wizard",
        "Desktop Health Check",
        "One-Click Quality Gate",
        "Backup / Restore Wizard",
        "Error Recovery Wizard",
        "Local Log Viewer",
        "Diagnostics Bundle UI",
        "Offline Help Center",
        "Settings / Preferences Sections",
        "SafePathSummary",
    ]:
        assert token in app


def test_v30_local_first_and_no_onlineization_copy_exists() -> None:
    app = _read(APP_TSX)
    for token in [
        "No account needed",
        "No cloud sync",
        "No online marketplace",
        "API keys stay local",
        "Nothing is uploaded",
        "no remote",
    ]:
        assert token.lower() in app.lower()
    assert not re.search(r"<button[^>]*>\s*(Account|Cloud Sync|Online Marketplace)\s*</button>", app, re.IGNORECASE)


def test_v30_frontend_does_not_render_plaintext_secrets() -> None:
    app = _read(APP_TSX)
    api = _read(API_TS)
    assert not re.search(r"<input[^>]+name=[\"']api_key[\"']", app, flags=re.IGNORECASE)
    assert not re.search(r"api_key\s*:\s*[\"'][^\"']+", app)
    assert not re.search(r"sk-[A-Za-z0-9_-]{12,}", app + api)
    for token in ["api_key_env", "secret_ref", "No plaintext api_key field", "Secret ref"]:
        assert token in app + api


def test_v30_api_helpers_exist_for_local_studio() -> None:
    api = _read(API_TS)
    for helper in [
        "fetchLocalStudioStatus",
        "fetchLocalStudioConfigSummary",
        "fetchLocalStudioStartupChecks",
        "createBackupDryRun",
        "createLocalBackup",
        "restoreBackupDryRun",
        "fetchRecoveryIssues",
        "dryRunRecovery",
        "fetchLocalLogs",
        "previewDiagnosticsBundle",
    ]:
        assert helper in api


def test_v30_static_check_covers_ux_boundaries() -> None:
    script = _read(V30_CHECK)
    for token in [
        "Local Launcher / Startup Status",
        "Backup / Restore Wizard",
        "Error Recovery Wizard",
        "Local Log Viewer",
        "Diagnostics Bundle UI",
        "First-Run Onboarding",
        "Plaintext api_key input",
        "Account|Cloud Sync|Online Marketplace",
    ]:
        assert token in script
