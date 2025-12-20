"""
Node-related Pydantic schemas

节点相关的请求/响应模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ========== 节点注册 ==========

class NodeRegisterRequest(BaseModel):
    """节点注册请求"""
    node_name: str = Field(..., min_length=1, max_length=200, description="节点名称")
    capabilities: List[str] = Field(default=["all"], description="能力标签列表")
    max_concurrent_tasks: int = Field(default=1, ge=1, le=10, description="最大并发任务数")
    worker_version: str = Field(default="1.0.0", description="Worker版本号")
    location: Optional[str] = Field(default=None, max_length=100, description="地理位置")


class NodeRegisterResponse(BaseModel):
    """节点注册响应"""
    node_id: str = Field(..., description="系统分配的节点ID (UUID)")
    node_secret: str = Field(..., description="节点密钥（仅返回一次，请妥善保存）")
    token: str = Field(..., description="初始访问Token")
    expires_at: datetime = Field(..., description="Token过期时间")
    heartbeat_interval: int = Field(default=30, description="心跳间隔（秒）")


# ========== 节点认证 ==========

class NodeAuthRequest(BaseModel):
    """节点认证请求"""
    node_id: str = Field(..., description="节点ID")
    node_secret: str = Field(..., description="节点密钥")


class NodeAuthResponse(BaseModel):
    """节点认证响应"""
    token: str = Field(..., description="访问Token")
    expires_at: datetime = Field(..., description="Token过期时间")
    heartbeat_interval: int = Field(default=30, description="心跳间隔（秒）")


# ========== 心跳 ==========

class HeartbeatRequest(BaseModel):
    """心跳请求"""
    current_tasks: int = Field(default=0, ge=0, description="当前运行任务数")
    running_task_ids: List[int] = Field(default=[], description="正在运行的任务ID列表")
    cpu_usage: Optional[float] = Field(default=None, ge=0, le=100, description="CPU使用率")
    memory_usage: Optional[float] = Field(default=None, ge=0, le=100, description="内存使用率")
    disk_usage: Optional[float] = Field(default=None, ge=0, le=100, description="磁盘使用率")
    worker_version: Optional[str] = Field(default=None, description="Worker版本号")


class HeartbeatResponse(BaseModel):
    """心跳响应"""
    status: str = Field(..., description="状态: ok/drain/shutdown")
    next_heartbeat_seconds: int = Field(default=30, description="下次心跳时间（秒）")
    assigned_tasks: List[int] = Field(default=[], description="新分配的任务ID列表")
    cancel_tasks: List[int] = Field(default=[], description="需要取消的任务ID列表")
    message: Optional[str] = Field(default=None, description="附加消息")


# ========== 节点信息 ==========

class NodeInfo(BaseModel):
    """节点信息"""
    id: int
    node_id: str
    node_name: str
    status: str
    ip_address: Optional[str] = None
    location: Optional[str] = None
    capabilities: List[str] = []
    max_concurrent_tasks: int = 1
    current_tasks: int = 0
    total_completed: int = 0
    total_failed: int = 0
    success_rate: float = 100.0
    avg_task_duration: float = 0.0
    worker_version: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NodeListResponse(BaseModel):
    """节点列表响应"""
    total: int = Field(..., description="总数")
    nodes: List[NodeInfo] = Field(default=[], description="节点列表")


class NodeUpdateRequest(BaseModel):
    """节点更新请求"""
    node_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    capabilities: Optional[List[str]] = None
    max_concurrent_tasks: Optional[int] = Field(default=None, ge=1, le=10)
    location: Optional[str] = Field(default=None, max_length=100)
    tags: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


# ========== 任务相关 ==========

class TaskClaimRequest(BaseModel):
    """任务认领请求"""
    task_id: int = Field(..., description="任务ID")


class TaskProgressRequest(BaseModel):
    """任务进度上报请求"""
    progress: int = Field(..., ge=0, le=100, description="进度百分比")
    message: Optional[str] = Field(default=None, description="进度消息")
    current_items: Optional[int] = Field(default=None, description="当前处理项数")
    total_items: Optional[int] = Field(default=None, description="总项数")


class TaskCompleteRequest(BaseModel):
    """任务完成请求"""
    success_items: int = Field(default=0, ge=0, description="成功项数")
    failed_items: int = Field(default=0, ge=0, description="失败项数")
    total_items: int = Field(default=0, ge=0, description="总项数")
    duplicate_items: int = Field(default=0, ge=0, description="去重项数")
    result_summary: Optional[Dict[str, Any]] = Field(default=None, description="结果摘要")
    result_data: Optional[List[Dict[str, Any]]] = Field(default=None, description="结果数据")
    image_stats: Optional[Dict[str, int]] = Field(default=None, description="图片处理统计")


class TaskFailRequest(BaseModel):
    """任务失败请求"""
    error_message: str = Field(..., description="错误消息")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    should_retry: bool = Field(default=True, description="是否应该重试")


# ========== 图片上传 ==========

class ImageUploadResponse(BaseModel):
    """图片上传响应"""
    image_id: Optional[int] = Field(default=None, description="图片ID")
    local_url: Optional[str] = Field(default=None, description="本地存储URL")
    status: str = Field(..., description="状态: saved/duplicate/error")
    message: Optional[str] = Field(default=None, description="消息")


class ImageBatchUploadResponse(BaseModel):
    """批量图片上传响应"""
    total: int = Field(..., description="总数")
    saved: int = Field(default=0, description="保存成功数")
    duplicates: int = Field(default=0, description="重复数")
    errors: int = Field(default=0, description="错误数")
    images: List[ImageUploadResponse] = Field(default=[], description="各图片处理结果")


# ========== 任务信息 ==========

class TaskInfo(BaseModel):
    """任务信息"""
    id: int
    task_type: str
    platform: Optional[str] = None
    shop_url: Optional[str] = None
    status: str
    priority: int = 0
    progress: int = 0
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_count: int = 0
    config: Optional[Dict[str, Any]] = None
    assigned_node_id: Optional[int] = None
    assigned_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应"""
    total: int = Field(..., description="总数")
    tasks: List[TaskInfo] = Field(default=[], description="任务列表")
