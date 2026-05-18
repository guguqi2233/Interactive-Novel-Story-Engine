import base64
import json
from io import BytesIO
from pathlib import Path
from shutil import copytree
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.scenario_templates import ScenarioTemplateRenderer
from app.main import app
from app.scenarios.regression import ScenarioRegressionCase, run_scenario_regression_suite
from app.session_store import InMemorySessionStore


def _make_client(tmp_path: Path) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v08_integration.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = tmp_path / "mods"
    app.state.narrative_eval_reports = []
    app.state.playtest_reports = []
    app.state.scenario_regression_runs = []
    app.state.scenario_template_renderer = ScenarioTemplateRenderer(
        templates_root=Path("templates"),
        worlds_root=worlds_root,
    )
    app.state.settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'private.db'}",
        enable_authoring_api=True,
        enable_debug_api=True,
        enable_eval_api=True,
        enable_playtest_api=True,
        enable_perf_logging=True,
        llm_provider="local_stub",
        llm_api_key="test-secret-placeholder",
    )
    return TestClient(app)


def test_v08_visual_authoring_editors_validate_preview_and_preserve_player_boundaries(
    tmp_path: Path,
) -> None:
    client = _make_client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    before_state = client.get(f"/game/state/{session_id}").json()
    world_path = tmp_path / "worlds" / "mist_valley"

    map_graph = client.get("/authoring/worlds/mist_valley/map").json()["graph"]
    assert map_graph["nodes"]
    assert map_graph["edges"]
    original_locations = (world_path / "locations.yaml").read_text(encoding="utf-8")
    map_graph["nodes"][0]["x"] += 25
    preview_map = client.post("/authoring/worlds/mist_valley/map/preview", json={"graph": map_graph})
    assert preview_map.status_code == 200
    assert (world_path / "locations.yaml").read_text(encoding="utf-8") == original_locations
    invalid_map = json.loads(json.dumps(map_graph))
    invalid_map["edges"].append(
        {
            "source_location_id": "village_square",
            "target_location_id": "missing_location",
            "edge_type": "exit",
            "label": "bad",
            "visibility": "public",
        }
    )
    assert client.post("/authoring/worlds/mist_valley/map/validate", json={"graph": invalid_map}).json()["ok"] is False
    saved_map = client.put("/authoring/worlds/mist_valley/map", json={"graph": map_graph})
    assert saved_map.status_code == 200
    assert saved_map.json()["validation"]["ok"] is True

    quest_graph = client.get("/authoring/worlds/mist_valley/quests/graph").json()
    preview_quest = client.post("/authoring/worlds/mist_valley/quests/graph/preview", json={"graph": quest_graph})
    assert preview_quest.status_code == 200
    assert preview_quest.json()["validation"]["ok"] is True
    invalid_quest = json.loads(json.dumps(quest_graph))
    invalid_quest["quests"][0]["stages"][0]["next_stages"] = ["missing_stage"]
    invalid_quest_preview = client.post(
        "/authoring/worlds/mist_valley/quests/graph/preview",
        json={"graph": invalid_quest},
    )
    assert invalid_quest_preview.json()["validation"]["ok"] is False
    unreachable_quest = json.loads(json.dumps(quest_graph))
    stage_template = json.loads(json.dumps(unreachable_quest["quests"][0]["stages"][0]))
    stage_template.update(
        {
            "id": "unreachable_integration_stage",
            "title": "Unreachable Integration Stage",
            "next_stages": [],
            "failure_stages": [],
            "alternate_stages": [],
        }
    )
    unreachable_quest["quests"][0]["stages"].append(stage_template)
    unreachable_preview = client.post(
        "/authoring/worlds/mist_valley/quests/graph/preview",
        json={"graph": unreachable_quest},
    )
    assert any(issue["code"] == "quest_unreachable_stage" for issue in unreachable_preview.json()["validation"]["warnings"])
    visible_state_text = client.get(f"/game/state/{session_id}").text
    assert "sealed_letter" not in visible_state_text
    assert "state_deltas" not in visible_state_text
    assert client.get(f"/game/state/{session_id}").json() == before_state


