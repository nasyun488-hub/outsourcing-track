from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.export_service import ExportService
from app.models.user import User
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/excel")
def export_excel(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    factory_id: Optional[str] = Query(None, description="厂家ID过滤"),
    order_id: Optional[str] = Query(None, description="订单ID过滤"),
    status: Optional[str] = Query(None, description="订单状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    导出Excel
    - 按角色过滤权限：
      - 企业管理员：全量导出
      - 厂家：仅本厂数据
    - 支持按日期范围、厂家、状态过滤
    """
    service = ExportService(db)
    
    # 获取当前用户信息用于权限过滤
    user_role = current_user.role
    user_factory_id = current_user.factory_id
    
    excel_file = service.export_to_excel(
        user_role=user_role,
        user_factory_id=user_factory_id,
        start_date=start_date,
        end_date=end_date,
        factory_id=factory_id,
        status=status,
        order_id=order_id,
    )
    
    return StreamingResponse(
        iter([excel_file.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=orders_export.xlsx"
        }
    )