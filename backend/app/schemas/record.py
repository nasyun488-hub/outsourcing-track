"""
流转记录相关的Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ============== 基础枚举类型 ==============
RecordStatusLiteral = Literal["pending", "received", "shipped", "completed"]
LockTypeLiteral = Literal["none", "entry_lock", "relation_lock", "sync_lock"]


# ============== 接收录入 ==============
class ReceiveRequest(BaseModel):
    """接收录入请求"""
    record_id: str = Field(..., description="流转记录ID")
    receive_qty: int = Field(..., gt=0, description="接收数量（正整数）")
    receive_time: Optional[datetime] = Field(None, description="接收时间（默认当前时间）")


class ReceiveBatchResponse(BaseModel):
    """接收批次响应"""
    batch_id: str
    record_id: str
    user_id: str
    receive_time: datetime
    receive_qty: int
    batch_no: int
    return_qty: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 发出录入 ==============
class ShipRequest(BaseModel):
    """发出录入请求"""
    record_id: str = Field(..., description="流转记录ID")
    ship_qty: int = Field(..., gt=0, description="发出数量（正整数）")
    ship_time: Optional[datetime] = Field(None, description="发出时间（默认当前时间）")


class ShipBatchResponse(BaseModel):
    """发出批次响应"""
    batch_id: str
    record_id: str
    user_id: str
    ship_time: datetime
    ship_qty: int
    batch_no: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 退件 ==============
class ReturnRequest(BaseModel):
    """退件请求"""
    from_record_id: str = Field(..., description="退出发送方流转记录ID")
    to_record_id: str = Field(..., description="接收退回方流转记录ID")
    return_qty: int = Field(..., gt=0, description="退件数量（正整数）")
    return_reason: str = Field(..., min_length=1, max_length=256, description="退件原因（必填）")


class ReturnRecordResponse(BaseModel):
    """退件记录响应"""
    return_id: str
    from_record_id: str
    to_record_id: str
    user_id: str
    return_reason: str
    return_qty: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 流转记录状态 ==============
class RecordStatusResponse(BaseModel):
    """订单工序状态列表响应"""
    record_id: str
    order_id: str
    process_id: str
    process_seq: str
    process_name: str
    factory_id: str
    factory_name: str
    record_status: RecordStatusLiteral
    lock_type: LockTypeLiteral
    total_receive_qty: int
    total_ship_qty: int
    gross_receive_qty: int = 0
    gross_ship_qty: int = 0
    returned_in_qty: int = 0
    returned_out_qty: int = 0
    prev_ship_qty: int = 0
    current_receive_qty: int = 0
    current_ship_qty: int = 0
    available_receive_qty: int = 0
    available_ship_qty: int = 0
    partial_receive: bool
    partial_ship: bool
    last_receive_time: Optional[datetime]
    last_ship_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== 扫码跳转 ==============
class ScanJumpResponse(BaseModel):
    """扫码跳转判断响应"""
    qr_code: str
    record_id: Optional[str] = None
    jump_type: Literal["receive", "ship", "view", "not_found"] = Field(..., description="跳转类型")
    message: str
    record_status: Optional[RecordStatusLiteral] = None
    lock_type: Optional[LockTypeLiteral] = None
    factory_id: Optional[str] = None


class BatchScanRequest(BaseModel):
    """批量扫码解析请求"""
    qr_codes: List[str] = Field(..., min_length=1, max_length=500, description="二维码内容列表")


class BatchScanResponse(BaseModel):
    """批量扫码解析响应"""
    total: int
    success_count: int
    fail_count: int
    items: List[ScanJumpResponse]


# ============== 操作日志 ==============
class ActionLogResponse(BaseModel):
    """操作日志响应"""
    log_id: str
    user_id: str
    action_type: str
    target_table: str
    target_id: str
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============== 综合响应 ==============
class RecordResponse(BaseModel):
    """流转记录完整响应"""
    record_id: str
    order_id: str
    process_id: str
    process_seq: Optional[str] = None
    process_name: Optional[str] = None
    factory_id: str
    factory_name: Optional[str] = None
    record_status: RecordStatusLiteral
    lock_type: LockTypeLiteral
    total_receive_qty: int
    total_ship_qty: int
    gross_receive_qty: int = 0
    gross_ship_qty: int = 0
    returned_in_qty: int = 0
    returned_out_qty: int = 0
    prev_ship_qty: int = 0
    current_receive_qty: int = 0
    current_ship_qty: int = 0
    available_receive_qty: int = 0
    available_ship_qty: int = 0
    partial_receive: bool
    partial_ship: bool
    last_receive_time: Optional[datetime]
    last_ship_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecordDetailResponse(RecordResponse):
    """带批次的流转记录详情响应"""
    receive_batches: List[ReceiveBatchResponse] = []
    ship_batches: List[ShipBatchResponse] = []
    returns: List[ReturnRecordResponse] = []
    previous_record_id: Optional[str] = None
    next_record_id: Optional[str] = None


class ReceiveResponse(BaseModel):
    """接收操作响应"""
    success: bool
    message: str
    batch: ReceiveBatchResponse
    record: RecordResponse


class ShipResponse(BaseModel):
    """发出操作响应"""
    success: bool
    message: str
    batch: ShipBatchResponse
    record: RecordResponse


class ReturnResponse(BaseModel):
    """退件操作响应"""
    success: bool
    message: str
    return_record: ReturnRecordResponse
    from_record: RecordResponse
    to_record: RecordResponse


class OrderRecordsResponse(BaseModel):
    """订单全部工序流转状态响应"""
    order_id: str
    records: List[RecordStatusResponse]
