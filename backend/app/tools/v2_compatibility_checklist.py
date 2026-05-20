from __future__ import annotations

import argparse
import json
from pathlib import Path

from pydantic import BaseModel, Field


REQUIRED_CONTRACT_DOCS = [
    "COMPATIBILITY_BOUNDARY.md",
    "GAMESTATE_CONTRACT.md",
    "STATEDELTA_CONTRACT.md",
    "EVENTLOG_CONTRACT.md",
    "CONTENT_PACK_SCHEMA_CONTRACT.md",
    "SAVE_MIGRATION_CONTRACT.md",
    "MODULE_MANIFEST_CONTRACT.md",
    "ACTION_MOD_CONTRACT.md",
    "PROMPT_PROFILE_CONTRACT.md",
    "PROVIDER_GATEWAY_CONTRACT.md",
    "PACKAGE_CONTRACT.md",
    "AUTHORING_API_CONTRACT.md",
    "DEBUG_API_CONTRACT.md",
    "QUALITY_GATE_CONTRACT.md",
]


class CompatibilityChecklistItem(BaseModel):
    id: str
    passed: bool
    message: str


class CompatibilityChecklistResult(BaseModel):
    passed: bool
    items: list[CompatibilityChecklistItem] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


def run_checklist(docs_root: Path = Path("docs")) -> CompatibilityChecklistResult:
    items: list[CompatibilityChecklistItem] = []
    blockers: list[str] = []
    for doc_name in REQUIRED_CONTRACT_DOCS:
        exists = (docs_root / doc_name).exists()
        items.append(
            CompatibilityChecklistItem(
                id=f"doc:{doc_name}",
                passed=exists,
                message="present" if exists else "missing",
            )
        )
        if not exists:
            blockers.append(f"Missing contract doc: {doc_name}")
    return CompatibilityChecklistResult(passed=not blockers, items=items, blockers=blockers)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run v2.0 compatibility readiness checklist.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--docs-root", default="docs")
    args = parser.parse_args()
    result = run_checklist(Path(args.docs_root))
    payload = result.model_dump(mode="json")
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    else:
        print("PASS" if result.passed else "FAIL")
        for item in result.items:
            print(f"- {item.id}: {item.message}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
