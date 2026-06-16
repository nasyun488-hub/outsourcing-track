from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime

from app.models.notification import Notification, NotificationType


class NotificationService:
    """通知服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_notification(
        self,
        user_id: str,
        notif_type: NotificationType,
        title: str,
        content: Optional[str] = None,
        related_id: Optional[str] = None,
        related_type: Optional[str] = None,
        jump_url: Optional[str] = None,
    ) -> Notification:
        """
        创建通知
        - 通知类型：transfer/sync_error/approval/register
        """
        notification = Notification(
            notif_id=self._generate_id(),
            user_id=user_id,
            notif_type=notif_type,
            title=title,
            content=content,
            related_id=related_id,
            related_type=related_type,
            jump_url=jump_url,
            is_read="0",
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def _generate_id(self) -> str:
        """生成通知ID"""
        import time
        import random
        return f"notif_{int(time.time()*1000)}_{random.randint(1000,9999)}"

    def create_transfer_notification(
        self,
        user_id: str,
        order_id: str,
        process_id: str,
        from_handler: str,
        to_handler: str,
    ) -> Notification:
        """创建流转通知"""
        title = f"订单已流转至 {to_handler}"
        content = f"从 {from_handler} 流转至 {to_handler}"
        return self.create_notification(
            user_id=user_id,
            notif_type=NotificationType.TRANSFER,
            title=title,
            content=content,
            related_id=order_id,
            related_type="order",
            jump_url=f"/kanban/{order_id}",
        )

    def create_sync_error_notification(
        self,
        user_id: str,
        order_id: Optional[str],
        error_message: str,
    ) -> Notification:
        """创建同步异常通知"""
        title = "MOM同步失败"
        content = f"同步失败: {error_message}。请检查网络或联系管理员。"
        return self.create_notification(
            user_id=user_id,
            notif_type=NotificationType.SYNC_ERROR,
            title=title,
            content=content,
            related_id=order_id,
            related_type="order",
            jump_url=f"/kanban/{order_id}",
        )

    def create_approval_notification(
        self,
        user_id: str,
        order_id: str,
        approval_result: str,
        approver: str,
    ) -> Notification:
        """创建审批通知"""
        title = f"审批结果: {approval_result}"
        content = f"审批人: {approver}"
        return self.create_notification(
            user_id=user_id,
            notif_type=NotificationType.APPROVAL,
            title=title,
            content=content,
            related_id=order_id,
            related_type="order",
            jump_url=f"/kanban/{order_id}",
        )

    def create_register_notification(
        self,
        user_id: str,
        user_name: str,
    ) -> Notification:
        """创建注册通知"""
        title = "注册成功"
        content = f"欢迎 {user_name} 加入系统"
        return self.create_notification(
            user_id=user_id,
            notif_type=NotificationType.REGISTER,
            title=title,
            content=content,
            related_id=user_id,
            related_type="user",
            jump_url="/",
        )

    def get_user_notifications(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        is_read: Optional[int] = None,
        notif_type: Optional[str] = None,
    ) -> dict:
        """获取用户通知列表"""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if is_read is not None:
            query = query.filter(Notification.is_read == str(is_read))
        if notif_type:
            query = query.filter(Notification.notif_type == notif_type)

        # 统计未读数
        unread_count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == "0")
            .count()
        )

        # 分页
        total = query.count()
        offset = (page - 1) * page_size
        notifications = (
            query.order_by(desc(Notification.created_at))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        items = []
        for n in notifications:
            items.append({
                "notif_id": n.notif_id,
                "user_id": n.user_id,
                "notif_type": n.notif_type.value if hasattr(n.notif_type, 'value') else n.notif_type,
                "title": n.title,
                "content": n.content,
                "is_read": int(n.is_read) if n.is_read else 0,
                "related_id": n.related_id,
                "related_type": n.related_type,
                "jump_url": n.jump_url,
                "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S") if n.created_at else None,
            })

        return {
            "total": total,
            "unread_count": unread_count,
            "items": items,
        }

    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """标记单条通知已读"""
        notification = (
            self.db.query(Notification)
            .filter(Notification.notif_id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if not notification:
            return False

        notification.is_read = "1"
        self.db.commit()
        return True

    def mark_all_as_read(self, user_id: str) -> int:
        """标记所有通知已读"""
        result = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == "0")
            .update({"is_read": "1"})
        )
        self.db.commit()
        return result
