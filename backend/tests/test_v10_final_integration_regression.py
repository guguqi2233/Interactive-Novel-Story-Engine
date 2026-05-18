import base64
import json
from io import BytesIO
from pathlib import Path
from random import Random
from shutil import copytree
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import EventLog
from app.core.game_loop import GameLoop
from app.core.world_state import FactState, GameState, LocationState, NPCState, PlayerState, WorldObjectState, load_game_state_payload
from app.db.migration_service import MigrationService
from app.db.repository import SQLiteSaveRepository
from app.engine.action_dispatcher import ActionDispatcher
from app.engine.content.mod_loader import ModLoader
from app.engine.content.scenario_templates import ScenarioTemplateRenderer
from app.engine.content.validator import validate_world_pack
from app.llm.fake_provider import FakeLLMProvider
from app.llm.intent_parser import IntentParser
from app.llm.narrator import Narrator
from app.main import app
from app.playtesting.batch import PlaytestBatchRunRequest, run_playtest_batch
from app.quality.benchmarks import BenchmarkRunRequest, run_benchmark_suite
from app.quality.gate import QualityGateConfig, QualityGateProfile, run_quality_gate
from app.scenarios.regression import sample_scenario_regression_cases, run_scenario_regression_suite
from app.session_store import InMemorySessionStore, build_visible_state


@pytest.fixture()
def final_client(tmp_path: Path):
    original_state = {
        name: getattr(app.state, name, None)
        for name in (
            "settings",
            "session_store",
            "save_repository",
            "worlds_root",
            "mods_root",
            "scenario_template_renderer",
            "playtest_batch_reports",
            "quality_gate_results",
            "benchmark_reports",
        )
    }
    original_has = {name: hasattr(app.state, name) for name in original_state}
    worlds_root = tmp_path / "worlds"
    mods_root = tmp_path / "mods"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    _write_valid_mod(mods_root)
    app.state.session_store = InMemorySessionStore(worlds_root=str(worlds_root))
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v10_final.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = mods_root
    app.state.scenario_template_renderer = ScenarioTemplateRenderer(Path("templates"), worlds_root)
    app.state.playtest_batch_reports = []
    app.state.quality_gate_results = []
    app.state.benchmark_reports = []
    app.state.settings = Settings(
        enable_authoring_api=True,
        enable_debug_api=True,
        enable_eval_api=True,
        enable_playtest_api=True,
        enable_perf_logging=True,
        llm_provider="local_stub",
        llm_api_key="test-api-key-placeholder",
    )
    try:
        yield TestClient(app), tmp_path
    finally:
        for name, value in original_state.items():
            if original_has[name]:
                setattr(app.state, name, value)
            elif hasattr(app.state, name):
                delattr(app.state, name)


def test_v10_final_core_game_loop_records_events_deltas_and_keeps_visibility_safe() -> None:
    game_loop = _make_final_game_loop()
    for player_input in ["observe", "go smithy", "talk harlan", "search", "use charm", "wait"]:
        game_loop.step(player_input)

    events = game_loop.event_log.list_events()
    visible = build_visible_state(game_loop.state).model_dump(mode="json")
    serialized_visible = json.dumps(visible, ensure_ascii=False).lower()

    assert [event.action_type for event in events] == ["observe", "move", "talk", "search", "use_item", "wait"]
    assert game_loop.state.turn == 6
    assert game_loop.state.player.location_id == "blacksmith"
    assert all(event.visible_to_player for event in events)
    assert all(event.state_deltas for event in events)
    assert all(delta.path for event in events for delta in event.state_deltas)
    assert "hidden_truth" not in serialized_visible
    assert "state_deltas" not in serialized_visible
    assert all("Mock narrative" in event.narrative_text for event in events)


def test_v10_final_save_migration_contract_preserves_dry_run_history_and_failure_safety(final_client) -> None:
    client, _tmp_path = final_client
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]
    repository: SQLiteSaveRepository = app.state.save_repository
    _force_legacy_save(repository, save_id)

    before_dry_run = repository.get_save(save_id)
    dry_run = client.post(f"/saves/{save_id}/migrate-dry-run")
    after_dry_run = repository.get_save(save_id)
    apply = client.post(f"/saves/{save_id}/migrate")
    migrated = repository.get_save(save_id)

    assert dry_run.status_code == 200
    assert dry_run.json()["dry_run"] is True
    assert after_dry_run.schema_version == before_dry_run.schema_version == "legacy"
    assert after_dry_run.state_json == before_dry_run.state_json
    assert apply.status_code == 200
    assert apply.json()["dry_run"] is False
    assert "legacy->0.6" in migrated.migration_history

    corrupt_id = "corrupt-save"
    repository.save_snapshot(corrupt_id, load_game_state_payload(json.loads(migrated.state_json)), [])
    with repository._connect() as connection:  # noqa: SLF001 - fixture corruption for failure-safety check
        connection.execute(
            "UPDATE save_games SET state_json = ?, schema_version = 'legacy' WHERE save_id = ?",
            ("{not-json", corrupt_id),
        )
    before_failure = repository.get_save(corrupt_id)
    failure = client.post(f"/saves/{corrupt_id}/migrate")
    after_failure = repository.get_save(corrupt_id)

    assert failure.status_code == 400
    assert after_failure.state_json == before_failure.state_json
    assert after_failure.schema_version == "legacy"


