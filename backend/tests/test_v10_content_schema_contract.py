from pathlib import Path
from shutil import copytree

from app.engine.content.scenario_templates import ScenarioTemplateRenderer
from app.engine.content.validator import validate_world_pack


TEMPLATE_VARIABLES = {
    "world_id": "schema_contract_world",
    "world_name": "Schema Contract World",
    "start_location_id": "square",
    "npc_id": "mara",
    "npc_name": "Mara",
}


def test_v10_mist_valley_content_pack_contract_validates() -> None:
    report = validate_world_pack("mist_valley", worlds_root=Path("worlds"))

    assert report.ok
    assert report.errors == []


def test_v10_starter_templates_render_to_valid_content_pack(tmp_path: Path) -> None:
    templates_root = tmp_path / "templates"
    worlds_root = tmp_path / "worlds"
    copytree(Path("templates"), templates_root, dirs_exist_ok=True)
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    renderer = ScenarioTemplateRenderer(templates_root=templates_root, worlds_root=worlds_root)

    templates = renderer.list_templates()

    assert templates
    for template in templates:
        variables = dict(TEMPLATE_VARIABLES) if template.template_type == "world" else {}
        target_world_id = None if template.template_type == "world" else "mist_valley"
        preview = renderer.preview_template(template.id, variables, target_world_id=target_world_id)
        assert preview.validation_report is not None
        assert preview.validation_report.ok, template.id
        assert preview.writes_to_disk is False


def test_v10_invalid_content_schema_fixture_is_rejected(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    world_path = worlds_root / "bad_schema"
    copytree(Path("worlds") / "mist_valley", world_path)
    (world_path / "items.yaml").write_text(
        """
items:
  - id: invalid_double_placed_item
    name: Invalid Double Placed Item
    description: This item has conflicting placement fields.
    location_id: village_square
    owner_id: player
    portable: true
""".strip(),
        encoding="utf-8",
    )
    manifest = (world_path / "manifest.yaml").read_text(encoding="utf-8").replace("world_id: mist_valley", "world_id: bad_schema")
    (world_path / "manifest.yaml").write_text(manifest, encoding="utf-8")

    report = validate_world_pack("bad_schema", worlds_root=worlds_root)

    assert not report.ok
    assert any(issue.file == "items.yaml" and issue.code == "item_conflicting_ownership" for issue in report.errors)


def test_v10_hidden_fact_leakage_fixture_is_caught_by_validation(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    world_path = worlds_root / "hidden_leak"
    copytree(Path("worlds") / "mist_valley", world_path)
    manifest = (world_path / "manifest.yaml").read_text(encoding="utf-8").replace("world_id: mist_valley", "world_id: hidden_leak")
    (world_path / "manifest.yaml").write_text(manifest, encoding="utf-8")
    original_facts = (world_path / "facts.yaml").read_text(encoding="utf-8")
    (world_path / "facts.yaml").write_text(
        original_facts
        + "\n"
        + "  - id: hidden_vault_truth\n"
        + "    text: The mayor hid the vault key under the bridge.\n"
        + "    visibility: hidden\n"
        + "    known_by:\n"
        + "      - harlan\n"
        + "    tags:\n"
        + "      - secret\n",
        encoding="utf-8",
    )
    original_rumors = (world_path / "rumors.yaml").read_text(encoding="utf-8")
    (world_path / "rumors.yaml").write_text(
        original_rumors
        + "\n"
        + "  - id: unsafe_vault_rumor\n"
        + "    fact_id: hidden_vault_truth\n"
        + "    text_for_player: The mayor hid the vault key under the bridge.\n"
        + "    truth_status: unknown\n"
        + "    known_by_npcs:\n"
        + "      - harlan\n"
        + "    known_by_factions:\n"
        + "      - village_council\n"
        + "    known_by_player: false\n"
        + "    spread_level: 1\n"
        + "    tags:\n"
        + "      - secret\n",
        encoding="utf-8",
    )

    report = validate_world_pack("hidden_leak", worlds_root=worlds_root)

    assert report.ok
    warning = next(issue for issue in report.warnings if issue.code == "rumor_reveals_hidden_fact")
    assert warning.file == "rumors.yaml"
    assert warning.ref_id == "hidden_vault_truth"
