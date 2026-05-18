import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.quality.gate import QualityGateConfig, run_quality_gate  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local release quality gate.")
    parser.add_argument("--world", default="mist_valley", help="World id to validate.")
    parser.add_argument("--worlds-root", default="worlds", help="World pack root.")
    parser.add_argument("--mods-root", default="mods", help="Local mods root.")
    parser.add_argument("--fail-on-warning", action="store_true", help="Fail when warnings are present.")
    parser.add_argument("--allow-errors", action="store_true", help="Do not fail on error issues.")
    parser.add_argument("--allow-blockers", action="store_true", help="Do not fail on blocker issues.")
    parser.add_argument("--min-health-score", type=int, default=70, help="Minimum heuristic health score.")
    parser.add_argument("--max-performance-p95", type=float, default=None, help="Optional max benchmark p95 in ms.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    result = run_quality_gate(
        args.world,
        QualityGateConfig(
            allow_warnings=not args.fail_on_warning,
            fail_on_error=not args.allow_errors,
            fail_on_blocker=not args.allow_blockers,
            min_health_score=args.min_health_score,
            max_performance_p95_ms=args.max_performance_p95,
        ),
        worlds_root=args.worlds_root,
        mods_root=args.mods_root,
    )
    if args.json:
        print(json.dumps(result.model_dump_normal(), indent=2))
    else:
        print(f"Quality gate: {'PASS' if result.passed else 'FAIL'}")
        print(f"World: {result.world_id}")
        print(f"Health score: {result.health_score}")
        print(f"Blockers: {len(result.blockers)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Warnings: {len(result.warnings)}")
        print(f"Reports: {len(result.report_links)}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
