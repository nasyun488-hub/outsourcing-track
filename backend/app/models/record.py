"""
流转记录相关的SQLAlchemy模型
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Enum, ForeignKey, Text, JSON, DECIMAL
)
from sqlalchemy.orm import relationship

from app.database import Base


class ProcessRecord(Base):
    """流转记录表（核心表）"""
    __tablename__ = "process_records"

    record_id = Column(String(64), primary_key=True, comment="记录ID")
    order_id = Column(String(64), ForeignKey("orders.order_id"), nullable=False, comment="订单ID")
    process_id = Column(String(64), ForeignKey("processes.process_id"), nullable=False, comment="工序ID")
    factory_id = Column(String(64), ForeignKey("factories.factory_id"), nullable=False, comment="承接厂家ID")
    record_status = Column(
        Enum("pending", "received", "shipped", "completed", name="record_status_enum"),
        nullable=False, default="pending", comment="流转阶段"
    )
    lock_type = Column(
        Enum("none", "entry_lock", "relation_lock", "sync_lock", name="lock_type_enum"),
        nullable=False, default="none", comment="锁定类型"
    )
    total_receive_qty = Column(Integer, nullable=False, default=0, comment="累计接收数量")
    total_ship_qty = Column(Integer, nullable=False, default=0, comment="累计发出数量")
    partial_receive = Column(Integer, default=0, comment="是否部分接收（0=否，1=是）")
    partial_ship = Column(Integer, default=0, comment="是否部分发出（0=否，1=是）")
    last_receive_time = Column(DateTime, nullable=True, comment="最后接收时间")
    last_ship_time = Column(DateTime, nullable=True, comment="最后发出时间")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系（returns_* 延后定义，见文件末尾）
    order = relationship("Order", back_populates="records")
    process = relationship("Process", back_populates="record")
    factory = relationship("Factory", back_populates="records")
    receive_batches = relationship("ReceiveBatch", back_populates="record", cascade="all, delete-orphan")
    ship_batches = relationship("ShipBatch", back_populates="record", cascade="all, delete-orphan")


class ReceiveBatch(Base):
    """接收批次表"""
    __tablename__ = "receive_batches"

    batch_id = Column(String(64), primary_key=True, comment="批次ID")
    record_id = Column(String(64), ForeignKey("process_records.record_id"), nullable=False, comment="所属流转记录ID")
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, comment="接收人ID")
    receive_time = Column(DateTime, nullable=False, comment="接收时间")
    receive_qty = Column(Integer, nullable=False, comment="接收数量")
    batch_no = Column(Integer, nullable=False, comment="批次序号（同一record的第N次接收）")
    return_qty = Column(Integer, nullable=False, default=0, comment="累计退件数量（负数计入）")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    record = relationship("ProcessRecord", back_populates="receive_batches")
    user = relationship("User", back_populates="receive_batches")


class ShipBatch(Base):
    """发出批次表"""
    __tablename__ = "ship_batches"

    batch_id = Column(String(64), primary_key=True, comment="批次ID")
    record_id = Column(String(64), ForeignKey("process_records.record_id"), nullable=False, comment="所属流转记录ID")
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, comment="发出人ID")
    ship_time = Column(DateTime, nullable=False, comment="发出时间")
    ship_qty = Column(Integer, nullable=False, comment="发出数量")
    batch_no = Column(Integer, nullable=False, comment="批次序号")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    record = relationship("ProcessRecord", back_populates="ship_batches")
    user = relationship("User", back_populates="ship_batches")


class ReturnRecord(Base):
    """退件记录表"""
    __tablename__ = "return_records"

    return_id = Column(String(64), primary_key=True, comment="退件ID")
    from_record_id = Column(String(64), ForeignKey("process_records.record_id"), nullable=False, comment="退出发送方流转记录ID")
    to_record_id = Column(String(64), ForeignKey("process_records.record_id"), nullable=False, comment="接收退回方流转记录ID")
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, comment="操作人ID")
    return_reason = Column(String(256), nullable=False, comment="退件原因")
    return_qty = Column(Integer, nullable=False, comment="退件数量（正数）")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")

    # 关系
    from_record = relationship("ProcessRecord", foreign_keys=[from_record_id], back_populates="returns_sent")
    to_record = relationship("ProcessRecord", foreign_keys=[to_record_id], back_populates="returns_received")
    user = relationship("User", back_populates="return_records")


# 延后的 ProcessRecord 关系（需要 ReturnRecord 已定义）
ProcessRecord.returns_sent = relationship(
    "ReturnRecord", foreign_keys=[ReturnRecord.from_record_id], back_populates="from_record"
)
ProcessRecord.returns_received = relationship(
    "ReturnRecord", foreign_keys=[ReturnRecord.to_record_id], back_populates="to_record"
)
