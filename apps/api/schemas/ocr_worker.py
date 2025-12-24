"""
OCR Worker API 请求/响应模型
"""

from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field


# ========== Worker 注册 ==========

class OCRWorkerRegister(BaseModel):
    """Worker 注册请求"""
    worker_id: str = Field(..., description="Worker 唯一标识")
    worker_name: Optional[str] = Field(None, description="Worker 名称")
    ocr_provider: str = Field(default="ollama", description="OCR 提供商: ollama/siliconflow")
    max_concurrent: int = Field(default=1, description="最大并发任务数")


class OCRWorkerRegisterResponse(BaseModel):
    """Worker 注册响应"""
    success: bool
    worker_id: str
    token: str = Field(..., description="认证 Token，格式: worker_id:secret")
    message: str = ""


# ========== 任务领取 ==========

class OCRTaskClaimRequest(BaseModel):
    """领取任务请求"""
    worker_id: str = Field(..., description="Worker ID")
    max_tasks: int = Field(default=1, ge=1, le=10, description="最多领取任务数")


class OCRTaskInfo(BaseModel):
    """OCR 任务信息"""
    pending_id: int = Field(..., description="待审装备 ID")
    images: List[str] = Field(default_factory=list, description="图片路径列表")
    brand_name: Optional[str] = None
    product_name: Optional[str] = None
    source_url: Optional[str] = None


class OCRTaskClaimResponse(BaseModel):
    """领取任务响应"""
    success: bool
    tasks: List[OCRTaskInfo] = Field(default_factory=list)
    message: str = ""


# ========== 结果汇报 ==========

class OCRTaskReport(BaseModel):
    """OCR 结果汇报"""
    pending_id: int = Field(..., description="待审装备 ID")
    worker_id: str = Field(..., description="Worker ID")
    status: Literal["success", "failed"] = Field(..., description="处理状态")
    ocr_text: Optional[str] = Field(None, description="OCR 识别的文本（Markdown 格式）")
    error_message: Optional[str] = Field(None, description="错误信息")
    processing_time_ms: int = Field(..., description="处理耗时（毫秒）")
    provider: str = Field(..., description="使用的 OCR 提供商")


class OCRTaskReportResponse(BaseModel):
    """汇报响应"""
    success: bool
    message: str = ""


# ========== 心跳 ==========

class OCRHeartbeatRequest(BaseModel):
    """心跳请求"""
    worker_id: str
    current_tasks: List[int] = Field(default_factory=list, description="当前处理中的任务 ID")
    cpu_usage: Optional[float] = Field(None, description="CPU 使用率")
    memory_usage: Optional[float] = Field(None, description="内存使用率")


class OCRHeartbeatResponse(BaseModel):
    """心跳响应"""
    success: bool
    server_time: str
    commands: List[dict] = Field(default_factory=list, description="下发的命令")


# ========== 统计和查询 ==========

class OCRStats(BaseModel):
    """OCR 任务统计"""
    total: int = Field(0, description="总任务数")
    pending: int = Field(0, description="待处理")
    processing: int = Field(0, description="处理中")
    completed: int = Field(0, description="已完成")
    failed: int = Field(0, description="失败")
    skipped: int = Field(0, description="跳过（无图片）")


class OCRTaskItem(BaseModel):
    """OCR 任务列表项"""
    pending_id: int
    brand_name: Optional[str] = None
    product_name: Optional[str] = None
    ocr_status: str
    ocr_worker_id: Optional[str] = None
    ocr_started_at: Optional[datetime] = None
    ocr_completed_at: Optional[datetime] = None
    ocr_processing_time_ms: Optional[int] = None
    ocr_provider: Optional[str] = None
    ocr_retry_count: int = 0
    ocr_error_message: Optional[str] = None
    ocr_priority: int = 0
    images_count: int = 0
    created_at: Optional[datetime] = None


class OCRTaskListResponse(BaseModel):
    """任务列表响应"""
    success: bool
    tasks: List[OCRTaskItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20


# ========== 管理员操作 ==========

class OCRTaskRetryResponse(BaseModel):
    """重试任务响应"""
    success: bool
    message: str
    pending_id: int
    previous_status: str


class OCRTaskBatchRetryRequest(BaseModel):
    """批量重试请求"""
    pending_ids: Optional[List[int]] = Field(None, description="指定任务ID列表，不指定则重试所有失败任务")
    ocr_status: Optional[Literal["failed", "skipped", "processing"]] = Field(
        default="failed",
        description="筛选要重试的任务状态"
    )


class OCRTaskBatchRetryResponse(BaseModel):
    """批量重试响应"""
    success: bool
    message: str
    retried_count: int
    skipped_count: int
    pending_ids: List[int] = Field(default_factory=list)


class OCRTaskSkipResponse(BaseModel):
    """跳过任务响应"""
    success: bool
    message: str
    pending_id: int


class OCRTaskSetPriorityRequest(BaseModel):
    """设置优先级请求"""
    priority: int = Field(..., ge=0, le=10, description="优先级: 0=默认, 1=低, 5=高, 10=紧急")


class OCRTaskSetPriorityResponse(BaseModel):
    """设置优先级响应"""
    success: bool
    message: str
    pending_id: int
    old_priority: int
    new_priority: int


class OCRTaskDeleteResponse(BaseModel):
    """删除任务响应"""
    success: bool
    message: str
    pending_id: int
