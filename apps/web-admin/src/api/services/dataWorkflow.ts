/**
 * 数据处理工作流 API 服务
 */

import client from '../client'
import type {
  WorkflowStats,
  WorkerListResponse,
  OCRTaskListResponse,
  OCRTaskFilters,
  ReviewTaskListResponse,
  ReviewTaskFilters,
  ReviewAction,
  OperationResponse,
  ExtractResponse,
  ExtractedDataUpdate,
  TaskImagesResponse,
} from '../../types/dataWorkflow'

const BASE_URL = '/admin/workflow'

export const dataWorkflowApi = {
  // ========== 统计 ==========

  /**
   * 获取工作流统计数据
   */
  getStats: (): Promise<WorkflowStats> => {
    return client.get(`${BASE_URL}/stats`)
  },

  // ========== Worker 监控 ==========

  /**
   * 获取 Worker 列表
   */
  getWorkers: (): Promise<WorkerListResponse> => {
    return client.get(`${BASE_URL}/workers`)
  },

  // ========== OCR 任务 ==========

  /**
   * 获取 OCR 任务列表
   */
  getOCRTasks: (params?: OCRTaskFilters): Promise<OCRTaskListResponse> => {
    return client.get(`${BASE_URL}/ocr/tasks`, { params })
  },

  /**
   * 重试 OCR 任务
   */
  retryOCRTask: (pendingId: number): Promise<OperationResponse> => {
    return client.post(`${BASE_URL}/ocr/tasks/${pendingId}/retry`)
  },

  /**
   * 批量重试 OCR 任务
   */
  batchRetryOCRTasks: (pendingIds: number[]): Promise<OperationResponse> => {
    return client.post(`${BASE_URL}/ocr/tasks/batch-retry`, pendingIds)
  },

  /**
   * 跳过 OCR 任务
   */
  skipOCRTask: (pendingId: number): Promise<OperationResponse> => {
    return client.post(`${BASE_URL}/ocr/tasks/${pendingId}/skip`)
  },

  /**
   * 设置 OCR 任务优先级
   */
  setOCRTaskPriority: (pendingId: number, priority: number): Promise<OperationResponse> => {
    return client.put(`${BASE_URL}/ocr/tasks/${pendingId}/priority`, null, {
      params: { priority },
    })
  },

  /**
   * 删除 OCR 任务
   */
  deleteOCRTask: (pendingId: number): Promise<OperationResponse> => {
    return client.delete(`${BASE_URL}/ocr/tasks/${pendingId}`)
  },

  // ========== 审核任务 ==========

  /**
   * 获取审核任务列表
   */
  getReviewTasks: (params?: ReviewTaskFilters): Promise<ReviewTaskListResponse> => {
    return client.get(`${BASE_URL}/review/tasks`, { params })
  },

  /**
   * 审核任务
   */
  reviewTask: (taskId: number, action: ReviewAction): Promise<OperationResponse> => {
    return client.post(`${BASE_URL}/review/tasks/${taskId}/review`, action)
  },

  /**
   * 删除审核任务
   */
  deleteReviewTask: (taskId: number): Promise<OperationResponse> => {
    return client.delete(`${BASE_URL}/review/tasks/${taskId}`)
  },

  // ========== 装备提取 ==========

  /**
   * 一键提取装备信息
   */
  extractEquipment: (taskId: number): Promise<ExtractResponse> => {
    return client.post(`${BASE_URL}/review/tasks/${taskId}/extract`)
  },

  /**
   * 保存编辑后的装备数据
   */
  saveExtractedData: (taskId: number, data: ExtractedDataUpdate): Promise<OperationResponse> => {
    return client.put(`${BASE_URL}/review/tasks/${taskId}/extracted-data`, data)
  },

  // ========== 图片查看 ==========

  /**
   * 获取任务图片列表
   */
  getTaskImages: (taskId: number): Promise<TaskImagesResponse> => {
    return client.get(`${BASE_URL}/review/tasks/${taskId}/images`)
  },

  /**
   * 获取图片 URL（用于 <img> 标签）
   * 由于 img 标签无法携带 Authorization header，需要通过 query parameter 传递 token
   */
  getImageUrl: (imagePath: string): string => {
    const token = localStorage.getItem('fishing_admin_token')
    return `/api/v1${BASE_URL}/images/${imagePath}?token=${token || ''}`
  },
}

export default dataWorkflowApi
