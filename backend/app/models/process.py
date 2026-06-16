"""
工序模型
"""
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Process(Base):
    """工序表"""
    __tablename__ = "processes"

    process_id = Column(String(64), primary_key=True, comment="工序ID")
    order_id = Column(String(64), ForeignKey("orders.order_id"), nullable=False, comment="所属订单ID")
    process_seq = Column(String(16), nullable=False, comment="工序编码（如010/020）")
    process_name = Column(String(64), nullable=False, comment="工序名称")
    factory_id = Column(String(64), ForeignKey("factories.factory_id"), nullable=False, comment="承接厂家ID")
    process_order = Column(Integer, nullable=False, comment="工序顺序号（1,2,3...）")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    order = relationship("Order", back_populates="processes")
    factory = relationship("Factory", back_populates="processes")
    record = relationship("ProcessRecord", back_populates="process", uselist=False)
