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

export type WorkflowTab = 'collection' | 'ocr' | 'import' | 'review' | 'worker'

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
  excel_import: { icon: 'FileExcelOutlined', text: 'Excel导入' },
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

// ========== WebSocket 实时更新相关 ==========

/**
 * WebSocket 事件类型
 */
export type WorkflowEventType =
  | 'init'
  | 'stats_update'
  | 'worker_update'
  | 'task_claimed'
  | 'ocr_started'
  | 'ocr_progress'
  | 'ocr_completed'
  | 'ocr_failed'
  | 'review_update'
  | 'worker_log'
  | 'pong'

/**
 * OCR 处理阶段
 */
export type OCRStage = 'downloading' | 'merging' | 'ocr_processing' | 'extracting'

/**
 * OCR 阶段配置
 */
export const OCR_STAGE_CONFIG: Record<OCRStage, { order: number; text: string; icon: string }> = {
  downloading: { order: 0, text: '下载图片', icon: 'DownloadOutlined' },
  merging: { order: 1, text: '合并图片', icon: 'MergeCellsOutlined' },
  ocr_processing: { order: 2, text: 'OCR识别', icon: 'ScanOutlined' },
  extracting: { order: 3, text: '数据提取', icon: 'FileSearchOutlined' },
}

/**
 * OCR 进度信息
 */
export interface OCRProgressInfo {
  pending_id: number
  stage: OCRStage
  progress: number // 0-100
  message: string | null
  current_image: number | null
  total_images: number | null
  timestamp: string
}

/**
 * Worker 日志级别
 */
export type WorkerLogLevel = 'debug' | 'info' | 'warning' | 'error'

/**
 * Worker 日志项
 */
export interface WorkerLogItem {
  timestamp: string
  worker_id: string
  level: WorkerLogLevel
  message: string
  pending_id: number | null
}

/**
 * WebSocket 事件数据
 */
export interface WorkflowWSEvent<T = unknown> {
  type: WorkflowEventType
  data: T
  pending_id?: number
  timestamp: string
}

/**
 * 初始化事件数据
 */
export interface WSInitData {
  stats: WorkflowStats | null
  workers: WorkerInfo[] | null
}

/**
 * 任务领取事件数据
 */
export interface WSTaskClaimedData {
  worker_id: string
  ocr_provider: string | null
}

/**
 * OCR 完成事件数据
 */
export interface WSOCRCompletedData {
  success: boolean
  processing_time_ms: number
  ocr_text_length: number | null
  extracted_count: number | null
}

/**
 * OCR 失败事件数据
 */
export interface WSOCRFailedData {
  error_code: string
  error_message: string
  retry_count: number
}

/**
 * 日志级别颜色配置
 */
export const LOG_LEVEL_CONFIG: Record<WorkerLogLevel, { color: string; tag: string }> = {
  debug: { color: '#8c8c8c', tag: 'DEBUG' },
  info: { color: '#1890ff', tag: 'INFO' },
  warning: { color: '#faad14', tag: 'WARN' },
  error: { color: '#ff4d4f', tag: 'ERROR' },
}

/**
 * WebSocket 连接状态
 */
export type WSConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

/**
 * WebSocket 连接状态配置
 */
export const WS_STATUS_CONFIG: Record<WSConnectionStatus, { color: string; text: string }> = {
  connecting: { color: 'processing', text: '连接中' },
  connected: { color: 'success', text: '已连接' },
  disconnected: { color: 'default', text: '已断开' },
  error: { color: 'error', text: '连接错误' },
}

// ========== Excel 导入相关 ==========

/**
 * 导入模板信息
 */
export interface ImportTemplateInfo {
  equipment_type: string
  equipment_type_label: string
  download_url: string
}

/**
 * 模板列表响应
 */
export interface ImportTemplateListResponse {
  templates: ImportTemplateInfo[]
}

/**
 * 导入预览行
 */
export interface ImportPreviewRow {
  row_number: number
  data: Record<string, unknown>
  is_valid: boolean
  errors: string[]
}

/**
 * 导入预览响应
 */
export interface ImportPreviewResponse {
  success: boolean
  message: string
  equipment_type: string
  total_rows: number
  valid_rows: number
  invalid_rows: number
  preview_data: ImportPreviewRow[]
}

/**
 * 导入错误
 */
export interface ImportError {
  row: number
  errors: string[]
  data: Record<string, unknown>
}

/**
 * 导入响应
 */
export interface ImportResponse {
  success: boolean
  message: string
  total_rows: number
  imported_count: number
  failed_count: number
  pending_ids: number[]
  errors: ImportError[]
}

/**
 * 导入装备类型选项
 */
export const IMPORT_EQUIPMENT_TYPES = [
  { key: 'rod', label: '鱼竿' },
  { key: 'reel', label: '渔轮' },
  { key: 'line', label: '鱼线' },
  { key: 'lure', label: '拟饵' },
]
