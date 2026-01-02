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
   * 初始化默认数据
   */
  initData: (): Promise<AccessoryInitDataResponse> => {
    return client.post('/admin/content/accessories/init')
  },
}

export default accessoryApi
