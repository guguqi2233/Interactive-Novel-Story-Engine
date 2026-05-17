import json
from pathlib import Path
from random import Random
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import Event
from app.core.instrumentation import get_performance_recorder, set_performance_logging_enabled
from app.core.state_delta import StateDelta, StateDeltaOperation
from app.core.world_state import (
    CombatState,
    FactState,
    FactVisibility,
    GameState,
    LocationState,
    NPCState,
    PlayerState,
    RelationshipState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.content.mod_loader import ModLoader
from app.engine.rules.combat import resolve_attack_with_options
from app.evals.narrative_quality import NarrativeQualityCase, evaluate_narrative_quality
from app.llm.local_provider import LocalStubProvider
from app.llm.provider_base import LLMProviderError
from app.llm.provider_factory import create_llm_provider
from app.llm.schemas import NarrativeResult
from app.main import app
from app.playtesting.invariants import check_playtest_invariants
from app.playtesting.runner import PlaytestOptions, run_playtest
from app.session_store import InMemorySessionStore, build_visible_state


def _make_client(
    tmp_path: Path,
    *,
    authoring_enabled: bool = True,
    debug_enabled: bool = True,
    perf_enabled: bool = False,
) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v06_integration.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = tmp_path / "mods"
    app.state.settings = Settings(
        enable_authoring_api=authoring_enabled,
        enable_debug_api=debug_enabled,
        enable_perf_logging=perf_enabled,
        llm_provider="mock",
        llm_api_key="super-secret-test-key",
    )
    set_performance_logging_enabled(perf_enabled)
    get_performance_recorder().clear()
    return TestClient(app)


def _legacy_state() -> GameState:
    return GameState(
        world_id="mist_valley",
        player=PlayerState(location_id="village_square"),
        locations={"village_square": LocationState(id="village_square", name="Village Square")},
        facts={
            "public_notice": FactState(
                id="public_notice",
                text="The square is busy.",
                visibility=FactVisibility.PUBLIC,
            ),
            "hidden_cache": FactState(
                id="hidden_cache",
                text="Secret migration text must stay hidden.",
                visibility=FactVisibility.HIDDEN,
            ),
        },
        player_visible_facts={"public_notice"},
    )


def _force_legacy_save(repository: SQLiteSaveRepository, save_id: str) -> None:
    state = _legacy_state()
    repository.create_save(save_id, state)
    payload = state.model_dump(mode="json")
    payload.pop("schema_version", None)
    with repository._connect() as connection:  # noqa: SLF001 - test fixture setup
        connection.execute(
            """
            UPDATE save_games
            SET state_json = ?, schema_version = 'legacy', engine_version = 'legacy'
            WHERE save_id = ?
            """,
            (json.dumps(payload), save_id),
        )
    repository.append_event(
        save_id,
        Event(
            event_id="legacy-event-1",
            turn=1,
            actor_id="player",
            action_type="wait",
            result="success",
            visible_to_player=True,
            state_deltas=[
                StateDelta(operation=StateDeltaOperation.INC, path="turn", value=1),
            ],
        ),
    )


def _write_mod(
    root: Path,
    mod_id: str,
    *,
    dependencies: list[str] | None = None,
    conflicts: list[str] | None = None,
    engine_version_min: str = "0.6.0",
) -> Path:
    mod_path = root / mod_id
    content_root = mod_path / "content"
    content_root.mkdir(parents=True)
    copytree(Path("worlds") / "mist_valley", content_root / "mist_valley")
    mod_path.joinpath("mod.yaml").write_text(
        f"""
id: {mod_id}
name: {mod_id}
version: 0.1.0
engine_version_min: {engine_version_min}
content_schema_version: "0.6"
dependencies: {dependencies or []}
optional_dependencies: []
conflicts: {conflicts or []}
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
    return mod_path


def test_v06_save_migration_api_preserves_events_and_visibility(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    repository = app.state.save_repository
    _force_legacy_save(repository, "legacy-save")
    before = repository.get_save("legacy-save")

    status_response = client.get("/saves/legacy-save/migration-status")
    dry_run_response = client.post("/saves/legacy-save/migrate-dry-run")
    after_dry_run = repository.get_save("legacy-save")
    migrate_response = client.post("/saves/legacy-save/migrate")
    load_response = client.post("/game/load/legacy-save")

    assert status_response.status_code == 200
    assert status_response.json()["needs_migration"] is True
    assert dry_run_response.status_code == 200
    assert dry_run_response.json()["dry_run"] is True
    assert after_dry_run.state_json == before.state_json
    assert migrate_response.status_code == 200
    assert "legacy->0.6" in repository.get_save("legacy-save").migration_history
    assert [event.event_id for event in repository.list_events("legacy-save")] == ["legacy-event-1"]
    assert load_response.status_code == 200
    visible_state_text = json.dumps(load_response.json()["visible_state"])
    assert "Secret migration text" not in visible_state_text


def test_v06_authoring_preview_graph_and_perf_boundaries(tmp_path: Path) -> None:
    client = _make_client(tmp_path, perf_enabled=True)
    original = client.get("/authoring/worlds/mist_valley/files/npcs.yaml").json()["content"]
    proposed = original.replace("  - id: harlan", "  - id: harlan_removed")
    session_id = client.post("/game/start", json={"world_id": "mist_valley"}).json()["session_id"]
    game_loop = app.state.session_store.get_session(session_id)
    before_state = game_loop.state.model_dump_json()
    game_loop.state.npcs["shadow"] = NPCState(
        id="shadow",
        location_id=game_loop.state.player.location_id,
        visible=True,
        hidden=True,
    )
    game_loop.state.relationships["shadow_player"] = RelationshipState(
        id="shadow_player",
        source_id="shadow",
        target_id="player",
        relation_type="watching",
        known_by_player=True,
    )

    preview_response = client.post(
        "/authoring/worlds/mist_valley/preview-file-change",
        json={"file_name": "npcs.yaml", "proposed_content": proposed},
    )
    impact_response = client.post(
        "/authoring/worlds/mist_valley/impact-analysis",
        json={"file_name": "npcs.yaml", "proposed_content": proposed},
    )
    graph_response = client.get(f"/game/{session_id}/graphs/relationships")
    debug_graph_response = client.get(f"/debug/sessions/{session_id}/graphs/relationships")
    client.post("/game/input", json={"session_id": session_id, "player_input": "observe"})
    perf_response = client.get("/debug/performance/recent")
    after_file = client.get("/authoring/worlds/mist_valley/files/npcs.yaml").json()["content"]

    assert preview_response.status_code == 200
    assert preview_response.json()["parsed_ok"] is True
    assert preview_response.json()["validation_report"]["ok"] is False
    assert preview_response.json()["validation_report"]["errors"]
    assert impact_response.status_code == 200
    assert "harlan" in impact_response.json()["removed_npcs"]
    assert after_file == original
    assert graph_response.status_code == 200
    assert "shadow_player" not in graph_response.text
    assert debug_graph_response.status_code == 200
    assert "shadow_player" in debug_graph_response.text
    assert perf_response.status_code == 200
    assert "super-secret-test-key" not in perf_response.text
    assert "state_deltas" not in perf_response.text
    assert game_loop.state.model_dump_json() != before_state
    assert game_loop.state.relationships["shadow_player"].source_id == "shadow"


def test_v06_authoring_disabled_and_path_traversal_are_blocked(tmp_path: Path) -> None:
    client = _make_client(tmp_path, authoring_enabled=False)

    disabled_response = client.get("/authoring/worlds")
    traversal_response = client.post(
        "/authoring/worlds/mist_valley/preview-file-change",
        json={"file_name": "../manifest.yaml", "proposed_content": "world_id: x"},
    )

    assert disabled_response.status_code == 403
    assert traversal_response.status_code == 403
    assert "super-secret-test-key" not in disabled_response.text + traversal_response.text


def test_v06_playtesting_agent_is_deterministic_and_event_driven(tmp_path: Path) -> None:
    options = PlaytestOptions(
        world_id="mist_valley",
        strategy="random_valid_action_agent",
        max_steps=4,
        seed=9,
        save_every=3,
        database_path=str(tmp_path / "playtest.db"),
    )

    first = run_playtest(options)
    second = run_playtest(options)

    assert [action.input_text for action in first.actions_taken] == [
        action.input_text for action in second.actions_taken
    ]
    assert first.errors == []
    assert first.save_load_failures == []
    assert first.turns_run == 4
    assert all(action.event_id for action in first.actions_taken)
    assert first.final_state_summary.event_count >= first.turns_run


def test_v06_playtesting_invariants_catch_visibility_leak() -> None:
    state = _legacy_state()
    state.player_visible_facts.add("hidden_cache")

    result = check_playtest_invariants(state, events=[])

    assert "hidden_fact_marked_visible:hidden_cache" in result.visibility_leaks
    assert "hidden_fact_text_visible:hidden_cache" in result.visibility_leaks


def test_v06_narrative_quality_catches_core_failures_without_llm() -> None:
    base_case = {
        "id": "integration-quality",
        "allowed_suggested_actions": ["observe", "search"],
        "action_result": ActionResult(
            success_level=SuccessLevel.SUCCESS,
            reason="Rule outcome.",
            visible_facts=[],
        ),
    }

    invented_item = evaluate_narrative_quality(
        NarrativeQualityCase(
            **base_case,
            narrative=NarrativeResult(
                text="The player finds the invented crystal crown.",
                suggested_actions=["observe"],
                short_summary="Invented item.",
            ),
            invented_item_terms=["crystal crown"],
        )
    )
    hidden_leak = evaluate_narrative_quality(
        NarrativeQualityCase(
            **base_case,
            narrative=NarrativeResult(
                text="Secret migration text must stay hidden.",
                suggested_actions=["observe"],
                short_summary="Hidden leak.",
            ),
            hidden_fact_texts=["Secret migration text"],
        )
    )
    contradiction = evaluate_narrative_quality(
        NarrativeQualityCase(
            id="integration-quality-failure",
            allowed_suggested_actions=["observe", "search"],
            narrative=NarrativeResult(
                text="You clearly succeeded despite the failed rule result.",
                suggested_actions=["observe"],
                short_summary="Contradiction.",
            ),
            action_result=ActionResult(
                success_level=SuccessLevel.FAILURE,
                reason="Rule failure.",
                visible_facts=[],
            ),
        )
    )

    assert not invented_item.passed
    assert not hidden_leak.passed
    assert not contradiction.passed


def test_v06_mod_versioning_rejects_unsafe_or_incompatible_content(tmp_path: Path) -> None:
    mods_root = tmp_path / "mods"
    _write_mod(mods_root, "base_mod")
    _write_mod(mods_root, "addon_mod", dependencies=["base_mod"])
    _write_mod(mods_root, "conflict_mod", conflicts=["base_mod"])
    unsafe_path = _write_mod(mods_root, "unsafe_mod")
    unsafe_path.joinpath("evil.py").write_text("print('not allowed')\n", encoding="utf-8")
    traversal_path = _write_mod(mods_root, "traversal_mod")
    manifest = traversal_path / "mod.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("  - content", "  - ../outside"),
        encoding="utf-8",
    )

    loader = ModLoader(mods_root)
    dependency_report = loader.resolve_load_order(["addon_mod", "base_mod"])
    conflict_report = loader.detect_conflicts(["base_mod", "conflict_mod"])
    unsafe_report = loader.validate_mod("unsafe_mod")
    traversal_report = loader.validate_mod("traversal_mod")

    assert dependency_report.ok
    assert dependency_report.load_order == ["base_mod", "addon_mod"]
    assert not conflict_report.ok
    assert ("base_mod", "conflict_mod") in conflict_report.conflicts
    assert any(issue.code == "mod_executable_code_forbidden" for issue in unsafe_report.errors)
    assert any(issue.code == "unsafe_content_path" for issue in traversal_report.errors)


def test_v06_local_provider_and_combat_slice_stay_within_boundaries() -> None:
    provider = create_llm_provider(Settings(llm_provider="local_stub"))
    assert isinstance(provider, LocalStubProvider)
    try:
        create_llm_provider(Settings(llm_provider="local_http", local_llm_base_url=None))
    except LLMProviderError as exc:
        assert "LOCAL_LLM_BASE_URL is required" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("local_http without base URL should fail")

    state = GameState(
        world_id="combat-integration",
        player=PlayerState(location_id="arena"),
        locations={"arena": LocationState(id="arena", name="Arena")},
        npcs={
            "bandit": NPCState(
                id="bandit",
                location_id="arena",
                hp=6,
                max_hp=6,
                combat_stance="defensive",
                status_effects=["guarded"],
            ),
            "hidden_witness": NPCState(
                id="hidden_witness",
                location_id="arena",
                visible=True,
                hidden=True,
            ),
        },
        combats={
            "combat-1": CombatState(
                id="combat-1",
                combatant_ids=["player", "bandit", "hidden_witness"],
                location_id="arena",
            )
        },
    )
    state.player.attack = 10

    attack, attack_deltas = resolve_attack_with_options(state, "player", "bandit", Random(0), lethal=False)
    visible_state = build_visible_state(state)

    assert attack.outcome.value in {"hit", "glancing", "critical"}
    assert all(delta.operation in StateDeltaOperation for delta in attack_deltas)
    assert any(delta.path == "npcs.bandit.status_effects" for delta in attack_deltas)
    assert visible_state.active_combat is not None
    assert "bandit" in visible_state.active_combat.visible_combatants
    assert "hidden_witness" not in visible_state.active_combat.visible_combatants
