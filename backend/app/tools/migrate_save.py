import argparse
import json

from app.config import get_settings
from app.db.migration_service import MigrationService
from app.db.repository import SaveRepositoryError, SQLiteSaveRepository


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect or migrate local SQLite saves.")
    parser.add_argument("--database-url", default=None, help="SQLite database URL/path. Defaults to DATABASE_URL.")
    parser.add_argument("--save-id", default=None, help="Save id to inspect or migrate.")
    parser.add_argument("--list", action="store_true", help="List available migrations.")
    parser.add_argument("--status", action="store_true", help="Show migration status for --save-id.")
    parser.add_argument("--dry-run", action="store_true", help="Run migration without writing the database.")
    parser.add_argument("--apply", action="store_true", help="Apply migration and create a backup save.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    selected_actions = [args.list, args.status, args.dry_run, args.apply]
    if sum(1 for action in selected_actions if action) != 1:
        parser.error("Choose exactly one of --list, --status, --dry-run, or --apply.")
    if not args.list and not args.save_id:
        parser.error("--save-id is required unless --list is used.")

    repository = SQLiteSaveRepository(_sqlite_path_from_url(args.database_url or get_settings().database_url))
    service = MigrationService(repository)

    try:
        if args.list:
            migrations = service.list_available_migrations()
            payload = {"migrations": [migration.model_dump(mode="json") for migration in migrations]}
            _print_payload(payload, args.json)
            return 0
        if args.status:
            status = service.status(args.save_id)
            _print_payload(status.model_dump(mode="json"), args.json)
            return 0
        if args.dry_run:
            report = service.dry_run(args.save_id)
            _print_payload(report.model_dump(mode="json"), args.json)
            return 0 if report.success else 1
        report = service.apply(args.save_id)
        _print_payload(report.model_dump(mode="json"), args.json)
        return 0 if report.success else 1
    except SaveRepositoryError as exc:
        error_payload = {"error": str(exc)}
        _print_payload(error_payload, args.json)
        return 1


def _print_payload(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if "error" in payload:
        print(f"error: {payload['error']}")
        return
    if "migrations" in payload:
        print("available migrations:")
        for migration in payload["migrations"]:  # type: ignore[index]
            print(
                f"- {migration['migration_id']}: "
                f"{migration['source_version']} -> {migration['target_version']} "
                f"({migration['description']})"
            )
        return
    if "needs_migration" in payload:
        print(f"save id: {payload['save_id']}")
        print(f"current version: {payload['schema_version']}")
        print(f"target version: {payload['target_schema_version']}")
        print(f"engine version: {payload['engine_version']}")
        print(f"world id: {payload['world_id']}")
        print(f"world version: {payload['world_version']}")
        print(f"content pack version: {payload['content_pack_version']}")
        print(f"needs migration: {payload['needs_migration']}")
        print(f"migration path: {_format_path(payload.get('migration_path', []))}")
        _print_warnings(payload.get("warnings", []))
        return
    print(f"save id: {payload['save_id']}")
    print(f"current version: {payload['source_version']}")
    print(f"target version: {payload['target_version']}")
    print(f"dry run: {payload['dry_run']}")
    print(f"success: {payload['success']}")
    print(f"backup save id: {payload.get('backup_save_id') or 'none'}")
    print(f"migration path: {_format_history(payload.get('applied_migrations', []))}")
    _print_warnings(payload.get("warnings", []))


def _print_warnings(raw_warnings: object) -> None:
    warnings = raw_warnings if isinstance(raw_warnings, list) else []
    if not warnings:
        print("warnings: none")
        return
    print("warnings:")
    for warning in warnings:
        print(f"- {warning}")


def _format_path(raw_path: object) -> str:
    if not isinstance(raw_path, list) or not raw_path:
        return "none"
    return " -> ".join(str(item) for item in raw_path)


def _format_history(raw_history: object) -> str:
    if not isinstance(raw_history, list) or not raw_history:
        return "none"
    return " -> ".join(str(item.get("migration_id", "unknown")) for item in raw_history if isinstance(item, dict))


def _sqlite_path_from_url(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        return database_url.removeprefix("sqlite:///")
    if database_url.startswith("sqlite://"):
        return database_url.removeprefix("sqlite://")
    return database_url


if __name__ == "__main__":
    raise SystemExit(main())
