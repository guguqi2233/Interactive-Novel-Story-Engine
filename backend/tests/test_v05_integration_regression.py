from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.core.event_log import Event
from app.core.state_delta import StateDelta, StateDeltaOperation, apply_delta
from app.core.world_state import (
    ActorCondition,
    CrimeState,
    CrimeStatus,
    FactionState,
    GameState,
    LocationState,
    NPCGoalState,
    NPCGoalStatus,
    NPCState,
    PlayerState,
    RelationshipState,
    ReputationState,
    RumorState,
    WorldObjectState,
)
from app.db.repository import SQLiteSaveRepository
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.content.mod_loader import ModLoader
from app.engine.content.side_quest_generator import (
    QuestDraft,
    QuestDraftStage,
    rule_based_generate_side_quest,
    validate_quest_draft,
)
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.economy import buy_item, can_sell
from app.engine.rules.faction_conflict import resolve_faction_conflicts_from_crimes
from app.engine.rules.npc_planning import choose_plan_for_npc, resolve_npc_planning_tick
from app.engine.rules.rumors import propagate_rumors
from app.llm.context_builder import MemoryContextBuilder
from app.llm.memory_store import MemoryRecord, MemoryVisibility, SQLiteMemoryStore
from app.main import app
from app.session_store import InMemorySessionStore, build_visible_state


def apply_all(state: GameState, deltas: list[StateDelta]) -> GameState:
    next_state = state
    for delta in deltas:
        next_state = apply_delta(next_state, delta)
    return next_state


