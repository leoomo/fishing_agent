"""
系统监控 Schema
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class APIStatsResponse(BaseModel):
    """API 统计响应"""
    total_requests: int = Field(..., description="总调用次数")
    avg_response_time: float = Field(..., description="平均响应时间（毫秒）")
    error_rate: float = Field(..., description="错误率（小数）")
    requests_by_endpoint: Dict[str, int] = Field(..., description="按端点统计")
    requests_by_status: Dict[str, int] = Field(..., description="按状态码统计")
    requests_by_day: List[Dict[str, Any]] = Field(..., description="按日期统计")


class LLMStatsResponse(BaseModel):
    """LLM 统计响应"""
    total_calls: int = Field(..., description="总调用次数")
    total_tokens: int = Field(..., description="总Token数")
    total_cost: float = Field(..., description="总成本（CNY）")
    success_rate: float = Field(..., description="成功率（小数）")
    by_provider: List[Dict[str, Any]] = Field(..., description="按提供商统计")
    by_day: List[Dict[str, Any]] = Field(..., description="按日期统计")


class DBPerformanceResponse(BaseModel):
    """数据库性能响应"""
    avg_query_time: float = Field(..., description="平均查询时间（毫秒）")
    slow_queries: int = Field(..., description="慢查询数量")
    connection_pool_size: int = Field(..., description="连接池大小")
    active_connections: int = Field(..., description="活动连接数")
    table_sizes: List[Dict[str, Any]] = Field(..., description="表大小统计")


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


# ========== Agent 监控相关 Schema ==========

class AgentStats(BaseModel):
    """单个 Agent 的统计数据"""
    agent_type: str = Field(..., description="Agent 类型")
    total_executions: int = Field(..., description="总执行次数")
    success_rate: float = Field(..., description="成功率（%）")
    avg_latency_ms: float = Field(..., description="平均延时（毫秒）")
    total_tokens: int = Field(..., description="总 Token 数")
    total_cost: float = Field(..., description="总成本（CNY）")


class AgentStatsResponse(BaseModel):
    """Agent 统计响应"""
    agents: List[AgentStats] = Field(..., description="各 Agent 统计")
    total_executions: int = Field(0, description="所有 Agent 总执行次数")
    total_tokens: int = Field(0, description="所有 Agent 总 Token 数")
    total_cost: float = Field(0, description="所有 Agent 总成本")


class ToolStats(BaseModel):
    """工具统计数据"""
    tool_name: str = Field(..., description="工具名称")
    category: str = Field(..., description="工具类别")
    call_count: int = Field(..., description="调用次数")
    success_rate: float = Field(..., description="成功率（%）")
    avg_latency_ms: float = Field(..., description="平均延时（毫秒）")


class ToolStatsResponse(BaseModel):
    """工具统计响应"""
    tools: List[ToolStats] = Field(..., description="工具统计列表")
    by_category: Dict[str, int] = Field(..., description="按类别统计调用数")


class LatencyPercentilesResponse(BaseModel):
    """延时百分位响应"""
    p50: int = Field(..., description="P50 延时（毫秒）")
    p90: int = Field(..., description="P90 延时（毫秒）")
    p99: int = Field(..., description="P99 延时（毫秒）")
    min: int = Field(..., description="最小延时（毫秒）")
    max: int = Field(..., description="最大延时（毫秒）")


class CostReportItem(BaseModel):
    """成本报表项"""
    date: str = Field(..., description="日期")
    agent_type: str = Field(..., description="Agent 类型")
    total_cost: float = Field(..., description="总成本")
    total_tokens: int = Field(..., description="总 Token 数")
    executions: int = Field(..., description="执行次数")


class CostReportResponse(BaseModel):
    """成本报表响应"""
    items: List[CostReportItem] = Field(..., description="成本报表项列表")
    total_cost: float = Field(..., description="总成本")
    by_agent: Dict[str, float] = Field(..., description="按 Agent 类型的成本")


class AgentTrendItem(BaseModel):
    """Agent 趋势项"""
    date: str = Field(..., description="日期")
    executions: int = Field(..., description="执行次数")
    tokens: int = Field(..., description="Token 数")
    cost: float = Field(..., description="成本")
    success_rate: float = Field(..., description="成功率")


class AgentTrendsResponse(BaseModel):
    """Agent 趋势响应"""
    agent_type: Optional[str] = Field(None, description="Agent 类型（None 表示所有）")
    trends: List[AgentTrendItem] = Field(..., description="趋势数据")
