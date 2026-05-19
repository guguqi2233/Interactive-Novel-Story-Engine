from pathlib import Path
from shutil import copytree

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.engine.content.character_pack_builder import (
    CharacterPack,
    CharacterPackExportRequest,
    CharacterPackFile,
    CharacterPackImportRequest,
    CharacterPackManifest,
    export_character_pack,
    import_character_pack_dry_run,
)
from app.engine.content.authoring_service import ContentAuthoringService
from app.main import app
from app.session_store import InMemorySessionStore


def _copy_world(tmp_path: Path) -> Path:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    return worlds_root


def _client(tmp_path: Path, worlds_root: Path) -> TestClient:
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "character_pack.db")
    app.state.worlds_root = worlds_root
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock")
    return TestClient(app)


def _pack(character_id: str = "mira") -> CharacterPack:
    return CharacterPack(
        manifest=CharacterPackManifest(
            pack_id="mira_pack",
            name="Mira Pack",
            exported_at="2026-05-19T00:00:00+00:00",
            character_ids=[character_id],
        ),
        characters=[
            {
                "id": character_id,
                "name": "Mira",
                "location_id": "village_square",
                "personality": "Curious and careful.",
            }
        ],
        rp_profiles={character_id: {"public_persona": "A careful local guide."}},
        voice_profiles={character_id: {"tone": "warm"}},
    )


def test_export_character_pack_contains_manifest(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)

    pack = export_character_pack(
        CharacterPackExportRequest(world_id="mist_valley", character_ids=["harlan"]),
        service,
    )

    assert pack.manifest.pack_id == "mist_valley_characters"
    assert pack.manifest.character_ids == ["harlan"]
    assert pack.characters[0]["id"] == "harlan"


def test_import_dry_run_does_not_write_disk(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    before = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")

    preview = import_character_pack_dry_run(
        CharacterPackImportRequest(world_id="mist_valley", pack=_pack()),
        service,
    )

    assert preview.validation.ok
    assert "npcs.yaml" in preview.would_write_files
    assert (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8") == before


def test_invalid_pack_is_rejected(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)

    response = client.post(
        "/authoring/character-packs/import-dry-run",
        json={"world_id": "mist_valley", "pack": {"characters": []}},
    )

    assert response.status_code == 422


def test_hidden_fact_default_not_exported_to_safe_pack(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)

    pack = export_character_pack(
        CharacterPackExportRequest(world_id="mist_valley", character_ids=["harlan"], safe_export=True),
        service,
    )
    payload = pack.model_dump_json()

    assert "sealed_letter_under_stone" not in payload
    assert "A sealed letter is hidden beneath a loose paving stone." not in payload
    assert pack.manifest.includes_hidden_facts is False


def test_executable_file_is_rejected(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    pack = _pack()
    pack.files.append(CharacterPackFile(path="scripts/install.py", content="print('nope')"))

    preview = import_character_pack_dry_run(
        CharacterPackImportRequest(world_id="mist_valley", pack=pack),
        service,
    )

    assert not preview.validation.ok
    assert any(issue.code == "character_pack_executable_file_rejected" for issue in preview.validation.errors)


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    service = ContentAuthoringService(worlds_root)
    pack = _pack()
    pack.files.append(CharacterPackFile(path="../npcs.yaml", content="npcs: []"))

    preview = import_character_pack_dry_run(
        CharacterPackImportRequest(world_id="mist_valley", pack=pack),
        service,
    )

    assert not preview.validation.ok
    assert any(issue.code == "character_pack_path_traversal_rejected" for issue in preview.validation.errors)


def test_apply_requires_explicit_confirmation(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)

    response = client.post(
        "/authoring/character-packs/import-apply",
        json={"world_id": "mist_valley", "pack": _pack().model_dump(mode="json"), "confirm_apply": False},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["applied"] is False
    assert any(issue["code"] == "character_pack_apply_requires_confirmation" for issue in payload["validation"]["errors"])


def test_apply_runs_validation_before_write(tmp_path: Path) -> None:
    worlds_root = _copy_world(tmp_path)
    client = _client(tmp_path, worlds_root)
    pack = _pack("bad_mira")
    pack.characters[0]["location_id"] = "missing_location"
    before = (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8")

    response = client.post(
        "/authoring/character-packs/import-apply",
        json={"world_id": "mist_valley", "pack": pack.model_dump(mode="json"), "confirm_apply": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["applied"] is False
    assert payload["validation"]["ok"] is False
    assert (worlds_root / "mist_valley" / "npcs.yaml").read_text(encoding="utf-8") == before
