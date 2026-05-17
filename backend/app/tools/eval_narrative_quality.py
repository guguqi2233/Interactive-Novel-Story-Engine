import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.evals.narrative_quality import (  # noqa: E402
    sample_narrative_quality_cases,
    run_narrative_quality_evals,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic narrative quality evals.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    report = run_narrative_quality_evals(sample_narrative_quality_cases())
    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(f"Total cases: {report.total_cases}")
        print(f"Passed: {report.passed}")
        print(f"Failed: {report.failed}")
        if report.failure_reasons:
            print(json.dumps(report.failure_reasons, ensure_ascii=False, indent=2))
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
