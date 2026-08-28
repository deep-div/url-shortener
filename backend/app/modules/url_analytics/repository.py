from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date, extract
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.modules.url_analytics.models import Analytics, UniqueIp
from app.modules.url_shortener.models import Url


class UrlRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_code(self, code: str) -> Url | None:
        result = await self.session.execute(select(Url).filter(Url.code == code))
        return result.scalar_one_or_none()

    async def save_analytics_batch(self, clicks: list) -> list[bool]:
        ## 2 SQL write queries
        # Bulk upsert unique IPs — returns only rows that were actually inserted (new IPs)
        ip_stmt = (
            pg_insert(UniqueIp)
            .values([{"code": c.code, "ip": c.ip} for c in clicks])
            .on_conflict_do_nothing(constraint="unique_contraint_code_ip")
            .returning(UniqueIp.code, UniqueIp.ip)
        )
        result = await self.session.execute(ip_stmt)
        newly_unique = {(r.code, r.ip) for r in result.all()}

        # Bulk insert all analytics rows in one statement
        await self.session.execute(
            pg_insert(Analytics),
            [
                {
                    "code": c.code,
                    "clicked_at": c.clicked_at,
                    "ip": c.ip,
                    "country": c.country,
                    "city": c.city,
                    "device": c.device,
                    "browser": c.browser,
                }
                for c in clicks
            ],
        )
        await self.session.commit()
        return [(c.code, c.ip) in newly_unique for c in clicks]

    #  Analytics — read (per URL)
    async def get_summary(self, code: str) -> dict:
        result = await self.session.execute(
            select(
                func.count(Analytics.id).label("total_clicks"),
                func.count(Analytics.ip.distinct()).label("unique_clicks"),
                func.max(Analytics.clicked_at).label("last_clicked_at"),
            ).filter(Analytics.code == code)
        )
        row = result.one()
        return {
            "total_clicks": row.total_clicks or 0,
            "unique_clicks": row.unique_clicks or 0,
            "last_clicked_at": row.last_clicked_at,
        }

    async def get_clicks_by_day(self, code: str) -> list[dict]:
        date_col = cast(Analytics.clicked_at, Date)
        result = await self.session.execute(
            select(date_col.label("date"), func.count().label("clicks"))
            .filter(Analytics.code == code)
            .group_by(date_col)
            .order_by(date_col)
        )
        return [{"date": str(r.date), "clicks": r.clicks} for r in result.all()]

    async def get_peak_hours(self, code: str) -> dict[int, int]:
        hour_col = extract("hour", Analytics.clicked_at)
        result = await self.session.execute(
            select(hour_col.label("hour"), func.count().label("clicks"))
            .filter(Analytics.code == code)
            .group_by(hour_col)
        )
        return {int(r.hour): r.clicks for r in result.all()}

    async def get_by_country(self, code: str) -> dict[str, int]:
        result = await self.session.execute(
            select(Analytics.country.label("country"), func.count().label("clicks"))
            .filter(Analytics.code == code, Analytics.country.isnot(None))
            .group_by(Analytics.country)
        )
        return {r.country: r.clicks for r in result.all()}

    async def get_by_city(self, code: str) -> dict[str, int]:
        result = await self.session.execute(
            select(Analytics.city.label("city"), func.count().label("clicks"))
            .filter(Analytics.code == code, Analytics.city.isnot(None))
            .group_by(Analytics.city)
        )
        return {r.city: r.clicks for r in result.all()}

    async def get_by_device(self, code: str) -> dict[str, int]:
        result = await self.session.execute(
            select(Analytics.device.label("device"), func.count().label("clicks"))
            .filter(Analytics.code == code, Analytics.device.isnot(None))
            .group_by(Analytics.device)
        )
        return {r.device: r.clicks for r in result.all()}

    async def get_by_browser(self, code: str) -> dict[str, int]:
        result = await self.session.execute(
            select(Analytics.browser.label("browser"), func.count().label("clicks"))
            .filter(Analytics.code == code, Analytics.browser.isnot(None))
            .group_by(Analytics.browser)
        )
        return {r.browser: r.clicks for r in result.all()}

    async def get_unique_ips(self, code: str) -> list[str]:
        result = await self.session.execute(
            select(UniqueIp.ip).filter(UniqueIp.code == code, UniqueIp.ip.isnot(None))
        )
        return [r.ip for r in result.all()]


