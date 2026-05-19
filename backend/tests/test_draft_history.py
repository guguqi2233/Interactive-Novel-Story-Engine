from pathlib import Path
from shutil import copytree

import pytest

from app.engine.content.draft_history import AuthoringDraftHistoryError, AuthoringDraftHistoryService, AuthoringDraftSnapshotRequest


def test_draft_history_rejects_broader_sensitive_env_markers(tmp_path: Path) -> None:
    worlds_root = tmp_path / "worlds"
    copytree(Path("worlds") / "mist_valley", worlds_root / "mist_valley")
    service = AuthoringDraftHistoryService(worlds_root)

    with pytest.raises(AuthoringDraftHistoryError):
        service.create_snapshot(
            AuthoringDraftSnapshotRequest(
                world_id="mist_valley",
                draft_content={"manifest.yaml": "world_id: mist_valley\nname: Mist\nLOCAL_LLM_BASE_URL=http://127.0.0.1:11434\n"},
            )
        )
