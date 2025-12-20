// 系统监控类型定义

export interface APIStats {
  total_requests: number
  avg_response_time: number
  error_rate: number
  requests_by_endpoint: Record<string, number>
  requests_by_status: Record<string, number>
  requests_by_day: Array<{ date: string; count: number }>
}

export interface LLMStats {
  total_calls: number
  total_tokens: number
  total_cost: number
  success_rate: number
  by_provider: Array<{
    provider: string
    calls: number
    tokens: number
    cost: number
    avg_latency: number
  }>
  by_day: Array<{ date: string; calls: number; tokens: number }>
}

export interface DBPerformance {
  avg_query_time: number
  slow_queries: number
  connection_pool_size: number
  active_connections: number
  table_sizes: Array<{ table: string; size_mb: number; row_count: number }>
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  api_status: string
  db_status: string
  llm_status: string
  uptime_seconds: number
}

export interface RealtimeStats {
  api_requests_per_minute: number
  llm_tokens_per_minute: number
  error_rate: number
  active_users: number
}

// ========== Agent 监控类型 ==========

export interface AgentStats {
  agent_type: string
  total_executions: number
  success_rate: number
  avg_latency_ms: number
  total_tokens: number
  total_cost: number
}

export interface AgentStatsResponse {
  agents: AgentStats[]
  total_executions: number
  total_tokens: number
  total_cost: number
}

export interface ToolStats {
  tool_name: string
  category: string
  call_count: number
  success_rate: number
  avg_latency_ms: number
}

export interface ToolStatsResponse {
  tools: ToolStats[]
  by_category: Record<string, number>
}

export interface LatencyPercentiles {
  p50: number
  p90: number
  p99: number
  min: number
  max: number
}

export interface CostReportItem {
  date: string
  agent_type: string
  total_cost: number
  total_tokens: number
  executions: number
}

export interface CostReportResponse {
  items: CostReportItem[]
  total_cost: number
  by_agent: Record<string, number>
}

export interface AgentTrendItem {
  date: string
  executions: number
  tokens: number
  cost: number
  success_rate: number
}

export interface AgentTrendsResponse {
  agent_type: string | null
  trends: AgentTrendItem[]
}
