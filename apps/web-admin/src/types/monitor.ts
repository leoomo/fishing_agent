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
