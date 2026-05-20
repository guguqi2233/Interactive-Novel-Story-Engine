from pathlib import Path

from fastapi.testclient import TestClient

from app.desktop.update_notes import LocalUpdateNotesService
from app.main import app


def test_release_notes_index_generates_from_local_docs(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "V1_0_RELEASE_NOTES.md").write_text(
        "# v1.0 Release Notes\n\nCore world engine.\n\n## 已知限制\n- Local only.\n\n## 从 v0.9 升级注意事项\n- Run migrations.\n",
        encoding="utf-8",
    )

    index = LocalUpdateNotesService(docs, current_version="v1.7").build_index()

    assert index.local_only is True
    assert index.current_version == "v1.7"
    assert index.release_notes[0].version == "v1.0"
    assert index.release_notes[0].known_limitations == ["Local only."]
    assert index.release_notes[0].upgrade_notes == ["Run migrations."]


def test_missing_release_notes_are_friendly_warnings(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()

    index = LocalUpdateNotesService(docs).build_index()

    assert any("Missing release notes for v1.7" in warning for warning in index.warnings)
    assert index.release_notes == []


def test_release_notes_index_redacts_api_keys(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "V1_6_RELEASE_NOTES.md").write_text(
        "# v1.6\n\nNever store sk-live-secret1234567890 in docs.\n\n## Known Limitations\n- API_KEY=secret-value\n",
        encoding="utf-8",
    )

    index = LocalUpdateNotesService(docs).build_index()

    payload = index.model_dump_json()
    assert "sk-live-secret" not in payload
    assert "secret-value" not in payload
    assert "[REDACTED" in payload


def test_update_notes_api_uses_local_index() -> None:
    client = TestClient(app)

    response = client.get("/studio/update-notes")

    assert response.status_code == 200
    payload = response.json()
    assert payload["local_only"] is True
    assert payload["current_version"] == "v1.7"
    assert isinstance(payload["release_notes"], list)
