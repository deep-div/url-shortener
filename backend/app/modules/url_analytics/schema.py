import datetime
from enum import Enum
from pydantic import BaseModel


class DeviceType(str, Enum):
    Mobile = "Mobile"
    Tablet = "Tablet"
    Desktop = "Desktop"
    Other = "Other"

# internal schema used by click capture pipeline
class AnalyticsResponse(BaseModel):
    code: str
    clicked_at: datetime.datetime
    ip: str | None
    country: str | None
    city: str | None
    device: DeviceType | None
    browser: str | None

    class Config:
        from_attributes = True


# Analytics Read Schemas for Dashboard
# NOTE: this schema is the source of truth for the analytics dashboard UI.
# Only fields actually rendered on the analytics page belong here — keep the
# redis counters, DB models, and aggregation logic in sync with this shape.

class LinkInfo(BaseModel):
    code: str
    short_url: str
    long_url: str

class SummaryInfo(BaseModel):
    total_clicks: int
    unique_clicks: int
    total_countries: int
    total_cities: int
    last_clicked_at: datetime.datetime | None

class ClicksByDayItem(BaseModel):
    date: str
    clicks: int

class UrlStatsResponse(BaseModel):
    link: LinkInfo
    summary: SummaryInfo
    clicks_by_day: list[ClicksByDayItem]
    peak_hours: dict[int, int]  # hour -> total clicks across all days
    by_country: dict
    by_city: dict
    by_device: dict
    by_browser: dict


# Redis / SSE live-update payload (published on `updates:{code}`).
# Field names intentionally match SummaryInfo / UrlStatsResponse above —
# this is the enforced source of truth for the Redis counters and the
# live snapshot broadcast to the analytics dashboard over SSE.

class LiveSummary(BaseModel):
    total_clicks: int
    last_clicked_at: str | None
    total_countries: int
    total_cities: int

class LiveSnapshot(BaseModel):
    summary: LiveSummary
    by_country: dict[str, int]
    by_city: dict[str, int]
    by_device: dict[str, int]
    by_browser: dict[str, int]
    clicks_by_day: dict[str, int]
