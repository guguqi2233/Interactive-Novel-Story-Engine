from __future__ import annotations

import argparse
import json
from typing import Any

from app.config import Settings
from app.llm.local_model_diagnostics import LocalModelDiagnosticRequest, run_local_model_diagnostics
from app.llm.model_compatibility import build_model_compatibility_matrix
from app.llm.provider_benchmark import (
    PROVIDER_BENCHMARK_TYPES,
    ProviderBenchmarkRun,
    ProviderBenchmarkType,
    run_provider_benchmark,
)
from app.llm.prompt_regression import (
    PROMPT_REGRESSION_CASE_TYPES,
    PromptRegressionCase,
    PromptRegressionCaseType,
    PromptRegressionRun,
    run_prompt_regression,
)
from app.llm.structured_output_reliability import (
    STRUCTURED_OUTPUT_SCHEMA_NAMES,
    StructuredOutputReliabilityRun,
    StructuredOutputSchemaName,
    StructuredOutputTestCase,
    run_structured_output_reliability,
)
from app.llm.token_budget import TokenBudgetRequest, build_default_token_budget_profiles, estimate_token_budget


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local Prompt Lab tools without exposing secrets.")
    parser.add_argument("--json", action="store_true", help="Emit safe JSON instead of a short human-readable summary.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    benchmark = subparsers.add_parser("benchmark-provider", help="Run provider benchmark harness.")
    benchmark.add_argument("--provider", default="fake")
    benchmark.add_argument("--model", default=None)
    benchmark.add_argument("--benchmark", action="append", choices=PROVIDER_BENCHMARK_TYPES)
    benchmark.add_argument("--iterations", type=int, default=1)
    benchmark.add_argument("--allow-real-provider", action="store_true")

    structured = subparsers.add_parser("structured-output", help="Run structured output reliability checks.")
    structured.add_argument("--provider", default="fake")
    structured.add_argument("--model", default=None)
    structured.add_argument("--schema", action="append", choices=STRUCTURED_OUTPUT_SCHEMA_NAMES)
    structured.add_argument("--allow-real-provider", action="store_true")

    regression = subparsers.add_parser("prompt-regression", help="Run prompt regression suite.")
    regression.add_argument("--baseline-profile", default="default_safe")
    regression.add_argument("--candidate-profile", default="default_safe")
    regression.add_argument("--baseline-provider", default="fake")
    regression.add_argument("--candidate-provider", default="fake")
    regression.add_argument("--case", action="append", choices=PROMPT_REGRESSION_CASE_TYPES)
    regression.add_argument("--allow-real-provider", action="store_true")

    diagnostics = subparsers.add_parser("local-diagnostics", help="Run local model diagnostics.")
    diagnostics.add_argument("--provider", default="local_stub", choices=["local_stub", "local_http"])
    diagnostics.add_argument("--model", default=None)
    diagnostics.add_argument("--base-url", default=None)
    diagnostics.add_argument("--fake-mode", default="ok", choices=["ok", "invalid_json", "timeout", "error"])
    diagnostics.add_argument("--allow-real-local-check", action="store_true")

    subparsers.add_parser("compatibility-matrix", help="Generate model compatibility matrix from local metadata.")

    budget = subparsers.add_parser("token-budget-report", help="Generate token budget report from a safe sample context.")
    budget.add_argument("--profile", default="narrator_balanced")
    budget.add_argument("--max-total-tokens", type=int, default=None)

    args = parser.parse_args(argv)
    try:
        payload, exit_code = _run_command(args)
    except Exception as exc:
        payload = {"ok": False, "error_type": type(exc).__name__, "error": _safe_text(str(exc))}
        exit_code = 2
    _emit(payload, json_output=args.json)
    return exit_code


def _run_command(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    if args.command == "benchmark-provider":
        benchmarks = [ProviderBenchmarkType(item) for item in (args.benchmark or [])]
        benchmark_kwargs: dict[str, Any] = {}
        if benchmarks:
            benchmark_kwargs["benchmark_types"] = benchmarks
        report = run_provider_benchmark(
            ProviderBenchmarkRun(
                provider_id=args.provider,
                model_id=args.model,
                allow_real_provider=args.allow_real_provider,
                iterations=max(1, args.iterations),
                **benchmark_kwargs,
            )
        )
        return report.model_dump_safe(), 1 if report.blockers or any(not case.ok for case in report.cases) else 0

    if args.command == "structured-output":
        cases = [
            StructuredOutputTestCase(id=f"cli_{schema}", schema_name=StructuredOutputSchemaName(schema))
            for schema in (args.schema or [])
        ]
        report = run_structured_output_reliability(
            StructuredOutputReliabilityRun(
                provider_id=args.provider,
                model_id=args.model,
                allow_real_provider=args.allow_real_provider,
                cases=cases,
            )
        )
        return report.model_dump_safe(), 1 if report.blockers or any(not case.ok for case in report.cases) else 0

    if args.command == "prompt-regression":
        cases = [
            PromptRegressionCase(id=f"cli_{case_type}", case_type=PromptRegressionCaseType(case_type))
            for case_type in (args.case or [])
        ]
        report = run_prompt_regression(
            PromptRegressionRun(
                baseline_profile_id=args.baseline_profile,
                candidate_profile_id=args.candidate_profile,
                baseline_provider_id=args.baseline_provider,
                candidate_provider_id=args.candidate_provider,
                cases=cases,
                allow_real_provider=args.allow_real_provider,
            )
        )
        return report.model_dump_safe(), 1 if report.pass_fail == "fail" else 0

    if args.command == "local-diagnostics":
        settings = Settings(llm_provider="mock", local_llm_base_url=args.base_url or "")
        report = run_local_model_diagnostics(
            LocalModelDiagnosticRequest(
                provider_id=args.provider,
                model_id=args.model,
                base_url=args.base_url,
                fake_mode=args.fake_mode if not args.allow_real_local_check else None,
                allow_real_local_check=args.allow_real_local_check,
            ),
            settings=settings,
        )
        return report.model_dump_safe(), 1 if report.blockers else 0

    if args.command == "compatibility-matrix":
        matrix = build_model_compatibility_matrix()
        return matrix.model_dump_safe(), 0

    if args.command == "token-budget-report":
        profile = next((item for item in build_default_token_budget_profiles() if item.id == args.profile), build_default_token_budget_profiles()[0])
        if args.max_total_tokens is not None:
            profile = profile.model_copy(update={"max_total_tokens": args.max_total_tokens})
        report = estimate_token_budget(TokenBudgetRequest(profile=profile))
        return report.model_dump_safe(), 1 if report.blockers else 0

    return {"ok": False, "error": f"Unknown command: {args.command}"}, 2


def _emit(payload: dict[str, Any], *, json_output: bool) -> None:
    safe = _strip_sensitive(payload)
    if json_output:
        print(json.dumps(safe, ensure_ascii=False, indent=2))
        return
    title = safe.get("run_id") or safe.get("matrix_id") or safe.get("report_id") or safe.get("provider_id") or "prompt-lab"
    status = safe.get("pass_fail") or ("fail" if safe.get("blockers") else "pass")
    print(f"{title}: {status}")
    if "total_cases" in safe:
        print(f"cases: {safe.get('total_cases')}")
    if "average_latency_ms" in safe:
        print(f"average_latency_ms: {safe.get('average_latency_ms')}")
    blockers = safe.get("blockers") or []
    warnings = safe.get("warnings") or []
    if blockers:
        print(f"blockers: {', '.join(str(item) for item in blockers)}")
    if warnings:
        print(f"warnings: {', '.join(str(item) for item in warnings)}")


def _strip_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _strip_sensitive(item) for key, item in value.items() if _safe_key(str(key))}
    if isinstance(value, list):
        return [_strip_sensitive(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _safe_key(key: str) -> bool:
    lowered = key.lower()
    return "api_key" not in lowered and "raw_env" not in lowered and "secret" not in lowered


def _safe_text(value: str) -> str:
    lowered = value.lower()
    if "sk-" in lowered or "api_key" in lowered or "hidden fact" in lowered or "npc secret" in lowered:
        return "[redacted]"
    return value[:500]


if __name__ == "__main__":
    raise SystemExit(main())
