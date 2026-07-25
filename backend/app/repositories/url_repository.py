from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.models import Url


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