def test_v10_final_content_pack_templates_and_validation_fixtures(final_client, tmp_path: Path) -> None:
    client, workspace = final_client
    worlds_root = workspace / "worlds"

    report = validate_world_pack("mist_valley", worlds_root=worlds_root)
    assert report.ok

    renderer = ScenarioTemplateRenderer(Path("templates"), worlds_root)
    for template in renderer.list_templates():
        variables = (
            {
                "world_id": "template_contract_world",
                "world_name": "Template Contract World",
                "start_location_id": "square",
                "npc_id": "mara",
                "npc_name": "Mara",
            }
            if template.template_type == "world"
            else {}
        )
        target_world_id = None if template.template_type == "world" else "mist_valley"
        preview = renderer.preview_template(template.id, variables, target_world_id=target_world_id)
        assert preview.writes_to_disk is False
        assert preview.validation_report is not None
        assert preview.validation_report.ok, template.id

    bad_world = tmp_path / "bad_worlds" / "bad_schema"
    copytree(worlds_root / "mist_valley", bad_world)
    (bad_world / "items.yaml").write_text(
        """
items:
  - id: conflicting
    name: Conflicting
    description: Bad placement.
    location_id: village_square
    owner_id: player
""".strip(),
        encoding="utf-8",
    )
    manifest = (bad_world / "manifest.yaml").read_text(encoding="utf-8").replace("world_id: mist_valley", "world_id: bad_schema")
    (bad_world / "manifest.yaml").write_text(manifest, encoding="utf-8")
    invalid_report = validate_world_pack("bad_schema", worlds_root=tmp_path / "bad_worlds")
    assert any(issue.code == "item_conflicting_ownership" for issue in invalid_report.errors)

    leak_world = tmp_path / "leak_worlds" / "leak"
    copytree(worlds_root / "mist_valley", leak_world)
    manifest = (leak_world / "manifest.yaml").read_text(encoding="utf-8").replace("world_id: mist_valley", "world_id: leak")
    (leak_world / "manifest.yaml").write_text(manifest, encoding="utf-8")
    (leak_world / "facts.yaml").write_text(
        (leak_world / "facts.yaml").read_text(encoding="utf-8")
        + "\n  - id: hidden_test_truth\n    text: Secret hidden test truth.\n    visibility: hidden\n    known_by: [harlan]\n",
        encoding="utf-8",
    )
    (leak_world / "rumors.yaml").write_text(
        (leak_world / "rumors.yaml").read_text(encoding="utf-8")
        + "\n  - id: hidden_test_rumor\n    fact_id: hidden_test_truth\n    text_for_player: Secret hidden test truth.\n",
        encoding="utf-8",
    )
    leak_report = validate_world_pack("leak", worlds_root=tmp_path / "leak_worlds")
    assert any(issue.code == "rumor_reveals_hidden_fact" for issue in leak_report.warnings)
    assert client.get("/authoring/worlds").status_code == 200


def test_v10_final_authoring_editors_preview_validate_and_do_not_touch_active_state(final_client) -> None:
    client, _workspace = final_client
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    before_state = client.get(f"/game/state/{session_id}").json()

    map_graph = client.get("/authoring/worlds/mist_valley/map").json()["graph"]
    assert client.post("/authoring/worlds/mist_valley/map/preview", json={"graph": map_graph}).json()["validation"]["ok"] is True
    assert client.put("/authoring/worlds/mist_valley/map", json={"graph": map_graph}).json()["validation"]["ok"] is True

    quest_graph = client.get("/authoring/worlds/mist_valley/quests/graph").json()
    assert client.post("/authoring/worlds/mist_valley/quests/graph/preview", json={"graph": quest_graph}).json()["validation"]["ok"] is True
    bad_quest = json.loads(json.dumps(quest_graph))
    bad_quest["quests"][0]["stages"][0]["next_stages"] = ["missing_stage"]
    assert client.put("/authoring/worlds/mist_valley/quests/graph", json={"graph": bad_quest}).json()["validation"]["ok"] is False

    npc_graph = client.get("/authoring/worlds/mist_valley/npcs/goals").json()
    social_graph = client.get("/authoring/worlds/mist_valley/social/graph").json()
    economy_graph = client.get("/authoring/worlds/mist_valley/economy").json()
    rumor_graph = client.get("/authoring/worlds/mist_valley/rumor-crime").json()
    assert client.post("/authoring/worlds/mist_valley/npcs/goals/preview", json={"graph": npc_graph}).status_code == 200
    assert client.post("/authoring/worlds/mist_valley/social/graph/preview", json={"graph": social_graph}).status_code == 200
    assert client.post("/authoring/worlds/mist_valley/economy/preview", json={"graph": economy_graph}).status_code == 200
    assert client.post("/authoring/worlds/mist_valley/rumor-crime/preview", json={"graph": rumor_graph}).status_code == 200
    assert client.get(f"/game/state/{session_id}").json() == before_state

    app.state.settings = Settings(enable_authoring_api=False, enable_debug_api=False, llm_provider="local_stub")
    assert client.get("/authoring/worlds").status_code == 403


