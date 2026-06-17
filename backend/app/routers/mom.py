from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.mom_service import MOMService

router = APIRouter(prefix="/api/mom", tags=["mom"])


class MOMProcessItem(BaseModel):
    process_id: Optional[str] = None
    process_seq: str
    process_name: str
    factory_id: str
    process_order: Optional[int] = None


class MOMOrderItem(BaseModel):
    order_id: str
    primary_factory_id: str
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    spec: Optional[str] = None
    unit: Optional[str] = None
    delivery_date: Optional[str] = None
    part_no: Optional[str] = None
    total_qty: int = 0
    mom_created_at: Optional[str] = None
    processes: list[MOMProcessItem] = Field(default_factory=list)


class MOMImportRequest(BaseModel):
    source_type: Literal["mom_json", "standard_file"] = "standard_file"
    batch_no: Optional[str] = None
    dry_run: bool = False
    orders: list[MOMOrderItem]


class MOMImportResponse(BaseModel):
    success: bool
    message: str
    source_type: str
    created_orders: int
    updated_orders: int
    created_processes: int
    updated_processes: int
    created_records: int
    skipped_records: int
    action_log_id: Optional[str] = None
    errors: list[str] = Field(default_factory=list)


def require_import_permission(user: User) -> None:
    if user.role not in {"enterprise_admin", "primary_admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅企业管理员或主厂管理员可导入MOM标准文件",
        )


@router.post("/orders/import", response_model=MOMImportResponse)
def import_mom_orders(
    payload: MOMImportRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    require_import_permission(current_user)
    service = MOMService(db)
    try:
        return service.import_orders(
            payload=payload.model_dump(),
            user=current_user,
            ip_address=request.client.host if request.client else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
