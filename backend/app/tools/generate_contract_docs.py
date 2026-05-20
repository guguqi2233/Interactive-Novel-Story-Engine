from __future__ import annotations

import argparse
from pathlib import Path

from app.compatibility.contracts import DEPRECATED_FIELDS
from app.compatibility.matrix import build_compatibility_matrix


DOCS_ROOT = Path("docs")


def render_contract_index() -> str:
    matrix = build_compatibility_matrix()
    lines = [
        "# Contract Index",
        "",
        "Generated from local schema constants. This document contains no raw env, API keys, hidden facts, or user data.",
        "",
        "## Stable Contracts",
    ]
    for entry in matrix.entries:
        lines.append(f"- `{entry.contract}`: `{entry.current_version}` ({entry.status})")
    lines.extend(["", "## Notes", "- v1.8 compatibility contracts are local-only and deterministic."])
    return "\n".join(lines) + "\n"


def render_schema_matrix() -> str:
    matrix = build_compatibility_matrix()
    lines = [
        "# Schema Version Matrix",
        "",
        f"- Engine version: `{matrix.engine_version}`",
        f"- GameState schema version: `{matrix.game_state_schema_version}`",
        f"- Save version: `{matrix.save_version}`",
        "",
        "| Contract | Current Version | Status |",
        "| --- | --- | --- |",
    ]
    for entry in matrix.entries:
        lines.append(f"| {entry.contract} | {entry.current_version} | {entry.status} |")
    return "\n".join(lines) + "\n"


def render_deprecated_fields() -> str:
    lines = [
        "# Deprecated Fields",
        "",
        "Deprecated fields must include replacement and migration metadata.",
        "",
        "| Field | Deprecated | Replacement | Migration Strategy |",
        "| --- | --- | --- | --- |",
    ]
    for field in DEPRECATED_FIELDS:
        lines.append(
            f"| `{field.field_path}` | `{field.deprecated_version}` | `{field.replacement}` | {field.migration_strategy} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic v1.8 contract docs.")
    parser.add_argument("--check", action="store_true", help="Render without writing files.")
    args = parser.parse_args()
    outputs = {
        "CONTRACT_INDEX.md": render_contract_index(),
        "SCHEMA_VERSION_MATRIX.md": render_schema_matrix(),
        "DEPRECATED_FIELDS.md": render_deprecated_fields(),
    }
    if args.check:
        for name, content in outputs.items():
            print(f"--- {name} ---")
            print(content, end="")
        return 0
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        (DOCS_ROOT / name).write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
