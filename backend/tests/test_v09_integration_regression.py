import json
from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.migration_service import MigrationService
from app.db.repository import SQLiteSaveRepository
from app.evals.narrative_consistency import (
    NarrativeConsistencyRule,
    run_narrative_consistency_evals,
)
from app.main import app
from app.playtesting.batch import PlaytestBatchRunRequest, run_playtest_batch
from app.playtesting.runner import (
    PlaytestOptions,
    PlaytestScenario,
    PlaytestScenarioType,
    run_playtest,
    run_playtest_scenario,
)
from app.quality import QualityIssue, QualityIssueSeverity, WorldQualityReport
from app.quality.benchmarks import BenchmarkRunRequest, run_benchmark_suite
from app.quality.combat_balance import analyze_combat_balance
from app.quality.dead_end_detector import analyze_dead_ends
from app.quality.economy_balance import analyze_economy_balance
from app.quality.gate import QualityGateConfig, run_quality_gate
from app.quality.health_score import build_world_health_score
from app.quality.npc_behavior_coverage import analyze_npc_behavior_coverage
from app.quality.quest_analysis import analyze_quest_completion
from app.quality.save_load_stress import run_save_load_migration_stress
from app.quality.schedule_conflict_detector import analyze_schedule_conflicts
from app.quality.social_consequence_coverage import analyze_social_consequence_coverage
from app.session_store import InMemorySessionStore
from app.tools import quality_gate as quality_gate_cli

from .evals.narrative_consistency.test_narrative_consistency import _case
from .test_combat_balance import write_world as write_combat_world
from .test_dead_end_detector import write_world as write_dead_end_world
from .test_economy_balance import write_world as write_economy_world
from .test_npc_behavior_coverage import NPC_WITH_GOALS, write_world as write_npc_world
from .test_quest_completion_analysis import write_world as write_quest_world
from .test_save_load_stress import force_legacy_save, make_state, make_stress_events
from .test_schedule_conflict_detector import write_world as write_schedule_world
from .test_social_consequence_coverage import write_world as write_social_world


def make_client(tmp_path: Path, enabled: bool = True) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "v09_integration.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = tmp_path / "mods"
    app.state.playtest_reports = []
    app.state.playtest_batch_reports = []
    app.state.quality_gate_results = []
    app.state.settings = Settings(
        enable_eval_api=enabled,
        enable_playtest_api=enabled,
        enable_debug_api=False,
        llm_provider="local_stub",
        llm_api_key="test-secret-placeholder",
    )
    return TestClient(app)


def test_v09_quality_report_aggregation_and_hidden_safety() -> None:
    hidden_text = "A sealed letter is hidden beneath a loose paving stone."
    reports = [
        WorldQualityReport(
            world_id="mist_valley",
            categories=["structure"],
            issues=[
                QualityIssue(
                    id="blocker",
                    severity=QualityIssueSeverity.BLOCKER,
                    category="structure",
                    message="Blocker issue.",
                    hidden_details_debug_only={"secret": hidden_text},
                )
            ],
        ),
        WorldQualityReport(
            world_id="mist_valley",
            categories=["coverage"],
            issues=[
                QualityIssue(
                    id="warning",
                    severity=QualityIssueSeverity.WARNING,
                    category="coverage",
                    message="Coverage warning.",
                )
            ],
        ),
    ]

    health = build_world_health_score("mist_valley", reports)
    normal_payload = json.dumps([report.model_dump_normal() for report in reports], ensure_ascii=False)

    assert health.blockers == ["structure: Blocker issue."]
    assert health.overall_score < 100
    assert hidden_text not in normal_payload
    assert "hidden_details_debug_only" not in normal_payload


def test_v09_playtesting_scenarios_batch_and_boundaries_are_deterministic() -> None:
    exploration = run_playtest_scenario(
        PlaytestScenario(
            id="integration_explore",
            world_id="mist_valley",
            name="Integration Explore",
            scenario_type=PlaytestScenarioType.EXPLORATION,
            agent_type="explore_agent",
            max_steps=3,
            seed=44,
        )
    )
    save_load = run_playtest_scenario(
        PlaytestScenario(
            id="integration_save_load",
            world_id="mist_valley",
            name="Integration Save Load",
            scenario_type=PlaytestScenarioType.SAVE_LOAD_PATH,
            agent_type="random_valid_action_agent",
            max_steps=3,
            seed=44,
        )
    )
    leak_probe = run_playtest_scenario(
        PlaytestScenario(
            id="integration_hidden_leak",
            world_id="mist_valley",
            name="Integration Hidden Leak",
            scenario_type=PlaytestScenarioType.HIDDEN_LEAK_PROBE,
            agent_type="random_valid_action_agent",
            max_steps=1,
            seed=44,
            forbidden_outcomes={"visible_facts": ["village_square_is_misty"]},
        )
    )
    first = run_playtest(PlaytestOptions(world_id="mist_valley", strategy="random_valid_action_agent", max_steps=4, seed=9))
    second = run_playtest(PlaytestOptions(world_id="mist_valley", strategy="random_valid_action_agent", max_steps=4, seed=9))
    batch = run_playtest_batch(
        PlaytestBatchRunRequest(
            world_id="mist_valley",
            agent_types=["random_valid_action_agent", "explore_agent"],
            seeds=[1, 2],
            steps=2,
            save_load_check=True,
        )
    )

    assert exploration.playtest_report.turns_run == 3
    assert save_load.playtest_report.save_load_failures == []
    assert not leak_probe.passed
    assert "village_square_is_misty" in " ".join(leak_probe.hidden_leak_summary)
    assert [action.input_text for action in first.actions_taken] == [action.input_text for action in second.actions_taken]
    assert batch.total_runs == 4
    assert batch.failed == 0
    assert batch.coverage_summary.seeds_run == [1, 2]


