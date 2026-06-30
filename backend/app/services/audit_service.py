from __future__ import annotations

from datetime import datetime, time
from io import BytesIO
from typing import Any, Optional

import openpyxl
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.action_log import ActionLog
from app.models.user import User


class AuditService:
    """操作审计查询、汇总与Excel导出。"""

    def __init__(self, db: Session):
        self.db = db

    def list_logs(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 20,
        action_type: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        query = self._base_query(current_user)
        query = self._apply_filters(query, action_type, user_id, start_date, end_date)
        total = query.count()
        rows = (
            query.options(joinedload(ActionLog.user))
            .order_by(ActionLog.created_at.desc())
            .offset(max(page - 1, 0) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [self._serialize_log(row) for row in rows],
        }

    def get_summary(
        self,
        current_user: User,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        query = self._base_query(current_user)
        query = self._apply_filters(query, None, None, start_date, end_date)
        total = query.count()
        by_action = (
            query.with_entities(ActionLog.action_type, func.count(ActionLog.log_id))
            .group_by(ActionLog.action_type)
            .all()
        )
        # 当 current_user 不是 enterprise_admin 时，_base_query 已 join User
        # 重复 join 会导致 SQL JOIN 歧义 (primary_admin 500 bug)
        if current_user.role == "enterprise_admin":
            user_query = query.join(User, User.user_id == ActionLog.user_id)
        else:
            user_query = query  # User 已在 _base_query 中 join
        by_user = (
            user_query.with_entities(ActionLog.user_id, User.name, func.count(ActionLog.log_id))
            .group_by(ActionLog.user_id, User.name)
            .all()
        )
        return {
            "total_logs": total,
            "action_type_counts": {action: count for action, count in by_action},
            "user_counts": [
                {"user_id": uid, "user_name": name, "count": count}
                for uid, name, count in by_user
            ],
        }

    def export_logs(
        self,
        current_user: User,
        action_type: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> BytesIO:
        query = self._base_query(current_user)
        rows = (
            self._apply_filters(query, action_type, user_id, start_date, end_date)
            .options(joinedload(ActionLog.user))
            .order_by(ActionLog.created_at.desc())
            .all()
        )
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "审计日志"
        sheet.append(["时间", "用户", "角色", "动作", "对象表", "对象ID", "IP", "新值"])
        for row in rows:
            sheet.append([
                row.created_at.strftime("%Y-%m-%d %H:%M:%S") if row.created_at else "",
                row.user.name if row.user else row.user_id,
                row.user.role if row.user else "",
                row.action_type,
                row.target_table,
                row.target_id,
                row.ip_address or "",
                str(row.new_value or ""),
            ])
        stream = BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return stream

    def _base_query(self, current_user: User):
        query = self.db.query(ActionLog)
        if current_user.role != "enterprise_admin":
            query = query.join(User, User.user_id == ActionLog.user_id).filter(User.factory_id == current_user.factory_id)
        return query

    @staticmethod
    def _parse_date(value: Optional[str], end: bool = False) -> Optional[datetime]:
        if not value:
            return None
        parsed = datetime.fromisoformat(value)
        if len(value) == 10:
            return datetime.combine(parsed.date(), time.max if end else time.min)
        return parsed

    def _apply_filters(
        self,
        query,
        action_type: Optional[str],
        user_id: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ):
        if action_type:
            query = query.filter(ActionLog.action_type == action_type)
        if user_id:
            query = query.filter(ActionLog.user_id == user_id)
        start = self._parse_date(start_date)
        end = self._parse_date(end_date, end=True)
        if start:
            query = query.filter(ActionLog.created_at >= start)
        if end:
            query = query.filter(ActionLog.created_at <= end)
        return query

    @staticmethod
    def _serialize_log(log: ActionLog) -> dict[str, Any]:
        return {
            "log_id": log.log_id,
            "user_id": log.user_id,
            "user_name": log.user.name if log.user else None,
            "role": log.user.role if log.user else None,
            "action_type": log.action_type,
            "target_table": log.target_table,
            "target_id": log.target_id,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
