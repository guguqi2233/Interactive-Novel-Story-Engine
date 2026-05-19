import base64
import json
from io import BytesIO
from pathlib import Path
from shutil import copytree
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi.testclient import TestClient

from app.config import Settings
from app.db.repository import SQLiteSaveRepository
from app.main import app
from app.session_store import InMemorySessionStore


def _client(tmp_path: Path) -> TestClient:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    mods_root = tmp_path / "mods"
    _write_mod(mods_root)
    templates_root = tmp_path / "templates"
    copytree(Path("templates"), templates_root)
    app.state.session_store = InMemorySessionStore()
    app.state.save_repository = SQLiteSaveRepository(tmp_path / "library.db")
    app.state.worlds_root = worlds_root
    app.state.mods_root = mods_root
    app.state.scenario_template_renderer = None
    app.state.settings = Settings(enable_authoring_api=True, enable_debug_api=True, llm_provider="mock", llm_api_key="test-api-key-placeholder")
    return TestClient(app)


def test_library_list_works(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/library/items")

    assert response.status_code == 200
    payload = response.json()
    assert any(item["content_type"] == "world" and item["id"] == "mist_valley" for item in payload["items"])
    assert any(item["content_type"] == "mod" and item["id"] == "mist_mod" for item in payload["items"])
    assert "C:\\" not in response.text


def test_library_search_and_filter_works(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post(
        "/library/items/search",
        json={"query": "mist", "content_types": ["world"], "tags": ["world"]},
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == "mist_valley"
    assert items[0]["content_type"] == "world"


def test_library_batch_validate_works(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post("/library/items/batch-validate", json={"item_ids": ["mist_valley"], "content_types": ["world"]})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["passed"] == 1


def test_library_dependencies_display_correctly(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/library/items")

    mod = next(item for item in response.json()["items"] if item["id"] == "mist_mod")
    assert mod["dependencies"] == ["base_mod"]
    assert "C:\\" not in response.text


def test_invalid_package_is_identified(tmp_path: Path) -> None:
    client = _client(tmp_path)
    archive = _archive_b64(
        {
            "export_manifest.json": {"export_type": "world", "id": "bad_world"},
            "local_package_manifest.json": {
                "package_id": "bad_world",
                "package_type": "world",
                "included_files": ["worlds/bad_world/manifest.yaml"],
                "checksums": {"worlds/bad_world/manifest.yaml": "bad"},
            },
            "worlds/bad_world/manifest.yaml": "world_id: bad_world\nname: Bad\n",
        }
    )

    response = client.post("/library/import", json={"archive_base64": archive})

    assert response.status_code == 200
    assert response.json()["ok"] is False


def test_library_rejects_path_traversal(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/library/items/..secret")

    assert response.status_code == 400
    assert "Invalid library id" in response.json()["detail"]


def test_library_export_excludes_api_key(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post("/library/export", json={"content_type": "world", "item_id": "mist_valley"})

    assert response.status_code == 200
    assert "test-api-key-placeholder" not in response.text
    assert response.json()["archive_base64"]


def test_library_import_does_not_modify_active_game_state(tmp_path: Path) -> None:
    client = _client(tmp_path)
    start = client.post("/game/start", json={"world_id": "mist_valley"}).json()
    before_state = client.get(f"/game/state/{start['session_id']}").json()
    exported = client.post("/library/export", json={"content_type": "world", "item_id": "mist_valley"}).json()

    response = client.post("/library/import", json={"archive_base64": exported["archive_base64"], "overwrite": False})
    after_state = client.get(f"/game/state/{start['session_id']}").json()

    assert response.status_code == 200
    assert response.json()["ok"] is False
    assert after_state == before_state


def test_library_duplicate_rolls_back_when_validation_gate_blocks(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path)

    from app.engine.content.validation_gate import AuthoringValidationGate, AuthoringValidationGateResult
    from app.engine.content.validator import ValidationSeverity

    original = AuthoringValidationGate.evaluate

    def blocked(self, request):
        if request.world_id == "blocked_copy":
            report = request.validation_report
            report.add(ValidationSeverity.ERROR, "library.duplicate", "Blocked duplicate.", code="test_duplicate_gate_block")
            return AuthoringValidationGateResult(validation_report=report, allowed_to_save=False)
        return original(self, request)

    monkeypatch.setattr(AuthoringValidationGate, "evaluate", blocked)

    response = client.post("/library/duplicate", json={"content_type": "world", "item_id": "mist_valley", "new_id": "blocked_copy"})

    assert response.status_code == 400
    assert not (Path(app.state.worlds_root) / "blocked_copy").exists()


def _archive_b64(files: dict[str, object]) -> str:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, payload in files.items():
            content = json.dumps(payload) if isinstance(payload, dict) else str(payload)
            archive.writestr(name, content)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _write_mod(root: Path) -> None:
    mod = root / "mist_mod"
    world = mod / "worlds" / "mist_valley"
    world.mkdir(parents=True)
    (mod / "mod.yaml").write_text(
        """
id: mist_mod
name: Mist Mod
version: 1.0.0
engine_version_min: 0.8.0
content_schema_version: '1.0'
dependencies:
  - base_mod
entry_worlds:
  - mist_valley
content_paths:
  - worlds/mist_valley
""",
        encoding="utf-8",
    )
    (world / "manifest.yaml").write_text("world_id: mist_valley\nname: Mist Valley Mod\nstart_location_id: village_square\n", encoding="utf-8")
    (world / "locations.yaml").write_text("locations:\n  - id: village_square\n    name: Square\n    description: Mod square.\n    exits: {}\n", encoding="utf-8")
