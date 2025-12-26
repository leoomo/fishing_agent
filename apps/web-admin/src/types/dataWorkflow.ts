/**
 * 数据处理工作流类型定义
 */

// ========== 工作流统计 ==========

export interface WorkflowStats {
  // 爬虫阶段
  crawl_pending: number

  // OCR 阶段
  ocr_pending: number
  ocr_processing: number
  ocr_completed: number
  ocr_failed: number
  ocr_skipped: number

  // 审核阶段
  review_pending: number
  review_approved: number
  review_rejected: number

  // 统计指标
  today_processed: number
  avg_processing_time_ms: number
  success_rate: number
}

// ========== Worker 相关 ==========

export interface WorkerInfo {
  id: string
  status: 'active' | 'inactive'
  current_task: number | null
  last_heartbeat: string | null
  ocr_provider: string | null
  tasks_completed: number
}

export interface WorkerListResponse {
  workers: WorkerInfo[]
  total_active: number
}

// ========== OCR 任务 ==========

export interface OCRTaskItem {
  pending_id: number
  brand_name: string | null
  product_name: string | null
  images_count: number
  ocr_status: OCRStatus
  ocr_priority: number
  ocr_worker_id: string | null
  ocr_started_at: string | null
  ocr_processing_time_ms: number | null
  ocr_retry_count: number
  ocr_error_message: string | null
  ocr_provider: string | null
  created_at: string | null
}

export type OCRStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'skipped'

export interface OCRTaskListResponse {
  items: OCRTaskItem[]
  total: number
  page: number
  page_size: number
}

export interface OCRTaskFilters {
  ocr_status?: OCRStatus
  ocr_priority?: number
  page?: number
  page_size?: number
}

// 优先级选项
export const OCR_PRIORITY_OPTIONS = [
  { value: 10, label: '紧急', color: 'red' },
  { value: 5, label: '高', color: 'orange' },
  { value: 0, label: '默认', color: 'default' },
  { value: -5, label: '低', color: 'default' },
]

// ========== 审核任务 ==========

export interface ReviewTaskItem {
  id: number
  status: ReviewStatus
  source_type: string | null
  equipment_type: string | null
  brand_name: string | null
  product_name: string | null
  confidence: number
  ocr_text: string | null
  extracted_data: Record<string, unknown> | null
  source_url: string | null
  images_count: number
  created_at: string | null
  reviewed_at: string | null
  reviewed_by: number | null
  review_notes: string | null
}

export type ReviewStatus = 'pending' | 'approved' | 'rejected'

export interface ReviewTaskListResponse {
  items: ReviewTaskItem[]
  total: number
  page: number
  page_size: number
}

export interface ReviewTaskFilters {
  status?: ReviewStatus
  source_type?: string
  equipment_type?: string
  page?: number
  page_size?: number
}

export interface ReviewAction {
  action: 'approve' | 'reject'
  review_notes?: string
}

// ========== 通用响应 ==========

export interface OperationResponse {
  success: boolean
  message: string
  affected_count: number
}

// ========== 工作流阶段配置 ==========

export interface WorkflowStage {
  key: string
  title: string
  countKey: keyof WorkflowStats
  subCountKey?: keyof WorkflowStats
  color: string
  icon: string
}

export const WORKFLOW_STAGES: WorkflowStage[] = [
  {
    key: 'crawl',
    title: '采集队列',
    countKey: 'crawl_pending',
    color: '#1890ff',
    icon: 'RobotOutlined',
  },
  {
    key: 'ocr',
    title: 'OCR识别',
    countKey: 'ocr_pending',
    subCountKey: 'ocr_processing',
    color: '#722ed1',
    icon: 'ScanOutlined',
  },
  {
    key: 'extract',
    title: '数据提取',
    countKey: 'ocr_completed',
    color: '#13c2c2',
    icon: 'FileSearchOutlined',
  },
  {
    key: 'review',
    title: '人工审核',
    countKey: 'review_pending',
    color: '#faad14',
    icon: 'AuditOutlined',
  },
  {
    key: 'done',
    title: '已入库',
    countKey: 'review_approved',
    color: '#52c41a',
    icon: 'CheckCircleOutlined',
  },
]

// ========== Tab 配置 ==========

export type WorkflowTab = 'ocr' | 'review' | 'completed'

// ========== 状态映射 ==========

export const OCR_STATUS_CONFIG: Record<OCRStatus, { color: string; text: string }> = {
  pending: { color: 'default', text: '待处理' },
  processing: { color: 'processing', text: '处理中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
  skipped: { color: 'warning', text: '跳过' },
}

export const REVIEW_STATUS_CONFIG: Record<ReviewStatus, { color: string; text: string }> = {
  pending: { color: 'processing', text: '待审核' },
  approved: { color: 'success', text: '已通过' },
  rejected: { color: 'error', text: '已拒绝' },
}

export const SOURCE_TYPE_CONFIG: Record<string, { icon: string; text: string }> = {
  ecommerce: { icon: 'ShoppingOutlined', text: '电商平台' },
  official: { icon: 'GlobalOutlined', text: '官方网站' },
  forum: { icon: 'MessageOutlined', text: '论坛' },
  unknown: { icon: 'FileTextOutlined', text: '未知' },
}

export const EQUIPMENT_TYPE_CONFIG: Record<string, string> = {
  rod: '鱼竿',
  reel: '渔轮',
  line: '鱼线',
  lure: '拟饵',
  accessory: '配件',
  unknown: '未知',
}
