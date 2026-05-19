from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.engine.content.authoring_service import ALLOWED_AUTHORING_FILES
from app.engine.content.content_diff_review import ContentDiffRef, ContentDiffReview, ContentDiffReviewRequest, ContentDiffReviewService


class AuthoringDraftHistoryError(ValueError):
    """Raised when draft history input is unsafe or invalid."""


class AuthoringDraftSnapshotRequest(BaseModel):
    world_id: str
    label: str = ""
    draft_content: dict[str, str]
    max_history: int = Field(default=25, ge=1, le=200)


class AuthoringDraftSnapshot(BaseModel):
    draft_id: str
    world_id: str
    label: str = ""
    created_at: str
    affected_files: list[str] = Field(default_factory=list)
    draft_content: dict[str, str] = Field(default_factory=dict)
    requires_validation_before_save: bool = True


class AuthoringDraftHistory(BaseModel):
    local_only: bool = True
    storage: str = "worlds/.draft_history"
    snapshots: list[AuthoringDraftSnapshot] = Field(default_factory=list)


class AuthoringDraftRestoreResponse(BaseModel):
    snapshot: AuthoringDraftSnapshot
    writes_to_disk: bool = False
    requires_validation_before_save: bool = True


class AuthoringDraftCompareRequest(BaseModel):
    base_draft_id: str
    proposed_draft_id: str


class AuthoringDraftHistoryService:
    def __init__(self, worlds_root: str | Path = "worlds") -> None:
        self.worlds_root = Path(worlds_root)
        self.history_root = self.worlds_root / ".draft_history"

    def list_history(self, world_id: str | None = None) -> AuthoringDraftHistory:
        snapshots = [self._read_snapshot(path) for path in self._snapshot_paths()]
        filtered = [snapshot for snapshot in snapshots if world_id is None or snapshot.world_id == world_id]
        return AuthoringDraftHistory(snapshots=sorted(filtered, key=lambda item: item.created_at, reverse=True))

    def create_snapshot(self, request: AuthoringDraftSnapshotRequest) -> AuthoringDraftSnapshot:
        self._safe_world_id(request.world_id)
        draft_content = self._safe_draft_content(request.draft_content)
        snapshot = AuthoringDraftSnapshot(
            draft_id=f"draft_{uuid4().hex}",
            world_id=request.world_id,
            label=request.label[:120],
            created_at=datetime.now(UTC).isoformat(),
            affected_files=sorted(draft_content),
            draft_content=draft_content,
        )
        self.history_root.mkdir(parents=True, exist_ok=True)
        self._snapshot_path(snapshot.draft_id).write_text(snapshot.model_dump_json(), encoding="utf-8")
        self._trim_history(request.world_id, request.max_history)
        return snapshot

    def restore_snapshot(self, draft_id: str) -> AuthoringDraftRestoreResponse:
        return AuthoringDraftRestoreResponse(snapshot=self._get_snapshot(draft_id))

    def discard_snapshot(self, draft_id: str) -> AuthoringDraftHistory:
        self._snapshot_path(self._safe_draft_id(draft_id)).unlink(missing_ok=True)
        return self.list_history()

    def compare_snapshots(self, request: AuthoringDraftCompareRequest) -> ContentDiffReview:
        base = self._get_snapshot(request.base_draft_id)
        proposed = self._get_snapshot(request.proposed_draft_id)
        if base.world_id != proposed.world_id:
            raise AuthoringDraftHistoryError("Draft snapshots must target the same world.")
        return ContentDiffReviewService(self.worlds_root).review(
            ContentDiffReviewRequest(
                base=ContentDiffRef(world_id=base.world_id, files=base.draft_content),
                proposed=ContentDiffRef(world_id=proposed.world_id, files=proposed.draft_content),
                normal_view=True,
            )
        )

    def _trim_history(self, world_id: str, max_history: int) -> None:
        snapshots = self.list_history(world_id).snapshots
        for snapshot in snapshots[max_history:]:
            self._snapshot_path(snapshot.draft_id).unlink(missing_ok=True)

    def _get_snapshot(self, draft_id: str) -> AuthoringDraftSnapshot:
        path = self._snapshot_path(self._safe_draft_id(draft_id))
        if not path.exists():
            raise AuthoringDraftHistoryError(f"Draft snapshot not found: {draft_id}")
        return self._read_snapshot(path)

    def _snapshot_paths(self) -> list[Path]:
        if not self.history_root.exists():
            return []
        return sorted(self.history_root.glob("*.json"))

    def _read_snapshot(self, path: Path) -> AuthoringDraftSnapshot:
        return AuthoringDraftSnapshot.model_validate_json(path.read_text(encoding="utf-8"))

    def _snapshot_path(self, draft_id: str) -> Path:
        return self.history_root / f"{self._safe_draft_id(draft_id)}.json"

    def _safe_draft_content(self, content: dict[str, str]) -> dict[str, str]:
        if not content:
            raise AuthoringDraftHistoryError("Draft snapshot requires content.")
        safe: dict[str, str] = {}
        for file_name, value in content.items():
            if file_name not in ALLOWED_AUTHORING_FILES:
                raise AuthoringDraftHistoryError(f"File is not authoring-allowed: {file_name}")
            if _looks_sensitive(value):
                raise AuthoringDraftHistoryError("Draft snapshot rejected sensitive configuration content.")
            safe[file_name] = value
        return safe

    def _safe_world_id(self, value: str) -> str:
        if not value or not all(character.isalnum() or character in {"_", "-"} for character in value):
            raise AuthoringDraftHistoryError(f"Invalid world_id: {value}")
        return value

    def _safe_draft_id(self, value: str) -> str:
        if not value or not all(character.isalnum() or character in {"_", "-"} for character in value):
            raise AuthoringDraftHistoryError(f"Invalid draft_id: {value}")
        return value


def _looks_sensitive(value: str) -> bool:
    lowered = value.lower()
    return any(
        token in lowered
        for token in (
            "api_key",
            "apikey",
            "llm_api_key",
            "openai_api_key",
            "database_url",
            "local_llm_base_url",
            "authorization:",
            "bearer ",
            "private_key",
            "begin private key",
            "secret",
            "sk-",
        )
    )
