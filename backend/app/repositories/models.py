from sqlalchemy import BigInteger, Column, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func
import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


class Base(DeclarativeBase):
    pass


class Url(Base):
    __tablename__ = "urls"

    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    code       = Column(String(10), unique=True, nullable=False, index=True)
    long_url   = Column(Text, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(IST))
