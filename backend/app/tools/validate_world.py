import argparse
from pathlib import Path

from app.engine.content.validator import format_validation_report, validate_world_pack


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a local content pack.")
    parser.add_argument("world_id", help="World id under worlds/{world_id}")
    parser.add_argument(
        "--worlds-root",
        default="worlds",
        help="Directory containing world packs. Defaults to ./worlds",
    )
    args = parser.parse_args(argv)

    report = validate_world_pack(args.world_id, worlds_root=Path(args.worlds_root))
    print(format_validation_report(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
