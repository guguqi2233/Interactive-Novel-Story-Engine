import json
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.config import Settings
from app.core.world_state import (
    CrimeState,
    FactState,
    FactVisibility,
    FactionState,
    GameState,
    LocationState,
    NPCState,
    QuestState,
    QuestStatus,
    QuestVisibility,
    RelationshipState,
    ReputationState,
    RumorState,
    WitnessRecord,
    WorldObjectState,
)
from app.engine.actions.schemas import ActionResult, SuccessLevel
from app.engine.content.map_visual import build_player_visible_map_visual_graph
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.graphs import build_faction_graph, build_relationship_graph
from app.llm.context_builder import MemoryContextBuilder
from app.llm.memory_store import InMemoryMemoryStore, MemoryRecord, MemoryVisibility
from app.main import app
from app.playtesting.runner import PlaytestScenario, PlaytestScenarioType, run_playtest_scenario
from app.quality import QualityIssue, QualityIssueSeverity, WorldQualityReport
from app.session_store import InMemorySessionStore, build_visible_state


HIDDEN_FACT_ID = "sealed_letter_under_stone"
HIDDEN_FACT_TEXT = "A sealed letter is hidden beneath a loose paving stone."
NPC_SECRET = "harlan_knows_the_smugglers_route"
HIDDEN_WITNESS_ID = "hidden_watcher"
HIDDEN_RELATIONSHIP_ID = "hidden_harlan_watcher"
HIDDEN_FACTION_ID = "hidden_cabal"
HIDDEN_MEMORY_TEXT = "hidden memory about the sealed letter"
DEBUG_MEMORY_TEXT = "debug-only witness trace"
HIDDEN_ITEM_ID = "hidden_dagger"
HIDDEN_QUEST_ID = "hidden_letter_quest"
HIDDEN_RUMOR_TRUTH = "the letter names the smuggler"


class HiddenLeakCase(BaseModel):
    id: str
    leak_type: str
    outlet: str
    forbidden_terms: list[str] = Field(default_factory=list)
    safe_reason: str

    def assert_no_leak(self, payload: object) -> None:
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        leaked = [term for term in self.forbidden_terms if term and term in serialized]
        assert leaked == [], self.safe_reason


def make_hidden_leak_state() -> GameState:
    return GameState(
        world_id="hidden-leak-eval",
        locations={
            "square": LocationState(id="square", name="Square", exits={"north": "forge"}),
            "forge": LocationState(id="forge", name="Forge"),
        },
        player_visible_facts={"public_square"},
        facts={
            "public_square": FactState(
                id="public_square",
                text="The square is visible.",
                visibility=FactVisibility.PUBLIC,
                public=True,
            ),
            HIDDEN_FACT_ID: FactState(
                id=HIDDEN_FACT_ID,
                text=HIDDEN_FACT_TEXT,
                visibility=FactVisibility.HIDDEN,
                secret=True,
                known_by={"harlan"},
            ),
        },
        npcs={
            "harlan": NPCState(
                id="harlan",
                location_id="square",
                knowledge=[HIDDEN_FACT_ID],
                secrets=[NPC_SECRET],
            ),
            HIDDEN_WITNESS_ID: NPCState(
                id=HIDDEN_WITNESS_ID,
                location_id="square",
                hidden=True,
                visible=True,
                secrets=["saw_the_player"],
            ),
        },
        objects={
            HIDDEN_ITEM_ID: WorldObjectState(
                id=HIDDEN_ITEM_ID,
                name="Hidden dagger",
                location_id="square",
                hidden=True,
                tradeable=True,
                base_price=50,
            )
        },
        quests={
            HIDDEN_QUEST_ID: QuestState(
                id=HIDDEN_QUEST_ID,
                title="Hidden Letter Quest",
                description="Find the hidden letter.",
                initial_stage="start",
                current_stage="start",
                visibility=QuestVisibility.HIDDEN,
                status=QuestStatus.ACTIVE,
                known_to_player=False,
            )
        },
        crimes={
            "crime-1": CrimeState(
                id="crime-1",
                crime_type="theft",
                actor_id="player",
                location_id="square",
                witnessed_by=[HIDDEN_WITNESS_ID],
            )
        },
        witnesses={
            "crime-1:hidden_watcher": WitnessRecord(
                id="crime-1:hidden_watcher",
                npc_id=HIDDEN_WITNESS_ID,
                crime_id="crime-1",
                known_to_player=False,
            )
        },
        relationships={
            HIDDEN_RELATIONSHIP_ID: RelationshipState(
                id=HIDDEN_RELATIONSHIP_ID,
                source_id="harlan",
                target_id=HIDDEN_WITNESS_ID,
                relation_type="co_conspirator",
                trust=8,
                known_by_player=False,
            )
        },
        factions={
            "village": FactionState(
                id="village",
                name="Village",
                reputation=ReputationState(value=0, known_to_player=True),
                known_by_player=True,
            ),
            HIDDEN_FACTION_ID: FactionState(
                id=HIDDEN_FACTION_ID,
                name="Hidden Cabal",
                reputation=ReputationState(value=-10, known_to_player=False),
                relationships_to_other_factions={"village": -8},
                conflict_level=5,
                known_by_player=False,
            ),
        },
        rumors={
            "rumor-hidden": RumorState(
                id="rumor-hidden",
                fact_id=HIDDEN_FACT_ID,
                text_for_player=f"People whisper that {HIDDEN_FACT_TEXT}",
                truth_status="true",
                known_by_player=True,
                text=HIDDEN_RUMOR_TRUTH,
            )
        },
    )


