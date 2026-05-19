from __future__ import annotations

from pathlib import Path
from shutil import copytree

import yaml

from app.core.world_state import GameState
from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.npc_pack_generator import (
    NPCPackGeneratorApplyRequest,
    NPCPackGeneratorDraft,
    NPCPackGeneratorExportRequest,
    apply_npc_pack_generator,
    export_npc_pack_generator,
    preview_npc_pack_generator,
)


def _service(tmp_path: Path) -> ContentAuthoringService:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return ContentAuthoringService(worlds_root)


def _draft(**overrides: object) -> NPCPackGeneratorDraft:
    values = {
        "target_world_id": "mist_valley",
        "pack_id": "harbor_faces",
        "theme": "fog harbor",
        "faction_ids": ["village_council"],
        "location_ids": ["village_square", "blacksmith"],
        "npc_count": 3,
        "archetypes": ["guard", "informant", "merchant"],
        "rp_style": "restrained",
        "simulation_preset_ids": ["guard"],
        "relationship_density": 0.5,
        "hidden_secret_ratio": 0.5,
    }
    values.update(overrides)
    return NPCPackGeneratorDraft(**values)


def test_npc_pack_generator_creates_requested_candidates(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_npc_pack_generator(_draft(npc_count=4), service)

    assert preview.validation.ok
    assert len(preview.generated.npc_candidates) == 4
    assert len(preview.generated.rp_profiles) == 4
    assert len(preview.generated.voice_profiles) == 4


def test_npc_pack_generator_marks_hidden_secrets(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_npc_pack_generator(_draft(npc_count=2, hidden_secret_ratio=1.0), service)

    secrets = [secret for npc in preview.generated.npc_candidates for secret in npc.hidden_secrets]
    assert secrets
    assert all(secret.hidden and secret.visibility == "hidden" for secret in secrets)
    facts = yaml.safe_load(preview.yaml_contents["facts.yaml"])["facts"]
    generated_facts = [fact for fact in facts if str(fact.get("id", "")).startswith("harbor_faces_npc_")]
    assert generated_facts
    assert all(fact["visibility"] == "hidden" for fact in generated_facts)


def test_npc_pack_generator_invalid_faction_and_location_are_caught(tmp_path: Path) -> None:
    service = _service(tmp_path)

    preview = preview_npc_pack_generator(
        _draft(faction_ids=["missing_faction"], location_ids=["missing_location"]),
        service,
    )

    assert not preview.validation.ok
    assert {issue.code for issue in preview.validation.errors} >= {
        "npc_pack_missing_faction",
        "npc_pack_missing_location",
    }


def test_npc_pack_generator_preview_does_not_write_disk(tmp_path: Path) -> None:
    service = _service(tmp_path)
    npc_path = service.worlds_root / "mist_valley" / "npcs.yaml"
    before = npc_path.read_text(encoding="utf-8")

    preview = preview_npc_pack_generator(_draft(), service)

    assert preview.writes_to_disk is False
    assert preview.applied is False
    assert npc_path.read_text(encoding="utf-8") == before


def test_npc_pack_generator_apply_writes_after_validation_gate(tmp_path: Path) -> None:
    service = _service(tmp_path)

    result = apply_npc_pack_generator(
        NPCPackGeneratorApplyRequest(draft=_draft(), confirm_apply=True, confirm_warnings=True),
        service,
    )

    assert result.applied is True
    npc_yaml = yaml.safe_load((service.worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8"))
    ids = {npc["id"] for npc in npc_yaml["npcs"]}
    assert "harbor_faces_npc_1" in ids


def test_npc_pack_generator_does_not_modify_active_game_state(tmp_path: Path) -> None:
    service = _service(tmp_path)
    state = GameState(world_id="mist_valley")
    before = state.model_dump(mode="json")

    preview_npc_pack_generator(_draft(), service)
    apply_npc_pack_generator(
        NPCPackGeneratorApplyRequest(draft=_draft(), confirm_apply=True, confirm_warnings=True),
        service,
    )

    assert state.model_dump(mode="json") == before


def test_npc_pack_generator_export_pack_omits_api_key_and_hidden_facts(tmp_path: Path) -> None:
    service = _service(tmp_path)

    result = export_npc_pack_generator(
        NPCPackGeneratorExportRequest(draft=_draft(hidden_secret_ratio=1.0), safe_export=True),
        service,
    )

    assert result.exported_pack is not None
    payload = result.exported_pack.model_dump(mode="json")
    text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    assert "sk-" not in text
    assert "api_key" not in text.lower()
    assert "hidden fog harbor secret" not in text
    assert result.exported_pack.manifest.includes_hidden_facts is False


def test_npc_pack_generator_does_not_call_real_api() -> None:
    source = Path("backend/app/engine/content/npc_pack_generator.py").read_text(encoding="utf-8")

    assert "OpenAI" not in source
    assert "create_llm_provider" not in source
    assert "generate_json" not in source
