from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, DateTime
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
    code       = Column(String, unique=True, nullable=False, index=True)
    long_url   = Column(Text, unique=True, nullable=False, index=True)
    short_url  = Column(Text, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(IST))


class Analytics(Base):
    __tablename__ = "analytics"

    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    code       = Column(String, ForeignKey("urls.code"), nullable=False, index=True)
    clicked_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(IST), nullable=False)
    ip         = Column(String, nullable=True)
    country    = Column(String, nullable=True)
    city       = Column(String, nullable=True)
    device     = Column(String, nullable=True)
    browser    = Column(String, nullable=True)
    os         = Column(String, nullable=True)