def test_hidden_fact_hidden_witness_hidden_item_and_hidden_quest_do_not_enter_visible_state() -> None:
    state = make_hidden_leak_state()
    payload = build_visible_state(state).model_dump(mode="json")

    HiddenLeakCase(
        id="visible_state_core_boundaries",
        leak_type="hidden_fact",
        outlet="visible_state",
        forbidden_terms=[
            HIDDEN_FACT_TEXT,
            HIDDEN_FACT_ID,
            HIDDEN_WITNESS_ID,
            NPC_SECRET,
            HIDDEN_ITEM_ID,
            HIDDEN_QUEST_ID,
            HIDDEN_RUMOR_TRUTH,
        ],
        safe_reason="visible_state leaked hidden fact, witness, item, quest, rumor, or NPC secret identifier/text",
    ).assert_no_leak(payload)
    assert [fact["id"] for fact in payload["known_facts"]] == ["public_square"]
    assert payload["visible_objects"] == []
    assert payload["quests"] == []
    assert payload["known_rumors"][0]["text_for_player"] == (
        "You have heard a vague rumor, but not enough to confirm the details."
    )


def test_hidden_witness_and_raw_state_deltas_do_not_enter_player_api() -> None:
    app.state.settings = Settings(llm_provider="mock", llm_api_key="sk-test-fake-not-real")
    app.state.session_store = InMemorySessionStore()
    client = TestClient(app)
    session_id = client.post("/game/start").json()["session_id"]

    payload = client.post("/game/input", json={"session_id": session_id, "player_input": "observe"}).json()

    HiddenLeakCase(
        id="player_api_no_debug_or_hidden_witness",
        leak_type="raw_state_deltas",
        outlet="player_api",
        forbidden_terms=["state_deltas", HIDDEN_WITNESS_ID, "sk-test-fake-not-real"],
        safe_reason="player API leaked raw deltas, hidden witness, or test API key",
    ).assert_no_leak(payload)


def test_hidden_memory_debug_memory_and_npc_unknown_memory_do_not_enter_contexts() -> None:
    state = make_hidden_leak_state()
    store = InMemoryMemoryStore(
        [
            MemoryRecord(
                id="safe",
                content="The square looked quiet.",
                visibility=MemoryVisibility.NARRATOR_SAFE,
                entity_ids=["location:square"],
                fact_ids=["public_square"],
            ),
            MemoryRecord(
                id="hidden",
                content=HIDDEN_MEMORY_TEXT,
                visibility=MemoryVisibility.HIDDEN,
                fact_ids=[HIDDEN_FACT_ID],
            ),
            MemoryRecord(
                id="debug",
                content=DEBUG_MEMORY_TEXT,
                visibility=MemoryVisibility.DEBUG_ONLY,
            ),
            MemoryRecord(
                id="npc-unknown",
                content="NPC should not know this discoverable clue.",
                visibility=MemoryVisibility.NARRATOR_SAFE,
                fact_ids=["unknown_fact"],
            ),
        ]
    )

    context = MemoryContextBuilder(store).build(
        state=state,
        actor_id="player",
        current_location="square",
        action_result=ActionResult(success_level=SuccessLevel.SUCCESS, reason="Observed."),
        visible_facts=["public_square"],
        current_npc_id="harlan",
    )
    payload = {
        "narrator": [memory.content for memory in context.narrator_safe_memories],
        "player": [memory.content for memory in context.player_visible_memories],
        "npc": [memory.content for memory in context.npc_known_memories],
    }

    HiddenLeakCase(
        id="memory_context_hidden_debug_filter",
        leak_type="hidden_memory",
        outlet="memory_context",
        forbidden_terms=[HIDDEN_MEMORY_TEXT, DEBUG_MEMORY_TEXT],
        safe_reason="memory context leaked hidden or debug-only memory",
    ).assert_no_leak(payload)
    assert "The square looked quiet." in payload["narrator"]


