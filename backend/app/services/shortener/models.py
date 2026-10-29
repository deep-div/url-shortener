import datetime

import pytz
from sqlalchemy import BigInteger, Column, String, Text, DateTime

from app.clients.postgresql import Base

IST = pytz.timezone("Asia/Kolkata")


class Url(Base):
    __tablename__ = "urls"

    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    code       = Column(String, unique=True, nullable=False, index=True)
    long_url   = Column(Text, unique=True, nullable=False, index=True)
    short_url  = Column(Text, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(IST))
