// 爬虫管理类型定义

export interface CrawlerTask {
  task_id: number
  task_type: string
  task_name?: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | 'paused'
  start_time?: string
  end_time?: string
  duration?: number
  total_items: number
  success_items: number
  failed_items: number
  error_message?: string
  config?: Record<string, unknown>
  result_summary?: string
  created_at: string
  updated_at: string
  platform: string
  platform_name?: string
  priority?: 'high' | 'medium' | 'low'
  tags?: string[]
  retry_count?: number
  max_retries?: number
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
  task_name?: string
  task_type: string
  platform: string
  priority?: 'high' | 'medium' | 'low'
  description?: string
  target_url?: string
  config?: Record<string, unknown>
  max_pages?: number
  delay_range?: [number, number]
  retry_count?: number
  timeout?: number
  extract_images?: boolean
  use_proxy?: boolean
  random_ua?: boolean
}

// 筛选器类型
export interface TaskFilters {
  keyword?: string
  status?: string
  task_type?: string
  platform?: string
  priority?: string
  date_range?: [string, string]
  tags?: string[]
}

// 分页状态
export interface PaginationState {
  current: number
  pageSize: number
  total: number
}

// 统计数据
export interface TaskStats {
  total_tasks: number
  pending_tasks: number
  running_tasks: number
  success_tasks: number
  failed_tasks: number
  cancelled_tasks: number
  paused_tasks: number
  last_sync_time?: string
}

export interface SyncStatus {
  total_tasks: number
  pending_tasks: number
  running_tasks: number
  success_tasks: number
  failed_tasks: number
  last_sync_time?: string
}

// 任务模板
export interface TaskTemplate {
  id: number
  name: string
  description?: string
  task_type: string
  platform: string
  config: Record<string, unknown>
  is_public: boolean
  created_by: string
  created_at: string
  updated_at: string
  usage_count: number
}

// 工作流相关
export interface Workflow {
  id: number
  name: string
  description?: string
  steps: WorkflowStep[]
  config?: Record<string, unknown>
  created_by: string
  created_at: string
  updated_at: string
}

export interface WorkflowStep {
  id: number
  workflow_id: number
  step_type: string
  name: string
  config: Record<string, unknown>
  order_index: number
  dependencies?: number[]
}

export interface WorkflowExecution {
  id: number
  workflow_id: number
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  start_time?: string
  end_time?: string
  current_step_id?: number
  context?: Record<string, unknown>
  error_message?: string
  created_by: string
  created_at: string
  updated_at: string
}

// 调度任务
export interface ScheduleJob {
  id: number
  name: string
  task_id?: number
  workflow_id?: number
  cron_expression: string
  enabled: boolean
  next_run_time?: string
  last_run_time?: string
  timezone: string
  config?: Record<string, unknown>
  created_at: string
  updated_at: string
}