def test_v08_social_economy_consequence_validation_graph_and_frontend_contracts(
    tmp_path: Path,
) -> None:
    client = _make_client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]

    npc_graph = client.get("/authoring/worlds/mist_valley/npcs/goals").json()
    npc_graph["npcs"][0]["goals"][0]["conditions"] = ["fact:missing_fact"]
    npc_preview = client.post("/authoring/worlds/mist_valley/npcs/goals/preview", json={"graph": npc_graph})
    assert any(issue["code"] == "npc_goal_missing_fact" for issue in npc_preview.json()["validation"]["errors"])

    social_graph = client.get("/authoring/worlds/mist_valley/social/graph").json()
    social_graph["relationship_graph"]["relationships"][0]["source_id"] = "missing_npc"
    social_preview = client.post("/authoring/worlds/mist_valley/social/graph/preview", json={"graph": social_graph})
    assert any(issue["code"] == "relationship_missing_source" for issue in social_preview.json()["validation"]["errors"])
    player_graph = client.get(f"/game/{session_id}/graphs/relationships")
    assert player_graph.status_code == 200
    assert "debug_only" not in player_graph.text
    assert "hidden_edge" not in player_graph.text

    economy_graph = client.get("/authoring/worlds/mist_valley/economy").json()
    economy_graph["items"][2]["owner_id"] = "harlan"
    economy_graph["items"][2]["location_id"] = "village_square"
    economy_preview = client.post("/authoring/worlds/mist_valley/economy/preview", json={"graph": economy_graph})
    assert any(issue["code"] == "item_conflicting_ownership" for issue in economy_preview.json()["validation"]["errors"])
    assert "sealed_letter" not in client.post("/game/start", json={"world_id": "mist_valley"}).text

    consequence_graph = client.get("/authoring/worlds/mist_valley/rumor-crime").json()
    consequence_graph["rumors"][0]["fact_id"] = "missing_fact"
    invalid_rumor = client.post("/authoring/worlds/mist_valley/rumor-crime/preview", json={"graph": consequence_graph})
    assert any(issue["code"] == "rumor_missing_fact" for issue in invalid_rumor.json()["validation"]["errors"])
    consequence_graph = client.get("/authoring/worlds/mist_valley/rumor-crime").json()
    consequence_graph["rumors"][0]["text_for_player"] = "A sealed letter is hidden beneath a loose paving stone."
    leak_rumor = client.post("/authoring/worlds/mist_valley/rumor-crime/preview", json={"graph": consequence_graph})
    assert any(issue["code"] == "rumor_reveals_hidden_fact" for issue in leak_rumor.json()["validation"]["warnings"])
    consequence_graph["crimes"].append(
        {"id": consequence_graph["rumors"][0]["id"], "crime_type": "theft", "trigger_condition": "crime:theft"}
    )
    duplicate_rumor = client.post("/authoring/worlds/mist_valley/rumor-crime/preview", json={"graph": consequence_graph})
    assert any(issue["code"] == "duplicate_consequence_id" for issue in duplicate_rumor.json()["validation"]["errors"])

    validation_graph = client.post("/authoring/worlds/mist_valley/validation-graph")
    assert validation_graph.status_code == 200
    payload = validation_graph.json()
    assert payload["nodes"]
    assert any(edge["type"] in {"references", "contains"} for edge in payload["edges"])
    assert "test-secret-placeholder" not in validation_graph.text

    app_source = Path("frontend/src/App.tsx").read_text(encoding="utf-8")
    assert "AuthoringToolNav" in app_source
    assert "DirtyStateBanner" in app_source
    assert "HiddenContentBadge" in app_source
    assert "PreviewResultPanel" in app_source


