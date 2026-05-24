from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_cross_mode_conflict_review_pro_frontend_contract() -> None:
    app_source = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    api_source = (ROOT / "frontend" / "src" / "api.ts").read_text(encoding="utf-8")

    for token in [
        "CrossModeConflictReviewPro",
        "CrossMode Conflict Review Pro",
        "character identity",
        "timeline order",
        "relationship",
        "fact visibility",
        "stale link",
        "broken link",
        "proposal validation",
        "Mark reviewed",
        "Create fix draft",
        "Jump to source/target",
        "does not apply automatically",
        "do not bypass CrossMode validation",
        "Hidden target details",
    ]:
        assert token in app_source

    assert "affected_refs?: string[]" in api_source
    assert "apply_confirmed" not in app_source[app_source.index("function CrossModeConflictReviewPro"):app_source.index("function buildCrossModeConflictRows")]
    review_source = app_source[app_source.index("function CrossModeConflictReviewPro"):app_source.index("function buildCrossModeConflictRows")]
    assert "JSON.stringify" not in review_source
    assert "<pre>" not in review_source
