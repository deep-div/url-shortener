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

    async def get_raw_clicks(self, code: str) -> list[dict]:
        result = await self.session.execute(
            select(
                cast(Analytics.clicked_at, Date).label("date"),
                extract("hour", Analytics.clicked_at).label("hour"),
                Analytics.country,
                Analytics.city,
                Analytics.device,
                Analytics.browser,
            ).filter(Analytics.code == code)
        )
        return [
            {
                "date": str(r.date),
                "hour": int(r.hour),
                "country": r.country or "Others",
                "city": r.city or "Others",
                "device": r.device or "Others",
                "browser": r.browser or "Others",
            }
            for r in result.all()
        ]


