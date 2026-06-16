from sqlalchemy.orm import Session
from typing import Optional, Any, Dict
import time

from app.models.order import Order
from app.models.process import Process
from app.models.notification import Notification, NotificationType
from app.services.notification_service import NotificationService


class MOMService:
    """MOM集成服务（Mock实现）"""

    # 重试配置
    MAX_RETRIES = 3
    RETRY_INTERVAL_SECONDS = 5 * 60  # 5分钟

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def sync_orders_from_mom(
        self,
        factory_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        从MOM拉取派工单
        - 失败重试3次，间隔5分钟
        - 3次失败触发sync_error通知
        """
        retry_count = 0
        last_error = None

        while retry_count < self.MAX_RETRIES:
            try:
                # Mock API调用 - 模拟成功
                result = self._mock_fetch_orders_from_mom(factory_id, start_date, end_date)

                if result.get("success"):
                    return {
                        "success": True,
                        "message": "同步成功",
                        "data": result.get("data"),
                        "retry_count": retry_count,
                    }
            except Exception as e:
                last_error = str(e)

            retry_count += 1
            if retry_count < self.MAX_RETRIES:
                # 等待后重试
                time.sleep(self.RETRY_INTERVAL_SECONDS)

        # 3次失败，触发通知
        self._notify_sync_error(
            factory_id=factory_id,
            sync_type="orders",
            error_message=last_error or "未知错误",
        )

        return {
            "success": False,
            "message": f"同步失败，已重试{self.MAX_RETRIES}次",
            "error": last_error,
            "retry_count": retry_count,
        }

    def sync_record_to_mom(
        self,
        order_id: int,
        process_id: int,
        record_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        推送流转记录到MOM
        - 失败重试3次，间隔5分钟
        - 3次失败触发sync_error通知
        """
        retry_count = 0
        last_error = None

        while retry_count < self.MAX_RETRIES:
            try:
                # Mock API调用 - 模拟成功
                result = self._mock_push_record_to_mom(order_id, process_id, record_data)

                if result.get("success"):
                    # 更新process的mom_record_id
                    process = self.db.query(Process).filter(Process.id == process_id).first()
                    if process:
                        process.mom_record_id = result.get("mom_record_id")
                        self.db.commit()

                    return {
                        "success": True,
                        "message": "同步成功",
                        "data": result.get("data"),
                        "retry_count": retry_count,
                    }
            except Exception as e:
                last_error = str(e)

            retry_count += 1
            if retry_count < self.MAX_RETRIES:
                time.sleep(self.RETRY_INTERVAL_SECONDS)

        # 3次失败，触发通知
        self._notify_sync_error(
            factory_id=None,
            sync_type="records",
            error_message=last_error or "未知错误",
            order_id=order_id,
        )

        return {
            "success": False,
            "message": f"同步失败，已重试{self.MAX_RETRIES}次",
            "error": last_error,
            "retry_count": retry_count,
        }

    def _mock_fetch_orders_from_mom(
        self,
        factory_id: Optional[int],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> Dict[str, Any]:
        """
        Mock: 从MOM拉取派工单
        实际项目中这里应该是真实的API调用
        """
        # 模拟返回成功
        return {
            "success": True,
            "data": [
                {
                    "mom_work_order_id": f"MOM-WO-{int(time.time())}",
                    "order_no": f"SO{int(time.time())}",
                    "product_name": "Mock Product",
                    "quantity": 100,
                    "factory_id": factory_id,
                }
            ],
        }

    def _mock_push_record_to_mom(
        self,
        order_id: int,
        process_id: int,
        record_data: Optional[Dict],
    ) -> Dict[str, Any]:
        """
        Mock: 推送流转记录到MOM
        实际项目中这里应该是真实的API调用
        """
        # 模拟返回成功
        return {
            "success": True,
            "mom_record_id": f"MOM-REC-{int(time.time())}",
            "data": {
                "order_id": order_id,
                "process_id": process_id,
                "synced_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }

    def _notify_sync_error(
        self,
        factory_id: Optional[int],
        sync_type: str,
        error_message: str,
        order_id: Optional[int] = None,
    ):
        """触发同步错误通知"""
        # 通知该厂家的管理员或相关用户
        # 这里简化处理，实际应该查询该厂家的管理员用户
        admin_user_id = 1  # 默认管理员

        title = f"MOM{sync_type}同步失败"
        content = f"同步类型: {sync_type}，错误信息: {error_message}。已重试{self.MAX_RETRIES}次均失败，请检查网络或联系管理员。"

        self.notification_service.create_notification(
            user_id=admin_user_id,
            notif_type=NotificationType.SYNC_ERROR,
            title=title,
            content=content,
            related_id=order_id,
            related_type="mom_sync",
        )
