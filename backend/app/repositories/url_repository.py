from sqlalchemy.exc import IntegrityError

from app.clients.postgresql import db_session
from app.repositories.models import Url


class UrlRepository:

    def get_by_long_url(self, url: str) -> Url | None:
        return db_session.query(Url).filter(Url.long_url == url).first()

    def get_by_code(self, code: str) -> Url | None:
        return db_session.query(Url).filter(Url.code == code).first()

    def save(self, code: str, long_url: str, short_url: str) -> Url:
        row = Url(code=code, long_url=long_url, short_url=short_url)
        db_session.add(row)
        try:
            db_session.commit()
        except IntegrityError:
            db_session.rollback()
            raise
        return row
