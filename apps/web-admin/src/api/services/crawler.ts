import client from '../client'
import type {
  CrawlerTask,
  CrawlerTaskListResponse,
  CrawlerLog,
  TriggerCrawlerRequest,
  SyncStatus,
} from '@/types/crawler'

export const crawlerApi = {
  // 查询爬虫任务列表
  listTasks: (params: {
    page: number
    page_size: number
    task_type?: string
    status?: string
  }): Promise<CrawlerTaskListResponse> => {
    return client.get('/admin/crawler/tasks', { params })
  },

  // 获取任务详情
  getTask: (taskId: number): Promise<CrawlerTask> => {
    return client.get(`/admin/crawler/tasks/${taskId}`)
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

  // 获取同步状态
  getSyncStatus: (): Promise<SyncStatus> => {
    return client.get('/admin/crawler/sync-status')
  },
}
