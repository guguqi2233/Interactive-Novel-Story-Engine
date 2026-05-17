import base64
import json
from io import BytesIO
from pathlib import Path
from shutil import copytree
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.config import Settings
from app.core.instrumentation import get_performance_recorder, set_performance_logging_enabled
from app.db.repository import SQLiteSaveRepository
from app.engine.content.scenario_templates import ScenarioTemplateRenderer
from app.llm.local_provider import LocalHTTPProvider
from app.llm.provider_base import LLMProviderError
from app.llm.provider_factory import create_llm_provider
from app.main import app
from app.session_store import InMemorySessionStore


class _LocalJSONSchema(BaseModel):
    intent_type: str
    confidence: float


def _make_client(
    tmp_path: Path,
    *,
    authoring_enabled: bool = True,
    debug_enabled: bool = True,
    perf_enabled: bool = True,
    playtest_enabled: bool = True,
    eval_enabled: bool = True,
) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    mods_root = tmp_path / "mods"
    _write_mod(mods_root, "base_mod")
    _write_mod(mods_root, "addon_mod", dependencies=["base_mod"])
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v07_integration.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = mods_root
    app.state.narrative_eval_reports = []
    app.state.playtest_reports = []
    app.state.scenario_template_renderer = ScenarioTemplateRenderer(
        templates_root=Path("templates"),
        worlds_root=worlds_root,
    )
    app.state.settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'private_settings.db'}",
        enable_authoring_api=authoring_enabled,
        enable_debug_api=debug_enabled,
        enable_perf_logging=perf_enabled,
        enable_playtest_api=playtest_enabled,
        enable_eval_api=eval_enabled,
        llm_provider="mock",
        llm_api_key="test-secret-placeholder",
    )
    set_performance_logging_enabled(perf_enabled)
    get_performance_recorder().clear()
    return TestClient(app)


