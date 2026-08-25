from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.url_shortener.models import Url


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
