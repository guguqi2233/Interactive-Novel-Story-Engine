import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.playtesting.batch import PlaytestBatchRunRequest, run_playtest_batch  # noqa: E402


def _csv_ints(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _csv_strings(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic local playtest batches.")
    parser.add_argument("--world", default="mist_valley", help="World id to test.")
    parser.add_argument("--scenario-ids", default="", help="Comma-separated scenario ids.")
    parser.add_argument(
        "--agents",
        default="random_valid_action_agent",
        help="Comma-separated playtesting agents.",
    )
    parser.add_argument("--seeds", default="123", help="Comma-separated integer seeds.")
    parser.add_argument("--steps", type=int, default=25, help="Maximum steps per non-scenario run.")
    parser.add_argument("--stop-on-blocker", action="store_true", help="Stop at first blocker.")
    parser.add_argument("--save-load-check", action="store_true", help="Round-trip save/load during each run.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    report = run_playtest_batch(
        PlaytestBatchRunRequest(
            world_id=args.world,
            scenario_ids=_csv_strings(args.scenario_ids),
            agent_types=_csv_strings(args.agents) or ["random_valid_action_agent"],
            seeds=_csv_ints(args.seeds) or [123],
            steps=args.steps,
            stop_on_blocker=args.stop_on_blocker,
            save_load_check=args.save_load_check,
        )
    )

    if args.json:
        print(json.dumps(report.model_dump_normal(), indent=2))
    else:
        print(f"Batch run: {report.run_id}")
        print(f"World: {report.world_id}")
        print(f"Total runs: {report.total_runs}")
        print(f"Passed: {report.passed}")
        print(f"Failed: {report.failed}")
        print(f"Blockers: {report.blockers}")
        print(f"Aggregate issues: {len(report.aggregate_issues)}")
        print(json.dumps(report.coverage_summary.model_dump(mode="json"), indent=2))

    return 1 if report.blockers or report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
