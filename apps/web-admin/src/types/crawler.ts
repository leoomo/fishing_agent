// 爬虫管理类型定义

export interface CrawlerTask {
  id: number
  task_type: string
  task_name?: string
  status: 'pending' | 'running' | 'success' | 'failed'
  start_time?: string
  end_time?: string
  total_items: number
  success_items: number
  failed_items: number
  error_message?: string
  config?: Record<string, unknown>
  result_summary?: string
  created_at: string
  updated_at: string
}

export interface CrawlerTaskListResponse {
  tasks: CrawlerTask[]
  total: number
  page: number
  page_size: number
}

export interface CrawlerLog {
  id: number
  task_id: number
  level: 'info' | 'warning' | 'error'
  message: string
  details?: string
  created_at: string
}

export interface TriggerCrawlerRequest {
  task_type: string
  keywords?: string[]
  max_pages?: number
  proxy?: string
}

export interface SyncStatus {
  total_tasks: number
  pending_tasks: number
  running_tasks: number
  success_tasks: number
  failed_tasks: number
  last_sync_time?: string
}
