/**
 * 鱼百科 API 服务
 */

import client from '../client'
import type {
  FishSpecies,
  FishSpeciesListResponse,
  FishSpeciesListParams,
  FishSpeciesCreateRequest,
  FishSpeciesUpdateRequest,
  FishCategoryStatsResponse,
  FishInitDataResponse,
  FishKnowledge,
  FishKnowledgeCreate,
  FishKnowledgeUpdate,
  FishSeasonActivity,
  FishSeasonActivityCreate,
  FishSeasonActivityUpdate,
  EquipmentRecommendation,
  FetchProgressResponse,
  FetchStartRequest,
  FetchRetryRequest,
  FetchActionResponse,
} from '@/types/fish'

export const fishApi = {
  // ========== 鱼种 CRUD ==========

  /**
   * 获取鱼种列表
   */
  list: (params?: FishSpeciesListParams): Promise<FishSpeciesListResponse> => {
    return client.get('/admin/content/fish-species', { params })
  },

  /**
   * 获取分类统计
   */
  getStats: (): Promise<FishCategoryStatsResponse> => {
    return client.get('/admin/content/fish-species/stats')
  },

  /**
   * 获取鱼种详情
   */
  get: (id: number): Promise<FishSpecies> => {
    return client.get(`/admin/content/fish-species/${id}`)
  },

  /**
   * 创建鱼种
   */
  create: (data: FishSpeciesCreateRequest): Promise<FishSpecies> => {
    return client.post('/admin/content/fish-species', data)
  },

  /**
   * 更新鱼种
   */
  update: (id: number, data: FishSpeciesUpdateRequest): Promise<FishSpecies> => {
    return client.put(`/admin/content/fish-species/${id}`, data)
  },

  /**
   * 删除鱼种
   */
  delete: (id: number): Promise<void> => {
    return client.delete(`/admin/content/fish-species/${id}`)
  },

  /**
   * 初始化默认数据
   */
  initData: (): Promise<FishInitDataResponse> => {
    return client.post('/admin/content/fish-species/init')
  },

  // ========== 知识库管理 ==========

  /**
   * 添加知识条目
   */
  addKnowledge: (speciesId: number, data: FishKnowledgeCreate): Promise<FishKnowledge> => {
    return client.post(`/admin/content/fish-species/${speciesId}/knowledge`, data)
  },

  /**
   * 更新知识条目
   */
  updateKnowledge: (
    speciesId: number,
    knowledgeId: number,
    data: FishKnowledgeUpdate
  ): Promise<FishKnowledge> => {
    return client.put(`/admin/content/fish-species/${speciesId}/knowledge/${knowledgeId}`, data)
  },

  /**
   * 删除知识条目
   */
  deleteKnowledge: (speciesId: number, knowledgeId: number): Promise<void> => {
    return client.delete(`/admin/content/fish-species/${speciesId}/knowledge/${knowledgeId}`)
  },

  // ========== 季节活动管理 ==========

  /**
   * 添加季节活动
   */
  addSeasonActivity: (
    speciesId: number,
    data: FishSeasonActivityCreate
  ): Promise<FishSeasonActivity> => {
    return client.post(`/admin/content/fish-species/${speciesId}/seasons`, data)
  },

  /**
   * 更新季节活动
   */
  updateSeasonActivity: (
    speciesId: number,
    seasonId: number,
    data: FishSeasonActivityUpdate
  ): Promise<FishSeasonActivity> => {
    return client.put(`/admin/content/fish-species/${speciesId}/seasons/${seasonId}`, data)
  },

  /**
   * 删除季节活动
   */
  deleteSeasonActivity: (speciesId: number, seasonId: number): Promise<void> => {
    return client.delete(`/admin/content/fish-species/${speciesId}/seasons/${seasonId}`)
  },

  // ========== 装备推荐 ==========

  /**
   * 获取装备推荐（只读）
   */
  getEquipmentRecommendation: (speciesId: number): Promise<EquipmentRecommendation> => {
    return client.get(`/admin/content/fish-species/${speciesId}/equipment`)
  },

  // ========== 网络采集 ==========

  /**
   * 获取采集进度
   */
  getFetchProgress: (): Promise<FetchProgressResponse> => {
    return client.get('/admin/content/fish-species/fetch/progress')
  },

  /**
   * 开始采集
   */
  startFetch: (data: FetchStartRequest): Promise<FetchActionResponse> => {
    return client.post('/admin/content/fish-species/fetch/start', data)
  },

  /**
   * 暂停采集
   */
  pauseFetch: (): Promise<FetchActionResponse> => {
    return client.post('/admin/content/fish-species/fetch/pause')
  },

  /**
   * 重试失败项
   */
  retryFetch: (data: FetchRetryRequest): Promise<FetchActionResponse> => {
    return client.post('/admin/content/fish-species/fetch/retry', data)
  },

  /**
   * 重置采集进度
   */
  resetFetch: (): Promise<FetchActionResponse> => {
    return client.post('/admin/content/fish-species/fetch/reset')
  },
}

export default fishApi
