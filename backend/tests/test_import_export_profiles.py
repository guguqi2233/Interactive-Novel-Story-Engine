from __future__ import annotations

import pytest

from app.engine.content.authoring_service import ContentAuthoringService
from app.engine.content.character_pack_builder import (
    CharacterPack,
    CharacterPackExportRequest,
    CharacterPackFile,
    CharacterPackImportRequest,
    CharacterPackManifest,
    export_character_pack,
)
from app.engine.content.import_export_profiles import (
    ExportProfile,
    ImportProfile,
    apply_export_profile_to_character_pack,
    character_pack_export_request_for_profile,
    get_export_profile,
    get_import_profile,
    validate_character_pack_import_profile,
)


def test_safe_export_profile_excludes_hidden_facts_and_api_keys() -> None:
    service = ContentAuthoringService("worlds")
    profile = get_export_profile("safe")
    request = character_pack_export_request_for_profile(
        CharacterPackExportRequest(world_id="mist_valley", include_hidden_facts=True),
        profile,
    )

    pack = apply_export_profile_to_character_pack(export_character_pack(request, service), profile)

    serialized = pack.model_dump_json()
    assert "sealed_letter_under_stone" not in serialized
    assert "A sealed letter is hidden beneath a loose paving stone" not in serialized
    assert "sk-" not in serialized.lower()
    assert pack.manifest.includes_hidden_facts is False


def test_authoring_export_profile_includes_hidden_ids_with_redacted_text() -> None:
    service = ContentAuthoringService("worlds")
    profile = get_export_profile("authoring_redacted")
    request = character_pack_export_request_for_profile(
        CharacterPackExportRequest(world_id="mist_valley", include_hidden_facts=True),
        profile,
    )

    pack = apply_export_profile_to_character_pack(export_character_pack(request, service), profile)

    hidden = [candidate for candidate in pack.fact_candidates if candidate.id == "sealed_letter_under_stone"]
    assert hidden
    assert hidden[0].text == "[redacted]"
    assert "hidden_authoring_data" in hidden[0].tags
    assert "A sealed letter is hidden beneath a loose paving stone" not in pack.model_dump_json()
    assert pack.manifest.includes_hidden_facts is True


def test_import_profile_rejects_executable() -> None:
    pack = CharacterPack(
        manifest=CharacterPackManifest(
            pack_id="unsafe_pack",
            name="Unsafe Pack",
            exported_at="2026-01-01T00:00:00Z",
        ),
        files=[CharacterPackFile(path="scripts/install.py", content="print('nope')")],
    )

    report = validate_character_pack_import_profile(
        CharacterPackImportRequest(world_id="mist_valley", pack=pack),
        get_import_profile("safe"),
    )

    assert any(issue.code == "import_profile_executable_rejected" for issue in report.errors)


def test_import_profile_requires_validation() -> None:
    with pytest.raises(ValueError, match="require validation"):
        ImportProfile(profile_id="unsafe", name="Unsafe", require_validation=False)


def test_invalid_profile_is_rejected() -> None:
    with pytest.raises(ValueError, match="API keys"):
        ExportProfile(profile_id="bad", name="Bad", forbids_api_keys=False)
