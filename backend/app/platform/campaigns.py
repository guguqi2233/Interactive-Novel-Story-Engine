from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from app.platform.security import safe_identifier


class CampaignStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class CampaignMetadata(BaseModel):
    campaign_id: str
    name: str
    description: str = ""
    world_id: str
    active_save_id: str | None = None
    enabled_modules: list[str] = Field(default_factory=list)
    prompt_profile_id: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    last_played_at: str | None = None
    status: CampaignStatus = CampaignStatus.ACTIVE
    campaign_version: str = "2.0.0"
    notes: str = ""

    @field_validator("campaign_id", "world_id")
    @classmethod
    def validate_ids(cls, value: str) -> str:
        if not safe_identifier(value):
            raise ValueError("Unsafe campaign/world id")
        return value


class CampaignService:
    def __init__(self) -> None:
        self._campaigns: dict[str, CampaignMetadata] = {}
        self._current_campaign_id: str | None = None

    def create(self, campaign: CampaignMetadata) -> CampaignMetadata:
        self._campaigns[campaign.campaign_id] = campaign
        return campaign

    def list(self) -> list[CampaignMetadata]:
        return sorted(self._campaigns.values(), key=lambda item: item.campaign_id)

    def get(self, campaign_id: str) -> CampaignMetadata:
        return self._campaigns[campaign_id]

    def select(self, campaign_id: str) -> CampaignMetadata:
        campaign = self.get(campaign_id)
        campaign.last_played_at = datetime.now(UTC).isoformat()
        self._current_campaign_id = campaign_id
        return campaign

    def delete_metadata(self, campaign_id: str, *, confirm_delete: bool = False) -> bool:
        if not confirm_delete:
            raise ValueError("confirm_delete is required")
        self._campaigns.pop(campaign_id, None)
        if self._current_campaign_id == campaign_id:
            self._current_campaign_id = None
        return True

