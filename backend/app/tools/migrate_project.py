from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.platform.project_migration import migrate_project_apply, migrate_project_dry_run  # noqa: E402
from app.platform.project_repository import ProjectRepository  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate a v2.0 workspace into a v2.1 NarrativeProject.")
    parser.add_argument("--from", dest="source", required=True)
    parser.add_argument("--to", dest="target", required=True)
    parser.add_argument("--project-id", default="migrated_project")
    parser.add_argument("--project-name", default="Migrated Narrative Project")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.apply:
        report = migrate_project_apply(
            args.source,
            args.target,
            ProjectRepository(Path(args.target).resolve().parent),
            confirm_apply=True,
            project_id=args.project_id,
            project_name=args.project_name,
        )
    else:
        report = migrate_project_dry_run(args.source, args.target, project_id=args.project_id, project_name=args.project_name)
    if args.json:
        print(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))
    else:
        print(f"Project migration: {'APPLIED' if report.applied else 'DRY-RUN'}")
        print(f"Can migrate: {report.plan.can_migrate}")
        print(f"Copies: {len(report.plan.copies)}")
        print(f"Blockers: {len(report.plan.blockers)}")
    return 0 if report.plan.can_migrate or report.applied else 1


if __name__ == "__main__":
    raise SystemExit(main())

