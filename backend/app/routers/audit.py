from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/audit", tags=["audit"])


def require_audit_permission(current_user: User) -> None:
    if current_user.role not in {"enterprise_admin", "primary_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问操作审计报表")


@router.get("/logs")
def list_audit_logs(
    page: int = 1,
    page_size: int = 20,
    action_type: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_audit_permission(current_user)
    return AuditService(db).list_logs(
        current_user=current_user,
        page=page,
        page_size=page_size,
        action_type=action_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/summary")
def get_audit_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_audit_permission(current_user)
    return AuditService(db).get_summary(
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/export")
def export_audit_logs(
    action_type: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_audit_permission(current_user)
    stream = AuditService(db).export_logs(
        current_user=current_user,
        action_type=action_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )
    headers = {"Content-Disposition": "attachment; filename=audit-logs.xlsx"}
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
