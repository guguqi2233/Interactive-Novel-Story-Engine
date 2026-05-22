from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.engine.action_mod_schema import ActionMod
from app.engine.action_mod_test_harness import ActionModTestHarness


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local declarative Action Mod tests.")
    parser.add_argument("mod_path")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    mod_path = Path(args.mod_path)
    manifest_path = mod_path / "action_mod.json"
    tests_path = mod_path / "action_mod_tests.json"
    if not manifest_path.exists():
        manifest_path = mod_path / "action_mod.yaml"
    if not tests_path.exists():
        tests_path = mod_path / "action_mod_tests.yaml"
    action_mod = ActionMod.model_validate_json(manifest_path.read_text(encoding="utf-8")) if manifest_path.suffix == ".json" else ActionMod.model_validate(__import__("yaml").safe_load(manifest_path.read_text(encoding="utf-8")))
    harness = ActionModTestHarness(action_mod)
    report = harness.run_all_for_mod(ActionModTestHarness.load_test_cases(tests_path))
    if args.json_output:
        print(report.model_dump_json(indent=2))
    else:
        print(f"Action Mod tests {'passed' if report.ok else 'failed'}: {report.safe_summary}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
