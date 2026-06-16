from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"           # 待处理
    IN_PROGRESS = "in_progress"   # 进行中
    COMPLETED = "completed"       # 已完成
    CANCELLED = "cancelled"       # 已取消


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(64), primary_key=True, comment="订单ID")
    primary_factory_id = Column(String(64), ForeignKey("factories.factory_id"), nullable=False, index=True, comment="主厂家ID")
    order_status = Column(
        SQLEnum(OrderStatus, values_callable=lambda x: [e.value for e in x]),
        default=OrderStatus.PENDING, nullable=False, comment="订单状态"
    )
    product_name = Column(String(128), nullable=True, comment="制件名称")
    product_code = Column(String(64), nullable=True, comment="制件编码")
    spec = Column(String(128), nullable=True, comment="规格型号")
    unit = Column(String(16), nullable=True, comment="计量单位")
    delivery_date = Column(DateTime, nullable=True, comment="交付日期")
    part_no = Column(String(64), nullable=True, comment="零件号")
    total_qty = Column(Integer, default=0, nullable=False, comment="订单总数量")
    mom_created_at = Column(DateTime, nullable=True, comment="MOM系统创建时间")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    # 关系
    primary_factory = relationship("Factory", back_populates="primary_orders", foreign_keys=[primary_factory_id])
    processes = relationship("Process", back_populates="order", cascade="all, delete-orphan")
    records = relationship("ProcessRecord", back_populates="order")

    def __repr__(self):
        return f"<Order(order_id={self.order_id}, primary_factory_id={self.primary_factory_id}, order_status={self.order_status})>"
