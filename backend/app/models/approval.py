"""审批/解锁申请模型。"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class ApprovalRequest(Base):
    """修改审批表：当前最小闭环用于 entry_lock 解锁申请。"""
    __tablename__ = "approval_requests"

    request_id = Column(String(64), primary_key=True, comment="审批ID")
    record_id = Column(String(64), ForeignKey("process_records.record_id"), nullable=False, index=True, comment="关联流转记录ID")
    requester_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True, comment="申请人ID")
    approver_id = Column(String(64), ForeignKey("users.user_id"), nullable=True, index=True, comment="审批人ID")
    status = Column(Enum("pending", "approved", "rejected", name="approval_status_enum"), nullable=False, default="pending", index=True)
    request_type = Column(Enum("unlock", "modify", "cancel", name="approval_type_enum"), nullable=False, default="unlock")
    content = Column(Text, nullable=False, default="")
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    record = relationship("ProcessRecord")
    requester = relationship("User", foreign_keys=[requester_id])
    approver = relationship("User", foreign_keys=[approver_id])
