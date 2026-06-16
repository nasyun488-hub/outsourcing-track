from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProcessStatusEnum(str, Enum):
    PENDING = "pending"
    RECEIVED = "received"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    TRANSFERRED = "transferred"


# ============ 订单看板 ============

class OrderKanbanBase(BaseModel):
    """订单看板基础Schema"""
    order_no: str
    product_name: str
    quantity: int
    unit: Optional[str] = None
    status: OrderStatusEnum
    delivery_date: Optional[datetime] = None


class OrderKanbanResponse(OrderKanbanBase):
    """订单看板响应"""
    order_id: str
    product_code: Optional[str] = None
    spec: Optional[str] = None
    part_no: Optional[str] = None
    factory_id: str
    factory_name: Optional[str] = None
    primary_factory_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_overdue: bool = False  # 是否有超期工序
    process_count: int = 0    # 工序数量
    pending_count: int = 0    # 待处理工序数
    in_progress_count: int = 0
    completed_count: int = 0

    class Config:
        from_attributes = True


class OrderKanbanListResponse(BaseModel):
    """订单看板列表响应（分页）"""
    total: int
    page: int
    page_size: int
    items: List[OrderKanbanResponse]


# ============ 工序看板 ============

class ProcessKanbanBase(BaseModel):
    """工序看板基础Schema"""
    process_name: Optional[str] = None
    process_order: Optional[int] = None
    status: ProcessStatusEnum
    receive_time: Optional[datetime] = None
    send_time: Optional[datetime] = None
    is_overdue: bool = False  # 超期标红标记


class ProcessKanbanResponse(ProcessKanbanBase):
    """工序看板响应"""
    record_id: str
    order_id: str
    process_id: Optional[str] = None
    process_name: Optional[str] = None
    factory_id: Optional[str] = None
    factory_name: Optional[str] = None
    current_handler_id: Optional[str] = None
    current_handler_name: Optional[str] = None
    prev_process_id: Optional[str] = None
    next_process_id: Optional[str] = None
    is_overdue: bool = False
    receive_qty: int = 0
    ship_qty: int = 0
    prev_ship_qty: int = 0
    current_receive_qty: int = 0
    current_ship_qty: int = 0
    available_receive_qty: int = 0
    available_ship_qty: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProcessKanbanListResponse(BaseModel):
    """工序看板列表响应"""
    order_id: str
    order_no: str
    items: List[ProcessKanbanResponse]


# ============ 统计 ============

class KanbanStatsResponse(BaseModel):
    """看板统计响应"""
    total: int           # 全部订单
    pending: int         # 待处理
    in_progress: int     # 进行中
    completed: int       # 已完成
    overdue_count: int   # 超期工序数
