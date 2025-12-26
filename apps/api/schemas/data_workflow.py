"""
数据处理工作流 Schema 定义
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class WorkflowStats(BaseModel):
    """工作流统计数据"""
    # 爬虫阶段
    crawl_pending: int = Field(default=0, description="待爬取任务数")

    # OCR 阶段
    ocr_pending: int = Field(default=0, description="OCR 待处理")
    ocr_processing: int = Field(default=0, description="OCR 处理中")
    ocr_completed: int = Field(default=0, description="OCR 已完成")
    ocr_failed: int = Field(default=0, description="OCR 失败")
    ocr_skipped: int = Field(default=0, description="OCR 跳过")

    # 审核阶段
    review_pending: int = Field(default=0, description="待审核")
    review_approved: int = Field(default=0, description="已通过")
    review_rejected: int = Field(default=0, description="已拒绝")

    # 统计指标
    today_processed: int = Field(default=0, description="今日处理量")
    avg_processing_time_ms: int = Field(default=0, description="平均处理时间(ms)")
    success_rate: float = Field(default=0.0, description="成功率")


class WorkerInfo(BaseModel):
    """Worker 信息"""
    id: str = Field(..., description="Worker ID")
    status: str = Field(..., description="状态: active/inactive")
    current_task: Optional[int] = Field(None, description="当前处理的任务 ID")
    last_heartbeat: Optional[datetime] = Field(None, description="最后心跳时间")
    ocr_provider: Optional[str] = Field(None, description="OCR 提供商")
    tasks_completed: int = Field(default=0, description="已完成任务数")


class WorkerListResponse(BaseModel):
    """Worker 列表响应"""
    workers: List[WorkerInfo] = Field(default_factory=list)
    total_active: int = Field(default=0, description="活跃 Worker 数量")


# ========== OCR 任务相关 ==========

class OCRTaskItem(BaseModel):
    """OCR 任务项"""
    pending_id: int
    brand_name: Optional[str] = None
    product_name: Optional[str] = None
    images_count: int = 0
    ocr_status: str
    ocr_priority: int = 0
    ocr_worker_id: Optional[str] = None
    ocr_started_at: Optional[datetime] = None
    ocr_processing_time_ms: Optional[int] = None
    ocr_retry_count: int = 0
    ocr_error_message: Optional[str] = None
    ocr_provider: Optional[str] = None
    created_at: Optional[datetime] = None


class OCRTaskListResponse(BaseModel):
    """OCR 任务列表响应"""
    items: List[OCRTaskItem]
    total: int
    page: int
    page_size: int


class OCRTaskFilters(BaseModel):
    """OCR 任务筛选条件"""
    ocr_status: Optional[str] = None
    ocr_priority: Optional[int] = None
    page: int = 1
    page_size: int = 20


# ========== 审核任务相关 ==========

class ReviewTaskItem(BaseModel):
    """审核任务项"""
    id: int
    status: str
    source_type: Optional[str] = None
    equipment_type: Optional[str] = None
    brand_name: Optional[str] = None
    product_name: Optional[str] = None
    confidence: float = 0.0
    ocr_text: Optional[str] = None
    extracted_data: Optional[dict] = None
    source_url: Optional[str] = None
    images_count: int = 0
    created_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    review_notes: Optional[str] = None


class ReviewTaskListResponse(BaseModel):
    """审核任务列表响应"""
    items: List[ReviewTaskItem]
    total: int
    page: int
    page_size: int


class ReviewTaskFilters(BaseModel):
    """审核任务筛选条件"""
    status: Optional[str] = None
    source_type: Optional[str] = None
    equipment_type: Optional[str] = None
    page: int = 1
    page_size: int = 20


class ReviewAction(BaseModel):
    """审核操作"""
    action: str = Field(..., description="approve 或 reject")
    review_notes: Optional[str] = None


# ========== 操作响应 ==========

class OperationResponse(BaseModel):
    """通用操作响应"""
    success: bool
    message: str
    affected_count: int = 0
