from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.quality.project_gate import ProjectQualityGateConfig, run_project_quality_gate  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the NarrativeProject quality gate.")
    parser.add_argument("project_path")
    parser.add_argument("--profile", choices=["fast", "standard", "strict"], default="standard")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--skip-world-quality-gate", action="store_true")
    parser.add_argument("--include-cross-mode", action="store_true")
    args = parser.parse_args(argv)
    result = run_project_quality_gate(
        args.project_path,
        ProjectQualityGateConfig(profile=args.profile, run_world_quality_gate=not args.skip_world_quality_gate, include_cross_mode=args.include_cross_mode),
    )
    if args.json:
        print(json.dumps(result.model_dump_normal(), indent=2, ensure_ascii=False))
    else:
        print(f"Project quality gate: {'PASS' if result.passed else 'FAIL'}")
        print(f"Blockers: {len(result.blockers)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Warnings: {len(result.warnings)}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
