from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.config import get_settings  # noqa: E402
from app.desktop.crash_reports import CrashReportService  # noqa: E402
from app.desktop.startup_diagnostics import StartupDiagnosticsService, sanitize_startup_diagnostic_text  # noqa: E402
from app.desktop.workspaces import WorkspaceService  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run safe local desktop startup diagnostics.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--project-root", default=".", help="Repository/workspace root to inspect.")
    parser.add_argument("--backend-port", type=int, default=8000, help="Backend port to check.")
    parser.add_argument("--frontend-port", type=int, default=5173, help="Frontend port to check.")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    settings = get_settings()
    service = StartupDiagnosticsService(
        project_root=project_root,
        settings=settings,
        workspace_service=WorkspaceService(default_workspace=project_root),
        crash_report_service=CrashReportService(),
        backend_ports=(args.backend_port,),
        frontend_ports=(args.frontend_port,),
    )
    report = service.run()

    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        _print_human_report(report)
    return 1 if report.overall_status == "error" else 0


def _print_human_report(report: object) -> None:
    overall = getattr(report, "overall_status")
    print(f"Startup diagnostics: {overall}")
    for check in getattr(report, "checks"):
        detail = f" ({check.safe_detail})" if check.safe_detail else ""
        print(f"- [{check.status}] {check.label}: {check.message}{detail}")
    actions = getattr(report, "recommended_actions")
    if actions:
        print("Recommended actions:")
        for action in actions:
            print(f"- {sanitize_startup_diagnostic_text(action)}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": sanitize_startup_diagnostic_text(str(exc))}, indent=2), file=sys.stderr)
        raise SystemExit(2)
