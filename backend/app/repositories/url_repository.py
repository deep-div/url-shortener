from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, cast, Date

from app.repositories.models import Analytics, Url
import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


class UrlRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_long_url(self, url: str) -> Url | None:
        return self.session.query(Url).filter(Url.long_url == url).first()

    def get_by_code(self, code: str) -> Url | None:
        return self.session.query(Url).filter(Url.code == code).first()

    def save(self, code: str, long_url: str, short_url: str) -> Url:
        row = Url(code=code, long_url=long_url, short_url=short_url)
        self.session.add(row)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise
        return row


    def save_analytics(self, click) -> None:
        """Persist one click event. `click` is a AnalyticsResponse."""
        row = Analytics(
            code=click.code,
            clicked_at=click.clicked_at,
            ip=click.ip,
            country=click.country,
            city=click.city,
            device=click.device,
            browser=click.browser,
            os=click.os,
            referrer=click.referrer,
        )
        self.session.add(row)
        self.session.commit()

    #  Analytics — read (per URL)                                          

    def get_total_clicks(self, code: str) -> int:
        return self.session.query(func.count(Analytics.id)).filter(Analytics.code == code).scalar() or 0

    def get_unique_clicks(self, code: str) -> int:
        return self.session.query(func.count(distinct(Analytics.ip))).filter(Analytics.code == code).scalar() or 0

    def get_clicks_by_day(self, code: str) -> list[dict]:
        rows = (
            self.session.query(cast(Analytics.clicked_at, Date).label("date"), func.count(Analytics.id).label("clicks"))
            .filter(Analytics.code == code)
            .group_by(cast(Analytics.clicked_at, Date))
            .order_by(cast(Analytics.clicked_at, Date))
            .all()
        )
        return [{"date": str(r.date), "clicks": r.clicks} for r in rows]

    def get_breakdown(self, code: str, field: str) -> dict:
        col = getattr(Analytics, field)
        rows = (
            self.session.query(col.label("value"), func.count(Analytics.id).label("count"))
            .filter(Analytics.code == code)
            .group_by(col)
            .order_by(func.count(Analytics.id).desc())
            .all()
        )
        return {(r.value or "Unknown"): r.count for r in rows}

    #  Analytics — read (dashboard / global)                               #

    def get_total_clicks_all(self) -> int:
        return self.session.query(func.count(Analytics.id)).scalar() or 0

    def get_clicks_today(self) -> int:
        today = datetime.datetime.now(IST).date()
        return (
            self.session.query(func.count(Analytics.id))
            .filter(cast(Analytics.clicked_at, Date) == today)
            .scalar() or 0
        )

    def get_top_urls(self, limit: int = 5) -> list[dict]:
        rows = (
            self.session.query(Analytics.code, func.count(Analytics.id).label("clicks"))
            .group_by(Analytics.code)
            .order_by(func.count(Analytics.id).desc())
            .limit(limit)
            .all()
        )
        return [{"code": r.code, "clicks": r.clicks} for r in rows]

    def get_total_urls(self) -> int:
        return self.session.query(func.count(Url.id)).scalar() or 0

