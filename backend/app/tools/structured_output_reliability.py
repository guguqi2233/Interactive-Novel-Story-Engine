from __future__ import annotations

import argparse
import json

from app.llm.structured_output_reliability import (
    STRUCTURED_OUTPUT_SCHEMA_NAMES,
    StructuredOutputReliabilityRun,
    StructuredOutputSchemaName,
    StructuredOutputTestCase,
    run_structured_output_reliability,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local structured output reliability checks.")
    parser.add_argument("--provider", default="fake", help="Provider id. Defaults to fake.")
    parser.add_argument("--model", default=None, help="Optional model label.")
    parser.add_argument(
        "--schema",
        action="append",
        choices=STRUCTURED_OUTPUT_SCHEMA_NAMES,
        help="Schema to test. May be repeated. Defaults to all supported schemas.",
    )
    parser.add_argument("--allow-real-provider", action="store_true", help="Explicitly allow real external provider calls.")
    args = parser.parse_args(argv)

    cases = [
        StructuredOutputTestCase(id=f"cli_{schema_name}", schema_name=StructuredOutputSchemaName(schema_name))
        for schema_name in (args.schema or [])
    ]
    report = run_structured_output_reliability(
        StructuredOutputReliabilityRun(
            provider_id=args.provider,
            model_id=args.model,
            allow_real_provider=args.allow_real_provider,
            cases=cases,
        )
    )
    print(json.dumps(report.model_dump_safe(), ensure_ascii=False, indent=2))
    return 1 if report.blockers or any(not case.ok for case in report.cases) else 0


if __name__ == "__main__":
    raise SystemExit(main())
