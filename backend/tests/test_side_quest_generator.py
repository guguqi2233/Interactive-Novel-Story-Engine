from pathlib import Path

import pytest

from app.engine.content.side_quest_generator import (
    QuestDraft,
    QuestDraftStage,
    QuestDraftTrigger,
    llm_assisted_generate_side_quest,
    rule_based_generate_side_quest,
    validate_quest_draft,
)
from app.engine.content.world_loader import WorldLoader
from app.llm.fake_provider import FakeLLMProvider
from app.llm.provider_base import LLMProviderError


def load_pack():
    return WorldLoader("worlds").load("mist_valley")


def test_rule_based_generator_creates_quest_draft() -> None:
    pack = load_pack()
    state = pack.to_game_state()
    before_state = state.model_dump_json()

    draft = rule_based_generate_side_quest(pack, state)
    report = validate_quest_draft(draft, pack)

    assert isinstance(draft, QuestDraft)
    assert draft.title
    assert draft.stages
    assert report.ok
    assert state.model_dump_json() == before_state


def test_quest_draft_references_existing_content() -> None:
    pack = load_pack()
    draft = rule_based_generate_side_quest(pack)
    npc_ids = {npc.id for npc in pack.npcs}
    location_ids = {location.id for location in pack.locations}
    item_ids = {item.id for item in pack.items}

    assert set(draft.involved_npcs).issubset(npc_ids)
    assert set(draft.involved_locations).issubset(location_ids)
    assert set(draft.involved_items).issubset(item_ids)


def test_invalid_generated_reference_is_caught() -> None:
    pack = load_pack()
    draft = QuestDraft(
        title="Bad Draft",
        premise="A harmless premise.",
        involved_npcs=["missing_npc"],
        stages=[QuestDraftStage(id="start", title="Start")],
    )

    report = validate_quest_draft(draft, pack)

    assert not report.ok
    assert report.errors[0].code == "missing_npc"


def test_llm_assisted_generator_uses_fake_provider() -> None:
    pack = load_pack()
    provider = FakeLLMProvider(
        json_responses=[
            {
                "title": "Bridge Errand",
                "premise": "Harlan needs help checking a public lead near the old bridge.",
                "involved_npcs": ["harlan"],
                "involved_locations": ["old_bridge"],
                "involved_items": [],
                "required_facts": ["old_bridge_creaks_at_midnight"],
                "stages": [
                    {
                        "id": "ask_harlan",
                        "title": "Ask Harlan",
                        "description": "Ask Harlan what he heard.",
                        "objectives": ["talk_to_harlan"],
                        "next_stages": [],
                    }
                ],
                "triggers": [
                    {
                        "type": "npc_talked",
                        "id": "harlan",
                        "action": "complete_objective",
                        "objective_id": "talk_to_harlan",
                    }
                ],
                "rewards": ["small_payment"],
                "risk_flags": ["author_review"],
                "validation_notes": ["Fake provider draft."],
            }
        ]
    )

    draft = llm_assisted_generate_side_quest(pack, provider)

    assert draft.title == "Bridge Errand"
    assert draft.involved_npcs == ["harlan"]


def test_llm_output_schema_error_is_caught() -> None:
    pack = load_pack()
    provider = FakeLLMProvider(json_responses=[{"title": "Missing premise"}])

    with pytest.raises(LLMProviderError, match="schema validation"):
        llm_assisted_generate_side_quest(pack, provider)


def test_generator_does_not_write_quests_yaml(tmp_path: Path) -> None:
    source_pack = load_pack()
    world_path = tmp_path / "draft_world"
    world_path.mkdir()
    quests_path = world_path / "quests.yaml"
    quests_path.write_text("quests: []\n", encoding="utf-8")

    before = quests_path.read_text(encoding="utf-8")
    rule_based_generate_side_quest(source_pack, source_pack.to_game_state())

    assert quests_path.read_text(encoding="utf-8") == before


def test_hidden_fact_text_not_in_player_facing_draft() -> None:
    pack = load_pack()
    hidden_text = next(fact.text for fact in pack.facts if fact.id == "sealed_letter_under_stone")
    draft = rule_based_generate_side_quest(pack)

    payload = " ".join(
        [
            draft.title,
            draft.premise,
            *[stage.title + " " + stage.description for stage in draft.stages],
        ]
    )

    assert hidden_text not in payload


def test_hidden_fact_text_leak_fails_validation() -> None:
    pack = load_pack()
    hidden_text = next(fact.text for fact in pack.facts if fact.id == "sealed_letter_under_stone")
    draft = QuestDraft(
        title="Leaky Draft",
        premise=hidden_text,
        required_facts=["sealed_letter_under_stone"],
        stages=[QuestDraftStage(id="start", title="Start")],
        triggers=[QuestDraftTrigger(type="fact_discovered", id="sealed_letter_under_stone")],
    )

    report = validate_quest_draft(draft, pack)

    assert not report.ok
    assert any(issue.code == "hidden_fact_text_leak" for issue in report.errors)
