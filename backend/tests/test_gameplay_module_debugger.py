from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.gameplay_module_debugger import ModuleActionDryRunRequest, dry_run_module_action
from app.main import app
from app.session_store import InMemorySessionStore


def _write_debug_module(tmp_path: Path, *, hidden_fact: str = "sealed_secret_truth") -> Path:
    module_path = tmp_path / "gameplay_modules" / "debug_pray"
    module_path.joinpath("action_mods").mkdir(parents=True)
    module_path.joinpath("gameplay_module.yaml").write_text(
        """
id: debug_pray
name: Debug Pray
version: 0.1.0
module_type: action_pack
engine_version_min: 0.1.0
schema_version: "0.6"
provided_actions:
  - id: debug.pray
    action_type: debug.pray
state_schema_extensions:
  - path_prefix: module_state.debug_pray.enabled
    default_value: false
event_types:
  - id: debug.pray.resolved
    visible_to_player_by_default: true
permissions:
  execute_code: false
  access_network: false
  access_filesystem: false
  call_llm: false
  modify_game_state_directly: false
quality_tests: [action_mod_validation, hidden_leak_suite, module_regression]
""",
        encoding="utf-8",
    )
    module_path.joinpath("action_mods", "actions.yaml").write_text(
        f"""
actions:
  - id: debug.pray
    label: Pray
    aliases: [pray]
    category: general
    target_specs:
      - kind: current_location
    outcomes:
      success:
        success_level: success
        reason: Debug action resolved.
        hidden_facts: [{hidden_fact}]
        state_delta_templates:
          - operation: set
            path: flags.debug_prayed
            value: true
    event_type: debug.pray.resolved
""",
        encoding="utf-8",
    )
    return module_path


def _client(tmp_path: Path, *, debug: bool = True) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "module_debugger.db")
    app.state.gameplay_modules_root = str(tmp_path / "gameplay_modules")
    app.state.settings = Settings(enable_debug_api=debug, llm_provider="mock")
    return TestClient(app)


def test_gameplay_module_debug_api_disabled_is_unavailable(tmp_path: Path) -> None:
    _write_debug_module(tmp_path)
    client = _client(tmp_path, debug=False)

    response = client.get("/debug/modules")

    assert response.status_code == 403


def test_gameplay_module_debug_lists_modules(tmp_path: Path) -> None:
    _write_debug_module(tmp_path)
    client = _client(tmp_path)

    response = client.get("/debug/modules")

    assert response.status_code == 200
    payload = response.json()
    assert payload["modules"][0]["module_id"] == "debug_pray"
    assert payload["modules"][0]["contains_api_key"] is False
    assert payload["modules"][0]["actions"][0]["state_delta_templates"] == ["flags.debug_prayed"]


def test_gameplay_module_action_dry_run_does_not_modify_state(tmp_path: Path) -> None:
    _write_debug_module(tmp_path)

    response = dry_run_module_action(
        "debug_pray",
        "debug.pray",
        ModuleActionDryRunRequest(input_text="pray"),
        modules_root=tmp_path / "gameplay_modules",
    )

    assert response.state_unchanged is True
    assert response.state_delta_preview[0].path == "flags.debug_prayed"
    assert response.event_preview["delta_count"] == 1


def test_gameplay_module_action_dry_run_redacts_hidden_facts(tmp_path: Path) -> None:
    _write_debug_module(tmp_path, hidden_fact="sealed_hidden_phrase")
    client = _client(tmp_path)

    response = client.post(
        "/debug/modules/debug_pray/actions/debug.pray/dry-run",
        json={"input_text": "pray"},
    )

    assert response.status_code == 200
    payload_text = response.text
    payload = response.json()
    assert payload["visibility_summary"]["hidden_fact_count"] == 1
    assert payload["hidden_facts_redacted"] is True
    assert "sealed_hidden_phrase" not in payload_text
