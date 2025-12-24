/**
 * OCR Worker 类型定义
 */

export interface OCRStats {
  total: number
  pending: number
  processing: number
  completed: number
  failed: number
  skipped: number
}

export interface OCRTaskItem {
  pending_id: number
  brand_name?: string
  product_name?: string
  ocr_status: string
  ocr_worker_id?: string
  ocr_started_at?: string
  ocr_completed_at?: string
  ocr_processing_time_ms?: number
  ocr_provider?: string
  ocr_retry_count: number
  ocr_error_message?: string
  ocr_priority: number
  images_count: number
  created_at?: string
}

export interface OCRTaskListResponse {
  success: boolean
  tasks: OCRTaskItem[]
  total: number
  page: number
  page_size: number
}

export interface OCRTaskFilters {
  ocr_status?: string
  page?: number
  page_size?: number
}

// ========== 管理员操作 ==========

export interface OCRTaskRetryResponse {
  success: boolean
  message: string
  pending_id: number
  previous_status: string
}

export interface OCRTaskBatchRetryRequest {
  pending_ids?: number[]
  ocr_status?: 'failed' | 'skipped' | 'processing'
}

export interface OCRTaskBatchRetryResponse {
  success: boolean
  message: string
  retried_count: number
  skipped_count: number
  pending_ids: number[]
}

export interface OCRTaskSkipResponse {
  success: boolean
  message: string
  pending_id: number
}

export interface OCRTaskSetPriorityRequest {
  priority: number  // 0=默认, 1=低, 5=高, 10=紧急
}

export interface OCRTaskSetPriorityResponse {
  success: boolean
  message: string
  pending_id: number
  old_priority: number
  new_priority: number
}

export interface OCRTaskDeleteResponse {
  success: boolean
  message: string
  pending_id: number
}

// 优先级选项
export const OCR_PRIORITY_OPTIONS = [
  { label: '紧急', value: 10, color: '#ff4d4f' },
  { label: '高', value: 5, color: '#faad14' },
  { label: '默认', value: 0, color: '#d9d9d9' },
  { label: '低', value: 1, color: '#52c41a' },
] as const
