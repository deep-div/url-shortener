from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date, case, extract
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.repositories.models import Analytics, Url
import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


class UrlRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_code(self, code: str) -> Url | None:
        result = await self.session.execute(select(Url).filter(Url.code == code))
        return result.scalar_one_or_none()

    async def save_or_get(self, code: str, long_url: str, short_url: str) -> tuple[Url, bool]:
        stmt = (
            pg_insert(Url)
            .values(code=code, long_url=long_url, short_url=short_url)
            .on_conflict_do_update(index_elements=["long_url"], set_={"long_url": long_url})
            .returning(Url)
        )
        try:
            result = await self.session.execute(stmt)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        row = result.scalar_one()
        return row, row.code != code

    async def save_analytics(self, click) -> None:
        row = Analytics(
            code=click.code,
            clicked_at=click.clicked_at,
            ip=click.ip,
            country=click.country,
            city=click.city,
            device=click.device,
            browser=click.browser,
            os=click.os,
        )
        self.session.add(row)
        await self.session.commit()

    #  Analytics — read (per URL)

    def _date_filters(self, code: str, from_date, to_date):
        filters = [Analytics.code == code]
        if from_date:
            filters.append(cast(Analytics.clicked_at, Date) >= from_date)
        if to_date:
            filters.append(cast(Analytics.clicked_at, Date) <= to_date)
        return filters

    async def get_clicks_by_day(self, code: str, from_date=None, to_date=None) -> list[dict]:
        result = await self.session.execute(
            select(cast(Analytics.clicked_at, Date).label("date"), func.count(Analytics.id).label("clicks"))
            .filter(*self._date_filters(code, from_date, to_date))
            .group_by(cast(Analytics.clicked_at, Date))
            .order_by(cast(Analytics.clicked_at, Date))
        )
        return [{"date": str(r.date), "clicks": r.clicks} for r in result.all()]

    async def get_summary(self, code: str, created_at: datetime.datetime) -> dict:
        today = datetime.datetime.now(IST).date()
        week_start = today - datetime.timedelta(days=today.weekday())
        result = await self.session.execute(
            select(
                func.count(Analytics.id).label("total_clicks"),
                func.count(Analytics.ip.distinct()).label("unique_clicks"),
                func.max(Analytics.clicked_at).label("last_clicked_at"),
                func.sum(case((cast(Analytics.clicked_at, Date) == today, 1), else_=0)).label("clicks_today"),
                func.sum(case((cast(Analytics.clicked_at, Date) >= week_start, 1), else_=0)).label("clicks_this_week"),
            ).filter(Analytics.code == code)
        )
        row = result.one()
        days_active = max((today - created_at.date()).days, 1)
        total = row.total_clicks or 0
        return {
            "total_clicks": total,
            "unique_clicks": row.unique_clicks or 0,
            "clicks_today": int(row.clicks_today or 0),
            "clicks_this_week": int(row.clicks_this_week or 0),
            "avg_clicks_per_day": round(total / days_active, 2),
            "last_clicked_at": row.last_clicked_at,
        }

    async def get_clicks_by_hour(self, code: str, from_date=None, to_date=None) -> list[dict]:
        result = await self.session.execute(
            select(
                cast(Analytics.clicked_at, Date).label("date"),
                extract("hour", Analytics.clicked_at).label("hour"),
                func.count(Analytics.id).label("clicks"),
            )
            .filter(*self._date_filters(code, from_date, to_date))
            .group_by(cast(Analytics.clicked_at, Date), extract("hour", Analytics.clicked_at))
            .order_by(cast(Analytics.clicked_at, Date), extract("hour", Analytics.clicked_at))
        )
        return [{"date": str(r.date), "hour": int(r.hour), "clicks": r.clicks} for r in result.all()]

    async def get_peak_hours(self, code: str, from_date=None, to_date=None) -> dict:
        result = await self.session.execute(
            select(extract("hour", Analytics.clicked_at).label("hour"), func.count(Analytics.id).label("clicks"))
            .filter(*self._date_filters(code, from_date, to_date))
            .group_by(extract("hour", Analytics.clicked_at))
            .order_by(extract("hour", Analytics.clicked_at))
        )
        return {int(r.hour): r.clicks for r in result.all()}

    async def get_breakdown(self, code: str, field: str, from_date=None, to_date=None) -> dict:
        col = getattr(Analytics, field)
        result = await self.session.execute(
            select(col.label("value"), func.count(Analytics.id).label("count"))
            .filter(*self._date_filters(code, from_date, to_date))
            .group_by(col)
            .order_by(func.count(Analytics.id).desc())
        )
        return {(r.value or "Others"): r.count for r in result.all()}


