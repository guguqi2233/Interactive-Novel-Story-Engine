from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.engine.gameplay_module_packages import (  # noqa: E402
    GameplayModulePackageImportRequest,
    export_gameplay_module_package,
    import_gameplay_module_package_apply,
    import_gameplay_module_package_dry_run,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local gameplay module import/export CLI.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--modules-root", default="gameplay_modules")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export a gameplay module package.")
    export_parser.add_argument("--module-id", required=True)
    export_parser.add_argument("--output", default="")

    dry_run_parser = subparsers.add_parser("import-dry-run", help="Dry-run import a gameplay module package.")
    dry_run_parser.add_argument("--archive", required=True)

    apply_parser = subparsers.add_parser("import-apply", help="Apply a gameplay module package import.")
    apply_parser.add_argument("--archive", required=True)
    apply_parser.add_argument("--confirm-apply", action="store_true")
    apply_parser.add_argument("--overwrite", action="store_true")

    args = parser.parse_args(argv)
    try:
        result, ok = _dispatch(args)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    payload = result.model_dump(mode="json", exclude_none=True) if hasattr(result, "model_dump") else result
    if args.json:
        print(json.dumps(_strip_archive(payload), indent=2, sort_keys=True))
    else:
        print(json.dumps(_strip_archive(payload), indent=2))
    return 0 if ok else 1


def _dispatch(args: argparse.Namespace) -> tuple[object, bool]:
    if args.command == "export":
        result = export_gameplay_module_package(args.module_id, modules_root=args.modules_root)
        if args.output:
            import base64

            Path(args.output).write_bytes(base64.b64decode(result.archive_base64.encode("ascii")))
        return result, result.exported
    if args.command == "import-dry-run":
        request = GameplayModulePackageImportRequest(archive_base64=Path(args.archive).read_text(encoding="utf-8"))
        result = import_gameplay_module_package_dry_run(request)
        return result, result.ok
    if args.command == "import-apply":
        request = GameplayModulePackageImportRequest(
            archive_base64=Path(args.archive).read_text(encoding="utf-8"),
            confirm_apply=args.confirm_apply,
            overwrite=args.overwrite,
        )
        result = import_gameplay_module_package_apply(request, modules_root=args.modules_root)
        return result, result.ok and result.imported
    raise ValueError(f"Unknown command: {args.command}")


def _strip_archive(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _strip_archive(child)
            for key, child in value.items()
            if key != "archive_base64"
        }
    if isinstance(value, list):
        return [_strip_archive(child) for child in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
