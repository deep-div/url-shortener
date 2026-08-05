from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.repositories.models import Analytics, Url
import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


class UrlRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_long_url(self, url: str) -> Url | None:
        result = await self.session.execute(select(Url).filter(Url.long_url == url))
        return result.scalar_one_or_none()

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

    async def save(self, code: str, long_url: str, short_url: str) -> Url:
        row = Url(code=code, long_url=long_url, short_url=short_url)
        self.session.add(row)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        return row

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

    async def get_total_clicks(self, code: str) -> int:
        result = await self.session.execute(
            select(func.count(Analytics.id)).filter(Analytics.code == code)
        )
        return result.scalar() or 0


    async def get_clicks_by_day(self, code: str) -> list[dict]:
        result = await self.session.execute(
            select(cast(Analytics.clicked_at, Date).label("date"), func.count(Analytics.id).label("clicks"))
            .filter(Analytics.code == code)
            .group_by(cast(Analytics.clicked_at, Date))
            .order_by(cast(Analytics.clicked_at, Date))
        )
        return [{"date": str(r.date), "clicks": r.clicks} for r in result.all()]

    async def get_breakdown(self, code: str, field: str) -> dict:
        col = getattr(Analytics, field)
        result = await self.session.execute(
            select(col.label("value"), func.count(Analytics.id).label("count"))
            .filter(Analytics.code == code)
            .group_by(col)
            .order_by(func.count(Analytics.id).desc())
        )
        return {(r.value or "Unknown"): r.count for r in result.all()}

    #  Analytics — read (dashboard / global)

    async def get_total_clicks_all(self) -> int:
        result = await self.session.execute(select(func.count(Analytics.id)))
        return result.scalar() or 0

    async def get_clicks_today(self) -> int:
        today = datetime.datetime.now(IST).date()
        result = await self.session.execute(
            select(func.count(Analytics.id)).filter(cast(Analytics.clicked_at, Date) == today)
        )
        return result.scalar() or 0

    async def get_top_urls(self, limit: int = 5) -> list[dict]:
        result = await self.session.execute(
            select(Analytics.code, func.count(Analytics.id).label("clicks"))
            .group_by(Analytics.code)
            .order_by(func.count(Analytics.id).desc())
            .limit(limit)
        )
        return [{"code": r.code, "clicks": r.clicks} for r in result.all()]

    async def get_total_urls(self) -> int:
        result = await self.session.execute(select(func.count(Url.id)))
        return result.scalar() or 0

