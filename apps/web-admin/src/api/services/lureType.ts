/**
 * 拟饵类型 API 服务
 */

import client from '../client'
import type {
  LureType,
  LureTypeListResponse,
  LureTypeListParams,
  LureTypeCreateRequest,
  LureTypeUpdateRequest,
  CategoryStatsResponse,
  InitDataResponse,
} from '@/types/lureType'

export const lureTypeApi = {
  /**
   * 获取拟饵类型列表
   */
  list: (params?: LureTypeListParams): Promise<LureTypeListResponse> => {
    return client.get('/admin/content/lure-types', { params })
  },

  /**
   * 获取分类统计
   */
  getStats: (): Promise<CategoryStatsResponse> => {
    return client.get('/admin/content/lure-types/stats')
  },

  /**
   * 获取拟饵类型详情
   */
  get: (id: number): Promise<LureType> => {
    return client.get(`/admin/content/lure-types/${id}`)
  },

  /**
   * 创建拟饵类型
   */
  create: (data: LureTypeCreateRequest): Promise<LureType> => {
    return client.post('/admin/content/lure-types', data)
  },

  /**
   * 更新拟饵类型
   */
  update: (id: number, data: LureTypeUpdateRequest): Promise<LureType> => {
    return client.put(`/admin/content/lure-types/${id}`, data)
  },

  /**
   * 删除拟饵类型
   */
  delete: (id: number): Promise<void> => {
    return client.delete(`/admin/content/lure-types/${id}`)
  },

  /**
   * 初始化默认数据
   */
  initData: (): Promise<InitDataResponse> => {
    return client.post('/admin/content/lure-types/init')
  },
}

export default lureTypeApi
