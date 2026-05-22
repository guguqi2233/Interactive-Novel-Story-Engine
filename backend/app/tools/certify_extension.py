from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.platform.extension_certification import CertificationService
from app.platform.module_browser import ModuleBrowserService


def main() -> int:
    parser = argparse.ArgumentParser(description="Certify a local extension package.")
    parser.add_argument("package_path")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    path = Path(args.package_path).resolve()
    service = CertificationService(ModuleBrowserService(path.parent.parent if path.is_dir() else path.parent))
    report = service.certify_package(path.name if path.is_dir() else path.parent.name)
    if args.json_output:
        print(report.model_dump_json(indent=2))
    else:
        print(f"{report.package_id}: {report.level.value} ({'ok' if report.ok else 'blocked'})")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
