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

export type ReviewStatus = 'pending' | 'approved' | 'rejected'

/**
 * 审核历史记录项
 */
export interface ReviewHistoryItem {
  reviewed_by: number
  reviewed_at: string
  action: 'approve' | 'reject'
  review_notes: string | null
  previous_status: ReviewStatus
}

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
  review_history: ReviewHistoryItem[] | null  // 审核历史
}

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

// ========== 装备提取相关 ==========

/**
 * 提取的装备项
 */
export interface ExtractedEquipmentItem {
  equipment_type: string
  brand_name: string | null
  model: string | null
  name: string | null
  price_min: number | null
  price_max: number | null
  description: string | null
  features: string[]
  target_fish: string[]
  user_level: string | null
  specs: Record<string, unknown>
  confidence: number
  extraction_notes: string
}

/**
 * 装备提取响应
 */
export interface ExtractResponse {
  success: boolean
  message: string
  extracted_count: number
  items: ExtractedEquipmentItem[]
}

/**
 * 更新提取数据请求
 */
export interface ExtractedDataUpdate {
  items: ExtractedEquipmentItem[]
}

// ========== 装备规格字段配置 ==========

/**
 * 鱼竿调性选项
 */
export const ROD_POWER_OPTIONS = ['UL', 'L', 'ML', 'M', 'MH', 'H', 'XH']

/**
 * 鱼竿动作选项
 */
export const ROD_ACTION_OPTIONS = ['慢调', '中调', '快调', '超快调']

/**
 * 用户级别选项
 */
export const USER_LEVEL_OPTIONS = ['新手', '进阶', '高手']

/**
 * 装备类型选项
 */
export const EQUIPMENT_TYPE_OPTIONS = [
  { value: '鱼竿', label: '鱼竿' },
  { value: '渔轮', label: '渔轮' },
  { value: '鱼线', label: '鱼线' },
  { value: '拟饵', label: '拟饵' },
]

// ========== 图片相关 ==========

export interface ImageInfo {
  filename: string
  url: string
  order: number
  original_name: string | null
}

export interface TaskImagesResponse {
  task_id: number
  images: ImageInfo[]
  total: number
}
