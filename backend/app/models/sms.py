from datetime import datetime
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, Enum

from app.database import Base


class SMSCode(Base):
    __tablename__ = "sms_codes"

    # SQLite requires INTEGER PRIMARY KEY for autoincrement in pytest's in-memory DB;
    # MySQL keeps BIGINT to match production DDL.
    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, comment="自增ID")
    phone = Column(String(20), nullable=False, comment="手机号")
    code = Column(String(8), nullable=False, comment="验证码")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    used = Column(BigInteger, nullable=False, default=0, comment="是否已使用（0=未使用，1=已使用）")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