def test_v09_static_quality_analyzers_find_reachability_npc_balance_and_social_issues(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest"
    quest_root.mkdir()
    write_quest_world(
        quest_root,
        """
quests:
  - id: broken
    title: Broken
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [find_key]
        next_stages: [missing_stage]
      - id: orphan
        title: Orphan
        objectives: []
        next_stages: []
    triggers: []
""",
    )
    dead_root = tmp_path / "dead"
    dead_root.mkdir()
    write_dead_end_world(
        dead_root,
        facts_yaml="""
facts:
  - id: hidden_clue
    text: Secret clue text.
    visibility: hidden
    known_by: []
""",
        quests_yaml="""
quests:
  - id: clue_quest
    title: Clue Quest
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [discover_truth]
        next_stages: []
    triggers:
      - type: fact_discovered
        id: hidden_clue
        action: complete_objective
        objective_id: discover_truth
""",
    )
    locked_root = tmp_path / "locked"
    locked_root.mkdir()
    write_dead_end_world(
        locked_root,
        locations_yaml="""
locations:
  - id: square
    name: Square
    description: Start.
    exits:
      north: sealed_room
  - id: sealed_room
    name: Sealed Room
    description: Locked.
    exits: {}
    visual:
      visibility: hidden
      tags: [locked]
""",
        quests_yaml="""
quests:
  - id: sealed_room_quest
    title: Sealed Room Quest
    initial_stage: start
    visibility: public
    stages:
      - id: start
        title: Start
        objectives: [enter_room]
        next_stages: []
    triggers:
      - type: location_visited
        id: sealed_room
        action: complete_objective
        objective_id: enter_room
""",
    )
    npc_root = tmp_path / "npc"
    npc_root.mkdir()
    write_npc_world(npc_root, npcs_yaml=NPC_WITH_GOALS)
    schedule_root = tmp_path / "schedule"
    schedule_root.mkdir()
    write_schedule_world(
        schedule_root,
        npcs_yaml="""
npcs:
  - id: harlan
    name: Harlan
    location_id: square
    personality: Practical.
    schedule:
      - time_of_day: morning
        location_id: missing_forge
        activity: hammering
""",
    )
    economy_root = tmp_path / "economy"
    economy_root.mkdir()
    write_economy_world(
        economy_root,
        npcs_yaml="""
npcs:
  - id: mira
    name: Mira
    location_id: square
    personality: Sharp.
    merchant: true
    shop_inventory: [apple]
    buy_price_modifier: 0.5
    sell_price_modifier: 1.5
""",
    )
    combat_root = tmp_path / "combat"
    combat_root.mkdir()
    write_combat_world(
        combat_root,
        locations_yaml="""
locations:
  - id: arena
    name: Arena
    description: No way out.
    exits: {}
""",
        npcs_yaml="""
npcs:
  - id: iron_duelist
    name: Iron Duelist
    location_id: arena
    personality: Merciless.
    tags: [enemy, lethal]
    hp: 40
    max_hp: 40
    attack: 10
    defense: 2
    hostile_to: [player]
""",
    )
    social_root = tmp_path / "social"
    social_root.mkdir()
    write_social_world(
        social_root,
        rumors_yaml="""
rumors:
  - id: missing_faction_rumor
    fact_id: public_fact
    text_for_player: A public rumor.
    known_by_factions: [missing_faction]
    tags: [crime]
""",
    )

    quest = analyze_quest_completion("test_world", worlds_root=quest_root)
    dead = analyze_dead_ends("test_world", worlds_root=dead_root)
    locked = analyze_dead_ends("test_world", worlds_root=locked_root)
    npc = analyze_npc_behavior_coverage("test_world", worlds_root=npc_root)
    schedule = analyze_schedule_conflicts("test_world", worlds_root=schedule_root)
    economy = analyze_economy_balance("test_world", worlds_root=economy_root)
    combat = analyze_combat_balance("test_world", worlds_root=combat_root)
    social = analyze_social_consequence_coverage("test_world", worlds_root=social_root)

    assert quest.missing_next_stage_refs and quest.unreachable_stages
    assert dead.hidden_clue_never_discoverable
    assert locked.locked_door_without_key_path
    assert npc.unused_goal_warnings
    assert schedule.invalid_schedule_locations
    assert economy.arbitrage_risks
    assert combat.unavoidable_lethal_encounters
    assert social.missing_faction_effect_issues
    normal_payload = json.dumps(dead.model_dump_normal(), ensure_ascii=False)
    assert "Secret clue text" not in normal_payload


def test_v09_stress_benchmark_narrative_and_quality_gate_api_cli_work_together(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    repository = SQLiteSaveRepository(tmp_path / "stress.db")
    initial_state = make_state()
    final_state, events = make_stress_events(initial_state, count=105)
    stress = run_save_load_migration_stress(
        repository=repository,
        save_id="integration-stress",
        initial_state=final_state,
        events=events,
        save_load_cycles=3,
    )
    legacy_events = [
        event.model_copy(update={"event_id": f"legacy-{event.event_id}"})
        for event in events
    ]
    repository.save_snapshot("legacy-stress", final_state, legacy_events)
    force_legacy_save(repository, "legacy-stress", final_state)
    dry_run = MigrationService(repository).dry_run("legacy-stress")
    applied = MigrationService(repository).apply("legacy-stress")
    benchmark = run_benchmark_suite(
        BenchmarkRunRequest(
            world_id="mist_valley",
            iterations=1,
            benchmarks=["validate_world", "memory_search"],
            thresholds_ms={"validate_world": 0.001},
        )
    )
    narrative = run_narrative_consistency_evals(
        [
            _case("harlan says hello.", dead_npc_ids=["harlan"]),
            _case("The player finds the moon_sword.", invented_item_terms=["moon_sword"]),
            _case("hidden_watcher reveals a witness.", hidden_witness_ids=["hidden_watcher"]),
            _case("It is certain that harlan betrayed the town.", memory_only_facts=["harlan betrayed the town"]),
        ]
    )
    gate_api = client.post(
        "/quality/worlds/mist_valley/gate/run",
        json={"allow_warnings": True, "fail_on_error": False, "min_health_score": 0, "playtest_steps": 1},
    )
    disabled_client = make_client(tmp_path / "disabled", enabled=False)
    disabled_gate = disabled_client.post("/quality/worlds/mist_valley/gate/run", json={})
    cli_exit = quality_gate_cli.main(
        ["--world", "mist_valley", "--allow-errors", "--allow-blockers", "--min-health-score", "0", "--json"]
    )

    assert stress.turns == 105
    assert dry_run.dry_run is True
    assert applied.success is True
    assert benchmark.regressions
    serialized_benchmark = json.dumps(benchmark.model_dump_safe(), ensure_ascii=False).lower()
    assert "api_key" not in serialized_benchmark
    assert narrative.failed == 4
    reasons = " ".join(reason for case in narrative.case_results for reason in case.failure_reasons)
    assert NarrativeConsistencyRule.NO_DEAD_NPC_SPEAKING in reasons
    assert NarrativeConsistencyRule.NO_ITEM_INVENTED in reasons
    assert NarrativeConsistencyRule.NO_HIDDEN_WITNESS_REVEALED in reasons
    assert NarrativeConsistencyRule.NO_MEMORY_AS_AUTHORITATIVE_FACT in reasons
    assert gate_api.status_code == 200
    assert gate_api.json()["report_links"]
    assert disabled_gate.status_code == 403
    assert cli_exit == 0


def test_v09_player_boundaries_and_frontend_dashboard_contracts(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    start = client.post("/game/start", json={"world_id": "mist_valley"}).json()
    session_id = start["session_id"]
    state_text = client.get(f"/game/state/{session_id}").text
    client.post("/game/input", json={"session_id": session_id, "player_input": "observe"})
    events = client.get(f"/debug/sessions/{session_id}/events")
    batch = client.post(
        "/playtests/batch/run",
        json={"world_id": "mist_valley", "agent_types": ["random_valid_action_agent"], "seeds": [1, 2], "steps": 1},
    )
    source = Path("frontend/src/App.tsx").read_text(encoding="utf-8")

    assert "state_deltas" not in state_text
    assert "sealed_letter" not in state_text
    assert events.status_code == 403
    assert batch.status_code == 200
    assert "A sealed letter is hidden beneath a loose paving stone." not in batch.text
    assert "PlaytestingDashboard" in source
    assert "WorldHealthDashboard" in source
    assert "ContentCoverageDashboard" in source
    assert "PerformanceDashboard" in source
