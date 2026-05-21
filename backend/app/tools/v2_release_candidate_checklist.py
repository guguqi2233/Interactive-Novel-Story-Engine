from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.tools.v2_compatibility_checklist import run_checklist as run_v2_compatibility_checklist


REQUIRED_RC_DOCS = [
    "V2_0_RELEASE_CANDIDATE_CHECKLIST.md",
    "V2_0_COMPATIBILITY_CHECKLIST.md",
    "V1_9_ACCEPTANCE_REPORT.md",
    "V1_9_RELEASE_NOTES.md",
    "V1_9_SECURITY_AUDIT.md",
    "RELEASE_CANDIDATE_BOUNDARY.md",
]


class V2ReleaseCandidateChecklistItem(BaseModel):
    id: str
    passed: bool
    message: str


class V2ReleaseCandidateChecklistResult(BaseModel):
    passed: bool
    local_only: bool = True
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    items: list[V2ReleaseCandidateChecklistItem] = Field(default_factory=list)

    def model_dump_safe(self) -> dict:
        return self.model_dump(mode="json")


def run_rc_checklist(docs_root: Path = Path("docs")) -> V2ReleaseCandidateChecklistResult:
    items: list[V2ReleaseCandidateChecklistItem] = []
    blockers: list[str] = []
    for doc in REQUIRED_RC_DOCS:
        exists = (docs_root / doc).exists()
        items.append(V2ReleaseCandidateChecklistItem(id=f"doc:{doc}", passed=exists, message="present" if exists else "missing"))
        if not exists:
            blockers.append(f"Missing RC doc: {doc}")

    compatibility = run_v2_compatibility_checklist(docs_root)
    items.append(
        V2ReleaseCandidateChecklistItem(
            id="v2_compatibility_checklist",
            passed=compatibility.passed,
            message="pass" if compatibility.passed else "fail",
        )
    )
    blockers.extend(compatibility.blockers)
    return V2ReleaseCandidateChecklistResult(passed=not blockers, blockers=blockers, items=items)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run v2.0 release candidate readiness checklist.")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = run_rc_checklist(Path(args.docs_root))
    if args.json:
        print(json.dumps(result.model_dump_safe(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("PASS" if result.passed else "FAIL")
        for item in result.items:
            print(f"- {item.id}: {item.message}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
