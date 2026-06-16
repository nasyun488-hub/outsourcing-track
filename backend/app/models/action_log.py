"""
操作日志模型
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ActionLog(Base):
    """操作日志表"""
    __tablename__ = "action_logs"

    log_id = Column(String(64), primary_key=True, comment="日志ID")
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, comment="操作用户ID")
    action_type = Column(String(32), nullable=False, comment="操作类型（如RECEIVE,SHIP,RETURN,UNLOCK等）")
    target_table = Column(String(32), nullable=False, comment="操作表名")
    target_id = Column(String(64), nullable=False, comment="操作记录ID")
    old_value = Column(JSON, nullable=True, comment="修改前值")
    new_value = Column(JSON, nullable=True, comment="修改后值")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")

    # 关系
    user = relationship("User", back_populates="action_logs")
