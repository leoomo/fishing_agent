import client from '../client'
import type {
  APIStats,
  LLMStats,
  DBPerformance,
  SystemHealth,
  AgentStatsResponse,
  ToolStatsResponse,
  LatencyPercentiles,
  CostReportResponse,
  AgentTrendsResponse
} from '@/types/monitor'

export const monitorApi = {
  // API 调用统计
  getApiStats: (params?: {
    start_date?: string
    end_date?: string
  }): Promise<APIStats> => {
    return client.get('/admin/monitor/api-stats', { params })
  },

  // LLM 使用统计
  getLlmStats: (params?: {
    start_date?: string
    end_date?: string
  }): Promise<LLMStats> => {
    return client.get('/admin/monitor/llm-stats', { params })
  },

  // 数据库性能
  getDbPerformance: (): Promise<DBPerformance> => {
    return client.get('/admin/monitor/db-performance')
  },

  // 系统健康检查
  getHealthCheck: (): Promise<SystemHealth> => {
    return client.get('/admin/monitor/health-check')
  },

  // ========== Agent 监控 ==========

  // Agent 执行统计
  getAgentStats: (params?: {
    agent_type?: string
    start_date?: string
    end_date?: string
  }): Promise<AgentStatsResponse> => {
    return client.get('/admin/monitor/agent-stats', { params })
  },

  // 工具使用统计
  getToolStats: (params?: {
    start_date?: string
    end_date?: string
  }): Promise<ToolStatsResponse> => {
    return client.get('/admin/monitor/tool-stats', { params })
  },

  // 延时百分位
  getLatencyPercentiles: (params?: {
    agent_type?: string
    start_date?: string
  }): Promise<LatencyPercentiles> => {
    return client.get('/admin/monitor/latency-percentiles', { params })
  },

  // 成本报表
  getCostReport: (params?: {
    start_date?: string
    end_date?: string
    group_by?: 'day' | 'week' | 'month'
  }): Promise<CostReportResponse> => {
    return client.get('/admin/monitor/cost-report', { params })
  },

  // Agent 趋势
  getAgentTrends: (params?: {
    agent_type?: string
    days?: number
  }): Promise<AgentTrendsResponse> => {
    return client.get('/admin/monitor/agent-trends', { params })
  },
}