def test_v07_studio_status_settings_eval_and_performance_are_safe(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    studio_response = client.get("/studio/status")
    config_response = client.get("/studio/config-summary")
    eval_response = client.post("/evals/narrative/run")
    eval_recent_response = client.get("/evals/narrative/recent")
    perf_response = client.get("/debug/performance/summary")

    assert studio_response.status_code == 200
    studio_payload = studio_response.json()
    assert studio_payload["engine_version"]
    assert studio_payload["worlds_count"] == 1
    assert studio_payload["authoring_api_enabled"] is True
    assert studio_payload["debug_api_enabled"] is True
    assert "test-secret-placeholder" not in studio_response.text
    assert "state_json" not in studio_response.text

    assert config_response.status_code == 200
    config_payload = config_response.json()
    assert config_payload["llm_provider"] == "mock"
    assert config_payload["api_key_configured"] is True
    assert config_payload["database_path_hint"] == "sqlite local file: private_settings.db"
    assert "DATABASE_URL" not in config_response.text
    assert "LLM_API_KEY" not in config_response.text
    assert "test-secret-placeholder" not in config_response.text
    assert str(tmp_path) not in config_response.text

    assert eval_response.status_code == 200
    assert eval_response.json()["total_cases"] >= 1
    assert eval_response.json()["case_results"]
    assert eval_recent_response.status_code == 200
    assert "test-secret-placeholder" not in eval_recent_response.text

    assert perf_response.status_code == 200
    assert "test-secret-placeholder" not in perf_response.text
    assert "prompt" not in perf_response.text.lower()
    assert "hidden_cache" not in perf_response.text


def test_v07_migration_mod_authoring_import_export_and_playtest_flow(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    session_response = client.post("/game/start", json={"world_id": "mist_valley"})
    session_id = session_response.json()["session_id"]
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]

    migration_response = client.get(f"/saves/{save_id}/migration-status")
    dry_run_response = client.post(f"/saves/{save_id}/migrate-dry-run")
    mod_list_response = client.get("/authoring/mods")
    mod_load_order_response = client.get("/authoring/mods/load-order")
    playtest_response = client.post(
        "/playtests/run",
        json={
            "world_id": "mist_valley",
            "agent_type": "random_valid_action_agent",
            "steps": 3,
            "seed": 7,
            "save_load_check": True,
        },
    )
    export_response = client.get("/authoring/export/worlds/mist_valley")
    exported_archive = export_response.json()["archive_base64"]
    app.state.worlds_root = tmp_path / "imported_worlds"
    import_response = client.post("/authoring/import/worlds", json={"archive_base64": exported_archive})

    assert migration_response.status_code == 200
    assert migration_response.json()["needs_migration"] is False
    assert "state_json" not in migration_response.text
    assert "state_deltas" not in migration_response.text
    assert dry_run_response.status_code == 200
    assert dry_run_response.json()["dry_run"] is True
    assert mod_list_response.status_code == 200
    assert [mod["id"] for mod in mod_list_response.json()["mods"]] == ["addon_mod", "base_mod"]
    assert mod_load_order_response.status_code == 200
    assert mod_load_order_response.json()["load_order"] == ["base_mod", "addon_mod"]
    assert playtest_response.status_code == 200
    playtest_payload = playtest_response.json()
    assert playtest_payload["turns_run"] == 3
    assert all(action["event_id"] for action in playtest_payload["actions_taken"])
    assert playtest_payload["save_load_failures"] == []
    assert export_response.status_code == 200
    assert import_response.status_code == 200
    assert import_response.json()["imported"] is True
    assert "test-secret-placeholder" not in (
        migration_response.text + mod_list_response.text + playtest_response.text + import_response.text
    )


def test_v07_authoring_templates_and_quest_graph_do_not_touch_active_state(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    before_state = client.get(f"/game/state/{session_id}").json()

    template_response = client.post(
        "/authoring/templates/basic_village_world/preview",
        json={
            "variables": {
                "world_id": "integration_village",
                "world_name": "Integration Village",
                "start_location_id": "green",
                "npc_id": "mira",
                "npc_name": "Mira",
            }
        },
    )
    graph_response = client.get("/authoring/worlds/mist_valley/quests/graph")
    graph_payload = graph_response.json()
    graph_payload["quests"][0]["stages"][0]["title"] = "Integration Preview Title"
    graph_preview_response = client.post(
        "/authoring/worlds/mist_valley/quests/graph/preview",
        json={"graph": graph_payload},
    )
    invalid_graph = graph_response.json()
    invalid_graph["quests"][0]["stages"][0]["next_stages"] = ["missing_stage"]
    invalid_preview_response = client.post(
        "/authoring/worlds/mist_valley/quests/graph/preview",
        json={"graph": invalid_graph},
    )
    after_state = client.get(f"/game/state/{session_id}").json()

    assert template_response.status_code == 200
    assert template_response.json()["writes_to_disk"] is False
    assert template_response.json()["validation_report"]["ok"] is True
    assert graph_response.status_code == 200
    assert graph_preview_response.status_code == 200
    assert graph_preview_response.json()["validation"]["ok"] is True
    assert "Integration Preview Title" in graph_preview_response.json()["yaml_content"]
    assert invalid_preview_response.status_code == 200
    assert invalid_preview_response.json()["validation"]["ok"] is False
    assert before_state == after_state


def test_v07_import_export_rejects_unsafe_archives(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    zip_slip_archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "bad_world"},
            "../escape.txt": "nope",
        }
    )
    executable_archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "bad_world"},
            "worlds/bad_world/manifest.yaml": "world_id: bad_world\nname: Bad\n",
            "worlds/bad_world/evil.py": "print('no')\n",
        }
    )
    env_archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "bad_world"},
            "worlds/bad_world/manifest.yaml": "world_id: bad_world\nname: Bad\n",
            "worlds/bad_world/.env": "LLM_API_KEY=test-secret-placeholder\n",
        }
    )

    zip_slip_response = client.post("/authoring/import/worlds", json={"archive_base64": zip_slip_archive})
    executable_response = client.post("/authoring/import/worlds", json={"archive_base64": executable_archive})
    env_response = client.post("/authoring/import/worlds", json={"archive_base64": env_archive})

    assert zip_slip_response.status_code == 400
    assert "Unsafe archive path" in zip_slip_response.json()["detail"]
    assert executable_response.status_code == 400
    assert "executable code" in executable_response.json()["detail"]
    assert env_response.status_code == 400
    assert "sensitive file" in env_response.json()["detail"]
    assert "test-secret-placeholder" not in env_response.text


