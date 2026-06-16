from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import get_db
from app.schemas.notification import NotificationResponse, NotificationListResponse
from app.services.notification_service import NotificationService
from app.models.user import User
from app.config import settings
from jose import jwt, JWTError

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
security = HTTPBearer()


class NotificationResponse(BaseModel):
    notif_id: str
    user_id: str
    notif_type: str
    title: str
    content: Optional[str] = None
    is_read: int
    related_id: Optional[str] = None
    related_type: Optional[str] = None
    jump_url: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    total: int
    unread_count: int
    items: List[NotificationResponse]


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """从JWT token解析当前用户"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的认证信息")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的认证信息")

    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="用户不存在或未启用")
    return user


@router.get("", response_model=NotificationListResponse)
def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_read: Optional[int] = Query(None, description="0: 未读, 1: 已读"),
    notif_type: Optional[str] = Query(None, description="通知类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取我的通知列表
    - 支持分页
    - 支持按已读状态、类型过滤
    """
    service = NotificationService(db)
    result = service.get_user_notifications(
        user_id=current_user.user_id,
        page=page,
        page_size=page_size,
        is_read=is_read,
        notif_type=notif_type,
    )
    return result


@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    标记通知已读
    """
    service = NotificationService(db)
    success = service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.user_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="通知不存在或无权操作")

    return {"success": True, "message": "已标记为已读"}


@router.put("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    标记所有通知已读
    """
    service = NotificationService(db)
    count = service.mark_all_as_read(user_id=current_user.user_id)
    return {"success": True, "message": f"已标记{count}条通知为已读"}
