"""
厂家模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Factory(Base):
    """厂家表"""
    __tablename__ = "factories"

    factory_id = Column(String(64), primary_key=True, comment="厂家ID")
    factory_name = Column(String(128), nullable=False, unique=True, comment="厂家名称")
    factory_type = Column(
        Enum("primary", "cooperative", name="factory_type_enum"),
        nullable=False, default="cooperative", comment="primary=主厂家，cooperative=配合工序厂家"
    )
    factory_phone = Column(String(20), nullable=True, comment="联系电话")
    factory_address = Column(String(256), nullable=True, comment="地址")
    status = Column(
        Enum("active", "inactive", "pending", name="factory_status_enum"),
        nullable=False, default="pending", comment="active/待审核/inactive"
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    users = relationship("User", back_populates="factory")
    processes = relationship("Process", back_populates="factory")
    records = relationship("ProcessRecord", back_populates="factory")
    primary_orders = relationship("Order", back_populates="primary_factory", foreign_keys="Order.primary_factory_id")
