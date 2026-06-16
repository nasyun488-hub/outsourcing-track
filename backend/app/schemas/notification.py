from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class NotificationResponse(BaseModel):
    """通知响应"""
    id: int
    user_id: int
    type: str
    title: str
    content: Optional[str] = None
    is_read: int  # 0: 未读, 1: 已读
    related_id: Optional[int] = None
    related_type: Optional[str] = None
    created_at: str
    read_at: Optional[str] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """通知列表响应"""
    total: int
    unread_count: int
    items: List[NotificationResponse]


class NotificationCreateRequest(BaseModel):
    """创建通知请求"""
    user_id: int
    type: str  # transfer/sync_error/approval/register
    title: str
    content: Optional[str] = None
    related_id: Optional[int] = None
    related_type: Optional[str] = None
