/**
 * OCR Worker API 服务
 */

import client from '../client'
import type { OCRStats, OCRTaskListResponse, OCRTaskFilters } from '../../types/ocrWorker'
import type {
  OCRTaskRetryResponse,
  OCRTaskBatchRetryRequest,
  OCRTaskBatchRetryResponse,
  OCRTaskSkipResponse,
  OCRTaskSetPriorityRequest,
  OCRTaskSetPriorityResponse,
  OCRTaskDeleteResponse,
} from '../../types/ocrWorker'

export const ocrWorkerApi = {
  /**
   * 获取 OCR 任务统计
   */
  getStats: (): Promise<OCRStats> => {
    return client.get('/ocr-worker/stats')
  },

  /**
   * 获取 OCR 任务列表
   */
  getTasks: (params?: OCRTaskFilters): Promise<OCRTaskListResponse> => {
    return client.get('/ocr-worker/tasks', { params })
  },

  /**
   * 重试单个OCR任务
   */
  retryTask: (pendingId: number): Promise<OCRTaskRetryResponse> => {
    return client.post(`/ocr-worker/admin/tasks/${pendingId}/retry`)
  },

  /**
   * 批量重试OCR任务
   */
  retryTasksBatch: (data: OCRTaskBatchRetryRequest): Promise<OCRTaskBatchRetryResponse> => {
    return client.post('/ocr-worker/admin/tasks/retry-batch', data)
  },

  /**
   * 跳过OCR任务
   */
  skipTask: (pendingId: number): Promise<OCRTaskSkipResponse> => {
    return client.post(`/ocr-worker/admin/tasks/${pendingId}/skip`)
  },

  /**
   * 设置任务优先级
   */
  setTaskPriority: (pendingId: number, data: OCRTaskSetPriorityRequest): Promise<OCRTaskSetPriorityResponse> => {
    return client.put(`/ocr-worker/admin/tasks/${pendingId}/priority`, data)
  },

  /**
   * 删除任务
   */
  deleteTask: (pendingId: number): Promise<OCRTaskDeleteResponse> => {
    return client.delete(`/ocr-worker/admin/tasks/${pendingId}`)
  },
}

export default ocrWorkerApi
