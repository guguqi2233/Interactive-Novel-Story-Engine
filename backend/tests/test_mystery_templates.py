from __future__ import annotations

from pathlib import Path
from shutil import copytree

import yaml

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.mystery_templates import (
    MysteryTemplatePreviewRequest,
    apply_mystery_template,
    list_mystery_templates,
    preview_mystery_template,
)


def _service(tmp_path: Path) -> ContentAuthoringService:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return ContentAuthoringService(worlds_root)


def _request(**kwargs: object) -> MysteryTemplatePreviewRequest:
    values = {"target_world_id": "mist_valley"}
    values.update(kwargs)
    return MysteryTemplatePreviewRequest(**values)


def test_mystery_template_can_load() -> None:
    templates = list_mystery_templates()

    assert {template.id for template in templates} >= {"missing_heirloom_case"}


def test_mystery_truth_fact_is_hidden(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_mystery_template("missing_heirloom_case", _request(), service)

    truth = next(fact for fact in preview.generated.facts_draft if fact["id"] == "missing_heirloom_truth")
    assert truth["visibility"] == "hidden"
    assert preview.validation.ok


def test_mystery_clue_path_is_generated(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_mystery_template("missing_heirloom_case", _request(), service)

    assert preview.generated.questline_draft
    quest = preview.generated.questline_draft[0]
    trigger_ids = {trigger["id"] for trigger in quest["triggers"]}
    assert "heirloom_clue_1_fact" in trigger_ids


def test_mystery_red_herring_is_marked(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_mystery_template("missing_heirloom_case", _request(), service)

    red = next(fact for fact in preview.generated.facts_draft if fact["id"] == "heirloom_red_herring_smugglers")
    assert "red_herring" in red["tags"]


def test_mystery_hidden_truth_not_in_player_facing_text(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_mystery_template("missing_heirloom_case", _request(), service)

    player_text = yaml.safe_dump(
        {
            "quests": preview.generated.questline_draft,
            "rumors": preview.generated.rumor_draft,
            "items": preview.generated.evidence_items_draft,
        },
        sort_keys=False,
        allow_unicode=True,
    )
    assert "Harlan hid the heirloom" not in player_text


def test_mystery_scenario_regression_draft_generated(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_mystery_template("missing_heirloom_case", _request(), service)

    assert preview.generated.scenario_regression_draft
    scenario = preview.generated.scenario_regression_draft[0]
    assert scenario.forbidden_visible_facts == ["missing_heirloom_truth"]


def test_mystery_apply_uses_validation_gate(tmp_path: Path) -> None:
    service = _service(tmp_path)

    result = apply_mystery_template(
        "missing_heirloom_case",
        _request(confirm_apply=True, confirm_warnings=True),
        service,
    )

    assert result.applied is True
    facts = yaml.safe_load((service.worlds_root / "mist_valley" / "facts.yaml").read_text(encoding="utf-8"))["facts"]
    assert "missing_heirloom_truth" in {fact["id"] for fact in facts}


def test_mystery_template_does_not_call_real_api() -> None:
    source = Path("backend/app/engine/content/mystery_templates.py").read_text(encoding="utf-8")

    assert "OpenAI" not in source
    assert "create_llm_provider" not in source
    assert "generate_json" not in source
