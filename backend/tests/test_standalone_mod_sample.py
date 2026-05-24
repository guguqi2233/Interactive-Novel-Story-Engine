from __future__ import annotations

import json
from pathlib import Path

from app.engine.action_mod_schema import ActionMod
from app.engine.action_mod_test_harness import ActionModTestHarness
from app.platform.module_browser import ModuleBrowserService
from app.quality.mod_quality_gate import run_mod_quality_gate


ROOT = Path(__file__).resolve().parents[2]
SAMPLE_ROOT = ROOT / "mods" / "sample_basic_action_mod"


def test_standalone_sample_basic_action_mod_is_browser_visible_and_quality_safe() -> None:
    browser = ModuleBrowserService(ROOT)
    modules = {module.package_id: module for module in browser.list_modules()}

    assert "sample_basic_action_mod" in modules
    summary = modules["sample_basic_action_mod"]
    assert summary.validation_status == "valid"
    assert summary.permission_risk_level == "low"
    assert not summary.errors
    assert not any("executable" in warning.lower() for warning in summary.warnings)

    gate = run_mod_quality_gate(ROOT, "sample_basic_action_mod")
    assert gate.ok
    assert gate.compatibility_status == "compatible"


def test_standalone_sample_basic_action_mod_harness_passes_without_mutating_state() -> None:
    action_mod = ActionMod.model_validate(json.loads((SAMPLE_ROOT / "action_mod.json").read_text(encoding="utf-8")))
    tests = ActionModTestHarness.load_test_cases(SAMPLE_ROOT / "tests" / "basic_check.test.json")
    report = ActionModTestHarness(action_mod).run_all_for_mod(tests)

    assert report.ok
    assert report.safe_summary["test_count"] == 1
    assert report.results[0].state_unchanged
