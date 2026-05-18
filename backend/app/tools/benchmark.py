import argparse
import json
from pathlib import Path

from app.quality.benchmarks import BENCHMARK_TYPES, BenchmarkRunRequest, run_benchmark_suite


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local benchmark suite.")
    parser.add_argument("--world", default="mist_valley", help="World id under worlds/{world_id}.")
    parser.add_argument("--worlds-root", default="worlds", help="Directory containing world packs.")
    parser.add_argument("--iterations", type=int, default=1, help="Samples per benchmark.")
    parser.add_argument(
        "--benchmark",
        action="append",
        choices=BENCHMARK_TYPES,
        help="Benchmark type to run. May be repeated. Defaults to all.",
    )
    parser.add_argument(
        "--threshold",
        action="append",
        default=[],
        help="Threshold in name=milliseconds form, e.g. validate_world=50.",
    )
    args = parser.parse_args(argv)
    thresholds = _parse_thresholds(args.threshold)
    report = run_benchmark_suite(
        BenchmarkRunRequest(
            world_id=args.world,
            worlds_root=str(Path(args.worlds_root)),
            iterations=max(1, args.iterations),
            benchmarks=args.benchmark or list(BENCHMARK_TYPES),
            thresholds_ms=thresholds,
        )
    )
    print(json.dumps(report.model_dump_safe(), ensure_ascii=False, indent=2))
    return 1 if report.regressions or any(not sample.ok for sample in report.samples) else 0


def _parse_thresholds(values: list[str]) -> dict[str, float]:
    thresholds: dict[str, float] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"Invalid threshold: {value}")
        name, raw_ms = value.split("=", 1)
        thresholds[name] = float(raw_ms)
    return thresholds


if __name__ == "__main__":
    raise SystemExit(main())