def test_v07_local_provider_full_integration_uses_fake_transport_only() -> None:
    requests: list[tuple[str, dict[str, object], float]] = []

    def fake_transport(url: str, payload: dict[str, object], timeout: float) -> dict[str, object]:
        requests.append((url, payload, timeout))
        if payload.get("response_format"):
            return {"choices": [{"message": {"content": '{"intent_type": "observe", "confidence": 0.75}'}}]}
        return {"choices": [{"message": {"content": "local text"}}]}

    provider = LocalHTTPProvider(
        settings=Settings(
            llm_provider="local_http",
            local_llm_base_url="http://localhost:9999",
            local_llm_model="fake-local",
            local_llm_timeout_seconds=2.5,
            local_llm_json_mode=True,
        ),
        transport=fake_transport,
    )

    assert provider.generate_text([{"role": "user", "content": "hello"}]) == "local text"
    assert provider.generate_json([{"role": "user", "content": "look"}], _LocalJSONSchema) == _LocalJSONSchema(
        intent_type="observe",
        confidence=0.75,
    )
    assert requests[0][0] == "http://localhost:9999/chat/completions"
    assert requests[0][2] == 2.5
    try:
        create_llm_provider(Settings(llm_provider="local_http", local_llm_base_url=None))
    except LLMProviderError as exc:
        assert "LOCAL_LLM_BASE_URL is required" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("local_http without base URL should fail clearly")


def test_v07_frontend_dashboard_contracts_do_not_mix_debug_into_player_ui() -> None:
    app_source = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    api_source = Path("frontend/src/api.ts").read_text(encoding="utf-8")

    assert "Settings / Local Privacy" in app_source
    assert "fetchStudioConfigSummary" in app_source
    assert "NarrativeQualityDashboard" in app_source
    assert "PerformanceDashboard" in app_source
    assert "PlaytestingDashboard" in app_source
    assert "Export Bundle" in app_source
    assert "Export World" in app_source
    assert "Export Mod" in app_source
    assert "Dashboard data is a safe local summary" in app_source
    assert "/studio/config-summary" in api_source
    assert "/playtests/run" in api_source
    assert "/authoring/import/worlds" in api_source
    assert "/authoring/export/saves" in api_source


def _write_mod(mods_root: Path, mod_id: str, *, dependencies: list[str] | None = None) -> None:
    mod_path = mods_root / mod_id
    content_root = mod_path / "content"
    content_root.mkdir(parents=True)
    copytree(Path("worlds") / "mist_valley", content_root / "mist_valley")
    mod_path.joinpath("mod.yaml").write_text(
        f"""
id: {mod_id}
name: {mod_id}
version: 0.1.0
engine_version_min: 0.6.0
content_schema_version: "0.6"
dependencies: {dependencies or []}
optional_dependencies: []
conflicts: []
load_order_hint: 0
compatible_worlds:
  - mist_valley
migration_notes: ""
entry_worlds:
  - mist_valley
content_paths:
  - content
author: Local Tester
description: Integration mod.
""",
        encoding="utf-8",
    )


def _archive_b64(files: dict[str, str | dict[str, object]]) -> str:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, json.dumps(content) if isinstance(content, dict) else content)
    return base64.b64encode(buffer.getvalue()).decode("ascii")
