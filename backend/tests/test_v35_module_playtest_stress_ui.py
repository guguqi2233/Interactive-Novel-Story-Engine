from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_module_playtest_stress_ui_pro_frontend_contract() -> None:
    app_source = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")

    for token in [
        "ModulePlaytestStressProPanel",
        "Module Playtest / Stress UI Pro",
        "module playtest suites",
        "Run Selected Module Playtest",
        "Run Compatibility Stress",
        "Run Module Quality Gate",
        "Pass / fail",
        "Failed step",
        "Action coverage",
        "State namespace conflicts",
        "Migration conflicts",
        "Hidden leak warnings",
        "No arbitrary code execution",
        "No package code was executed",
        "No hidden text full content is shown",
        "Raw StateDelta payloads are not rendered",
    ]:
        assert token in app_source

    panel_source = app_source[
        app_source.index("function ModulePlaytestStressProPanel") :
        app_source.index("function RuleModuleContractPanel")
    ]
    assert "JSON.stringify" not in panel_source
    assert "<pre>" not in panel_source
    assert "Raw StateDelta payloads are not rendered" in panel_source
    assert "state_delta_preview:" not in panel_source
    assert "exec(" not in panel_source
    assert "eval(" not in panel_source
