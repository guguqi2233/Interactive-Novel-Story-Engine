from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.platform.cross_mode import validate_cross_mode_project  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate NarrativeProject cross-mode bridge artifacts.")
    parser.add_argument("project_path")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)
    report = validate_cross_mode_project(args.project_path, profile="debug" if args.debug else "normal")
    if args.json:
        print(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))
    else:
        print(f"Cross-mode validation: {'PASS' if report.ok else 'FAIL'}")
        print(f"Blockers: {len(report.blockers)}")
        print(f"Errors: {len(report.errors)}")
        print(f"Warnings: {len(report.warnings)}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
