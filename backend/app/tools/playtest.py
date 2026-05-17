import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.playtesting.runner import PlaytestOptions, run_playtest  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic local playtesting agents.")
    parser.add_argument("--world", default="mist_valley", help="World id to playtest.")
    parser.add_argument("--steps", type=int, default=25, help="Maximum agent steps.")
    parser.add_argument("--seed", type=int, default=123, help="Random seed.")
    parser.add_argument(
        "--strategy",
        default="random_valid_action_agent",
        choices=[
            "random_valid_action_agent",
            "explore_agent",
            "quest_following_agent",
            "stress_agent",
        ],
        help="Playtesting strategy.",
    )
    parser.add_argument("--save-every", type=int, default=0, help="Round-trip save/load every N steps.")
    parser.add_argument("--database-path", default=None, help="SQLite file for save/load checks.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as temp_dir:
        database_path = args.database_path
        if database_path is None and args.save_every:
            database_path = str(Path(temp_dir) / "playtest.db")
        report = run_playtest(
            PlaytestOptions(
                world_id=args.world,
                strategy=args.strategy,
                max_steps=args.steps,
                seed=args.seed,
                save_every=args.save_every or None,
                database_path=database_path,
            )
        )

    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(f"Playtest strategy: {report.strategy}")
        print(f"World: {report.world_id}")
        print(f"Seed: {report.seed}")
        print(f"Turns run: {report.turns_run}")
        print(f"Actions: {len(report.actions_taken)}")
        print(f"Errors: {len(report.errors)}")
        print(f"Invariant violations: {len(report.invariant_violations)}")
        print(f"Visibility leaks: {len(report.visibility_leaks)}")
        print(f"Save/load failures: {len(report.save_load_failures)}")
        print(json.dumps(report.final_state_summary.model_dump(mode="json"), indent=2))

    return 1 if report.errors or report.invariant_violations or report.visibility_leaks else 0


if __name__ == "__main__":
    raise SystemExit(main())
