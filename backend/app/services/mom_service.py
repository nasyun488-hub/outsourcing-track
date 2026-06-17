from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.action_log import ActionLog
from app.models.order import Order
from app.models.process import Process
from app.models.record import ProcessRecord
from app.models.user import User


class MOMService:
    """MOM标准文件/JSON导入服务。"""

    def __init__(self, db: Session):
        self.db = db

    def import_orders(
        self,
        payload: dict[str, Any],
        user: User,
        ip_address: Optional[str] = None,
    ) -> dict[str, Any]:
        source_type = payload.get("source_type") or "standard_file"
        if source_type not in {"mom_json", "standard_file"}:
            raise ValueError("source_type仅支持mom_json或standard_file")

        orders = payload.get("orders") or []
        if not isinstance(orders, list) or not orders:
            raise ValueError("orders不能为空")

        created_orders = 0
        updated_orders = 0
        created_processes = 0
        updated_processes = 0
        created_records = 0
        skipped_records = 0
        errors: list[str] = []

        for order_data in orders:
            order_id = str(order_data.get("order_id") or "").strip()
            primary_factory_id = str(order_data.get("primary_factory_id") or "").strip()
            if not order_id or not primary_factory_id:
                errors.append("订单缺少order_id或primary_factory_id")
                continue

            order = self.db.query(Order).filter(Order.order_id == order_id).first()
            order_values = {
                "primary_factory_id": primary_factory_id,
                "product_name": order_data.get("product_name"),
                "product_code": order_data.get("product_code"),
                "spec": order_data.get("spec"),
                "unit": order_data.get("unit"),
                "delivery_date": self._parse_dt(order_data.get("delivery_date")),
                "part_no": order_data.get("part_no"),
                "total_qty": int(order_data.get("total_qty") or 0),
                "mom_created_at": self._parse_dt(order_data.get("mom_created_at")),
            }
            if order is None:
                order = Order(order_id=order_id, **order_values)
                self.db.add(order)
                created_orders += 1
            else:
                for key, value in order_values.items():
                    setattr(order, key, value)
                updated_orders += 1

            processes = order_data.get("processes") or []
            for index, process_data in enumerate(processes, start=1):
                process_seq = str(process_data.get("process_seq") or "").strip()
                process_name = str(process_data.get("process_name") or "").strip()
                factory_id = str(process_data.get("factory_id") or "").strip()
                if not process_seq or not process_name or not factory_id:
                    errors.append(f"订单{order_id}存在不完整工序")
                    continue

                process_id = process_data.get("process_id") or f"{order_id}-{process_seq}"
                process = self.db.query(Process).filter(Process.process_id == process_id).first()
                process_values = {
                    "order_id": order_id,
                    "process_seq": process_seq,
                    "process_name": process_name,
                    "factory_id": factory_id,
                    "process_order": int(process_data.get("process_order") or index),
                }
                if process is None:
                    process = Process(process_id=process_id, **process_values)
                    self.db.add(process)
                    created_processes += 1
                else:
                    for key, value in process_values.items():
                        setattr(process, key, value)
                    updated_processes += 1

                record_id = f"REC-{process_id}"
                record = self.db.query(ProcessRecord).filter(ProcessRecord.record_id == record_id).first()
                if record is None:
                    self.db.add(
                        ProcessRecord(
                            record_id=record_id,
                            order_id=order_id,
                            process_id=process_id,
                            factory_id=factory_id,
                            record_status="pending",
                            lock_type="none",
                            total_receive_qty=0,
                            total_ship_qty=0,
                        )
                    )
                    created_records += 1
                else:
                    skipped_records += 1

        if payload.get("dry_run"):
            self.db.rollback()
            action_log_id = None
        else:
            action_log_id = f"LOG-{uuid4().hex}"
            self.db.add(
                ActionLog(
                    log_id=action_log_id,
                    user_id=user.user_id,
                    action_type="MOM_IMPORT",
                    target_table="orders",
                    target_id=payload.get("batch_no") or "mom_import",
                    old_value=None,
                    new_value={
                        "source_type": source_type,
                        "created_orders": created_orders,
                        "updated_orders": updated_orders,
                        "created_processes": created_processes,
                        "created_records": created_records,
                        "errors": errors,
                    },
                    ip_address=ip_address,
                )
            )
            self.db.commit()

        return {
            "success": not errors,
            "message": "导入完成" if not errors else "导入完成，存在部分错误",
            "source_type": source_type,
            "created_orders": created_orders,
            "updated_orders": updated_orders,
            "created_processes": created_processes,
            "updated_processes": updated_processes,
            "created_records": created_records,
            "skipped_records": skipped_records,
            "action_log_id": action_log_id,
            "errors": errors,
        }

    @staticmethod
    def _parse_dt(value: Any) -> Optional[datetime]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        text = str(value).replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return datetime.strptime(str(value), "%Y-%m-%d")
