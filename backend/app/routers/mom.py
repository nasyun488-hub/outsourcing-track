from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any

from app.database import get_db
from app.services.mom_service import MOMService

router = APIRouter(prefix="/api/mom", tags=["mom"])


class MOMSyncRequest(BaseModel):
    """MOM同步请求基类"""
    pass


class MOMOrdersSyncRequest(MOMSyncRequest):
    """拉取MOM派工单请求"""
    factory_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class MOMRecordsSyncRequest(MOMSyncRequest):
    """推送流转记录到MOM请求"""
    order_id: int
    process_id: int
    record_data: Optional[dict] = None


class MOMSyncResponse(BaseModel):
    """MOM同步响应"""
    success: bool
    message: str
    data: Optional[Any] = None
    retry_count: int = 0


@router.post("/orders/sync", response_model=MOMSyncResponse)
def sync_mom_orders(
    request: MOMOrdersSyncRequest,
    db: Session = Depends(get_db),
):
    """
    从MOM拉取派工单
    - 失败重试3次，间隔5分钟
    - 3次失败触发sync_error通知
    """
    service = MOMService(db)
    result = service.sync_orders_from_mom(
        factory_id=request.factory_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    return result


@router.post("/records/sync", response_model=MOMSyncResponse)
def sync_mom_records(
    request: MOMRecordsSyncRequest,
    db: Session = Depends(get_db),
):
    """
    推送流转记录到MOM
    - 失败重试3次，间隔5分钟
    - 3次失败触发sync_error通知
    """
    service = MOMService(db)
    result = service.sync_record_to_mom(
        order_id=request.order_id,
        process_id=request.process_id,
        record_data=request.record_data,
    )
    return result
