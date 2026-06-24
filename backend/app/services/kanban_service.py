from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import Optional, List
from datetime import datetime, timedelta

from app.models.order import Order, OrderStatus
from app.models.process import Process
from app.models.record import ProcessRecord, ReturnRecord
from app.models.user import User
from app.models.notification import Notification, NotificationType
from app.schemas.kanban import (
    OrderKanbanListResponse,
    OrderKanbanResponse,
    ProcessKanbanListResponse,
    ProcessKanbanResponse,
    KanbanStatsResponse,
)


class KanbanService:
    """看板统计服务"""

    def __init__(self, db: Session):
        self.db = db

    def _visible_orders_query(self, current_user=None):
        """按当前用户权限返回可见订单查询，订单列表和首页统计必须共用同一口径。"""
        query = self.db.query(Order).options(joinedload(Order.primary_factory))
        if current_user and getattr(current_user, "role", None) != "enterprise_admin":
            user_factory_id = getattr(current_user, "factory_id", None)
            order_ids = self.db.query(ProcessRecord.order_id).filter(ProcessRecord.factory_id == user_factory_id)
            query = query.filter(or_(Order.primary_factory_id == user_factory_id, Order.order_id.in_(order_ids)))
        return query

    def get_orders_kanban(
        self,
        page: int = 1,
        page_size: int = 20,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        primary_factory_id: Optional[str] = None,
        status: Optional[str] = None,
        order_no: Optional[str] = None,
        quick: Optional[str] = None,
        current_user=None,
    ) -> OrderKanbanListResponse:
        """
        获取订单看板列表
        - 支持分页、过滤
        """
        query = self._visible_orders_query(current_user)

        # 过滤条件
        if start_date:
            query = query.filter(Order.created_at >= start_date)
        if end_date:
            query = query.filter(Order.created_at <= end_date)
        if primary_factory_id:
            query = query.filter(Order.primary_factory_id == primary_factory_id)
        if order_no:
            like_value = f"%{order_no}%"
            query = query.filter(or_(
                Order.order_id.like(like_value),
                Order.product_name.like(like_value),
                Order.product_code.like(like_value),
                Order.part_no.like(like_value),
            ))
        if status:
            query = query.filter(Order.order_status == status)
        if quick in {"overdue", "todo", "soon", "receive", "ship"}:
            query = query.join(ProcessRecord, ProcessRecord.order_id == Order.order_id)
            if quick == "overdue":
                query = query.filter(ProcessRecord.record_status.in_(["pending", "received"]))
            elif quick in {"todo", "receive", "ship"}:
                query = query.filter(Order.order_status.in_([OrderStatus.PENDING.value, OrderStatus.IN_PROGRESS.value]))
            elif quick == "soon":
                query = query.filter(Order.order_status == OrderStatus.IN_PROGRESS.value)
            query = query.distinct()

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        orders = query.order_by(Order.updated_at.desc()).offset(offset).limit(page_size).all()

        # 构建响应
        items = []
        for order in orders:
            # 获取工序统计
            process_stats = self._get_order_process_stats(order.order_id)

            items.append(OrderKanbanResponse(
                order_id=order.order_id,
                order_no=order.order_id,
                product_name=order.product_name or f"制件-{order.order_id}",
                product_code=order.product_code,
                spec=order.spec,
                part_no=order.part_no,
                quantity=order.total_qty,
                unit=order.unit or "件",
                status=order.order_status,
                delivery_date=order.delivery_date,
                factory_id=order.primary_factory_id,
                factory_name=order.primary_factory.factory_name if order.primary_factory else order.primary_factory_id,
                primary_factory_id=order.primary_factory_id,
                is_overdue=process_stats["has_overdue"],
                process_count=process_stats["process_count"],
                pending_count=process_stats.get("pending_count", 0),
                in_progress_count=process_stats.get("in_progress_count", 0),
                completed_count=process_stats.get("completed_count", 0),
                created_at=order.created_at,
                updated_at=order.updated_at,
            ))

        return OrderKanbanListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
        )

    def _get_order_process_stats(self, order_id: str) -> dict:
        """获取订单工序统计"""
        records = self.db.query(ProcessRecord).filter(ProcessRecord.order_id == order_id).all()

        # 使用 MySQL UTC_TIMESTAMP() 计算超期（避免 Python/MySQL 时区不一致）
        # 在 MySQL 中执行: TIMESTAMPDIFF(HOUR, created_at, UTC_TIMESTAMP()) > 48
        from sqlalchemy import text

        has_overdue = False
        overdue_threshold_hours = 48

        pending_count = 0
        in_progress_count = 0
        completed_count = 0

        for record in records:
            if record.record_status == 'pending':
                pending_count += 1
                # pending：created_at 距离现在超过48小时
                result = self.db.execute(
                    text("SELECT TIMESTAMPDIFF(HOUR, :created_at, UTC_TIMESTAMP()) AS diff"),
                    {"created_at": record.created_at}
                ).fetchone()
                diff_hours = result[0] if result else 0
                if diff_hours > overdue_threshold_hours:
                    has_overdue = True
            elif record.record_status == 'received':
                in_progress_count += 1
                # received：last_receive_time 距离现在超过48小时，且未发出
                if record.last_receive_time:
                    result = self.db.execute(
                        text("SELECT TIMESTAMPDIFF(HOUR, :recv_time, UTC_TIMESTAMP()) AS diff"),
                        {"recv_time": record.last_receive_time}
                    ).fetchone()
                    diff_hours = result[0] if result else 0
                    if diff_hours > overdue_threshold_hours:
                        has_overdue = True
            elif record.record_status == 'shipped':
                in_progress_count += 1
            elif record.record_status == 'completed':
                completed_count += 1

        return {
            "has_overdue": has_overdue,
            "process_count": len(records),
            "pending_count": pending_count,
            "in_progress_count": in_progress_count,
            "completed_count": completed_count,
        }

    def _effective_quantities(self, record: ProcessRecord) -> tuple[int, int]:
        """返回退件折算后的有效接收/发出数量，避免看板展示超过业务可用量。"""
        returned_out_qty = self.db.query(func.coalesce(func.sum(ReturnRecord.return_qty), 0)).filter(
            ReturnRecord.from_record_id == record.record_id
        ).scalar() or 0
        returned_in_qty = self.db.query(func.coalesce(func.sum(ReturnRecord.return_qty), 0)).filter(
            ReturnRecord.to_record_id == record.record_id
        ).scalar() or 0
        receive_qty = max(int(record.total_receive_qty or 0) - int(returned_in_qty or 0), 0)
        ship_qty = max(int(record.total_ship_qty or 0) - int(returned_out_qty or 0), 0)
        return receive_qty, ship_qty

    @staticmethod
    def _clamp_qty(value: int, upper: int) -> int:
        """数量展示防御：不小于0，也不超过上游/本工序可供上限。"""
        return min(max(int(value or 0), 0), max(int(upper or 0), 0))

    @staticmethod
    def _is_factory_scoped_user(current_user) -> bool:
        """厂家角色只能操作本厂工序；企业管理员可跨厂操作。"""
        role = getattr(current_user, "role", None)
        return role in {
            "primary_admin", "primary_operator",
            "cooperative_admin", "cooperative_operator",
            "factory_admin", "factory_operator", "operator",
        }

    def _action_state_for_process(
        self,
        record: ProcessRecord,
        current_user,
        available_receive_qty: int,
        available_ship_qty: int,
    ) -> dict:
        """统一计算看板动作权限，避免前端按可用数量误推荐跨厂操作。"""
        user_factory_id = getattr(current_user, "factory_id", None) if current_user else None
        role = getattr(current_user, "role", None) if current_user else None

        owns_process = bool(record.factory_id) and str(record.factory_id) == str(user_factory_id)
        can_cross_factory = role == "enterprise_admin"
        can_operate_factory = can_cross_factory or owns_process

        raw_can_receive = available_receive_qty > 0
        raw_can_ship = available_ship_qty > 0
        can_receive = can_operate_factory and raw_can_receive
        can_ship = can_operate_factory and raw_can_ship
        next_action = "receive" if can_receive else ("ship" if can_ship else None)

        disabled_reason = None
        if not can_operate_factory:
            disabled_reason = "仅可查看相邻工序，无权操作该厂家工序"
        elif raw_can_receive or raw_can_ship:
            disabled_reason = None
        elif available_receive_qty <= 0 and int(record.total_receive_qty or 0) <= 0:
            disabled_reason = "等待上道发出"
        else:
            disabled_reason = "暂无可操作数量"

        return {
            "can_receive": can_receive,
            "can_ship": can_ship,
            "can_operate": can_receive or can_ship,
            "disabled_reason": disabled_reason,
            "next_action": next_action,
        }

    @staticmethod
    def _risk_state_for_process(
        record: ProcessRecord,
        process: Optional[Process],
        factory_name: str,
        diff_hours: int,
        is_overdue: bool,
        available_receive_qty: int,
        available_ship_qty: int,
    ) -> dict:
        """按工序状态、可操作数量和超期小时数输出风险等级与原因。"""
        process_name = process.process_name if process else (record.process_id or "未知工序")
        if is_overdue and (available_receive_qty > 0 or available_ship_qty > 0):
            return {
                "risk_level": "high",
                "risk_reason": f"{process_name}（{factory_name}）已停留 {diff_hours} 小时，超过48小时阈值",
            }
        if record.record_status == "pending" and available_receive_qty > 0:
            return {
                "risk_level": "medium",
                "risk_reason": f"{process_name}（{factory_name}）待接收，可能成为当前卡点",
            }
        if record.record_status == "received" and available_ship_qty > 0:
            return {
                "risk_level": "medium",
                "risk_reason": f"{process_name}（{factory_name}）已接收未发出，需跟进发出",
            }
        return {"risk_level": "normal", "risk_reason": None}

    @staticmethod
    def _pick_bottleneck(items: list[ProcessKanbanResponse]) -> Optional[ProcessKanbanResponse]:
        """当前卡点优先级：超期高风险 > 可操作待处理 > 中风险等待 > 首个未完成。"""
        for item in items:
            if item.risk_level == "high":
                return item
        for item in items:
            if item.can_operate:
                return item
        for item in items:
            if item.risk_level == "medium":
                return item
        for item in items:
            if item.status not in {"shipped", "completed"}:
                return item
        return None

    def _create_risk_notification_once(self, order_id: str, bottleneck: Optional[ProcessKanbanResponse], current_user=None) -> None:
        """给卡点所属厂家未读用户生成幂等风险提醒；同一订单同一用户未读提醒只保留一条。"""
        if not bottleneck or bottleneck.risk_level != "high" or not bottleneck.factory_id:
            return

        target_users = self.db.query(User).filter(
            User.factory_id == bottleneck.factory_id,
            User.status == "active",
        ).all()
        title = f"订单 {order_id} 存在超期风险"
        content = bottleneck.risk_reason or "工序停留超过48小时，请及时处理。"
        for user in target_users:
            exists = self.db.query(Notification).filter(
                Notification.user_id == user.user_id,
                Notification.related_id == order_id,
                Notification.related_type == "order",
                Notification.title == title,
                Notification.is_read == "0",
            ).first()
            if exists:
                continue
            notification = Notification(
                notif_id=self._generate_notification_id(),
                user_id=user.user_id,
                notif_type=NotificationType.TRANSFER,
                title=title,
                content=content,
                related_id=order_id,
                related_type="order",
                jump_url=f"/kanban/{order_id}",
                is_read="0",
            )
            self.db.add(notification)
        self.db.commit()

    @staticmethod
    def _generate_notification_id() -> str:
        import time
        import random
        return f"notif_{int(time.time()*1000)}_{random.randint(1000,9999)}"

    def get_processes_kanban(self, order_id: str, current_user=None) -> ProcessKanbanListResponse:
        """
        获取工序流转看板
        - 超期标红：接收后48小时未发出
        """
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise ValueError(f"订单 {order_id} 不存在")
        if current_user and getattr(current_user, "role", None) != "enterprise_admin":
            user_factory_id = getattr(current_user, "factory_id", None)
            participates = self.db.query(ProcessRecord).filter(
                ProcessRecord.order_id == order_id,
                ProcessRecord.factory_id == user_factory_id,
            ).first()
            if order.primary_factory_id != user_factory_id and not participates:
                raise PermissionError("无权查看该订单")

        records = (
            self.db.query(ProcessRecord)
            .options(joinedload(ProcessRecord.process), joinedload(ProcessRecord.factory))
            .filter(ProcessRecord.order_id == order_id)
            .join(Process, Process.process_id == ProcessRecord.process_id)
            .order_by(Process.process_order.asc())
            .all()
        )
        ordered_process_ids = [record.process_id for record in records]

        # 检查超期：pending超过48h未处理 或 received超过48h未发出
        # 使用 MySQL UTC_TIMESTAMP() 避免时区问题
        from sqlalchemy import text
        overdue_threshold_hours = 48

        items = []
        safe_order_qty = max(int(order.total_qty or 0), 0)
        display_quantities: list[dict[str, int]] = []
        for index, record in enumerate(records):
            process = record.process
            factory = record.factory
            is_overdue = False
            diff_hours = 0
            if record.record_status == 'pending':
                # pending：created_at超过48h未处理
                result = self.db.execute(
                    text("SELECT TIMESTAMPDIFF(HOUR, :created_at, UTC_TIMESTAMP()) AS diff"),
                    {"created_at": record.created_at}
                ).fetchone()
                diff_hours = result[0] if result else 0
                if diff_hours > overdue_threshold_hours:
                    is_overdue = True
            elif record.record_status == 'received':
                # received：last_receive_time超过48h未发出
                if record.last_receive_time:
                    result = self.db.execute(
                        text("SELECT TIMESTAMPDIFF(HOUR, :recv_time, UTC_TIMESTAMP()) AS diff"),
                        {"recv_time": record.last_receive_time}
                    ).fetchone()
                    diff_hours = result[0] if result else 0
                    if diff_hours > overdue_threshold_hours:
                        is_overdue = True

            upstream_qty = safe_order_qty if index == 0 else display_quantities[index - 1]["ship_qty"]
            effective_receive_qty, effective_ship_qty = self._effective_quantities(record)
            display_receive_qty = self._clamp_qty(effective_receive_qty, upstream_qty)
            display_ship_qty = self._clamp_qty(effective_ship_qty, display_receive_qty)
            available_receive_qty = max(upstream_qty - display_receive_qty, 0)
            available_ship_qty = max(display_receive_qty - display_ship_qty, 0)
            display_quantities.append({
                "receive_qty": display_receive_qty,
                "ship_qty": display_ship_qty,
            })
            action_state = self._action_state_for_process(
                record,
                current_user,
                available_receive_qty,
                available_ship_qty,
            )
            factory_name = factory.factory_name if factory else record.factory_id
            risk_state = self._risk_state_for_process(
                record,
                process,
                factory_name,
                int(diff_hours or 0),
                is_overdue,
                available_receive_qty,
                available_ship_qty,
            )

            items.append(ProcessKanbanResponse(
                record_id=record.record_id,
                order_id=record.order_id,
                process_id=record.process_id,
                process_name=process.process_name if process else record.process_id,
                process_order=process.process_order if process else 0,
                status=record.record_status,
                receive_time=record.last_receive_time,
                send_time=record.last_ship_time,
                is_overdue=is_overdue,
                factory_id=record.factory_id,
                factory_name=factory.factory_name if factory else record.factory_id,
                prev_process_id=ordered_process_ids[index - 1] if index > 0 else None,
                next_process_id=ordered_process_ids[index + 1] if index + 1 < len(ordered_process_ids) else None,
                receive_qty=display_receive_qty,
                ship_qty=display_ship_qty,
                prev_ship_qty=upstream_qty,
                current_receive_qty=display_receive_qty,
                current_ship_qty=display_ship_qty,
                available_receive_qty=available_receive_qty,
                available_ship_qty=available_ship_qty,
                can_receive=action_state["can_receive"],
                can_ship=action_state["can_ship"],
                can_operate=action_state["can_operate"],
                disabled_reason=action_state["disabled_reason"],
                next_action=action_state["next_action"],
                is_bottleneck=False,
                risk_level=risk_state["risk_level"],
                risk_reason=risk_state["risk_reason"],
                created_at=record.created_at,
                updated_at=record.updated_at,
            ))

        bottleneck = self._pick_bottleneck(items)
        if bottleneck:
            bottleneck.is_bottleneck = True
        self._create_risk_notification_once(order.order_id, bottleneck, current_user=current_user)

        return ProcessKanbanListResponse(
            order_id=order.order_id,
            order_no=order.order_id,
            items=items,
            current_bottleneck_record_id=bottleneck.record_id if bottleneck else None,
            risk_level=bottleneck.risk_level if bottleneck else "normal",
            risk_reason=bottleneck.risk_reason if bottleneck else None,
        )

    def get_kanban_stats(self, factory_id: Optional[str] = None, current_user=None) -> KanbanStatsResponse:
        """
        获取看板统计
        - 全部/待处理/进行中/已完成订单数
        - 超期工序数
        """
        query = self._visible_orders_query(current_user)
        if factory_id:
            query = query.filter(Order.primary_factory_id == factory_id)

        total = query.count()
        pending = query.filter(Order.order_status == OrderStatus.PENDING.value).count()
        in_progress = query.filter(Order.order_status == OrderStatus.IN_PROGRESS.value).count()
        completed = query.filter(Order.order_status == OrderStatus.COMPLETED.value).count()

        visible_order_ids = [row[0] for row in query.with_entities(Order.order_id).all()]

        # 超期工序数
        # 使用 MySQL UTC_TIMESTAMP() 避免 Python/MySQL 时区不一致
        from sqlalchemy import text
        overdue_threshold_hours = 48

        # 分开查：pending 用 created_at，received 用 last_receive_time
        pending_overdue = self.db.query(ProcessRecord).filter(
            ProcessRecord.record_status == 'pending',
        )
        if visible_order_ids:
            pending_overdue = pending_overdue.filter(ProcessRecord.order_id.in_(visible_order_ids))
        else:
            pending_overdue = pending_overdue.filter(False)
        if factory_id:
            pending_overdue = pending_overdue.filter(ProcessRecord.factory_id == factory_id)

        pending_count = 0
        for record in pending_overdue.all():
            result = self.db.execute(
                text("SELECT TIMESTAMPDIFF(HOUR, :created_at, UTC_TIMESTAMP()) AS diff"),
                {"created_at": record.created_at}
            ).fetchone()
            diff_hours = result[0] if result else 0
            if diff_hours > overdue_threshold_hours:
                pending_count += 1

        received_overdue = self.db.query(ProcessRecord).filter(
            ProcessRecord.record_status == 'received',
            ProcessRecord.last_receive_time.isnot(None),
        )
        if visible_order_ids:
            received_overdue = received_overdue.filter(ProcessRecord.order_id.in_(visible_order_ids))
        else:
            received_overdue = received_overdue.filter(False)
        if factory_id:
            received_overdue = received_overdue.filter(ProcessRecord.factory_id == factory_id)

        received_count = 0
        for record in received_overdue.all():
            if record.last_receive_time:
                result = self.db.execute(
                    text("SELECT TIMESTAMPDIFF(HOUR, :recv_time, UTC_TIMESTAMP()) AS diff"),
                    {"recv_time": record.last_receive_time}
                ).fetchone()
                diff_hours = result[0] if result else 0
                if diff_hours > overdue_threshold_hours:
                    received_count += 1

        overdue_count = pending_count + received_count

        return KanbanStatsResponse(
            total=total,
            pending=pending,
            in_progress=in_progress,
            completed=completed,
            overdue_count=overdue_count,
        )