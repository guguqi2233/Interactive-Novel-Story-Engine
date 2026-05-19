import argparse
import json

from app.llm.provider_benchmark import (
    PROVIDER_BENCHMARK_TYPES,
    ProviderBenchmarkRun,
    ProviderBenchmarkType,
    run_provider_benchmark,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local provider benchmark harness.")
    parser.add_argument("--provider", default="fake", help="Provider id: fake, mock, local_stub, local_http, openai.")
    parser.add_argument("--model", default=None, help="Optional model id label for the report.")
    parser.add_argument(
        "--benchmark",
        action="append",
        choices=PROVIDER_BENCHMARK_TYPES,
        help="Benchmark type to run. May be repeated. Defaults to the safe smoke set.",
    )
    parser.add_argument("--iterations", type=int, default=1, help="Iterations per case.")
    parser.add_argument("--allow-real-provider", action="store_true", help="Explicitly allow real external provider calls.")
    args = parser.parse_args(argv)

    request_kwargs = {
        "provider_id": args.provider,
        "model_id": args.model,
        "allow_real_provider": args.allow_real_provider,
        "iterations": max(1, args.iterations),
    }
    if args.benchmark:
        request_kwargs["benchmark_types"] = [ProviderBenchmarkType(value) for value in args.benchmark]
    request = ProviderBenchmarkRun(**request_kwargs)
    report = run_provider_benchmark(request)
    print(json.dumps(report.model_dump_safe(), ensure_ascii=False, indent=2))
    return 1 if report.blockers or any(not case.ok for case in report.cases) else 0


if __name__ == "__main__":
    raise SystemExit(main())
