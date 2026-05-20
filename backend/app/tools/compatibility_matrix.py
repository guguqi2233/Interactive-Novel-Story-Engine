from __future__ import annotations

import argparse
import json

from app.compatibility.matrix import CompatibilityCheckRequest, build_compatibility_matrix, check_compatibility


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect local schema/contract compatibility.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("--contract", help="Contract name to check.")
    parser.add_argument("--version", help="Version to check.")
    args = parser.parse_args()

    if args.contract or args.version:
        if not args.contract or not args.version:
            parser.error("--contract and --version must be provided together")
        result = check_compatibility(CompatibilityCheckRequest(contract=args.contract, version=args.version))
        payload = result.model_dump(mode="json")
    else:
        payload = build_compatibility_matrix().model_dump(mode="json")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        if "entries" in payload:
            print(f"Engine: {payload['engine_version']}")
            for entry in payload["entries"]:
                print(f"- {entry['contract']}: {entry['current_version']} [{entry['status']}]")
        else:
            print(f"{payload['contract']} {payload['version']}: {payload['status']} - {payload['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
