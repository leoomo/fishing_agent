import client from '../client'
import type { APIStats, LLMStats, DBPerformance, SystemHealth } from '@/types/monitor'

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
}
