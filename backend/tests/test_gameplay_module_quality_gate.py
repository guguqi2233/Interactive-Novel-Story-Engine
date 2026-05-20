from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.quality.gameplay_module_quality import run_gameplay_module_quality_gate
from app.session_store import InMemorySessionStore
from app.tools import module_quality_gate as module_quality_gate_cli


def _write_module(
    tmp_path: Path,
    module_id: str = "pray_module",
    *,
    execute_code: bool = False,
    state_path: str = "module_state.pray_module.enabled",
    action_delta_path: str = "flags.prayed",
    hidden_leak: bool = False,
    migration_required: bool = False,
    migration_defaults: str = "{}",
    quality_tests: list[str] | None = None,
) -> Path:
    module_path = tmp_path / "gameplay_modules" / module_id
    module_path.joinpath("action_mods").mkdir(parents=True)
    tests = quality_tests or ["action_mod_validation", "hidden_leak_suite", "module_regression"]
    module_path.joinpath("gameplay_module.yaml").write_text(
        f"""
id: {module_id}
name: Pray Module
version: 0.1.0
module_type: action_pack
engine_version_min: 0.1.0
schema_version: "0.6"
provided_actions:
  - id: {module_id}.pray
    action_type: {module_id}.pray
provided_rules: []
state_schema_extensions:
  - path_prefix: {state_path}
    default_value: false
    migration_required: {str(migration_required).lower()}
    player_visible: false
event_types:
  - id: {module_id}.pray.resolved
    visible_to_player_by_default: true
    debug_only: false
permissions:
  execute_code: {str(execute_code).lower()}
  access_network: false
  access_filesystem: false
  call_llm: false
  modify_game_state_directly: false
save_compatibility:
  safe_to_add_mid_save: true
  migration_required: {str(migration_required).lower()}
  requires_new_game: false
  migration_defaults: {migration_defaults}
quality_tests: {tests}
""",
        encoding="utf-8",
    )
    hidden_fields = (
        """
        visible_facts: [sealed_secret]
        hidden_facts: [sealed_secret]
        hidden_outcome: true
    visibility_policy:
      hidden_outcome_player_visible: true
"""
        if hidden_leak
        else ""
    )
    module_path.joinpath("action_mods", "actions.yaml").write_text(
        f"""
actions:
  - id: {module_id}.pray
    label: Pray
    aliases: [pray]
    category: general
    outcomes:
      success:
        success_level: success
        reason: The module resolves this action through declarative rules.
        state_delta_templates:
          - operation: set
            path: {action_delta_path}
            value: true
{hidden_fields}
    event_type: {module_id}.pray.resolved
""",
        encoding="utf-8",
    )
    return module_path


def _client(tmp_path: Path) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "module_quality_api.db")
    app.state.gameplay_modules_root = str(tmp_path / "gameplay_modules")
    app.state.settings = Settings(enable_eval_api=True, enable_playtest_api=True, llm_provider="mock")
    return TestClient(app)


def test_valid_gameplay_module_quality_gate_passes(tmp_path: Path) -> None:
    _write_module(tmp_path)

    report = run_gameplay_module_quality_gate("pray_module", modules_root=tmp_path / "gameplay_modules")

    assert report.passed is True
    assert report.summary["executes_module_code"] is False
    assert {check.name: check.status for check in report.checks}["manifest_valid"] == "pass"
    assert "sealed_secret" not in str(report.model_dump_normal())


def test_execute_code_module_fails_quality_gate(tmp_path: Path) -> None:
    _write_module(tmp_path, execute_code=True)

    report = run_gameplay_module_quality_gate("pray_module", modules_root=tmp_path / "gameplay_modules")

    assert report.passed is False
    assert any(issue.safe_details["code"] == "gameplay_module_forbidden_permission" for issue in report.blockers)
    assert any(check.name == "no_execute_code" and check.status == "fail" for check in report.checks)


def test_forbidden_state_delta_path_fails_quality_gate(tmp_path: Path) -> None:
    _write_module(tmp_path, action_delta_path="player.hp")

    report = run_gameplay_module_quality_gate("pray_module", modules_root=tmp_path / "gameplay_modules")

    assert report.passed is False
    assert any(issue.safe_details["code"] == "action_mod_forbidden_state_delta_path" for issue in report.blockers)
    assert any(check.name == "no_forbidden_paths" and check.status == "fail" for check in report.checks)


def test_hidden_leak_fails_quality_gate_and_normal_report_is_redacted(tmp_path: Path) -> None:
    _write_module(tmp_path, hidden_leak=True)

    report = run_gameplay_module_quality_gate("pray_module", modules_root=tmp_path / "gameplay_modules")

    assert report.passed is False
    codes = {issue.safe_details["code"] for issue in report.blockers}
    assert "action_mod_hidden_output_visible" in codes
    assert "sealed_secret" not in str(report.model_dump_normal())
    assert any(check.name == "hidden_leak_suite_pass" and check.status == "fail" for check in report.checks)


def test_missing_migration_defaults_fails_quality_gate(tmp_path: Path) -> None:
    _write_module(tmp_path, migration_required=True, migration_defaults="{}")

    report = run_gameplay_module_quality_gate("pray_module", modules_root=tmp_path / "gameplay_modules")

    assert report.passed is False
    codes = {issue.safe_details["code"] for issue in report.blockers}
    assert "gameplay_module_missing_migration_defaults" in codes
    assert "action_mod_missing_migration_defaults" in codes


def test_gameplay_module_quality_gate_api_runs(tmp_path: Path) -> None:
    _write_module(tmp_path)
    client = _client(tmp_path)

    response = client.post("/quality/modules/pray_module/gate/run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module_id"] == "pray_module"
    assert payload["passed"] is True
    assert payload["summary"]["calls_real_llm"] is False


def test_gameplay_module_quality_gate_cli_runs(tmp_path: Path) -> None:
    _write_module(tmp_path)

    exit_code = module_quality_gate_cli.main(
        ["pray_module", "--modules-root", str(tmp_path / "gameplay_modules"), "--json"]
    )

    assert exit_code == 0
