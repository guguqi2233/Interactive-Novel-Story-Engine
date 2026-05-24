from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_provider_usage_cost_dashboard_pro_frontend_contract() -> None:
    app_source = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")

    for token in [
        "ProviderUsageCostDashboard",
        "Provider Usage / Cost Dashboard Pro",
        "Usage Overview",
        "By provider",
        "By model",
        "By mode",
        "By use case",
        "By success/error",
        "Estimated Tokens",
        "Estimated Cost",
        "Average Latency",
        "Error Count",
        "Full prompt/output text and secrets are excluded",
        "Prompts, outputs, API keys, hidden facts, mature/private text",
    ]:
        assert token in app_source

    assert "prompt_text" not in app_source
    assert "output_text" not in app_source
