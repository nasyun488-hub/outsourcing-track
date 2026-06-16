from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import get_db
from app.schemas.kanban import (
    OrderKanbanListResponse,
    OrderKanbanResponse,
    ProcessKanbanListResponse,
    ProcessKanbanResponse,
    KanbanStatsResponse,
)
from app.services.kanban_service import KanbanService
from app.models.user import User
from app.config import settings
from jose import jwt, JWTError

router = APIRouter(prefix="/api/kanban", tags=["kanban"])
security = HTTPBearer()


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


@router.get("/orders", response_model=OrderKanbanListResponse)
def get_orders_kanban(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    order_no: Optional[str] = None,
    factory_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    订单总览看板
    - 支持分页
    - 支持按时间范围、订单号、厂家、状态过滤
    """
    service = KanbanService(db)
    result = service.get_orders_kanban(
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
        primary_factory_id=factory_id,
        status=status,
        order_no=order_no,
        current_user=current_user,
    )
    return result


@router.get("/orders/{order_id}/processes", response_model=ProcessKanbanListResponse)
def get_processes_kanban(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    工序流转看板
    - 查看某订单的所有工序及其流转状态
    - 超期标红：pending超48h未处理 或 received超48h未发出
    """
    service = KanbanService(db)
    try:
        result = service.get_processes_kanban(order_id, current_user=current_user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return result


@router.get("/stats", response_model=KanbanStatsResponse)
def get_kanban_stats(
    factory_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    看板统计
    - 全部/待处理/进行中/已完成订单数
    - 超期工序数
    """
    service = KanbanService(db)
    result = service.get_kanban_stats(factory_id=factory_id)
    return result
