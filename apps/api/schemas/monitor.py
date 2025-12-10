"""
系统监控 Schema
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class APIStatsResponse(BaseModel):
    """API 统计响应"""
    total_calls: int = Field(..., description="总调用次数")
    avg_response_time: float = Field(..., description="平均响应时间（毫秒）")
    error_rate: float = Field(..., description="错误率（%）")
    top_endpoints: List[Dict[str, Any]] = Field(..., description="Top端点列表")


class LLMStatsResponse(BaseModel):
    """LLM 统计响应"""
    total_calls: int = Field(..., description="总调用次数")
    total_tokens: int = Field(..., description="总Token数")
    total_cost: float = Field(..., description="总成本（CNY）")
    avg_response_time: float = Field(..., description="平均响应时间（秒）")
    success_rate: float = Field(..., description="成功率（%）")
    by_provider: Dict[str, Dict] = Field(..., description="按提供商统计")


class DBPerformanceResponse(BaseModel):
    """数据库性能响应"""
    avg_query_time: float = Field(..., description="平均查询时间（毫秒）")
    slow_queries_count: int = Field(..., description="慢查询数量")
    connection_pool_size: int = Field(..., description="连接池大小")
    active_connections: int = Field(..., description="活动连接数")
    table_sizes: Dict[str, int] = Field(..., description="表大小（MB）")


class SystemHealthResponse(BaseModel):
    """系统健康检查响应"""
    status: str = Field(..., description="系统状态（healthy/degraded/unhealthy）")
    api_status: str = Field(..., description="API状态")
    db_status: str = Field(..., description="数据库状态")
    llm_status: str = Field(..., description="LLM服务状态")
    uptime_seconds: float = Field(..., description="运行时间（秒）")


class RealtimeStatsResponse(BaseModel):
    """实时统计响应（用于WebSocket）"""
    timestamp: str = Field(..., description="时间戳")
    api_calls_per_minute: int = Field(..., description="每分钟API调用数")
    api_errors_per_minute: int = Field(..., description="每分钟API错误数")
    llm_calls_per_minute: int = Field(..., description="每分钟LLM调用数")
    llm_tokens_per_minute: int = Field(..., description="每分钟LLM Token消耗")