def test_hidden_relationship_and_faction_conflict_do_not_enter_player_graphs() -> None:
    state = make_hidden_leak_state()
    relationship_graph = build_relationship_graph(state, debug=False).model_dump(mode="json")
    faction_graph = build_faction_graph(state, debug=False).model_dump(mode="json")
    debug_relationship_graph = build_relationship_graph(state, debug=True).model_dump(mode="json")

    HiddenLeakCase(
        id="player_graph_hidden_relationships",
        leak_type="hidden_relationship",
        outlet="player_graph",
        forbidden_terms=[HIDDEN_RELATIONSHIP_ID, HIDDEN_WITNESS_ID, HIDDEN_FACTION_ID, "Hidden Cabal"],
        safe_reason="player graph leaked hidden relationship, witness, faction, or conflict",
    ).assert_no_leak({"relationships": relationship_graph, "factions": faction_graph})
    assert HIDDEN_RELATIONSHIP_ID in json.dumps(debug_relationship_graph, ensure_ascii=False)


def test_hidden_map_edge_does_not_enter_player_map(tmp_path: Path) -> None:
    write_hidden_map_world(tmp_path)
    pack = WorldLoader(tmp_path).load("hidden_map")
    player_graph = build_player_visible_map_visual_graph(pack, ["square", "secret_room"]).model_dump(mode="json")

    HiddenLeakCase(
        id="player_map_hidden_edge",
        leak_type="hidden_map_edge",
        outlet="player_map",
        forbidden_terms=["secret_room", "Secret Room"],
        safe_reason="player map leaked hidden map node or edge",
    ).assert_no_leak(player_graph)
    assert player_graph["edges"] == []


def test_debug_api_isolated_from_player_api() -> None:
    app.state.settings = Settings(enable_debug_api=False, llm_provider="mock", llm_api_key="sk-test-fake-not-real")
    app.state.session_store = InMemorySessionStore()
    client = TestClient(app)
    session_id = client.post("/game/start").json()["session_id"]
    client.post("/game/input", json={"session_id": session_id, "player_input": "observe"})

    disabled_debug = client.get(f"/debug/sessions/{session_id}/events")
    player_payload = client.post("/game/input", json={"session_id": session_id, "player_input": "wait 30"}).json()

    assert disabled_debug.status_code == 403
    assert "state_deltas" not in json.dumps(player_payload, ensure_ascii=False)

    app.state.settings = Settings(enable_debug_api=True, llm_provider="mock", llm_api_key="sk-test-fake-not-real")
    enabled_debug = client.get(f"/debug/sessions/{session_id}/events")

    assert enabled_debug.status_code == 200
    assert "state_deltas" in json.dumps(enabled_debug.json(), ensure_ascii=False)


def test_scenario_and_quality_normal_reports_do_not_print_hidden_text() -> None:
    scenario_report = run_playtest_scenario(
        PlaytestScenario(
            id="hidden-leak-report-normal",
            world_id="mist_valley",
            name="Hidden leak report normal view",
            scenario_type=PlaytestScenarioType.HIDDEN_LEAK_PROBE,
            max_steps=0,
            forbidden_outcomes={"visible_facts": ["village_square_is_misty"]},
        )
    ).model_dump_normal()
    quality_report = WorldQualityReport(
        world_id="mist_valley",
        issues=[
            QualityIssue(
                id="hidden-detail",
                severity=QualityIssueSeverity.WARNING,
                category="visibility",
                message="Hidden detail redaction check.",
                hidden_details_debug_only={"hidden_fact_text": HIDDEN_FACT_TEXT},
            )
        ],
        summary={"hidden_details_debug_only": {"hidden_fact_text": HIDDEN_FACT_TEXT}},
    ).model_dump_normal()

    HiddenLeakCase(
        id="normal_reports_redact_hidden_text",
        leak_type="hidden_fact",
        outlet="scenario_report normal view and quality_report normal view",
        forbidden_terms=[HIDDEN_FACT_TEXT, "hidden_details_debug_only"],
        safe_reason="normal report leaked hidden text or debug-only field",
    ).assert_no_leak({"scenario_report": scenario_report, "quality_report": quality_report})


def write_hidden_map_world(root: Path) -> None:
    world_path = root / "hidden_map"
    world_path.mkdir()
    (world_path / "manifest.yaml").write_text(
        """
world_id: hidden_map
name: Hidden Map
version: "1.0"
start_location_id: square
""",
        encoding="utf-8",
    )
    (world_path / "locations.yaml").write_text(
        """
locations:
  - id: square
    name: Square
    description: Start.
    exits:
      north: secret_room
  - id: secret_room
    name: Secret Room
    description: Hidden.
    exits:
      south: square
    visual:
      visibility: hidden
""",
        encoding="utf-8",
    )
    for file_name, root_key in {
        "npcs.yaml": "npcs",
        "items.yaml": "items",
        "quests.yaml": "quests",
        "facts.yaml": "facts",
        "factions.yaml": "factions",
        "rumors.yaml": "rumors",
        "relationships.yaml": "relationships",
    }.items():
        (world_path / file_name).write_text(f"{root_key}: []\n", encoding="utf-8")
