import client from '../client'
import type {
  CrawlerTask,
  CrawlerTaskListResponse,
  CrawlerLog,
  TriggerCrawlerRequest,
  SyncStatus,
} from '@/types/crawler'

// 登录相关类型定义
export interface LoginStartResponse {
  qr_code: string
  expires_at: number
  task_id: number
  platform: string
}

export interface LoginRefreshResponse {
  qr_code: string
  expires_at: number
}

export interface LoginStatusResponse {
  status: string
  qr_code?: string
  expires_at?: number
  user_info?: any
  error_message?: string
}

export const crawlerApi = {
  // 查询爬虫任务列表
  listTasks: (params: {
    page: number
    page_size: number
    task_type?: string
    status?: string
    platform?: string
    date_range?: [string, string]
  }): Promise<CrawlerTaskListResponse> => {
    return client.get('/admin/crawler/tasks', { params })
  },

  // 获取任务详情
  getTask: (taskId: number): Promise<CrawlerTask> => {
    return client.get(`/admin/crawler/tasks/${taskId}`)
  },

  // 更新任务
  updateTask: (taskId: number, taskData: Partial<CrawlerTask>): Promise<CrawlerTask> => {
    return client.put(`/admin/crawler/tasks/${taskId}`, taskData)
  },

  // 触发爬虫任务
  triggerCrawler: (data: TriggerCrawlerRequest): Promise<CrawlerTask> => {
    return client.post('/admin/crawler/tasks/trigger', data)
  },

  // 重试失败任务
  retryTask: (taskId: number): Promise<CrawlerTask> => {
    return client.post(`/admin/crawler/tasks/${taskId}/retry`)
  },

  // 获取任务日志
  getTaskLogs: (taskId: number, level?: string): Promise<CrawlerLog[]> => {
    return client.get(`/admin/crawler/tasks/${taskId}/logs`, {
      params: level ? { level } : {},
    })
  },

  // 删除任务
  deleteTask: (taskId: number): Promise<void> => {
    return client.delete(`/admin/crawler/tasks/${taskId}`)
  },

  // 批量删除任务
  bulkDeleteTasks: (taskIds: number[]): Promise<void> => {
    return client.post('/admin/crawler/tasks/bulk-delete', { task_ids: taskIds })
  },

  // 获取同步状态
  getSyncStatus: (): Promise<SyncStatus> => {
    return client.get('/admin/crawler/sync-status')
  },

  // ========== 登录相关API ==========

  // 开始登录流程
  startLogin: (taskId: number): Promise<LoginStartResponse> => {
    return client.post(`/admin/crawler/login/start`, { task_id: taskId })
  },

  // 刷新二维码
  refreshQRCode: (taskId: number): Promise<LoginRefreshResponse> => {
    return client.post(`/admin/crawler/login/refresh-qr`, { task_id: taskId })
  },

  // 获取登录状态
  getLoginStatus: (taskId: number): Promise<LoginStatusResponse> => {
    return client.get(`/admin/crawler/login/status/${taskId}`)
  },

  // 获取二维码图片
  getQRCode: (taskId: number): Promise<string> => {
    return client.get(`/admin/crawler/login/qr/${taskId}`, {
      responseType: 'blob'
    }).then(response => {
      return URL.createObjectURL(response.data)
    })
  },

  // 取消登录流程
  cancelLogin: (taskId: number): Promise<void> => {
    return client.post(`/admin/crawler/login/cancel`, { task_id: taskId })
  },

  // ========== 工作流相关API ==========

  // 获取工作流模板列表
  getWorkflowTemplates: (): Promise<any[]> => {
    return client.get('/admin/workflows/templates')
  },

  // 创建工作流
  createWorkflow: (workflowData: any): Promise<any> => {
    return client.post('/admin/workflows', workflowData)
  },

  // 执行工作流
  executeWorkflow: (workflowId: number, params?: any): Promise<any> => {
    return client.post(`/admin/workflows/${workflowId}/execute`, params)
  },

  // 获取工作流执行状态
  getWorkflowExecution: (executionId: number): Promise<any> => {
    return client.get(`/admin/workflows/executions/${executionId}`)
  },

  // ========== 调度相关API ==========

  // 获取调度任务列表
  getSchedules: (): Promise<any[]> => {
    return client.get('/admin/scheduler/jobs')
  },

  // 创建调度任务
  createSchedule: (scheduleData: any): Promise<any> => {
    return client.post('/admin/scheduler/jobs', scheduleData)
  },

  // 更新调度任务
  updateSchedule: (jobId: number, scheduleData: any): Promise<any> => {
    return client.put(`/admin/scheduler/jobs/${jobId}`, scheduleData)
  },

  // 删除调度任务
  deleteSchedule: (jobId: number): Promise<void> => {
    return client.delete(`/admin/scheduler/jobs/${jobId}`)
  },

  // 暂停调度任务
  pauseSchedule: (jobId: number): Promise<void> => {
    return client.post(`/admin/scheduler/jobs/${jobId}/pause`)
  },

  // 恢复调度任务
  resumeSchedule: (jobId: number): Promise<void> => {
    return client.post(`/admin/scheduler/jobs/${jobId}/resume`)
  },

  // ========== 任务模板相关API ==========

  // 获取任务模板列表
  getTaskTemplates: (): Promise<any[]> => {
    return client.get('/admin/crawler/templates')
  },

  // 创建任务模板
  createTaskTemplate: (templateData: any): Promise<any> => {
    return client.post('/admin/crawler/templates', templateData)
  },

  // 应用任务模板
  applyTaskTemplate: (templateId: number): Promise<any> => {
    return client.post(`/admin/crawler/templates/${templateId}/apply`)
  },

  // ========== 数据导出API ==========

  // 导出任务数据
  exportTasks: (params: {
    format: 'csv' | 'excel'
    task_ids?: number[]
    filters?: any
  }): Promise<Blob> => {
    return client.get('/admin/crawler/export', {
      params,
      responseType: 'blob'
    })
  },
}
