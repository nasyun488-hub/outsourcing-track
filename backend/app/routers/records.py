"""
流转记录API路由
包含接收/发出/退件/查询/扫码等接口
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.record_service import RecordService, RecordServiceError
from app.schemas.record import (
    ReceiveRequest, ReceiveResponse, ReceiveBatchResponse, RecordResponse,
    ShipRequest, ShipResponse, ShipBatchResponse,
    ReturnRequest, ReturnResponse, ReturnRecordResponse,
    RecordStatusResponse, OrderRecordsResponse,
    ScanJumpResponse, RecordDetailResponse, BatchScanRequest, BatchScanResponse
)
from app.models.user import User
from app.models.record import ProcessRecord

router = APIRouter(prefix="/api/records", tags=["流转记录"])
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """从JWT token解析当前用户"""
    from app.config import settings
    from jose import jwt, JWTError

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
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="用户未登录、未启用或token无效")
    return user


def check_permission(user: User, allowed_roles: list = None) -> None:
    """权限检查"""
    if allowed_roles is None:
        allowed_roles = RecordService.ALLOWED_ROLES
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"角色 {user.role} 无权执行此操作"
        )


def check_record_visible(user: User, record: ProcessRecord) -> None:
    """详情/扫码可见性：企业管理员可看全部；其他用户仅可看本厂工序记录。"""
    if user.role == "enterprise_admin":
        return
    if user.factory_id != record.factory_id:
        raise HTTPException(status_code=403, detail="无权查看其他厂家流转记录")


@router.post("/receive", response_model=ReceiveResponse)
def receive(
    request: ReceiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    接收录入
    - 权限：coop_admin/operator, primary_admin/operator
    - 前置校验：上道工序有ship_qty，下道工序未接收时不可录入
    - 允许分批接收，每批独立batch_no，累计更新record.total_receive_qty
    - 首次接收后record_status='received'，lock_type='entry_lock'
    """
    check_permission(current_user)

    service = RecordService(db)
    try:
        batch, record = service.receive(
            record_id=request.record_id,
            user_id=current_user.user_id,
            receive_qty=request.receive_qty,
            receive_time=request.receive_time
        )

        return ReceiveResponse(
            success=True,
            message="接收成功",
            batch=ReceiveBatchResponse.model_validate(batch),
            record=RecordResponse.model_validate(record)
        )
    except RecordServiceError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/ship", response_model=ShipResponse)
def ship(
    request: ShipRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    发出录入
    - 权限：同上
    - 发出时检查：累计接收量 >= 本次发出量
    - 允许分批发货，每批独立batch_no
    - 发出后record_status='shipped'
    - 下道工序接收确认后，本道自动升级为relation_lock
    """
    check_permission(current_user)

    service = RecordService(db)
    try:
        batch, record = service.ship(
            record_id=request.record_id,
            user_id=current_user.user_id,
            ship_qty=request.ship_qty,
            ship_time=request.ship_time
        )

        return ShipResponse(
            success=True,
            message="发出成功",
            batch=ShipBatchResponse.model_validate(batch),
            record=RecordResponse.model_validate(record)
        )
    except RecordServiceError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/return", response_model=ReturnResponse)
def return_goods(
    request: ReturnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    退件
    - 在发出页面入口
    - 退件数量为正数，计入上道厂的库存
    - 退件后更新本道receive_qty（减少）和上道ship_qty（减少）
    - 必须填写退件原因
    """
    check_permission(current_user)

    service = RecordService(db)
    try:
        return_record, from_record, to_record = service.return_goods(
            from_record_id=request.from_record_id,
            to_record_id=request.to_record_id,
            user_id=current_user.user_id,
            return_qty=request.return_qty,
            return_reason=request.return_reason
        )

        return ReturnResponse(
            success=True,
            message="退件成功",
            return_record=ReturnRecordResponse.model_validate(return_record),
            from_record=RecordResponse.model_validate(from_record),
            to_record=RecordResponse.model_validate(to_record)
        )
    except RecordServiceError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/{order_id}", response_model=OrderRecordsResponse)
def get_order_records(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取订单全部工序流转状态
    返回订单所有工序的当前状态列表
    """
    check_permission(current_user)

    service = RecordService(db)
    records = service.get_order_records(order_id)

    # 数据隔离：非企业管理员只返回本厂工序记录
    if current_user.role != "enterprise_admin":
        records = [r for r in records if r.factory_id == current_user.factory_id]

    return OrderRecordsResponse(
        order_id=order_id,
        records=[RecordStatusResponse.model_validate(r) for r in records]
    )


@router.get("/scan/judge", response_model=ScanJumpResponse)
def scan_judge(
    qr_code: str = Query(..., description="二维码内容"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    扫码跳转判断
    - 扫码后根据record_status和lock_type判断跳转页面
    - 返回: receive(接收页)/ship(发出页)/view(查看页)/not_found
    """
    check_permission(current_user)

    service = RecordService(db)
    result = service.scan_judge(qr_code)
    if result.get("record_id"):
        try:
            record = service.get_record_detail(result["record_id"])
            check_record_visible(current_user, record)
        except RecordServiceError as e:
            raise HTTPException(status_code=400, detail=e.message)

    return ScanJumpResponse(**result)


@router.post("/scan/batch", response_model=BatchScanResponse)
def batch_scan_judge(
    request: BatchScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量扫码跳转判断：适配固定/手持扫码枪连续扫码、整批粘贴码值。"""
    check_permission(current_user)
    service = RecordService(db)
    items = []
    seen = set()
    for raw_code in request.qr_codes:
        qr_code = (raw_code or "").strip()
        if not qr_code or qr_code in seen:
            continue
        seen.add(qr_code)
        result = service.scan_judge(qr_code)
        if result.get("record_id"):
            try:
                record = service.get_record_detail(result["record_id"])
                check_record_visible(current_user, record)
            except HTTPException:
                result = {"qr_code": qr_code, "jump_type": "not_found", "message": "无权查看该流转记录"}
            except RecordServiceError as e:
                result = {"qr_code": qr_code, "jump_type": "not_found", "message": e.message}
        items.append(ScanJumpResponse(**result))

    success_count = sum(1 for item in items if item.jump_type != "not_found")
    return BatchScanResponse(
        total=len(items),
        success_count=success_count,
        fail_count=len(items) - success_count,
        items=items
    )


@router.get("/detail/{record_id}", response_model=RecordDetailResponse)
def get_record_detail(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取流转记录详情（含批次信息）
    """
    check_permission(current_user)

    service = RecordService(db)
    record = service.get_record_detail(record_id)
    check_record_visible(current_user, record)

    return RecordDetailResponse.model_validate(record)


@router.post("/unlock/{record_id}", response_model=RecordResponse)
def apply_unlock(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    申请解锁（entry_lock状态下，下道未接收确认前，本厂管理员可申请）
    实际解锁逻辑需要审批流程，这里仅记录申请
    """
    # 需要admin角色
    check_permission(current_user, allowed_roles=[
        "enterprise_admin", "primary_admin", "cooperative_admin"
    ])

    service = RecordService(db)
    try:
        record = service.get_record_detail(record_id)

        if record.lock_type != "entry_lock":
            raise HTTPException(
                status_code=400,
                detail="只有entry_lock状态可以申请解锁"
            )

        # 实际应该创建审批请求，这里简化处理
        return RecordResponse.model_validate(record)
    except RecordServiceError as e:
        raise HTTPException(status_code=400, detail=e.message)
