import argparse
import json
from pathlib import Path

from app.engine.content.content_batch_validator import (
    BatchPackageType,
    ContentBatchValidationRequest,
    ContentBatchValidationTarget,
    validate_content_batch,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch validate local content packages without executing code.")
    parser.add_argument("--worlds-root", default="worlds")
    parser.add_argument("--packages-root", default="packages")
    parser.add_argument("--templates-root", default="templates")
    parser.add_argument("--mods-root", default="mods")
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help="Target in type:id or type:id:path form. Types: " + ",".join(item.value for item in BatchPackageType),
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON report.")
    args = parser.parse_args()

    targets = [_parse_target(value) for value in args.target]
    request = ContentBatchValidationRequest(
        targets=targets,
        worlds_root=args.worlds_root,
        packages_root=args.packages_root,
        templates_root=args.templates_root,
        mods_root=args.mods_root,
    )
    report = validate_content_batch(request)
    if args.json:
        print(report.model_dump_json(indent=2))
    else:
        print(f"total={report.total} passed={report.passed} warning={report.warning} failed={report.failed}")
        for item in report.per_package_report:
            print(f"{item.package_type.value}:{item.id}:{item.status}")
    return 0 if report.failed == 0 else 1


def _parse_target(value: str) -> ContentBatchValidationTarget:
    parts = value.split(":", 2)
    if len(parts) < 2:
        raise SystemExit("--target must be type:id or type:id:path")
    package_type = BatchPackageType(parts[0])
    path = parts[2] if len(parts) == 3 else None
    return ContentBatchValidationTarget(package_type=package_type, id=parts[1], path=path)


if __name__ == "__main__":
    raise SystemExit(main())
