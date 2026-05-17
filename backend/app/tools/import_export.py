from __future__ import annotations

import argparse
import os
from pathlib import Path

from app.db.repository import SQLiteSaveRepository
from app.engine.content.import_export import ImportExportError, ImportExportService


def main() -> int:
    parser = argparse.ArgumentParser(description="Import/export local world, mod, and save archives.")
    parser.add_argument("--worlds-root", default=os.getenv("AUTHORING_ROOT", "worlds"))
    parser.add_argument("--mods-root", default=os.getenv("MODS_ROOT", "mods"))
    parser.add_argument("--database", default=_database_path_from_env())
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_export_command(subparsers, "export-world", "world_id")
    _add_import_command(subparsers, "import-world")
    _add_export_command(subparsers, "export-mod", "mod_id")
    _add_import_command(subparsers, "import-mod")
    _add_export_command(subparsers, "export-save", "save_id")
    _add_import_command(subparsers, "import-save")

    args = parser.parse_args()
    service = ImportExportService(
        worlds_root=args.worlds_root,
        mods_root=args.mods_root,
        repository=SQLiteSaveRepository(args.database),
    )

    try:
        if args.command == "export-world":
            exported = service.export_world(args.world_id)
            _write_archive(args.output, exported.archive_base64)
            print(f"Exported world archive: {args.output}")
        elif args.command == "import-world":
            result = service.import_world(_read_archive(args.archive), overwrite=args.overwrite)
            _print_import_result(result.model_dump())
        elif args.command == "export-mod":
            exported = service.export_mod(args.mod_id)
            _write_archive(args.output, exported.archive_base64)
            print(f"Exported mod archive: {args.output}")
        elif args.command == "import-mod":
            result = service.import_mod(_read_archive(args.archive), overwrite=args.overwrite)
            _print_import_result(result.model_dump())
        elif args.command == "export-save":
            exported = service.export_save(args.save_id)
            _write_archive(args.output, exported.archive_base64)
            print(f"Exported save archive: {args.output}")
        elif args.command == "import-save":
            result = service.import_save(_read_archive(args.archive), overwrite=args.overwrite)
            _print_import_result(result.model_dump())
    except ImportExportError as exc:
        print(f"Import/export failed: {exc}")
        return 1
    return 0


def _add_export_command(subparsers: argparse._SubParsersAction[argparse.ArgumentParser], name: str, id_name: str) -> None:
    command = subparsers.add_parser(name)
    command.add_argument(f"--{id_name.replace('_', '-')}", dest=id_name, required=True)
    command.add_argument("--output", required=True)


def _add_import_command(subparsers: argparse._SubParsersAction[argparse.ArgumentParser], name: str) -> None:
    command = subparsers.add_parser(name)
    command.add_argument("--archive", required=True)
    command.add_argument("--overwrite", action="store_true")


def _database_path_from_env() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("sqlite:///"):
        return database_url.removeprefix("sqlite:///")
    return os.getenv("DATABASE_PATH", "data/app.db")


def _write_archive(path: str, archive_base64: str) -> None:
    import base64

    Path(path).write_bytes(base64.b64decode(archive_base64.encode("ascii")))


def _read_archive(path: str) -> str:
    import base64

    return base64.b64encode(Path(path).read_bytes()).decode("ascii")


def _print_import_result(result: dict[str, object]) -> None:
    print(f"Imported: {result['imported']}")
    print(f"Type: {result['import_type']}")
    print(f"Id: {result['id']}")
    print(f"Validation ok: {result['validation_ok']}")
    if result["errors"]:
        print(f"Errors: {result['errors']}")
    if result["warnings"]:
        print(f"Warnings: {result['warnings']}")
    if result["migration_needed"]:
        print("Migration needed: true")


if __name__ == "__main__":
    raise SystemExit(main())
