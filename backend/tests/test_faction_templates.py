from __future__ import annotations

from pathlib import Path
from shutil import copytree

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.faction_templates import (
    FactionTemplate,
    FactionTemplatePreviewRequest,
    FactionTemplateRelation,
    apply_faction_template,
    list_faction_templates,
    preview_faction_template,
    preview_faction_template_object,
)
from app.engine.content.world_loader import WorldLoader
from app.engine.rules.graphs import build_faction_graph


def _service(tmp_path: Path) -> ContentAuthoringService:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return ContentAuthoringService(worlds_root)


def _request(**kwargs: object) -> FactionTemplatePreviewRequest:
    values = {"target_world_id": "mist_valley"}
    values.update(kwargs)
    return FactionTemplatePreviewRequest(**values)


def test_faction_template_can_load() -> None:
    templates = list_faction_templates()

    assert {template.id for template in templates} >= {"city_watch", "secret_cell"}


def test_faction_relations_draft_can_generate(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_faction_template("city_watch", _request(), service)

    assert preview.validation.ok
    faction = preview.generated.factions_draft[0]
    assert faction["relations"]["old_road_smugglers"] == -25
    assert preview.generated.relationship_candidates[0]["relation_type"] == "hostile"


def test_faction_template_generates_npc_duty_candidates(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_faction_template("city_watch", _request(), service)

    duty_types = {duty["duty_type"] for duty in preview.generated.npc_faction_duty_candidates}
    assert {"guard_location", "report_crime_to_faction"} <= duty_types


def test_hidden_faction_does_not_enter_player_graph(tmp_path: Path) -> None:
    service = _service(tmp_path)

    result = apply_faction_template(
        "secret_cell",
        _request(confirm_apply=True, confirm_warnings=True),
        service,
    )
    state = WorldLoader(service.worlds_root).load("mist_valley").to_game_state()
    player_graph = build_faction_graph(state, debug=False)
    debug_graph = build_faction_graph(state, debug=True)

    assert result.applied is True
    assert "secret_cell" not in {node.id for node in player_graph.nodes}
    assert "secret_cell" in {node.id for node in debug_graph.nodes}


def test_invalid_relation_is_caught(tmp_path: Path) -> None:
    service = _service(tmp_path)
    template = FactionTemplate(
        id="bad_faction",
        name="Bad Faction",
        faction_type="bad",
        relations=[FactionTemplateRelation(target_faction_id="missing_faction", value=-10)],
    )

    preview = preview_faction_template_object(template, _request(), service)

    assert not preview.validation.ok
    assert any(issue.code == "faction_template_invalid_relation" for issue in preview.validation.errors)


def test_faction_template_preview_does_not_write_disk(tmp_path: Path) -> None:
    service = _service(tmp_path)
    path = service.worlds_root / "mist_valley" / "factions.yaml"
    before = path.read_text(encoding="utf-8")

    preview = preview_faction_template("city_watch", _request(), service)

    assert preview.writes_to_disk is False
    assert preview.applied is False
    assert path.read_text(encoding="utf-8") == before


def test_faction_template_does_not_call_llm() -> None:
    source = Path("backend/app/engine/content/faction_templates.py").read_text(encoding="utf-8")

    assert "OpenAI" not in source
    assert "create_llm_provider" not in source
    assert "generate_json" not in source
