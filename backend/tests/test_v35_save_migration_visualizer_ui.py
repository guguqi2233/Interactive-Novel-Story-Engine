from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_save_migration_visualizer_frontend_contract() -> None:
    app_source = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")

    for token in [
        "Save Migration Visualizer",
        "schema version",
        "Migration needed",
        "Dry-run",
        "Migration plan",
        "Affected fields",
        "Module state migration",
        "Destructive blocked",
        "explicit confirm",
        "Raw save JSON",
        "hidden facts",
        "API keys",
        "Destructive remove blocked by default",
        "buildSaveMigrationPlanRows",
        "buildSaveModuleMigrationRows",
        "buildDestructiveMigrationBlockers",
    ]:
        assert token in app_source

    visualizer_source = app_source[
        app_source.index("function MigrationPanel") :
        app_source.index("function lastMigratedAt")
    ]
    assert "JSON.stringify" not in visualizer_source
    assert "<pre>" not in visualizer_source
    assert "state_json" not in visualizer_source
    assert "raw save JSON" not in visualizer_source.lower().replace("raw save json", "")
