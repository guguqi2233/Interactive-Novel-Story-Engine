from __future__ import annotations

import argparse
import json

from app.llm.prompt_regression import (
    PROMPT_REGRESSION_CASE_TYPES,
    PromptRegressionCase,
    PromptRegressionCaseType,
    PromptRegressionRun,
    run_prompt_regression,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local Prompt Lab regression checks.")
    parser.add_argument("--baseline-profile", default="default_safe")
    parser.add_argument("--candidate-profile", default="default_safe")
    parser.add_argument("--baseline-provider", default="fake")
    parser.add_argument("--candidate-provider", default="fake")
    parser.add_argument("--baseline-model", default=None)
    parser.add_argument("--candidate-model", default=None)
    parser.add_argument(
        "--case",
        action="append",
        choices=PROMPT_REGRESSION_CASE_TYPES,
        help="Regression case type to run. May be repeated. Defaults to all safe cases.",
    )
    parser.add_argument("--allow-real-provider", action="store_true", help="Explicitly allow real external provider calls.")
    args = parser.parse_args(argv)

    cases = [
        PromptRegressionCase(id=f"cli_{case_type}", case_type=PromptRegressionCaseType(case_type))
        for case_type in (args.case or [])
    ]
    report = run_prompt_regression(
        PromptRegressionRun(
            baseline_profile_id=args.baseline_profile,
            candidate_profile_id=args.candidate_profile,
            baseline_provider_id=args.baseline_provider,
            baseline_model_id=args.baseline_model,
            candidate_provider_id=args.candidate_provider,
            candidate_model_id=args.candidate_model,
            cases=cases,
            allow_real_provider=args.allow_real_provider,
        )
    )
    print(json.dumps(report.model_dump_safe(), ensure_ascii=False, indent=2))
    return 1 if report.pass_fail == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
