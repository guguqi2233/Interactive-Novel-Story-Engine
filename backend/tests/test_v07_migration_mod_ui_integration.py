import json
from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def _write_mod(
    tmp_path: Path,
    mod_id: str,
    *,
    dependencies: list[str] | None = None,
    conflicts: list[str] | None = None,
    version: str = "0.1.0",
    load_order_hint: int = 0,
) -> None:
    mod_path = tmp_path / "mods" / mod_id
    content_root = mod_path / "content"
    content_root.mkdir(parents=True)
    copytree(Path("worlds") / "mist_valley", content_root / "mist_valley")
    mod_path.joinpath("mod.yaml").write_text(
        f"""
id: {mod_id}
name: {mod_id}
version: {version}
engine_version_min: 0.5.0
content_schema_version: "0.6"
dependencies: {dependencies or []}
optional_dependencies: []
conflicts: {conflicts or []}
load_order_hint: {load_order_hint}
compatible_worlds:
  - mist_valley
migration_notes: "Review saves before enabling this local content pack."
entry_worlds:
  - mist_valley
content_paths:
  - content
author: Local Tester
description: Local content-only mod.
""",
        encoding="utf-8",
    )


def _make_client(tmp_path: Path) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    _write_mod(tmp_path, "base_mod", version="0.1.0", load_order_hint=0)
    _write_mod(tmp_path, "addon_mod", dependencies=["base_mod"], version="0.2.0", load_order_hint=1)
    _write_mod(tmp_path, "conflict_mod", conflicts=["addon_mod"], version="0.1.0", load_order_hint=2)

    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v07_migration_mod.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = tmp_path / "mods"
    app.state.settings = Settings(
        enable_authoring_api=True,
        enable_debug_api=False,
        llm_provider="mock",
        llm_api_key="super-secret-test-key",
    )
    return TestClient(app)


def _make_legacy_modded_save(client: TestClient, tmp_path: Path) -> str:
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]
    repository = app.state.save_repository
    save = repository.get_save(save_id)
    state_payload = json.loads(save.state_json)
    state_payload.pop("schema_version", None)
    with repository._connect() as connection:  # noqa: SLF001 - test fixture setup
        connection.execute(
            """
            UPDATE save_games
            SET state_json = ?,
                schema_version = 'legacy',
                engine_version = 'legacy',
                enabled_mods = ?
            WHERE save_id = ?
            """,
            (
                json.dumps(state_payload, ensure_ascii=False, sort_keys=True),
                json.dumps([{"id": "base_mod", "version": "0.0.1"}], sort_keys=True),
                save_id,
            ),
        )
    return save_id


def test_save_migration_ui_backend_flow_with_mod_version_warning(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    save_id = _make_legacy_modded_save(client, tmp_path)

    status_response = client.get(f"/game/saves/{save_id}/migration-status")
    dry_run_response = client.post(f"/game/saves/{save_id}/migrate-dry-run")
    pre_apply_summary = client.get("/game/saves").json()["saves"][0]
    apply_response = client.post(f"/game/saves/{save_id}/migrate")
    post_apply_status = client.get(f"/saves/{save_id}/migration-status")
    post_apply_summary = client.get("/game/saves").json()["saves"][0]

    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["needs_migration"] is True
    assert status_payload["migration_path"] == ["legacy->0.6"]
    assert any("version mismatch" in warning for warning in status_payload["warnings"])
    assert "state_json" not in str(status_payload)
    assert "state_deltas" not in str(status_payload)
    assert "super-secret-test-key" not in str(status_payload)

    assert dry_run_response.status_code == 200
    dry_run_payload = dry_run_response.json()
    assert dry_run_payload["dry_run"] is True
    assert dry_run_payload["applied_migrations"][0]["migration_id"] == "legacy->0.6"
    assert pre_apply_summary["enabled_mods"] == {"base_mod": "0.0.1"}

    assert apply_response.status_code == 200
    apply_payload = apply_response.json()
    assert apply_payload["dry_run"] is False
    assert apply_payload["backup_save_id"] == f"{save_id}.backup"
    assert apply_payload["applied_migrations"][0]["migration_id"] == "legacy->0.6"
    assert post_apply_status.json()["needs_migration"] is False
    assert post_apply_summary["save_id"] == save_id
    assert post_apply_summary["enabled_mods"] == {"base_mod": "0.0.1"}
    assert "sealed_letter_under_stone" not in str(post_apply_summary)


def test_mod_manager_api_flow_lists_dependencies_conflicts_and_load_order(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    list_response = client.get("/authoring/mods")
    addon_detail_response = client.get("/authoring/mods/addon_mod")
    conflict_detail_response = client.get("/authoring/mods/conflict_mod")
    addon_validation_response = client.post("/authoring/mods/addon_mod/validate")
    load_order_response = client.get("/authoring/mods/load-order")

    assert list_response.status_code == 200
    mods = {mod["id"]: mod for mod in list_response.json()["mods"]}
    assert mods["addon_mod"]["dependencies"] == ["base_mod"]
    assert mods["conflict_mod"]["conflicts"] == ["addon_mod"]
    assert mods["base_mod"]["compatible_worlds"] == ["mist_valley"]

    assert addon_detail_response.status_code == 200
    assert addon_detail_response.json()["mod"]["dependencies"] == ["base_mod"]
    assert conflict_detail_response.status_code == 200
    assert conflict_detail_response.json()["mod"]["conflicts"] == ["addon_mod"]
    assert addon_validation_response.status_code == 200
    assert addon_validation_response.json()["ok"] is True
    assert load_order_response.status_code == 200
    assert load_order_response.json()["load_order"].index("base_mod") < load_order_response.json()["load_order"].index("addon_mod")
    assert "super-secret-test-key" not in str(list_response.json())


def test_mod_manager_authoring_disabled_fallback(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    app.state.settings = Settings(enable_authoring_api=False, llm_provider="mock")

    list_response = client.get("/authoring/mods")
    load_order_response = client.get("/authoring/mods/load-order")

    assert list_response.status_code == 403
    assert load_order_response.status_code == 403
    assert list_response.json()["detail"] == "Authoring API is disabled"


def test_frontend_migration_and_mod_manager_ui_contracts() -> None:
    app_source = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    api_source = Path("frontend/src/api.ts").read_text(encoding="utf-8")

    assert "Migration needed" in app_source
    assert "Dry-run is safe and does not write the database" in app_source
    assert "Apply migration to this save?" in app_source
    assert "Migration history" in app_source
    assert "Dependencies" in app_source
    assert "Conflicts" in app_source
    assert "Mod Manager uses the local authoring API" in app_source
    assert "/saves/${encodeURIComponent(saveId)}/migration-status" in api_source
    assert "/saves/${encodeURIComponent(saveId)}/migrate-dry-run" in api_source
    assert "/saves/${encodeURIComponent(saveId)}/migrate" in api_source
    assert "/authoring/mods/load-order" in api_source
