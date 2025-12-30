"""
数据处理工作流 Schema 定义
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
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

class ReviewHistoryItem(BaseModel):
    """审核历史记录项"""
    reviewed_by: int = Field(..., description="审核人 ID")
    reviewed_at: str = Field(..., description="审核时间 (ISO 格式)")
    action: str = Field(..., description="操作: approve 或 reject")
    review_notes: Optional[str] = Field(None, description="审核备注")
    previous_status: str = Field(..., description="操作前的状态")


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
    extracted_data: Any = None  # 可以是 dict 或 List[dict]
    source_url: Optional[str] = None
    images_count: int = 0
    created_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    review_notes: Optional[str] = None
    review_history: Optional[List[ReviewHistoryItem]] = None  # 审核历史


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


# ========== 装备提取相关 ==========

class ExtractedEquipmentItem(BaseModel):
    """提取的装备项"""
    equipment_type: str = ""
    brand_name: Optional[str] = None
    model: Optional[str] = None
    name: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    description: Optional[str] = None
    features: List[str] = []
    target_fish: List[str] = []
    user_level: Optional[str] = None
    specs: dict = {}
    confidence: float = 0.0
    extraction_notes: str = ""


class ExtractResponse(BaseModel):
    """装备提取响应"""
    success: bool
    message: str
    extracted_count: int = 0
    items: List[ExtractedEquipmentItem] = []


class ExtractedDataUpdate(BaseModel):
    """更新提取数据的请求"""
    items: List[ExtractedEquipmentItem] = Field(..., description="编辑后的装备列表")


# ========== 图片相关 ==========

class ImageInfo(BaseModel):
    """图片信息"""
    filename: str = Field(..., description="文件名")
    url: str = Field(..., description="图片访问 URL")
    order: int = Field(default=0, description="排序顺序")
    original_name: Optional[str] = Field(None, description="原始文件名")


class TaskImagesResponse(BaseModel):
    """任务图片列表响应"""
    task_id: int
    images: List[ImageInfo] = []
    total: int = 0


# ========== WebSocket 实时更新相关 ==========

class OCRProgressReport(BaseModel):
    """OCR 处理进度上报"""
    pending_id: int = Field(..., description="任务 ID")
    stage: str = Field(
        ...,
        description="处理阶段: downloading, merging, ocr_processing, extracting"
    )
    progress: int = Field(..., ge=0, le=100, description="进度百分比 (0-100)")
    message: Optional[str] = Field(None, description="进度描述")
    current_image: Optional[int] = Field(None, description="当前处理的图片索引")
    total_images: Optional[int] = Field(None, description="总图片数")


class WorkerLogSubmit(BaseModel):
    """Worker 日志提交"""
    level: str = Field(
        default="info",
        description="日志级别: debug, info, warning, error"
    )
    message: str = Field(..., description="日志内容")
    pending_id: Optional[int] = Field(None, description="关联的任务 ID")


class WorkflowWSEvent(BaseModel):
    """WebSocket 事件"""
    type: str = Field(
        ...,
        description="事件类型: init, stats_update, worker_update, task_claimed, "
                    "ocr_started, ocr_progress, ocr_completed, ocr_failed, "
                    "review_update, worker_log"
    )
    data: Any = Field(None, description="事件数据")
    pending_id: Optional[int] = Field(None, description="关联的任务 ID")
    timestamp: str = Field(..., description="事件时间戳 (ISO 格式)")


# ========== Excel 导入相关 ==========

class ImportPreviewRow(BaseModel):
    """导入预览行"""
    row_number: int = Field(..., description="行号")
    data: dict = Field(..., description="行数据")
    is_valid: bool = Field(..., description="是否有效")
    errors: List[str] = Field(default_factory=list, description="验证错误列表")


class ImportPreviewResponse(BaseModel):
    """导入预览响应"""
    success: bool
    message: str
    equipment_type: str = Field(..., description="装备类型")
    total_rows: int = Field(default=0, description="总行数")
    valid_rows: int = Field(default=0, description="有效行数")
    invalid_rows: int = Field(default=0, description="无效行数")
    preview_data: List[ImportPreviewRow] = Field(default_factory=list)


class ImportError(BaseModel):
    """导入错误"""
    row: int = Field(..., description="行号")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    data: dict = Field(default_factory=dict, description="行数据")


class ImportResponse(BaseModel):
    """导入响应"""
    success: bool
    message: str
    total_rows: int = Field(default=0, description="总行数")
    imported_count: int = Field(default=0, description="成功导入数量")
    failed_count: int = Field(default=0, description="失败数量")
    pending_ids: List[int] = Field(default_factory=list, description="创建的待审核记录 ID")
    errors: List[ImportError] = Field(default_factory=list, description="错误详情")


class ImportTemplateInfo(BaseModel):
    """导入模板信息"""
    equipment_type: str = Field(..., description="装备类型 key")
    equipment_type_label: str = Field(..., description="装备类型名称")
    download_url: str = Field(..., description="模板下载 URL")


class ImportTemplateListResponse(BaseModel):
    """导入模板列表响应"""
    templates: List[ImportTemplateInfo] = Field(default_factory=list)
