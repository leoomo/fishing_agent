"""
爬虫管理 Schema
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ========== 爬虫任务 Schema ==========

class CrawlerTaskCreate(BaseModel):
    """创建爬虫任务请求"""
    task_type: str = Field(..., pattern="^(taobao|jd|forum)$", description="任务类型")
    task_name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    config: Optional[Dict[str, Any]] = Field(None, description="任务配置（JSON）")


class CrawlerTaskResponse(BaseModel):
    """爬虫任务响应"""
    id: int
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
    """爬虫任务列表响应（分页）"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    tasks: List[CrawlerTaskResponse] = Field(..., description="任务列表")


class CrawlerLogResponse(BaseModel):
    """爬虫日志响应"""
    id: int
    task_id: int
    level: str  # info, warning, error
    message: str
    details: Optional[str] = None  # JSON string
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class TriggerCrawlerRequest(BaseModel):
    """触发爬虫任务请求"""
    task_type: str = Field(..., pattern="^(taobao|jd|forum)$", description="任务类型")
    keywords: Optional[List[str]] = Field(None, description="搜索关键词列表")
    max_pages: Optional[int] = Field(5, ge=1, le=50, description="最大爬取页数")
    proxy: Optional[str] = Field(None, description="代理服务器")


class SyncStatusResponse(BaseModel):
    """数据同步状态响应"""
    last_sync_time: Optional[str] = None
    total_synced: int
    pending_sync: int
    duplicate_removed: int
    sync_errors: int
