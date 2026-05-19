from __future__ import annotations

from pathlib import Path
from shutil import copytree

import yaml

from app.core.world_state import GameState
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.quest_pack_generator import (
    QuestPackGeneratorApplyRequest,
    QuestPackGeneratorDraft,
    apply_quest_pack_generator,
    preview_quest_pack_generator,
)


def _service(tmp_path: Path) -> ContentAuthoringService:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return ContentAuthoringService(worlds_root)


def _draft(**overrides: object) -> QuestPackGeneratorDraft:
    values = {
        "target_world_id": "mist_valley",
        "pack_id": "bridge_case",
        "theme": "bridge mystery",
        "quest_count": 2,
        "involved_npcs": ["harlan"],
        "involved_locations": ["village_square", "old_bridge"],
        "involved_factions": ["village_council"],
        "required_facts": [],
        "mystery_mode": True,
        "failure_paths_enabled": True,
        "reward_policy": "story",
    }
    values.update(overrides)
    return QuestPackGeneratorDraft(**values)


def test_quest_pack_generator_creates_quest_candidates(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_quest_pack_generator(_draft(quest_count=3), service)

    assert preview.validation.ok or {issue.code for issue in preview.validation.warnings} == {"quest_pack_hidden_objective_review", "quest_hidden_objective_leak_risk"}
    assert len(preview.generated.quest_candidates) == 3


def test_quest_pack_generator_quest_graph_is_valid(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_quest_pack_generator(_draft(mystery_mode=False), service)

    assert preview.generated.quest_graph is not None
    assert len(preview.generated.quest_graph.quests) == 2
    assert preview.validation.ok


def test_quest_pack_generator_scenario_regression_draft_generated(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_quest_pack_generator(_draft(mystery_mode=False, quest_count=1), service)

    assert len(preview.generated.scenario_regression_candidates) == 1
    scenario = preview.generated.scenario_regression_candidates[0]
    assert scenario.world_id == "mist_valley"
    assert scenario.expected_quest_states == {"bridge_case_quest_1": "active"}


def test_quest_pack_generator_hidden_facts_not_in_player_text(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_quest_pack_generator(_draft(mystery_mode=True, quest_count=1), service)

    facts = yaml.safe_load(preview.yaml_contents["facts.yaml"])["facts"]
    generated_fact = next(fact for fact in facts if fact["id"] == "bridge_case_quest_1_clue")
    assert generated_fact["visibility"] == "hidden"
    quest_text = yaml.safe_dump(preview.generated.quest_candidates, sort_keys=False, allow_unicode=True)
    assert "Hidden quest clue" not in quest_text


def test_quest_pack_generator_invalid_refs_are_caught(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_quest_pack_generator(
        _draft(involved_npcs=["missing_npc"], involved_locations=["missing_location"]),
        service,
    )

    assert not preview.validation.ok
    assert {issue.code for issue in preview.validation.errors} >= {
        "quest_pack_missing_npc",
        "quest_pack_missing_location",
    }


def test_quest_pack_generator_preview_does_not_write_disk(tmp_path: Path) -> None:
    service = _service(tmp_path)
    path = service.worlds_root / "mist_valley" / "quests.yaml"
    before = path.read_text(encoding="utf-8")

    preview = preview_quest_pack_generator(_draft(mystery_mode=False), service)

    assert preview.writes_to_disk is False
    assert preview.applied is False
    assert path.read_text(encoding="utf-8") == before


def test_quest_pack_generator_apply_uses_validation(tmp_path: Path) -> None:
    service = _service(tmp_path)

    result = apply_quest_pack_generator(
        QuestPackGeneratorApplyRequest(draft=_draft(mystery_mode=False), confirm_apply=True, confirm_warnings=True),
        service,
    )

    assert result.applied is True
    quests = yaml.safe_load((service.worlds_root / "mist_valley" / "quests.yaml").read_text(encoding="utf-8"))["quests"]
    assert "bridge_case_quest_1" in {quest["id"] for quest in quests}


def test_quest_pack_generator_does_not_modify_active_game_state(tmp_path: Path) -> None:
    service = _service(tmp_path)
    state = GameState(world_id="mist_valley")
    before = state.model_dump(mode="json")

    preview_quest_pack_generator(_draft(mystery_mode=False), service)
    apply_quest_pack_generator(
        QuestPackGeneratorApplyRequest(draft=_draft(mystery_mode=False), confirm_apply=True, confirm_warnings=True),
        service,
    )

    assert state.model_dump(mode="json") == before


def test_quest_pack_generator_does_not_call_real_api() -> None:
    source = Path("backend/app/engine/content/quest_pack_generator.py").read_text(encoding="utf-8")

    assert "OpenAI" not in source
    assert "create_llm_provider" not in source
    assert "generate_json" not in source
