from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.world_state import GameState
from app.engine.content.world_pack_wizard import (
    WorldPackWizard,
    WorldPackWizardApplyRequest,
    WorldPackWizardDraft,
)


def _draft(**overrides: object) -> WorldPackWizardDraft:
    values = {
        "world_id": "wizard_world",
        "name": "Wizard World",
        "genre": "mystery",
        "tone": "grounded",
        "description": "A deterministic local world pack draft.",
        "starting_location": "arrival_square",
        "location_seed_count": 2,
        "npc_seed_count": 1,
        "quest_seed_count": 1,
        "enabled_systems": ["quests", "roleplay", "npc_simulation", "factions", "rumors"],
        "default_prompt_profile": "default_safe",
        "default_quality_profile": "standard",
    }
    values.update(overrides)
    return WorldPackWizardDraft(**values)


def test_world_pack_wizard_draft_can_be_generated(tmp_path: Path) -> None:
    wizard = WorldPackWizard(tmp_path / "worlds")

    draft = wizard.create_draft(**_draft().model_dump())

    assert draft.world_id == "wizard_world"
    assert draft.default_prompt_profile == "default_safe"
    assert draft.llm_assisted is False


def test_world_pack_wizard_preview_does_not_write_disk(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    wizard = WorldPackWizard(worlds_root)

    preview = wizard.preview_files(_draft())

    assert preview.writes_to_disk is False
    assert preview.applied is False
    assert sorted(path.name for path in worlds_root.rglob("*")) == []
    assert {file.file_name for file in preview.generated_files} >= {
        "manifest.yaml",
        "locations.yaml",
        "npcs.yaml",
        "items.yaml",
        "quests.yaml",
        "facts.yaml",
    }


def test_world_pack_wizard_apply_generates_world_pack_files(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    wizard = WorldPackWizard(worlds_root)
    draft = _draft()

    result = wizard.apply_to_worlds_directory(
        WorldPackWizardApplyRequest(draft=draft, confirm_apply=True, confirm_warnings=True)
    )

    assert result.applied is True
    assert result.gate_allowed_to_save is True
    world_path = worlds_root / draft.world_id
    assert (world_path / "manifest.yaml").exists()
    assert (world_path / "locations.yaml").exists()
    assert (world_path / "factions.yaml").exists()
    assert (world_path / "rumors.yaml").exists()


def test_world_pack_wizard_invalid_world_id_rejected() -> None:
    with pytest.raises(ValidationError):
        _draft(world_id="../outside")


def test_world_pack_wizard_validation_errors_block_apply(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    (worlds_root / "wizard_world").mkdir(parents=True)
    wizard = WorldPackWizard(worlds_root)

    result = wizard.apply_to_worlds_directory(
        WorldPackWizardApplyRequest(draft=_draft(), confirm_apply=True, confirm_warnings=True)
    )

    assert result.applied is False
    assert result.validation is not None
    assert any(issue.code == "world_pack_wizard_world_exists" for issue in result.validation.errors)


def test_world_pack_wizard_does_not_modify_active_game_state(tmp_path: Path) -> None:
    wizard = WorldPackWizard(tmp_path / "worlds")
    state = GameState(world_id="active_world")
    before = state.model_dump(mode="json")

    wizard.preview_files(_draft())
    wizard.apply_to_worlds_directory(WorldPackWizardApplyRequest(draft=_draft(), confirm_apply=True))

    assert state.model_dump(mode="json") == before


def test_world_pack_wizard_does_not_call_real_api() -> None:
    source = Path("backend/app/engine/content/world_pack_wizard.py").read_text(encoding="utf-8")

    assert "OpenAI" not in source
    assert "create_llm_provider" not in source
    assert "generate_json" not in source
