from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.quality.module_quality_gate import run_module_quality_gate  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the v2.7 advanced module quality gate.")
    parser.add_argument("project_path", nargs="?", default=".", help="Local project path; currently used only for report context.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)
    report = run_module_quality_gate()
    payload = report.model_dump(mode="json")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Advanced module quality gate for {args.project_path}")
        print(f"passed: {str(report.passed).lower()}")
        print(f"blockers: {len(report.blockers)}")
        for blocker in report.blockers:
            print(f"- {blocker}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
