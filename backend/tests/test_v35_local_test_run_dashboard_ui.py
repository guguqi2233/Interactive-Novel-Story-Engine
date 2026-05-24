from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_local_test_run_dashboard_frontend_contract() -> None:
    app_source = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")

    for token in [
        "Local Test Run Dashboard",
        "python -m pytest",
        "cd frontend && npm.cmd run build",
        "provider/model discovery tests",
        "fake provider or fake client",
        "quality_gate",
        "Latest safe test report",
        "Frontend build status",
        "local-only",
        "No arbitrary command UI",
        "No generic terminal",
        "no custom shell input",
        "no raw env",
        "No arbitrary command input or terminal is exposed",
        "buildLocalTestSafeReports",
    ]:
        assert token in app_source

    dashboard_source = app_source[
        app_source.index("function LocalTestRunDashboard") :
        app_source.index("function buildLocalTestSafeReports")
    ]
    forbidden_tokens = [
        "child_process",
        "exec(",
        "spawn(",
        "powershell",
        "cmd.exe",
        "terminal input",
    ]
    for token in forbidden_tokens:
        assert token not in dashboard_source
    assert "onClick={command" not in dashboard_source
