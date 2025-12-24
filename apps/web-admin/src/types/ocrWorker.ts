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
