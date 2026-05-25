from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND = REPO_ROOT / "frontend"
APP_TSX = FRONTEND / "src" / "App.tsx"
API_TS = FRONTEND / "src" / "api.ts"
PACKAGE_JSON = FRONTEND / "package.json"
V29_CHECK = FRONTEND / "scripts" / "check-v29-ui-safety.mjs"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_v29_frontend_build_scripts_and_dependencies_are_lightweight() -> None:
    package = json.loads(read(PACKAGE_JSON))

    assert package["scripts"]["build"] == "tsc -b && vite build"
    assert package["scripts"]["check:v29-ui"] == "node scripts/check-v29-ui-safety.mjs"

    dependencies = set(package.get("dependencies", {})) | set(package.get("devDependencies", {}))
    large_ui_dependencies = {
        "@mui/material",
        "antd",
        "chakra-ui",
        "@chakra-ui/react",
        "bootstrap",
        "semantic-ui-react",
        "blueprintjs",
        "primereact",
        "ag-grid-react",
        "echarts",
        "highcharts",
    }
    assert dependencies.isdisjoint(large_ui_dependencies)


def test_v29_shell_navigation_and_landing_surfaces_exist() -> None:
    app = read(APP_TSX)

    required_components = [
        "function UnifiedNavigation",
        "function ProjectHomeRedesignPanel",
        "function ModeLandingPage",
        "function LocalStatusBar",
        "function WorldStudioLanding",
        "function ScriptModEntryPanel",
        "function CrossModeDashboardPanel",
        "function QualityDashboardUXPanel",
        "function DiagnosticsExportPanel",
        "function LocalHelpOnboardingPanel",
    ]
    for component in required_components:
        assert component in app

    for label in [
        "Project Home",
        "Novel",
        "Tavern",
        "World",
        "Cross-Mode",
        "Script / Mods",
        "Providers",
        "Quality",
        "Debug / Replay",
        "Settings",
    ]:
        assert label in app


def test_v29_shared_state_and_safe_summary_components_exist() -> None:
    app = read(APP_TSX)

    for component in [
        "function SafeSummaryCard",
        "function ModeCard",
        "function RiskBadge",
        "function ValidationStatusBadge",
        "function FeatureCard",
        "function LocalOnlyBadge",
        "function SecretSafeNotice",
        "function DisabledState",
        "function EmptyState",
        "function ErrorPanel",
    ]:
        assert component in app

    assert "sanitizeDisplayError(message)" in app
    assert "Traceback" in app
    assert "authorization" in app.lower()


def test_v29_provider_setup_has_no_plaintext_api_key_field() -> None:
    app = read(APP_TSX)

    assert "api_key_env" in app
    assert "secret_ref" in app
    assert "plaintext API key field" in app
    assert not re.search(r"<input[^>]+name=[\"']api_key[\"']", app, flags=re.IGNORECASE)
    assert not re.search(r"api_key\s*:\s*[\"'][^\"']+", app)


def test_v29_privacy_export_and_diagnostics_are_secret_safe_by_default() -> None:
    app = read(APP_TSX)

    for alternatives in [
        ("API keys are not stored in project", "API Key 不保存到项目"),
        ("export filters secrets", "导出默认过滤"),
        ("No cloud sync", "不使用云同步"),
        ("Diagnostics Export", "诊断 / 导出"),
        ("Nothing is uploaded", "不上传", "不会上传"),
        ("raw state_deltas",),
        ("mature/private content", "mature/private"),
        ("debug memory",),
    ]:
        assert any(text in app for text in alternatives), alternatives

    assert "api_key_status: \"[redacted]\"" in app
    assert any(text in app for text in ["Debug export gated", "Debug 导出", "Debug 包受保护", "Safe Debug Export"])
    assert "ENABLE_DEBUG_API" in app


def test_v29_normal_ui_hidden_debug_and_mature_boundaries_are_documented() -> None:
    app = read(APP_TSX)

    for text in [
        "Hidden World facts are not displayed in normal Novel UI.",
        "Tavern does not directly modify World state.",
        "Mature Module is disabled by default.",
        "Normal view uses visible state only.",
        "Raw state deltas are not shown in normal review.",
        "No online marketplace",
        "no remote auto-download",
        "no arbitrary code execution",
    ]:
        assert text in app


def test_v29_api_client_redacts_sensitive_errors_and_detects_disabled_states() -> None:
    api = read(API_TS)

    for helper in [
        "export class ApiError",
        "export async function safeFetch",
        "export async function parseJsonSafe",
        "export function getErrorMessageSafe",
        "export function isApiDisabledError",
        "export function isDebugDisabledError",
        "function redactSensitiveText",
    ]:
        assert helper in api

    for pattern in [
        "sk-[A-Za-z0-9_-]+",
        "authorization",
        "api[_-]?key",
        "raw[_\\s-]?prompts?",
        "state[_\\s-]?deltas?",
        "Traceback",
        "[local path redacted]",
    ]:
        assert pattern in api


def test_v29_static_check_script_covers_ui_safety_boundaries() -> None:
    script = read(V29_CHECK)

    for token in [
        "UnifiedNavigation",
        "LocalStatusBar",
        "DiagnosticsExportPanel",
        "Provider Setup",
        "No cloud sync",
        "No online marketplace",
        "Mature Module is disabled by default",
        "Plaintext api_key input",
        "Account|Cloud Sync|Online Marketplace",
        "Secret-looking sk-* token",
    ]:
        assert token in script
