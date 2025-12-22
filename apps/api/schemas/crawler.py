"""
数据采集管理 Schema
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime


# ========== 数据采集任务 Schema ==========

class CrawlerTaskCreate(BaseModel):
    """创建数据采集任务请求"""
    task_type: str = Field(..., pattern="^(taobao|jd|forum)$", description="任务类型")
    task_name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    config: Optional[Dict[str, Any]] = Field(None, description="任务配置（JSON）")


class CrawlerTaskResponse(BaseModel):
    """数据采集任务响应"""
    task_id: int  # 前端期望 task_id 而不是 id
    task_type: str
    task_name: str
    status: str  # pending, running, success, failed
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_items: int
    success_items: int
    failed_items: int
    error_message: Optional[str] = None
    config: Optional[str] = None  # JSON string
    result_summary: Optional[str] = None  # JSON string
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class CrawlerTaskListResponse(BaseModel):
    """数据采集任务列表响应（分页）"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    tasks: List[CrawlerTaskResponse] = Field(..., description="任务列表")


class CrawlerLogResponse(BaseModel):
    """数据采集日志响应"""
    id: int
    task_id: int
    level: str  # info, warning, error
    message: str
    details: Optional[str] = None  # JSON string
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class TriggerCrawlerRequest(BaseModel):
    """触发数据采集任务请求"""
    task_type: str = Field(..., pattern="^(taobao|jd|pdd|forum)$", description="任务类型")
    keywords: Optional[List[str]] = Field(None, description="搜索关键词列表")
    shop_url: Optional[str] = Field(None, description="店铺URL")
    max_pages: Optional[int] = Field(5, ge=1, le=50, description="最大爬取页数")
    proxy: Optional[str] = Field(None, description="代理服务器")


class SyncStatusResponse(BaseModel):
    """数据同步状态响应"""
    last_sync_time: Optional[str] = None
    total_synced: int = 0
    pending_sync: int = 0
    duplicate_removed: int = 0
    sync_errors: int = 0
    # 任务状态统计（前端概览使用）
    total_tasks: int = 0
    pending_tasks: int = 0
    queued_tasks: int = 0
    running_tasks: int = 0
    success_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0


# ========== 工作流 Schema ==========

class WorkflowStepDefinition(BaseModel):
    """工作流步骤定义"""
    id: str = Field(..., description="步骤唯一标识")
    name: str = Field(..., description="步骤名称")
    task_type: str = Field(..., description="任务类型")
    order: int = Field(..., description="执行顺序", ge=1)
    config: Dict[str, Any] = Field(default_factory=dict, description="任务配置")
    depends_on: List[str] = Field(default_factory=list, description="依赖的步骤ID列表")
    condition: Optional[str] = Field(None, description="执行条件（可选）")

    @field_validator('depends_on')
    @classmethod
    def validate_dependencies(cls, v):
        """验证依赖关系不能循环"""
        # 这里可以添加更复杂的循环依赖检测
        return v


class WorkflowTemplateDefinition(BaseModel):
    """工作流模板定义"""
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    steps: List[WorkflowStepDefinition]

    @field_validator('steps')
    @classmethod
    def validate_steps(cls, v):
        """验证步骤定义"""
        # 允许创建空的模板，后续可以添加步骤
        if not v:
            return v

        # 检查步骤ID唯一性
        step_ids = [step.id for step in v]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("步骤ID必须唯一")

        # 检查顺序唯一性
        orders = [step.order for step in v]
        if len(orders) != len(set(orders)):
            raise ValueError("步骤顺序必须唯一")

        return v


class WorkflowTemplateBase(BaseModel):
    """工作流模板基础模型"""
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(default=None, description="模板描述")
    category: Optional[str] = Field(default="custom", description="模板分类")
    version: str = Field(default="1.0", description="模板版本")
    tags: List[str] = Field(default_factory=list, description="标签列表")


class WorkflowTemplateCreate(WorkflowTemplateBase):
    """创建工作流模板请求"""
    workflow_def: WorkflowTemplateDefinition

    @field_validator('workflow_def')
    @classmethod
    def validate_workflow_consistency(cls, v, info):
        """验证工作流定义与基本信息的一致性"""
        if v.name != info.data.get('name'):
            raise ValueError("工作流定义中的名称必须与模板名称一致")
        if v.version != info.data.get('version'):
            raise ValueError("工作流定义中的版本必须与模板版本一致")
        return v


