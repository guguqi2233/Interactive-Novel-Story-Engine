from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.platform.project_validation import validate_project  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a local NarrativeProject.")
    parser.add_argument("project_path")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)
    report = validate_project(args.project_path, profile="debug" if args.debug else "normal")
    if args.json:
        print(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))
    else:
        print(f"Project validation: {'PASS' if report.ok else 'FAIL'}")
        print(f"errors: {len(report.errors)}")
        print(f"warnings: {len(report.warnings)}")
        print(f"suggestions: {len(report.suggestions)}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

