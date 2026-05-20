import base64
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


def _draft(path: str = "flags.prayed", aliases: list[str] | None = None) -> dict:
    return {
        "module_id": "magic_basics",
        "name": "Magic Basics",
        "version": "0.1.0",
        "actions": [
            {
                "id": "magic.pray",
                "label": "Pray",
                "aliases": aliases or ["pray"],
                "category": "general",
                "target_specs": [{"kind": "current_location", "required": True}],
                "outcomes": {
                    "success": {
                        "success_level": "success",
                        "reason": "Deterministic local prayer.",
                        "state_delta_templates": [
                            {"operation": "set", "path": path, "value": True}
                        ],
                    }
                },
                "event_type": "magic.pray.resolved",
            }
        ],
    }


def test_action_mod_preview_valid_draft_passes(tmp_path: Path) -> None:
    app.state.worlds_root = tmp_path
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)

    response = client.post("/authoring/action-mods/preview", json=_draft())

    assert response.status_code == 200
    payload = response.json()
    assert payload["validation"]["ok"] is True
    assert payload["writes_to_disk"] is False
    assert payload["executes_code"] is False


def test_action_mod_validate_invalid_path_returns_field_error(tmp_path: Path) -> None:
    app.state.worlds_root = tmp_path
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)

    response = client.post("/authoring/action-mods/validate", json=_draft(path="player.hp"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["validation"]["ok"] is False
    assert payload["validation"]["errors"][0]["code"] == "action_mod_forbidden_state_delta_path"
    assert "state_delta_templates" in payload["validation"]["errors"][0]["path"]


def test_action_mod_alias_conflict_returns_warning(tmp_path: Path) -> None:
    app.state.worlds_root = tmp_path
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)
    draft = _draft()
    draft["actions"].append({**draft["actions"][0], "id": "magic.invoke", "event_type": "magic.invoke.resolved"})

    response = client.post("/authoring/action-mods/validate", json=draft)

    assert response.status_code == 200
    assert response.json()["validation"]["warnings"][0]["code"] == "action_mod_alias_conflict"


def test_action_mod_export_package_does_not_contain_api_key(tmp_path: Path) -> None:
    app.state.worlds_root = tmp_path
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)

    response = client.post("/authoring/action-mods/export", json=_draft())

    assert response.status_code == 200
    payload = response.json()
    assert payload["exported"] is True
    assert payload["contains_api_key"] is False
    archive_bytes = base64.b64decode(payload["archive_base64"])
    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        content = "\n".join(archive.read(name).decode("utf-8") for name in archive.namelist())
    assert "sk-" not in content
    assert "api_key" not in content.lower()


def test_action_mod_export_rejects_secret_like_text(tmp_path: Path) -> None:
    app.state.worlds_root = tmp_path
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
    client = TestClient(app)
    draft = _draft()
    draft["actions"][0]["label"] = "sk-real-looking-secret"

    response = client.post("/authoring/action-mods/export", json=draft)

    assert response.status_code == 200
    payload = response.json()
    assert payload["exported"] is False
    assert payload["contains_api_key"] is True
    assert payload["archive_base64"] == ""
    assert payload["validation"]["errors"][0]["code"] == "action_mod_export_secret_forbidden"


def test_action_mod_authoring_api_disabled(tmp_path: Path) -> None:
    app.state.worlds_root = tmp_path
    app.state.settings = Settings(enable_authoring_api=False, llm_provider="mock")
    client = TestClient(app)

    response = client.post("/authoring/action-mods/preview", json=_draft())

    assert response.status_code == 403
    assert response.json()["detail"] == "Authoring API is disabled"
    app.state.settings = Settings(enable_authoring_api=True, llm_provider="mock")
