import datetime

import pytz
from sqlalchemy import BigInteger, Column, ForeignKey, Index, String, DateTime, UniqueConstraint

from app.clients.postgresql import Base

IST = pytz.timezone("Asia/Kolkata")


class Analytics(Base):
    __tablename__ = "analytics"

    id         = Column(BigInteger, primary_key=True, autoincrement=True)
    code       = Column(String, ForeignKey("urls.code"), nullable=False)
    clicked_at = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(IST), nullable=False)
    ip         = Column(String, nullable=True)
    country    = Column(String, nullable=True)
    city       = Column(String, nullable=True)
    device     = Column(String, nullable=True)
    browser    = Column(String, nullable=True)

    __table_args__ = (
        Index("index_code_clickedat", "code", "clicked_at"),
        Index("index_code_ip", "code", "ip"),
    )


class UniqueIp(Base):
    __tablename__ = "unique_ips"

    id   = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String, ForeignKey("urls.code"), nullable=False)
    ip   = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint("code", "ip", name="unique_contraint_code_ip"),)
