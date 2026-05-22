from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.quality.mod_quality_gate import run_mod_quality_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v2.6 local Mod Quality Gate.")
    parser.add_argument("package_path")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    path = Path(args.package_path).resolve()
    project_root = path.parent.parent if path.is_dir() else path.parent
    package_id = path.name if path.is_dir() else path.parent.name
    report = run_mod_quality_gate(project_root, package_id)
    if args.json_output:
        print(report.model_dump_json(indent=2))
    else:
        print(f"Mod Quality Gate {'passed' if report.ok else 'failed'} for {report.package_id}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
