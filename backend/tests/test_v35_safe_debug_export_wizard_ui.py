from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_safe_debug_export_wizard_frontend_contract() -> None:
    app_source = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")

    for token in [
        "SafeDebugExportWizard",
        "Safe Debug Export Wizard",
        "EventLog debug",
        "StateDelta debug",
        "visibility compare report",
        "module debug summary",
        "provider diagnostics safe summary",
        "ENABLE_DEBUG_API",
        "raw debug scope, explicit confirm required",
        "I explicitly confirm raw debug export",
        "Preview Debug Export",
        "Create Local Debug Export",
        "Redaction policy",
        "API key",
        "provider secrets",
        "raw env",
        "Authorization header",
        "No upload was performed",
    ]:
        assert token in app_source

    wizard_source = app_source[
        app_source.index("function SafeDebugExportWizard") :
        app_source.index("function LocalConfigWizardPanel")
    ]
    assert "debugEnabled" in wizard_source
    assert "confirmRawExport" in wizard_source
    assert "disabled={!canPreview}" in wizard_source
    assert "disabled={!canCreate}" in wizard_source
    assert "JSON.stringify" not in wizard_source
    assert "<pre>" not in wizard_source
    assert "upload" in wizard_source.lower()
