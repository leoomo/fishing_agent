/**
 * OCR Worker API 服务
 */

import client from '../client'
import type { OCRStats, OCRTaskListResponse, OCRTaskFilters } from '../../types/ocrWorker'

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
}

export default ocrWorkerApi
