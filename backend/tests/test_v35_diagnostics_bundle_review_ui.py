from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_diagnostics_bundle_review_ui_frontend_contract() -> None:
    app_source = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    api_source = (ROOT / "frontend" / "src" / "api.ts").read_text(encoding="utf-8")

    for token in [
        "Diagnostics Bundle Review UI",
        "Diagnostics Preview",
        "Included sections",
        "Excluded sections",
        "app summary",
        "project safe summary",
        "provider safe summary",
        "quality summary",
        "module status",
        "recent redacted errors",
        "redacted logs",
        ".env",
        "API key",
        "provider secrets",
        "raw env",
        "raw prompt/output",
        "hidden facts",
        "NPC secrets",
        "debug memory",
        "raw state_deltas",
        "mature/private",
        "database files",
        "Create Diagnostics Bundle",
        "I confirm debug bundle export",
        "ENABLE_DEBUG_API",
        "No upload was performed",
        "buildDiagnosticsSafePayloadPreview",
    ]:
        assert token in app_source

    assert "createDiagnosticsBundle" in api_source
    panel_source = app_source[
        app_source.index("function DiagnosticsBundlePanel") :
        app_source.index("function LocalConfigWizardPanel")
    ]
    assert "JSON.stringify(preview.safe_payload" not in panel_source
    assert "<pre>" not in panel_source
    assert "upload" in panel_source.lower()
    assert "confirmedDebug" in panel_source