def test_v10_final_quality_playtest_scenario_and_benchmark_smoke_are_safe(final_client) -> None:
    _client, workspace = final_client
    quality = run_quality_gate(
        "mist_valley",
        QualityGateConfig(profile=QualityGateProfile.STANDARD, min_health_score=0),
        worlds_root=str(workspace / "worlds"),
        mods_root=str(workspace / "mods"),
    )
    scenarios = [case for case in sample_scenario_regression_cases() if case.world_id == "mist_valley"]
    scenario_run = run_scenario_regression_suite(scenarios[:2], worlds_root=workspace / "worlds")
    first_batch = run_playtest_batch(
        PlaytestBatchRunRequest(world_id="mist_valley", seeds=[7, 8], steps=2, save_load_check=True),
        worlds_root=str(workspace / "worlds"),
    )
    second_batch = run_playtest_batch(
        PlaytestBatchRunRequest(world_id="mist_valley", seeds=[7, 8], steps=2, save_load_check=True),
        worlds_root=str(workspace / "worlds"),
    )
    benchmark = run_benchmark_suite(
        BenchmarkRunRequest(world_id="mist_valley", worlds_root=str(workspace / "worlds"), iterations=1, benchmarks=["validate_world", "memory_search"])
    )
    quality_payload = json.dumps(quality.model_dump_normal(), ensure_ascii=False)
    benchmark_payload = json.dumps(benchmark.model_dump_safe(), ensure_ascii=False).lower()

    assert quality.passed is True
    assert scenario_run.failed == 0
    assert first_batch.total_runs == second_batch.total_runs == 2
    assert [item.seed for item in first_batch.run_items] == [item.seed for item in second_batch.run_items]
    assert all(sample.ok for sample in benchmark.samples)
    assert "A sealed letter is hidden beneath a loose paving stone." not in quality_payload
    assert "api_key" not in benchmark_payload
    assert "prompt" not in benchmark_payload


def test_v10_final_import_export_mod_and_security_boundaries(final_client) -> None:
    client, workspace = final_client
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]

    export_response = client.get("/authoring/export/worlds/mist_valley")
    assert export_response.status_code == 200
    imported_root = workspace / "imported_worlds"
    app.state.worlds_root = imported_root
    dry_run = client.post("/authoring/import/packages/dry-run", json={"archive_base64": export_response.json()["archive_base64"]})
    assert dry_run.status_code == 200
    assert dry_run.json()["ok"] is True
    assert not (imported_root / "mist_valley").exists()

    assert client.post("/authoring/import/packages/dry-run", json={"archive_base64": _zip_slip_archive()}).json()["ok"] is False
    assert client.post("/authoring/import/packages/dry-run", json={"archive_base64": _executable_archive()}).json()["ok"] is False

    mod_loader = ModLoader(workspace / "mods")
    assert mod_loader.validate_mod("mist_mod").ok is True
    bad_mod = _write_valid_mod(workspace / "mods", "bad_mod")
    bad_mod.joinpath("evil.py").write_text("print('no')\n", encoding="utf-8")
    assert any(issue.code == "mod_executable_code_forbidden" for issue in mod_loader.validate_mod("bad_mod").errors)

    state_payload = client.get(f"/game/state/{session_id}").text
    disabled_settings = Settings(enable_authoring_api=False, enable_debug_api=False, enable_playtest_api=False, enable_eval_api=False, llm_provider="local_stub")
    app.state.settings = disabled_settings
    debug_response = client.get(f"/debug/sessions/{session_id}/timeline")
    authoring_response = client.get("/authoring/worlds")
    save_list = client.get("/game/saves")
    migration_status = client.get(f"/saves/{save_id}/migration-status")

    assert "state_deltas" not in state_payload
    assert "test-api-key-placeholder" not in state_payload
    assert debug_response.status_code == 403
    assert authoring_response.status_code == 403
    assert "state_json" not in save_list.text
    assert "state_deltas" not in save_list.text
    assert "state_json" not in migration_status.text


