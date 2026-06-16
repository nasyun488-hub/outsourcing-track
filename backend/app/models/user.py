from datetime import datetime
from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(64), primary_key=True, comment="用户ID")
    factory_id = Column(String(64), ForeignKey("factories.factory_id"), nullable=False, comment="所属厂家ID")
    phone = Column(String(20), nullable=False, unique=True, comment="手机号（登录账号）")
    name = Column(String(32), nullable=False, comment="姓名")
    role = Column(
        Enum(
            "enterprise_admin",
            "primary_admin",
            "primary_operator",
            "cooperative_admin",
            "cooperative_operator",
            "factory_admin",
            "factory_operator",
            "operator",
            name="user_role_enum"
        ),
        nullable=False,
        comment="5种角色"
    )
    password_hash = Column(String(256), nullable=False, comment="密码哈希")
    status = Column(
        Enum("active", "inactive", "pending", name="user_status_enum"),
        nullable=False,
        default="pending",
        comment="pending=待审核"
    )
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    factory = relationship("Factory", back_populates="users")
    notifications = relationship("Notification", back_populates="user")
    receive_batches = relationship("ReceiveBatch", back_populates="user")
    ship_batches = relationship("ShipBatch", back_populates="user")
    return_records = relationship("ReturnRecord", back_populates="user")
    action_logs = relationship("ActionLog", back_populates="user")

    @property
    def is_enterprise_admin(self):
        return self.role == "enterprise_admin"

    @property
    def is_factory_user(self):
        return self.role in {"primary_admin", "primary_operator", "cooperative_admin", "cooperative_operator", "factory_admin", "factory_operator", "operator"}