def copy_mist_valley(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def make_client(
    tmp_path: Path,
    *,
    authoring_enabled: bool,
    worlds_root: Path | None = None,
) -> TestClient:
    tmp_path.mkdir(parents=True, exist_ok=True)
    active_worlds_root = worlds_root or copy_mist_valley(tmp_path)
    app.state.session_store = InMemorySessionStore(worlds_root=str(active_worlds_root))
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v05_api.db")
    app.state.worlds_root = active_worlds_root
    app.state.mods_root = tmp_path / "mods"
    app.state.settings = Settings(
        llm_provider="mock",
        enable_authoring_api=authoring_enabled,
        enable_debug_api=True,
        llm_api_key="test-only-key",
    )
    return TestClient(app)


def test_v05_authoring_flow_is_gated_path_safe_and_does_not_mutate_active_state(
    tmp_path: Path,
) -> None:
    worlds_root = copy_mist_valley(tmp_path)
    disabled_client = make_client(tmp_path / "disabled", authoring_enabled=False, worlds_root=worlds_root)
    assert disabled_client.get("/authoring/worlds").status_code == 403

    client = make_client(tmp_path / "enabled", authoring_enabled=True, worlds_root=worlds_root)
    session_payload = client.post("/game/start", json={"world_id": "mist_valley"}).json()
    session_id = session_payload["session_id"]
    before_state = client.get(f"/game/state/{session_id}").json()["visible_state"]
    assert before_state["location"]["id"] == "village_square"

    read_response = client.get("/authoring/worlds/mist_valley/files/facts.yaml")
    traversal_response = client.get("/authoring/worlds/mist_valley/files/../manifest.yaml")
    invalid_write = client.put(
        "/authoring/worlds/mist_valley/files/locations.yaml",
        json={
            "content": (
                "locations:\n"
                "  - id: village_square\n"
                "    name: Broken Square\n"
                "    description: Broken exit.\n"
                "    exits:\n"
                "      east: missing_location\n"
            )
        },
    )
    after_state = client.get(f"/game/state/{session_id}").json()["visible_state"]

    assert read_response.status_code == 200
    assert "facts:" in read_response.json()["content"]
    assert traversal_response.status_code in {400, 404}
    assert "test-only-key" not in traversal_response.text
    assert invalid_write.status_code == 400
    assert invalid_write.json()["detail"]["errors"][0]["file"] == "locations.yaml"
    assert after_state == before_state
    assert "sealed_letter_under_stone" not in str(after_state)


def test_v05_memory_persistence_and_context_filtering_do_not_override_state(
    tmp_path: Path,
) -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    before_state = state.model_dump_json()
    repository = SQLiteSaveRepository(tmp_path / "memory.db")
    repository.save_snapshot("save-1", state, [])
    store = SQLiteMemoryStore(repository, "save-1")
    safe = MemoryRecord(
        id="memory-safe",
        content="The square was quiet after the last bell.",
        source_event_ids=["event-visible"],
        tags=["location", "quest"],
        entity_ids=["location:village_square", "player"],
        fact_ids=["village_square_is_misty"],
        visibility=MemoryVisibility.NARRATOR_SAFE,
        importance=5,
        created_turn=3,
    )
    hidden = MemoryRecord(
        id="memory-hidden",
        content="The sealed letter names the hidden culprit.",
        source_event_ids=["event-hidden"],
        tags=["source_event_hidden"],
        entity_ids=["sealed_letter"],
        fact_ids=["sealed_letter_under_stone"],
        visibility=MemoryVisibility.HIDDEN,
        importance=10,
        created_turn=4,
    )
    debug = MemoryRecord(
        id="memory-debug",
        content="Raw state_deltas debug trace.",
        tags=["debug"],
        entity_ids=["debug"],
        visibility=MemoryVisibility.DEBUG_ONLY,
        importance=10,
        created_turn=5,
    )

    store.add_memory(safe)
    store.add_memory(hidden)
    store.add_memory(debug)
    action_result = ActionResult(
        success_level=SuccessLevel.SUCCESS,
        reason="Safe context test.",
        visible_facts=["village_square_is_misty"],
    )

    context = MemoryContextBuilder(store).build(
        state,
        actor_id=state.player.id,
        current_location=state.player.location_id,
        action_result=action_result,
        visible_facts=["village_square_is_misty"],
        current_npc_id="harlan",
    )

    assert [memory.id for memory in store.search_by_tags(["location"])] == ["memory-safe"]
    assert [memory.id for memory in store.search_by_entity("sealed_letter")] == ["memory-hidden"]
    assert [memory.id for memory in store.search_by_fact("sealed_letter_under_stone")] == ["memory-hidden"]
    assert [memory.id for memory in repository.list_memories("save-1")] == [
        "memory-debug",
        "memory-hidden",
        "memory-safe",
    ]
    assert [memory.id for memory in context.narrator_safe_memories] == ["memory-safe"]
    assert [memory.id for memory in context.player_visible_memories] == []
    assert "memory-hidden" not in {memory.id for memory in context.npc_known_memories}
    assert state.model_dump_json() == before_state


def test_v05_npc_goals_planning_relationships_and_knowledge_boundaries() -> None:
    state = WorldLoader("worlds").load("mist_valley").to_game_state()
    assert any(isinstance(goal, NPCGoalState) for goal in state.npcs["harlan"].goals)

    state.npcs["mira"] = NPCState(id="mira", location_id="blacksmith")
    state.npcs["tomas"] = NPCState(id="tomas", location_id="blacksmith")
    state.relationships["harlan_trusts_mira"] = RelationshipState(
        id="harlan_trusts_mira",
        source_id="harlan",
        target_id="mira",
        relation_type="trust",
        trust=8,
    )
    state.relationships["harlan_distrusts_tomas"] = RelationshipState(
        id="harlan_distrusts_tomas",
        source_id="harlan",
        target_id="tomas",
        relation_type="trust",
        trust=-5,
    )
    state.rumors["bridge_warning_shared"] = RumorState(
        id="bridge_warning_shared",
        text_for_player="Someone is warning locals about the old bridge.",
        known_by_npcs={"harlan"},
        tags=["public"],
    )

    planning_result = resolve_npc_planning_tick(state)
    rumor_state = apply_all(state, propagate_rumors(state))

    assert planning_result.events
    assert all(delta.metadata.get("source") == "npc_planning" for delta in planning_result.state_deltas)
    assert "mira" in rumor_state.rumors["bridge_warning_shared"].known_by_npcs
    assert "tomas" not in rumor_state.rumors["bridge_warning_shared"].known_by_npcs

    state.npcs["harlan"].goals = []
    state.rumors = {}
    state.crimes["unknown-crime"] = CrimeState(
        id="unknown-crime",
        crime_type="theft",
        actor_id="player",
        target_id="sealed_letter",
        location_id="blacksmith",
        status=CrimeStatus.WITNESSED,
        witnessed_by=["mira"],
        severity=1,
        created_turn=state.turn,
    )
    assert choose_plan_for_npc(state, "harlan") is None

    state.crimes = {}
    state.npcs["harlan"].alive = False
    state.npcs["harlan"].condition = ActorCondition.DEAD
    assert choose_plan_for_npc(state, "harlan") is None
    assert all(event.target_id != "harlan" for event in resolve_npc_planning_tick(state).events)


def test_v05_social_economy_and_relationship_state_survive_save_load(tmp_path: Path) -> None:
    state = GameState(
        world_id="v05-social-economy",
        player=PlayerState(location_id="market", currency=30),
        locations={"market": LocationState(id="market", name="Market")},
        factions={
            "guild": FactionState(
                id="guild",
                name="Guild",
                reputation=ReputationState(value=-15, known_to_player=True),
                known_by_player=True,
            )
        },
        npcs={
            "mira": NPCState(
                id="mira",
                location_id="market",
                faction_id="guild",
                merchant=True,
                shop_inventory=["apple"],
            )
        },
        objects={
            "apple": WorldObjectState(
                id="apple",
                owner_id="mira",
                portable=True,
                base_price=10,
                tradeable=True,
            ),
            "stolen_ring": WorldObjectState(
                id="stolen_ring",
                owner_id="player",
                portable=True,
                base_price=50,
                tradeable=True,
                tags=["stolen"],
            ),
        },
        relationships={
            "mira_player_trade": RelationshipState(
                id="mira_player_trade",
                source_id="mira",
                target_id="player",
                relation_type="trade",
                trust=1,
                known_by_player=True,
            )
        },
        crimes={
            "crime-theft": CrimeState(
                id="crime-theft",
                crime_type="theft",
                actor_id="player",
                target_id="mira",
                location_id="market",
                status=CrimeStatus.REPORTED,
                severity=2,
                created_turn=1,
            )
        },
    )

    trade_deltas = buy_item(state, "mira", "apple")
    state = apply_all(state, trade_deltas)
    conflict_deltas = resolve_faction_conflicts_from_crimes(state)
    state = apply_all(state, conflict_deltas)
    event = Event(
        event_id="trade-and-conflict",
        turn=state.turn,
        actor_id="player",
        action_type="buy",
        result="success",
        state_deltas=[*trade_deltas, *conflict_deltas],
        visible_to_player=True,
    )
    repository = SQLiteSaveRepository(tmp_path / "social_economy.db")
    repository.save_snapshot("save-1", state, [event])
    loaded = repository.load_save("save-1")

    assert state.objects["apple"].owner_id == "player"
    assert state.player.currency == 18
    assert not can_sell(state, "mira", "stolen_ring").allowed
    assert loaded.player.currency == state.player.currency
    assert loaded.objects["apple"].owner_id == "player"
    assert loaded.relationships == state.relationships
    assert loaded.factions["guild"].alert_level >= 2
    assert all(delta.path.startswith(("player.", "objects.", "npcs.", "factions.", "social_flags.")) for delta in event.state_deltas)
    assert "sealed_letter_under_stone" not in build_visible_state(loaded).model_dump_json()


def test_v05_quest_drafts_and_mod_packaging_are_validation_only(tmp_path: Path) -> None:
    pack = WorldLoader("worlds").load("mist_valley")
    state = pack.to_game_state()
    before_state = state.model_dump_json()

    draft = rule_based_generate_side_quest(pack, state)
    invalid_draft = QuestDraft(
        title="Invalid Draft",
        premise="A harmless invalid reference.",
        involved_npcs=["missing_npc"],
        stages=[QuestDraftStage(id="start", title="Start")],
    )
    valid_report = validate_quest_draft(draft, pack)
    invalid_report = validate_quest_draft(invalid_draft, pack)

    mod_root = tmp_path / "mods" / "mist_mod"
    content_root = mod_root / "content"
    copytree(Path("worlds") / "mist_valley", content_root / "mist_valley")
    mod_root.joinpath("mod.yaml").write_text(
        """
id: mist_mod
name: Mist Mod
version: 0.1.0
engine_version_min: 0.5.0
dependencies: []
conflicts: []
entry_worlds:
  - mist_valley
content_paths:
  - content
""",
        encoding="utf-8",
    )
    mod_root.joinpath("script.py").write_text("print('forbidden')\n", encoding="utf-8")
    loader = ModLoader(tmp_path / "mods")
    discovered = loader.discover_mods()
    mod_report = loader.validate_mod("mist_mod")

    assert valid_report.ok
    assert not invalid_report.ok
    assert invalid_report.errors[0].code == "missing_npc"
    assert state.model_dump_json() == before_state
    assert [mod.manifest.id for mod in discovered] == ["mist_mod"]
    assert not mod_report.ok
    assert any(issue.code == "mod_executable_code_forbidden" for issue in mod_report.errors)


def test_v05_multi_world_save_browser_filters_summaries_and_loaded_game_continues(
    tmp_path: Path,
) -> None:
    worlds_root = copy_mist_valley(tmp_path)
    client = make_client(tmp_path, authoring_enabled=True, worlds_root=worlds_root)
    start = client.post("/game/start", json={"world_id": "mist_valley"}).json()
    session_id = start["session_id"]
    save_id = client.post(f"/game/{session_id}/save").json()["save_id"]

    other_state = GameState(
        world_id="other_world",
        player=PlayerState(location_id="start"),
        locations={"start": LocationState(id="start", name="Other Start")},
    )
    app.state.save_repository.create_save("other-save", other_state)

    all_saves = client.get("/game/saves").json()["saves"]
    filtered = client.get("/game/saves?world_id=mist_valley").json()["saves"]
    delete_response = client.delete("/game/saves/other-save")
    loaded = client.post(f"/game/load/{save_id}").json()
    continued = client.post(
        "/game/input",
        json={"session_id": loaded["session_id"], "player_input": "观察"},
    ).json()

    assert {save["world_id"] for save in all_saves} == {"mist_valley", "other_world"}
    assert [save["world_id"] for save in filtered] == ["mist_valley"]
    assert filtered[0]["current_location_name"] == "Village Square"
    assert "sealed_letter_under_stone" not in str(filtered)
    assert "state_deltas" not in str(filtered)
    assert delete_response.status_code == 200
    assert continued["turn"] == loaded["turn"] + 1
    assert "hidden_facts" not in str(continued)