def _make_final_game_loop() -> GameLoop:
    intents = [
        ("observe", None, None),
        ("move", "blacksmith", None),
        ("talk", "harlan", None),
        ("search", None, None),
        ("use_item", "lucky_charm", None),
        ("wait", None, 30),
    ]
    responses: list[dict[str, object]] = []
    for index, (action_type, target_id, minutes) in enumerate(intents):
        payload: dict[str, object] = {
            "action_type": action_type,
            "raw_text": action_type,
            "confidence": 0.9,
            "requires_clarification": False,
        }
        if target_id is not None:
            payload["target_id"] = target_id
        if minutes is not None:
            payload["minutes"] = minutes
        responses.extend(
            [
                payload,
                {
                    "text": f"Mock narrative {index}",
                    "suggested_actions": ["observe", "wait"],
                    "short_summary": f"Mock summary {index}",
                },
            ]
        )
    provider = FakeLLMProvider(json_responses=responses)
    return GameLoop(
        state=GameState(
            world_id="v10-final-loop",
            player=PlayerState(location_id="square"),
            locations={
                "square": LocationState(id="square", name="Square", exits={"east": "blacksmith"}),
                "blacksmith": LocationState(id="blacksmith", name="Blacksmith", exits={"west": "square"}),
            },
            npcs={"harlan": NPCState(id="harlan", location_id="blacksmith", knowledge=["public_hint"], secrets=["hidden_truth"])},
            objects={
                "notice": WorldObjectState(id="notice", location_id="square", visible=True),
                "lucky_charm": WorldObjectState(id="lucky_charm", owner_id="player", visible=True, portable=True),
            },
            facts={
                "public_hint": FactState(id="public_hint", text="Public hint.", visibility="public", public=True, known_by={"player", "harlan"}),
                "forge_clue": FactState(id="forge_clue", text="Forge clue.", visibility="discoverable", tags=["location:blacksmith"]),
                "hidden_truth": FactState(id="hidden_truth", text="Hidden truth.", visibility="hidden", secret=True, known_by={"harlan"}),
            },
            player_visible_facts={"public_hint"},
        ),
        event_log=EventLog(),
        intent_parser=IntentParser(provider),
        action_dispatcher=ActionDispatcher(),
        narrator=Narrator(provider),
        rng=Random(10),
    )


def _force_legacy_save(repository: SQLiteSaveRepository, save_id: str) -> None:
    save = repository.get_save(save_id)
    state_payload = json.loads(save.state_json)
    state_payload.pop("schema_version", None)
    with repository._connect() as connection:  # noqa: SLF001 - test fixture setup
        connection.execute(
            """
            UPDATE save_games
            SET state_json = ?, schema_version = 'legacy', engine_version = 'legacy'
            WHERE save_id = ?
            """,
            (json.dumps(state_payload), save_id),
        )


def _write_valid_mod(mods_root: Path, mod_id: str = "mist_mod") -> Path:
    mod_path = mods_root / mod_id
    content_root = mod_path / "content"
    content_root.mkdir(parents=True)
    copytree(Path("worlds") / "mist_valley", content_root / "mist_valley")
    mod_path.joinpath("mod.yaml").write_text(
        f"""
id: {mod_id}
name: {mod_id}
version: 0.1.0
engine_version_min: 0.5.0
content_schema_version: "0.6"
dependencies: []
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
description: Local content-only mod.
""",
        encoding="utf-8",
    )
    return mod_path


def _raw_archive_b64(files: dict[str, str]) -> str:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _zip_slip_archive() -> str:
    return _raw_archive_b64(
        {
            "local_package_manifest.json": json.dumps(
                {
                    "package_id": "bad",
                    "package_type": "world",
                    "version": "1.0.0",
                    "engine_version_min": "1.0.0",
                    "schema_version": "1.0",
                    "included_files": ["../evil.txt"],
                    "checksums": {"../evil.txt": "x"},
                    "dependencies": [],
                    "conflicts": [],
                    "created_at": "2026-05-19T00:00:00Z",
                }
            ),
            "../evil.txt": "nope",
        }
    )


def _executable_archive() -> str:
    return _raw_archive_b64(
        {
            "local_package_manifest.json": json.dumps(
                {
                    "package_id": "bad",
                    "package_type": "world",
                    "version": "1.0.0",
                    "engine_version_min": "1.0.0",
                    "schema_version": "1.0",
                    "included_files": ["worlds/bad/evil.py"],
                    "checksums": {"worlds/bad/evil.py": "x"},
                    "dependencies": [],
                    "conflicts": [],
                    "created_at": "2026-05-19T00:00:00Z",
                }
            ),
            "worlds/bad/evil.py": "print('no')\n",
        }
    )
