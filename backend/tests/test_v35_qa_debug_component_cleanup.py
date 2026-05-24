from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_v35_qa_debug_component_cleanup_contract() -> None:
    app_source = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")

    for token in [
        "SafeDebugNotice",
        "EventTypeBadge",
        "StateDeltaOpBadge",
        "QualitySeverityBadge",
        "LeakRiskBadge",
        "ProviderConnectionStatusBadge",
        "ModelCapabilityBadge",
        "TestRunStatusBadge",
        "RedactedValue",
        "SafeReportCard",
        "FilterToolbar",
        "<EventTypeBadge",
        "<StateDeltaOpBadge",
        "<LeakRiskBadge",
        "<ProviderConnectionStatusBadge",
        "<ModelCapabilityBadge",
        "<TestRunStatusBadge",
        "<SafeReportCard",
        "<FilterToolbar",
    ]:
        assert token in app_source

    component_source = app_source[
        app_source.index("function SafeDebugNotice") :
        app_source.index("function moduleRiskBadgeLevel")
    ]
    assert "JSON.stringify" not in component_source
    assert "<pre>" not in component_source
    assert "api_key" not in component_source.lower()

    normal_cleanup_slice = app_source[
        app_source.index("function LocalTestRunDashboard") :
        app_source.index("function LocalConfigWizardPanel")
    ]
    assert "child_process" not in normal_cleanup_slice
    assert "exec(" not in normal_cleanup_slice
    assert "spawn(" not in normal_cleanup_slice
