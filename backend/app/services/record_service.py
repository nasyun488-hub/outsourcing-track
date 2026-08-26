"""
流转记录核心业务逻辑服务
包含三层锁定状态机、分批机制、退件处理等核心逻辑
"""
from datetime import datetime
from typing import Optional, List, Tuple
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.record import ProcessRecord, ReceiveBatch, ShipBatch, ReturnRecord
from app.models.order import Order
from app.models.process import Process
from app.models.factory import Factory
from app.models.user import User
from app.models.action_log import ActionLog


class RecordServiceError(Exception):
    """业务逻辑异常"""
    def __init__(self, message: str, code: str = "RECORD_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class RecordService:
    """流转记录核心业务服务"""

    # 允许操作的角色
    ALLOWED_ROLES = ["enterprise_admin", "primary_admin", "primary_operator", 
                     "cooperative_admin", "cooperative_operator"]

    def __init__(self, db: Session):
        self.db = db

    def _generate_id(self) -> str:
        """生成UUID"""
        return uuid.uuid4().hex

    def _get_record(self, record_id: str) -> ProcessRecord:
        """获取流转记录"""
        record = self.db.query(ProcessRecord).filter(
            ProcessRecord.record_id == record_id
        ).first()
        if not record:
            raise RecordServiceError(f"流转记录不存在: {record_id}", "RECORD_NOT_FOUND")
        return record

    def _get_user(self, user_id: str) -> User:
        """获取用户"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise RecordServiceError(f"用户不存在: {user_id}", "USER_NOT_FOUND")
        return user

    def _get_previous_process_record(self, record: ProcessRecord) -> Optional[ProcessRecord]:
        """获取上道工序的流转记录"""
        # 获取当前工序信息
        process = self.db.query(Process).filter(
            Process.process_id == record.process_id
        ).first()
        if not process:
            raise RecordServiceError(f"工序不存在: {record.process_id}", "PROCESS_NOT_FOUND")

        # 查找上道工序（process_order - 1）
        prev_process = self.db.query(Process).filter(
            and_(
                Process.order_id == record.order_id,
                Process.process_order == process.process_order - 1
            )
        ).first()

        if not prev_process:
            return None  # 本道是第一道工序

        # 获取上道工序的流转记录
        prev_record = self.db.query(ProcessRecord).filter(
            and_(
                ProcessRecord.order_id == record.order_id,
                ProcessRecord.process_id == prev_process.process_id
            )
        ).first()
        return prev_record

    def _get_next_process_record(self, record: ProcessRecord) -> Optional[ProcessRecord]:
        """获取下道工序的流转记录"""
        process = self.db.query(Process).filter(
            Process.process_id == record.process_id
        ).first()
        if not process:
            return None

        next_process = self.db.query(Process).filter(
            and_(
                Process.order_id == record.order_id,
                Process.process_order == process.process_order + 1
            )
        ).first()

        if not next_process:
            return None

        next_record = self.db.query(ProcessRecord).filter(
            and_(
                ProcessRecord.order_id == record.order_id,
                ProcessRecord.process_id == next_process.process_id
            )
        ).first()
        return next_record

    def _check_receive_permission(self, user: User, record: ProcessRecord) -> bool:
        """检查接收权限：用户必须在对应厂家"""
        if user.factory_id != record.factory_id:
            raise RecordServiceError("您不属于该厂家，无权操作", "PERMISSION_DENIED")
        return True

    def _check_lock_for_receive(self, record: ProcessRecord) -> None:
        """检查接收时的锁定状态

        entry_lock 表示本道首次接收后、下道确认前的录入保护，
        但不能阻断同一工序继续分批接收；relation_lock/sync_lock 才是不可再接收状态。
        """
        if record.lock_type in ["relation_lock", "sync_lock"]:
            raise RecordServiceError(
                f"记录已锁定（{record.lock_type}），无法接收",
                "RECORD_LOCKED"
            )

    def _check_lock_for_ship(self, record: ProcessRecord) -> None:
        """检查发出时的锁定状态

        entry_lock 不能阻断发出，否则会形成：接收后 entry_lock → 不能发出 → 下道不能接收 → 无法升级 relation_lock 的死锁。
        """
        if record.lock_type in ["relation_lock", "sync_lock"]:
            raise RecordServiceError(
                f"记录已锁定（{record.lock_type}），无法发出",
                "RECORD_LOCKED"
            )

    def _attach_runtime_fields(self, record: ProcessRecord) -> ProcessRecord:
        """给 ORM 对象附加前端所需的只读运行态字段。"""
        prev_record = self._get_previous_process_record(record)
        next_record = self._get_next_process_record(record)
        process = self.db.query(Process).filter(Process.process_id == record.process_id).first()
        factory = self.db.query(Factory).filter(Factory.factory_id == record.factory_id).first()

        order = self.db.query(Order).filter(Order.order_id == record.order_id).first()
        prev_snapshot = self._quantity_snapshot(prev_record) if prev_record else None
        snapshot = self._quantity_snapshot(record)
        upstream_qty = prev_snapshot["effective_ship_qty"] if prev_snapshot else (order.total_qty if order else record.total_receive_qty)
        upstream_qty = max(int(upstream_qty or 0), 0)
        prev_ship_qty = upstream_qty
        effective_receive_qty = min(snapshot["effective_receive_qty"], upstream_qty)
        effective_ship_qty = min(snapshot["effective_ship_qty"], effective_receive_qty)
        available_receive_qty = max(upstream_qty - effective_receive_qty, 0)
        available_ship_qty = max(effective_receive_qty - effective_ship_qty, 0)

        setattr(record, "previous_record_id", prev_record.record_id if prev_record else None)
        setattr(record, "next_record_id", next_record.record_id if next_record else None)
        setattr(record, "process_seq", str(process.process_order) if process else "")
        setattr(record, "process_name", process.process_name if process else record.process_id)
        setattr(record, "factory_name", factory.factory_name if factory else record.factory_id)
        setattr(record, "prev_ship_qty", prev_ship_qty)
        setattr(record, "current_receive_qty", effective_receive_qty)
        setattr(record, "current_ship_qty", effective_ship_qty)
        setattr(record, "available_receive_qty", available_receive_qty)
        setattr(record, "available_ship_qty", available_ship_qty)
        setattr(record, "returned_out_qty", snapshot["returned_out_qty"])
        setattr(record, "returned_in_qty", snapshot["returned_in_qty"])
        setattr(record, "gross_receive_qty", record.total_receive_qty)
        setattr(record, "gross_ship_qty", record.total_ship_qty)
        return record

    def _write_action_log(
        self, user_id: str, action_type: str, target_table: str,
        target_id: str, old_value: dict = None, new_value: dict = None
    ) -> ActionLog:
        """写入操作日志"""
        log = ActionLog(
            log_id=self._generate_id(),
            user_id=user_id,
            action_type=action_type,
            target_table=target_table,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value
        )
        self.db.add(log)
        return log

    def _sum_return_qty(self, record_id: str, direction: str) -> int:
        """汇总退件数量。

        direction=out：本记录作为上道发送方，被下道退回的数量。
        direction=in：本记录作为下道接收方，主动退回给上道的数量。

        退件采用“业务流水 + 有效数量”模型：历史接收/发出批次数量不回写扣减，
        当前可用量统一通过 total - return 汇总计算，避免历史批次被改写后对账混乱。
        """
        column = ReturnRecord.from_record_id if direction == "out" else ReturnRecord.to_record_id
        value = self.db.query(func.coalesce(func.sum(ReturnRecord.return_qty), 0)).filter(
            column == record_id
        ).scalar()
        return int(value or 0)

    def _quantity_snapshot(self, record: ProcessRecord) -> dict:
        """返回记录的毛数量、退件数量、有效数量快照。"""
        returned_out_qty = self._sum_return_qty(record.record_id, "out")
        returned_in_qty = self._sum_return_qty(record.record_id, "in")
        effective_receive_qty = max((record.total_receive_qty or 0) - returned_in_qty, 0)
        effective_ship_qty = max((record.total_ship_qty or 0) - returned_out_qty, 0)
        return {
            "returned_out_qty": returned_out_qty,
            "returned_in_qty": returned_in_qty,
            "effective_receive_qty": effective_receive_qty,
            "effective_ship_qty": effective_ship_qty,
        }

    def _sync_record_status_by_effective_qty(self, record: ProcessRecord) -> None:
        """按有效数量同步记录状态，不回写历史批次数量。"""
        snapshot = self._quantity_snapshot(record)
        effective_receive_qty = snapshot["effective_receive_qty"]
        effective_ship_qty = snapshot["effective_ship_qty"]

        if effective_ship_qty > 0:
            record.record_status = "shipped"
        elif effective_receive_qty > 0:
            record.record_status = "received"
        else:
            record.record_status = "pending"

        if record.record_status == "pending" and record.lock_type != "sync_lock":
            record.lock_type = "none"
        elif record.lock_type == "relation_lock":
            record.lock_type = "entry_lock"

    def receive(
        self, record_id: str, user_id: str, receive_qty: int,
        receive_time: datetime = None
    ) -> Tuple[ReceiveBatch, ProcessRecord]:
        """
        接收录入
        - 权限校验：用户在对应厂家
        - 前置校验：上道有ship_qty，下道未接收
        - 分批机制：每批独立batch_no
        - 锁定：首次接收后 entry_lock
        """
        # 获取记录和用户
        record = self._get_record(record_id)
        user = self._get_user(user_id)

        # 权限检查
        self._check_receive_permission(user, record)

        # 锁定检查
        self._check_lock_for_receive(record)

        # 前置校验：上道必须有有效发出量
        prev_record = self._get_previous_process_record(record)
        if prev_record and self._quantity_snapshot(prev_record)["effective_ship_qty"] == 0:
            raise RecordServiceError(
                "上道工序尚无发出量，本道无法接收",
                "NO_SHIP_FROM_PREV"
            )

        # 前置校验：接收量不能超过上游有效可供量；首道以上单总量为上限
        if prev_record:
            prev_snapshot = self._quantity_snapshot(prev_record)
            snapshot = self._quantity_snapshot(record)
            available_qty = prev_snapshot["effective_ship_qty"] - snapshot["effective_receive_qty"]
        else:
            order = self.db.query(Order).filter(Order.order_id == record.order_id).first()
            snapshot = self._quantity_snapshot(record)
            available_qty = (order.total_qty if order else 0) - snapshot["effective_receive_qty"]
        if receive_qty > available_qty:
            raise RecordServiceError(
                f"接收数量({receive_qty})超过可接收量({available_qty})",
                "QTY_EXCEED"
            )

        # 计算批次号
        batch_count = self.db.query(ReceiveBatch).filter(
            ReceiveBatch.record_id == record_id
        ).count()
        batch_no = batch_count + 1

        # 创建接收批次
        receive_time = receive_time or datetime.utcnow()
        batch = ReceiveBatch(
            batch_id=self._generate_id(),
            record_id=record_id,
            user_id=user_id,
            receive_time=receive_time,
            receive_qty=receive_qty,
            batch_no=batch_no,
            return_qty=0
        )
        self.db.add(batch)

        # 记录操作前的状态
        old_status = {
            "record_status": record.record_status,
            "total_receive_qty": record.total_receive_qty,
            "lock_type": record.lock_type
        }

        # 更新流转记录
        record.total_receive_qty += receive_qty
        record.last_receive_time = receive_time
        record.partial_receive = 1 if batch_no > 1 else 0

        # 首次接收后状态更新
        if record.record_status == "pending":
            record.record_status = "received"
            record.lock_type = "entry_lock"

        # 记录操作日志
        self._write_action_log(
            user_id=user_id,
            action_type="RECEIVE",
            target_table="receive_batches",
            target_id=batch.batch_id,
            old_value=None,
            new_value={
                "batch_id": batch.batch_id,
                "record_id": record_id,
                "receive_qty": receive_qty,
                "batch_no": batch_no
            }
        )

        self._write_action_log(
            user_id=user_id,
            action_type="UPDATE",
            target_table="process_records",
            target_id=record_id,
            old_value=old_status,
            new_value={
                "record_status": record.record_status,
                "total_receive_qty": record.total_receive_qty,
                "lock_type": record.lock_type
            }
        )

        # P0 Bug Fix: 检测上一道 record 是否为 entry_lock，若是则自动升级为 relation_lock
        prev_record_for_lock = self._get_previous_process_record(record)
        if prev_record_for_lock and prev_record_for_lock.lock_type == "entry_lock":
            old_prev_lock = prev_record_for_lock.lock_type
            prev_record_for_lock.lock_type = "relation_lock"
            self._write_action_log(
                user_id=user_id,
                action_type="UPGRADE_LOCK",
                target_table="process_records",
                target_id=prev_record_for_lock.record_id,
                old_value={"lock_type": old_prev_lock},
                new_value={"lock_type": "relation_lock"}
            )

        # 更新订单状态
        self._update_order_status(record.order_id, user_id)

        self.db.commit()
        self.db.refresh(record)
        self.db.refresh(batch)

        return batch, record

    def ship(
        self, record_id: str, user_id: str, ship_qty: int,
        ship_time: datetime = None
    ) -> Tuple[ShipBatch, ProcessRecord]:
        """
        发出录入
        - 权限校验
        - 前置校验：累计接收量 >= 本次发出量
        - 分批机制
        - 发出后状态更新
        - 下道接收确认后自动升级relation_lock
        """
        record = self._get_record(record_id)
        user = self._get_user(user_id)

        # 权限检查
        self._check_receive_permission(user, record)

        # 锁定检查
        self._check_lock_for_ship(record)

        # 前置校验：有效累计已接收 - 有效累计已发出 为本次可发出量
        snapshot = self._quantity_snapshot(record)
        available_ship_qty = snapshot["effective_receive_qty"] - snapshot["effective_ship_qty"]
        if ship_qty > available_ship_qty:
            raise RecordServiceError(
                f"发出数量({ship_qty})超过可发出量({available_ship_qty})",
                "QTY_EXCEED"
            )

        # 计算批次号
        batch_count = self.db.query(ShipBatch).filter(
            ShipBatch.record_id == record_id
        ).count()
        batch_no = batch_count + 1

        # 创建发出批次
        ship_time = ship_time or datetime.utcnow()
        batch = ShipBatch(
            batch_id=self._generate_id(),
            record_id=record_id,
            user_id=user_id,
            ship_time=ship_time,
            ship_qty=ship_qty,
            batch_no=batch_no
        )
        self.db.add(batch)

        # 记录操作前的状态
        old_status = {
            "record_status": record.record_status,
            "total_ship_qty": record.total_ship_qty,
            "lock_type": record.lock_type
        }

        # 更新流转记录
        record.total_ship_qty += ship_qty
        record.last_ship_time = ship_time
        record.partial_ship = 1 if batch_no > 1 else 0
        record.record_status = "shipped"

        # 写入操作日志
        self._write_action_log(
            user_id=user_id,
            action_type="SHIP",
            target_table="ship_batches",
            target_id=batch.batch_id,
            old_value=None,
            new_value={
                "batch_id": batch.batch_id,
                "record_id": record_id,
                "ship_qty": ship_qty,
                "batch_no": batch_no
            }
        )

        self._write_action_log(
            user_id=user_id,
            action_type="UPDATE",
            target_table="process_records",
            target_id=record_id,
            old_value=old_status,
            new_value={
                "record_status": record.record_status,
                "total_ship_qty": record.total_ship_qty,
                "lock_type": record.lock_type
            }
        )

        # 更新订单状态
        self._update_order_status(record.order_id, user_id)

        self.db.commit()
        self.db.refresh(record)
        self.db.refresh(batch)

        return batch, record

    def return_goods(
        self, from_record_id: str, to_record_id: str, user_id: str,
        return_qty: int, return_reason: str
    ) -> Tuple[ReturnRecord, ProcessRecord, ProcessRecord]:
        """
        退件
        - 退件数量为正数
        - 更新本道receive_qty（减少）和上道ship_qty（减少）
        - 必须填写退件原因
        - 锁定状态检查
        """
        from_record = self._get_record(from_record_id)
        to_record = self._get_record(to_record_id)
        user = self._get_user(user_id)

        # 权限检查：用户必须在接收退回方厂家
        self._check_receive_permission(user, to_record)

        # 原因必填
        if not return_reason or len(return_reason.strip()) == 0:
            raise RecordServiceError("退件原因必填", "REASON_REQUIRED")

        # 退件数量必须为正
        if return_qty <= 0:
            raise RecordServiceError("退件数量必须为正数", "QTY_MUST_POSITIVE")

        # 锁定检查：sync_lock 表示已同步MOM，不允许退件；relation_lock 表示上下道已确认，
        # 但真实业务中退件正发生在下道确认接收后，因此允许 relation_lock 下退件并在后续降级为 entry_lock。
        if from_record.lock_type == "sync_lock":
            raise RecordServiceError(
                f"发送方记录已锁定（{from_record.lock_type}），无法退件",
                "RECORD_LOCKED"
            )
        if to_record.lock_type == "sync_lock":
            raise RecordServiceError(
                f"接收方记录已锁定（{to_record.lock_type}），无法退件",
                "RECORD_LOCKED"
            )

        # 校验退件量不能超过有效可退量：历史批次不回写扣减，按退件流水汇总计算净值。
        to_snapshot = self._quantity_snapshot(to_record)
        from_snapshot = self._quantity_snapshot(from_record)
        if return_qty > to_snapshot["effective_receive_qty"]:
            raise RecordServiceError(
                f"退件数量({return_qty})超过接收方有效接收量({to_snapshot['effective_receive_qty']})",
                "QTY_EXCEED"
            )

        if return_qty > from_snapshot["effective_ship_qty"]:
            raise RecordServiceError(
                f"退件数量({return_qty})超过发送方有效发出量({from_snapshot['effective_ship_qty']})",
                "QTY_EXCEED"
            )

        # 创建退件记录
        return_record = ReturnRecord(
            return_id=self._generate_id(),
            from_record_id=from_record_id,
            to_record_id=to_record_id,
            user_id=user_id,
            return_reason=return_reason,
            return_qty=return_qty
        )
        self.db.add(return_record)

        # 记录操作前的状态
        old_from_status = {
            "total_ship_qty": from_record.total_ship_qty,
            "lock_type": from_record.lock_type
        }
        old_to_status = {
            "total_receive_qty": to_record.total_receive_qty,
            "lock_type": to_record.lock_type
        }

        # 退件只记录业务流水，不直接核减 total_receive_qty / total_ship_qty。
        # total_* 保留历史累计毛数量，当前可用量由 _quantity_snapshot() 统一按退件流水折算。
        # 这样接收批次、发出批次、退件记录三类凭证可独立对账，避免“历史批次被改写”造成混乱。
        from_record.partial_ship = 1
        to_record.partial_receive = 1
        self._sync_record_status_by_effective_qty(from_record)
        self._sync_record_status_by_effective_qty(to_record)

        # 写入操作日志
        self._write_action_log(
            user_id=user_id,
            action_type="RETURN",
            target_table="return_records",
            target_id=return_record.return_id,
            old_value=None,
            new_value={
                "return_id": return_record.return_id,
                "from_record_id": from_record_id,
                "to_record_id": to_record_id,
                "return_qty": return_qty,
                "return_reason": return_reason
            }
        )

        self._write_action_log(
            user_id=user_id,
            action_type="UPDATE",
            target_table="process_records",
            target_id=from_record_id,
            old_value=old_from_status,
            new_value={
                "total_ship_qty": from_record.total_ship_qty,
                "effective_ship_qty": self._quantity_snapshot(from_record)["effective_ship_qty"],
                "returned_out_qty": self._quantity_snapshot(from_record)["returned_out_qty"],
                "lock_type": from_record.lock_type,
                "record_status": from_record.record_status
            }
        )

        self._write_action_log(
            user_id=user_id,
            action_type="UPDATE",
            target_table="process_records",
            target_id=to_record_id,
            old_value=old_to_status,
            new_value={
                "total_receive_qty": to_record.total_receive_qty,
                "effective_receive_qty": self._quantity_snapshot(to_record)["effective_receive_qty"],
                "returned_in_qty": self._quantity_snapshot(to_record)["returned_in_qty"],
                "lock_type": to_record.lock_type,
                "record_status": to_record.record_status
            }
        )

        self._update_order_status(from_record.order_id, user_id)

        self.db.commit()
        self.db.refresh(return_record)
        self.db.refresh(from_record)
        self.db.refresh(to_record)

        return return_record, self._attach_runtime_fields(from_record), self._attach_runtime_fields(to_record)

    def _update_order_status(self, order_id: str, operator_id: Optional[str] = None) -> None:
        """更新订单状态。

        业务终态以数量闭环为准：所有工序累计发出量均达到订单总量时，订单自动完成。
        同时把已足量发出的工序标记为 completed/sync_lock，避免看板统计仍停留在 shipped/in_progress。
        """
        order = self.db.query(Order).filter(Order.order_id == order_id).first()
        records = self.get_order_records(order_id)
        if not order or not records:
            return

        total_qty = order.total_qty or 0
        all_fully_shipped = total_qty > 0 and all(
            self._quantity_snapshot(r)["effective_ship_qty"] >= total_qty for r in records
        )

        if all_fully_shipped:
            new_status = "completed"
            for r in records:
                if r.record_status != "completed" or r.lock_type != "sync_lock":
                    old_record_state = {
                        "record_status": r.record_status,
                        "lock_type": r.lock_type,
                    }
                    r.record_status = "completed"
                    r.lock_type = "sync_lock"
                    log_user_id = operator_id or self._get_system_user_id() or "system"
                    if log_user_id != "system":
                        self._write_action_log(
                            user_id=log_user_id,
                            action_type="COMPLETE_RECORD",
                            target_table="process_records",
                            target_id=r.record_id,
                            old_value=old_record_state,
                            new_value={"record_status": "completed", "lock_type": "sync_lock"}
                        )
        elif any(self._quantity_snapshot(r)["effective_receive_qty"] > 0 or self._quantity_snapshot(r)["effective_ship_qty"] > 0 for r in records):
            new_status = "in_progress"
        else:
            new_status = "pending"

        if order.order_status != new_status:
            old_status = order.order_status
            order.order_status = new_status
            log_user_id = operator_id or self._get_system_user_id() or "system"
            if log_user_id != "system":
                self._write_action_log(
                    user_id=log_user_id,
                    action_type="UPDATE_ORDER_STATUS",
                    target_table="orders",
                    target_id=order_id,
                    old_value={"order_status": old_status},
                    new_value={"order_status": new_status}
                )

    def _get_system_user_id(self) -> Optional[str]:
        """获取可用于系统日志的真实用户ID，避免 action_logs.user_id 外键失败。"""
        user = self.db.query(User).filter(User.role == "enterprise_admin").first()
        return user.user_id if user else None

    def get_order_records(self, order_id: str) -> List[ProcessRecord]:
        """获取订单全部工序流转状态"""
        records = self.db.query(ProcessRecord).filter(
            ProcessRecord.order_id == order_id
        ).order_by(ProcessRecord.created_at).all()

        return [self._attach_runtime_fields(record) for record in records]

    def get_record_detail(self, record_id: str) -> ProcessRecord:
        """获取流转记录详情（含批次），附带上下道记录ID供前端退件/跳转使用。"""
        record = self._get_record(record_id)
        return self._attach_runtime_fields(record)

    def scan_judge(self, qr_code: str, user_id: str = None) -> dict:
        """
        扫码跳转判断
        qr_code格式: record_{record_id} 或 process_{process_id}_{factory_id}
        返回: jump_type (receive/ship/view/not_found)
        """
        # 解析qr_code
        if qr_code.startswith("record_"):
            record_id = qr_code.replace("record_", "")
            record = self.db.query(ProcessRecord).filter(
                ProcessRecord.record_id == record_id
            ).first()
        elif qr_code.startswith("process_"):
            # process_{process_id}_{factory_id}
            parts = qr_code.split("_")
            if len(parts) >= 3:
                process_id = "_".join(parts[1:-1])
                factory_id = parts[-1]
                record = self.db.query(ProcessRecord).filter(
                    and_(
                        ProcessRecord.process_id == process_id,
                        ProcessRecord.factory_id == factory_id
                    )
                ).first()
            else:
                return {
                    "qr_code": qr_code,
                    "jump_type": "not_found",
                    "message": "二维码格式错误"
                }
        else:
            return {
                "qr_code": qr_code,
                "jump_type": "not_found",
                "message": "无法识别的二维码格式"
            }

        if not record:
            return {
                "qr_code": qr_code,
                "jump_type": "not_found",
                "message": "未找到对应的流转记录"
            }

        # 判断跳转类型
        jump_type = "view"  # 默认查看页

        if record.record_status == "pending":
            # 待接收 -> 接收页
            jump_type = "receive"
        elif record.record_status == "received":
            # 已接收未发出 -> 发出页
            jump_type = "ship"
        elif record.record_status in ["shipped", "completed"]:
            # 已发出 -> 查看页
            jump_type = "view"

        return {
            "qr_code": qr_code,
            "record_id": record.record_id,
            "jump_type": jump_type,
            "message": f"跳转到{jump_type}页面",
            "record_status": record.record_status,
            "lock_type": record.lock_type,
            "factory_id": record.factory_id
        }

    def upgrade_to_relation_lock(self, record_id: str, operator_id: str) -> ProcessRecord:
        """
        升级到relation_lock
        条件：下道工序接收确认后，本道自动升级
        """
        record = self._get_record(record_id)

        # 检查是否有下道
        next_record = self._get_next_process_record(record)
        if not next_record:
            raise RecordServiceError("没有下道工序，无法升级锁定状态", "NO_NEXT_PROCESS")

        # 检查下道是否已接收
        if next_record.record_status not in ["received", "shipped", "completed"]:
            raise RecordServiceError(
                "下道工序尚未接收，无法升级锁定状态",
                "NEXT_NOT_RECEIVED"
            )

        old_lock = record.lock_type
        record.lock_type = "relation_lock"

        self._write_action_log(
            user_id=operator_id,
            action_type="UPGRADE_LOCK",
            target_table="process_records",
            target_id=record_id,
            old_value={"lock_type": old_lock},
            new_value={"lock_type": "relation_lock"}
        )

        self.db.commit()
        self.db.refresh(record)
        return record

    def upgrade_to_sync_lock(self, record_id: str, operator_id: str) -> ProcessRecord:
        """
        升级到sync_lock
        条件：数据同步至MOM后升级
        """
        record = self._get_record(record_id)

        if record.lock_type != "relation_lock":
            raise RecordServiceError(
                f"当前状态({record.lock_type})无法直接升级到sync_lock",
                "INVALID_LOCK_TRANSITION"
            )

        old_lock = record.lock_type
        record.lock_type = "sync_lock"

        self._write_action_log(
            user_id=operator_id,
            action_type="UPGRADE_LOCK",
            target_table="process_records",
            target_id=record_id,
            old_value={"lock_type": old_lock},
            new_value={"lock_type": "sync_lock"}
        )

        self.db.commit()
        self.db.refresh(record)
        return record