class WorkflowTemplateUpdate(BaseModel):
    """更新工作流模板请求"""
    name: Optional[str] = Field(None, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    category: Optional[str] = Field(None, description="模板分类")
    version: Optional[str] = Field(None, description="模板版本")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    workflow_def: Optional[WorkflowTemplateDefinition] = Field(None, description="工作流定义")


class WorkflowTemplateResponse(WorkflowTemplateBase):
    """工作流模板响应"""
    id: int
    workflow_def: Dict[str, Any]
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    usage_count: int

    model_config = ConfigDict(from_attributes=True)


class WorkflowExecutionRequest(BaseModel):
    """工作流执行请求"""
    template_id: int = Field(..., description="模板ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="执行参数")
    priority: int = Field(default=0, description="优先级")
    max_retries: int = Field(default=3, description="最大重试次数")
    timeout_seconds: int = Field(default=3600, description="超时时间（秒）")


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    workflow_id: str = Field(..., description="工作流实例ID")
    template_id: int
    status: str
    created_at: datetime
    task_count: int
    completed_count: int
    failed_count: int
    running_count: int
    pending_count: int


class WorkflowTaskStatus(BaseModel):
    """工作流任务状态"""
    task_id: int
    step_id: str
    step_name: str
    status: str
    created_at: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_items: int = 0
    success_items: int = 0
    failed_items: int = 0
    error_message: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    """工作流状态响应"""
    workflow_id: str
    template_name: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tasks: List[WorkflowTaskStatus]
    progress_percentage: float


# ========== 调度 Schema ==========

class ScheduleBase(BaseModel):
    """调度基础模型"""
    name: str = Field(..., description="调度名称")
    template_id: int = Field(..., description="工作流模板ID")
    cron_expression: str = Field(..., description="Cron表达式")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    params: Dict[str, Any] = Field(default_factory=dict, description="执行参数")
    is_enabled: bool = Field(default=True, description="是否启用")
    max_instances: int = Field(default=1, description="最大并发实例数")
    timeout_seconds: int = Field(default=3600, description="超时时间（秒）")


class ScheduleCreate(ScheduleBase):
    """创建调度请求"""
    description: Optional[str] = Field(None, description="调度描述")

    @field_validator('cron_expression')
    @classmethod
    def validate_cron(cls, v):
        """验证Cron表达式"""
        # 简单验证，实际使用时可以用croniter验证
        parts = v.split()
        if len(parts) != 5:
            raise ValueError("Cron表达式必须包含5个字段: 分 时 日 月 周")
        return v


class ScheduleUpdate(BaseModel):
    """更新调度请求"""
    name: Optional[str] = Field(None, description="调度名称")
    description: Optional[str] = Field(None, description="调度描述")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    timezone: Optional[str] = Field(None, description="时区")
    params: Optional[Dict[str, Any]] = Field(None, description="执行参数")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    max_instances: Optional[int] = Field(None, description="最大并发实例数")
    timeout_seconds: Optional[int] = Field(None, description="超时时间")


class ScheduleResponse(ScheduleBase):
    """调度响应"""
    id: int
    description: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int
    success_count: int
    failure_count: int

    model_config = ConfigDict(from_attributes=True)


class ScheduleJobStatus(BaseModel):
    """调度任务状态"""
    job_id: str
    schedule_name: str
    workflow_id: Optional[str] = None
    status: str  # running, completed, failed, paused
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    next_run_time: Optional[datetime] = None
    execution_count: int
    misfire_grace_time: int


class SchedulePreviewRequest(BaseModel):
    """调度预览请求"""
    cron_expression: str = Field(..., description="Cron表达式")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class SchedulePreviewResponse(BaseModel):
    """调度预览响应"""
    cron_expression: str
    timezone: str
    next_runs: List[datetime]
    total_count: int
    preview_range: Dict[str, datetime]


class CronExpressionRequest(BaseModel):
    """生成Cron表达式请求"""
    frequency: str = Field(..., description="频率类型", pattern="^(minutely|hourly|daily|weekly|monthly|yearly|custom)$")
    interval: int = Field(default=1, description="间隔", ge=1)
    specific_times: List[str] = Field(default_factory=list, description="特定时间点")
    days_of_month: List[int] = Field(default_factory=list, description="月份中的日期")
    days_of_week: List[str] = Field(default_factory=list, description="星期中的日期")
    months: List[str] = Field(default_factory=list, description="月份")
    timezone: str = Field(default="Asia/Shanghai", description="时区")


class CronExpressionResponse(BaseModel):
    """生成Cron表达式响应"""
    cron_expression: str
    description: str
    next_runs: List[datetime]
    timezone: str


# ========== 通用响应 Schema ==========

class ApiResponse(BaseModel):
    """API响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None
    errors: Optional[List[str]] = None


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
