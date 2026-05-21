from __future__ import annotations

from pydantic import BaseModel, Field


class CampaignChronicle(BaseModel):
    campaign_id: str
    major_events: list[str] = Field(default_factory=list)
    hidden_redacted: bool = True


class CampaignArc(BaseModel):
    arc_id: str
    title: str
    status: str = "active"


class CampaignHealthReport(BaseModel):
    campaign_id: str
    ok: bool = True
    warnings: list[str] = Field(default_factory=list)
    save_health: str = "unknown"
    branch_health: str = "unknown"


class LongCampaignService:
    def chronicle(self, campaign_id: str, event_summaries: list[str] | None = None) -> CampaignChronicle:
        safe = [event for event in (event_summaries or []) if "hidden" not in event.lower() and "secret" not in event.lower()]
        return CampaignChronicle(campaign_id=campaign_id, major_events=safe)

    def health(self, campaign_id: str, *, saves_count: int = 0, branches_count: int = 0) -> CampaignHealthReport:
        warnings = []
        if saves_count == 0:
            warnings.append("No saves associated with campaign.")
        return CampaignHealthReport(campaign_id=campaign_id, ok=not warnings, warnings=warnings, save_health=f"{saves_count} saves", branch_health=f"{branches_count} branches")

