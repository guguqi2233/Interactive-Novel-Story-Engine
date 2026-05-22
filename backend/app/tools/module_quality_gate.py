from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.quality.gameplay_module_quality import run_gameplay_module_quality_gate  # noqa: E402
from app.quality.module_quality_gate import run_module_quality_gate  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local gameplay or v2.7 advanced module quality gate.")
    parser.add_argument("module_id", help="Gameplay module id or local project path to validate.")
    parser.add_argument("--modules-root", default="gameplay_modules", help="Directory containing gameplay modules.")
    parser.add_argument("--advanced", action="store_true", help="Run the v2.7 advanced module quality gate.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    candidate_path = Path(args.module_id)
    if args.advanced or candidate_path.exists():
        report = run_module_quality_gate()
        payload = report.model_dump(mode="json")
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"Advanced module quality gate: {candidate_path}")
            print(f"passed: {str(report.passed).lower()}")
            print(f"blockers: {len(report.blockers)}")
            for blocker in report.blockers:
                print(f"- {blocker}")
        return 0 if report.passed else 1

    report = run_gameplay_module_quality_gate(args.module_id, modules_root=args.modules_root)
    payload = report.model_dump_normal()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Gameplay module quality gate: {report.module_id}")
        print(f"passed: {str(report.passed).lower()}")
        print(f"blockers: {len(report.blockers)}")
        print(f"warnings: {len(report.warnings)}")
        for check in report.checks:
            print(f"- {check.name}: {check.status.value}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
