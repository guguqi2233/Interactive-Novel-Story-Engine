from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "app.tools.prompt_lab", *args],
        cwd=Path.cwd() / "backend",
        text=True,
        capture_output=True,
        check=False,
    )


def test_prompt_lab_cli_help() -> None:
    result = _run(["--help"])

    assert result.returncode == 0
    assert "benchmark-provider" in result.stdout


def test_mock_benchmark_cli_json() -> None:
    result = _run(["--json", "benchmark-provider", "--provider", "fake", "--benchmark", "generate_text_smoke"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["provider_id"] == "fake"
    assert "sk-" not in result.stdout


def test_structured_output_cli_json() -> None:
    result = _run(["--json", "structured-output", "--provider", "fake", "--schema", "PlayerIntent"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["total_cases"] == 1


def test_prompt_regression_cli_json() -> None:
    result = _run(["--json", "prompt-regression", "--case", "intent_parser_schema"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["pass_fail"] == "pass"


def test_local_diagnostics_fake_mode_cli_json() -> None:
    result = _run(["--json", "local-diagnostics", "--provider", "local_stub", "--fake-mode", "ok"])

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["provider_id"] == "local_stub"


def test_real_provider_without_allow_is_blocked() -> None:
    result = _run(["--json", "benchmark-provider", "--provider", "openai", "--benchmark", "generate_text_smoke"])

    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["real_provider_blocked"] is True


def test_compatibility_and_token_budget_cli() -> None:
    matrix = _run(["--json", "compatibility-matrix"])
    budget = _run(["--json", "token-budget-report", "--max-total-tokens", "500"])

    assert matrix.returncode == 0
    assert json.loads(matrix.stdout)["rows"]
    assert budget.returncode == 0
    assert json.loads(budget.stdout)["final_context_tokens"] <= 500
