import datetime
from enum import Enum
from pydantic import BaseModel


class DeviceType(str, Enum):
    Mobile = "Mobile"
    Tablet = "Tablet"
    Desktop = "Desktop"
    Other = "Other"


class OsType(str, Enum):
    Windows = "Windows"
    macOS = "macOS"
    Android = "Android"
    iOS = "iOS"
    Linux = "Linux"
    ChromeOS = "Chrome OS"
    Other = "Other"

    @classmethod
    def from_ua(cls, raw: str) -> "OsType":
        _map = {
            "windows": cls.Windows,
            "android": cls.Android,
            "ios": cls.iOS,
            "mac os x": cls.macOS,
            "macos": cls.macOS,
            "ubuntu": cls.Linux,
            "linux": cls.Linux,
            "chrome os": cls.ChromeOS,
        }
        return _map.get(raw.lower(), cls.Other)


class ReferrerType(str, Enum):
    Direct = "Direct"
    Google = "Google"
    Twitter = "Twitter"
    LinkedIn = "LinkedIn"
    Facebook = "Facebook"
    Instagram = "Instagram"
    YouTube = "YouTube"
    Other = "Other"


class ShortenResponse(BaseModel):
    short_url: str
    code: str


class AnalyticsResponse(BaseModel):
    code: str
    clicked_at: datetime.datetime
    ip: str | None
    device: DeviceType | None
    browser: str | None
    os: OsType | None
    referrer: ReferrerType | None
    class Config:
        from_attributes = True


class ClicksByDayItem(BaseModel):
    date: str
    clicks: int


class TopUrlItem(BaseModel):
    code: str
    clicks: int


class UrlStatsResponse(BaseModel):
    code: str
    total_clicks: int
    unique_clicks: int
    clicks_by_day: list[ClicksByDayItem]
    by_device: dict
    by_browser: dict
    by_os: dict
    by_referrer: dict


class DashboardResponse(BaseModel):
    total_urls: int
    total_clicks: int
    clicks_today: int
    top_urls: list[TopUrlItem]
