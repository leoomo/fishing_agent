/**
 * 钓鱼配件 API 服务
 */

import client from '../client'
import type {
  Accessory,
  AccessoryListResponse,
  AccessoryListParams,
  AccessoryCreateRequest,
  AccessoryUpdateRequest,
  AccessoryCategoryStatsResponse,
  AccessoryOptionsResponse,
  AccessoryInitDataResponse,
  AccessoryBatchDeleteResponse,
  AccessoryImportPreviewResponse,
  AccessoryImportResult,
} from '@/types/accessory'

export const accessoryApi = {
  /**
   * 获取配件列表
   */
  list: (params?: AccessoryListParams): Promise<AccessoryListResponse> => {
    return client.get('/admin/content/accessories', { params })
  },

  /**
   * 获取分类统计
   */
  getStats: (): Promise<AccessoryCategoryStatsResponse> => {
    return client.get('/admin/content/accessories/stats')
  },

  /**
   * 获取表单选项
   */
  getOptions: (): Promise<AccessoryOptionsResponse> => {
    return client.get('/admin/content/accessories/options')
  },

  /**
   * 获取配件详情
   */
  get: (id: number): Promise<Accessory> => {
    return client.get(`/admin/content/accessories/${id}`)
  },

  /**
   * 创建配件
   */
  create: (data: AccessoryCreateRequest): Promise<Accessory> => {
    return client.post('/admin/content/accessories', data)
  },

  /**
   * 更新配件
   */
  update: (id: number, data: AccessoryUpdateRequest): Promise<Accessory> => {
    return client.put(`/admin/content/accessories/${id}`, data)
  },

  /**
   * 删除配件
   */
  delete: (id: number): Promise<void> => {
    return client.delete(`/admin/content/accessories/${id}`)
  },

  /**
   * 批量删除配件
   */
  batchDelete: (ids: number[]): Promise<AccessoryBatchDeleteResponse> => {
    return client.post('/admin/content/accessories/batch-delete', { ids })
  },

  /**
   * 初始化默认数据
   */
  initData: (): Promise<AccessoryInitDataResponse> => {
    return client.post('/admin/content/accessories/init')
  },

  /**
   * 下载导入模板
   */
  downloadTemplate: async (): Promise<void> => {
    const response = await client.get('/admin/content/accessories/export/template', {
      responseType: 'blob',
    })
    // 创建下载链接
    const blob = new Blob([response as unknown as BlobPart], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '配件导入模板.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },

  /**
   * 预览导入数据
   */
  importPreview: (file: File): Promise<AccessoryImportPreviewResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/admin/content/accessories/import/preview', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  /**
   * 执行导入
   */
  importExecute: (file: File): Promise<AccessoryImportResult> => {
    const formData = new FormData()
    formData.append('file', file)
    return client.post('/admin/content/accessories/import/execute', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  /**
   * 导出数据
   */
  exportData: async (): Promise<void> => {
    const response = await client.get('/admin/content/accessories/export', {
      responseType: 'blob',
    })
    // 创建下载链接
    const blob = new Blob([response as unknown as BlobPart], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `配件数据导出_${new Date().toISOString().slice(0, 10)}.xlsx`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },
}

export default accessoryApi
