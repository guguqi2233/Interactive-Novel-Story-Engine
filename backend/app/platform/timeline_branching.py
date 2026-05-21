from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.platform.security import safe_identifier


class TimelineBranch(BaseModel):
    branch_id: str
    campaign_id: str
    parent_branch_id: str | None = None
    source_save_id: str
    source_event_id: str | None = None
    turn: int | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    name: str
    description: str = ""
    status: str = "active"
    current_save_id: str


class TimelineBranchDiff(BaseModel):
    branch_id: str
    compared_to: str
    changed_events: list[str] = Field(default_factory=list)
    hidden_redacted: bool = True


class TimelineBranchService:
    def __init__(self) -> None:
        self._branches: dict[str, TimelineBranch] = {}
        self._current_branch_id: str | None = None

    def create_branch(self, branch: TimelineBranch) -> TimelineBranch:
        if not safe_identifier(branch.branch_id):
            raise ValueError("Unsafe branch_id")
        self._branches[branch.branch_id] = branch
        return branch

    def list_branches(self, campaign_id: str) -> list[TimelineBranch]:
        return sorted((branch for branch in self._branches.values() if branch.campaign_id == campaign_id), key=lambda item: item.branch_id)

    def switch(self, branch_id: str) -> TimelineBranch:
        branch = self._branches[branch_id]
        self._current_branch_id = branch_id
        return branch

    def diff(self, branch_id: str, compared_to: str) -> TimelineBranchDiff:
        changed = [] if branch_id == compared_to else [branch_id, compared_to]
        return TimelineBranchDiff(branch_id=branch_id, compared_to=compared_to, changed_events=changed)

