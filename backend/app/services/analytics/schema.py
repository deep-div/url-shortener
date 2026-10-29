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


# Redis pub/sub (published on `updates:{code}`) reuses UrlStatsResponse
# directly — the live SSE payload and the dashboard's initial GET response
# are now the exact same shape, so the frontend can merge them as-is.