def test_v08_timeline_branch_scenario_template_prompt_and_package_flow(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    client.post("/game/input", json={"session_id": session_id, "player_input": "smithy"})
    client.post("/game/input", json={"session_id": session_id, "player_input": "search"})
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]

    timeline = client.get(f"/debug/saves/{save_id}/timeline").json()
    turns = [turn["turn"] for turn in timeline["turns"]]
    assert turns == sorted(turns)
    assert any(event["state_deltas"] for turn in timeline["turns"] for event in turn["events"])
    before_timeline = client.get(f"/debug/saves/{save_id}/timeline").json()
    dry_run = client.post(f"/debug/saves/{save_id}/replay-dry-run").json()
    after_timeline = client.get(f"/debug/saves/{save_id}/timeline").json()
    assert dry_run["replay_summary"]["event_count"] == before_timeline["event_count"]
    assert before_timeline == after_timeline
    assert "state_deltas" not in client.get(f"/game/state/{session_id}").text

    world_path = tmp_path / "worlds" / "mist_valley"
    (world_path / ".env").write_text("LLM_API_KEY=test-secret-placeholder", encoding="utf-8")
    (world_path / "debug.db").write_text("sqlite", encoding="utf-8")
    branch_response = client.post(
        "/authoring/worlds/mist_valley/branches",
        json={"branch_id": "v08_branch", "name": "v0.8 branch"},
    )
    assert branch_response.status_code == 200
    branch_path = tmp_path / "worlds" / ".branches" / "mist_valley" / "v08_branch"
    assert (branch_path / "manifest.yaml").exists()
    assert not (branch_path / ".env").exists()
    assert not (branch_path / "debug.db").exists()
    branch_items = branch_path / "items.yaml"
    branch_items.write_text(
        branch_items.read_text(encoding="utf-8")
        + "\n  - id: v08_branch_item\n    name: Branch Item\n    description: Branch-only item.\n    portable: true\n",
        encoding="utf-8",
    )
    diff_response = client.get("/authoring/worlds/mist_valley/diff", params={"other": "v08_branch"})
    diff = diff_response.json()["diff"]
    assert any(entity["entity_id"] == "v08_branch_item" for entity in diff["added_entities"])
    (world_path / ".env").unlink()
    (world_path / "debug.db").unlink()

    saves_before = client.get("/game/saves").json()["saves"]
    scenario_response = client.post(
        "/scenarios/regression/run",
        json={"world_id": "mist_valley", "scenario_ids": ["mist_valley_opening_observe"]},
    )
    forbidden_run = run_scenario_regression_suite(
        [
            ScenarioRegressionCase(
                id="forbidden_integration",
                world_id="mist_valley",
                name="Forbidden integration",
                input_sequence=["observe"],
                forbidden_visible_facts=["village_square_is_misty"],
            )
        ],
        worlds_root=tmp_path / "worlds",
    )
    saves_after = client.get("/game/saves").json()["saves"]
    assert scenario_response.status_code == 200
    assert forbidden_run.failed == 1
    assert saves_after == saves_before

    template_preview = client.post(
        "/authoring/templates/basic_village_world/preview",
        json={
            "variables": {
                "world_id": "v08_template_world",
                "world_name": "V08 Template World",
                "start_location_id": "green",
                "npc_id": "guide",
                "npc_name": "Guide",
            }
        },
    )
    invalid_template = client.post("/authoring/templates/basic_village_world/preview", json={"variables": {}})
    assert template_preview.json()["writes_to_disk"] is False
    assert template_preview.json()["validation_report"]["ok"] is True
    assert invalid_template.status_code == 400

    profile_response = client.post("/studio/prompt-profiles/select", json={"profile_id": "local_story"})
    config_response = client.get("/studio/config-summary")
    assert profile_response.status_code == 200
    assert config_response.json()["selected_prompt_profile_id"] == "local_story"
    assert "test-secret-placeholder" not in config_response.text
    assert "hidden facts" not in json.dumps(config_response.json()["prompt_profiles"]).lower()

    export_response = client.get("/authoring/export/worlds/mist_valley")
    archive = _zip_entries(export_response.json()["archive_base64"])
    manifest = json.loads(archive["local_package_manifest.json"])
    assert manifest["checksums"]["worlds/mist_valley/manifest.yaml"]
    tampered = _tamper_archive_file(
        export_response.json()["archive_base64"],
        "worlds/mist_valley/manifest.yaml",
        "world_id: mist_valley\nname: Tampered\n",
    )
    checksum_response = client.post("/authoring/import/packages/dry-run", json={"archive_base64": tampered})
    zip_slip_response = client.post("/authoring/import/packages/dry-run", json={"archive_base64": _zip_slip_archive()})
    executable_response = client.post("/authoring/import/packages/dry-run", json={"archive_base64": _executable_archive()})
    assert checksum_response.json()["ok"] is False
    assert zip_slip_response.json()["ok"] is False
    assert executable_response.json()["ok"] is False
    save_export = client.get(f"/authoring/export/saves/{save_id}").json()["archive_base64"]
    save_dry_run = client.post("/authoring/import/packages/dry-run", json={"archive_base64": save_export})
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "imported_saves.db")
    save_import = client.post(
        "/authoring/import/packages/apply",
        json={"archive_base64": save_export, "confirm_apply": True},
    )
    status_response = client.get(f"/saves/{save_id}/migration-status")
    assert save_dry_run.status_code == 200
    assert save_dry_run.json()["migration_needed"] is False
    assert save_import.status_code == 200
    assert status_response.status_code == 200
    assert status_response.json()["needs_migration"] is False
    assert "test-secret-placeholder" not in (
        timeline.__str__() + branch_response.text + scenario_response.text + template_preview.text + save_import.text
    )


def _zip_entries(archive_base64: str) -> dict[str, str]:
    with ZipFile(BytesIO(base64.b64decode(archive_base64))) as archive:
        return {name: archive.read(name).decode("utf-8") for name in archive.namelist()}


def _tamper_archive_file(archive_base64: str, file_name: str, content: str) -> str:
    source = BytesIO(base64.b64decode(archive_base64))
    target = BytesIO()
    with ZipFile(source) as old_archive, ZipFile(target, "w", ZIP_DEFLATED) as new_archive:
        for name in old_archive.namelist():
            new_archive.writestr(name, content if name == file_name else old_archive.read(name))
    return base64.b64encode(target.getvalue()).decode("ascii")


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
                    "version": "0.8.16",
                    "engine_version_min": "0.8.0",
                    "schema_version": "0.8",
                    "included_files": ["../evil.txt"],
                    "checksums": {"../evil.txt": "x"},
                    "dependencies": [],
                    "conflicts": [],
                    "created_at": "2026-05-18T00:00:00Z",
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
                    "version": "0.8.16",
                    "engine_version_min": "0.8.0",
                    "schema_version": "0.8",
                    "included_files": ["worlds/bad/evil.py"],
                    "checksums": {"worlds/bad/evil.py": "x"},
                    "dependencies": [],
                    "conflicts": [],
                    "created_at": "2026-05-18T00:00:00Z",
                }
            ),
            "worlds/bad/evil.py": "print('no')\n",
        }
    )
