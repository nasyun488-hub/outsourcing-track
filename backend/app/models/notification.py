from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class NotificationType(str, enum.Enum):
    TRANSFER = "transfer"       # 流转通知
    SYNC_ERROR = "sync_error"   # 同步异常
    APPROVAL = "approval"       # 审批通知
    REGISTER = "register"       # 注册通知
    OTHER = "other"             # 其他


class Notification(Base):
    __tablename__ = "notifications"

    notif_id = Column(String(64), primary_key=True, comment="通知ID")
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True, comment="通知用户ID")
    title = Column(String(128), nullable=False, comment="通知标题")
    content = Column(Text, nullable=False, comment="通知内容")
    notif_type = Column(
        SQLEnum(NotificationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=NotificationType.OTHER, index=True, comment="通知类型"
    )
    is_read = Column(String(1), default="0", nullable=False, comment="是否已读")
    related_id = Column(String(64), nullable=True, comment="关联业务ID")
    related_type = Column(String(32), nullable=True, comment="关联业务类型")
    jump_url = Column(String(256), nullable=True, comment="前端跳转URL")
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment="创建时间")

    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(notif_id={self.notif_id}, user_id={self.user_id}, notif_type={self.notif_type}, is_read={self.is_read})>"
